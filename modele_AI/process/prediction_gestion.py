"""
MODULE 3 — PRÉDICTION DE CONGESTION
=====================================
Système d'analyse comportementale des foules — JOJ Dakar 2026

Objectif : Anticiper les surcharges 5 / 10 / 15 minutes avant qu'elles arrivent.

Modèle     : TimeGPT (Nixtla) — modèle pré-entraîné, zéro donnée d'entraînement requise
             Entraîné sur des milliards de séries temporelles → prêt à l'emploi immédiat
Features   : historique de densité par zone (série temporelle)
Sorties    : densité prédite à +5min, +10min, +15min par zone
Seuil      : densité prédite > 3.5 pers/m² → ⚠️ ATTENTION PRÉVENTIVE
API        : clé gratuite sur https://dashboard.nixtla.io/
"""

import time
import math
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
import dotenv # type: ignore
import os 

from nixtla import NixtlaClient
from indicateurs import calculer_densite_flux, calculer_risque, calculer_capacite, afficher_tableau_bord


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

dotenv.load_dotenv()  # charge NIXTLA_API_KEY depuis .

# Clé API TimeGPT — obtenir gratuitement sur https://dashboard.nixtla.io/
NIXTLA_API_KEY = os.getenv('NIXTLA_API_KEY')  # Load API key from environment variable

ZONES           = ["A", "B", "C", "D", "G"]
FENETRE_MIN     = 15         # minimum d'historique requis par TimeGPT
HORIZON_PRED    = [5, 10, 15]  # prédictions en minutes
SEUIL_PREVENTIF = 3.5        # pers/m²
PAS_SECONDES    = 60         # 1 observation par minute

METEO_API_URL   = "https://api.open-meteo.com/v1/forecast"
METEO_LAT       = 14.6928    # Dakar
METEO_LON       = -17.4467


# ─────────────────────────────────────────────
# MÉTÉO
# ─────────────────────────────────────────────

def get_meteo() -> tuple:
    """
    Récupère température et humidité à Dakar via Open-Meteo (gratuit, sans clé).
    Retourne (30.0, 70.0) si pas de connexion.

    Returns:
        (temperature_celsius, humidite_pct)
    """
    try:
        params = {
            "latitude":  METEO_LAT,
            "longitude": METEO_LON,
            "current":   "temperature_2m,relative_humidity_2m",
            "timezone":  "Africa/Dakar",
        }
        data = requests.get(METEO_API_URL, params=params, timeout=3).json()["current"]
        return float(data["temperature_2m"]), float(data["relative_humidity_2m"])
    except Exception:
        return 30.0, 70.0


# ─────────────────────────────────────────────
# ALERTES PRÉVENTIVES
# ─────────────────────────────────────────────

def generer_alertes_preventives(predictions: dict) -> list:
    """
    Génère des alertes colorées si la densité prédite dépasse le seuil.

    Args:
        predictions : {"A": {5: float, 10: float, 15: float}, ...}
    Returns:
        liste de strings colorées
    """
    JAUNE, ROUGE, RESET = "\033[93m", "\033[91m", "\033[0m"
    alertes = []
    ts      = datetime.now().strftime("%H:%M:%S")

    for zone, horizons in predictions.items():
        for minutes, densite in horizons.items():
            if densite >= SEUIL_PREVENTIF:
                niveau = ROUGE if densite >= 4.0 else JAUNE
                icone  = "🔴" if densite >= 4.0 else "⚠️"
                alertes.append(
                    f"{niveau}{icone} [{ts}] PREVENTIF | Zone {zone} | "
                    f"+{minutes}min | densité prédite = {densite:.2f} pers/m²{RESET}"
                )
    return alertes


# ─────────────────────────────────────────────
# PRÉDICTEUR TIMEGPT
# ─────────────────────────────────────────────

class CongestionPredictor:
    """
    Prédit la densité de foule à +5, +10, +15 minutes par zone avec TimeGPT.

    TimeGPT est un modèle fondation pré-entraîné sur des milliards de séries
    temporelles — aucun entraînement local requis, appel API direct.

    Utilisation :
        predictor = CongestionPredictor()
        predictor.ajouter_observation(zone_data)   # chaque minute
        predictions = predictor.predire()
        alertes     = generer_alertes_preventives(predictions)
    """

    def __init__(self):
        self.client     = NixtlaClient(api_key=NIXTLA_API_KEY)
        self.historique = {z: deque(maxlen=60) for z in ZONES}  # 60 min max
        self.timestamps = deque(maxlen=60)
        print("[INFO] TimeGPT initialisé.")

    def ajouter_observation(self, zone_data: dict):
        """
        Ajoute une observation à l'historique de chaque zone.
        À appeler toutes les 60 secondes.

        Args:
            zone_data : {"A": {"density": float}, "B": {...}, ...}
        """
        ts = datetime.now().replace(second=0, microsecond=0)
        self.timestamps.append(ts)

        for z in ZONES:
            densite = zone_data.get(z, {}).get("density", 0.0)
            self.historique[z].append(densite)

    def _construire_dataframe(self, zone: str) -> pd.DataFrame:
        """
        Construit le DataFrame au format attendu par TimeGPT.

        Format requis :
            - colonne 'ds'       : timestamps (datetime)
            - colonne 'y'        : valeur de la série (densité)
            - colonne 'unique_id': identifiant de la série

        Args:
            zone : identifiant de zone
        Returns:
            DataFrame pandas
        """
        valeurs = list(self.historique[zone])
        ts_list = list(self.timestamps)[-len(valeurs):]

        return pd.DataFrame({
            "unique_id": zone,
            "ds":        ts_list,
            "y":         valeurs,
        })

    def predire(self) -> dict:
        """
        Appelle l'API TimeGPT pour prédire la densité à +5, +10, +15 min.
        Retourne un dict vide si l'historique est insuffisant (< FENETRE_MIN points).

        Returns:
            {"A": {5: float, 10: float, 15: float}, "B": {...}, ...}
            ou {} si pas assez d'historique
        """
        if len(self.timestamps) < FENETRE_MIN:
            return {}

        predictions = {z: {} for z in ZONES}
        horizon_max = max(HORIZON_PRED)   # prédire jusqu'à +15 min en un appel

        # Construire un DataFrame multi-séries (toutes les zones en un appel)
        dfs = [self._construire_dataframe(z) for z in ZONES]
        df_all = pd.concat(dfs, ignore_index=True)

        try:
            forecast = self.client.forecast(
                df=df_all,
                h=horizon_max,
                freq="min",
                time_col="ds",
                target_col="y",
                id_col="unique_id",
            )

            # Extraire les valeurs à +5, +10, +15 min
            for z in ZONES:
                df_z = forecast[forecast["unique_id"] == z].reset_index(drop=True)
                for h in HORIZON_PRED:
                    idx = h - 1   # index 0-based (h=5 → index 4)
                    if idx < len(df_z):
                        val = float(df_z.loc[idx, "TimeGPT"])
                        predictions[z][h] = max(0.0, val)
                    else:
                        predictions[z][h] = 0.0

        except Exception as e:
            print(f"[ERREUR] TimeGPT API : {e}")
            return {}

        return predictions


# ─────────────────────────────────────────────
# AFFICHAGE
# ─────────────────────────────────────────────

def afficher_predictions(predictions: dict):
    """
    Affiche les prédictions par zone et horizon avec couleurs.

    Args:
        predictions : dict retourné par CongestionPredictor.predire()
    """
    VERT, JAUNE, ROUGE, RESET = "\033[92m", "\033[93m", "\033[91m", "\033[0m"
    ts = datetime.now().strftime("%H:%M:%S")

    print(f"\n{'═'*70}")
    print(f"  PRÉDICTIONS TimeGPT [{ts}]")
    print(f"{'═'*70}")
    print(f"  {'Zone':<6} {'  +5min':>9} {'  +10min':>10} {'  +15min':>10}")
    print(f"  {'─'*38}")

    for zone, horizons in predictions.items():
        ligne = f"  {zone:<6}"
        for h in HORIZON_PRED:
            d = horizons.get(h, 0.0)
            c = ROUGE if d >= 4.0 else (JAUNE if d >= SEUIL_PREVENTIF else VERT)
            ligne += f" {c}{d:>8.2f}/m²{RESET}"
        print(ligne)

    alertes = generer_alertes_preventives(predictions)
    if alertes:
        print(f"\n  Alertes préventives :")
        for a in alertes:
            print(f"    {a}")
    else:
        print(f"\n  {VERT}✅ Aucune surcharge prévue dans les 15 prochaines minutes.{RESET}")


# ─────────────────────────────────────────────
# FONCTIONS DU PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def construire_zone_data(zone_counts: dict, in_count: int,
                         out_count: int, frame_idx: int) -> dict:
    """
    Construit zone_data à partir des comptages réels par zone
    issus de detection_traking.stream_frames().

    Args:
        zone_counts : {"A": int, "B": int, "C": int, "D": int} — comptage réel par zone
        in_count    : personnes entrées (cumulé global)
        out_count   : personnes sorties (cumulé global)
        frame_idx   : indice de frame courant
    Returns:
        dict zone_data compatible avec ajouter_observation()
    """
    in_rate  = in_count  / max(1, frame_idx)
    out_rate = out_count / max(1, frame_idx)

    zone_data = {}
    for z in ZONES:
        count = zone_counts.get(z, 0)
        zone_data[z] = {
            "density":  count / 25.0,   # surface par zone = 25 m²
            "in_rate":  in_rate,
            "out_rate": out_rate,
        }
    # Zone globale G = total
    total = sum(zone_counts.get(z, 0) for z in ["A", "B", "C", "D"])
    zone_data["G"] = {
        "density":  total / 100.0,  # surface totale = 100 m²
        "in_rate":  in_rate,
        "out_rate": out_rate,
    }
    return zone_data


def lancer_prediction(source: str, intervalle_pred_min: float = 1.0):
    """
    Boucle principale de prédiction en temps réel.
    - Observation ajoutée toutes les 60 secondes
    - Prédiction affichée toutes les `intervalle_pred_min` minutes

    Args:
        source               : URL ou chemin vidéo
        intervalle_pred_min  : fréquence des appels TimeGPT (en minutes)
    """
    from detection_traking import stream_frames

    predictor         = CongestionPredictor()
    derniere_obs      = time.time()
    derniere_pred     = time.time()
    intervalle_pred_s = intervalle_pred_min * 60
    frame_idx         = 0

    print(f"[INFO] Démarrage prédiction TimeGPT — {source}")
    print(f"[INFO] Observation /60s | Prédiction /{intervalle_pred_min}min")
    print("-" * 70)

    for frame, in_count, out_count, zone_counts, _ in stream_frames(source):
        frame_idx += 1
        now = time.time()

        if now - derniere_obs >= PAS_SECONDES:
            zone_data = construire_zone_data(zone_counts, in_count, out_count, frame_idx)
            predictor.ajouter_observation(zone_data)
            derniere_obs = now

        if now - derniere_pred >= intervalle_pred_s:
            predictions = predictor.predire()
            if predictions:
                # Tableau de bord : densité/flux + risque + capacité
                afficher_tableau_bord(in_count, out_count, frame_idx, alertes=[])
                # Prédictions TimeGPT
                afficher_predictions(predictions)
            else:
                manquant = FENETRE_MIN - len(predictor.timestamps)
                # Afficher quand même les indicateurs temps réel
                afficher_tableau_bord(in_count, out_count, frame_idx, alertes=[])
                print(f"[INFO] Prédiction en attente — encore {manquant} observations requises.")
            derniere_pred = now


# ─────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    PHONE_STREAM = "http://192.168.137.228:4747/video"
    # PHONE_STREAM = "video illustration foule.mp4"

    lancer_prediction(
        source              = PHONE_STREAM,
        intervalle_pred_min = 1.0,
    )
