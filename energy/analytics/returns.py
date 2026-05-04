"""Log returns and rolling realized volatility."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import TRADING_DAYS_PER_YEAR


def log_returns(close: pd.Series) -> pd.Series:
    """Daily log returns of a price series."""
    return np.log(close / close.shift(1))


def rolling_vol(returns: pd.Series, window: int, annualize: bool = True) -> pd.Series:
    """Rolling realized volatility of a returns series.

    Annualized as sqrt(252) * std when `annualize=True`.
    """
    vol = returns.rolling(window=window, min_periods=window).std()
    if annualize:
        vol = vol * np.sqrt(TRADING_DAYS_PER_YEAR)
    return vol
