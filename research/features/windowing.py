"""Aggregate per-bar features into 5-minute non-overlapping windows.

Each window summarizes the prior W minutes (W = config.WINDOW_SIZE_MIN) and is
keyed on the *last* bar of the window. The Stage-1 regime models consume these
windows; the Stage-2 forecaster aligns to the same index so its targets and
features come from the same regime label.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from research import config

# Columns we aggregate by mean (smooth signals).
_MEAN_COLS = ("rv", "pk_vol", "vwap_dev", "amihud", "ofi", "beta_t", "spy_ret_5m")
# Columns we aggregate by sum (returns).
_SUM_COLS = ("ret_1m", "ret_5m", "ret_15m")
# Columns we keep last (dummies, last forward target).
_LAST_COLS = ("open_drive", "close_drive", "midday", "fomc", "cpi", "nfp",
              "minute_of_day")


def make_windows(features: pd.DataFrame, window: int | None = None) -> pd.DataFrame:
    """Resample the feature DataFrame into non-overlapping W-min windows.

    Returns a DataFrame indexed by the window-end timestamp with columns:
      - mean of `_MEAN_COLS`
      - sum  of `_SUM_COLS`  (suffix `_w`)
      - last of `_LAST_COLS`
      - last of fwd_ret_*m   (target columns kept untouched)
    Rows with any NaN in core inputs are dropped.
    """
    if features.empty:
        return features

    W = window or config.WINDOW_SIZE_MIN
    rule = f"{W}min"

    parts: list[pd.DataFrame] = []

    mean_cols = [c for c in _MEAN_COLS if c in features.columns]
    if mean_cols:
        parts.append(features[mean_cols].resample(rule, label="right", closed="right").mean())

    sum_cols = [c for c in _SUM_COLS if c in features.columns]
    if sum_cols:
        s = features[sum_cols].resample(rule, label="right", closed="right").sum()
        s = s.rename(columns={c: f"{c}_w" for c in s.columns})
        parts.append(s)

    last_cols = [c for c in _LAST_COLS if c in features.columns]
    fwd_cols = [c for c in features.columns if c.startswith("fwd_ret_")]
    keep_last = last_cols + fwd_cols
    if keep_last:
        parts.append(features[keep_last].resample(rule, label="right", closed="right").last())

    out = pd.concat(parts, axis=1)
    # restrict to RTH-ish windows only: minute_of_day between 13:30 and 20:00 UTC
    if "minute_of_day" in out.columns:
        mod = out["minute_of_day"]
        out = out.loc[(mod >= 13 * 60 + 30) & (mod <= 20 * 60)]
    # require core regime features non-null
    core = [c for c in ("rv", "pk_vol", "vwap_dev", "ret_5m_w") if c in out.columns]
    if core:
        out = out.dropna(subset=core)
    return out


def stack_panel(symbol_to_windows: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Stack per-symbol windowed frames into a long panel with (symbol, ts) MI."""
    parts = []
    for sym, df in symbol_to_windows.items():
        if df.empty:
            continue
        d = df.copy()
        d["symbol"] = sym
        parts.append(d.reset_index().rename(columns={"timestamp": "ts", df.index.name or "index": "ts"}))
    if not parts:
        return pd.DataFrame()
    panel = pd.concat(parts, ignore_index=True)
    return panel.set_index(["symbol", "ts"]).sort_index()
