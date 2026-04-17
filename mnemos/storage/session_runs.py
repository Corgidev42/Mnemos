# -*- coding: utf-8 -*-
import json
import os

from mnemos import config
from mnemos.paths import full_table_runs_legacy_path, session_runs_path

_VALID_SESSION_KINDS = frozenset(config.SESSION_KIND_LABELS_FR)


def normalize_full_table_run_legacy(obj):
    if not isinstance(obj, dict):
        return None
    try:
        at = str(obj.get("at", "")).strip()
        duration_s = float(obj["duration_s"])
        total_q = int(obj["total_q"])
        score = int(obj["score"])
        errors = int(obj["errors"])
        sens = str(obj.get("sens", ""))
        shuffle = bool(obj.get("shuffle", False))
        flashcard = bool(obj.get("flashcard", False))
    except (KeyError, TypeError, ValueError):
        return None
    if not at or total_q < 0 or score < 0 or errors < 0:
        return None
    return {
        "at": at,
        "duration_s": round(duration_s, 1),
        "total_q": total_q,
        "score": score,
        "errors": errors,
        "sens": sens,
        "shuffle": shuffle,
        "flashcard": flashcard,
    }


def load_full_table_runs_legacy():
    path = full_table_runs_legacy_path()
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return []
    raw = []
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        if int(data.get("mnemos_full_table_runs_version", 0)) >= 1:
            r = data.get("runs")
            if isinstance(r, list):
                raw = r
    out = []
    for item in raw:
        row = normalize_full_table_run_legacy(item)
        if row:
            out.append(row)
    return out[-200:]


def normalize_session_run(obj):
    if not isinstance(obj, dict):
        return None
    kind = str(obj.get("kind", "")).strip()
    if kind not in _VALID_SESSION_KINDS:
        return None
    try:
        at = str(obj.get("at", "")).strip()
        duration_s = float(obj["duration_s"])
        total_q = int(obj["total_q"])
        score = int(obj["score"])
        errors = int(obj["errors"])
        flashcard = bool(obj.get("flashcard", False))
        sens = str(obj.get("sens", ""))
        shuffle = bool(obj.get("shuffle", False))
    except (KeyError, TypeError, ValueError):
        return None
    if not at or total_q < 0 or score < 0 or errors < 0:
        return None
    return {
        "at": at,
        "kind": kind,
        "duration_s": round(duration_s, 1),
        "total_q": total_q,
        "score": score,
        "errors": errors,
        "flashcard": flashcard,
        "sens": sens,
        "shuffle": shuffle,
    }


def load_session_runs():
    path = session_runs_path()
    runs = []
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError):
            data = None
        raw = []
        if isinstance(data, list):
            raw = data
        elif isinstance(data, dict):
            if int(data.get("mnemos_session_runs_version", 0)) >= 1:
                r = data.get("runs")
                if isinstance(r, list):
                    raw = r
        for item in raw:
            row = normalize_session_run(item)
            if row:
                runs.append(row)
    if not runs and os.path.isfile(full_table_runs_legacy_path()):
        for item in load_full_table_runs_legacy():
            base = dict(item)
            base["kind"] = "full_table"
            row = normalize_session_run(base)
            if row:
                runs.append(row)
        if runs:
            save_session_runs(runs)
    return runs[-500:]


def save_session_runs(runs):
    path = session_runs_path()
    clean = []
    for item in runs[-500:]:
        row = normalize_session_run(item)
        if row:
            clean.append(row)
    payload = {
        "mnemos_session_runs_version": config.SESSION_RUNS_VERSION,
        "runs": clean,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)
        f.flush()
        os.fsync(f.fileno())
