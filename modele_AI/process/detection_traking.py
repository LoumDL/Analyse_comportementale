import cv2
from ultralytics import YOLO, solutions
from indicateurs import calculer_densite_flux

# ─────────────────────────────────────────────
# CONSTANTES ZONES
# ─────────────────────────────────────────────
ZONE_LABELS = ["A", "B", "C", "D"]   # haut-gauche, haut-droit, bas-gauche, bas-droit


# ─────────────────────────────────────────────
# LOCALISATION PAR ZONE
# ─────────────────────────────────────────────

def assigner_zone(cx: float, cy: float, frame_w: int, frame_h: int) -> str:
    """
    Assigne une zone A/B/C/D à une personne selon sa position dans le cadre.

    Découpage du cadre en 4 quadrants :
        A = haut-gauche  | B = haut-droit
        C = bas-gauche   | D = bas-droit

    Args:
        cx, cy   : centre de la bounding box (coordonnées pixel)
        frame_w  : largeur du cadre
        frame_h  : hauteur du cadre
    Returns:
        lettre de zone "A", "B", "C" ou "D"
    """
    col = 0 if cx < frame_w / 2 else 1
    row = 0 if cy < frame_h / 2 else 1
    return [["A", "B"], ["C", "D"]][row][col]


def compter_par_zone(boxes, frame_w: int, frame_h: int) -> dict:
    """
    Compte le nombre de personnes dans chaque zone A/B/C/D
    à partir des bounding boxes détectées.

    Args:
        boxes    : tenseur YOLO boxes.xyxy (coordonnées x1,y1,x2,y2)
        frame_w  : largeur du cadre
        frame_h  : hauteur du cadre
    Returns:
        {"A": int, "B": int, "C": int, "D": int}
    """
    counts = {z: 0 for z in ZONE_LABELS}
    for box in boxes:
        x1, y1, x2, y2 = box[:4]
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        zone = assigner_zone(float(cx), float(cy), frame_w, frame_h)
        counts[zone] += 1
    return counts


def annoter_zones(frame, counts: dict) -> None:
    """
    Dessine la grille A/B/C/D et le comptage par zone directement sur le cadre.

    Args:
        frame  : image BGR (modifiée en place)
        counts : {"A": int, ...} retourné par compter_par_zone()
    """
    h, w = frame.shape[:2]
    mid_x, mid_y = w // 2, h // 2

    cv2.line(frame, (mid_x, 0),  (mid_x, h), (200, 200, 200), 1)
    cv2.line(frame, (0, mid_y),  (w, mid_y), (200, 200, 200), 1)

    positions = {
        "A": (10,         20),
        "B": (mid_x + 10, 20),
        "C": (10,         mid_y + 20),
        "D": (mid_x + 10, mid_y + 20),
    }
    for zone, pos in positions.items():
        cv2.putText(frame, f"Zone {zone}: {counts[zone]}",
                    pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 200), 2)


# ─────────────────────────────────────────────
# COMPTAGE GLOBAL (avec ObjectCounter)
# ─────────────────────────────────────────────

def count_persons(video_path: str):
    """
    Compte les personnes et affiche densité, flux et répartition par zone.

    Args:
        video_path : chemin vidéo ou URL flux caméra
    """
    model         = YOLO("yolo26n.pt")
    region_points = [(20, 400), (1080, 400), (1080, 360), (20, 360)]

    counter = solutions.ObjectCounter(
        show=True,
        region=region_points,
        model="yolo26n.pt",
        classes=[0],
    )

    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"Erreur : impossible d'ouvrir '{video_path}'"

    frame_idx = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_idx += 1
        h, w = frame.shape[:2]

        # Comptage global (entrées/sorties)
        results   = counter(frame)
        in_count  = results.in_count
        out_count = results.out_count

        # Localisation par zone via YOLO.track()
        track_res  = model.track(frame, persist=True, classes=[0], verbose=False)
        zone_counts = {z: 0 for z in ZONE_LABELS}
        if track_res and track_res[0].boxes is not None:
            zone_counts = compter_par_zone(track_res[0].boxes.xyxy.cpu().numpy(), w, h)

        df = calculer_densite_flux(in_count, out_count, frame_idx)
        print(f"Frame {frame_idx:04d} | "
              f"Entrees: {in_count} | Sorties: {out_count} | "
              f"Actives: {df['personnes_actives']} | "
              f"Densité: {df['densite']:.3f}/m² | "
              f"Flux net: {df['flux_net']:+.1f} pers/min | "
              f"Zones: A={zone_counts['A']} B={zone_counts['B']} "
              f"C={zone_counts['C']} D={zone_counts['D']}")

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ─────────────────────────────────────────────
# GÉNÉRATEUR AVEC ZONES — utilisé par les autres modules
# ─────────────────────────────────────────────

def stream_frames(source: str):
    """
    Générateur qui produit les données de comptage + localisation par zone
    frame par frame, sans bloquer l'appelant.

    Câble la localisation A/B/C/D au tracker YOLO :
        - ObjectCounter → in_count / out_count globaux
        - YOLO.track()  → positions individuelles → zone par personne

    Args:
        source : chemin vidéo ou URL flux
    Yields:
        (frame, in_count, out_count, zone_counts, tracks)

        zone_counts : {"A": int, "B": int, "C": int, "D": int}
        tracks      : [{"id": int, "cx": float, "cy": float, "zone": str}, ...]
    """
    model         = YOLO("yolo26n.pt")
    region_points = [(20, 400), (1080, 400), (1080, 360), (20, 360)]

    counter = solutions.ObjectCounter(
        show=False,
        region=region_points,
        model="yolo26n.pt",
        classes=[0],
    )

    cap = cv2.VideoCapture(source)
    assert cap.isOpened(), f"Erreur : impossible d'ouvrir '{source}'"

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        h, w = frame.shape[:2]

        # ── Comptage global (entrées / sorties) ──────────────────────────
        counter_res = counter(frame)
        in_count    = counter_res.in_count
        out_count   = counter_res.out_count

        # ── Tracking individuel + localisation par zone ───────────────────
        track_res   = model.track(frame, persist=True, classes=[0], verbose=False)
        zone_counts = {z: 0 for z in ZONE_LABELS}
        tracks      = []

        if track_res and track_res[0].boxes is not None:
            boxes = track_res[0].boxes
            ids   = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else []
            xyxy  = boxes.xyxy.cpu().numpy()

            for i, box in enumerate(xyxy):
                x1, y1, x2, y2 = box[:4]
                cx   = float((x1 + x2) / 2)
                cy   = float((y1 + y2) / 2)
                zone = assigner_zone(cx, cy, w, h)
                zone_counts[zone] += 1

                track_id = int(ids[i]) if i < len(ids) else -1
                tracks.append({"id": track_id, "cx": cx, "cy": cy, "zone": zone})

        yield frame, in_count, out_count, zone_counts, tracks

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    PHONE_STREAM = "http://192.168.137.228:4747/video"
    count_persons(PHONE_STREAM)
