# -*- coding: utf-8 -*-
"""Écrans / mixins UI par domaine fonctionnel."""

from mnemos.ui.screens.drawing import DrawingMixin
from mnemos.ui.screens.flashcard import FlashcardMixin
from mnemos.ui.screens.home import HomeMixin
from mnemos.ui.screens.preferences import PreferencesMixin
from mnemos.ui.screens.quiz import QuizMixin
from mnemos.ui.screens.stats import StatsMixin
from mnemos.ui.screens.table_browse import TableBrowseMixin
from mnemos.ui.screens.table_edit import TableEditMixin

__all__ = [
    "DrawingMixin",
    "FlashcardMixin",
    "HomeMixin",
    "PreferencesMixin",
    "QuizMixin",
    "StatsMixin",
    "TableBrowseMixin",
    "TableEditMixin",
]
