#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mnémos — Quiz GUI (système majeur / mémoire des nombres)
Interface pour apprendre et réviser les associations nombre ↔ image.
Améliorations v2 :
  - Mode Flashcard (blocs, sens, auto-évaluation)
  - Raccourcis clavier (Échap, Entrée, chiffres)
  - Auto-avance après bonne réponse
  - Streak (série) de bonnes réponses
  - Scroll macOS natif
  - Centrage fenêtre
  - Meilleure UX globale
"""

# os/sys en premier : variables d'environnement Tk doivent être posées avant
# l'import de _tkinter, sinon Tcl/Tk 9 peut appeler Tk_CreateConsoleWindow au
# démarrage et déclencher une assertion AppKit sur macOS (menu principal).
import os
import sys

# Référence forte : fermer le master fermerait le slave (stdin) en EOF.
_TK_MAC_PTY_MASTER = None

if sys.platform == "darwin":
    # Windows / docs : évite la console Tk si supporté par le build.
    os.environ["TK_NO_CONSOLE"] = "1"
    # Sur macOS, Tcl/Tk 9 n'utilise pas TK_NO_CONSOLE : TkpInit ouvre la console
    # Tk si stdin n'est pas un TTY (ex. .app sans console depuis le Finder).
    # Tk_CreateConsoleWindow construit alors la barre de menus et peut abort()
    # dans NSMenuItem. Attacher stdin à un pseudo-TTY évite cette branche.
    if not os.isatty(0):
        try:
            import pty

            _TK_MAC_PTY_MASTER, _slave = pty.openpty()
            os.dup2(_slave, 0)
            os.close(_slave)
        except OSError:
            _TK_MAC_PTY_MASTER = None

import csv
import json
import random
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import urllib.request
import zipfile
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# Version — incrémenter à chaque release (ex: v1.0.1)
VERSION = "1.5.3"
# Nom produit (mnémoniques / système majeur)
APP_NAME = "Mnémos"
APP_BUNDLE_APP = f"{APP_NAME}.app"
RELEASE_ASSET_PREFIX = "Mnémos"
GITHUB_REPO = "Corgidev42/Mnemos"
# Fichiers sur GitHub Releases : le build ou `gh` peut produire « Mnemos » (ASCII)
# ou « Mnémos » (accent) — les deux doivent être reconnus pour la maj auto (.zip).
ASSET_NAME_MARKERS = (
    "Mnémos",
    "Mnemos",
    "TableDeRappel",
    "Majeur",
)


def _release_asset_matches(name, ext):
    """True si le fichier release est un .zip / .dmg de cette app (noms historiques inclus)."""
    if not name.endswith(ext):
        return False
    return any(marker in name for marker in ASSET_NAME_MARKERS)


def _is_macos_bundle_update_zip(name):
    """
    True si ce .zip est celui du bundle .app macOS pour la maj auto.

    Les releases incluent aussi Mnemos-Windows-x64.zip et Mnemos-Linux-x64.zip
    (CI) : ils matchent « Mnemos » mais ne contiennent pas Mnémos.app — il ne
    faut pas les prendre pour _install_update_self.
    """
    if not _release_asset_matches(name, ".zip"):
        return False
    lower = name.lower()
    if "windows" in lower or "linux" in lower:
        return False
    return True


# ============================================================
# Constantes de style — thème "Memory Palace" (violet & turquoise)
# ============================================================
BG_DARK = "#0d0b14"
BG_CARD = "#15101d"
BG_INPUT = "#1c1626"
BG_CARD_HOVER = "#1e1828"
FG_PRIMARY = "#f2eef8"
FG_SECONDARY = "#8b7da8"
FG_ACCENT = "#a78bfa"
FG_GREEN = "#34d399"
FG_RED = "#f87171"
FG_YELLOW = "#facc15"
FG_MAUVE = "#c084fc"
FG_ORANGE = "#fb923c"
FG_GOLD = "#eab308"
BTN_BG = "#211c2e"
BTN_HOVER = "#2a2438"
BTN_ACCENT = "#7c3aed"
BTN_ACCENT_FG = "#ffffff"
TAB_ACTIVE_BG = "#2e2640"
TAB_ACTIVE_FG = "#ffffff"
CHECK_ON = "#34d399"
CHECK_BG = "#15101d"
BORDER_ACCENT = "#3d3560"
SHADOW = "#08060c"

# Helvetica Neue sur Mac, fallback Helvetica ailleurs
_FONT = "Helvetica Neue" if sys.platform == "darwin" else "Helvetica"
FONT_TITLE = (_FONT, 30, "bold")
FONT_SUBTITLE = (_FONT, 15)
FONT_BODY = (_FONT, 13)
FONT_BODY_BOLD = (_FONT, 13, "bold")
FONT_SMALL = (_FONT, 11)
FONT_BIG = (_FONT, 44, "bold")
FONT_HUGE = (_FONT, 58, "bold")
FONT_QUESTION = (_FONT, 21)
FONT_INPUT = (_FONT, 19)
FONT_STREAK = (_FONT, 15, "bold")

# Auto-avance par défaut (ms) — surchargé par preferences.json (0 = désactivé)
DEFAULT_AUTO_ADVANCE_CORRECT_MS = 1200
DEFAULT_AUTO_ADVANCE_WRONG_MS = 0

DEFAULT_PREFERENCES = {
    "auto_advance_correct_ms": DEFAULT_AUTO_ADVANCE_CORRECT_MS,
    "auto_advance_wrong_ms": DEFAULT_AUTO_ADVANCE_WRONG_MS,
}

# ============================================================
# Données — table intégrée, stats en JSON (plus de CSV externe)
# ============================================================

# Table de rappel intégrée dans l'app (nombre, mot)
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


def _app_resource_dir():
    """Dossier des ressources embarquées (script en dev, _MEIPASS sous PyInstaller)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _weekly_plan_pdf_path():
    """Chemin du PDF « plan de révision hebdomadaire » (nom ASCII pour le build)."""
    return os.path.join(_app_resource_dir(), "Plan_hebdomadaire_Mnemos.pdf")


def _icon_path():
    """Chemin de l'icône (dev ou .app)."""
    base = _app_resource_dir()
    for name in (
        "Mnemos_icon.png",
        "Majeur_icon.png",
        "TableDeRappel_icon.png",
    ):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p
    return os.path.join(base, "Mnemos_icon.png")


def _load_logo_photo(width=80):
    """Charge l'icône en PhotoImage pour le menu (ou None si indisponible)."""
    if not _HAS_PIL:
        return None
    path = _icon_path()
    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        w, h = img.size
        s = min(w, h)
        img = img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
        img = img.resize((width, width), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def _get_app_support_dir():
    """Dossier des données utilisateur (dev ou .app)."""
    if getattr(sys, "frozen", False):
        root = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        path = os.path.join(root, APP_NAME)
        if not os.path.isdir(path):
            for old_name in ("Majeur", "TableDeRappel"):
                old = os.path.join(root, old_name)
                if os.path.isdir(old):
                    try:
                        shutil.copytree(old, path)
                    except OSError:
                        pass
                    break
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".app_data")
    os.makedirs(path, exist_ok=True)
    return path


def _stats_path():
    return os.path.join(_get_app_support_dir(), "stats.json")


def _table_path():
    return os.path.join(_get_app_support_dir(), "table.json")


def _prefs_path():
    return os.path.join(_get_app_support_dir(), "preferences.json")


def load_preferences():
    """Charge les préférences (auto-avance, etc.)."""
    prefs = dict(DEFAULT_PREFERENCES)
    path = _prefs_path()
    if not os.path.isfile(path):
        return prefs
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return prefs
        for key in DEFAULT_PREFERENCES:
            if key not in data:
                continue
            try:
                v = int(data[key])
            except (TypeError, ValueError):
                continue
            prefs[key] = max(0, min(120_000, v))
    except (OSError, json.JSONDecodeError):
        pass
    return prefs


def save_preferences(prefs):
    """Enregistre les préférences sur disque."""
    out = {k: int(prefs.get(k, DEFAULT_PREFERENCES[k])) for k in DEFAULT_PREFERENCES}
    for k in out:
        out[k] = max(0, min(120_000, out[k]))
    path = _prefs_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    return out


def _weak_manual_path():
    return os.path.join(_get_app_support_dir(), "weak_manual.json")


def load_manual_weak_set(table):
    """Ensemble (nombre, mot) marqués comme points faibles manuels."""
    valid = {(n, m) for n, m in table}
    out = set()
    path = _weak_manual_path()
    if not os.path.isfile(path):
        return out
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return out
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                n, m = str(item[0]).strip(), str(item[1]).strip()
                if (n, m) in valid:
                    out.add((n, m))
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return out


def save_manual_weak_set(manual_weak, table):
    """Sauvegarde les points faibles manuels (liste triée pour diff stable)."""
    valid = {(n, m) for n, m in table}
    cleaned = sorted((n, m) for n, m in manual_weak if (n, m) in valid)
    path = _weak_manual_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=0)
        f.flush()
        os.fsync(f.fileno())
    return set(cleaned)


# ============================================================
# Mise à jour via GitHub Releases
# ============================================================
def _parse_version(s):
    """Parse 'v1.0.2' ou '1.0.2' -> (1, 0, 2)."""
    s = str(s).strip().lstrip("v")
    try:
        return tuple(int(x) for x in s.split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _get_app_bundle_path():
    """Chemin du .app quand on tourne en mode frozen (macOS)."""
    if not getattr(sys, "frozen", False):
        return None
    path = os.path.abspath(sys.executable)
    # Remonter jusqu'à trouver un dossier .app
    for _ in range(10):  # sécurité
        parent = os.path.dirname(path)
        if not parent or parent == path:
            return None
        path = parent
        if path.endswith(".app") and os.path.isdir(path):
            return path
    return None


def _auto_update_eligibility():
    """
    (peut_maj_auto: bool, code: str)
    code : '' | 'not_bundled' | 'from_dmg' — pour messages utilisateur précis.
    """
    if not getattr(sys, "frozen", False):
        return False, "not_bundled"
    app_path = _get_app_bundle_path()
    if not app_path or not os.path.isdir(app_path):
        return False, "not_bundled"
    if "/Volumes/" in app_path:
        return False, "from_dmg"
    return True, ""


def _can_auto_update():
    """True si l'app est le .app installé (pas python, pas depuis le DMG monté)."""
    return _auto_update_eligibility()[0]


def check_for_update(callback):
    """
    Vérifie si une mise à jour est disponible.
    callback(ok, result) avec result = dict ou message d'erreur.
    """
    def _do_check():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "v0.0.0")
            current = _parse_version(VERSION)
            latest = _parse_version(tag)
            if latest > current:
                zip_url = dmg_url = None
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    url = asset.get("browser_download_url")
                    if _is_macos_bundle_update_zip(name):
                        zip_url = url
                    elif _release_asset_matches(name, ".dmg"):
                        dmg_url = url
                callback(True, {
                    "tag": tag, "zip_url": zip_url, "dmg_url": dmg_url,
                    "body": data.get("body", ""),
                })
            else:
                callback(True, {"up_to_date": True})
        except Exception as e:
            callback(False, str(e))

    threading.Thread(target=_do_check, daemon=True).start()


def _ensure_macos_executables(app_bundle_path):
    """
    zipfile.extractall() ne restaure pas le bit d'exécution sur macOS.
    Rend exécutables tous les fichiers dans Contents/MacOS/ (binaire principal + libs).
    """
    macos_dir = os.path.join(app_bundle_path, "Contents", "MacOS")
    if not os.path.isdir(macos_dir):
        return
    for name in os.listdir(macos_dir):
        p = os.path.join(macos_dir, name)
        if os.path.isfile(p):
            try:
                mode = os.stat(p).st_mode
                os.chmod(p, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except OSError:
                pass


def _install_update_self(zip_url, tag, callback):
    """
    Mise à jour automatique : télécharge le .zip, extrait, remplace l'app, relance.
    Uniquement en mode .app sur macOS.
    """
    def _do_install():
        try:
            app_path = _get_app_bundle_path()
            if not app_path or not os.path.isdir(app_path):
                callback(False, "Mise à jour auto indisponible (pas en mode .app)")
                return

            cache_dir = os.path.join(
                os.path.expanduser("~"),
                "Library", "Caches", APP_NAME, "update",
            )
            os.makedirs(cache_dir, exist_ok=True)

            # Télécharger le .zip (User-Agent requis par GitHub)
            zip_path = os.path.join(cache_dir, f"{RELEASE_ASSET_PREFIX}-{tag}.zip")
            req = urllib.request.Request(
                zip_url, headers={"User-Agent": f"{APP_NAME}-Updater/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(zip_path, "wb") as f:
                    f.write(resp.read())
                    f.flush()
                    os.fsync(f.fileno())

            # Repartir d’un cache vide (évite un mélange avec un .zip CI ou une vieille extraction)
            for fname in os.listdir(cache_dir):
                fp = os.path.join(cache_dir, fname)
                if os.path.isdir(fp):
                    shutil.rmtree(fp, ignore_errors=True)

            # Extraire
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(cache_dir)

            # Le .zip contient l'app à la racine (nouveau nom ou ancien bundle)
            extracted_app = None
            for folder in (
                APP_BUNDLE_APP,
                "Table de Rappel.app",
                "Majeur.app",
            ):
                p = os.path.join(cache_dir, folder)
                if os.path.isdir(p):
                    extracted_app = p
                    break
            if not extracted_app:
                callback(
                    False,
                    f"Format du .zip invalide ({APP_BUNDLE_APP} manquant)",
                )
                return

            _ensure_macos_executables(extracted_app)

            # Script qui attend notre fin, remplace, relance
            # xattr -cr : retire quarantine/Gatekeeper qui bloque les apps téléchargées
            pid = os.getpid()
            script = f'''#!/bin/bash
set -e
APP_PATH={repr(app_path)}
NEW_APP={repr(extracted_app)}
CACHE_DIR={repr(cache_dir)}
PID={pid}
while kill -0 $PID 2>/dev/null; do sleep 0.3; done
sleep 1
if [ -d "$NEW_APP" ]; then
  xattr -cr "$NEW_APP" 2>/dev/null || true
  rm -rf "$APP_PATH"
  ditto "$NEW_APP" "$APP_PATH" 2>/dev/null || cp -R "$NEW_APP" "$APP_PATH"
  xattr -cr "$APP_PATH" 2>/dev/null || true
  for f in "$APP_PATH/Contents/MacOS/"*; do
    [ -f "$f" ] && chmod +x "$f" 2>/dev/null || true
  done
  open "$APP_PATH"
fi
rm -rf "$CACHE_DIR"
'''
            script_path = os.path.join(
                tempfile.gettempdir(), f"{APP_NAME}_updater.sh")
            with open(script_path, "w") as f:
                f.write(script)
            os.chmod(script_path, 0o755)

            # Lancer le script en arrière-plan
            subprocess.Popen(["bash", script_path], start_new_session=True)

            callback(True, "restart")  # signal spécial : on va quitter
        except Exception as e:
            callback(False, str(e))

    threading.Thread(target=_do_install, daemon=True).start()


def download_and_open_dmg(url, callback):
    """Télécharge le .dmg et l'ouvre (fallback manuel). callback(success, message)."""

    def _do_download():
        try:
            dest = os.path.join(
                tempfile.gettempdir(), f"{APP_NAME}_update.dmg")
            urllib.request.urlretrieve(url, dest)
            os.system(f'open "{dest}"')
            callback(
                True,
                f"Le .dmg a été ouvert. Glisse « {APP_NAME} » dans Applications.",
            )
        except Exception as e:
            callback(False, str(e))

    threading.Thread(target=_do_download, daemon=True).start()


def load_table():
    """Charge la table (table.json si modifiée, sinon TABLE_EMBEDDED)."""
    path = _table_path()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return [tuple(row) for row in data]
        except (json.JSONDecodeError, TypeError):
            pass
    return list(TABLE_EMBEDDED)


def parse_imported_table_file(path):
    """
    Lit un fichier JSON ou CSV et retourne une liste de (nombre, mot).
    JSON : [["0","bulle"], ...] ou [{"nombre":"0","mot":"bulle"}, ...]
    CSV : colonnes Nombre,Mot (en-tête optionnel).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            raise ValueError("Fichier vide.")
        first = [c.strip().lower() for c in rows[0][:2]]
        if first and first[0] in ("nombre", "number", "#", "n"):
            rows = rows[1:]
        out = []
        for row in rows:
            if len(row) >= 2:
                n, m = row[0].strip(), row[1].strip()
                if n and m:
                    out.append((n, m))
        if not out:
            raise ValueError("Aucune ligne valide (attendu : Nombre,Mot).")
        return out

    with open(path, encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON invalide : une liste est attendue.")
    out = []
    for item in data:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            n, m = str(item[0]).strip(), str(item[1]).strip()
            if n and m:
                out.append((n, m))
        elif isinstance(item, dict):
            n = str(
                item.get("nombre")
                or item.get("Nombre")
                or item.get("n")
                or ""
            ).strip()
            m = str(
                item.get("mot")
                or item.get("Mot")
                or item.get("m")
                or ""
            ).strip()
            if n and m:
                out.append((n, m))
    if not out:
        raise ValueError("Aucune paire nombre / mot reconnue dans le JSON.")
    return out


STATS_KEY_SEP = "\x01"

# Stats par paire : [score N→M, score M→N, temps moyen s/lettre (mot), temps moyen s/chiffre (nombre)]
def _default_stats_row():
    return [0, 0, 0.0, 0.0]


def _normalize_stats_vals(vals):
    """Migre l'ancien format [nm, mn, t] vers [nm, mn, t_nm, t_mn]."""
    if not isinstance(vals, (list, tuple)) or len(vals) < 3:
        return _default_stats_row()
    s_nm = int(vals[0])
    s_mn = int(vals[1])
    t_nm = float(vals[2])
    t_mn = float(vals[3]) if len(vals) >= 4 else 0.0
    return [s_nm, s_mn, t_nm, t_mn]


def _stats_key(nombre, mot):
    return f"{nombre}{STATS_KEY_SEP}{mot}"


def load_stats(table):
    """Charge les stats depuis stats.json."""
    stats = {}
    path = _stats_path()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                for key, vals in data.items():
                    if STATS_KEY_SEP in key and isinstance(vals, list) and len(vals) >= 3:
                        n, m = key.split(STATS_KEY_SEP, 1)
                        stats[(n, m)] = _normalize_stats_vals(vals)
        except (json.JSONDecodeError, TypeError):
            pass
    for nombre, mot in table:
        if (nombre, mot) not in stats:
            stats[(nombre, mot)] = _default_stats_row()
    return stats


def save_stats(stats):
    """Sauvegarde les stats en JSON (écriture immédiate)."""
    path = _stats_path()
    data = {
        _stats_key(n, m): [int(v[0]), int(v[1]), float(v[2]), float(v[3])]
        for (n, m), v in stats.items()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
        f.flush()
        os.fsync(f.fileno())


# ============================================================
# Application principale
# ============================================================
class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Quiz v{VERSION}")
        self.configure(bg=BG_DARK)
        self.minsize(960, 700)
        self.geometry("1000x740")

        # Centrage fenêtre
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 1000) // 2
        y = (sh - 740) // 2
        self.geometry(f"1000x740+{x}+{y}")

        # Données
        self.table = load_table()
        self.stats = load_stats(self.table)
        self.preferences = load_preferences()
        self.manual_weak = load_manual_weak_set(self.table)

        # Variables de quiz
        self.questions = []
        self.current_q = 0
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.quiz_start_time = 0
        self.question_start_time = 0
        self.results = []  # (mode, nombre, mot, user_answer, correct, time)
        self._auto_advance_id = None
        self._stats_sort_tab = "worst"  # persistent stats sort state

        # Container principal
        self.container = tk.Frame(self, bg=BG_DARK)
        self.container.pack(fill="both", expand=True)

        # Raccourci global : Échap = retour menu
        self.bind("<Escape>", lambda e: self.show_main_menu())

        # Fermeture fenêtre : sauvegarder avant de quitter
        self.protocol("WM_DELETE_WINDOW", self._on_quit)

        # Démarrer avec le menu
        self.show_main_menu()

    def _on_quit(self):
        """Sauvegarde les stats avant de fermer."""
        try:
            save_stats(self.stats)
        except Exception:
            pass
        self.destroy()

    # --------------------------------------------------------
    # Utilitaires UI
    # --------------------------------------------------------
    def clear(self):
        """Supprime tous les widgets du container et annule les timers."""
        if self._auto_advance_id:
            self.after_cancel(self._auto_advance_id)
            self._auto_advance_id = None
        for w in self.container.winfo_children():
            w.destroy()

    def make_button(self, parent, text, command, accent=False, width=25,
                    danger=False):
        if danger:
            bg, fg, hover_bg = FG_RED, "#ffffff", "#fda4af"
        elif accent:
            bg, fg, hover_bg = BTN_ACCENT, BTN_ACCENT_FG, "#8b5cf6"
        else:
            bg, fg, hover_bg = BTN_BG, FG_PRIMARY, BTN_HOVER

        btn = tk.Label(
            parent, text=text,
            font=FONT_BODY_BOLD, bg=bg, fg=fg,
            cursor="hand2", width=width, pady=10, padx=4,
            relief="flat", anchor="center",
            highlightthickness=1, highlightbackground=BORDER_ACCENT,
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg, highlightbackground=FG_ACCENT))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg, highlightbackground=BORDER_ACCENT))
        return btn

    def make_card(self, parent, **kwargs):
        """Carte avec bordure subtile et padding généreux."""
        card = tk.Frame(parent, bg=BG_CARD, padx=24, pady=18,
                        highlightthickness=1, highlightbackground=BORDER_ACCENT, **kwargs)
        return card

    @staticmethod
    def _bind_mousewheel(canvas):
        """Scroll compatible macOS + Linux + Windows."""
        def _on_mousewheel(event):
            # macOS trackpad : event.delta est en pixels (grand)
            if abs(event.delta) > 10:
                canvas.yview_scroll(-1 * (event.delta // 3), "units")
            else:
                canvas.yview_scroll(-1 * event.delta, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

    # --------------------------------------------------------
    # Écran : Menu principal
    # --------------------------------------------------------
    def show_main_menu(self):
        self.clear()
        self.unbind("<Return>")
        for key in ("r", "f", "p"):
            self.unbind(key)

        # Header avec logo + titre
        header = tk.Frame(self.container, bg=BG_DARK)
        header.pack(pady=(28, 0))

        logo_img = _load_logo_photo(72)
        if logo_img:
            self._logo_ref = logo_img  # Garde la ref (évite GC)
            logo_lbl = tk.Label(header, image=logo_img, bg=BG_DARK)
            logo_lbl.pack(side="left", padx=(0, 16))
            logo_lbl.bind("<Button-1>", lambda e: self._show_about())
            logo_lbl.config(cursor="hand2")

        title_frame = tk.Frame(header, bg=BG_DARK)
        title_frame.pack(side="left")
        tk.Label(
            title_frame, text=APP_NAME,
            font=("Helvetica Neue", 32, "bold") if sys.platform == "darwin" else ("Helvetica", 32, "bold"),
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(anchor="w")
        about_lbl = tk.Label(
            title_frame,
            text=f"Système majeur — associations nombre ↔ image · v{VERSION}",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
            cursor="hand2",
        )
        about_lbl.pack(anchor="w", pady=(2, 0))
        about_lbl.bind("<Button-1>", lambda e: self._show_about())

        tk.Frame(self.container, bg=BG_DARK, height=22).pack()  # Espace

        # Stats résumé
        total = len(self.stats)
        bien_connus = sum(1 for v in self.stats.values() if v[0] + v[1] >= 4)
        en_cours = sum(1 for v in self.stats.values() if 0 < v[0] + v[1] < 4)
        a_revoir = sum(
            1 for v in self.stats.values()
            if v[0] + v[1] <= 0 and (v[0] != 0 or v[1] != 0)
        )
        non_vus = sum(
            1 for v in self.stats.values() if v[0] == 0 and v[1] == 0
        )

        stats_frame = self.make_card(self.container)
        stats_frame.pack(pady=(0, 20), padx=60, fill="x")

        # Barre de maîtrise
        bar_canvas = tk.Canvas(stats_frame, height=12, bg=BTN_BG,
                               highlightthickness=0)
        bar_canvas.pack(fill="x", pady=(0, 12))
        self.after(50, lambda: self._draw_mastery_bar(
            bar_canvas, total, bien_connus, en_cours, a_revoir, non_vus))

        stats_inner = tk.Frame(stats_frame, bg=BG_CARD)
        stats_inner.pack()

        for label, value, color in [
            ("Total", total, FG_PRIMARY),
            ("Maîtrisés", bien_connus, FG_GREEN),
            ("En cours", en_cours, FG_YELLOW),
            ("À revoir", a_revoir, FG_RED),
            ("Non vus", non_vus, FG_SECONDARY),
        ]:
            col = tk.Frame(stats_inner, bg=BG_CARD, padx=18)
            col.pack(side="left")
            tk.Label(col, text=str(value),
                     font=("Helvetica", 22, "bold"),
                     bg=BG_CARD, fg=color).pack()
            tk.Label(col, text=label, font=FONT_SMALL,
                     bg=BG_CARD, fg=FG_SECONDARY).pack()

        # ---- Modes de quiz ----
        modes_frame = tk.Frame(self.container, bg=BG_DARK)
        modes_frame.pack(pady=5)

        modes = [
            ("1", "📦  Quiz par bloc", self.show_bloc_config),
            ("2", "🎯  Focus points faibles", self.start_focus_mode),
            ("3", "🎲  Quiz aléatoire", self.start_random_mode),
            ("4", "📋  Toute la table", self.start_full_mode),
            ("5", "🃏  Mode Flashcard", self.start_flashcard_mode),
        ]
        for key, text, cmd in modes:
            row = tk.Frame(modes_frame, bg=BG_DARK)
            row.pack(fill="x", pady=3)
            # Raccourci clavier
            tk.Label(row, text=key, font=FONT_BODY_BOLD, bg=BG_INPUT,
                     fg=FG_ACCENT, width=3, pady=2).pack(side="left", padx=(0, 8))
            self.make_button(row, text, cmd, width=32).pack(side="left")

        # Raccourcis clavier 1–5
        for key, _, cmd in modes:
            self.bind(key, lambda e, c=cmd: c())
        self.bind("p", lambda e: self._open_weekly_plan_pdf())

        # ---- Boutons secondaires ----
        bottom_frame = tk.Frame(self.container, bg=BG_DARK)
        bottom_frame.pack(pady=(15, 10))
        self.make_button(
            bottom_frame, "📊  Statistiques", self.show_stats_view, width=25,
        ).pack(side="left", padx=5)
        self.make_button(
            bottom_frame, "📖  Parcourir la table", self.show_table_view,
            width=25,
        ).pack(side="left", padx=5)
        self.make_button(
            bottom_frame, "⚙️  Préférences", self.show_preferences, width=18,
        ).pack(side="left", padx=5)
        self.make_button(
            bottom_frame,
            "📅  Plan hebdomadaire (PDF)",
            self._open_weekly_plan_pdf,
            width=26,
        ).pack(side="left", padx=5)

        io_row = tk.Frame(self.container, bg=BG_DARK)
        io_row.pack(pady=(0, 5))
        self.make_button(
            io_row, "📤  Exporter la table…", self._export_table_file, width=22,
        ).pack(side="left", padx=5)
        self.make_button(
            io_row, "📥  Importer une table…", self._import_table_file, width=22,
        ).pack(side="left", padx=5)

        # Footer
        footer_row = tk.Frame(self.container, bg=BG_DARK)
        footer_row.pack(side="bottom", pady=(0, 10))
        tk.Label(
            footer_row,
            text="Raccourcis : 1-5 = modes · P = plan hebdo · Échap = menu · Entrée = valider",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(side="left")
        # Lien mise à jour
        upd_lbl = tk.Label(
            footer_row, text="  ·  🔄 Vérifier les mises à jour",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_ACCENT, cursor="hand2",
        )
        upd_lbl.pack(side="left")
        upd_lbl.bind("<Button-1>", lambda e: self._check_update())

    def show_preferences(self):
        """Réglages : délais d'auto-avance après bonne / mauvaise réponse (ms, 0 = off)."""
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="⚙️ Préférences", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(25, 8))
        tk.Label(
            self.container,
            text="Délai avant passage automatique (en millisecondes). "
                 "0 = désactivé : tu dois cliquer ou valider avec Entrée.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY, wraplength=640,
        ).pack(pady=(0, 20))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x", pady=5)

        def row(parent, label, default_ms):
            fr = tk.Frame(parent, bg=BG_CARD)
            fr.pack(fill="x", pady=10)
            tk.Label(
                fr, text=label, font=FONT_BODY, bg=BG_CARD,
                fg=FG_PRIMARY, wraplength=520, justify="left",
            ).pack(anchor="w")
            sp = tk.Spinbox(
                fr, from_=0, to=120000, increment=100, width=10,
                font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
                insertbackground=FG_PRIMARY, buttonbackground=BTN_BG,
            )
            sp.delete(0, "end")
            sp.insert(0, str(default_ms))
            sp.pack(anchor="w", pady=(6, 0))
            return sp

        sp_ok = row(
            card,
            "Après une bonne réponse (avant la question suivante). "
            "Par défaut 1200 ms (1,2 s).",
            self.preferences.get(
                "auto_advance_correct_ms", DEFAULT_AUTO_ADVANCE_CORRECT_MS,
            ),
        )
        sp_bad = row(
            card,
            "Après une mauvaise réponse. 0 par défaut : pas d’auto-avance.",
            self.preferences.get(
                "auto_advance_wrong_ms", DEFAULT_AUTO_ADVANCE_WRONG_MS,
            ),
        )

        def _save_prefs():
            try:
                ok_ms = int(sp_ok.get().strip() or "0")
                bad_ms = int(sp_bad.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Préférences", "Valeurs invalides (entiers).")
                return
            self.preferences = save_preferences({
                "auto_advance_correct_ms": ok_ms,
                "auto_advance_wrong_ms": bad_ms,
            })
            messagebox.showinfo("Préférences", "Réglages enregistrés.")

        btn_bar = tk.Frame(self.container, bg=BG_DARK)
        btn_bar.pack(pady=(22, 12))
        self.make_button(btn_bar, "💾  Enregistrer", _save_prefs, accent=True).pack(
            side="left", padx=5,
        )
        self.make_button(btn_bar, "⬅  Retour au menu", self.show_main_menu).pack(
            side="left", padx=5,
        )

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, fill, r=4):
        """Dessine un rectangle aux coins arrondis."""
        if x2 <= x1 or y2 <= y1:
            return
        r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")
        canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline="")
        canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline="")
        canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline="")
        canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline="")

    def _draw_mastery_bar(self, canvas, total, ok, en_cours, revoir, non_vus):
        """Dessine une barre de progression colorée aux coins arrondis."""
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if total == 0 or w <= 0 or h <= 0:
            return
        r = min(4, h // 2)
        segments = [
            (ok, FG_GREEN), (en_cours, FG_YELLOW),
            (revoir, FG_RED), (non_vus, BTN_BG),
        ]
        x = 0
        for count, color in segments:
            seg_w = max(0, int(w * count / total))
            if seg_w > 0:
                self._draw_rounded_rect(canvas, x, 0, x + seg_w, h, color, r)
            x += seg_w

    def _open_weekly_plan_pdf(self):
        """Ouvre le PDF du plan de révision dans l’application par défaut (Aperçu, etc.)."""
        path = os.path.abspath(_weekly_plan_pdf_path())
        if not os.path.isfile(path):
            messagebox.showerror(
                APP_NAME,
                "Le fichier du plan hebdomadaire est introuvable.\n"
                "Réinstalle l’application ou contacte le support.",
            )
            return
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", path], start_new_session=True)
            elif sys.platform == "win32":
                os.startfile(path)  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", path], start_new_session=True)
        except OSError as exc:
            messagebox.showerror(
                APP_NAME,
                f"Impossible d’ouvrir le PDF :\n{exc}",
            )

    def _show_about(self):
        """Affiche version et chemin de l'app."""
        app_path = _get_app_bundle_path()
        path_info = app_path if app_path else sys.executable
        messagebox.showinfo(
            "À propos",
            f"{APP_NAME} v{VERSION}\n\n"
            f"Chemin : {path_info}\n\n"
            "(Clic pour vérifier les mises à jour)",
        )

    def _check_update(self):
        """Vérifie les mises à jour et affiche une boîte de dialogue."""
        check_for_update(self._on_update_result)

    def _on_update_result(self, ok, result):
        """Callback après vérification des mises à jour (thread)."""
        def _show():
            if not ok:
                messagebox.showerror("Erreur", f"Impossible de vérifier : {result}")
                return
            if result.get("up_to_date"):
                messagebox.showinfo("À jour", f"Tu as déjà la dernière version (v{VERSION}).")
                return
            tag = result.get("tag", "")
            zip_url = result.get("zip_url")
            dmg_url = result.get("dmg_url")

            # Auto-update si .zip dispo et app PyInstaller (pas python3, pas DMG monté)
            can_auto, auto_reason = _auto_update_eligibility()
            use_auto = bool(zip_url) and can_auto
            if use_auto:
                msg = (
                    f"Une nouvelle version ({tag}) est disponible. "
                    f"Mise à jour automatique ?"
                )
            elif not zip_url:
                msg = (
                    f"Une nouvelle version ({tag}) est disponible. "
                    f"Aucun fichier .zip sur la release (maj auto impossible). "
                    f"Télécharger le .dmg pour installer à la main ?"
                )
            elif auto_reason == "from_dmg":
                msg = (
                    f"Une nouvelle version ({tag}) est disponible. "
                    f"Tu lances l’app depuis le disque image : copie « {APP_NAME} » "
                    f"dans Applications, puis rouvre-la depuis le dossier Applications "
                    f"pour activer la mise à jour automatique. "
                    f"Télécharger le .dmg maintenant ?"
                )
            else:
                msg = (
                    f"Une nouvelle version ({tag}) est disponible. "
                    f"La mise à jour automatique ne fonctionne qu’avec l’application "
                    f"« {APP_NAME}.app » installée (pas en lançant le script Python). "
                    f"Télécharger le .dmg ?"
                )
            if not messagebox.askyesno("Mise à jour disponible", msg):
                return

            if use_auto:
                _install_update_self(zip_url, tag.lstrip("v"), self._on_download_result)
            elif dmg_url:
                download_and_open_dmg(dmg_url, self._on_download_result)
            else:
                messagebox.showinfo(
                    "Mise à jour disponible",
                    f"Version {tag} disponible sur GitHub.",
                )

        self.after(0, _show)

    def _on_download_result(self, success, message):
        """Callback après téléchargement ou mise à jour auto (thread)."""
        def _show():
            if success:
                if message == "restart":
                    self._on_quit()  # Ferme l'app pour que l'updater la remplace
                else:
                    messagebox.showinfo("Téléchargement terminé", message)
            else:
                messagebox.showerror("Erreur", f"Échec : {message}")

        self.after(0, _show)

    # --------------------------------------------------------
    # Écran : Configuration bloc
    # --------------------------------------------------------
    def show_bloc_config(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📦 Quiz par bloc", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(35, 15))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x")

        tk.Label(
            card,
            text="Sélectionne les blocs à réviser :",
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY, wraplength=600,
        ).pack(pady=(5, 12))

        # Grille de blocs
        blocs_frame = tk.Frame(card, bg=BG_CARD)
        blocs_frame.pack(pady=5)

        self.bloc_vars = {}
        for i in range(11):  # 0..10
            start = i * 10
            end = min(start + 9, 100)
            var = tk.BooleanVar(value=False)
            self.bloc_vars[i] = var
            cb = tk.Checkbutton(
                blocs_frame, text=f"  {start:>3}–{end}", variable=var,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0,
                indicatoron=True, onvalue=True, offvalue=False,
            )
            cb.grid(row=i // 4, column=i % 4, padx=12, pady=5, sticky="w")

        # Sélection rapide
        quick_frame = tk.Frame(card, bg=BG_CARD)
        quick_frame.pack(pady=(8, 5))
        self.make_button(
            quick_frame, "Tout sélectionner", self._select_all_blocs, width=18,
        ).pack(side="left", padx=5)
        self.make_button(
            quick_frame, "Tout désélectionner", self._deselect_all_blocs,
            width=18,
        ).pack(side="left", padx=5)

        tens_frame = tk.Frame(card, bg=BG_CARD)
        tens_frame.pack(pady=(6, 2))
        tk.Label(
            tens_frame, text="Sélection rapide :",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))
        row_a = tk.Frame(tens_frame, bg=BG_CARD)
        row_a.pack(fill="x")
        self.make_button(
            row_a, "50 diz. paires (0,20…80)", self._select_even_tens_blocs,
            width=22,
        ).pack(side="left", padx=4, pady=2)
        self.make_button(
            row_a, "50 diz. impaires (10…90)", self._select_odd_tens_blocs,
            width=22,
        ).pack(side="left", padx=4, pady=2)
        row_b = tk.Frame(tens_frame, bg=BG_CARD)
        row_b.pack(fill="x")
        self.make_button(
            row_b, "50 nombres pairs (0–98)", self._start_quiz_even_numbers,
            width=24,
        ).pack(side="left", padx=4, pady=2)
        self.make_button(
            row_b, "50 nombres impairs (1–99)", self._start_quiz_odd_numbers,
            width=24,
        ).pack(side="left", padx=4, pady=2)

        # Direction
        self._add_direction_picker(card)

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=20)
        self.make_button(btn_frame, "🚀  Lancer le quiz",
                         self._start_bloc_quiz, accent=True).pack(
            side="left", padx=10)
        self.make_button(btn_frame, "⬅  Retour",
                         self.show_main_menu).pack(side="left", padx=10)

    def _select_all_blocs(self):
        for v in self.bloc_vars.values():
            v.set(True)

    def _deselect_all_blocs(self):
        for v in self.bloc_vars.values():
            v.set(False)

    def _select_even_tens_blocs(self):
        """Blocs 0–9, 20–29, … 80–89 (dizaines paires)."""
        for i, v in self.bloc_vars.items():
            v.set(i in (0, 2, 4, 6, 8))

    def _select_odd_tens_blocs(self):
        """Blocs 10–19, … 90–99 (dizaines impaires)."""
        for i, v in self.bloc_vars.items():
            v.set(i in (1, 3, 5, 7, 9))

    def _start_quiz_even_numbers(self):
        pairs = [
            p for p in self.table
            if int(p[0]) < 100 and int(p[0]) % 2 == 0
        ]
        if not pairs:
            messagebox.showwarning(
                "Attention",
                "Aucune paire nombre pair 0–98 dans la table.",
            )
            return
        self._build_questions(pairs)

    def _start_quiz_odd_numbers(self):
        pairs = [
            p for p in self.table
            if int(p[0]) < 100 and int(p[0]) % 2 != 0
        ]
        if not pairs:
            messagebox.showwarning(
                "Attention",
                "Aucune paire nombre impair 1–99 dans la table.",
            )
            return
        self._build_questions(pairs)

    def _add_direction_picker(self, parent):
        """Widget de sélection de direction réutilisable."""
        sens_frame = tk.Frame(parent, bg=BG_CARD)
        sens_frame.pack(pady=(12, 5))
        tk.Label(sens_frame, text="Direction :", font=FONT_BODY_BOLD,
                 bg=BG_CARD, fg=FG_PRIMARY).pack(side="left", padx=(0, 10))

        self.sens_var = tk.StringVar(value="3")
        for text, val in [("Nombre → Mot", "1"), ("Mot → Nombre", "2"),
                          ("Les deux", "3")]:
            tk.Radiobutton(
                sens_frame, text=f"  {text}", variable=self.sens_var,
                value=val,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0,
            ).pack(side="left", padx=8)

    def _start_bloc_quiz(self):
        selected = [i for i, v in self.bloc_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Attention",
                                   "Sélectionne au moins un bloc !")
            return
        pairs = []
        for bloc_i in selected:
            start = bloc_i * 10
            end = min(start + 9, 100)
            pairs.extend(
                [p for p in self.table if start <= int(p[0]) <= end])
        if not pairs:
            messagebox.showwarning("Attention",
                                   "Aucune correspondance pour ces blocs.")
            return
        self._build_questions(pairs)

    # --------------------------------------------------------
    # Modes de démarrage rapide
    # --------------------------------------------------------
    def start_focus_mode(self):
        self._show_sens_then_start(self._do_start_focus)

    def _do_start_focus(self):
        manual = [p for p in self.manual_weak if p in self.stats]
        tri = sorted(self.stats.items(),
                     key=lambda x: x[1][0] + x[1][1])
        seen = set(manual)
        pool = list(manual)
        for k, _v in tri:
            if len(pool) >= 20:
                break
            if k in seen:
                continue
            pool.append(k)
            seen.add(k)
        if not pool:
            messagebox.showwarning(
                "Attention",
                "Aucune paire à réviser (stats ou points faibles manuels).",
            )
            return
        self._build_questions(pool)

    def start_random_mode(self):
        self._show_random_config()

    def _show_random_config(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="🎲 Quiz aléatoire", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(60, 20))

        card = self.make_card(self.container)
        card.pack(padx=120)

        row_n = tk.Frame(card, bg=BG_CARD)
        row_n.pack(fill="x", pady=(8, 12))
        tk.Label(
            row_n, text="Nombre de questions :",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
        ).pack(side="left", padx=(0, 10))
        self.random_n_var = tk.StringVar(value="20")
        tk.Entry(
            row_n, textvariable=self.random_n_var, font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", width=8, justify="center",
        ).pack(side="left", ipady=4)
        tk.Label(
            row_n,
            text="  (tirage avec remise dans la table)",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(side="left", padx=(10, 0))

        self._add_direction_picker(card)

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=30)
        self.make_button(
            btn_frame, "🚀  Lancer", self._do_start_random,
            accent=True,
        ).pack(side="left", padx=10)
        self.make_button(
            btn_frame, "⬅  Retour", self.show_main_menu,
        ).pack(side="left", padx=10)

    def _do_start_random(self):
        try:
            nq = int(self.random_n_var.get().strip())
        except (ValueError, AttributeError):
            messagebox.showwarning(
                "Attention", "Nombre de questions invalide (entier).")
            return
        if nq < 1:
            messagebox.showwarning(
                "Attention", "Il faut au moins une question.")
            return
        if nq > 500:
            messagebox.showwarning(
                "Attention", "Maximum 500 questions pour cette session.")
            return
        pairs = [random.choice(self.table) for _ in range(nq)]
        self._build_questions(pairs)

    def start_full_mode(self):
        self._show_sens_then_start(self._do_start_full)

    def _do_start_full(self):
        self._build_questions(list(self.table))

    def _show_sens_then_start(self, callback):
        """Demande la direction puis lance le quiz."""
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="Direction du quiz", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(60, 25))

        self.sens_var = tk.StringVar(value="3")
        card = self.make_card(self.container)
        card.pack(padx=120)

        options = [
            ("1", "Nombre → Mot", "On te donne le nombre, trouve le mot"),
            ("2", "Mot → Nombre", "On te donne le mot, trouve le nombre"),
            ("3", "Les deux sens", "Questions mélangées dans les deux sens"),
        ]
        for val, title, desc in options:
            f = tk.Frame(card, bg=BG_CARD, pady=5)
            f.pack(fill="x")
            tk.Radiobutton(
                f, text=f"  {title}", variable=self.sens_var, value=val,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0, anchor="w",
            ).pack(anchor="w")
            tk.Label(f, text=f"       {desc}", font=FONT_SMALL,
                     bg=BG_CARD, fg=FG_SECONDARY).pack(anchor="w")

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=30)
        self.make_button(btn_frame, "🚀  Lancer", callback,
                         accent=True).pack(side="left", padx=10)
        self.make_button(btn_frame, "⬅  Retour",
                         self.show_main_menu).pack(side="left", padx=10)

    def _unbind_menu_keys(self):
        """Détache les raccourcis du menu principal."""
        for key in ("1", "2", "3", "4", "5", "p"):
            self.unbind(key)

    # --------------------------------------------------------
    # Construction des questions et lancement
    # --------------------------------------------------------
    def _build_questions(self, pairs):
        sens = self.sens_var.get()
        self.questions = []
        for nombre, mot in pairs:
            if sens in ("1", "3"):
                self.questions.append(("nombre->mot", nombre, mot))
            if sens in ("2", "3"):
                self.questions.append(("mot->nombre", nombre, mot))
        random.shuffle(self.questions)
        self.current_q = 0
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.results = []
        self.quiz_start_time = time.time()
        self.question_start_time = time.time()
        self._show_question()

    # --------------------------------------------------------
    # Écran : Question du quiz
    # --------------------------------------------------------
    def _show_question(self):
        self.clear()
        self.unbind("<Return>")

        mode, nombre, mot = self.questions[self.current_q]
        total = len(self.questions)
        idx = self.current_q + 1

        # -- Barre de progression & infos --
        top_bar = tk.Frame(self.container, bg=BG_DARK)
        top_bar.pack(fill="x", padx=40, pady=(18, 0))

        tk.Label(
            top_bar, text=f"Question {idx}/{total}",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(side="left")

        # Streak
        if self.streak >= 2:
            tk.Label(
                top_bar, text=f"🔥 {self.streak}",
                font=FONT_STREAK, bg=BG_DARK, fg=FG_ORANGE,
            ).pack(side="left", padx=15)

        if idx > 1:
            tk.Label(
                top_bar, text=f"Score : {self.score}/{idx - 1}",
                font=FONT_BODY, bg=BG_DARK, fg=FG_GREEN,
            ).pack(side="right", padx=(0, 12))

        self.session_timer_label = tk.Label(
            top_bar, text="⏳ Session : 0.0s",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
        )
        self.session_timer_label.pack(side="right")

        # Progress bar
        bar = tk.Canvas(self.container, height=6, bg=BTN_BG,
                        highlightthickness=0)
        bar.pack(fill="x", padx=40, pady=(5, 0))
        self.after(50, lambda: self._draw_progress(bar, idx, total))

        # -- Zone question --
        q_frame = tk.Frame(self.container, bg=BG_DARK)
        q_frame.pack(expand=True, fill="both", padx=40)

        if mode == "nombre->mot":
            tk.Label(
                q_frame, text="Quel mot correspond au nombre…",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(30, 8))
            tk.Label(
                q_frame, text=nombre, font=FONT_BIG,
                bg=BG_DARK, fg=FG_ACCENT,
            ).pack(pady=(0, 20))
        else:
            tk.Label(
                q_frame, text="Quel nombre correspond au mot…",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(30, 8))
            tk.Label(
                q_frame, text=mot, font=FONT_BIG,
                bg=BG_DARK, fg=FG_GREEN,
            ).pack(pady=(0, 20))

        # Input
        self.answer_var = tk.StringVar()
        entry = tk.Entry(
            q_frame, textvariable=self.answer_var,
            font=FONT_INPUT, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat",
            justify="center", width=25,
        )
        entry.pack(ipady=8, pady=(0, 15))
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._submit_answer())

        # Bouton valider
        self.make_button(
            q_frame, "Valider ↵", self._submit_answer, accent=True, width=20,
        ).pack()

        # Timer live
        self.timer_label = tk.Label(
            q_frame, text="⏱ 0.0s", font=FONT_SMALL,
            bg=BG_DARK, fg=FG_SECONDARY,
        )
        self.timer_label.pack(pady=(12, 0))
        self._update_quiz_timers()

    def _draw_progress(self, canvas, current, total):
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if total <= 0 or w <= 0 or h <= 0:
            return
        fill_w = int(w * (current - 1) / total)
        if fill_w > 0:
            self._draw_rounded_rect(canvas, 0, 0, fill_w, h, FG_ACCENT, min(3, h // 2))

    def _update_quiz_timers(self):
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            elapsed_q = time.time() - self.question_start_time
            self.timer_label.configure(text=f"⏱ Question : {elapsed_q:.1f}s")
        if hasattr(self, "session_timer_label") and self.session_timer_label.winfo_exists():
            elapsed_s = time.time() - self.quiz_start_time
            self.session_timer_label.configure(
                text=f"⏳ Session : {elapsed_s:.1f}s",
            )
        if (
            hasattr(self, "timer_label") and self.timer_label.winfo_exists()
        ) or (
            hasattr(self, "session_timer_label")
            and self.session_timer_label.winfo_exists()
        ):
            self.after(100, self._update_quiz_timers)

    def _apply_answer_stats(self, mode, nombre, mot, correct, elapsed):
        """Met à jour les compteurs / temps moyen pour une paire (quiz ou flashcard)."""
        if mode == "nombre->mot":
            if correct:
                self.stats[(nombre, mot)][0] += 1
                nb_lettres = len(mot)
                if nb_lettres > 0:
                    tpl = elapsed / nb_lettres
                    ancien = self.stats[(nombre, mot)][2]
                    self.stats[(nombre, mot)][2] = (
                        tpl if ancien == 0 else (ancien + tpl) / 2
                    )
            else:
                self.stats[(nombre, mot)][0] -= 1
        else:
            if correct:
                self.stats[(nombre, mot)][1] += 1
                nb_ch = len(str(nombre))
                if nb_ch > 0:
                    tps = elapsed / nb_ch
                    ancien = self.stats[(nombre, mot)][3]
                    self.stats[(nombre, mot)][3] = (
                        tps if ancien == 0 else (ancien + tps) / 2
                    )
            else:
                self.stats[(nombre, mot)][1] -= 1
        save_stats(self.stats)

    def _submit_answer(self):
        answer = self.answer_var.get().strip().lower()
        if not answer:
            return

        mode, nombre, mot = self.questions[self.current_q]
        elapsed = time.time() - self.question_start_time

        if mode == "nombre->mot":
            correct = answer == mot.lower()
            expected = mot
        else:
            correct = answer == nombre
            expected = nombre

        self._apply_answer_stats(mode, nombre, mot, correct, elapsed)

        if correct:
            self.score += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.streak = 0

        self.results.append((mode, nombre, mot, answer, correct, elapsed))
        self.question_start_time = time.time()

        self._show_feedback(correct, expected, elapsed)

    # --------------------------------------------------------
    # Écran : Feedback après réponse
    # --------------------------------------------------------
    def _show_feedback(self, correct, expected, elapsed):
        self.clear()
        mode, nombre, mot, answer, _, _ = self.results[-1]

        if correct:
            icon, msg, color = "✅", "Correct !", FG_GREEN
        else:
            icon, msg, color = "❌", "Mauvaise réponse", FG_RED

        tk.Label(
            self.container, text=icon, font=("Helvetica", 64),
            bg=BG_DARK, fg=color,
        ).pack(pady=(40, 0))
        tk.Label(
            self.container, text=msg, font=FONT_TITLE,
            bg=BG_DARK, fg=color,
        ).pack(pady=(0, 10))

        # Streak badge
        if correct and self.streak >= 3:
            tk.Label(
                self.container,
                text=f"🔥 Série de {self.streak} !",
                font=FONT_STREAK, bg=BG_DARK, fg=FG_ORANGE,
            ).pack()

        # Détails
        card = self.make_card(self.container)
        card.pack(padx=120, pady=(10, 0))

        if not correct:
            tk.Label(
                card, text=f"Ta réponse : {answer}", font=FONT_BODY,
                bg=BG_CARD, fg=FG_RED,
            ).pack(anchor="w", pady=2)
            tk.Label(
                card, text=f"Bonne réponse : {expected}",
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_GREEN,
            ).pack(anchor="w", pady=2)

        tk.Label(
            card, text=f"{nombre}  ↔  {mot}",
            font=FONT_QUESTION, bg=BG_CARD, fg=FG_ACCENT,
        ).pack(pady=(10, 5))
        tk.Label(
            card, text=f"⏱ {elapsed:.1f}s",
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack()

        # Progression
        idx = self.current_q + 1
        total = len(self.questions)
        tk.Label(
            self.container, text=f"{idx}/{total} — Score : {self.score}/{idx}",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(12, 0))

        # Navigation
        self.current_q += 1
        if self.current_q < total:
            btn_text = "Question suivante →"
            btn_cmd = self._show_question
        else:
            btn_text = "Voir les résultats 🏁"
            btn_cmd = self._show_results

        btn = self.make_button(
            self.container, btn_text, btn_cmd, accent=True, width=25,
        )
        btn.pack(pady=20)
        self.bind("<Return>", lambda e: btn_cmd())
        btn.focus_set()

        delay_ok = int(self.preferences.get(
            "auto_advance_correct_ms", DEFAULT_AUTO_ADVANCE_CORRECT_MS,
        ))
        delay_bad = int(self.preferences.get(
            "auto_advance_wrong_ms", DEFAULT_AUTO_ADVANCE_WRONG_MS,
        ))

        if correct and delay_ok > 0 and self.current_q < total:
            tk.Label(
                self.container, text="Suite automatique…",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack()
            self._auto_advance_id = self.after(delay_ok, btn_cmd)
        elif (
            not correct
            and delay_bad > 0
        ):
            tk.Label(
                self.container, text="Suite automatique…",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack()
            self._auto_advance_id = self.after(delay_bad, btn_cmd)

    # --------------------------------------------------------
    # Écran : Résultats du quiz
    # --------------------------------------------------------
    def _show_results(self):
        self.unbind("<Return>")
        self.clear()
        save_stats(self.stats)

        total_time = time.time() - self.quiz_start_time
        total_q = len(self.questions)
        pct = (self.score / total_q * 100) if total_q else 0

        tk.Label(
            self.container, text="🏁 Résultats", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(25, 10))

        # Score principal
        score_color = (FG_GREEN if pct >= 80
                       else (FG_YELLOW if pct >= 50 else FG_RED))
        tk.Label(
            self.container, text=f"{self.score}/{total_q}",
            font=FONT_HUGE, bg=BG_DARK, fg=score_color,
        ).pack()
        tk.Label(
            self.container,
            text=f"{pct:.0f}%  ·  Meilleure série : {self.best_streak} 🔥",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 6))
        tk.Label(
            self.container,
            text=f"⏳ Chronomètre total de la série : {total_time:.1f}s",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
        ).pack(pady=(0, 15))

        # Temps moyen par question
        if total_q > 0:
            avg_time = total_time / total_q
            tk.Label(
                self.container,
                text=f"⏱ Temps moyen : {avg_time:.1f}s / question",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(0, 10))

        # Erreurs
        errors = [r for r in self.results if not r[4]]
        if errors:
            err_card = self.make_card(self.container)
            err_card.pack(padx=60, fill="x", pady=(0, 8))

            tk.Label(
                err_card, text=f"❌ {len(errors)} erreur(s) à revoir :",
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_RED,
            ).pack(anchor="w", pady=(0, 8))

            list_frame = tk.Frame(err_card, bg=BG_CARD)
            list_frame.pack(fill="x")

            for mode, nombre, mot, answer, _, t in errors[:15]:
                direction = "→" if mode == "nombre->mot" else "←"
                line = (f"  {nombre} {direction} {mot}  "
                        f"(ta réponse : {answer}, {t:.1f}s)")
                tk.Label(
                    list_frame, text=line, font=FONT_SMALL,
                    bg=BG_CARD, fg=FG_SECONDARY, anchor="w",
                ).pack(anchor="w")
            if len(errors) > 15:
                tk.Label(
                    list_frame,
                    text=f"  … et {len(errors) - 15} autre(s)",
                    font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
                ).pack(anchor="w")
        else:
            tk.Label(
                self.container, text="🎉 Aucune erreur ! Parfait !",
                font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_GREEN,
            ).pack(pady=10)

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=15)
        self.make_button(
            btn_frame, "🔄  Recommencer", self.show_main_menu, accent=True,
        ).pack(side="left", padx=10)

        # Relancer uniquement les erreurs
        if errors:
            self.make_button(
                btn_frame, "🎯  Re-quiz erreurs",
                lambda: self._requiz_errors(errors), width=20,
            ).pack(side="left", padx=10)

        self.make_button(
            btn_frame, "🚪  Quitter", self._on_quit,
        ).pack(side="left", padx=10)

    def _requiz_errors(self, errors):
        """Relance un quiz uniquement sur les erreurs."""
        self.questions = [
            (mode, nombre, mot) for mode, nombre, mot, _, _, _ in errors
        ]
        random.shuffle(self.questions)
        self.current_q = 0
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.results = []
        self.quiz_start_time = time.time()
        self.question_start_time = time.time()
        self._show_question()

    # --------------------------------------------------------
    # MODE FLASHCARD
    # --------------------------------------------------------
    def _build_flashcard_tuples(self, pairs, sens):
        """Liste (mode, nombre, mot) pour les cartes, selon la direction."""
        out = []
        for nombre, mot in pairs:
            if sens in ("1", "3"):
                out.append(("nombre->mot", nombre, mot))
            if sens in ("2", "3"):
                out.append(("mot->nombre", nombre, mot))
        return out

    def start_flashcard_mode(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="🃏 Mode Flashcard", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_MAUVE,
        ).pack(pady=(35, 10))
        tk.Label(
            self.container,
            text="Choisis les blocs, la direction et le nombre de cartes. "
                 "Retourne la carte, puis indique si tu l’avais bien mémorisée "
                 "(les stats sont mises à jour).",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY, wraplength=640,
        ).pack(pady=(0, 18))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x")

        tk.Label(
            card,
            text="Blocs à inclure :",
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(anchor="w", pady=(5, 8))

        blocs_frame = tk.Frame(card, bg=BG_CARD)
        blocs_frame.pack(pady=5)
        self.fc_bloc_vars = {}
        for i in range(11):
            start = i * 10
            end = min(start + 9, 100)
            var = tk.BooleanVar(value=False)
            self.fc_bloc_vars[i] = var
            tk.Checkbutton(
                blocs_frame, text=f"  {start:>3}–{end}", variable=var,
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=CHECK_ON, highlightthickness=0,
                indicatoron=True, onvalue=True, offvalue=False,
            ).grid(row=i // 4, column=i % 4, padx=12, pady=5, sticky="w")

        quick_frame = tk.Frame(card, bg=BG_CARD)
        quick_frame.pack(pady=(4, 2))
        self.make_button(
            quick_frame, "Tout sélectionner", self._fc_select_all_blocs, width=18,
        ).pack(side="left", padx=5)
        self.make_button(
            quick_frame, "Tout désélectionner", self._fc_deselect_all_blocs,
            width=18,
        ).pack(side="left", padx=5)

        self._add_direction_picker(card)

        nb_row = tk.Frame(card, bg=BG_CARD)
        nb_row.pack(pady=(14, 6), fill="x")
        tk.Label(
            nb_row, text="Nombre de cartes :",
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
        ).pack(side="left", padx=(0, 12))
        self.fc_count_var = tk.StringVar(value="20")
        tk.Entry(
            nb_row, textvariable=self.fc_count_var, font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", width=8, justify="center",
        ).pack(side="left", ipady=4)
        tk.Label(
            nb_row,
            text="  (tirage parmi les cartes possibles selon blocs + sens)",
            font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(side="left", padx=(10, 0))

        self.fc_shuffle_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card, text="  Ordre aléatoire", variable=self.fc_shuffle_var,
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
            selectcolor=CHECK_BG, activebackground=BG_CARD,
            activeforeground=CHECK_ON, highlightthickness=0,
        ).pack(anchor="w", pady=(6, 4))

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=20)
        self.make_button(
            btn_frame, "🃏  Commencer", self._launch_flashcards, accent=True,
        ).pack(side="left", padx=10)
        self.make_button(
            btn_frame, "⬅  Retour", self.show_main_menu,
        ).pack(side="left", padx=10)

    def _fc_select_all_blocs(self):
        for v in self.fc_bloc_vars.values():
            v.set(True)

    def _fc_deselect_all_blocs(self):
        for v in self.fc_bloc_vars.values():
            v.set(False)

    def _launch_flashcards(self):
        selected = [i for i, v in self.fc_bloc_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning(
                "Attention", "Sélectionne au moins un bloc !")
            return
        pairs = []
        for bloc_i in selected:
            start = bloc_i * 10
            end = min(start + 9, 100)
            pairs.extend(
                [p for p in self.table if start <= int(p[0]) <= end])
        if not pairs:
            messagebox.showwarning(
                "Attention", "Aucune correspondance pour ces blocs.")
            return

        sens = self.sens_var.get()
        pool = self._build_flashcard_tuples(pairs, sens)
        if not pool:
            messagebox.showwarning("Attention", "Aucune carte générée.")
            return

        try:
            want = int(self.fc_count_var.get().strip())
        except ValueError:
            messagebox.showwarning(
                "Attention", "Nombre de cartes invalide (entier).")
            return
        if want < 1:
            messagebox.showwarning("Attention", "Il faut au moins une carte.")
            return

        if self.fc_shuffle_var.get():
            random.shuffle(pool)
        n = min(want, len(pool))
        if want > len(pool):
            messagebox.showinfo(
                "Cartes disponibles",
                f"Seulement {len(pool)} carte(s) possible(s) avec ces options — "
                f"session de {len(pool)} cartes.",
            )
        self.fc_cards = pool[:n]

        self.fc_idx = 0
        self.fc_revealed = False
        self.fc_score = 0
        self.fc_streak = 0
        self.fc_best_streak = 0
        self.fc_results = []
        self.fc_quiz_start = time.time()
        self._show_flashcard()

    def _show_flashcard(self):
        self.clear()
        for key in ("<space>", "<Return>", "<Right>", "r", "f"):
            self.unbind(key)

        if not self.fc_revealed:
            self.fc_card_t0 = time.time()

        mode, nombre, mot = self.fc_cards[self.fc_idx]
        total = len(self.fc_cards)
        idx = self.fc_idx + 1

        top_bar = tk.Frame(self.container, bg=BG_DARK)
        top_bar.pack(fill="x", padx=40, pady=(18, 0))
        tk.Label(
            top_bar, text=f"🃏 Flashcard {idx}/{total}",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_MAUVE,
        ).pack(side="left")
        done_prev = idx - 1
        if done_prev > 0:
            tk.Label(
                top_bar,
                text=f"  Réussies : {self.fc_score}/{done_prev}",
                font=FONT_BODY, bg=BG_DARK, fg=FG_GREEN,
            ).pack(side="left", padx=(12, 0))
        if self.fc_streak >= 2:
            tk.Label(
                top_bar, text=f"  🔥 {self.fc_streak}",
                font=FONT_STREAK, bg=BG_DARK, fg=FG_ORANGE,
            ).pack(side="left", padx=(8, 0))

        self.fc_session_timer_lbl = tk.Label(
            top_bar, text="⏳ Session : 0.0s",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
        )
        self.fc_session_timer_lbl.pack(side="right", padx=(8, 0))
        self.fc_card_timer_lbl = tk.Label(
            top_bar, text="⏱ Carte : 0.0s",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        )
        self.fc_card_timer_lbl.pack(side="right")
        self._update_flashcard_timers()

        bar = tk.Canvas(self.container, height=4, bg=BTN_BG,
                        highlightthickness=0)
        bar.pack(fill="x", padx=60, pady=(8, 10))
        self.after(50, lambda: self._draw_progress(bar, idx, total))

        card = tk.Frame(
            self.container, bg=FG_MAUVE, padx=3, pady=3,
        )
        card.pack(padx=120, pady=16, fill="x")

        inner = tk.Frame(card, bg=BG_CARD, padx=30, pady=30)
        inner.pack(fill="both", expand=True)

        hint = (
            "Quel mot correspond ?" if mode == "nombre->mot" else
            "Quel nombre correspond ?"
        )
        tk.Label(
            inner, text=hint, font=FONT_SMALL,
            bg=BG_CARD, fg=FG_SECONDARY,
        ).pack(pady=(0, 8))

        if mode == "nombre->mot":
            tk.Label(
                inner, text=nombre, font=FONT_BIG,
                bg=BG_CARD, fg=FG_ACCENT,
            ).pack(pady=(5, 10))
            if self.fc_revealed:
                tk.Label(
                    inner, text="↕", font=FONT_BODY,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack()
                tk.Label(
                    inner, text=mot, font=FONT_BIG,
                    bg=BG_CARD, fg=FG_GREEN,
                ).pack(pady=(10, 10))
            else:
                tk.Label(
                    inner, text="???", font=FONT_QUESTION,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack(pady=(10, 10))
        else:
            tk.Label(
                inner, text=mot, font=FONT_BIG,
                bg=BG_CARD, fg=FG_GREEN,
            ).pack(pady=(5, 10))
            if self.fc_revealed:
                tk.Label(
                    inner, text="↕", font=FONT_BODY,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack()
                tk.Label(
                    inner, text=nombre, font=FONT_BIG,
                    bg=BG_CARD, fg=FG_ACCENT,
                ).pack(pady=(10, 10))
            else:
                tk.Label(
                    inner, text="???", font=FONT_QUESTION,
                    bg=BG_CARD, fg=FG_SECONDARY,
                ).pack(pady=(10, 10))

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=12)

        if not self.fc_revealed:
            btn = self.make_button(
                btn_frame, "Retourner (Espace)",
                self._reveal_flashcard, accent=True, width=24,
            )
            btn.pack()
            btn.focus_set()
            self.bind("<space>", lambda e: self._reveal_flashcard())
            self.bind("<Return>", lambda e: self._reveal_flashcard())
        else:
            ok_btn = self.make_button(
                btn_frame, "✓  J’avais bon",
                lambda: self._flashcard_self_rate(True), accent=True, width=18,
            )
            ok_btn.pack(side="left", padx=6)
            bad_btn = self.make_button(
                btn_frame, "✗  Je me suis trompé",
                lambda: self._flashcard_self_rate(False), danger=True, width=22,
            )
            bad_btn.pack(side="left", padx=6)
            ok_btn.focus_set()
            self.bind("r", lambda e: self._flashcard_self_rate(True))
            self.bind("f", lambda e: self._flashcard_self_rate(False))
            self.bind("<Return>", lambda e: self._flashcard_self_rate(True))

            tk.Label(
                self.container,
                text="Raccourcis : R = bon · F = raté · Entrée = bon",
                font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
            ).pack(pady=(4, 0))

        self.make_button(
            self.container, "⬅  Retour au menu", self.show_main_menu,
        ).pack(pady=(14, 10))

    def _update_flashcard_timers(self):
        if hasattr(self, "fc_session_timer_lbl") and self.fc_session_timer_lbl.winfo_exists():
            self.fc_session_timer_lbl.configure(
                text=f"⏳ Session : {time.time() - self.fc_quiz_start:.1f}s",
            )
        if hasattr(self, "fc_card_timer_lbl") and self.fc_card_timer_lbl.winfo_exists():
            t0 = getattr(self, "fc_card_t0", self.fc_quiz_start)
            self.fc_card_timer_lbl.configure(
                text=f"⏱ Carte : {time.time() - t0:.1f}s",
            )
        if (
            hasattr(self, "fc_session_timer_lbl")
            and self.fc_session_timer_lbl.winfo_exists()
        ) or (
            hasattr(self, "fc_card_timer_lbl")
            and self.fc_card_timer_lbl.winfo_exists()
        ):
            self.after(100, self._update_flashcard_timers)

    def _reveal_flashcard(self):
        self.fc_revealed = True
        self._show_flashcard()

    def _flashcard_self_rate(self, correct):
        mode, nombre, mot = self.fc_cards[self.fc_idx]
        elapsed = time.time() - self.fc_card_t0
        self._apply_answer_stats(mode, nombre, mot, correct, elapsed)
        self.fc_results.append(
            (mode, nombre, mot, "(flashcard)", correct, elapsed))
        if correct:
            self.fc_score += 1
            self.fc_streak += 1
            self.fc_best_streak = max(self.fc_best_streak, self.fc_streak)
        else:
            self.fc_streak = 0

        last = self.fc_idx >= len(self.fc_cards) - 1
        if last:
            self._show_flashcard_end()
        else:
            self.fc_idx += 1
            self.fc_revealed = False
            self._show_flashcard()

    def _show_flashcard_end(self):
        self.clear()
        for key in ("<space>", "<Return>", "<Right>", "r", "f"):
            self.unbind(key)

        total = len(self.fc_cards)
        good = self.fc_score
        total_s = time.time() - getattr(self, "fc_quiz_start", time.time())
        tk.Label(
            self.container, text="🃏 Session terminée", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_MAUVE,
        ).pack(pady=(50, 12))
        tk.Label(
            self.container,
            text=f"Tu as indiqué {good} bonne(s) réponse(s) sur {total}.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_PRIMARY,
        ).pack(pady=(0, 8))
        tk.Label(
            self.container,
            text=f"⏳ Temps total de la session : {total_s:.1f}s",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 8))
        if self.fc_best_streak >= 2:
            tk.Label(
                self.container,
                text=f"Meilleure série : 🔥 {self.fc_best_streak}",
                font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_ORANGE,
            ).pack(pady=(0, 16))
        row = tk.Frame(self.container, bg=BG_DARK)
        row.pack(pady=20)
        self.make_button(
            row, "🃏  Nouvelle session", self.start_flashcard_mode,
            accent=True, width=22,
        ).pack(side="left", padx=8)
        self.make_button(
            row, "⬅  Menu principal", self.show_main_menu, width=20,
        ).pack(side="left", padx=8)

    # --------------------------------------------------------
    # Écran : Statistiques
    # --------------------------------------------------------
    def show_stats_view(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📊 Statistiques", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(20, 5))
        tk.Label(
            self.container,
            text="Temps moyen (s) : par lettre du mot (N→M) et par chiffre du "
                 "nombre (M→N), mis à jour sur les bonnes réponses.",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY, wraplength=720,
        ).pack(pady=(0, 8))

        # Tabs — use persistent sort state
        tab_frame = tk.Frame(self.container, bg=BG_DARK)
        tab_frame.pack(fill="x", padx=40, pady=(0, 5))

        current_tab = self._stats_sort_tab

        def make_tab(text, val):
            is_active = current_tab == val
            bg = TAB_ACTIVE_BG if is_active else BG_DARK
            fg = TAB_ACTIVE_FG if is_active else FG_SECONDARY
            btn = tk.Label(
                tab_frame, text=text, font=FONT_BODY_BOLD,
                bg=bg, fg=fg, cursor="hand2", padx=15, pady=6,
                relief="flat",
            )
            btn.pack(side="left", padx=(0, 2))
            if is_active:
                # Bright underline for active tab
                underline = tk.Frame(tab_frame, bg=FG_ACCENT, height=3)
                underline.pack(side="left", fill="x", padx=(0, 2))
            btn.bind("<Button-1>", lambda e: self._switch_stats_tab(val))
            btn.bind("<Enter>", lambda e: btn.configure(
                bg=TAB_ACTIVE_BG if not is_active else bg))
            btn.bind("<Leave>", lambda e: btn.configure(bg=bg))

        make_tab("🔻 Moins connus", "worst")
        make_tab("🔺 Plus connus", "best")
        tk.Label(
            tab_frame, text=            "(Les éléments révisés apparaissent dans Plus connus)",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(side="left", padx=(12, 0))

        # Bouton reset
        reset_btn = tk.Label(
            tab_frame, text="🗑 Réinitialiser", font=FONT_SMALL,
            bg=BG_DARK, fg=FG_RED, cursor="hand2", padx=10,
        )
        reset_btn.pack(side="right")
        reset_btn.bind("<Button-1>", lambda e: self._confirm_reset_stats())

        # Liste
        self.stats_list_frame = tk.Frame(self.container, bg=BG_DARK)
        self.stats_list_frame.pack(fill="both", expand=True, padx=40, pady=5)
        self._render_stats_list(current_tab)

        self.make_button(
            self.container, "⬅  Retour au menu", self.show_main_menu,
        ).pack(pady=(5, 15))

    def _confirm_reset_stats(self):
        if messagebox.askyesno(
            "Réinitialiser",
            "Remettre toutes les stats à zéro ? Cette action est irréversible.",
        ):
            for key in self.stats:
                self.stats[key] = _default_stats_row()
            save_stats(self.stats)
            self.show_stats_view()

    def _switch_stats_tab(self, tab):
        self._stats_sort_tab = tab
        self.show_stats_view()

    def _render_stats_list(self, mode):
        for w in self.stats_list_frame.winfo_children():
            w.destroy()

        reverse = mode == "best"
        tri = sorted(self.stats.items(),
                     key=lambda x: x[1][0] + x[1][1], reverse=reverse)

        canvas = tk.Canvas(self.stats_list_frame, bg=BG_DARK,
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.stats_list_frame, orient="vertical",
                                  command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        # Header
        hdr = tk.Frame(inner, bg=BTN_BG, pady=5)
        hdr.pack(fill="x", pady=(0, 2))
        for text, w in [("#", 4), ("Nombre", 7), ("Mot", 14),
                        ("N→M", 5), ("M→N", 5), ("s/lettre", 9), ("s/ch.", 8)]:
            tk.Label(hdr, text=text, font=FONT_SMALL, bg=BTN_BG,
                     fg=FG_SECONDARY, width=w, anchor="center").pack(
                side="left")

        for i, ((nombre, mot), vals) in enumerate(tri):
            s_nm, s_mn, t_nm, t_mn = vals
            total_score = s_nm + s_mn
            if total_score >= 4:
                row_bg = "#0d2818"
            elif total_score < 0:
                row_bg = "#28181d"
            else:
                row_bg = BG_CARD if i % 2 == 0 else BG_CARD_HOVER

            row = tk.Frame(inner, bg=row_bg, pady=3)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=str(i + 1), font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=4,
                     anchor="center").pack(side="left")
            tk.Label(row, text=nombre, font=FONT_BODY_BOLD,
                     bg=row_bg, fg=FG_ACCENT, width=7,
                     anchor="center").pack(side="left")
            tk.Label(row, text=mot, font=FONT_BODY,
                     bg=row_bg, fg=FG_PRIMARY, width=14,
                     anchor="w").pack(side="left")

            nm_color = (FG_GREEN if s_nm > 0
                        else (FG_RED if s_nm < 0 else FG_SECONDARY))
            mn_color = (FG_GREEN if s_mn > 0
                        else (FG_RED if s_mn < 0 else FG_SECONDARY))

            tk.Label(row, text=str(s_nm), font=FONT_BODY,
                     bg=row_bg, fg=nm_color, width=5,
                     anchor="center").pack(side="left")
            tk.Label(row, text=str(s_mn), font=FONT_BODY,
                     bg=row_bg, fg=mn_color, width=5,
                     anchor="center").pack(side="left")

            tnm = f"{t_nm:.2f}" if t_nm > 0 else "—"
            tmn = f"{t_mn:.2f}" if t_mn > 0 else "—"
            tk.Label(row, text=tnm, font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=9,
                     anchor="center").pack(side="left")
            tk.Label(row, text=tmn, font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=8,
                     anchor="center").pack(side="left")

    # --------------------------------------------------------
    # Écran : Parcourir la table
    # --------------------------------------------------------
    def show_table_view(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📖 Ma table", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(20, 8))

        # Barre de recherche
        search_frame = tk.Frame(self.container, bg=BG_DARK)
        search_frame.pack(fill="x", padx=60, pady=(0, 8))

        tk.Label(search_frame, text="🔍", font=FONT_BODY,
                 bg=BG_DARK, fg=FG_SECONDARY).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_table())
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat", width=30,
        )
        search_entry.pack(side="left", ipady=4)
        search_entry.focus_set()

        # Légende
        legend = tk.Frame(self.container, bg=BG_DARK)
        legend.pack(padx=60, anchor="w")
        for label, color in [("Maîtrisé", FG_GREEN), ("En cours", FG_YELLOW),
                             ("À revoir", FG_RED), ("Non vu", BTN_BG)]:
            tk.Label(legend, text="●", font=FONT_SMALL, bg=BG_DARK,
                     fg=color).pack(side="left", padx=(0, 2))
            tk.Label(legend, text=label, font=FONT_SMALL, bg=BG_DARK,
                     fg=FG_SECONDARY).pack(side="left", padx=(0, 12))
        tk.Label(legend, text="🎯", font=FONT_SMALL, bg=BG_DARK,
                 fg=FG_ORANGE).pack(side="left", padx=(8, 2))
        tk.Label(legend, text="Inclus au focus faibles", font=FONT_SMALL,
                 bg=BG_DARK, fg=FG_SECONDARY).pack(side="left", padx=(0, 12))

        # Zone table
        self.table_frame = tk.Frame(self.container, bg=BG_DARK)
        self.table_frame.pack(fill="both", expand=True, padx=40, pady=5)
        self._render_table_cards(self.table)

        btn_bar = tk.Frame(self.container, bg=BG_DARK)
        btn_bar.pack(pady=(5, 12))
        self.make_button(
            btn_bar, "⬅  Retour au menu", self.show_main_menu,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_bar, "✏️  Modifier la table", self._show_edit_table,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_bar, "📤  Exporter…", self._export_table_file,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_bar, "📥  Importer…", self._import_table_file,
        ).pack(side="left", padx=5)

    def _persist_weak_toggle(self, pair, enabled):
        """Marque / retire une paire des points faibles manuels (mode 2)."""
        if enabled:
            self.manual_weak.add(pair)
        else:
            self.manual_weak.discard(pair)
        self.manual_weak = save_manual_weak_set(self.manual_weak, self.table)

    def _filter_table(self):
        query = self.search_var.get().strip().lower()
        if query:
            filtered = [
                (n, m) for n, m in self.table
                if query in n.lower() or query in m.lower()
            ]
        else:
            filtered = self.table
        self._render_table_cards(filtered)

    def _render_table_cards(self, items):
        for w in self.table_frame.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.table_frame, bg=BG_DARK,
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical",
                                  command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        cols = 5
        for i, (nombre, mot) in enumerate(items):
            r, c = divmod(i, cols)

            vals = self.stats.get((nombre, mot), _default_stats_row())
            total_s = vals[0] + vals[1]
            if total_s >= 4:
                border_color = FG_GREEN
            elif total_s < 0:
                border_color = FG_RED
            elif total_s > 0:
                border_color = FG_YELLOW
            else:
                border_color = BTN_BG

            cell = tk.Frame(inner, bg=border_color, padx=2, pady=2)
            cell.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

            inner_cell = tk.Frame(cell, bg=BG_CARD, padx=8, pady=6)
            inner_cell.pack(fill="both", expand=True)

            tk.Label(
                inner_cell, text=nombre, font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=FG_ACCENT,
            ).pack()
            tk.Label(
                inner_cell, text=mot, font=FONT_SMALL,
                bg=BG_CARD, fg=FG_PRIMARY,
            ).pack()

            weak_var = tk.BooleanVar(value=(nombre, mot) in self.manual_weak)
            tk.Checkbutton(
                inner_cell, text="🎯 Point faible", variable=weak_var,
                command=lambda p=(nombre, mot), v=weak_var: self._persist_weak_toggle(
                    p, v.get(),
                ),
                font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY,
                selectcolor=CHECK_BG, activebackground=BG_CARD,
                activeforeground=FG_ORANGE, highlightthickness=0,
            ).pack(pady=(4, 0))

        for c in range(cols):
            inner.columnconfigure(c, weight=1, minsize=150)

    # --------------------------------------------------------
    # Écran : Éditer la table
    # --------------------------------------------------------
    def _show_edit_table(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="✏️ Modifier la table", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(20, 5))
        tk.Label(
            self.container,
            text="Modifie les mots associés à chaque nombre. "
                 "Les changements sont sauvegardés au clic.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 10))

        # Scrollable edit area
        edit_outer = tk.Frame(self.container, bg=BG_DARK)
        edit_outer.pack(fill="both", expand=True, padx=40, pady=5)

        canvas = tk.Canvas(edit_outer, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(edit_outer, orient="vertical",
                                  command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        # Header row
        hdr = tk.Frame(inner, bg=BTN_BG, pady=6)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="Nombre", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=10, anchor="center").pack(side="left")
        tk.Label(hdr, text="Mot actuel", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=20, anchor="center").pack(side="left")
        tk.Label(hdr, text="Nouveau mot", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=20, anchor="center").pack(side="left")
        tk.Label(hdr, text="", font=FONT_BODY_BOLD, bg=BTN_BG,
                 fg=FG_PRIMARY, width=12).pack(side="left")

        self._edit_entries = {}  # nombre -> StringVar

        for i, (nombre, mot) in enumerate(self.table):
            row_bg = BG_CARD if i % 2 == 0 else BG_CARD_HOVER
            row = tk.Frame(inner, bg=row_bg, pady=4)
            row.pack(fill="x", pady=1)

            # Nombre
            tk.Label(row, text=nombre, font=FONT_BODY_BOLD,
                     bg=row_bg, fg=FG_ACCENT, width=10,
                     anchor="center").pack(side="left")

            # Mot actuel
            tk.Label(row, text=mot, font=FONT_BODY,
                     bg=row_bg, fg=FG_PRIMARY, width=20,
                     anchor="center").pack(side="left")

            # Champ édition
            var = tk.StringVar(value=mot)
            self._edit_entries[nombre] = var
            entry = tk.Entry(
                row, textvariable=var, font=FONT_BODY,
                bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                relief="flat", width=20, justify="center",
            )
            entry.pack(side="left", padx=5, ipady=3)

            # Bouton sauvegarder cette ligne (Label pour macOS)
            save_btn = tk.Label(
                row, text="💾", font=FONT_BODY,
                bg=BTN_BG, fg=FG_GREEN, relief="flat",
                cursor="hand2", width=3, anchor="center", pady=3,
            )
            save_btn.bind(
                "<Button-1>",
                lambda e, n=nombre, v=var, r=row: self._save_one_entry(
                    n, v, r),
            )
            save_btn.bind("<Enter>", lambda e, b=save_btn: b.configure(bg=BTN_HOVER))
            save_btn.bind("<Leave>", lambda e, b=save_btn: b.configure(bg=BTN_BG))
            save_btn.pack(side="left", padx=5)

        # Bottom buttons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=(10, 12))
        self.make_button(
            btn_frame, "💾  Tout sauvegarder", self._save_all_entries,
            accent=True,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_frame, "📤  Exporter…", self._export_table_file,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_frame, "📥  Importer…", self._import_table_file,
        ).pack(side="left", padx=5)
        self.make_button(
            btn_frame, "⬅  Retour à la table", self.show_table_view,
        ).pack(side="left", padx=5)

    def _reset_stats_on_mot_change(self, nombre, old_mot, new_mot):
        """Nouvelle association nombre ↔ mot : les stats passées ne s'appliquent plus."""
        old_key = (nombre, old_mot)
        new_key = (nombre, new_mot)
        self.stats.pop(old_key, None)
        self.stats[new_key] = _default_stats_row()
        self.manual_weak.discard(old_key)
        self.manual_weak = save_manual_weak_set(self.manual_weak, self.table)

    def _save_one_entry(self, nombre, var, row_frame):
        """Sauvegarde un seul mot modifié."""
        new_mot = var.get().strip()
        if not new_mot:
            return

        # Trouver l'ancienne paire et mettre à jour
        for idx, (n, m) in enumerate(self.table):
            if n == nombre:
                old_mot = m
                if new_mot != old_mot:
                    # Mettre à jour la table
                    self.table[idx] = (nombre, new_mot)
                    self._reset_stats_on_mot_change(nombre, old_mot, new_mot)

                    # Flash vert pour confirmer
                    row_frame.configure(bg=FG_GREEN)
                    self.after(400, lambda rf=row_frame: rf.configure(
                        bg=BG_CARD))
                break

        self._persist_table()

    def _save_all_entries(self):
        """Sauvegarde toutes les modifications de la table."""
        changes = 0
        for idx, (nombre, old_mot) in enumerate(list(self.table)):
            var = self._edit_entries.get(nombre)
            if var:
                new_mot = var.get().strip()
                if new_mot and new_mot != old_mot:
                    self.table[idx] = (nombre, new_mot)
                    self._reset_stats_on_mot_change(nombre, old_mot, new_mot)
                    changes += 1

        self._persist_table()
        save_stats(self.stats)

        if changes > 0:
            messagebox.showinfo(
                "Sauvegardé",
                f"{changes} modification(s) enregistrée(s) !",
            )
        else:
            messagebox.showinfo("Rien à faire", "Aucune modification détectée.")

    def _export_table_file(self):
        """Exporte la table en JSON ou CSV."""
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter la table",
            defaultextension=".json",
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
            ],
        )
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                with open(path, "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["Nombre", "Mot"])
                    for n, m in self.table:
                        w.writerow([n, m])
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        [[n, m] for n, m in self.table],
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
            messagebox.showinfo(
                "Export réussi",
                f"{len(self.table)} paires enregistrées dans :\n{path}",
            )
        except OSError as e:
            messagebox.showerror("Export", str(e))

    def _import_table_file(self):
        """Importe une table depuis JSON ou CSV."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Importer une table",
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return
        try:
            new_table = parse_imported_table_file(path)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Import", str(e))
            return
        if not messagebox.askyesno(
            "Importer la table",
            f"Remplacer la table actuelle ({len(self.table)} paires) par "
            f"{len(new_table)} paires importées ?\n\n"
            "Les statistiques des paires absentes du nouveau fichier seront "
            "supprimées. Les paires identiques (même nombre et même mot) "
            "conservent leurs stats.",
        ):
            return
        merged = {}
        for n, m in new_table:
            key = (n, m)
            merged[key] = list(self.stats.get(key, _default_stats_row()))
        self.table = new_table
        self.stats = merged
        self.manual_weak = save_manual_weak_set(
            {p for p in self.manual_weak if p in set(new_table)},
            new_table,
        )
        self._persist_table()
        messagebox.showinfo(
            "Import réussi",
            f"{len(new_table)} paires chargées et enregistrées.",
        )
        self.show_table_view()

    def _persist_table(self):
        """Écrit la table modifiée en JSON."""
        path = _table_path()
        data = [[n, m] for n, m in self.table]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
            f.flush()
            os.fsync(f.fileno())
        save_stats(self.stats)


# ============================================================
# Point d'entrée
# ============================================================
if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
