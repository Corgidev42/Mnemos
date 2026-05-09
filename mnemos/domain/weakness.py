# -*- coding: utf-8 -*-
"""Priorité « point faible » : score d’apprentissage + lenteur relative aux autres paires."""

import math

# Niveaux pour l’UI (bordures, légende) — 0 = pas de signal fort
WEAKNESS_NONE = 0
WEAKNESS_LIGHT = 1
WEAKNESS_MODERATE = 2
WEAKNESS_CRITICAL = 3


def _median_positive(values):
    xs = sorted(v for v in values if v is not None and v > 0)
    if not xs:
        return 0.0
    n = len(xs)
    mid = n // 2
    if n % 2:
        return float(xs[mid])
    return (xs[mid - 1] + xs[mid]) / 2.0


def timing_baselines(stats):
    """Médianes des temps « par lettre / par caractère » sur les paires ayant des réponses justes."""
    nm_times = [row[2] for row in stats.values() if row[0] > 0 and row[2] > 0]
    mn_times = [row[3] for row in stats.values() if row[1] > 0 and row[3] > 0]
    return _median_positive(nm_times), _median_positive(mn_times)


def _slowness_ratio(t_pair, s_dir, median):
    if median <= 0 or s_dir <= 0 or t_pair <= 0:
        return None
    return t_pair / median


def focus_priority_score(row, med_nm, med_mn, is_manual):
    """
    Score élevé = à réviser en priorité (focus après les points faibles manuels).
    Combine erreurs / faible score cumulé et écart de temps par rapport aux médianes globales.
    """
    s_nm, s_mn, t_nm, t_mn = row
    tot = s_nm + s_mn
    pri = 0.0
    if is_manual:
        pri += 1000.0
    if tot < 0:
        pri += 500.0 + float(-tot) * 50.0
    elif tot == 0:
        pri += 85.0
    elif tot < 4:
        pri += float(4 - tot) * 42.0

    def slow_penalty(s_dir, t_dir, med):
        if med <= 0 or s_dir <= 0 or t_dir <= 0:
            return 0.0
        r = t_dir / med
        if r <= 1.0:
            return 0.0
        return math.pow(r - 1.0, 1.15)

    pri += slow_penalty(s_nm, t_nm, med_nm) * 48.0
    pri += slow_penalty(s_mn, t_mn, med_mn) * 48.0
    return pri


def weakness_level(row, med_nm, med_mn, is_manual):
    """
    Niveau affichable : critique (erreurs ou 🎯), modéré, léger, ou RAS sur ce critère.
    Les erreurs (score total < 0) sont toujours critiques — même si le temps n’est pas enregistré.
    """
    s_nm, s_mn, t_nm, t_mn = row
    tot = s_nm + s_mn
    if is_manual or tot < 0:
        return WEAKNESS_CRITICAL

    r_nm = _slowness_ratio(t_nm, s_nm, med_nm)
    r_mn = _slowness_ratio(t_mn, s_mn, med_mn)
    ratios = [x for x in (r_nm, r_mn) if x is not None]
    r_max = max(ratios) if ratios else None

    if tot >= 4:
        if r_max is not None and r_max >= 2.2:
            return WEAKNESS_LIGHT
        return WEAKNESS_NONE

    if tot == 0:
        return WEAKNESS_MODERATE if (r_max is not None and r_max >= 1.6) else WEAKNESS_LIGHT

    if r_max is not None and r_max >= 2.0:
        return WEAKNESS_MODERATE
    if tot <= 1:
        return WEAKNESS_LIGHT
    if r_max is not None and r_max >= 1.35:
        return WEAKNESS_LIGHT
    return WEAKNESS_NONE
