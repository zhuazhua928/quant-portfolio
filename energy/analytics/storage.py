"""Storage envelope, z-score, and YoY analytics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _add_keys(weekly: pd.DataFrame) -> pd.DataFrame:
    """Add `year`, `week_of_year` columns. Idempotent."""
    df = weekly.copy()
    if "year" not in df.columns:
        df["year"] = df["date"].dt.year
    if "week_of_year" not in df.columns:
        df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    return df


def five_year_envelope(weekly: pd.DataFrame, asof: pd.Timestamp | None = None) -> pd.DataFrame:
    """Same-week-of-year (min, p25, mean, p75, max) over the prior 5 calendar years.

    Excludes the current year (relative to `asof`) so the envelope is a true
    historical baseline.
    """
    if weekly.empty:
        return pd.DataFrame(
            columns=["week_of_year", "min", "p25", "mean", "std", "p75", "max"]
        )
    df = _add_keys(weekly)
    if asof is None:
        asof = df["date"].max()
    cutoff_year = int(pd.Timestamp(asof).year)
    hist = df[(df["year"] >= cutoff_year - 5) & (df["year"] < cutoff_year)]
    if hist.empty:
        return pd.DataFrame(
            columns=["week_of_year", "min", "p25", "mean", "std", "p75", "max"]
        )
    grouped = hist.groupby("week_of_year")["value"]
    env = grouped.agg(
        min="min",
        p25=lambda s: float(np.percentile(s, 25)),
        mean="mean",
        std="std",
        p75=lambda s: float(np.percentile(s, 75)),
        max="max",
    ).reset_index()
    return env


def storage_zscore(latest_value: float, latest_week: int, envelope: pd.DataFrame) -> float | None:
    """(current - 5yr_mean_for_same_week) / 5yr_std_for_same_week."""
    row = envelope.loc[envelope["week_of_year"] == latest_week]
    if row.empty:
        return None
    mean = float(row["mean"].iloc[0])
    std = float(row["std"].iloc[0])
    if std == 0 or pd.isna(std):
        return None
    return float((latest_value - mean) / std)


def yoy_delta(weekly: pd.DataFrame) -> dict | None:
    """Latest level minus same-week-of-year level one year prior."""
    if weekly.empty:
        return None
    df = _add_keys(weekly).sort_values("date")
    latest = df.iloc[-1]
    prior = df[
        (df["year"] == int(latest["year"]) - 1)
        & (df["week_of_year"] == int(latest["week_of_year"]))
    ]
    if prior.empty:
        return None
    prev = float(prior["value"].iloc[-1])
    cur = float(latest["value"])
    return {
        "latest": cur,
        "year_ago": prev,
        "delta": round(cur - prev, 1),
        "pct": round((cur - prev) / prev * 100, 2) if prev else None,
    }


def weekly_change(weekly: pd.DataFrame) -> dict | None:
    """Most recent weekly build (positive) or draw (negative)."""
    if len(weekly) < 2:
        return None
    df = weekly.sort_values("date").reset_index(drop=True)
    cur = float(df["value"].iloc[-1])
    prev = float(df["value"].iloc[-2])
    delta = cur - prev
    return {
        "delta": round(delta, 1),
        "label": "build" if delta > 0 else "draw",
    }
