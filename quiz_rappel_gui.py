#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table de Rappel - Quiz GUI (v2)
Interface graphique pour apprendre et réviser la table de rappel.
"""

import csv
import random
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ============================================================
# Constantes de style
# ============================================================
BG_DARK = "#1e1e2e"
BG_CARD = "#2a2a3d"
BG_INPUT = "#3a3a5c"
FG_PRIMARY = "#cdd6f4"
FG_SECONDARY = "#a6adc8"
FG_ACCENT = "#89b4fa"
FG_GREEN = "#a6e3a1"
FG_RED = "#f38ba8"
FG_YELLOW = "#f9e2af"
FG_MAUVE = "#cba6f7"
BTN_BG = "#45475a"
BTN_HOVER = "#585b70"
BTN_ACCENT = "#89b4fa"
BTN_ACCENT_FG = "#1e1e2e"
FONT_TITLE = ("Helvetica", 28, "bold")
FONT_SUBTITLE = ("Helvetica", 16)
FONT_BODY = ("Helvetica", 13)
FONT_BODY_BOLD = ("Helvetica", 13, "bold")
FONT_SMALL = ("Helvetica", 11)
FONT_BIG = ("Helvetica", 42, "bold")
FONT_QUESTION = ("Helvetica", 20)
FONT_INPUT = ("Helvetica", 18)

# ============================================================
# Données
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TABLE_FILE = os.path.join(BASE_DIR, "table_rappel.csv")
STATS_FILE = os.path.join(BASE_DIR, "stats_rappel.csv")


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
        writer.writerow(["Nombre", "Mot", "Score_nombre->mot", "Score_mot->nombre", "Temps_moyen_par_lettre"])
        for (nombre, mot), (s_nm, s_mn, t) in stats.items():
            writer.writerow([nombre, mot, s_nm, s_mn, f"{t:.3f}"])


# ============================================================
# Application principale
# ============================================================
class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Table de Rappel — Quiz v2")
        self.configure(bg=BG_DARK)
        self.minsize(900, 650)
        self.geometry("960x700")

        # Données
        self.table = load_table()
        self.stats = load_stats(self.table)

        # Variables de quiz
        self.questions = []
        self.current_q = 0
        self.score = 0
        self.quiz_start_time = 0
        self.question_start_time = 0
        self.results = []  # (mode, nombre, mot, user_answer, correct, time)

        # Container principal
        self.container = tk.Frame(self, bg=BG_DARK)
        self.container.pack(fill="both", expand=True)

        # Démarrer avec le menu
        self.show_main_menu()

    # --------------------------------------------------------
    # Utilitaires UI
    # --------------------------------------------------------
    def clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def make_button(self, parent, text, command, accent=False, width=25):
        bg = BTN_ACCENT if accent else BTN_BG
        fg = BTN_ACCENT_FG if accent else FG_PRIMARY
        hover_bg = "#7aa2f7" if accent else BTN_HOVER
        btn = tk.Button(
            parent, text=text, command=command,
            font=FONT_BODY_BOLD, bg=bg, fg=fg,
            activebackground=hover_bg, activeforeground=fg,
            relief="flat", cursor="hand2", width=width, pady=8
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    def make_card(self, parent, **kwargs):
        frame = tk.Frame(parent, bg=BG_CARD, padx=20, pady=15, **kwargs)
        return frame

    # --------------------------------------------------------
    # Écran : Menu principal
    # --------------------------------------------------------
    def show_main_menu(self):
        self.clear()

        # Titre
        tk.Label(
            self.container, text="🧠 Table de Rappel", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT
        ).pack(pady=(40, 5))
        tk.Label(
            self.container, text="Entraîne ta mémoire avec le système majeur",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY
        ).pack(pady=(0, 30))

        # Stats résumé
        total = len(self.stats)
        bien_connus = sum(1 for v in self.stats.values() if v[0] + v[1] >= 4)
        en_cours = sum(1 for v in self.stats.values() if 0 < v[0] + v[1] < 4)
        a_revoir = sum(1 for v in self.stats.values() if v[0] + v[1] <= 0 and (v[0] != 0 or v[1] != 0))
        non_vus = sum(1 for v in self.stats.values() if v[0] == 0 and v[1] == 0)

        stats_frame = self.make_card(self.container)
        stats_frame.pack(pady=(0, 25), padx=60, fill="x")

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
            tk.Label(col, text=str(value), font=("Helvetica", 22, "bold"), bg=BG_CARD, fg=color).pack()
            tk.Label(col, text=label, font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY).pack()

        # Boutons modes
        modes_frame = tk.Frame(self.container, bg=BG_DARK)
        modes_frame.pack(pady=5)

        modes = [
            ("📦  Quiz par bloc", self.show_bloc_config),
            ("🎯  Focus points faibles", self.start_focus_mode),
            ("🎲  Quiz aléatoire (20 Q)", self.start_random_mode),
            ("📋  Toute la table", self.start_full_mode),
        ]
        for text, cmd in modes:
            self.make_button(modes_frame, text, cmd, accent=False, width=30).pack(pady=5)

        # Boutons secondaires
        bottom_frame = tk.Frame(self.container, bg=BG_DARK)
        bottom_frame.pack(pady=(20, 10))
        self.make_button(bottom_frame, "📊  Voir les statistiques", self.show_stats_view, width=30).pack(side="left", padx=5)
        self.make_button(bottom_frame, "📖  Parcourir la table", self.show_table_view, width=30).pack(side="left", padx=5)

    # --------------------------------------------------------
    # Écran : Configuration bloc
    # --------------------------------------------------------
    def show_bloc_config(self):
        self.clear()

        tk.Label(
            self.container, text="📦 Quiz par bloc", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT
        ).pack(pady=(40, 20))

        card = self.make_card(self.container)
        card.pack(padx=80, fill="x")

        tk.Label(
            card, text="Sélectionne la plage de blocs (ex: 0-9 = bloc 0, 10-19 = bloc 1, …)",
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY, wraplength=600
        ).pack(pady=(5, 15))

        # Grille de sélection de blocs
        blocs_frame = tk.Frame(card, bg=BG_CARD)
        blocs_frame.pack(pady=10)

        self.bloc_vars = {}
        for i in range(11):  # 0..10
            start = i * 10
            end = min(start + 9, 100)
            var = tk.BooleanVar(value=False)
            self.bloc_vars[i] = var
            cb = tk.Checkbutton(
                blocs_frame, text=f"{start}-{end}", variable=var,
                font=FONT_BODY, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=FG_PRIMARY,
                highlightthickness=0
            )
            cb.grid(row=i // 4, column=i % 4, padx=12, pady=5, sticky="w")

        # Sens
        sens_frame = tk.Frame(card, bg=BG_CARD)
        sens_frame.pack(pady=(15, 5))
        tk.Label(sens_frame, text="Direction :", font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_PRIMARY).pack(side="left", padx=(0, 10))

        self.sens_var = tk.StringVar(value="3")
        for text, val in [("Nombre → Mot", "1"), ("Mot → Nombre", "2"), ("Les deux", "3")]:
            tk.Radiobutton(
                sens_frame, text=text, variable=self.sens_var, value=val,
                font=FONT_BODY, bg=BG_CARD, fg=FG_PRIMARY,
                selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=FG_PRIMARY,
                highlightthickness=0
            ).pack(side="left", padx=8)

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=25)
        self.make_button(btn_frame, "🚀  Lancer le quiz", self._start_bloc_quiz, accent=True).pack(side="left", padx=10)
        self.make_button(btn_frame, "⬅  Retour", self.show_main_menu).pack(side="left", padx=10)

    def _start_bloc_quiz(self):
        selected = [i for i, v in self.bloc_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Attention", "Sélectionne au moins un bloc !")
            return

        pairs = []
        for bloc_i in selected:
            start = bloc_i * 10
            end = min(start + 9, 100)
            pairs.extend([p for p in self.table if start <= int(p[0]) <= end])

        if not pairs:
            messagebox.showwarning("Attention", "Aucune correspondance trouvée pour ces blocs.")
            return

        self._build_questions(pairs)

    # --------------------------------------------------------
    # Modes de démarrage rapide
    # --------------------------------------------------------
    def start_focus_mode(self):
        self._show_sens_then_start(self._do_start_focus)

    def _do_start_focus(self):
        tri = sorted(self.stats.items(), key=lambda x: x[1][0] + x[1][1])
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

        tk.Label(
            self.container, text="Direction du quiz", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT
        ).pack(pady=(60, 30))

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
                selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=FG_PRIMARY,
                highlightthickness=0, anchor="w"
            ).pack(anchor="w")
            tk.Label(f, text=f"       {desc}", font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY).pack(anchor="w")

        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=30)
        self.make_button(btn_frame, "🚀  Lancer", callback, accent=True).pack(side="left", padx=10)
        self.make_button(btn_frame, "⬅  Retour", self.show_main_menu).pack(side="left", padx=10)

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
        self.results = []
        self.quiz_start_time = time.time()
        self.question_start_time = time.time()
        self._show_question()

    # --------------------------------------------------------
    # Écran : Question du quiz
    # --------------------------------------------------------
    def _show_question(self):
        self.clear()

        mode, nombre, mot = self.questions[self.current_q]
        total = len(self.questions)
        idx = self.current_q + 1

        # Barre de progression
        progress_frame = tk.Frame(self.container, bg=BG_DARK)
        progress_frame.pack(fill="x", padx=40, pady=(20, 0))

        tk.Label(
            progress_frame, text=f"Question {idx}/{total}",
            font=FONT_BODY_BOLD, bg=BG_DARK, fg=FG_SECONDARY
        ).pack(side="left")

        tk.Label(
            progress_frame, text=f"Score : {self.score}/{idx - 1}" if idx > 1 else "",
            font=FONT_BODY, bg=BG_DARK, fg=FG_GREEN
        ).pack(side="right")

        # Progress bar
        bar_frame = tk.Frame(self.container, bg=BG_DARK, height=6)
        bar_frame.pack(fill="x", padx=40, pady=(5, 0))

        canvas = tk.Canvas(bar_frame, height=6, bg=BTN_BG, highlightthickness=0)
        canvas.pack(fill="x")
        self.after(50, lambda: self._draw_progress(canvas, idx, total))

        # Zone question
        q_frame = tk.Frame(self.container, bg=BG_DARK)
        q_frame.pack(expand=True, fill="both", padx=40)

        if mode == "nombre->mot":
            tk.Label(
                q_frame, text="Quel mot correspond au nombre…",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY
            ).pack(pady=(30, 10))
            tk.Label(
                q_frame, text=nombre, font=FONT_BIG,
                bg=BG_DARK, fg=FG_ACCENT
            ).pack(pady=(0, 20))
        else:
            tk.Label(
                q_frame, text="Quel nombre correspond au mot…",
                font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY
            ).pack(pady=(30, 10))
            tk.Label(
                q_frame, text=mot, font=FONT_BIG,
                bg=BG_DARK, fg=FG_GREEN
            ).pack(pady=(0, 20))

        # Input
        self.answer_var = tk.StringVar()
        entry = tk.Entry(
            q_frame, textvariable=self.answer_var,
            font=FONT_INPUT, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat",
            justify="center", width=25
        )
        entry.pack(ipady=8, pady=(0, 15))
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._submit_answer())

        # Bouton valider
        self.make_button(q_frame, "Valider ↵", self._submit_answer, accent=True, width=20).pack()

        # Timer live
        self.timer_label = tk.Label(
            q_frame, text="⏱ 0.0s", font=FONT_SMALL, bg=BG_DARK, fg=FG_SECONDARY
        )
        self.timer_label.pack(pady=(15, 0))
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

        # Update stats
        if mode == "nombre->mot":
            if correct:
                self.stats[(nombre, mot)][0] += 1
                nb_lettres = len(mot)
                if nb_lettres > 0:
                    tpl = elapsed / nb_lettres
                    ancien = self.stats[(nombre, mot)][2]
                    self.stats[(nombre, mot)][2] = tpl if ancien == 0 else (ancien + tpl) / 2
            else:
                self.stats[(nombre, mot)][0] -= 1
        else:
            if correct:
                self.stats[(nombre, mot)][1] += 1
            else:
                self.stats[(nombre, mot)][1] -= 1

        if correct:
            self.score += 1

        self.results.append((mode, nombre, mot, answer, correct, elapsed))
        self.question_start_time = time.time()

        # Show feedback
        self._show_feedback(correct, expected, elapsed)

    # --------------------------------------------------------
    # Écran : Feedback après réponse
    # --------------------------------------------------------
    def _show_feedback(self, correct, expected, elapsed):
        self.clear()

        mode, nombre, mot, answer, _, _ = self.results[-1]

        # Icône et message
        if correct:
            icon = "✅"
            msg = "Correct !"
            color = FG_GREEN
        else:
            icon = "❌"
            msg = "Mauvaise réponse"
            color = FG_RED

        tk.Label(
            self.container, text=icon, font=("Helvetica", 64),
            bg=BG_DARK, fg=color
        ).pack(pady=(50, 5))
        tk.Label(
            self.container, text=msg, font=FONT_TITLE,
            bg=BG_DARK, fg=color
        ).pack(pady=(0, 15))

        # Détails
        card = self.make_card(self.container)
        card.pack(padx=120)

        if not correct:
            tk.Label(
                card, text=f"Ta réponse : {answer}", font=FONT_BODY,
                bg=BG_CARD, fg=FG_RED
            ).pack(anchor="w", pady=2)
            tk.Label(
                card, text=f"Bonne réponse : {expected}", font=FONT_BODY_BOLD,
                bg=BG_CARD, fg=FG_GREEN
            ).pack(anchor="w", pady=2)

        tk.Label(
            card, text=f"{nombre}  ↔  {mot}",
            font=FONT_QUESTION, bg=BG_CARD, fg=FG_ACCENT
        ).pack(pady=(10, 5))
        tk.Label(
            card, text=f"⏱ {elapsed:.1f}s",
            font=FONT_BODY, bg=BG_CARD, fg=FG_SECONDARY
        ).pack()

        # Progression
        idx = self.current_q + 1
        total = len(self.questions)
        tk.Label(
            self.container, text=f"{idx}/{total} — Score : {self.score}/{idx}",
            font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY
        ).pack(pady=(15, 0))

        # Bouton suivant / terminer
        self.current_q += 1
        if self.current_q < total:
            btn_text = "Question suivante →"
            btn_cmd = self._show_question
        else:
            btn_text = "Voir les résultats 🏁"
            btn_cmd = self._show_results

        btn = self.make_button(self.container, btn_text, btn_cmd, accent=True, width=25)
        btn.pack(pady=25)
        self.bind("<Return>", lambda e: btn_cmd())
        btn.focus_set()

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
            bg=BG_DARK, fg=FG_ACCENT
        ).pack(pady=(30, 15))

        # Score principal
        score_color = FG_GREEN if pct >= 80 else (FG_YELLOW if pct >= 50 else FG_RED)
        tk.Label(
            self.container, text=f"{self.score}/{total_q}",
            font=("Helvetica", 56, "bold"), bg=BG_DARK, fg=score_color
        ).pack()
        tk.Label(
            self.container, text=f"{pct:.0f}% — Temps total : {total_time:.1f}s",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_SECONDARY
        ).pack(pady=(0, 15))

        # Détail des erreurs
        errors = [r for r in self.results if not r[4]]
        if errors:
            err_card = self.make_card(self.container)
            err_card.pack(padx=60, fill="x", pady=(0, 10))

            tk.Label(
                err_card, text=f"❌ {len(errors)} erreur(s) à revoir :",
                font=FONT_BODY_BOLD, bg=BG_CARD, fg=FG_RED
            ).pack(anchor="w", pady=(0, 8))

            # Scrollable list
            list_frame = tk.Frame(err_card, bg=BG_CARD)
            list_frame.pack(fill="x")

            for mode, nombre, mot, answer, _, t in errors[:15]:
                direction = "→" if mode == "nombre->mot" else "←"
                line = f"  {nombre} {direction} {mot}  (ta réponse : {answer}, {t:.1f}s)"
                tk.Label(
                    list_frame, text=line, font=FONT_SMALL,
                    bg=BG_CARD, fg=FG_SECONDARY, anchor="w"
                ).pack(anchor="w")
            if len(errors) > 15:
                tk.Label(
                    list_frame, text=f"  … et {len(errors) - 15} autre(s)",
                    font=FONT_SMALL, bg=BG_CARD, fg=FG_SECONDARY
                ).pack(anchor="w")
        else:
            tk.Label(
                self.container, text="🎉 Aucune erreur ! Parfait !",
                font=FONT_SUBTITLE, bg=BG_DARK, fg=FG_GREEN
            ).pack(pady=10)

        # Boutons
        btn_frame = tk.Frame(self.container, bg=BG_DARK)
        btn_frame.pack(pady=20)
        self.make_button(btn_frame, "🔄  Recommencer", self.show_main_menu, accent=True).pack(side="left", padx=10)
        self.make_button(btn_frame, "🚪  Quitter", self.destroy).pack(side="left", padx=10)

    # --------------------------------------------------------
    # Écran : Voir les statistiques
    # --------------------------------------------------------
    def show_stats_view(self):
        self.clear()

        tk.Label(
            self.container, text="📊 Statistiques", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT
        ).pack(pady=(20, 10))

        # Tabs : Meilleurs / Pires
        tab_frame = tk.Frame(self.container, bg=BG_DARK)
        tab_frame.pack(fill="x", padx=40)

        self._stats_tab = tk.StringVar(value="worst")

        def make_tab(text, val):
            color = FG_ACCENT if self._stats_tab.get() == val else FG_SECONDARY
            btn = tk.Label(
                tab_frame, text=text, font=FONT_BODY_BOLD,
                bg=BG_DARK, fg=color, cursor="hand2", padx=15, pady=5
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e: self._switch_stats_tab(val))
            return btn

        make_tab("🔻 Moins connus", "worst")
        make_tab("🔺 Plus connus", "best")

        # Liste
        self.stats_list_frame = tk.Frame(self.container, bg=BG_DARK)
        self.stats_list_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self._render_stats_list("worst")

        # Retour
        self.make_button(self.container, "⬅  Retour au menu", self.show_main_menu).pack(pady=(5, 20))

    def _switch_stats_tab(self, tab):
        self._stats_tab.set(tab)
        self.show_stats_view()

    def _render_stats_list(self, mode):
        for w in self.stats_list_frame.winfo_children():
            w.destroy()

        reverse = mode == "best"
        tri = sorted(self.stats.items(), key=lambda x: x[1][0] + x[1][1], reverse=reverse)

        # Canvas with scrollbar
        canvas = tk.Canvas(self.stats_list_frame, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.stats_list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

        # Header
        hdr = tk.Frame(inner, bg=BTN_BG, pady=5)
        hdr.pack(fill="x", pady=(0, 2))
        for text, w in [("#", 4), ("Nombre", 8), ("Mot", 18), ("N→M", 6), ("M→N", 6), ("Temps/lettre", 12)]:
            tk.Label(hdr, text=text, font=FONT_SMALL, bg=BTN_BG, fg=FG_SECONDARY, width=w, anchor="center").pack(side="left")

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

            tk.Label(row, text=str(i + 1), font=FONT_SMALL, bg=row_bg, fg=FG_SECONDARY, width=4, anchor="center").pack(side="left")
            tk.Label(row, text=nombre, font=FONT_BODY_BOLD, bg=row_bg, fg=FG_ACCENT, width=8, anchor="center").pack(side="left")
            tk.Label(row, text=mot, font=FONT_BODY, bg=row_bg, fg=FG_PRIMARY, width=18, anchor="w").pack(side="left")

            nm_color = FG_GREEN if s_nm > 0 else (FG_RED if s_nm < 0 else FG_SECONDARY)
            mn_color = FG_GREEN if s_mn > 0 else (FG_RED if s_mn < 0 else FG_SECONDARY)

            tk.Label(row, text=str(s_nm), font=FONT_BODY, bg=row_bg, fg=nm_color, width=6, anchor="center").pack(side="left")
            tk.Label(row, text=str(s_mn), font=FONT_BODY, bg=row_bg, fg=mn_color, width=6, anchor="center").pack(side="left")

            t_text = f"{t:.2f}s" if t > 0 else "—"
            tk.Label(row, text=t_text, font=FONT_SMALL, bg=row_bg, fg=FG_SECONDARY, width=12, anchor="center").pack(side="left")

    # --------------------------------------------------------
    # Écran : Parcourir la table
    # --------------------------------------------------------
    def show_table_view(self):
        self.clear()

        tk.Label(
            self.container, text="📖 Table de Rappel", font=FONT_TITLE,
            bg=BG_DARK, fg=FG_ACCENT
        ).pack(pady=(20, 10))

        # Search
        search_frame = tk.Frame(self.container, bg=BG_DARK)
        search_frame.pack(fill="x", padx=60, pady=(0, 10))

        tk.Label(search_frame, text="🔍", font=FONT_BODY, bg=BG_DARK, fg=FG_SECONDARY).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_table())
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=FONT_BODY, bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY, relief="flat", width=30
        )
        search_entry.pack(side="left", ipady=4)
        search_entry.focus_set()

        # Table area
        self.table_frame = tk.Frame(self.container, bg=BG_DARK)
        self.table_frame.pack(fill="both", expand=True, padx=40, pady=5)

        self._render_table_cards(self.table)

        self.make_button(self.container, "⬅  Retour au menu", self.show_main_menu).pack(pady=(5, 15))

    def _filter_table(self):
        query = self.search_var.get().strip().lower()
        if query:
            filtered = [(n, m) for n, m in self.table if query in n.lower() or query in m.lower()]
        else:
            filtered = self.table
        self._render_table_cards(filtered)

    def _render_table_cards(self, items):
        for w in self.table_frame.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.table_frame, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

        cols = 5
        for i, (nombre, mot) in enumerate(items):
            r, c = divmod(i, cols)

            # Get score color
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
                bg=BG_CARD, fg=FG_ACCENT
            ).pack()
            tk.Label(
                inner_cell, text=mot, font=FONT_SMALL,
                bg=BG_CARD, fg=FG_PRIMARY
            ).pack()

        for c in range(cols):
            inner.columnconfigure(c, weight=1, minsize=140)


# ============================================================
# Point d'entrée
# ============================================================
if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
