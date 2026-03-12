"""
API FastAPI — Pont entre modele_AI et le dashboard Nuxt
=======================================================
Site unique — configuration caméra modifiable depuis le dashboard.

Endpoints :
  GET  /api/site                → état courant du site
  GET  /api/site/history        → historique densité 30 min
  GET  /api/site/predictions    → prédictions TimeGPT
  GET  /api/alerts?limit=N      → dernières alertes
  GET  /api/alerts/export       → export CSV
  PUT  /api/config              → mettre à jour nom + URL caméra
  GET  /api/config              → lire la configuration active
  GET  /api/stream              → flux MJPEG de la caméra (pour le dashboard)
  WS   /ws/socket.io            → flux temps réel (Socket.IO)

Lancement :
  cd modele_AI
  uvicorn api:app --reload --port 8000
"""

import sys, os, time, threading, uuid, json, base64, asyncio
from collections import deque
from datetime import datetime
from typing import Dict, Generator

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "process"))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import socketio

from detection_traking import stream_frames
from detection_anamalie import AnomalyDetector, analyser_frame
from prediction_gestion import CongestionPredictor, construire_zone_data

# ── Fichier de persistance config ─────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "site_config.json")
DEFAULT_CONFIG = {
    "name":   "Mon site",
    "source": "foule.mp4",   # URL caméra ou chemin fichier
    "lat":    14.7247,
    "lng":    -17.4591,
    "capacity": 1000,
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ── État global ────────────────────────────────────────────────────────────────
ZONE_AREA_M2 = 25.0

class SiteState:
    def __init__(self):
        self.config = load_config()
        self.zones: Dict[str, dict] = {
            z: {"count": 0, "density": 0.0, "avgSpeed": 0.0, "status": "normal"}
            for z in ["A", "B", "C", "D"]
        }
        self.in_count    = 0
        self.out_count   = 0
        self.frame_idx   = 0
        self.status      = "normal"
        self.last_update = datetime.now().isoformat()
        self.history: Dict[str, deque] = {z: deque(maxlen=30) for z in ["A","B","C","D"]}
        self.predictor   = CongestionPredictor()
        self.predictions: list = []
        self.last_obs_time  = 0.0
        self.last_pred_time = 0.0
        # Frame annotée partagée avec l'endpoint /api/stream
        self.latest_frame: np.ndarray | None = None
        self.frame_lock = threading.Lock()

    def update_zones(self, zone_counts: dict, in_c: int, out_c: int, frame_idx: int):
        self.in_count  = in_c
        self.out_count = out_c
        self.frame_idx = frame_idx
        for z, count in zone_counts.items():
            if z not in self.zones:
                continue
            density  = count / ZONE_AREA_M2
            avg_speed = max(0.1, 2.0 - density * 0.3)
            status   = "critical" if density >= 4.0 else "attention" if density >= 3.0 else "normal"
            self.zones[z] = {
                "count":    count,
                "density":  round(density, 2),
                "avgSpeed": round(avg_speed, 2),
                "status":   status,
            }
        self.status = (
            "critical"  if any(z["status"] == "critical"  for z in self.zones.values()) else
            "attention" if any(z["status"] == "attention" for z in self.zones.values()) else
            "normal"
        )
        self.last_update = datetime.now().isoformat()

    def snapshot(self) -> dict:
        return {
            "id":           "site-principal",
            "name":         self.config["name"],
            "source":       self.config["source"],
            "lat":          self.config["lat"],
            "lng":          self.config["lng"],
            "capacity":     self.config["capacity"],
            "totalPersons": sum(z["count"] for z in self.zones.values()),
            "inCount":      self.in_count,
            "outCount":     self.out_count,
            "zones":        self.zones,
            "status":       self.status,
            "lastUpdate":   self.last_update,
        }

site_state  = SiteState()
alerts_queue: deque = deque(maxlen=200)

# ── Thread d'analyse ───────────────────────────────────────────────────────────
analysis_thread: threading.Thread | None = None
stop_event      = threading.Event()
_loop: asyncio.AbstractEventLoop | None = None   # event loop principal FastAPI

def _emit(event: str, data):
    """Émet un événement Socket.IO depuis le thread d'analyse sans bloquer."""
    if _loop and not _loop.is_closed():
        asyncio.run_coroutine_threadsafe(sio.emit(event, data), _loop)

MESSAGES = {
    "normal":         lambda d: f"Flux normal — {d}",
    "panic":          lambda d: f"Panique détectée — {d}",
    "surcompression": lambda d: f"Surcompression — {d}",
    "chute":          lambda d: f"Chute détectée — {d}",
    "contre_flux":    lambda d: f"Contre-flux — {d}",
    "arret_masse":    lambda d: f"Arrêt de masse — {d}",
    "accumulation":   lambda d: f"Accumulation rapide — {d}",
}

def run_analysis():
    """Boucle principale : stream → détection → prédiction → broadcast."""
    detector  = AnomalyDetector()
    frame_idx = 0
    stop_event.clear()
    alerts_queue.clear()

    source = site_state.config["source"]
    print(f"[INFO] Démarrage analyse — source: {source}")

    try:
        for frame, in_count, out_count, zone_counts, tracks in stream_frames(source):
            if stop_event.is_set():
                break
            frame_idx += 1
            site_state.update_zones(zone_counts, in_count, out_count, frame_idx)

            with site_state.frame_lock:
                site_state.latest_frame = frame

            # Détection anomalies (toutes les 2 frames)
            if frame_idx % 2 == 0:
                raw_alerts = analyser_frame(detector, frame, zone_counts, tracks)
                for a in raw_alerts:
                    anomaly_type = getattr(a, "type_anomalie", "inconnu")
                    level        = a.level.lower() if hasattr(a, "level") else "info"
                    detail       = getattr(a, "detail", "")
                    message      = MESSAGES.get(anomaly_type, lambda d: d)(detail)

                    alert_obj = {
                        "id":          str(uuid.uuid4()),
                        "level":       level,
                        "siteId":      "site-principal",
                        "siteName":    site_state.config["name"],
                        "zone":        getattr(a, "zone", "G"),
                        "anomalyType": anomaly_type,
                        "message":     message,
                        "timestamp":   datetime.now().isoformat(),
                        "confidence":  getattr(a, "confiance", 0.8),
                        "resolved":    False,
                    }
                    alerts_queue.appendleft(alert_obj)
                    if anomaly_type != "normal":
                        _emit("alert", alert_obj)

            now = time.time()

            # Observation TimeGPT (1x/min)
            if now - site_state.last_obs_time >= 60:
                zone_data = construire_zone_data(zone_counts, in_count, out_count, frame_idx)
                site_state.predictor.ajouter_observation(zone_data)
                site_state.last_obs_time = now
                ts = datetime.now().replace(second=0, microsecond=0).isoformat()
                for z in ["A", "B", "C", "D"]:
                    site_state.history[z].append({"time": ts, "density": site_state.zones[z]["density"]})

            # Prédictions (toutes les 5 min)
            if now - site_state.last_pred_time >= 300:
                preds = site_state.predictor.predire()
                if preds:
                    site_state.predictions = [
                        {
                            "zone": z,
                            "h5":  round(preds[z].get(5, 0.0), 2),
                            "h10": round(preds[z].get(10, 0.0), 2),
                            "h15": round(preds[z].get(15, 0.0), 2),
                            "confidence": 0.85,
                            "trend": (
                                "up"   if preds[z].get(15, 0) > preds[z].get(5, 0) + 0.2 else
                                "down" if preds[z].get(15, 0) < preds[z].get(5, 0) - 0.2 else
                                "stable"
                            ),
                        }
                        for z in ["A", "B", "C", "D", "G"]
                    ]
                site_state.last_pred_time = now

            # Broadcast frame vidéo via WebSocket (~10 fps)
            if frame_idx % 3 == 0:
                thumb = cv2.resize(frame, (854, 480))
                _, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, 55])
                _emit("frame", base64.b64encode(buf.tobytes()).decode("ascii"))

            # Broadcast site_update (~2s)
            if frame_idx % 50 == 0:
                _emit("site_update", {
                    "timestamp": datetime.now().isoformat(),
                    "zones": {
                        z: {"count": v["count"], "density": v["density"], "avgSpeed": v["avgSpeed"]}
                        for z, v in site_state.zones.items()
                    },
                })

    except Exception as e:
        print(f"[ERREUR] Analyse arrêtée : {e}")
        site_state.status = "offline"


def restart_analysis():
    """Arrête et relance le thread d'analyse (après changement de config)."""
    global analysis_thread
    stop_event.set()
    if analysis_thread and analysis_thread.is_alive():
        analysis_thread.join(timeout=5)
    stop_event.clear()
    analysis_thread = threading.Thread(target=run_analysis, daemon=True, name="analysis")
    analysis_thread.start()


# ── FastAPI + Socket.IO ────────────────────────────────────────────────────────
# Socket.IO monté DANS FastAPI (évite le problème de 404 sur les routes REST)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False, engineio_logger=False,
)

app = FastAPI(title="JOJ Dakar 2026 — API Surveillance")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# Socket.IO accessible à /ws/socket.io
app.mount("/ws/socket.io", socketio.ASGIApp(sio, socketio_path=""))

# Alias pour compatibilité interne
fastapi_app = app


@app.on_event("startup")
async def on_startup():
    global _loop
    _loop = asyncio.get_running_loop()
    restart_analysis()


# ── REST endpoints ─────────────────────────────────────────────────────────────

class SiteConfig(BaseModel):
    name:   str
    source: str   # URL IP ou chemin fichier

@fastapi_app.get("/api/config")
async def get_config():
    return site_state.config

@fastapi_app.put("/api/config")
async def update_config(body: SiteConfig):
    """Met à jour le nom et l'URL de la caméra, puis redémarre l'analyse."""
    site_state.config["name"]   = body.name
    site_state.config["source"] = body.source
    save_config(site_state.config)
    # Redémarre le thread avec la nouvelle source
    threading.Thread(target=restart_analysis, daemon=True).start()
    await sio.emit("config_updated", site_state.config)
    return {"ok": True, "config": site_state.config}

@fastapi_app.get("/api/site")
async def get_site():
    return site_state.snapshot()

@fastapi_app.get("/api/site/history")
async def get_history():
    return {z: list(site_state.history[z]) for z in ["A","B","C","D"]}

@fastapi_app.get("/api/site/predictions")
async def get_predictions():
    return site_state.predictions

@fastapi_app.get("/api/alerts")
async def get_alerts(limit: int = Query(50, le=200)):
    return list(alerts_queue)[:limit]

@app.get("/api/stream")
async def video_stream():
    """
    Flux MJPEG avec annotations YOLO tracking.
    Sert les frames annotées produites par run_analysis().
    """
    # Frame d'attente (affichée tant que l'analyse n'a pas encore de frame)
    _waiting = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(_waiting, "Demarrage analyse...", (160, 170),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 210, 100), 2)
    cv2.putText(_waiting, site_state.config.get("source", ""), (80, 210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

    def mjpeg_generator() -> Generator[bytes, None, None]:
        while True:
            try:
                with site_state.frame_lock:
                    raw = site_state.latest_frame
                    frame = raw.copy() if raw is not None else None

                if frame is None:
                    frame = _waiting

                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if not ok:
                    time.sleep(0.04)
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + buf.tobytes()
                    + b"\r\n"
                )
            except Exception as e:
                print(f"[STREAM] Erreur frame ignorée : {e}")
            time.sleep(0.04)   # ~25 fps

    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control":    "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",   # désactive le buffering nginx/proxy
            "Pragma":           "no-cache",
        },
    )


@fastapi_app.get("/api/alerts/export")
async def export_alerts():
    header = "id,level,siteName,zone,anomalyType,message,timestamp,confidence\n"
    rows   = "\n".join(
        f"{a['id']},{a['level']},{a['siteName']},{a['zone']},"
        f"{a['anomalyType']},\"{a['message']}\",{a['timestamp']},{a['confidence']}"
        for a in alerts_queue
    )
    return StreamingResponse(
        iter([header + rows]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alertes_joj.csv"},
    )


# ── Socket.IO events ───────────────────────────────────────────────────────────

@sio.event
async def connect(sid, environ):
    print(f"[WS] Client connecté : {sid}")
    # État initial au client
    await sio.emit("site_update", {
        "timestamp": datetime.now().isoformat(),
        "zones": {
            z: {"count": v["count"], "density": v["density"], "avgSpeed": v["avgSpeed"]}
            for z, v in site_state.zones.items()
        },
    }, to=sid)
    await sio.emit("config_updated", site_state.config, to=sid)

@sio.event
async def disconnect(sid):
    print(f"[WS] Client déconnecté : {sid}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
