# Mnemos — Quiz mémoire (système majeur)

> Entraîne ta mémoire avec le [système majeur](https://fr.wikipedia.org/wiki/Syst%C3%A8me_majeur) grâce à une interface graphique interactive.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Aperçu

**Mnemos** est un quiz pour mémoriser les correspondances nombre ↔ image (anciennement « Table de Rappel », puis « Majeur »). Interface tkinter avec design moderne.

### Fonctionnalités

| Mode | Description |
|------|-------------|
| 📦 **Par bloc** | Blocs de 10, raccourcis 50 dizaines paires/impaires ou 50 nombres pairs/impairs |
| 🎯 **Focus faibles** | Quiz sur les points faibles (marquage manuel + stats) |
| 🎲 **Aléatoire** | Nombre de questions et direction au choix |
| 📋 **Toute la table** | Quiz complet sur les 100+ correspondances |
| 🃏 **Flashcard** | Blocs, sens, nombre de cartes et auto-évaluation |

### UX

- ⌨️ **Raccourcis** : `1`–`5` = modes, `Échap` = menu, `Entrée` = valider
- ⏩ **Auto-avance** après bonne réponse
- 🔥 **Streak** de bonnes réponses en live
- 📊 **Statistiques** avec temps moyen (s/lettre pour N→M, s/chiffre pour M→N) sur bonnes réponses
- ⏳ **Chronomètres** : temps par question / carte et temps total de session (quiz, toute la table, flashcards)
- 🎯 **Points faibles manuels** : coches dans « Parcourir la table », repris dans le mode Focus
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

Les releases publient les fichiers `Mnemos-*.zip` / `Mnemos-*.dmg` (voir `GITHUB_REPO` dans `quiz_rappel_gui.py`). Les anciennes releases peuvent encore porter le préfixe `Mnémos-` ; l’app les reconnaît encore.

Après création du .dmg, il faut supprimer les attributs systemes pour éviter le message "L'application est endommagée" :

```bash
xattr -cr /path/to/Mnemos-*.dmg
```

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

- `Mnemos-X.Y.Z.dmg` — installer (glisser dans Applications)
- `Mnemos-X.Y.Z.zip` — mise à jour automatique

### Release

```bash
# 1. Incrémenter VERSION dans quiz_rappel_gui.py
# 2. Commit et push
git add -A && git commit -m "..." && git push

# 3. Build + publication
make release
```

Prérequis : `gh auth login`

Quand la release est **publiée** sur GitHub, le workflow **Build Windows & Linux** construit en parallèle des archives `Mnemos-Windows-x64.zip` et `Mnemos-Linux-x64.zip` et les ajoute à la même release (quelques minutes après le `.dmg` / `.zip` macOS).

---

## Windows et Linux

PyInstaller **ne croise pas** les plateformes : on ne peut pas générer un `.exe` depuis macOS. Deux approches :

### Binaires

1. Va sur [Releases](https://github.com/Corgidev42/Mnemos/releases) et télécharge **`Mnemos-Windows-x64.zip`** ou **`Mnemos-Linux-x64.zip`** (ajoutés automatiquement après chaque release macOS, voir ci-dessus).
2. **Windows** : dézippe le dossier `Mnemos`, lance **`Mnemos.exe`**. Si Windows Defender ou un antivirus signale un faux positif (fréquent avec PyInstaller), autorise l’exception ou utilise la méthode Python ci-dessous.
3. **Linux** : dézippe, puis dans un terminal : `chmod +x Mnemos/Mnemos` et lance `./Mnemos/Mnemos`. Il faut un bureau avec affichage (X11 ou Wayland avec Tk). Sur Ubuntu/Debian, si un `.so` manque : `sudo apt install python3-tk` peut aider pour une install **source** ; le build PyInstaller embarque en principe Tk.

La **mise à jour automatique** intégrée à l’app est prévue pour le **bundle macOS** ; sous Windows/Linux, il suffit de retélécharger la nouvelle release.

### Méthode « source » (Python installé)

```bash
git clone https://github.com/Corgidev42/Mnemos.git && cd Mnemos
pip install pillow
python3 quiz_rappel_gui.py
```

Prérequis : **Python 3.9+** et **tkinter** (souvent inclus ; sinon paquet `python3-tk` sur Debian/Ubuntu).

### Build manuel Win/Linux (machine locale)

Sur une machine **Windows** ou **Linux** avec Python + tkinter :

```bash
pip install pyinstaller pillow
pyinstaller --noconfirm Mnemos_ci.spec
```

Sortie dans `dist/Mnemos/` (exécutable `Mnemos` ou `Mnemos.exe`).

---

## Structure

```
.
├── quiz_rappel_gui.py      # Application principale
├── Mnemos.spec             # PyInstaller — bundle macOS (.app)
├── Mnemos_ci.spec          # PyInstaller — dossier Win/Linux (CI)
├── Mnemos_icon.png         # Icône source
├── Mnemos.icns             # Icône macOS (généré)
├── .github/workflows/      # CI : builds Windows & Linux sur release
├── scripts/
│   ├── build_dmg.sh        # Build .app / .dmg / .zip
│   └── make_icns.sh        # Génère l'icône .icns
├── Makefile
├── requirements.txt
└── README.md
```

Données : table intégrée dans l'app ; stats dans `~/.app_data/` (dev) ou `~/Library/Application Support/Mnemos/` (app). Au premier lancement, un ancien dossier `Mnémos` est renommé en `Mnemos` si besoin ; les données de `Majeur` ou `TableDeRappel` sont copiées sinon.

---

## Licence

MIT
