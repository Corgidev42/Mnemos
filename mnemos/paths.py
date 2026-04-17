# -*- coding: utf-8 -*-
"""Chemins disque : dépôt (dev), _MEIPASS (frozen), Application Support."""
import os
import sys

from mnemos import config

_MNEMOS_PKG = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_MNEMOS_PKG)


def app_resource_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return REPO_ROOT


def weekly_plan_pdf_path():
    return os.path.join(app_resource_dir(), "Plan_hebdomadaire_Mnemos.pdf")


def get_app_support_dir():
    if getattr(sys, "frozen", False):
        root = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        path = os.path.join(root, config.APP_NAME)
        if not os.path.isdir(path):
            accent = os.path.join(root, "Mnémos")
            if os.path.isdir(accent):
                try:
                    os.rename(accent, path)
                except OSError:
                    try:
                        import shutil
                        shutil.copytree(accent, path)
                    except OSError:
                        pass
            if not os.path.isdir(path):
                for old_name in ("Majeur", "TableDeRappel"):
                    old = os.path.join(root, old_name)
                    if os.path.isdir(old):
                        try:
                            import shutil
                            shutil.copytree(old, path)
                        except OSError:
                            pass
                        break
    else:
        path = os.path.join(REPO_ROOT, ".app_data")
    os.makedirs(path, exist_ok=True)
    return path


def stats_path():
    return os.path.join(get_app_support_dir(), "stats.json")


def table_path():
    return os.path.join(get_app_support_dir(), "table.json")


def prefs_path():
    return os.path.join(get_app_support_dir(), "preferences.json")


def weekly_plan_user_path():
    return os.path.join(get_app_support_dir(), "weekly_plan.json")


def weak_manual_path():
    return os.path.join(get_app_support_dir(), "weak_manual.json")


def full_table_runs_legacy_path():
    return os.path.join(get_app_support_dir(), "full_table_runs.json")


def session_runs_path():
    return os.path.join(get_app_support_dir(), "session_runs.json")
