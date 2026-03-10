# Documentation technique — Système d'analyse comportementale JOJ Dakar 2026

---

## Architecture générale

```
test.py                 → tests isolés (comptage + heatmap)
detection_traking.py    → Module 1 : détection, tracking, localisation par zone
detection_anamalie.py   → Module 2 : détection d'anomalies comportementales
prediction_gestion.py   → Module 3 : prédiction de congestion TimeGPT
indicateurs.py          → Module partagé : indicateurs densité / risque / capacité
```

Flux de données :
```
flux vidéo → stream_frames() → analyser_frame() + construire_zone_data()
                                     ↓                      ↓
                            AnomalyDetector         CongestionPredictor
                                     ↓                      ↓
                            afficher_tableau_bord   afficher_predictions
```

---

## test.py

### `track_and_count_persons(video_path, output_path)`
Lit une vidéo, détecte et suit les personnes avec YOLO ObjectCounter, puis sauvegarde la vidéo annotée avec les comptages entrées/sorties.

**Params :** `video_path` — source vidéo ; `output_path` — fichier de sortie (défaut `object_counting_output.avi`)

**Fonctionnement :** Ouvre la vidéo → crée un `solutions.ObjectCounter` sur une zone rectangulaire fixe → boucle frame par frame → écrit chaque frame annotée → arrêt sur touche `q`.

---

### `generate_person_heatmap(video_path, output_path, colormap, classes, region_points)`
Génère une heatmap de densité/déplacement des personnes sur toute la durée de la vidéo.

**Params :** `colormap` — palette OpenCV (défaut `COLORMAP_PARULA`) ; `classes` — filtre par classe YOLO (défaut toutes) ; `region_points` — zone optionnelle.

**Fonctionnement :** Ouvre la vidéo → crée `solutions.Heatmap` → accumule la chaleur frame par frame → sauvegarde la vidéo colorée résultante.

---

## detection_traking.py — Module 1

### `assigner_zone(cx, cy, frame_w, frame_h) → str`
Détermine à quelle zone (A/B/C/D) appartient une personne selon la position du centre de sa bounding box dans le cadre.

**Logique :**
- Cadre divisé en 4 quadrants égaux par les lignes médianes horizontale et verticale.
- `A` = haut-gauche, `B` = haut-droit, `C` = bas-gauche, `D` = bas-droit.
- Une personne appartient à **une seule zone** (le centre tranche).

---

### `compter_par_zone(boxes, frame_w, frame_h) → dict`
Parcourt toutes les bounding boxes d'une frame et compte le nombre de personnes par zone.

**Entrée :** `boxes` — tenseur YOLO `boxes.xyxy` (x1, y1, x2, y2).
**Sortie :** `{"A": int, "B": int, "C": int, "D": int}`

---

### `annoter_zones(frame, counts) → None`
Dessine la grille A/B/C/D et le comptage par zone directement sur la frame (modification en place). Trace deux lignes grises (verticale + horizontale) puis écrit le label de chaque zone dans son coin.

---

### `count_persons(video_path)`
Boucle de comptage bloquante (usage autonome). Affiche frame par frame sur la console : entrées, sorties, personnes actives, densité, flux net, répartition par zone. Utilise `ObjectCounter` (in/out global) + `YOLO.track()` (positions individuelles).

> **Note :** Fonction autonome — ne pas importer depuis les autres modules. Utiliser `stream_frames()` à la place.

---

### `stream_frames(source) → generator`
Générateur non-bloquant central du projet. Produit les données de chaque frame à la demande, sans bloquer l'appelant.

**Double inférence par frame :**
1. `ObjectCounter` → `in_count` / `out_count` globaux (comptage de franchissement de ligne)
2. `YOLO.track()` → positions individuelles → zone A/B/C/D par personne

**Yield à chaque frame :**
```
(frame, in_count, out_count, zone_counts, tracks)

frame       : image BGR numpy
in_count    : int — personnes entrées (cumulé)
out_count   : int — personnes sorties (cumulé)
zone_counts : {"A": int, "B": int, "C": int, "D": int}
tracks      : [{"id": int, "cx": float, "cy": float, "zone": str}, ...]
```

**Arrêt :** fin de vidéo ou touche `q`.

---

## indicateurs.py — Module partagé

### `calculer_densite_flux(in_count, out_count, frame_idx, fps) → dict`
Calcule tous les indicateurs de densité et de flux à partir des comptages cumulés.

**Formules clés :**
- `personnes_actives = in_count - out_count`
- `densite = actives / 500 m²` (surface totale surveillée)
- `flux_entrant = in_count / temps_ecoule_min`

**Retourne :** `personnes_actives`, `densite`, `flux_entrant`, `flux_sortant`, `flux_net`, `temps_ecoule_min`

---

### `afficher_densite_flux(df)`
Affiche le bloc densité & flux en console avec couleurs adaptées à la charge :
- Vert → FLUIDE (< 1.5 pers/m²)
- Jaune → DENSE (< 3.0)
- Orange → SERRÉ (< 4.0)
- Rouge → CRITIQUE (≥ 4.0)

---

### `calculer_risque(densite, flux_net, nb_alertes, nb_critical) → dict`
Calcule un **score de risque global de 0 à 100** composé de trois contributions :
- 40 pts max → densité (proportionnel à DENSITE_CRITIQUE = 4.0)
- 30 pts max → flux net entrant (accumulation rapide)
- 30 pts max → alertes actives (× 10 pts/alerte critique, × 4 pts/alerte normale)

**Niveaux :** FAIBLE (0–24) → MODÉRÉ (25–49) → ÉLEVÉ (50–74) → CRITIQUE (75–100)

**Retourne :** `score`, `niveau`, `couleur`, `icone`, `recommandation`

---

### `afficher_risque(risque)`
Affiche le score de risque sous forme de barre de progression ASCII (20 caractères) colorée selon le niveau.

---

### `calculer_capacite(actives, flux_entrant) → dict`
Calcule le taux d'occupation et le temps estimé avant saturation du site.

**Formule saturation :** `places_disponibles / flux_entrant` (en minutes)

**Statuts :** OK (< 50%) → ATTENTION (< 75%) → PLEIN (< 95%) → SATURÉ (≥ 95%)

**Retourne :** `taux_occupation`, `places_disponibles`, `temps_saturation`, `statut`, `couleur`

---

### `afficher_capacite(cap)`
Affiche le taux d'occupation sous forme de barre de progression ASCII et le temps avant saturation.

---

### `afficher_tableau_bord(in_count, out_count, frame_idx, alertes, fps)`
**Fonction centrale** appelée par les trois modules. Agrège et affiche les trois blocs :
1. Densité & flux
2. Indicateurs de risque
3. Indicateurs de capacité
4. Liste des alertes actives (ou message vert si aucune)

---

## detection_anamalie.py — Module 2

### Dataclass `Alert`
Représente une alerte d'anomalie. Champs : `level` (info/warning/critical), `zone`, `type_anomalie`, `timestamp`, `confiance`, `detail`.

La méthode `__str__` formate l'alerte avec couleurs ANSI : jaune (info), orange (warning), rouge (critical).

---

### Dataclass `ZoneState`
État interne d'une zone : vitesses, directions, accélérations, densité, comptage, horodatage d'entrée. Sert de mémoire persistante entre les frames pour détecter les anomalies temporelles (arrêt de masse).

---

### `analyse_posture(keypoints, conf_threshold) → dict`
Analyse le squelette COCO-17 d'une personne pour détecter deux comportements anormaux :

| Indicateur | Logique |
|---|---|
| `bras_leves` | Au moins un poignet (idx 9 ou 10) au-dessus de l'épaule correspondante (Y pixel plus petit) |
| `au_sol` | Nez (idx 0) à moins de 40 px des hanches (idx 11-12) — hauteur corporelle effondrée |

Ignore les keypoints avec confiance < `conf_threshold` (défaut 0.4). Retourne aussi la confiance moyenne globale.

---

### `detect_pose_anomalies(zone, pose_results) → list[Alert]`
Agrège les résultats de `analyse_posture()` pour toutes les personnes d'une zone et génère des alertes :

- **panic** (CRITICAL) : ≥ 30% des personnes ont les bras levés
- **chute** (CRITICAL) : au moins 1 personne détectée au sol

La confiance de l'alerte est proportionnelle au pourcentage détecté.

---

### `detect_rules(zone, state) → list[Alert]`
Applique quatre règles métier sur les données de mouvement du `ZoneState` :

| Anomalie | Niveau | Déclencheur |
|---|---|---|
| surcompression | CRITICAL | densité > 4 pers/m² ET vitesse moyenne < 5 px/s |
| contre_flux | WARNING | > 30% des directions dévient de > 150° de la moyenne |
| arret_masse | WARNING | vitesse moy < 2 px/s pendant > 20 secondes consécutives |
| accumulation | INFO | > 50 personnes/min entrent dans la zone |

---

### `AnomalyDetector` (classe)
Orchestre YOLO-Pose + règles métier. Maintient un état par zone et un cache de résultats de pose.

**`__init__(fps, zone_area_m2, pose_model_path, frame_skip)`**
Charge le modèle YOLO-Pose (`yolo11n-pose.pt`). `frame_skip` permet de ne faire l'inférence pose que tous les N frames pour économiser le CPU.

**`process_frame(frame, zone, tracks, person_count) → list[Alert]`**
Pipeline complet pour une zone sur une frame :
1. Met à jour le `ZoneState` (densité, vitesses, directions, accélérations)
2. Exécute YOLO-Pose tous les `frame_skip` frames → cache `last_pose_results`
3. Appelle `detect_pose_anomalies()` sur le cache
4. Appelle `detect_rules()` sur l'état de mouvement
5. Dédoublonne (évite alertes panic en double pose + règle)
6. Retourne la liste consolidée d'alertes

---

### `analyser_frame(detector, frame, zone_counts, tracks) → list[Alert]`
Itère sur les zones A/B/C/D, filtre les tracks par zone et appelle `detector.process_frame()` pour chacune. Agrège toutes les alertes en une seule liste.

**Rôle :** Séparer la logique de dispatch par zone de la logique de détection dans `AnomalyDetector`.

---

### `afficher_rapport(in_count, out_count, alertes)`
Affiche un rapport console horodaté : comptages globaux + liste colorée des alertes. Affiche un message vert si aucune anomalie.

---

### `lancer_surveillance(source)`
**Point d'entrée du Module 2.** Boucle principale :
1. Consomme `stream_frames(source)` frame par frame
2. Appelle `analyser_frame()` à chaque frame
3. Appelle `afficher_tableau_bord()` toutes les 30 secondes (`INTERVALLE_RAPPORT`)

---

## prediction_gestion.py — Module 3

### `get_meteo() → (float, float)`
Interroge l'API Open-Meteo (gratuite, sans clé) pour obtenir la température et l'humidité à Dakar en temps réel. Retourne `(30.0, 70.0)` si pas de connexion.

---

### `generer_alertes_preventives(predictions) → list[str]`
Parcourt le dict de prédictions et génère des alertes colorées pour chaque zone et horizon dépassant le seuil `SEUIL_PREVENTIF = 3.5 pers/m²`.

- ≥ 4.0 pers/m² → rouge `🔴`
- ≥ 3.5 pers/m² → jaune `⚠️`

---

### `CongestionPredictor` (classe)

**`__init__()`**
Initialise le client TimeGPT (Nixtla) et les deques d'historique (60 observations max, soit 60 minutes).

**`ajouter_observation(zone_data)`**
Ajoute un point d'historique horodaté pour chaque zone. À appeler toutes les 60 secondes.

**`zone_data` attendu :**
```python
{"A": {"density": float, "in_rate": float, "out_rate": float}, ...}
```

**`_construire_dataframe(zone) → DataFrame`**
Construit le DataFrame au format TimeGPT pour une zone :
- colonne `unique_id` : identifiant de zone
- colonne `ds` : timestamps datetime
- colonne `y` : valeurs de densité

**`predire() → dict`**
Appelle l'API TimeGPT avec toutes les zones en un seul batch. Retourne les densités prédites à +5, +10 et +15 minutes.

Retourne `{}` si moins de 15 observations dans l'historique (`FENETRE_MIN`).

**Sortie :** `{"A": {5: float, 10: float, 15: float}, "B": {...}, ...}`

---

### `afficher_predictions(predictions)`
Affiche un tableau console avec les prédictions par zone et par horizon, colorées selon la densité prédite (vert / jaune / rouge). Appelle `generer_alertes_preventives()` pour les avertissements.

---

### `construire_zone_data(zone_counts, in_count, out_count, frame_idx) → dict`
Convertit les comptages bruts de `stream_frames()` en `zone_data` compatible avec `ajouter_observation()`.

- Densité par zone = `count / 25 m²`
- Zone globale G = total / 100 m²
- Taux entrée/sortie = comptages cumulés / frame_idx

---

### `lancer_prediction(source, intervalle_pred_min)`
**Point d'entrée du Module 3.** Boucle principale :
1. Consomme `stream_frames(source)` frame par frame
2. Toutes les 60 secondes : appelle `ajouter_observation()`
3. Toutes les `intervalle_pred_min` minutes : appelle `predire()` + affiche le tableau de bord + les prédictions
4. Affiche le nombre d'observations manquantes si l'historique est insuffisant

---

## Modèles utilisés

### 1. YOLOv26n — `yolo26n.pt`

| Propriété | Valeur |
|---|---|
| Fichier | `yolo26n.pt` (local) |
| Famille | Ultralytics YOLO |
| Tâche | Détection d'objets (bounding boxes) |
| Classe utilisée | `0` — personne (dataset COCO) |
| Utilisé dans | `detection_traking.py`, `test.py` |

**Rôle dans le projet :**
- `YOLO.track()` → tracking individuel par ByteTrack, produit un identifiant unique (`track_id`) par personne et les bounding boxes `xyxy` utilisées pour localiser chaque individu dans une zone A/B/C/D.
- `solutions.ObjectCounter` (basé sur le même modèle) → comptage de franchissement de la ligne de région → `in_count` / `out_count`.
- `solutions.Heatmap` → carte thermique de densité de passage.

**Format de sortie :**
```
boxes.xyxy   : tensor (N, 4) — coordonnées [x1, y1, x2, y2] par détection
boxes.id     : tensor (N,)   — identifiant de tracking par personne
```

**Documentation officielle :** https://docs.ultralytics.com/models/

---

### 2. YOLOv26n-Pose — `yolo26n-pose.pt`

| Propriété | Valeur |
|---|---|
| Fichier | `yolo26n-pose.pt` (local) |
| Famille | Ultralytics YOLO |
| Tâche | Estimation de pose (keypoints) |
| Squelette | COCO-17 keypoints |
| Utilisé dans | `detection_anamalie.py` |

**Rôle dans le projet :**
Détecte la posture de chaque personne dans la frame. Fournit 17 points articulaires (keypoints) avec leur position (x, y) et un score de confiance.

**Keypoints COCO-17 exploités :**

| Index | Articulation | Usage |
|---|---|---|
| 0 | Nez | Détection personne au sol |
| 5 | Épaule gauche | Référence bras levé |
| 6 | Épaule droite | Référence bras levé |
| 9 | Poignet gauche | Détection bras levé |
| 10 | Poignet droit | Détection bras levé |
| 11 | Hanche gauche | Détection personne au sol |
| 12 | Hanche droite | Détection personne au sol |

**Format de sortie :**
```
results[0].keypoints.data : tensor (N, 17, 3)
    N  = nombre de personnes détectées
    17 = nombre de keypoints COCO
    3  = [x, y, confiance]
```

**Fréquence d'inférence :** tous les `frame_skip = 2` frames (optimisation CPU). Le cache `last_pose_results` est réutilisé sur les frames intermédiaires.

**Documentation officielle :** https://docs.ultralytics.com/tasks/pose/

---

### 3. TimeGPT — Nixtla

| Propriété | Valeur |
|---|---|
| Fournisseur | Nixtla |
| Type | Modèle fondation pré-entraîné (zero-shot) |
| Tâche | Prédiction de séries temporelles |
| API | REST (clé gratuite sur https://dashboard.nixtla.io/) |
| Package Python | `nixtla` |
| Utilisé dans | `prediction_gestion.py` |

**Rôle dans le projet :**
Prédit la densité de foule par zone à +5, +10 et +15 minutes sans aucun entraînement local. TimeGPT est entraîné sur des milliards de séries temporelles — il s'utilise directement par appel API.

**Pourquoi TimeGPT plutôt qu'un autre modèle :**

| Modèle | Rejeté car |
|---|---|
| LSTM / Transformer maison | Nécessite TensorFlow/GPU, trop lourd sur CPU |
| LightGBM | Nécessite des données d'entraînement réelles |
| TimeGPT | Pré-entraîné, zéro donnée requise, appel API simple |

**Format d'entrée attendu :**
```python
DataFrame avec colonnes :
    unique_id  : identifiant de la série (zone : "A", "B", ...)
    ds         : timestamps datetime (fréquence "min")
    y          : valeur à prédire (densité pers/m²)
```

**Paramètres d'appel :**
```python
client.forecast(
    df        = df_all,     # toutes les zones en un seul batch
    h         = 15,         # horizon = 15 minutes
    freq      = "min",      # granularité minute
    time_col  = "ds",
    target_col= "y",
    id_col    = "unique_id",
)
```

**Contrainte :** minimum 15 observations historiques (`FENETRE_MIN`) avant le premier appel.

**Documentation officielle :** https://docs.nixtla.io/

---

### 4. Open-Meteo API

| Propriété | Valeur |
|---|---|
| Type | API REST météo |
| Authentification | Aucune (gratuite sans clé) |
| Données fournies | Température (°C), humidité relative (%) |
| Localisation | Dakar — lat 14.6928, lon -17.4467 |
| Utilisé dans | `prediction_gestion.py` → `get_meteo()` |

**Usage :** donnée contextuelle récupérée à chaque cycle. Sert d'enrichissement potentiel du contexte opérationnel (chaleur extrême → risque de malaise accru).

**Documentation officielle :** https://open-meteo.com/en/docs

---

## Seuils de référence

| Paramètre | Valeur | Fichier |
|---|---|---|
| Surface totale surveillée | 500 m² | indicateurs.py |
| Capacité maximale site | 2 000 pers. | indicateurs.py |
| Densité confort | 1.5 pers/m² | indicateurs.py |
| Densité dense | 3.0 pers/m² | indicateurs.py |
| Densité critique | 4.0 pers/m² | indicateurs.py |
| Seuil surcompression | 4.0 pers/m² | detection_anamalie.py |
| Seuil contre-flux | 30 % | detection_anamalie.py |
| Durée arrêt de masse | 20 s | detection_anamalie.py |
| Seuil accumulation | 50 pers/min | detection_anamalie.py |
| Seuil alerte préventive | 3.5 pers/m² | prediction_gestion.py |
| Fenêtre minimum TimeGPT | 15 observations | prediction_gestion.py |
| Intervalle rapport | 30 s | detection_anamalie.py |
