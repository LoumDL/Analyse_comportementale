import sys
import os
import threading

# Ajoute le dossier process/ au chemin de recherche Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "process"))

from detection_traking import count_persons
from detection_anamalie import lancer_surveillance
from prediction_gestion import lancer_prediction


# ─────────────────────────────────────────────
# CONFIGURATION DES SITES
# ─────────────────────────────────────────────
# Ajouter / retirer des sites ici.
# "source" : chemin fichier, webcam (0), ou URL IP-Webcam/DroidCam
# "mode"   : "tracking" | "anomalie" | "prediction"

SITES = [
    {"nom": "Stade principal",   "source": "foule.mp4",                       "mode": "prediction"},
    {"nom": "Entrée nord",       "source": "http://192.168.1.101:4747/video", "mode": "anomalie"},
    {"nom": "Zone VIP",          "source": "http://192.168.1.102:4747/video", "mode": "tracking"},
]

# ─────────────────────────────────────────────
# DISPATCH PAR MODE
# ─────────────────────────────────────────────

MODE_FONCTIONS = {
    "tracking":   count_persons,
    "anomalie":   lancer_surveillance,
    "prediction": lancer_prediction,
}


def lancer_site(site: dict):
    """Lance la surveillance d'un site dans son thread."""
    nom    = site["nom"]
    source = site["source"]
    mode   = site["mode"]
    fn     = MODE_FONCTIONS.get(mode)

    if fn is None:
        print(f"[ERREUR] Mode inconnu pour le site '{nom}' : {mode}")
        return

    print(f"[INFO] Démarrage site '{nom}' | mode={mode} | source={source}")
    try:
        fn(source)
    except Exception as e:
        print(f"[ERREUR] Site '{nom}' arrêté : {e}")


# ─────────────────────────────────────────────
# POINT D'ENTRÉE MULTI-SITES
# ─────────────────────────────────────────────

if __name__ == "__main__":
    threads = []

    for site in SITES:
        t = threading.Thread(target=lancer_site, args=(site,), name=site["nom"], daemon=True)
        threads.append(t)
        t.start()

    print(f"[INFO] {len(threads)} site(s) en surveillance. Appuyez sur Ctrl+C pour arrêter.")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[INFO] Arrêt demandé — fermeture de tous les sites.")
