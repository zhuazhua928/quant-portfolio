"""ERCOT historical price + forecast pulls via gridstatus.

Caching: each year of LMP data is large (~130k DAM rows, ~800k RTM rows).
We cache the HB_NORTH-filtered, hourly-aggregated frames per year as parquet.
Forecasts are short-history (only recent days), so when the historical feed
is unavailable we fall back to actuals as proxies and flag the substitution
in the metadata.

This is appropriate for a methodological replication: ERCOT's STWPF wind
forecast is published with limited history via gridstatus, so for the
historical backtest window we use *realized* wind generation as the
exogenous variable. This is one step removed from the paper (which uses
day-ahead forecasts), but it is the closest publicly-reproducible analog.
The page documents this clearly.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..config import CACHE_DIR, HUB

logger = logging.getLogger(__name__)


def _cache_path(name: str, year: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}_{year}.parquet"


def _to_hourly_index(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Interval Start to UTC hourly index, sort, dedupe."""
    if "Interval Start" not in df.columns:
        raise ValueError(f"missing 'Interval Start' col, got {list(df.columns)}")
    out = df.copy()
    out["ts"] = pd.to_datetime(out["Interval Start"], utc=True).dt.floor("h")
    out = out.drop_duplicates(subset=["ts"]).sort_values("ts").set_index("ts")
    return out


def fetch_dam_spp_hourly(year: int, hub: str = HUB) -> pd.DataFrame:
    """DAM Settlement Point Price for one year, hub-filtered, hourly.

    Returns DataFrame indexed by UTC hourly ts with column 'da_price' ($/MWh).
    Cached to parquet.
    """
    path = _cache_path(f"dam_{hub}", year)
    if path.exists():
        return pd.read_parquet(path)

    from gridstatus import Ercot

    logger.info("fetching ERCOT DAM SPP %d ...", year)
    raw = Ercot().get_dam_spp(year=year)
    sub = raw[raw["Location"] == hub].copy()
    sub = _to_hourly_index(sub)
    out = sub[["SPP"]].rename(columns={"SPP": "da_price"})
    out["da_price"] = pd.to_numeric(out["da_price"], errors="coerce")
    out.to_parquet(path)
    logger.info("  -> %d hourly rows cached at %s", len(out), path)
    return out


def fetch_rtm_spp_hourly(year: int, hub: str = HUB) -> pd.DataFrame:
    """RTM SPP for one year, hub-filtered, aggregated 15-min -> hourly mean.

    Returns DataFrame indexed by UTC hourly ts with column 'rt_price' ($/MWh).
    Cached to parquet.
    """
    path = _cache_path(f"rtm_{hub}", year)
    if path.exists():
        return pd.read_parquet(path)

    from gridstatus import Ercot

    logger.info("fetching ERCOT RTM SPP %d (15-min) ...", year)
    raw = Ercot().get_rtm_spp(year=year)
    sub = raw[raw["Location"] == hub].copy()
    sub["ts_utc"] = pd.to_datetime(sub["Interval Start"], utc=True)
    sub["hour"] = sub["ts_utc"].dt.floor("h")
    hourly = (
        sub.groupby("hour")["SPP"]
        .mean()
        .rename("rt_price")
        .to_frame()
        .sort_index()
    )
    hourly.index.name = "ts"
    hourly.to_parquet(path)
    logger.info("  -> %d hourly rows cached at %s", len(hourly), path)
    return hourly


def fetch_actual_load_hourly(year: int) -> pd.DataFrame:
    """ERCOT system-wide actual load by year, hourly. Used as the demand proxy.

    Falls back to per-year retrieval; if the historical endpoint is
    unavailable returns an empty frame and the pipeline imputes from EIA-930.
    """
    path = _cache_path("load", year)
    if path.exists():
        return pd.read_parquet(path)

    from gridstatus import Ercot

    try:
        logger.info("fetching ERCOT system-wide load %d ...", year)
        start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        end = pd.Timestamp(f"{year + 1}-01-01", tz="UTC")
        raw = Ercot().get_load(date=start, end=end)
        if raw is None or raw.empty:
            return pd.DataFrame(columns=["load"])
        col = "Load" if "Load" in raw.columns else raw.columns[-1]
        raw["ts"] = pd.to_datetime(raw["Interval Start"], utc=True).dt.floor("h")
        out = raw.groupby("ts")[col].mean().rename("load").to_frame().sort_index()
        out.to_parquet(path)
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("ERCOT load fetch %d failed: %s — will rely on EIA-930", year, exc)
        return pd.DataFrame(columns=["load"])
