"""Calendar spreads, contango/backwardation, key seasonal aggregates.

Conventions
-----------
- A *forward curve* is a list of dicts with at least `year`, `month`, `close`
  fields (as produced by `energy.sources.futures.fetch_forward_curve`).
- A *spread* is signed `near - far`; a positive widow-maker (March - April)
  means the market prices winter scarcity above shoulder-season storage.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

WINTER_MONTHS = (11, 12, 1, 2, 3)   # Nov-Mar
SUMMER_MONTHS = (4, 5, 6, 7, 8, 9, 10)  # Apr-Oct (the rest)


def _curve_index(curve: list[dict]) -> dict[tuple[int, int], float]:
    """Map (year, month) -> close for fast lookup."""
    return {(c["year"], c["month"]): float(c["close"]) for c in curve}


def calendar_spread(curve: list[dict], near: tuple[int, int], far: tuple[int, int]) -> float | None:
    """Signed spread `near - far` for two specific (year, month) contracts."""
    idx = _curve_index(curve)
    if near not in idx or far not in idx:
        return None
    return round(idx[near] - idx[far], 4)


def contango_score(curve: list[dict]) -> dict:
    """First-vs-second-month spread.

    Returns `{m1, m2, spread, label}` where label is 'contango' (M2>M1),
    'backwardation' (M2<M1), or 'flat'.
    """
    if len(curve) < 2:
        return {"m1": None, "m2": None, "spread": None, "label": "n/a"}
    m1 = float(curve[0]["close"])
    m2 = float(curve[1]["close"])
    spread = m2 - m1
    if spread > 0.005:
        label = "contango"
    elif spread < -0.005:
        label = "backwardation"
    else:
        label = "flat"
    return {
        "m1": round(m1, 4),
        "m2": round(m2, 4),
        "spread": round(spread, 4),
        "label": label,
    }


def widow_maker(curve: list[dict]) -> dict | None:
    """The March-April spread (`H - J`) for the *next* delivery cycle on the curve.

    This is the canonical natural-gas seasonality trade: winter scarcity
    (March) vs. shoulder-season abundance (April).
    """
    idx = _curve_index(curve)
    march_apr = None
    for (y, m), _ in idx.items():
        if m == 3 and (y, 4) in idx:
            march_apr = (y, idx[(y, 3)] - idx[(y, 4)])
            break
    if march_apr is None:
        return None
    y, spread = march_apr
    return {"year": y, "spread": round(spread, 4)}


def winter_strip(curve: list[dict]) -> dict | None:
    """Average of the next Nov-Mar (5-month) winter strip."""
    rows = [c for c in curve if c["month"] in WINTER_MONTHS]
    if len(rows) < 5:
        return None
    rows = sorted(rows, key=lambda c: (c["year"], c["month"]))[:5]
    avg = sum(float(c["close"]) for c in rows) / 5
    return {
        "contracts": [c["expiry_label"] for c in rows],
        "average": round(avg, 4),
    }


def summer_winter_diff(curve: list[dict]) -> dict | None:
    """Average winter strip minus average of the *immediately preceding* summer
    strip (Apr-Oct, 7 months) on the curve, when both windows are available.
    """
    summers = sorted(
        [c for c in curve if c["month"] in SUMMER_MONTHS],
        key=lambda c: (c["year"], c["month"]),
    )
    winters = sorted(
        [c for c in curve if c["month"] in WINTER_MONTHS],
        key=lambda c: (c["year"], c["month"]),
    )
    if len(summers) < 7 or len(winters) < 5:
        return None
    summer_avg = sum(float(c["close"]) for c in summers[:7]) / 7
    winter_avg = sum(float(c["close"]) for c in winters[:5]) / 5
    return {
        "summer_avg": round(summer_avg, 4),
        "winter_avg": round(winter_avg, 4),
        "diff": round(winter_avg - summer_avg, 4),
    }


def front_month_history_spread(
    front_close: pd.Series,
    second_close: pd.Series,
) -> pd.Series:
    """Historical M2 - M1 spread series (positive = contango).

    Both series should be aligned on date index.
    """
    df = pd.concat({"m1": front_close, "m2": second_close}, axis=1).dropna()
    return df["m2"] - df["m1"]
