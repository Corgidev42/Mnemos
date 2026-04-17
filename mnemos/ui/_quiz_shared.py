"""Imports et constantes partagés par l’UI (sans QuizApp)."""
# -*- coding: utf-8 -*-
"""Application Tk — fenêtre principale et navigation."""
import csv
import datetime
import json
import os
import queue
import random
import re
import ssl
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from mnemos import config
from mnemos import theme
from mnemos.domain import table as domain_table
from mnemos.paths import (
    app_resource_dir as _app_resource_dir,
    get_app_support_dir as _get_app_support_dir,
    table_path as _table_path,
    weekly_plan_pdf_path as _weekly_plan_pdf_path,
)
from mnemos.storage import (
    VALID_SESSION_KINDS as _VALID_SESSION_KINDS,
    default_stats_row as _default_stats_row,
    load_manual_weak_set,
    load_preferences,
    load_session_runs,
    load_stats,
    load_table,
    load_weekly_plan_days,
    merged_stats_for_imported_table,
    norm_map_from_stats_json_obj as _norm_map_from_stats_json_obj,
    norm_pair as _norm_pair,
    normalize_session_run as _normalize_session_run,
    normalize_stats_vals as _normalize_stats_vals,
    pairs_from_json_rows as _pairs_from_json_rows,
    parse_imported_table_file,
    parse_imported_weekly_plan_file,
    save_manual_weak_set,
    save_preferences,
    save_session_runs,
    save_stats,
    save_weekly_plan_days,
    stats_key as _stats_key,
)
from mnemos.ui import assets
from mnemos.updater import check as updater_check
from mnemos.updater import install as updater_install

VERSION = config.VERSION
APP_NAME = config.APP_NAME
APP_BUNDLE_APP = config.APP_BUNDLE_APP
RELEASE_ASSET_PREFIX = config.RELEASE_ASSET_PREFIX
GITHUB_REPO = config.GITHUB_REPO
TABLE_EMBEDDED = config.TABLE_EMBEDDED
WEEKDAY_LABELS_FR = config.WEEKDAY_LABELS_FR
DEFAULT_WEEKLY_PLAN_DAYS = config.DEFAULT_WEEKLY_PLAN_DAYS
DEFAULT_AUTO_ADVANCE_CORRECT_MS = config.DEFAULT_AUTO_ADVANCE_CORRECT_MS
DEFAULT_AUTO_ADVANCE_WRONG_MS = config.DEFAULT_AUTO_ADVANCE_WRONG_MS
CONSEIL_TEXTE_COMPLET = config.CONSEIL_TEXTE_COMPLET
DEFAULT_PREFERENCES = config.DEFAULT_PREFERENCES
TABLE_EXPORT_VERSION = config.TABLE_EXPORT_VERSION
FULL_BACKUP_VERSION = config.FULL_BACKUP_VERSION
SESSION_KIND_LABELS_FR = config.SESSION_KIND_LABELS_FR
STATS_KEY_SEP = config.STATS_KEY_SEP
SESSION_RUNS_VERSION = config.SESSION_RUNS_VERSION

for _theme_key in (
    "BG_DARK", "BG_CARD", "BG_INPUT", "BG_CARD_HOVER",
    "FG_PRIMARY", "FG_SECONDARY", "FG_ACCENT", "FG_GREEN", "FG_RED",
    "FG_YELLOW", "FG_MAUVE", "FG_ORANGE", "FG_GOLD",
    "BTN_BG", "BTN_HOVER", "BTN_ACCENT", "BTN_ACCENT_FG",
    "TAB_ACTIVE_BG", "TAB_ACTIVE_FG", "CHECK_ON", "CHECK_BG",
    "BORDER_ACCENT", "FONT_TITLE", "FONT_SUBTITLE", "FONT_BODY",
    "FONT_BODY_BOLD", "FONT_SMALL", "FONT_BIG", "FONT_HUGE",
    "FONT_QUESTION", "FONT_INPUT", "FONT_STREAK",
):
    globals()[_theme_key] = getattr(theme, _theme_key)
del _theme_key

_parse_nombre_int = domain_table.parse_nombre_int
_sort_table_pairs = domain_table.sort_table_pairs
_bloc_count_for_table = domain_table.bloc_count_for_table
_pairs_in_bloc_indices = domain_table.pairs_in_bloc_indices


def _conseil_full_text():
    return domain_table.conseil_full_text()


_icon_path = assets.icon_path
_load_logo_photo = assets.load_logo_photo

check_for_update = updater_check.check_for_update
download_and_open_dmg = updater_check.download_and_open_dmg
_auto_update_eligibility = updater_install.auto_update_eligibility
_can_auto_update = updater_install.can_auto_update
_install_update_self = updater_install.install_update_self
_get_app_bundle_path = updater_install.get_app_bundle_path

# « from _quiz_shared import * » n’exporte pas les noms « _ » sans __all__ explicite.
__all__ = [k for k in globals().keys() if not k.startswith("__")]

