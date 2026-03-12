import cv2
import math
from ultralytics import YOLO

# ─────────────────────────────────────────────
# CONSTANTES ZONES
# ─────────────────────────────────────────────
ZONE_LABELS = ["A", "B", "C", "D"]   # haut-gauche, haut-droit, bas-gauche, bas-droit


# ─────────────────────────────────────────────
# LOCALISATION PAR ZONE
# ─────────────────────────────────────────────

def assigner_zone(cx: float, cy: float, frame_w: int, frame_h: int) -> str:
    col = 0 if cx < frame_w / 2 else 1
    row = 0 if cy < frame_h / 2 else 1
    return [["A", "B"], ["C", "D"]][row][col]


# ─────────────────────────────────────────────
# GÉNÉRATEUR PRINCIPAL — utilisé par api.py
# ─────────────────────────────────────────────

def stream_frames(source: str):
    """
    Générateur frame par frame : une seule inférence YOLO par frame.
    in_count / out_count sont estimés via suivi des IDs actifs.

    Yields:
        (frame, in_count, out_count, zone_counts, tracks)
    """
    model = YOLO("yolo26n.pt")

    cap = cv2.VideoCapture(source)
    assert cap.isOpened(), f"Erreur : impossible d'ouvrir '{source}'"

    INFER_W        = 640
    prev_positions: dict = {}   # {track_id: (cx, cy)}
    seen_ids:       set  = set()
    lost_ids:       set  = set()

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        h, w = frame.shape[:2]

        # Resize pour l'inférence
        scale   = INFER_W / w
        infer_h = int(h * scale)
        small   = cv2.resize(frame, (INFER_W, infer_h))

        # ── Une seule inférence YOLO ──────────────────────────────────────
        track_res   = model.track(small, persist=True, classes=[0], verbose=False)
        zone_counts = {z: 0 for z in ZONE_LABELS}
        tracks      = []
        current_ids: set = set()

        if track_res and track_res[0].boxes is not None:
            boxes = track_res[0].boxes
            ids   = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else []
            xyxy  = boxes.xyxy.cpu().numpy()

            for i, box in enumerate(xyxy):
                x1, y1, x2, y2 = box[:4]
                cx       = float((x1 + x2) / 2) / scale
                cy       = float((y1 + y2) / 2) / scale
                zone     = assigner_zone(cx, cy, w, h)
                zone_counts[zone] += 1
                track_id = int(ids[i]) if i < len(ids) else -1
                current_ids.add(track_id)

                # Vitesse et direction
                speed     = 0.0
                direction = 0.0
                if track_id in prev_positions:
                    px, py = prev_positions[track_id]
                    dx     = cx - px
                    dy     = cy - py
                    speed  = math.hypot(dx, dy)
                    if speed > 0.5:
                        direction = math.degrees(math.atan2(dy, dx)) % 360
                prev_positions[track_id] = (cx, cy)

                tracks.append({
                    "id": track_id, "cx": cx, "cy": cy,
                    "zone": zone, "speed": speed, "direction": direction,
                })

        # in/out estimés par apparition/disparition d'IDs
        new_ids  = current_ids - seen_ids
        gone_ids = set(prev_positions.keys()) - current_ids
        seen_ids |= new_ids
        lost_ids |= gone_ids

        # Nettoyage mémoire
        prev_positions = {k: v for k, v in prev_positions.items() if k in current_ids}

        yield frame, len(seen_ids), len(lost_ids), zone_counts, tracks

    cap.release()


if __name__ == "__main__":
    PHONE_STREAM = "http://192.168.2.108:4747/video"
    for frame, inc, outc, zones, tracks in stream_frames(PHONE_STREAM):
        print(f"in={inc} out={outc} zones={zones} tracks={len(tracks)}")
