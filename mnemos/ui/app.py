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


def run_app():
    app = QuizApp()
    app.mainloop()
