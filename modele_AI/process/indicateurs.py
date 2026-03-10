"""
INDICATEURS PARTAGÉS — JOJ Dakar 2026
======================================
Module transversal utilisé par :
    - detection_traking.py   → densité et flux en temps réel
    - detection_anamalie.py  → indicateurs de risque par frame
    - prediction_gestion.py  → indicateurs de capacité préventifs

Trois blocs d'indicateurs :
    1. Densité foule & flux  — mesure instantanée de la charge
    2. Indicateurs de risque — score et niveau (FAIBLE → CRITIQUE)
    3. Indicateurs de capacité — taux d'occupation et temps avant saturation
"""

from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION SITE JOJ
# ─────────────────────────────────────────────
SURFACE_TOTALE_M2  = 500.0   # surface totale surveillée en m²
CAPACITE_MAX       = 2000    # capacité maximale du site (personnes)
DENSITE_CONFORT    = 1.5     # pers/m² — foule confortable
DENSITE_DENSE      = 3.0     # pers/m² — foule dense
DENSITE_CRITIQUE   = 4.0     # pers/m² — surcompression

# Couleurs ANSI
VERT   = "\033[92m"
JAUNE  = "\033[93m"
ORANGE = "\033[33m"
ROUGE  = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
GRAS   = "\033[1m"


# ─────────────────────────────────────────────
# 1. DENSITÉ FOULE & FLUX
# ─────────────────────────────────────────────

def calculer_densite_flux(in_count: int, out_count: int,
                           frame_idx: int, fps: float = 25.0) -> dict:
    """
    Calcule les indicateurs de densité et de flux à partir des comptages.

    Indicateurs produits :
        - personnes_actives : personnes présentes sur le site (in - out)
        - densite           : pers/m² sur la surface totale surveillée
        - flux_entrant      : pers/min entrant (moyenne cumulée)
        - flux_sortant      : pers/min sortant (moyenne cumulée)
        - flux_net          : flux_entrant - flux_sortant
        - temps_ecoule_min  : durée de la session en minutes

    Args:
        in_count  : compteur cumulé d'entrées
        out_count : compteur cumulé de sorties
        frame_idx : indice de frame courant
        fps       : fréquence d'images
    Returns:
        dict avec tous les indicateurs de densité et flux
    """
    temps_ecoule_s  = frame_idx / max(fps, 1)
    temps_ecoule_min = temps_ecoule_s / 60.0

    actives      = max(0, in_count - out_count)
    densite      = actives / SURFACE_TOTALE_M2
    flux_entrant = (in_count  / temps_ecoule_min) if temps_ecoule_min > 0 else 0.0
    flux_sortant = (out_count / temps_ecoule_min) if temps_ecoule_min > 0 else 0.0

    return {
        "personnes_actives":  actives,
        "densite":            round(densite, 3),
        "flux_entrant":       round(flux_entrant, 1),
        "flux_sortant":       round(flux_sortant, 1),
        "flux_net":           round(flux_entrant - flux_sortant, 1),
        "temps_ecoule_min":   round(temps_ecoule_min, 1),
    }


def afficher_densite_flux(df: dict):
    """
    Affiche les indicateurs de densité et flux avec couleurs adaptées.

    Args:
        df : dict retourné par calculer_densite_flux()
    """
    d = df["densite"]
    if d < DENSITE_CONFORT:
        couleur_dens, label_dens = VERT,   "FLUIDE"
    elif d < DENSITE_DENSE:
        couleur_dens, label_dens = JAUNE,  "DENSE"
    elif d < DENSITE_CRITIQUE:
        couleur_dens, label_dens = ORANGE, "SERRÉ"
    else:
        couleur_dens, label_dens = ROUGE,  "CRITIQUE"

    flux_net = df["flux_net"]
    couleur_flux = VERT if flux_net <= 0 else (JAUNE if flux_net < 20 else ROUGE)

    print(f"\n  {GRAS}{CYAN}── DENSITÉ & FLUX ─────────────────────────────────{RESET}")
    print(f"  Personnes actives : {GRAS}{df['personnes_actives']}{RESET}")
    print(f"  Densité           : {couleur_dens}{GRAS}{d:.3f} pers/m²  [{label_dens}]{RESET}")
    print(f"  Flux entrant      : {df['flux_entrant']:.1f} pers/min")
    print(f"  Flux sortant      : {df['flux_sortant']:.1f} pers/min")
    print(f"  Flux net          : {couleur_flux}{flux_net:+.1f} pers/min{RESET}  "
          f"({'accumulation' if flux_net > 0 else 'dispersion'})")
    print(f"  Session           : {df['temps_ecoule_min']:.1f} min")


# ─────────────────────────────────────────────
# 2. INDICATEURS DE RISQUE
# ─────────────────────────────────────────────

def calculer_risque(densite: float, flux_net: float, nb_alertes: int,
                    nb_critical: int) -> dict:
    """
    Calcule un score de risque global (0–100) et son niveau associé.

    Composition du score :
        - 40 pts : densité (0 → DENSITE_CRITIQUE)
        - 30 pts : flux net entrant (accumulation rapide)
        - 30 pts : alertes actives (pondérées par criticité)

    Niveaux :
        0–24   → FAIBLE   🟢
        25–49  → MODÉRÉ   🟡
        50–74  → ÉLEVÉ    🟠
        75–100 → CRITIQUE 🔴

    Args:
        densite    : densité courante (pers/m²)
        flux_net   : flux net entrant (pers/min)
        nb_alertes : nombre total d'alertes actives
        nb_critical: nombre d'alertes de niveau "critical"
    Returns:
        dict avec score, niveau, couleur, recommandation
    """
    score_densite = min(40, (densite / DENSITE_CRITIQUE) * 40)
    score_flux    = min(30, max(0, flux_net / 2.0))
    score_alertes = min(30, nb_critical * 10 + (nb_alertes - nb_critical) * 4)
    score         = int(score_densite + score_flux + score_alertes)

    if score < 25:
        niveau, couleur, icone = "FAIBLE",   VERT,   "🟢"
        reco = "Surveillance normale."
    elif score < 50:
        niveau, couleur, icone = "MODÉRÉ",   JAUNE,  "🟡"
        reco = "Surveiller l'évolution — renforcer les équipes aux entrées."
    elif score < 75:
        niveau, couleur, icone = "ÉLEVÉ",    ORANGE, "🟠"
        reco = "Activer le protocole de gestion de foule — limiter les entrées."
    else:
        niveau, couleur, icone = "CRITIQUE", ROUGE,  "🔴"
        reco = "URGENCE — déclencher évacuation partielle et fermer les accès."

    return {
        "score":           score,
        "niveau":          niveau,
        "couleur":         couleur,
        "icone":           icone,
        "recommandation":  reco,
    }


def afficher_risque(risque: dict):
    """
    Affiche les indicateurs de risque dans la console.

    Args:
        risque : dict retourné par calculer_risque()
    """
    c = risque["couleur"]
    barre_pleine = int(risque["score"] / 5)   # barre sur 20 caractères
    barre = "█" * barre_pleine + "░" * (20 - barre_pleine)

    print(f"\n  {GRAS}{CYAN}── INDICATEURS DE RISQUE ──────────────────────────{RESET}")
    print(f"  Score global : {c}{GRAS}{risque['score']:3d}/100{RESET}  "
          f"{c}[{barre}]{RESET}")
    print(f"  Niveau       : {c}{GRAS}{risque['icone']} {risque['niveau']}{RESET}")
    print(f"  Action       : {c}{risque['recommandation']}{RESET}")


# ─────────────────────────────────────────────
# 3. INDICATEURS DE CAPACITÉ
# ─────────────────────────────────────────────

def calculer_capacite(actives: int, flux_entrant: float) -> dict:
    """
    Calcule le taux d'occupation et le temps estimé avant saturation.

    Indicateurs produits :
        - taux_occupation    : % de la capacité maximale utilisée
        - places_disponibles : CAPACITE_MAX - actives
        - temps_saturation   : minutes avant saturation si flux_entrant constant
                               (None si pas d'accumulation)
        - statut             : "OK" | "ATTENTION" | "PLEIN" | "SATURÉ"

    Args:
        actives      : personnes actuellement présentes
        flux_entrant : pers/min entrant actuellement
    Returns:
        dict avec indicateurs de capacité
    """
    taux       = min(100.0, (actives / CAPACITE_MAX) * 100)
    disponibles = max(0, CAPACITE_MAX - actives)

    if flux_entrant > 0 and disponibles > 0:
        temps_sat = round(disponibles / flux_entrant, 1)
    else:
        temps_sat = None

    if taux < 50:
        statut, couleur = "OK",        VERT
    elif taux < 75:
        statut, couleur = "ATTENTION", JAUNE
    elif taux < 95:
        statut, couleur = "PLEIN",     ORANGE
    else:
        statut, couleur = "SATURÉ",    ROUGE

    return {
        "taux_occupation":    round(taux, 1),
        "places_disponibles": disponibles,
        "temps_saturation":   temps_sat,
        "statut":             statut,
        "couleur":            couleur,
    }


def afficher_capacite(cap: dict):
    """
    Affiche les indicateurs de capacité dans la console.

    Args:
        cap : dict retourné par calculer_capacite()
    """
    c    = cap["couleur"]
    taux = cap["taux_occupation"]
    barre_pleine = int(taux / 5)
    barre = "█" * barre_pleine + "░" * (20 - barre_pleine)

    sat_txt = (f"{cap['temps_saturation']} min" if cap["temps_saturation"]
               else "indéterminé")

    print(f"\n  {GRAS}{CYAN}── INDICATEURS DE CAPACITÉ ────────────────────────{RESET}")
    print(f"  Occupation   : {c}{GRAS}{taux:.1f}%{RESET}  {c}[{barre}]{RESET}  "
          f"({CAPACITE_MAX} pers. max)")
    print(f"  Disponibles  : {c}{cap['places_disponibles']} places{RESET}")
    print(f"  Statut site  : {c}{GRAS}{cap['statut']}{RESET}")
    print(f"  Saturation   : dans {sat_txt} au rythme actuel")


# ─────────────────────────────────────────────
# AFFICHAGE COMPLET (les 3 blocs ensemble)
# ─────────────────────────────────────────────

def afficher_tableau_bord(in_count: int, out_count: int,
                           frame_idx: int, alertes: list,
                           fps: float = 25.0):
    """
    Affiche le tableau de bord complet : densité/flux + risque + capacité.
    Fonction centrale appelable depuis les 3 modules.

    Args:
        in_count  : compteur cumulé d'entrées
        out_count : compteur cumulé de sorties
        frame_idx : indice de frame courant
        alertes   : liste d'Alert du module detection_anamalie
        fps       : fréquence d'images
    """
    ts = datetime.now().strftime("%H:%M:%S")

    df     = calculer_densite_flux(in_count, out_count, frame_idx, fps)
    nb_crit = sum(1 for a in alertes if hasattr(a, "level") and a.level == "critical")
    risque  = calculer_risque(df["densite"], df["flux_net"], len(alertes), nb_crit)
    cap     = calculer_capacite(df["personnes_actives"], df["flux_entrant"])

    print(f"\n{'═'*54}")
    print(f"  {GRAS}TABLEAU DE BORD JOJ DAKAR 2026  [{ts}]{RESET}")
    print(f"{'═'*54}")

    afficher_densite_flux(df)
    afficher_risque(risque)
    afficher_capacite(cap)

    print(f"\n  {GRAS}{CYAN}── ALERTES ACTIVES ─────────────────────────────────{RESET}")
    if alertes:
        for a in alertes:
            print(f"    {a}")
    else:
        print(f"    {VERT}✅ Aucune anomalie détectée.{RESET}")

    print(f"{'═'*54}")
