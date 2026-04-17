# -*- coding: utf-8 -*-
"""Persistance (fichiers JSON / CSV) — réexport pour imports courts."""

from mnemos.storage.preferences_store import load_preferences, save_preferences
from mnemos import config
from mnemos.storage.session_runs import (
    load_session_runs,
    normalize_session_run,
    save_session_runs,
)
from mnemos.storage.stats_store import (
    default_stats_row,
    load_stats,
    merged_stats_for_imported_table,
    norm_map_from_stats_json_obj,
    norm_pair,
    normalize_stats_vals,
    pairs_from_json_rows,
    parse_imported_table_file,
    save_stats,
    stats_key,
)
from mnemos.storage.table_io import load_table
from mnemos.storage.weak_manual_store import load_manual_weak_set, save_manual_weak_set
from mnemos.storage.weekly_plan_store import (
    load_weekly_plan_days,
    parse_imported_weekly_plan_file,
    save_weekly_plan_days,
)

VALID_SESSION_KINDS = frozenset(config.SESSION_KIND_LABELS_FR)

__all__ = [
    "VALID_SESSION_KINDS",
    "default_stats_row",
    "load_manual_weak_set",
    "load_preferences",
    "load_session_runs",
    "load_stats",
    "load_table",
    "load_weekly_plan_days",
    "merged_stats_for_imported_table",
    "norm_map_from_stats_json_obj",
    "norm_pair",
    "normalize_session_run",
    "normalize_stats_vals",
    "pairs_from_json_rows",
    "parse_imported_table_file",
    "parse_imported_weekly_plan_file",
    "save_manual_weak_set",
    "save_preferences",
    "save_session_runs",
    "save_stats",
    "save_weekly_plan_days",
    "stats_key",
]
