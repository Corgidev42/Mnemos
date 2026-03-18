#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table de Rappel — Quiz GUI (v2)
Interface graphique pour apprendre et réviser la table de rappel.
Améliorations v2 :
  - Mode Flashcard (révision sans stress)
  - Raccourcis clavier (Échap, Entrée, chiffres)
  - Auto-avance après bonne réponse
  - Streak (série) de bonnes réponses
  - Scroll macOS natif
  - Centrage fenêtre
  - Meilleure UX globale
"""

import csv
import json
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

# Version — incrémenter à chaque release (ex: v1.0.1)
VERSION = "1.0.0"
GITHUB_REPO = "Corgidev42/TableDeRappel-v2"

# ============================================================
# Constantes de style — thème Catppuccin Mocha
# ============================================================
BG_DARK = "#1e1e2e"
BG_CARD = "#2a2a3d"
BG_INPUT = "#3a3a5c"
FG_PRIMARY = "#e4e8f7"          # brighter white for better contrast
FG_SECONDARY = "#b0b8d1"        # slightly brighter secondary
FG_ACCENT = "#89b4fa"
FG_GREEN = "#a6e3a1"
FG_RED = "#f38ba8"
FG_YELLOW = "#f9e2af"
FG_MAUVE = "#cba6f7"
FG_ORANGE = "#fab387"
BTN_BG = "#45475a"
BTN_HOVER = "#585b70"
BTN_ACCENT = "#5d8fd6"           # darker blue for better text contrast
BTN_ACCENT_FG = "#ffffff"        # white text on accent buttons
TAB_ACTIVE_BG = "#3d3f58"        # visible active tab background
TAB_ACTIVE_FG = "#ffffff"        # bright white active tab text
CHECK_ON = "#a6e3a1"             # green indicator when checked
CHECK_BG = "#2a2a3d"             # checkbox background

FONT_TITLE = ("Helvetica", 28, "bold")
FONT_SUBTITLE = ("Helvetica", 16)
FONT_BODY = ("Helvetica", 13)
FONT_BODY_BOLD = ("Helvetica", 13, "bold")
FONT_SMALL = ("Helvetica", 11)
FONT_BIG = ("Helvetica", 42, "bold")
FONT_HUGE = ("Helvetica", 56, "bold")
FONT_QUESTION = ("Helvetica", 20)
FONT_INPUT = ("Helvetica", 18)
FONT_STREAK = ("Helvetica", 15, "bold")

# Auto-avance (ms) après une bonne réponse
AUTO_ADVANCE_MS = 1200

# ============================================================
# Données — chemins adaptés pour .app (bundle read-only)
# ============================================================
def _get_data_paths():
    """Retourne (table_path, stats_path) pour dev ou .app."""
    if getattr(sys, "frozen", False):
        # Mode .app : données dans ~/Library/Application Support
        app_support = os.path.join(
            os.path.expanduser("~"),
            "Library", "Application Support", "TableDeRappel"
        )
        os.makedirs(app_support, exist_ok=True)
        bundle_dir = sys._MEIPASS  # ressources du bundle
        table_bundle = os.path.join(bundle_dir, "table_rappel.csv")
        stats_bundle = os.path.join(bundle_dir, "stats_rappel.csv")
        table_path = os.path.join(app_support, "table_rappel.csv")
        stats_path = os.path.join(app_support, "stats_rappel.csv")
        # Copier la table par défaut si pas encore initialisée
        if not os.path.exists(table_path) and os.path.exists(table_bundle):
            shutil.copy(table_bundle, table_path)
        if not os.path.exists(stats_path) and os.path.exists(stats_bundle):
            shutil.copy(stats_bundle, stats_path)
        return table_path, stats_path
    # Mode développement
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return (
        os.path.join(base_dir, "table_rappel.csv"),
        os.path.join(base_dir, "stats_rappel.csv"),
    )

TABLE_FILE, STATS_FILE = _get_data_paths()


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
                # Chercher un .dmg dans les assets
                dmg_url = None
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".dmg"):
                        dmg_url = asset.get("browser_download_url")
                        break
                callback(True, {"tag": tag, "url": dmg_url, "body": data.get("body", "")})
            else:
                callback(True, {"up_to_date": True})
        except Exception as e:
            callback(False, str(e))

    threading.Thread(target=_do_check, daemon=True).start()


def download_and_open_dmg(url, callback):
    """Télécharge le .dmg et l'ouvre. callback(success, message)."""

    def _do_download():
        try:
            dest = os.path.join(tempfile.gettempdir(), "TableDeRappel_update.dmg")
            urllib.request.urlretrieve(url, dest)
            os.system(f'open "{dest}"')  # macOS : monte le .dmg
            callback(True, "Le fichier .dmg a été téléchargé et ouvert. Glisse « Table de Rappel » dans le dossier Applications pour terminer la mise à jour.")
        except Exception as e:
            callback(False, str(e))

    threading.Thread(target=_do_download, daemon=True).start()


def load_table():
    """Charge la table de rappel depuis le CSV."""
    table = []
    with open(TABLE_FILE, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for row in reader:
            if len(row) >= 2 and row[1].strip():
                table.append((row[0].strip(), row[1].strip()))
    return table


def load_stats(table):
    """Charge ou initialise les stats."""
    stats = {}
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) == 4:
                    nombre, mot, s_nm, s_mn = row
                    stats[(nombre, mot)] = [int(s_nm), int(s_mn), 0.0]
                elif len(row) >= 5:
                    nombre, mot, s_nm, s_mn, t = row
                    stats[(nombre, mot)] = [int(s_nm), int(s_mn), float(t)]
    for nombre, mot in table:
        if (nombre, mot) not in stats:
            stats[(nombre, mot)] = [0, 0, 0.0]
    return stats


def save_stats(stats):
    """Sauvegarde les stats."""
    with open(STATS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Nombre", "Mot", "Score_nombre->mot",
                         "Score_mot->nombre", "Temps_moyen_par_lettre"])
        for (nombre, mot), (s_nm, s_mn, t) in stats.items():
            writer.writerow([nombre, mot, s_nm, s_mn, f"{t:.3f}"])


# ============================================================
# Application principale
# ============================================================
class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Table de Rappel — Quiz v{VERSION}")
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

        # Démarrer avec le menu
        self.show_main_menu()

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
            bg, fg, hover_bg = FG_RED, "#ffffff", "#e06080"
        elif accent:
            bg, fg, hover_bg = BTN_ACCENT, BTN_ACCENT_FG, "#4a7abd"
        else:
            bg, fg, hover_bg = BTN_BG, FG_PRIMARY, BTN_HOVER

        # Use tk.Label instead of tk.Button — macOS ignores bg/fg on
        # native Aqua buttons, but Labels always respect colors.
        btn = tk.Label(
            parent, text=text,
            font=FONT_BODY_BOLD, bg=bg, fg=fg,
            cursor="hand2", width=width, pady=8,
            relief="flat", anchor="center",
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    def make_card(self, parent, **kwargs):
        return tk.Frame(parent, bg=BG_CARD, padx=20, pady=15, **kwargs)

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

        # Titre
        tk.Label(
            self.container, text="🧠 Table de Rappel", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT,
        ).pack(pady=(35, 3))
        tk.Label(
            self.container, text="Entraîne ta mémoire avec le système majeur",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 25))

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
            ("3", "🎲  Quiz aléatoire (20 Q)", self.start_random_mode),
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

        # Footer
        footer_row = tk.Frame(self.container, bg=BG_DARK)
        footer_row.pack(side="bottom", pady=(0, 10))
        tk.Label(
            footer_row,
            text="Raccourcis : 1-5 = modes · Échap = menu · Entrée = valider",
            font=FONT_SMALL, bg=BG_DARK, fg="#585b70",
        ).pack(side="left")
        # Lien mise à jour
        upd_lbl = tk.Label(
            footer_row, text="  ·  🔄 Vérifier les mises à jour",
            font=FONT_SMALL, bg=BG_DARK, fg=FG_ACCENT, cursor="hand2",
        )
        upd_lbl.pack(side="left")
        upd_lbl.bind("<Button-1>", lambda e: self._check_update())

    def _draw_mastery_bar(self, canvas, total, ok, en_cours, revoir, non_vus):
        """Dessine une barre de progression colorée de la maîtrise globale."""
        canvas.update_idletasks()
        w = canvas.winfo_width()
        if total == 0 or w <= 0:
            return
        segments = [
            (ok, FG_GREEN), (en_cours, FG_YELLOW),
            (revoir, FG_RED), (non_vus, "#45475a"),
        ]
        x = 0
        for count, color in segments:
            seg_w = int(w * count / total)
            if seg_w > 0:
                canvas.create_rectangle(x, 0, x + seg_w, 12,
                                        fill=color, outline="")
            x += seg_w

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
            url = result.get("url")
            if url:
                if messagebox.askyesno(
                    "Mise à jour disponible",
                    f"Une nouvelle version ({tag}) est disponible. Télécharger ?",
                ):
                    download_and_open_dmg(url, self._on_download_result)
            else:
                messagebox.showinfo(
                    "Mise à jour disponible",
                    f"Version {tag} disponible. Rends-toi sur GitHub pour la télécharger.",
                )

        self.after(0, _show)

    def _on_download_result(self, success, message):
        """Callback après téléchargement du .dmg (thread)."""
        def _show():
            if success:
                messagebox.showinfo("Téléchargement terminé", message)
            else:
                messagebox.showerror("Erreur", f"Échec du téléchargement : {message}")

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
        tri = sorted(self.stats.items(),
                     key=lambda x: x[1][0] + x[1][1])
        faibles = [k for k, v in tri[:20]]
        self._build_questions(faibles)

    def start_random_mode(self):
        self._show_sens_then_start(self._do_start_random)

    def _do_start_random(self):
        pairs = [random.choice(self.table) for _ in range(20)]
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
        for key in ("1", "2", "3", "4", "5"):
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
            ).pack(side="right")

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
        self._update_timer()

    def _draw_progress(self, canvas, current, total):
        canvas.update_idletasks()
        w = canvas.winfo_width()
        fill_w = int(w * (current - 1) / total)
        canvas.create_rectangle(0, 0, fill_w, 6, fill=FG_ACCENT, outline="")

    def _update_timer(self):
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            elapsed = time.time() - self.question_start_time
            self.timer_label.configure(text=f"⏱ {elapsed:.1f}s")
            self.after(100, self._update_timer)

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

        # Mise à jour des stats
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
            else:
                self.stats[(nombre, mot)][1] -= 1

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

        # Auto-avance si correct
        if correct and self.current_q < total:
            # Countdown label
            countdown_lbl = tk.Label(
                self.container, text=f"Suite automatique…",
                font=FONT_SMALL, bg=BG_DARK, fg="#585b70",
            )
            countdown_lbl.pack()
            self._auto_advance_id = self.after(AUTO_ADVANCE_MS, btn_cmd)

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
            text=f"{pct:.0f}%  ·  {total_time:.1f}s  ·  "
                 f"Meilleure série : {self.best_streak} 🔥",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY,
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
            btn_frame, "🚪  Quitter", self.destroy,
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
    def start_flashcard_mode(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="🃏 Mode Flashcard", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_MAUVE,
        ).pack(pady=(40, 10))
        tk.Label(
            self.container,
            text="Révise sans pression ! Clique ou appuie sur Espace "
                 "pour retourner la carte.",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY,
        ).pack(pady=(0, 20))

        # Options de blocs (simplifié)
        card = self.make_card(self.container)
        card.pack(padx=100, fill="x")

        tk.Label(card, text="Plage de nombres :", font=FONT_BODY_BOLD,
                 bg=BG_CARD, fg=FG_PRIMARY).pack(anchor="w")

        range_frame = tk.Frame(card, bg=BG_CARD)
        range_frame.pack(fill="x", pady=5)

        tk.Label(range_frame, text="De", font=FONT_BODY,
                 bg=BG_CARD, fg=FG_SECONDARY).pack(side="left", padx=(0, 5))
        self.fc_start_var = tk.StringVar(value="0")
        tk.Entry(
            range_frame, textvariable=self.fc_start_var, font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", width=6, justify="center",
        ).pack(side="left", ipady=3)

        tk.Label(range_frame, text="  à  ", font=FONT_BODY,
                 bg=BG_CARD, fg=FG_SECONDARY).pack(side="left")
        self.fc_end_var = tk.StringVar(value="100")
        tk.Entry(
            range_frame, textvariable=self.fc_end_var, font=FONT_BODY,
            bg=BG_INPUT, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief="flat", width=6, justify="center",
        ).pack(side="left", ipady=3)

        # Mélanger ?
        self.fc_shuffle_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card, text="  Ordre aléatoire", variable=self.fc_shuffle_var,
            font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY,
            selectcolor=CHECK_BG, activebackground=BG_CARD,
            activeforeground=CHECK_ON, highlightthickness=0,
        ).pack(anchor="w", pady=5)

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=20)
        self.make_button(
            btn_frame, "🃏  Commencer", self._launch_flashcards, accent=True,
        ).pack(side="left", padx=10)
        self.make_button(
            btn_frame, "⬅  Retour", self.show_main_menu,
        ).pack(side="left", padx=10)

    def _launch_flashcards(self):
        try:
            s = int(self.fc_start_var.get())
            e = int(self.fc_end_var.get())
        except ValueError:
            messagebox.showwarning("Attention", "Plage invalide (nombres).")
            return

        self.fc_cards = [
            (n, m) for n, m in self.table if s <= int(n) <= e
        ]
        if not self.fc_cards:
            messagebox.showwarning("Attention", "Aucune carte dans cette plage.")
            return

        if self.fc_shuffle_var.get():
            random.shuffle(self.fc_cards)

        self.fc_idx = 0
        self.fc_revealed = False
        self._show_flashcard()

    def _show_flashcard(self):
        self.clear()

        nombre, mot = self.fc_cards[self.fc_idx]
        total = len(self.fc_cards)
        idx = self.fc_idx + 1

        # Barre
        tk.Label(
            self.container,
            text=f"🃏 Flashcard {idx}/{total}",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_MAUVE,
        ).pack(pady=(20, 5))

        bar = tk.Canvas(self.container, height=4, bg=BTN_BG,
                        highlightthickness=0)
        bar.pack(fill="x", padx=60, pady=(0, 10))
        self.after(50, lambda: self._draw_progress(bar, idx, total))

        # Carte
        card = tk.Frame(
            self.container, bg=FG_MAUVE, padx=3, pady=3,
        )
        card.pack(padx=120, pady=20, fill="x")

        inner = tk.Frame(card, bg=BG_CARD, padx=30, pady=30)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner, text=nombre, font=FONT_BIG,
            bg=BG_CARD, fg=FG_ACCENT,
        ).pack(pady=(10, 15))

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

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=10)

        if not self.fc_revealed:
            btn = self.make_button(
                btn_frame, "Retourner (Espace)",
                self._reveal_flashcard, accent=True, width=22,
            )
            btn.pack()
            btn.focus_set()
            self.bind("<space>", lambda e: self._reveal_flashcard())
            self.bind("<Return>", lambda e: self._reveal_flashcard())
        else:
            self.unbind("<space>")
            self.unbind("<Return>")

            if self.fc_idx < total - 1:
                next_btn = self.make_button(
                    btn_frame, "Suivante →", self._next_flashcard,
                    accent=True, width=15,
                )
                next_btn.pack(side="left", padx=5)
                next_btn.focus_set()
                self.bind("<Return>", lambda e: self._next_flashcard())
                self.bind("<Right>", lambda e: self._next_flashcard())
            else:
                done_btn = self.make_button(
                    btn_frame, "Terminé ✓", self.show_main_menu,
                    accent=True, width=15,
                )
                done_btn.pack(side="left", padx=5)
                done_btn.focus_set()
                self.bind("<Return>", lambda e: self.show_main_menu())

            if self.fc_idx > 0:
                self.make_button(
                    btn_frame, "← Précédente", self._prev_flashcard, width=15,
                ).pack(side="left", padx=5)
                self.bind("<Left>", lambda e: self._prev_flashcard())

        # Retour
        self.make_button(
            self.container, "⬅  Retour au menu", self.show_main_menu,
        ).pack(pady=(15, 10))

    def _reveal_flashcard(self):
        self.fc_revealed = True
        self._show_flashcard()

    def _next_flashcard(self):
        self.fc_idx += 1
        self.fc_revealed = False
        self._show_flashcard()

    def _prev_flashcard(self):
        self.fc_idx -= 1
        self.fc_revealed = False
        self._show_flashcard()

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
                self.stats[key] = [0, 0, 0.0]
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
        for text, w in [("#", 4), ("Nombre", 8), ("Mot", 18),
                        ("N→M", 6), ("M→N", 6), ("Temps/l.", 12)]:
            tk.Label(hdr, text=text, font=FONT_SMALL, bg=BTN_BG,
                     fg=FG_SECONDARY, width=w, anchor="center").pack(
                side="left")

        for i, ((nombre, mot), vals) in enumerate(tri):
            s_nm, s_mn, t = vals
            total_score = s_nm + s_mn
            if total_score >= 4:
                row_bg = "#1e3a2e"
            elif total_score < 0:
                row_bg = "#3a1e2e"
            else:
                row_bg = BG_CARD if i % 2 == 0 else "#252540"

            row = tk.Frame(inner, bg=row_bg, pady=3)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=str(i + 1), font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=4,
                     anchor="center").pack(side="left")
            tk.Label(row, text=nombre, font=FONT_BODY_BOLD,
                     bg=row_bg, fg=FG_ACCENT, width=8,
                     anchor="center").pack(side="left")
            tk.Label(row, text=mot, font=FONT_BODY,
                     bg=row_bg, fg=FG_PRIMARY, width=18,
                     anchor="w").pack(side="left")

            nm_color = (FG_GREEN if s_nm > 0
                        else (FG_RED if s_nm < 0 else FG_SECONDARY))
            mn_color = (FG_GREEN if s_mn > 0
                        else (FG_RED if s_mn < 0 else FG_SECONDARY))

            tk.Label(row, text=str(s_nm), font=FONT_BODY,
                     bg=row_bg, fg=nm_color, width=6,
                     anchor="center").pack(side="left")
            tk.Label(row, text=str(s_mn), font=FONT_BODY,
                     bg=row_bg, fg=mn_color, width=6,
                     anchor="center").pack(side="left")

            t_text = f"{t:.2f}s" if t > 0 else "—"
            tk.Label(row, text=t_text, font=FONT_SMALL,
                     bg=row_bg, fg=FG_SECONDARY, width=12,
                     anchor="center").pack(side="left")

    # --------------------------------------------------------
    # Écran : Parcourir la table
    # --------------------------------------------------------
    def show_table_view(self):
        self.clear()
        self._unbind_menu_keys()

        tk.Label(
            self.container, text="📖 Table de Rappel", font=FONT_TITLE,
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

            vals = self.stats.get((nombre, mot), [0, 0, 0.0])
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
            row_bg = BG_CARD if i % 2 == 0 else "#252540"
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
            btn_frame, "⬅  Retour à la table", self.show_table_view,
        ).pack(side="left", padx=5)

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

                    # Transférer les stats
                    old_key = (nombre, old_mot)
                    new_key = (nombre, new_mot)
                    if old_key in self.stats:
                        self.stats[new_key] = self.stats.pop(old_key)
                    elif new_key not in self.stats:
                        self.stats[new_key] = [0, 0, 0.0]

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
                    old_key = (nombre, old_mot)
                    new_key = (nombre, new_mot)
                    if old_key in self.stats:
                        self.stats[new_key] = self.stats.pop(old_key)
                    elif new_key not in self.stats:
                        self.stats[new_key] = [0, 0, 0.0]
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

    def _persist_table(self):
        """Écrit la table de rappel dans le CSV."""
        with open(TABLE_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Nombre", "Mot"])
            for nombre, mot in self.table:
                writer.writerow([nombre, mot])
        save_stats(self.stats)


# ============================================================
# Point d'entrée
# ============================================================
if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
