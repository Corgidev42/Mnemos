# -*- coding: utf-8 -*-
import json
import os

from mnemos.paths import weak_manual_path


def load_manual_weak_set(table):
    valid = {(n, m) for n, m in table}
    out = set()
    path = weak_manual_path()
    if not os.path.isfile(path):
        return out
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return out
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                n, m = str(item[0]).strip(), str(item[1]).strip()
                if (n, m) in valid:
                    out.add((n, m))
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return out


def save_manual_weak_set(manual_weak, table):
    valid = {(n, m) for n, m in table}
    cleaned = sorted((n, m) for n, m in manual_weak if (n, m) in valid)
    path = weak_manual_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=0)
        f.flush()
        os.fsync(f.fileno())
    return set(cleaned)
