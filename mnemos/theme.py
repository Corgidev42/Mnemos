# -*- coding: utf-8 -*-
"""Couleurs et polices Tk (dépend uniquement de sys pour la police)."""
import sys

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
