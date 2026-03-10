

import cv2
from ultralytics import solutions


def track_and_count_persons(video_path: str, output_path: str = "object_counting_output.avi"):
    """
    Détecte, suit et compte les personnes dans une vidéo en utilisant YOLO + ObjectCounter.

    Args:
        video_path  : chemin vers la vidéo source.
        output_path : chemin du fichier vidéo de sortie annoté.
    """
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"Erreur : impossible d'ouvrir la vidéo '{video_path}'"

    region_points = [(20, 400), (1080, 400), (1080, 360), (20, 360)]  # zone rectangulaire

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    video_writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
    )

    counter = solutions.ObjectCounter(
        show=True,
        region=region_points,
        model="yolo26n.pt",
        classes=[0],  # classe 0 = personne (COCO)
    )

    print(f"[INFO] Traitement de '{video_path}'...")

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            print("[INFO] Fin de la vidéo ou frame vide.")
            break

        results = counter(frame)
        video_writer.write(results.plot_im)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Arrêt demandé par l'utilisateur.")
            break

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Vidéo annotée sauvegardée dans '{output_path}'")



def generate_person_heatmap(video_path: str, output_path: str = "heatmap_output.avi",
                            colormap: int = cv2.COLORMAP_PARULA,
                            classes: list = None, region_points: list = None):
    """
    Génère une heatmap des déplacements/densité de personnes dans une vidéo.

    Args:
        video_path     : chemin vers la vidéo source.
        output_path    : chemin du fichier vidéo de sortie annoté.
        colormap       : colormap OpenCV utilisée pour la heatmap (défaut: COLORMAP_PARULA).
        classes        : liste des classes à analyser, ex: [0] pour personnes. None = toutes.
        region_points  : points définissant une région de comptage (optionnel).
    """
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"Erreur : impossible d'ouvrir la vidéo '{video_path}'"

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    video_writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
    )

    heatmap_kwargs = dict(
        show=True,
        model="yolo26n.pt",
        colormap=colormap,
    )
    if classes is not None:
        heatmap_kwargs["classes"] = classes
    if region_points is not None:
        heatmap_kwargs["region"] = region_points

    heatmap = solutions.Heatmap(**heatmap_kwargs)

    print(f"[INFO] Génération de la heatmap pour '{video_path}'...")

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            print("[INFO] Fin de la vidéo ou frame vide.")
            break

        results = heatmap(frame)
        video_writer.write(results.plot_im)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Arrêt demandé par l'utilisateur.")
            break

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Heatmap sauvegardée dans '{output_path}'")


if __name__ == "__main__":
    track_and_count_persons("video illustration foule.mp4")
    #generate_person_heatmap("video illustration foule.mp4", classes=[0])
