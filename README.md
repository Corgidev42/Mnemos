# Table de Rappel — Quiz GUI

> Entraîne ta mémoire avec le [système majeur](https://fr.wikipedia.org/wiki/Syst%C3%A8me_majeur) grâce à une interface graphique interactive.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Aperçu

Ce programme est un quiz interactif qui t'aide à mémoriser les 100 correspondances nombre ↔ mot de la **table de rappel** (système majeur). L'interface graphique est construite avec `tkinter` (inclus dans Python, aucune dépendance externe).

### Fonctionnalités

| Mode | Description |
|------|-------------|
| 📦 **Par bloc** | Choisis quels blocs de 10 réviser (0–9, 10–19…) |
| 🎯 **Focus faibles** | Quiz sur les 20 correspondances les moins maîtrisées |
| 🎲 **Aléatoire** | 20 questions tirées au hasard |
| 📋 **Toute la table** | Quiz complet sur les 100+ correspondances |
| 🃏 **Flashcard** | Révision sans stress — retourne les cartes à ton rythme |

### UX

- ⌨️ **Raccourcis clavier** : `1`–`5` = modes, `Échap` = menu, `Entrée` = valider
- ⏩ **Auto-avance** après bonne réponse (1,2s)
- 🔥 **Streak** — série de bonnes réponses affichée en live
- 📊 **Statistiques** détaillées (score par sens, temps moyen par lettre)
- 🎯 **Re-quiz erreurs** — relance un quiz uniquement sur tes erreurs
- 📖 **Vue table** avec recherche et code couleur (maîtrisé / en cours / à revoir)
- 🗑 **Reset stats** en un clic
- 🔄 **Mise à jour** — vérifie les nouvelles versions via GitHub (clic sur « Vérifier les mises à jour »)

---

## Prérequis

- **Python 3.9+** avec `tkinter`

Sur macOS avec Homebrew :

```bash
brew install python-tk@3.14   # adapter selon ta version de Python
```

Sur Ubuntu/Debian :

```bash
sudo apt install python3-tk
```

---

## Installation

```bash
git clone git@github.com:Corgidev42/TableDeRappel-v2.git
cd TableDeRappel-v2
```

---

## Utilisation

```bash
# Lancer l'interface graphique
make run

# Ou directement
python3 quiz_rappel_gui.py
```

### Commandes Make

| Commande | Description |
|----------|-------------|
| `make run` | Lance le quiz GUI |
| `make cli` | Lance la version CLI originale |
| `make check` | Vérifie la syntaxe Python |
| `make clean` | Supprime les fichiers cache |
| `make reset` | Remet les stats à zéro |
| `make dmg` | Crée l'app .app et le .dmg (macOS) |
| `make help` | Affiche l'aide |

---

## Build .dmg (macOS)

Pour créer un installateur `.dmg` et une app autonome :

```bash
pip install pyinstaller
make dmg
# ou : ./build_dmg.sh
```

Le fichier `dist/TableDeRappel-1.0.0.dmg` est généré. Glisse l'app dans Applications pour installer.

### Workflow de mise à jour

1. Incrémenter `VERSION` dans `quiz_rappel_gui.py` (ex: `"1.0.1"`)
2. Lancer `make dmg`
3. Créer un tag : `git tag v1.0.1`
4. Publier une release sur GitHub avec le `.dmg` en pièce jointe
5. Les utilisateurs cliquent sur « Vérifier les mises à jour » dans l'app pour télécharger

---

## Structure du projet

```
.
├── quiz_rappel_gui.py    # Interface graphique (v2)
├── quiz_rappel.py        # Version CLI originale
├── table_rappel.csv      # Table de rappel (nombre, mot)
├── stats_rappel.csv      # Statistiques de progression
├── TableDeRappel.spec    # Config PyInstaller
├── build_dmg.sh          # Script de build .dmg
├── Makefile              # Commandes utilitaires
├── .gitignore
└── README.md
```

### Format des données

**table_rappel.csv** — La table de correspondances :
```csv
Nombre,Mot
0,bulle
1,sapin
2,cygne
...
```

**stats_rappel.csv** — Progression (généré automatiquement) :
```csv
Nombre,Mot,Score_nombre->mot,Score_mot->nombre,Temps_moyen_par_lettre
0,bulle,3,3,0.501
```

---

## Licence

MIT
