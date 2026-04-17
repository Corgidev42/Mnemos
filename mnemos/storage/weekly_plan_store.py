# -*- coding: utf-8 -*-
import json
import os

from mnemos import config
from mnemos.paths import weekly_plan_user_path


def load_weekly_plan_days():
    path = weekly_plan_user_path()
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) >= 7:
                return [str(data[i]).strip() for i in range(7)]
            if isinstance(data, dict):
                keys = (
                    "lundi", "mardi", "mercredi", "jeudi",
                    "vendredi", "samedi", "dimanche",
                )
                if all(k in data for k in keys):
                    return [str(data[k]).strip() for k in keys]
        except (OSError, json.JSONDecodeError, TypeError, KeyError):
            pass
    return list(config.DEFAULT_WEEKLY_PLAN_DAYS)


def save_weekly_plan_days(days):
    clean = [str(days[i]).strip() if i < len(days) else "" for i in range(7)]
    path = weekly_plan_user_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    return clean


def parse_imported_weekly_plan_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    if isinstance(data, list):
        if len(data) < 7:
            raise ValueError(
                "Le fichier doit contenir au moins 7 entrées (Lundi → Dimanche).",
            )
        return [str(data[i]).strip() for i in range(7)]
    if isinstance(data, dict):
        keys = (
            "lundi", "mardi", "mercredi", "jeudi",
            "vendredi", "samedi", "dimanche",
        )
        if all(k in data for k in keys):
            return [str(data[k]).strip() for k in keys]
    raise ValueError(
        "Format invalide : attendu une liste JSON d’au moins 7 textes, "
        "ou un objet avec les clés lundi … dimanche.",
    )
