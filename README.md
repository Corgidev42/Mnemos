# Mnémos — Quiz mémoire (système majeur)

> Entraîne ta mémoire avec le [système majeur](https://fr.wikipedia.org/wiki/Syst%C3%A8me_majeur) grâce à une interface graphique interactive.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Aperçu

**Mnémos** est un quiz pour mémoriser les correspondances nombre ↔ image (anciennement « Table de Rappel », puis « Majeur »). Interface tkinter avec design moderne.

### Fonctionnalités

| Mode | Description |
|------|-------------|
| 📦 **Par bloc** | Choisis les blocs de 10 à réviser (0–9, 10–19…) |
| 🎯 **Focus faibles** | Quiz sur les 20 correspondances les moins maîtrisées |
| 🎲 **Aléatoire** | 20 questions tirées au hasard |
| 📋 **Toute la table** | Quiz complet sur les 100+ correspondances |
| 🃏 **Flashcard** | Blocs, sens, nombre de cartes et auto-évaluation |

### UX

- ⌨️ **Raccourcis** : `1`–`5` = modes, `Échap` = menu, `Entrée` = valider
- ⏩ **Auto-avance** après bonne réponse
- 🔥 **Streak** de bonnes réponses en live
- 📊 **Statistiques** avec temps moyen (s/lettre pour N→M, s/chiffre pour M→N) sur bonnes réponses
- 📖 **Vue table** avec recherche et code couleur
- 📤 **Export / import** de la table (JSON ou CSV) depuis le menu ou l’écran « Parcourir la table »
- 🔄 **Mise à jour automatique** — place l'app dans Applications pour l'activer

---

## Prérequis

- **Python 3.9+** avec `tkinter`
- **Pillow** (pour le logo et le build) : `pip install pillow`

Sur macOS :

```bash
brew install python-tk@3.14   # adapter selon ta version
pip install pillow
```

---

## Installation

```bash
git clone git@github.com:Corgidev42/Mnemos.git
cd Mnemos
pip install -r requirements.txt
```

Les releases publient les fichiers `Mnémos-*.zip` / `Mnémos-*.dmg` (voir `GITHUB_REPO` dans `quiz_rappel_gui.py`).

---

## Utilisation

```bash
make run
# ou
python3 quiz_rappel_gui.py
```

### Commandes

| Commande | Description |
|----------|-------------|
| `make run` | Lance l'application |
| `make check` | Vérifie la syntaxe Python |
| `make clean` | Supprime les fichiers cache |
| `make reset` | Remet les stats à zéro |
| `make dmg` | Build .app, .dmg et .zip (macOS) |
| `make release` | Build + publie sur GitHub |
| `make help` | Affiche l'aide |

---

## Build macOS

```bash
make dmg
```

Génère dans `dist/` :

- `Mnémos-X.Y.Z.dmg` — installer (glisser dans Applications)
- `Mnémos-X.Y.Z.zip` — mise à jour automatique

### Release

```bash
# 1. Incrémenter VERSION dans quiz_rappel_gui.py
# 2. Commit et push
git add -A && git commit -m "..." && git push

# 3. Build + publication
make release
```

Prérequis : `gh auth login`

---

## Structure

```
.
├── quiz_rappel_gui.py      # Application principale
├── Mnemos.spec             # Config PyInstaller
├── Mnemos_icon.png         # Icône source
├── Mnemos.icns             # Icône macOS (généré)
├── scripts/
│   ├── build_dmg.sh        # Build .app / .dmg / .zip
│   └── make_icns.sh        # Génère l'icône .icns
├── Makefile
├── requirements.txt
└── README.md
```

Données : table intégrée dans l'app ; stats dans `~/.app_data/` (dev) ou `~/Library/Application Support/Mnémos/` (app). Au premier lancement, les données de `Majeur` ou `TableDeRappel` sont copiées si besoin.

---

## Licence

MIT
