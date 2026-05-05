"""Helpers for selecting OOS test windows over the daily panel."""

from __future__ import annotations

import pandas as pd


def oos_dates(daily: pd.DataFrame, oos_start: str) -> pd.DatetimeIndex:
    idx = daily.index
    return idx[idx >= pd.Timestamp(oos_start)]
