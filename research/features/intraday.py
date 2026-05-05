"""Per-bar intraday feature engineering.

Inputs: 1-minute OHLCV DataFrame for a single symbol (UTC index) plus the
SPY DataFrame for cross-sectional features (rolling beta).

Output: a wide DataFrame keyed on the same UTC index containing engineered
features. NaNs at the leading edge of rolling windows are preserved; the
windowing layer drops them.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from research import config

# US regular session in UTC: 13:30 - 20:00 (DST: 14:30 - 21:00). We do not
# attempt to handle DST per-day; instead session features are derived from the
# minute-of-day relative to whatever 'open' the bar series exhibits each day.

_RTH_MINUTES = 390  # standard 6.5 hour session


def _log_returns(close: pd.Series, horizons: tuple[int, ...]) -> pd.DataFrame:
    out = {}
    for h in horizons:
        out[f"ret_{h}m"] = np.log(close).diff(h)
    return pd.DataFrame(out, index=close.index)


def _realized_vol(close: pd.Series, window: int) -> pd.Series:
    r1 = np.log(close).diff()
    return r1.rolling(window).std() * np.sqrt(window)


def _parkinson_vol(high: pd.Series, low: pd.Series, window: int) -> pd.Series:
    # Parkinson (1980) range-based estimator
    hl = np.log(high / low) ** 2
    return np.sqrt(hl.rolling(window).mean() / (4.0 * np.log(2.0)))


def _vwap_deviation(close: pd.Series, vwap: pd.Series | None,
                    high: pd.Series, low: pd.Series, volume: pd.Series) -> pd.Series:
    """Percent deviation of close from a session-cumulative VWAP.

    If the bar feed already supplies a per-minute VWAP, use it; otherwise
    rebuild a session VWAP from typical price * volume.
    """
    if vwap is not None and vwap.notna().any():
        return (close - vwap) / vwap
    typical = (high + low + close) / 3.0
    pv = typical * volume
    # group by UTC date as a proxy for "session"
    session_id = pd.Series(close.index.date, index=close.index)
    cum_pv = pv.groupby(session_id).cumsum()
    cum_v = volume.groupby(session_id).cumsum().replace(0, np.nan)
    sess_vwap = cum_pv / cum_v
    return (close - sess_vwap) / sess_vwap


def _amihud(close: pd.Series, volume: pd.Series, window: int) -> pd.Series:
    r1 = np.log(close).diff().abs()
    dollar_vol = (close * volume).replace(0, np.nan)
    illiq = r1 / dollar_vol
    return illiq.rolling(window).mean()


def _ofi_lee_ready(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Order-flow imbalance proxy: signed minute volume using the tick rule.

    sign = +1 if close_t > close_{t-1}, -1 if <, else carry previous sign.
    Returns a rolling sum of signed volume normalized by total volume.
    """
    diff = np.sign(close.diff()).replace(0, np.nan).ffill().fillna(0)
    signed = diff * volume
    s = signed.rolling(15).sum()
    v = volume.rolling(15).sum().replace(0, np.nan)
    return (s / v).fillna(0)


def _rolling_beta(asset_ret: pd.Series, mkt_ret: pd.Series, window: int) -> pd.Series:
    aligned = pd.concat([asset_ret.rename("a"), mkt_ret.rename("m")], axis=1)
    cov = aligned["a"].rolling(window).cov(aligned["m"])
    var = aligned["m"].rolling(window).var().replace(0, np.nan)
    return cov / var


def _session_dummies(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Coarse session-of-day flags based on UTC minute-of-day.

    Bins (approximate, regardless of DST):
      open_drive  : first 30 minutes after the first observed bar of each day
      midday      : 16:00 - 19:00 UTC
      close_drive : last 30 minutes before the last observed bar of each day
    """
    dates = pd.Series(idx.date, index=idx)
    minute = idx.hour * 60 + idx.minute
    df = pd.DataFrame(index=idx)
    df["minute_of_day"] = minute
    # Use within-session rank to flag open/close
    rank = pd.Series(minute, index=idx).groupby(dates).rank(method="first")
    counts = pd.Series(1, index=idx).groupby(dates).transform("count")
    df["open_drive"] = (rank <= 30).astype(int)
    df["close_drive"] = (rank > (counts - 30)).astype(int)
    df["midday"] = ((minute >= 16 * 60) & (minute < 19 * 60)).astype(int)
    return df


def _macro_dummies(idx: pd.DatetimeIndex) -> pd.DataFrame:
    """FOMC / CPI / NFP same-day dummies.

    FOMC dates are explicit in config.MACRO_EVENTS. CPI is approximated as the
    second Wed of each month; NFP as the first Friday.
    """
    iso = pd.Series(idx.date, index=idx).astype(str)
    fomc = iso.isin(config.MACRO_EVENTS.keys()).astype(int)

    days = pd.Series(idx.date, index=idx)
    dow = pd.Series(idx.dayofweek, index=idx)        # Mon=0 .. Sun=6
    dom = pd.Series(idx.day, index=idx)
    # second Wednesday: Wed (dow=2) and 8 <= day <= 14
    cpi = ((dow == 2) & (dom.between(8, 14))).astype(int)
    # first Friday: Fri (dow=4) and 1 <= day <= 7
    nfp = ((dow == 4) & (dom.between(1, 7))).astype(int)
    return pd.DataFrame({"fomc": fomc, "cpi": cpi, "nfp": nfp}, index=idx)


def build_features(bars: pd.DataFrame, spy_bars: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the full feature matrix for a single symbol.

    Parameters
    ----------
    bars : 1-min OHLCV for the target symbol (UTC index, columns include
           open/high/low/close/volume; vwap optional).
    spy_bars : 1-min OHLCV for SPY, used for rolling intraday beta. Optional;
           if None, beta features are filled with NaN.
    """
    if bars.empty:
        return pd.DataFrame()

    close = bars["close"]
    high = bars["high"]
    low = bars["low"]
    volume = bars["volume"].astype("float64")
    vwap = bars["vwap"] if "vwap" in bars.columns else None

    feats = _log_returns(close, config.RETURN_HORIZONS_MIN)
    feats["rv"] = _realized_vol(close, config.RV_WINDOW_MIN)
    feats["pk_vol"] = _parkinson_vol(high, low, config.RV_WINDOW_MIN)
    feats["vwap_dev"] = _vwap_deviation(close, vwap, high, low, volume)
    feats["amihud"] = _amihud(close, volume, config.AMIHUD_WINDOW_MIN)
    feats["ofi"] = _ofi_lee_ready(close, volume)

    if spy_bars is not None and not spy_bars.empty:
        spy_ret = np.log(spy_bars["close"]).diff()
        # align SPY to the symbol's index (forward-fill missing minutes)
        spy_ret_aligned = spy_ret.reindex(bars.index).ffill()
        asset_ret = np.log(close).diff()
        feats["beta_t"] = _rolling_beta(asset_ret, spy_ret_aligned, config.BETA_WINDOW_MIN)
        feats["spy_ret_5m"] = spy_ret_aligned.rolling(5).sum()
    else:
        feats["beta_t"] = np.nan
        feats["spy_ret_5m"] = np.nan

    sd = _session_dummies(bars.index)
    md = _macro_dummies(bars.index)
    feats = feats.join(sd).join(md)

    # forward-target columns (used by Stage-2 only; stored alongside features)
    for h in config.FORECAST_HORIZONS_MIN:
        feats[f"fwd_ret_{h}m"] = np.log(close).shift(-h) - np.log(close)

    return feats
