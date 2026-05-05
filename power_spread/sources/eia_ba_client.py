"""EIA-930 hourly demand / wind / solar series for the ERCOT BA (ERCO).

EIA series IDs:
    EBA.ERCO-ALL.D.H        hourly demand (MWh)
    EBA.ERCO-ALL.DF.H       hourly demand forecast (MWh)
    EBA.ERCO-ALL.NG.WND.H   hourly net generation, wind (MWh)
    EBA.ERCO-ALL.NG.SUN.H   hourly net generation, solar (MWh)

EIA-930 hourly data starts 2015-07. The DF (demand forecast) series begins
2018-07; before that, only realized demand is available.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from ..config import CACHE_DIR, EIA_API_BASE, EIA_API_KEY, EIA_BA

logger = logging.getLogger(__name__)


class EIAKeyMissing(RuntimeError):
    pass


def _require_key() -> str:
    if not EIA_API_KEY:
        raise EIAKeyMissing("EIA_API_KEY not set in .env")
    return EIA_API_KEY


def _cache_path(series_id: str, start: str, end: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = series_id.replace(".", "_").replace("-", "_")
    return CACHE_DIR / f"eia_{safe}_{start}_{end}.parquet"


def _fetch_eia_paged(series_id: str, start: str, end: str) -> pd.DataFrame:
    """EIA v2 hourly data endpoint, paginated 5000 rows at a time."""
    key = _require_key()
    parent_route, sub_id = series_id.split("/", 1) if "/" in series_id else ("electricity/rto/region-data/data", series_id)
    # For EBA series we use the 'electricity/rto/region-data' frequency=hourly endpoint
    url = f"{EIA_API_BASE}/electricity/rto/region-data/data/"

    rows: list[dict] = []
    offset = 0
    page_size = 5000
    while True:
        params = {
            "api_key": key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": EIA_BA,
            "facets[type][]": series_id,  # e.g., "D" or "DF" or "NG"
            "start": start,
            "end": end,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": page_size,
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json().get("response", {})
        page = payload.get("data") or []
        if not page:
            break
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
        time.sleep(0.2)
    return pd.DataFrame(rows)


def fetch_eia_series(
    series_type: str,
    start: str,
    end: str,
    fueltype: str | None = None,
) -> pd.DataFrame:
    """Fetch one EBA series. series_type in {'D', 'DF', 'NG'}.

    For NG (net generation), pass fueltype in {'WND', 'SUN', 'NG', ...}.
    Returns DataFrame indexed by UTC ts, single 'value' column.
    """
    cache_key = f"{series_type}_{fueltype or 'na'}"
    path = _cache_path(cache_key, start, end)
    if path.exists():
        return pd.read_parquet(path)

    key = _require_key()
    url = f"{EIA_API_BASE}/electricity/rto/region-data/data/"

    rows: list[dict] = []
    offset = 0
    page_size = 5000
    while True:
        params: dict = {
            "api_key": key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": EIA_BA,
            "facets[type][]": series_type,
            "start": start,
            "end": end,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": page_size,
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json().get("response", {})
        page = payload.get("data") or []
        if not page:
            break
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
        time.sleep(0.2)

    if not rows:
        return pd.DataFrame(columns=["value"])

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["period"], utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    out = df.set_index("ts")[["value"]].sort_index()
    out = out[~out.index.duplicated(keep="last")]
    out.to_parquet(path)
    return out


def fetch_eia_fuel_generation(
    fueltype: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    """Fetch hourly net generation for one fueltype (e.g. WND, SUN) at ERCO."""
    cache_key = f"NG_{fueltype}"
    path = _cache_path(cache_key, start, end)
    if path.exists():
        return pd.read_parquet(path)

    key = _require_key()
    url = f"{EIA_API_BASE}/electricity/rto/fuel-type-data/data/"

    rows: list[dict] = []
    offset = 0
    page_size = 5000
    while True:
        params: dict = {
            "api_key": key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": EIA_BA,
            "facets[fueltype][]": fueltype,
            "start": start,
            "end": end,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": page_size,
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json().get("response", {})
        page = payload.get("data") or []
        if not page:
            break
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
        time.sleep(0.2)

    if not rows:
        return pd.DataFrame(columns=["value"])

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["period"], utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    out = df.set_index("ts")[["value"]].sort_index()
    out = out[~out.index.duplicated(keep="last")]
    out.to_parquet(path)
    return out
