# -*- coding: utf-8 -*-
import csv
import json
import os

from mnemos import config
from mnemos.domain import table as table_domain
from mnemos.paths import stats_path


def default_stats_row():
    return [0, 0, 0.0, 0.0]


def normalize_stats_vals(vals):
    if not isinstance(vals, (list, tuple)) or len(vals) < 3:
        return default_stats_row()
    s_nm = int(vals[0])
    s_mn = int(vals[1])
    t_nm = float(vals[2])
    t_mn = float(vals[3]) if len(vals) >= 4 else 0.0
    return [s_nm, s_mn, t_nm, t_mn]


def stats_key(nombre, mot):
    return f"{nombre}{config.STATS_KEY_SEP}{mot}"


def norm_pair(pair):
    n, m = pair[0], pair[1]
    return (str(n).strip(), str(m).strip())


def pairs_from_json_rows(items):
    if not isinstance(items, list):
        raise ValueError("La clé « table » doit être une liste de paires.")
    out = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            n, m = str(item[0]).strip(), str(item[1]).strip()
            if n and m:
                out.append((n, m))
        elif isinstance(item, dict):
            n = str(
                item.get("nombre")
                or item.get("Nombre")
                or item.get("n")
                or ""
            ).strip()
            m = str(
                item.get("mot")
                or item.get("Mot")
                or item.get("m")
                or ""
            ).strip()
            if n and m:
                out.append((n, m))
    if not out:
        raise ValueError("Aucune paire nombre / mot reconnue.")
    return out


def norm_map_from_stats_json_obj(raw_stats):
    if not isinstance(raw_stats, dict) or not raw_stats:
        return None
    m = {}
    for sk, sv in raw_stats.items():
        if not isinstance(sk, str) or config.STATS_KEY_SEP not in sk:
            continue
        parts = sk.split(config.STATS_KEY_SEP, 1)
        if len(parts) != 2:
            continue
        if not isinstance(sv, (list, tuple)) or len(sv) < 3:
            continue
        m[norm_pair(parts)] = normalize_stats_vals(sv)
    return m or None


def parse_imported_table_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            raise ValueError("Fichier vide.")
        first = [c.strip().lower() for c in rows[0][:2]]
        if first and first[0] in ("nombre", "number", "#", "n"):
            rows = rows[1:]
        out = []
        norm_stats = {}
        for row in rows:
            if len(row) < 2:
                continue
            n, m = row[0].strip(), row[1].strip()
            if not n or not m:
                continue
            out.append((n, m))
            if len(row) >= 6:
                try:
                    s_nm = int(float(row[2].strip()))
                    s_mn = int(float(row[3].strip()))
                    t_nm = float(row[4].strip() or 0)
                    t_mn = float(row[5].strip() or 0)
                    norm_stats[norm_pair((n, m))] = [s_nm, s_mn, t_nm, t_mn]
                except (ValueError, TypeError, IndexError):
                    pass
        if not out:
            raise ValueError("Aucune ligne valide (attendu : Nombre,Mot).")
        return out, (norm_stats if norm_stats else None)

    with open(path, encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    if isinstance(data, dict) and int(data.get("mnemos_export_version", 0)) >= 2:
        rows = data.get("table")
        if not isinstance(rows, list):
            raise ValueError("Export v2 : champ « table » (liste) attendu.")
        table = pairs_from_json_rows(rows)
        st = data.get("stats")
        if st is None:
            norm_map = None
        elif isinstance(st, dict) and len(st) == 0:
            norm_map = {}
        else:
            norm_map = norm_map_from_stats_json_obj(st)
        return table, norm_map

    if isinstance(data, list):
        return pairs_from_json_rows(data), None

    raise ValueError(
        "JSON non reconnu : utilise une liste de paires ou un export Mnemos "
        f"(mnemos_export_version ≥ {config.TABLE_EXPORT_VERSION}).",
    )


def merged_stats_for_imported_table(new_table, norm_stats_map, previous_stats):
    if norm_stats_map is not None:
        out = {}
        for pair in new_table:
            row = norm_stats_map.get(norm_pair(pair))
            out[pair] = list(row) if row is not None else default_stats_row()
        return out
    by_norm = {norm_pair(k): list(v) for k, v in previous_stats.items()}
    out = {}
    for pair in new_table:
        row = by_norm.get(norm_pair(pair))
        out[pair] = list(row) if row is not None else default_stats_row()
    return out


def load_stats(table):
    raw = {}
    path = stats_path()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                for key, vals in data.items():
                    if config.STATS_KEY_SEP in key and isinstance(vals, list) and len(vals) >= 3:
                        n, m = key.split(config.STATS_KEY_SEP, 1)
                        pn = norm_pair((n, m))
                        raw[pn] = normalize_stats_vals(vals)
        except (json.JSONDecodeError, TypeError):
            pass
    stats = {}
    for nombre, mot in table:
        pn = norm_pair((nombre, mot))
        row = raw.get(pn)
        stats[(nombre, mot)] = (
            list(row) if row is not None else default_stats_row()
        )
    return stats


def save_stats(stats, table=None):
    if table is not None:
        valid = {norm_pair(p) for p in table}
        for k in list(stats.keys()):
            if norm_pair(k) not in valid:
                del stats[k]
    path = stats_path()
    data = {
        stats_key(n, m): [int(v[0]), int(v[1]), float(v[2]), float(v[3])]
        for (n, m), v in stats.items()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
        f.flush()
        os.fsync(f.fileno())
