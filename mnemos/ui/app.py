# -*- coding: utf-8 -*-
"""Application Tk — fenêtre principale (compose les mixins écran)."""
import tkinter as tk

from mnemos.ui._quiz_shared import *  # noqa: F403, F401
from mnemos.ui.widgets import WidgetsMixin
from mnemos.ui.screens.drawing import DrawingMixin
from mnemos.ui.screens.flashcard import FlashcardMixin
from mnemos.ui.screens.home import HomeMixin
from mnemos.ui.screens.preferences import PreferencesMixin
from mnemos.ui.screens.quiz import QuizMixin
from mnemos.ui.screens.stats import StatsMixin
from mnemos.ui.screens.table_browse import TableBrowseMixin
from mnemos.ui.screens.table_edit import TableEditMixin


class QuizApp(
    tk.Tk,
    WidgetsMixin,
    DrawingMixin,
    HomeMixin,
    PreferencesMixin,
    QuizMixin,
    FlashcardMixin,
    StatsMixin,
    TableBrowseMixin,
    TableEditMixin,
):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Quiz v{VERSION}")
        self.configure(bg=BG_DARK)
        self.minsize(1020, 720)
        self.geometry("1160x760")

        # Centrage fenêtre
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 1160) // 2
        y = (sh - 760) // 2
        self.geometry(f"1160x760+{x}+{y}")

        # Données
        self.table = load_table()
        self.stats = load_stats(self.table)
        self.preferences = load_preferences()
        self.manual_weak = load_manual_weak_set(self.table)
        self.session_runs = load_session_runs()
        self.session_flashcard_var = tk.BooleanVar(value=False)
        self._full_table_meta = {}

        # Callbacks réseau / threads → exécution sur le thread Tk uniquement
        self._main_thread_queue = queue.Queue()
        self.after(80, self._pump_main_thread_queue)

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
        self._stats_main_tab = "pairs"  # pairs | sessions
        self._stats_sort_tab = "worst"  # onglets « moins / plus connus » (colonne total)
        self._stats_sort_column = "total"  # total|idx|nombre|mot|s_nm|s_mn|t_nm|t_mn
        self._stats_sort_desc = False  # False = scores croissants (faibles d’abord)

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
            save_stats(self.stats, self.table)
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
    def _add_flashcard_option(self, parent, *, bg=BG_CARD):
        """Case à cocher : session en flashcards au lieu du quiz saisi."""
        tk.Checkbutton(
            parent,
            text="  Mode flashcards (retourner la carte, auto-évaluation)",
            variable=self.session_flashcard_var,
            font=FONT_BODY_BOLD, bg=bg, fg=FG_PRIMARY,
            selectcolor=CHECK_BG, activebackground=bg,
            activeforeground=CHECK_ON, highlightthickness=0,
            anchor="w",
        ).pack(anchor="w", pady=(12, 4))

    def _launch_flashcard_from_questions(self):
        """Démarre une session flashcard à partir de self.questions déjà construite."""
        self.fc_cards = list(self.questions)
        self.fc_idx = 0
        self.fc_revealed = False
        self.fc_score = 0
        self.fc_streak = 0
        self.fc_best_streak = 0
        self.fc_results = []
        self.fc_quiz_start = time.time()
        self._show_flashcard()

    def _record_session_run(
        self, *, total_q, score, errors_count, duration_s, flashcard,
    ):
        """Enregistre une session terminée (temps, score, erreurs, mode)."""
        if total_q <= 0:
            return
        kind = getattr(self, "_session_kind", None) or "bloc"
        if kind not in _VALID_SESSION_KINDS:
            kind = "bloc"
        meta = getattr(self, "_full_table_meta", None) or {}
        run = {
            "at": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "kind": kind,
            "duration_s": round(float(duration_s), 1),
            "total_q": int(total_q),
            "score": int(score),
            "errors": int(errors_count),
            "flashcard": bool(flashcard),
            "sens": str(meta.get("sens", "")),
            "shuffle": bool(meta.get("shuffle", False)),
        }
        row = _normalize_session_run(run)
        if not row:
            return
        self.session_runs.append(row)
        self.session_runs = self.session_runs[-500:]
        save_session_runs(self.session_runs)

    @staticmethod
    def _format_session_run_summary_line(run):
        """Résumé d’une session pour l’accueil ou la liste stats."""
        mois = (
            "janv.", "févr.", "mars", "avr.", "mai", "juin",
            "juil.", "août", "sept.", "oct.", "nov.", "déc.",
        )
        try:
            dt = datetime.datetime.fromisoformat(str(run.get("at", "")))
            date_s = f"{dt.day} {mois[dt.month - 1]} {dt.year}, {dt.hour:02d}:{dt.minute:02d}"
        except (TypeError, ValueError):
            date_s = str(run.get("at", ""))[:19]
        d = float(run.get("duration_s", 0))
        tq = int(run.get("total_q", 0))
        sc = int(run.get("score", 0))
        err = int(run.get("errors", 0))
        fc = bool(run.get("flashcard", False))
        mode_lbl = "flashcards" if fc else "quiz"
        kind_fr = SESSION_KIND_LABELS_FR.get(
            str(run.get("kind", "")), str(run.get("kind", "")),
        )
        return (
            f"{date_s} · {kind_fr} · {mode_lbl} · {d:.0f}s · {sc}/{tq} · {err} err."
        )


def run_app():
    app = QuizApp()
    app.mainloop()
