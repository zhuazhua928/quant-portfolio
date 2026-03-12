"""Relative volume versus recent intraday average."""

import pandas as pd


def compute_relative_volume(
    today_df: pd.DataFrame,
    historical_dfs: list[pd.DataFrame],
) -> float | None:
    """Compare today's cumulative volume against the average at the same time-of-day.

    Returns rvol as a ratio (1.0 = average, 2.0 = double).
    """
    if today_df.empty or not historical_dfs:
        return None

    # Current cumulative volume up to latest bar
    today_cum = today_df["volume"].sum()
    if today_cum == 0:
        return None

    # Latest bar time-of-day (in ET for alignment)
    idx_et = today_df.index.tz_convert("America/New_York")
    latest_time = idx_et[-1].time()

    # Compute average cumulative volume up to the same time-of-day across history
    hist_cums = []
    for hdf in historical_dfs:
        if hdf.empty:
            continue
        h_et = hdf.index.tz_convert("America/New_York")
        mask = h_et.time <= latest_time
        if mask.any():
            hist_cums.append(hdf.loc[mask, "volume"].sum())

    if not hist_cums:
        return None

    avg_cum = sum(hist_cums) / len(hist_cums)
    if avg_cum == 0:
        return None
    return float(today_cum / avg_cum)
