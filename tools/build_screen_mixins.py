#!/usr/bin/env python3
"""Découpe mnemos/ui/app.py monolithique en _quiz_shared, widgets, mixins et app minimal."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mnemos" / "ui" / "app.py"
SCREENS = ROOT / "mnemos" / "ui" / "screens"


def main():
    lines = APP.read_text(encoding="utf-8").splitlines(keepends=True)
    # Ligne 1-based L -> indice L - 1
    shared = "".join(lines[0:104])  # avant « class QuizApp »

    (ROOT / "mnemos" / "ui" / "_quiz_shared.py").write_text(
        '"""Imports et constantes partagés par l’UI (sans QuizApp)."""\n' + shared,
        encoding="utf-8",
    )

    widgets_body = "".join(lines[180:519])
    (ROOT / "mnemos" / "ui" / "widgets.py").write_text(
        '"""Widgets Tk réutilisables (mixins QuizApp)."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class WidgetsMixin:\n" + widgets_body,
        encoding="utf-8",
    )

    home_body = "".join(lines[287:670]) + "".join(lines[774:1097])
    (SCREENS / "home.py").write_text(
        '"""Accueil, sauvegarde complète, plan PDF, à propos, file MAJ."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class HomeMixin:\n" + home_body,
        encoding="utf-8",
    )

    prefs_body = "".join(lines[670:744])
    (SCREENS / "preferences.py").write_text(
        '"""Écran préférences."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class PreferencesMixin:\n" + prefs_body,
        encoding="utf-8",
    )

    drawing_body = "".join(lines[744:774])
    (SCREENS / "drawing.py").write_text(
        '"""Dessin canvas (barre de maîtrise, etc.)."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class DrawingMixin:\n" + drawing_body,
        encoding="utf-8",
    )

    quiz_body = "".join(lines[1100:1957])
    (SCREENS / "quiz.py").write_text(
        '"""Modes quiz : blocs, focus, aléatoire, toute la table, questions."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class QuizMixin:\n" + quiz_body,
        encoding="utf-8",
    )

    flash_body = "".join(lines[1960:2202])
    (SCREENS / "flashcard.py").write_text(
        '"""Session flashcards."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class FlashcardMixin:\n" + flash_body,
        encoding="utf-8",
    )

    stats_body = "".join(lines[2205:2619])
    (SCREENS / "stats.py").write_text(
        '"""Statistiques et historique de sessions."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class StatsMixin:\n" + stats_body,
        encoding="utf-8",
    )

    browse_body = "".join(lines[2622:2766])
    (SCREENS / "table_browse.py").write_text(
        '"""Parcours de la table."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class TableBrowseMixin:\n" + browse_body,
        encoding="utf-8",
    )

    edit_body = "".join(lines[2768:3160])
    (SCREENS / "table_edit.py").write_text(
        '"""Édition table, import/export table, plan hebdo fichier."""\n'
        "from mnemos.ui._quiz_shared import *  # noqa: F403, F401\n\n\n"
        "class TableEditMixin:\n" + edit_body,
        encoding="utf-8",
    )

    core = (
        "".join(lines[105:160])
        + "".join(lines[161:179])
        + "".join(lines[210:286])
    )

    new_app = '''# -*- coding: utf-8 -*-
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
''' + core + '''

def run_app():
    app = QuizApp()
    app.mainloop()
'''
    APP.write_text(new_app, encoding="utf-8")
    print("Wrote mixins + slim app.py")


if __name__ == "__main__":
    SCREENS.mkdir(parents=True, exist_ok=True)
    main()
