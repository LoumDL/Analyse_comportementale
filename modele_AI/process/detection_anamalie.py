"""
MODULE 2 — DÉTECTION D'ANOMALIES COMPORTEMENTALES
==================================================
Système d'analyse comportementale des foules — JOJ Dakar 2026

Anomalies détectées :
    CRITICAL  | panic          — Bras levés + accélération soudaine (posture YOLO-Pose)
    CRITICAL  | surcompression — Densité > 4 pers/m² + vitesse ≈ 0
    CRITICAL  | chute          — Personne au sol détectée par YOLO-Pose
    WARNING   | contre_flux    — > 30% de personnes à contre-sens
    WARNING   | arret_masse    — Vitesse moyenne < 2 px/s pendant > 20s
    INFO      | accumulation   — Taux d'entrée > 50 pers/min dans une zone

Modèle ML : YOLO-Pose (yolo11n-pose.pt) — pré-entraîné, temps réel sur CPU
Pipeline   : flux vidéo → YOLO-Pose → features posture → règles + pose → Alert
"""

import time
import math
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from ultralytics import YOLO
from detection_traking import stream_frames
from indicateurs import afficher_tableau_bord


# ─────────────────────────────────────────────
# SEUILS
# ─────────────────────────────────────────────
SEUIL_ACCELERATION  = 80.0   # px/s²
SEUIL_DENSITE_CRIT  = 4.0    # pers/m²
SEUIL_VITESSE_ZERO  = 5.0    # px/s
SEUIL_CONTRE_FLUX   = 0.30   # 30%
SEUIL_ARRET_MASSE   = 2.0    # px/s
DUREE_ARRET_MASSE   = 20.0   # secondes
SEUIL_ACCUMULATION  = 50     # pers/min
ZONES               = ["A", "B", "C", "D"]

# Indices keypoints COCO-17
KP_NEZ, KP_EPAULE_G, KP_EPAULE_D = 0, 5, 6
KP_HANCHE_G, KP_HANCHE_D         = 11, 12
KP_POIGNET_G, KP_POIGNET_D       = 9, 10
KP_CHEVILLE_G, KP_CHEVILLE_D     = 15, 16


# ─────────────────────────────────────────────
# STRUCTURES DE DONNÉES
# ─────────────────────────────────────────────

@dataclass
class Alert:
    """Représente une alerte d'anomalie comportementale."""
    level:         str        # "info" | "warning" | "critical"
    zone:          str        # "A" | "B" | "C" | "D"
    type_anomalie: str
    timestamp:     str
    confiance:     float
    detail:        str = ""

    def __str__(self):
        # Couleurs ANSI console
        color = {
            "info":     "\033[93m",   # jaune
            "warning":  "\033[33m",   # orange
            "critical": "\033[91m",   # rouge
        }.get(self.level, "\033[0m")
        reset = "\033[0m"
        icon  = {"info": "🟡", "warning": "🟠", "critical": "🔴"}.get(self.level, "⚪")
        return (f"{color}{icon} [{self.timestamp}] {self.level.upper():8s} | "
                f"Zone {self.zone} | {self.type_anomalie:15s} | "
                f"conf={self.confiance:.2f} | {self.detail}{reset}")


@dataclass
class ZoneState:
    """État courant d'une zone."""
    speeds:          list  = field(default_factory=list)
    directions:      list  = field(default_factory=list)
    accelerations:   list  = field(default_factory=list)
    density:         float = 0.0
    person_count:    int   = 0
    low_speed_since: float = None
    entry_timestamps: deque = field(default_factory=lambda: deque(maxlen=500))


# ─────────────────────────────────────────────
# ANALYSE DE POSTURE YOLO-POSE
# ─────────────────────────────────────────────

def analyse_posture(keypoints: np.ndarray, conf_threshold: float = 0.4) -> dict:
    """
    Analyse les keypoints d'une personne et retourne des indicateurs comportementaux.

    Keypoints COCO-17 utilisés :
        - Poignets (9, 10) vs épaules (5, 6) → bras levés = panique
        - Nez (0) vs hanches (11, 12)        → personne debout ou au sol
        - Épaules vs chevilles               → ratio hauteur = posture debout/assis/au sol

    Args:
        keypoints      : array (17, 3) — [x, y, confiance] par keypoint
        conf_threshold : confiance minimale pour considérer un keypoint valide
    Returns:
        dict avec clés : "bras_leves", "au_sol", "confiance_posture"
    """
    def kp(idx):
        """Retourne (x, y) si confiance suffisante, sinon None."""
        if keypoints[idx][2] >= conf_threshold:
            return keypoints[idx][:2]
        return None

    epaule_g  = kp(KP_EPAULE_G)
    epaule_d  = kp(KP_EPAULE_D)
    poignet_g = kp(KP_POIGNET_G)
    poignet_d = kp(KP_POIGNET_D)
    nez       = kp(KP_NEZ)
    hanche_g  = kp(KP_HANCHE_G)
    hanche_d  = kp(KP_HANCHE_D)

    bras_leves       = False
    au_sol           = False
    confiance_totale = float(np.mean(keypoints[:, 2]))

    # ── Bras levés : poignets au-dessus des épaules ───────────────────────
    bras_leves_count = 0
    if epaule_g is not None and poignet_g is not None:
        if poignet_g[1] < epaule_g[1]:   # Y plus petit = plus haut dans l'image
            bras_leves_count += 1
    if epaule_d is not None and poignet_d is not None:
        if poignet_d[1] < epaule_d[1]:
            bras_leves_count += 1
    bras_leves = bras_leves_count >= 1

    # ── Au sol : nez proche des hanches (ratio hauteur effondrée) ─────────
    if nez is not None and hanche_g is not None and hanche_d is not None:
        hanche_y = (hanche_g[1] + hanche_d[1]) / 2
        diff_y   = abs(float(nez[1]) - float(hanche_y))
        if diff_y < 40:   # seuil en pixels — à calibrer selon résolution
            au_sol = True

    return {
        "bras_leves":       bras_leves,
        "au_sol":           au_sol,
        "confiance_posture": confiance_totale,
    }


def detect_pose_anomalies(zone: str, pose_results: list) -> list:
    """
    Génère des alertes basées sur l'analyse de posture YOLO-Pose pour toutes
    les personnes détectées dans une zone.

    Args:
        zone         : identifiant de zone ("A"–"D")
        pose_results : liste de dicts retournés par analyse_posture()
    Returns:
        liste d'Alert
    """
    alerts = []
    now    = datetime.now().isoformat(timespec="seconds")

    if not pose_results:
        return alerts

    nb_bras_leves = sum(1 for p in pose_results if p["bras_leves"])
    nb_au_sol     = sum(1 for p in pose_results if p["au_sol"])
    total         = len(pose_results)

    # ── 🔴 PANIQUE : >30% des personnes ont les bras levés ────────────────
    pct_bras = nb_bras_leves / total if total > 0 else 0
    if pct_bras >= 0.30:
        alerts.append(Alert(
            level="critical", zone=zone, type_anomalie="panic",
            timestamp=now, confiance=round(pct_bras, 2),
            detail=f"{nb_bras_leves}/{total} bras leves (YOLO-Pose)"
        ))

    # ── 🔴 CHUTE : au moins une personne détectée au sol ──────────────────
    if nb_au_sol >= 1:
        conf = min(nb_au_sol / total, 1.0)
        alerts.append(Alert(
            level="critical", zone=zone, type_anomalie="chute",
            timestamp=now, confiance=round(conf, 2),
            detail=f"{nb_au_sol} personne(s) au sol (YOLO-Pose)"
        ))

    return alerts


# ─────────────────────────────────────────────
# DÉTECTEUR PAR RÈGLES (mouvement / densité)
# ─────────────────────────────────────────────

def detect_rules(zone: str, state: ZoneState) -> list:
    """
    Applique les règles métier sur les données de mouvement et retourne des alertes.

    Args:
        zone  : identifiant de zone
        state : ZoneState courant
    Returns:
        liste d'Alert
    """
    alerts = []
    now    = datetime.now().isoformat(timespec="seconds")

    speeds = np.array(state.speeds) if state.speeds else np.array([0.0])

    # ── 🔴 SURCOMPRESSION ─────────────────────────────────────────────────
    if state.density > SEUIL_DENSITE_CRIT and float(np.mean(speeds)) < SEUIL_VITESSE_ZERO:
        alerts.append(Alert(
            level="critical", zone=zone, type_anomalie="surcompression",
            timestamp=now,
            confiance=min(state.density / (SEUIL_DENSITE_CRIT * 2), 1.0),
            detail=f"densite={state.density:.2f}/m² vitesse={np.mean(speeds):.1f}px/s"
        ))

    # ── 🟠 CONTRE-FLUX ────────────────────────────────────────────────────
    if len(state.directions) >= 5:
        dirs       = np.array(state.directions)
        diff       = np.abs(dirs - float(np.mean(dirs)))
        diff       = np.where(diff > 180, 360 - diff, diff)
        pct_contre = float(np.mean(diff > 150))
        if pct_contre > SEUIL_CONTRE_FLUX:
            alerts.append(Alert(
                level="warning", zone=zone, type_anomalie="contre_flux",
                timestamp=now, confiance=round(pct_contre, 2),
                detail=f"{pct_contre*100:.0f}% a contre-sens"
            ))

    # ── 🟠 ARRÊT DE MASSE ────────────────────────────────────────────────
    vitesse_moy = float(np.mean(speeds))
    if vitesse_moy < SEUIL_ARRET_MASSE:
        if state.low_speed_since is None:
            state.low_speed_since = time.time()
        elif time.time() - state.low_speed_since > DUREE_ARRET_MASSE:
            duree = time.time() - state.low_speed_since
            alerts.append(Alert(
                level="warning", zone=zone, type_anomalie="arret_masse",
                timestamp=now, confiance=min(duree / 60.0, 1.0),
                detail=f"duree={duree:.0f}s vitesse={vitesse_moy:.1f}px/s"
            ))
    else:
        state.low_speed_since = None

    # ── 🟡 ACCUMULATION RAPIDE ────────────────────────────────────────────
    now_ts = time.time()
    recent = [t for t in state.entry_timestamps if now_ts - t <= 60.0]
    if len(recent) > SEUIL_ACCUMULATION:
        alerts.append(Alert(
            level="info", zone=zone, type_anomalie="accumulation",
            timestamp=now, confiance=min(len(recent) / (SEUIL_ACCUMULATION * 2), 1.0),
            detail=f"{len(recent)} pers/min"
        ))

    return alerts


# ─────────────────────────────────────────────
# DÉTECTEUR PRINCIPAL
# ─────────────────────────────────────────────

class AnomalyDetector:
    """
    Orchestre YOLO-Pose + règles métier pour détecter les anomalies en temps réel.

    Pipeline :
        frame vidéo
            └─► YOLO-Pose (yolo11n-pose.pt)
                    ├─► analyse_posture()    → panic / chute
                    └─► detect_rules()       → surcompression / contre_flux / arrêt / accumulation

    Utilisation :
        detector = AnomalyDetector()
        alerts   = detector.process_frame(frame, zone, tracks, person_count)
        for alert in alerts:
            print(alert)
    """

    def __init__(self, fps: float = 25.0, zone_area_m2: float = 25.0,
                 pose_model_path: str = "yolo26n-pose.pt", frame_skip: int = 2):
        """
        Args:
            fps              : fréquence d'images du flux
            zone_area_m2     : surface réelle d'une zone en m²
            pose_model_path  : chemin vers le modèle YOLO-Pose
            frame_skip       : inférence pose tous les N frames (optimisation CPU)
        """
        self.fps         = fps
        self.zone_area   = zone_area_m2
        self.frame_skip  = frame_skip
        self.frame_idx   = 0
        self.pose_model  = YOLO(pose_model_path)
        self.zone_states = {z: ZoneState() for z in ZONES + ["G"]}
        self.prev_speeds = defaultdict(float)
        self.last_pose_results: dict = {z: [] for z in ZONES + ["G"]}  # cache pose par zone
        print(f"[INFO] YOLO-Pose chargé : '{pose_model_path}'")

    def process_frame(self, frame: np.ndarray, zone: str,
                      tracks: list, person_count: int) -> list:
        """
        Traite une frame et retourne toutes les alertes de la zone.

        Args:
            frame        : image BGR (numpy array)
            zone         : zone concernée ("A"–"D")
            tracks       : [{"id": int, "speed": float, "direction": float}, ...]
            person_count : nombre de personnes dans la zone
        Returns:
            liste d'Alert (vide si aucune anomalie)
        """
        self.frame_idx += 1
        state = self.zone_states[zone]

        # ── Mise à jour état mouvement ────────────────────────────────────
        state.person_count = person_count
        state.density      = person_count / self.zone_area
        state.speeds       = [t["speed"] for t in tracks]
        state.directions   = [t["direction"] for t in tracks]
        state.accelerations = []
        for t in tracks:
            accel = abs(t["speed"] - self.prev_speeds[t["id"]]) * self.fps
            state.accelerations.append(accel)
            self.prev_speeds[t["id"]] = t["speed"]
        state.entry_timestamps.append(time.time())

        # ── Inférence YOLO-Pose (avec skip) ──────────────────────────────
        if self.frame_idx % self.frame_skip == 0:
            results = self.pose_model(frame, verbose=False, classes=[0])
            pose_data = []
            if results and results[0].keypoints is not None:
                for kps in results[0].keypoints.data.cpu().numpy():
                    if kps.shape[0] == 17:
                        pose_data.append(analyse_posture(kps))
            self.last_pose_results[zone] = pose_data

        # ── Détection anomalies posture (YOLO-Pose) ───────────────────────
        pose_alerts = detect_pose_anomalies(zone, self.last_pose_results[zone])

        # ── Détection anomalies mouvement (règles) ────────────────────────
        rule_alerts = detect_rules(zone, state)

        # Dédoublonnage : on évite panic en double (pose + règle)
        pose_types = {a.type_anomalie for a in pose_alerts}
        rule_alerts = [a for a in rule_alerts if a.type_anomalie not in pose_types]

        return pose_alerts + rule_alerts


# ─────────────────────────────────────────────
# CONSTANTES CONSOLE
# ─────────────────────────────────────────────
VERT               = "\033[92m"
RESET              = "\033[0m"
INTERVALLE_RAPPORT = 30.0   # secondes entre chaque affichage console
PHONE_STREAM       = "http://192.168.2.108:4747/video"
# PHONE_STREAM     = "video illustration foule.mp4"


# ─────────────────────────────────────────────
# FONCTIONS DU PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def analyser_frame(detector: AnomalyDetector, frame,
                   zone_counts: dict, tracks: list) -> list:
    """
    Analyse une frame zone par zone (A/B/C/D) en utilisant les données
    réelles de localisation issues de detection_traking.stream_frames().

    Pour chaque zone, construit les tracks avec vitesse et direction réelles,
    appelle AnomalyDetector.process_frame(), et génère une alerte "normal"
    si aucune anomalie n'est détectée dans la zone.

    Args:
        detector    : instance d'AnomalyDetector
        frame       : image BGR
        zone_counts : {"A": int, "B": int, "C": int, "D": int}
        tracks      : [{"id": int, "cx": float, "cy": float, "zone": str,
                         "speed": float, "direction": float}, ...]
    Returns:
        liste d'Alert (toutes zones confondues, inclut les zones normales)
    """
    alertes = []
    now     = datetime.now().isoformat(timespec="seconds")

    for zone, count in zone_counts.items():
        # Tracks réels de cette zone avec vitesse + direction calculées
        zone_tracks = [
            {
                "id":        t["id"],
                "speed":     t.get("speed", 0.0),
                "direction": t.get("direction", 0.0),
            }
            for t in tracks if t["zone"] == zone
        ]

        zone_alerts = detector.process_frame(frame, zone=zone,
                                             tracks=zone_tracks,
                                             person_count=count)

        if zone_alerts:
            alertes += zone_alerts
        else:
            # Cas normal : aucune anomalie détectée dans cette zone
            alertes.append(Alert(
                level="info",
                zone=zone,
                type_anomalie="normal",
                timestamp=now,
                confiance=1.0,
                detail=f"{count} personne(s) — flux normal",
            ))

    return alertes


def afficher_rapport(in_count: int, out_count: int, alertes: list):
    """
    Affiche un rapport console horodaté avec couleurs.
    Vert si aucune anomalie, coloré selon le niveau sinon.

    Args:
        in_count  : personnes entrées (cumulé)
        out_count : personnes sorties (cumulé)
        alertes   : liste d'Alert de la frame courante
    """
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'─'*70}")
    print(f"  {ts}  |  Entrees: {in_count}  |  Sorties: {out_count}  |  "
          f"Actives: {in_count - out_count}")
    print(f"{'─'*70}")

    if alertes:
        for alert in alertes:
            print(f"  {alert}")
    else:
        print(f"  {VERT}✅ Situation normale — aucune anomalie détectée{RESET}")


def lancer_surveillance(source: str):
    """
    Boucle principale de surveillance en temps réel.
    Consomme stream_frames(), analyse chaque frame et affiche
    les rapports à intervalle régulier.

    Args:
        source : URL ou chemin vidéo du flux à surveiller
    """
    detector        = AnomalyDetector(fps=25.0, zone_area_m2=100.0, frame_skip=2)
    dernier_rapport = time.time()

    print(f"[INFO] Démarrage surveillance — {source}")
    print("-" * 70)

    frame_idx = 0
    for frame, in_count, out_count, zone_counts, tracks in stream_frames(source):
        frame_idx += 1
        alertes    = analyser_frame(detector, frame, zone_counts, tracks)

        if time.time() - dernier_rapport >= INTERVALLE_RAPPORT:
            afficher_tableau_bord(in_count, out_count, frame_idx, alertes)
            dernier_rapport = time.time()


# ─────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    lancer_surveillance(PHONE_STREAM)
