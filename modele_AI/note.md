🔴 CRITICAL — Panic
Ce qui se passe : Une foule qui panique se reconnaît par deux signaux simultanés :

Les gens lèvent les bras (fuite, bousculade, agression)
Les mouvements deviennent chaotiques (chacun part dans une direction différente)
Signal détecteur : YOLO-Pose détecte les poignets au-dessus des épaules sur >30% des personnes dans la zone.

Risque JOJ : Mouvement de foule incontrôlé, blessures par piétinement.

🔴 CRITICAL — Surcompression
Ce qui se passe : Trop de personnes dans un espace trop petit, compressées et immobiles. La foule est si dense qu'elle ne peut plus bouger — les gens sont coincés les uns contre les autres.

Signal détecteur : Densité > 4 personnes/m² ET vitesse moyenne ≈ 0.

Risque JOJ : Asphyxie, fractures costales, mort par compression (comme à Séoul 2022).

🔴 CRITICAL — Chute
Ce qui se passe : Une ou plusieurs personnes tombent au sol. Dans une foule dense, une chute peut provoquer un effet domino.

Signal détecteur : YOLO-Pose détecte que le nez d'une personne est à la même hauteur que ses hanches (corps horizontal).

Risque JOJ : Piétinement des personnes tombées.

🟠 WARNING — Contre-flux
Ce qui se passe : Une partie de la foule essaie d'aller dans le sens inverse du flux principal. Typique d'une sortie bloquée ou d'un mouvement de panique localisé.

Signal détecteur : Plus de 30% des personnes ont une direction opposée (>150°) à la direction moyenne de la zone.

Risque JOJ : Collisions frontales, chutes, blocage total de la circulation.

🟠 WARNING — Arrêt de masse
Ce qui se passe : Toute une zone se retrouve à l'arrêt complet pendant une longue durée. Ce n'est pas normal dans un événement sportif — cela indique un blocage (barrière, incident, panique localisée).

Signal détecteur : Vitesse moyenne < 2 px/s pendant plus de 20 secondes dans une zone.

Risque JOJ : Accumulation de pression derrière le blocage, surcompression imminente.

🟡 INFO — Accumulation rapide
Ce qui se passe : Un afflux soudain de personnes entre dans une zone en très peu de temps. La zone n'est pas encore en surcompression, mais elle y tend rapidement.

Signal détecteur : Plus de 50 personnes/minute entrent dans la même zone.

Risque JOJ : Précurseur de surcompression — c'est une alerte préventive pour agir avant que la situation devienne critique.

Résumé visuel

ENTRÉE MASSIVE       BLOCAGE           COMPRESSION        PANIQUE / CHUTE
(accumulation 🟡) → (arrêt_masse 🟠) → (surcompression 🔴) → (panic / chute 🔴)
                          ↑
                   (contre_flux 🟠)   ← fuite partielle
