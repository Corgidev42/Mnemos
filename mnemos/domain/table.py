# -*- coding: utf-8 -*-
"""Logique table de rappel (sans I/O)."""


def parse_nombre_int(n):
    try:
        return int(str(n).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def sort_table_pairs(table):
    def key_row(row):
        n = row[0]
        v = parse_nombre_int(n)
        if v is not None:
            return (0, v, str(n))
        return (1, str(n), str(n))

    return sorted(table, key=key_row)


def bloc_count_for_table(table):
    hi = -1
    for n, _ in table:
        v = parse_nombre_int(n)
        if v is not None:
            hi = max(hi, v)
    if hi < 0:
        return 11
    return max(11, (hi // 10) + 1)


def pairs_in_bloc_indices(table, bloc_i):
    start = bloc_i * 10
    end = start + 9
    out = []
    for p in table:
        v = parse_nombre_int(p[0])
        if v is not None and start <= v <= end:
            out.append(p)
    return out


def conseil_full_text():
    from mnemos import config
    return config.CONSEIL_TEXTE_COMPLET
