# -*- coding: utf-8 -*-
import json
import os

from mnemos import config
from mnemos.paths import prefs_path


def load_preferences():
    prefs = dict(config.DEFAULT_PREFERENCES)
    path = prefs_path()
    if not os.path.isfile(path):
        return prefs
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return prefs
        for key in config.DEFAULT_PREFERENCES:
            if key not in data:
                continue
            try:
                v = int(data[key])
            except (TypeError, ValueError):
                continue
            prefs[key] = max(0, min(120_000, v))
    except (OSError, json.JSONDecodeError):
        pass
    return prefs


def save_preferences(prefs):
    out = {
        k: int(prefs.get(k, config.DEFAULT_PREFERENCES[k]))
        for k in config.DEFAULT_PREFERENCES
    }
    for k in out:
        out[k] = max(0, min(120_000, out[k]))
    path = prefs_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    return out
