import logging
from typing import Any

import numpy as np
import pandas as pd

from .config import (
    BASE_SYMBOL,
    RETURN_WINDOWS,
    ROLLING_CORR_WINDOW,
    ROLLING_VOL_WINDOW,
)
from .utils import get_annualization_factor

logger = logging.getLogger(__name__)


def compute_returns(close: pd.Series) -> dict[str, float | None]:
    returns: dict[str, float | None] = {}
    for label, window in RETURN_WINDOWS.items():
        if len(close) > window:
            returns[label] = float(close.iloc[-1] / close.iloc[-1 - window] - 1)
        else:
            returns[label] = None
    # Day-to-date return
    if len(close) >= 2:
        returns["dtd"] = float(close.iloc[-1] / close.iloc[0] - 1)
    else:
        returns["dtd"] = None
    return returns


def compute_rolling_volatility(close: pd.Series, name: str) -> float | None:
    if len(close) < ROLLING_VOL_WINDOW + 1:
        return None
    log_ret = np.log(close / close.shift(1)).dropna()
    if len(log_ret) < ROLLING_VOL_WINDOW:
        return None
    rolling_vol = log_ret.rolling(ROLLING_VOL_WINDOW).std().iloc[-1]
    if pd.isna(rolling_vol):
        return None
    return float(rolling_vol * get_annualization_factor(name))


def compute_rolling_correlation(
    close: pd.Series, tsla_close: pd.Series | None, name: str
) -> float | None:
    if name == BASE_SYMBOL:
        return 1.0
    if tsla_close is None or close is None:
        return None
    # Align on common timestamps
    log_ret = np.log(close / close.shift(1))
    tsla_log_ret = np.log(tsla_close / tsla_close.shift(1))
    combined = pd.concat(
        {"sym": log_ret, "tsla": tsla_log_ret}, axis=1, join="inner"
    ).dropna()
    if len(combined) < ROLLING_CORR_WINDOW:
        return None
    corr = combined["sym"].rolling(ROLLING_CORR_WINDOW).corr(combined["tsla"]).iloc[-1]
    if pd.isna(corr):
        return None
    return float(corr)


def compute_all_features(
    data: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    tsla_close = data[BASE_SYMBOL]["Close"] if BASE_SYMBOL in data else None
    results = []
    for name, df in data.items():
        close = df["Close"]
        entry: dict[str, Any] = {
            "name": name,
            "last_price": float(close.iloc[-1]),
            "returns": compute_returns(close),
            "rolling_volatility_1h": compute_rolling_volatility(close, name),
            "rolling_correlation_to_TSLA_1h": compute_rolling_correlation(
                close, tsla_close, name
            ),
            "bar_count": len(df),
            "data_as_of": df.index[-1].isoformat(),
        }
        results.append(entry)
    return results
