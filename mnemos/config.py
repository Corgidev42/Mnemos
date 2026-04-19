# -*- coding: utf-8 -*-
"""Constantes produit et données embarquées (sans Tk)."""
VERSION = "2.0.4"
APP_NAME = "Mnemos"
APP_BUNDLE_APP = f"{APP_NAME}.app"
RELEASE_ASSET_PREFIX = "Mnemos"
GITHUB_REPO = "Corgidev42/Mnemos"
ASSET_NAME_MARKERS = (
    "Mnemos",
    "Mnémos",
    "TableDeRappel",
    "Majeur",
)

DEFAULT_AUTO_ADVANCE_CORRECT_MS = 1200
DEFAULT_AUTO_ADVANCE_WRONG_MS = 0

DEFAULT_PREFERENCES = {
    "auto_advance_correct_ms": DEFAULT_AUTO_ADVANCE_CORRECT_MS,
    "auto_advance_wrong_ms": DEFAULT_AUTO_ADVANCE_WRONG_MS,
}

TABLE_EMBEDDED = [
    ("0", "bulle"), ("1", "sapin"), ("2", "cygne"), ("3", "croix"), ("4", "platre"),
    ("5", "main"), ("6", "scie"), ("7", "tete"), ("8", "huitre"), ("9", "oeuf"),
    ("10", "saucisse"), ("11", "bronze"), ("12", "pelouse"), ("13", "fraise"),
    ("14", "gateau"), ("15", "samu"), ("16", "billet"), ("17", "police"),
    ("18", "pompier"), ("19", "omelette"), ("20", "bouteille de vin"),
    ("21", "assassin"), ("22", "coeur"), ("23", "doigt"), ("24", "tarte"),
    ("25", "cintre"), ("26", "cerise"), ("27", "crepe"), ("28", "pipe"),
    ("29", "crane"), ("30", "pet"), ("31", "pain"), ("32", "pneu"),
    ("33", "petit poid"), ("34", "pirate"), ("35", "pince"), ("36", "pastis"),
    ("37", "prophete"), ("38", "perle"), ("39", "pichet"), ("40", "carotte"),
    ("41", "catin"), ("42", "ordinateur"), ("43", "chat"), ("44", "voiture"),
    ("45", "siamois"), ("46", "cassis"), ("47", "chaussette"), ("48", "volcan"),
    ("49", "echelle"), ("50", "maison"), ("51", "marin"), ("52", "merde"),
    ("53", "maroilles"), ("54", "moto"), ("55", "miroir"), ("56", "marise"),
    ("57", "marteau"), ("58", "manette"), ("59", "mouchoir"), ("60", "cle"),
    ("61", "chien"), ("62", "cheveux"), ("63", "couronne"), ("64", "chevalier"),
    ("65", "coffre"), ("66", "cacao"), ("67", "cassette"), ("68", "cabane"),
    ("69", "ciseau"), ("70", "the"), ("71", "train"), ("72", "tarlouze"),
    ("73", "telephone"), ("74", "tarzan"), ("75", "tour eiffel"), ("76", "tourne vis"),
    ("77", "trotinette"), ("78", "truite"), ("79", "titeuf"), ("80", "de"),
    ("81", "druide"), ("83", "demon"), ("84", "docteur"), ("85", "dinosaure"),
    ("88", "dodo"), ("89", "dragon"), ("90", "danseuse"), ("91", "fleur"),
    ("92", "ballon"), ("93", "mousquetaire"), ("94", "parapluie"),
    ("95", "sac a dos"), ("96", "tapis"), ("97", "guitare"), ("98", "soleil"),
    ("99", "lune"), ("100", "sablier"),
]

WEEKDAY_LABELS_FR = (
    "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche",
)

DEFAULT_WEEKLY_PLAN_DAYS = [
    "Blocs 0–29 : révision active + erreurs récentes (stats « à revoir »).",
    "Blocs 30–59 : quiz mélange N→M et M→N, vitesse modérée.",
    "Blocs 60–89 : focus sur les images encore floues ; mode flashcards.",
    "Blocs 90–100 (et au-delà si tu en as) : consolidation ; toute la table en ordre croissant une fois.",
    "Jeu libre : aléatoire ou focus points faibles ; noter les 5 plus lents.",
    "Rappel léger : parcours rapide de toute la table (sans pression).",
    "Repos actif : uniquement les maîtrisés en doute ou rien — éviter la surcharge.",
]

CONSEIL_TEXTE_COMPLET = (
    "Applique ces trois étapes uniquement sur la zone de focus du jour (sauf le jeudi) :\n\n"
    "1. Le Scan (2 min) : Fais défiler les nombres de ta zone. Si l'image (ex: Dalle pour 82) "
    "est instantanée, passe. Si tu bloques plus d'une seconde, note-le mentalement.\n\n"
    "2. La Sensation (3 min) : Sur les mots qui ont bloqué, force le trait. Ne regarde pas "
    "l'objet, touche-le. Sens le froid de l'acier du Frein (91) ou la texture visqueuse du "
    "Foie (93).\n\n"
    "3. L'Action (5 min) : Prends un chiffre de ta zone et un autre au hasard dans toute la "
    "table. Crée une interaction violente ou absurde. Exemple : Ta Batte (24) fracasse ton "
    "Disque de Frein (91) dans une explosion d'étincelles.\n\n"
    "• Loi de Pareto : Si le Sapin (1) est gravé dans ton crâne, ne perds plus jamais une "
    "seconde dessus. Concentre-toi sur tes \"points noirs\".\n\n"
    "• Vitesse : Ton but ultime est de faire le tour complet (0-100) en moins de 90 secondes."
    "\n\n"
    "• Angle de vue : Pour renforcer une image, change d'angle. Visualise ton Foret (93) de "
    "très près ou en train de rougir sous la chaleur de ton Feu (92).\n"
)

STATS_KEY_SEP = "\x01"
TABLE_EXPORT_VERSION = 2
SESSION_RUNS_VERSION = 1
FULL_BACKUP_VERSION = 1

SESSION_KIND_LABELS_FR = {
    "full_table": "Toute la table",
    "bloc": "Par bloc",
    "focus": "Focus faibles",
    "random": "Aléatoire",
    "errors_review": "Re-quiz erreurs",
}
