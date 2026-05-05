"""Build the hourly + daily ERCOT panel from gridstatus + EIA-930 sources.

Output:
    hourly_panel: ts (UTC hourly), da_price, rt_price, spread, demand_fcst,
                  wind_actual, solar_actual
    daily_panel:  date (US/Central), p0_mean, p1_mean, spread, demand_fcst_mean,
                  wind_mean, solar_mean, weekday, is_weekend, is_holiday

Notes
-----
* `demand_fcst` is EIA-930 DF — a true forecast available before the day starts.
* `wind_actual` and `solar_actual` are EIA-930 realized net generation. The
  paper's exogenous variable is forecasted wind. We use *lagged* (yesterday's)
  realized wind as a persistence-forecast proxy — see features/transform.py.
"""

from __future__ import annotations

import logging
from typing import Iterable

import holidays
import pandas as pd

from ..config import CACHE_DIR, END_DATE, HUB, START_DATE, TZ
from ..sources.ercot_client import fetch_dam_spp_hourly, fetch_rtm_spp_hourly
from ..sources.eia_ba_client import fetch_eia_fuel_generation, fetch_eia_series

logger = logging.getLogger(__name__)


def _years_between(start: str, end: str) -> list[int]:
    s = pd.Timestamp(start).year
    e = pd.Timestamp(end).year
    return list(range(s, e + 1))


def build_hourly_panel(
    start: str = START_DATE,
    end: str = END_DATE,
    hub: str = HUB,
) -> pd.DataFrame:
    """Concatenate yearly DAM + RTM, merge with EIA-930 hourly series."""
    cache_path = CACHE_DIR / f"hourly_panel_{hub}_{start}_{end}.parquet"
    if cache_path.exists():
        logger.info("hourly_panel cache hit: %s", cache_path)
        return pd.read_parquet(cache_path)

    years = _years_between(start, end)
    da_parts = [fetch_dam_spp_hourly(y, hub) for y in years]
    rt_parts = [fetch_rtm_spp_hourly(y, hub) for y in years]
    da = pd.concat(da_parts, axis=0).sort_index()
    rt = pd.concat(rt_parts, axis=0).sort_index()

    # EIA-930 hourly series; pad endpoints so we don't drop boundary hours
    eia_start = f"{start}T00"
    eia_end = f"{(pd.Timestamp(end) + pd.Timedelta(days=1)).date().isoformat()}T00"
    demand_fcst = fetch_eia_series("DF", eia_start, eia_end).rename(
        columns={"value": "demand_fcst"}
    )
    wind = fetch_eia_fuel_generation("WND", eia_start, eia_end).rename(
        columns={"value": "wind_actual"}
    )
    solar = fetch_eia_fuel_generation("SUN", eia_start, eia_end).rename(
        columns={"value": "solar_actual"}
    )

    panel = (
        da.join(rt, how="outer")
        .join(demand_fcst, how="left")
        .join(wind, how="left")
        .join(solar, how="left")
    )
    panel = panel.loc[
        (panel.index >= pd.Timestamp(start, tz="UTC"))
        & (panel.index < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))
    ]
    panel["spread"] = panel["rt_price"] - panel["da_price"]
    panel = panel.sort_index()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(cache_path)
    logger.info("wrote hourly panel: %d rows -> %s", len(panel), cache_path)
    return panel


def build_daily_panel(
    hourly: pd.DataFrame | None = None,
    start: str = START_DATE,
    end: str = END_DATE,
    hub: str = HUB,
) -> pd.DataFrame:
    """Daily aggregation in the local tz: each variable is the simple mean of
    its 24 hourly values. Dummies (Mon, Sat, Sun, Holiday) follow paper Sec 3.
    """
    if hourly is None:
        hourly = build_hourly_panel(start=start, end=end, hub=hub)

    local = hourly.tz_convert(TZ)
    local["date"] = local.index.date
    daily = local.groupby("date").agg(
        p0_mean=("da_price", "mean"),
        p1_mean=("rt_price", "mean"),
        spread=("spread", "mean"),
        demand_fcst_mean=("demand_fcst", "mean"),
        wind_mean=("wind_actual", "mean"),
        solar_mean=("solar_actual", "mean"),
        n_hours=("da_price", "count"),
    )
    daily.index = pd.to_datetime(daily.index)
    daily.index.name = "date"

    daily["weekday"] = daily.index.dayofweek  # 0=Mon
    daily["is_mon"] = (daily["weekday"] == 0).astype(int)
    daily["is_sat"] = (daily["weekday"] == 5).astype(int)
    daily["is_sun"] = (daily["weekday"] == 6).astype(int)

    us = holidays.country_holidays("US", years=range(daily.index.year.min(), daily.index.year.max() + 1))
    daily["is_holiday"] = pd.Series(daily.index.date, index=daily.index).apply(
        lambda d: 1 if d in us else 0
    )
    return daily
