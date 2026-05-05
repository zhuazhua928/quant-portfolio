"""Compose source pulls + analytics into the four dashboard JSON artifacts."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..analytics import returns as ret
from ..analytics import spreads as sp
from ..analytics import storage as st
from ..config import (
    DATA_DIR,
    EIA_API_KEY,
    PRICE_HISTORY_YEARS,
    STORAGE_HISTORY_YEARS,
    VOL_WINDOWS,
)
from ..sources.eia import EIAKeyMissing, fetch_spot, fetch_storage
from ..sources.futures import fetch_forward_curve, fetch_front_month

logger = logging.getLogger(__name__)


def _clean_for_json(obj: Any) -> Any:
    """Recursively convert numpy/pandas types to native Python; NaN -> None."""
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_for_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else round(float(obj), 6)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float) and (obj != obj):
        return None
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = _clean_for_json(payload)
    path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("wrote %s (%d bytes)", path, path.stat().st_size)


# ---------------------------------------------------------------------------
# prices.json
# ---------------------------------------------------------------------------

def build_prices(front_month: pd.DataFrame) -> list[dict]:
    if front_month.empty:
        return []
    df = front_month[["close"]].copy()
    df["log_ret"] = ret.log_returns(df["close"])
    for w in VOL_WINDOWS:
        df[f"vol_{w}d"] = ret.rolling_vol(df["log_ret"], w)
    rows: list[dict] = []
    for ts, r in df.iterrows():
        rows.append(
            {
                "date": pd.Timestamp(ts).date().isoformat(),
                "close": round(float(r["close"]), 4),
                "log_ret": None if pd.isna(r["log_ret"]) else round(float(r["log_ret"]), 6),
                **{
                    f"vol_{w}d": None if pd.isna(r[f"vol_{w}d"]) else round(float(r[f"vol_{w}d"]), 6)
                    for w in VOL_WINDOWS
                },
            }
        )
    return rows


# ---------------------------------------------------------------------------
# curve.json
# ---------------------------------------------------------------------------

def build_curve(curve: list[dict]) -> dict:
    contango = sp.contango_score(curve)
    return {
        "asof": date.today().isoformat(),
        "contracts": curve,
        "contango": contango,
        "widow_maker": sp.widow_maker(curve),
        "winter_strip": sp.winter_strip(curve),
        "summer_winter": sp.summer_winter_diff(curve),
    }


# ---------------------------------------------------------------------------
# storage.json
# ---------------------------------------------------------------------------

def build_storage(weekly: pd.DataFrame) -> dict:
    if weekly.empty:
        return {
            "available": False,
            "weekly": [],
            "envelope": [],
            "latest": None,
            "weekly_change": None,
            "yoy": None,
            "zscore": None,
            "asof": None,
        }
    df = weekly.copy()
    df = df.sort_values("date").reset_index(drop=True)
    df["year"] = df["date"].dt.year
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)

    envelope = st.five_year_envelope(df)
    latest_row = df.iloc[-1]
    latest_value = float(latest_row["value"])
    latest_week = int(latest_row["week_of_year"])
    z = st.storage_zscore(latest_value, latest_week, envelope)
    yoy = st.yoy_delta(df)
    weekly_change = st.weekly_change(df)

    weekly_rows = [
        {
            "date": pd.Timestamp(r["date"]).date().isoformat(),
            "value": round(float(r["value"]), 1),
            "year": int(r["year"]),
            "week_of_year": int(r["week_of_year"]),
        }
        for _, r in df.tail(int(STORAGE_HISTORY_YEARS * 53)).iterrows()
    ]
    envelope_rows = [
        {
            "week_of_year": int(r["week_of_year"]),
            "min": round(float(r["min"]), 1),
            "p25": round(float(r["p25"]), 1),
            "mean": round(float(r["mean"]), 1),
            "p75": round(float(r["p75"]), 1),
            "max": round(float(r["max"]), 1),
        }
        for _, r in envelope.iterrows()
    ]
    return {
        "available": True,
        "asof": pd.Timestamp(latest_row["date"]).date().isoformat(),
        "weekly": weekly_rows,
        "envelope": envelope_rows,
        "latest": round(latest_value, 1),
        "weekly_change": weekly_change,
        "yoy": yoy,
        "zscore": None if z is None else round(z, 3),
    }


# ---------------------------------------------------------------------------
# summary.json
# ---------------------------------------------------------------------------

def build_summary(
    front_month: pd.DataFrame,
    curve_payload: dict,
    storage_payload: dict,
    spot_df: pd.DataFrame,
) -> dict:
    if front_month.empty:
        return {
            "asof": date.today().isoformat(),
            "front_month": None,
            "spot": None,
            "curve": curve_payload,
            "storage": storage_payload,
        }
    closes = front_month["close"]
    last_date = front_month.index[-1]
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else None
    week_ago = float(closes.iloc[-6]) if len(closes) >= 6 else None
    rets = ret.log_returns(closes)
    vol_30d_series = ret.rolling_vol(rets, 30)
    vol_30d = float(vol_30d_series.dropna().iloc[-1]) if not vol_30d_series.dropna().empty else None

    front_payload = {
        "ticker": "NG=F",
        "close": round(last, 4),
        "asof": pd.Timestamp(last_date).date().isoformat(),
        "change_d": None if prev is None else round(last - prev, 4),
        "change_d_pct": None if prev is None else round((last / prev - 1) * 100, 3),
        "change_w_pct": None if week_ago is None else round((last / week_ago - 1) * 100, 3),
        "vol_30d_annualized": None if vol_30d is None else round(vol_30d, 4),
    }

    spot_payload = None
    if not spot_df.empty:
        last_spot = spot_df.iloc[-1]
        spot_payload = {
            "value": round(float(last_spot["value"]), 4),
            "asof": pd.Timestamp(last_spot["date"]).date().isoformat(),
        }

    return {
        "asof": date.today().isoformat(),
        "front_month": front_payload,
        "spot": spot_payload,
        "curve": {
            "asof": curve_payload.get("asof"),
            "contango": curve_payload.get("contango"),
            "widow_maker": curve_payload.get("widow_maker"),
            "winter_strip": curve_payload.get("winter_strip"),
            "summer_winter": curve_payload.get("summer_winter"),
        },
        "storage": {
            "available": storage_payload.get("available"),
            "asof": storage_payload.get("asof"),
            "latest": storage_payload.get("latest"),
            "weekly_change": storage_payload.get("weekly_change"),
            "yoy": storage_payload.get("yoy"),
            "zscore": storage_payload.get("zscore"),
        },
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def export_all(output_dir: Path | None = None) -> dict[str, Path]:
    """Pull data, compute analytics, write 4 JSONs. Returns paths written."""
    out_dir = output_dir or DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("fetching front-month NG=F (%d years) ...", PRICE_HISTORY_YEARS)
    front = fetch_front_month()

    logger.info("fetching forward curve ...")
    curve = fetch_forward_curve()

    if EIA_API_KEY:
        try:
            logger.info("fetching EIA spot ...")
            spot_df = fetch_spot()
        except Exception as exc:  # noqa: BLE001
            logger.warning("EIA spot fetch failed: %s", exc)
            spot_df = pd.DataFrame(columns=["date", "value"])
        try:
            logger.info("fetching EIA storage ...")
            storage_df = fetch_storage()
        except Exception as exc:  # noqa: BLE001
            logger.warning("EIA storage fetch failed: %s", exc)
            storage_df = pd.DataFrame(columns=["date", "value"])
    else:
        logger.warning("EIA_API_KEY missing — spot and storage panels will be empty")
        spot_df = pd.DataFrame(columns=["date", "value"])
        storage_df = pd.DataFrame(columns=["date", "value"])

    prices_payload = build_prices(front)
    curve_payload = build_curve(curve)
    storage_payload = build_storage(storage_df)
    summary_payload = build_summary(front, curve_payload, storage_payload, spot_df)

    paths = {
        "summary": out_dir / "summary.json",
        "prices": out_dir / "prices.json",
        "curve": out_dir / "curve.json",
        "storage": out_dir / "storage.json",
    }
    _write_json(paths["summary"], summary_payload)
    _write_json(paths["prices"], prices_payload)
    _write_json(paths["curve"], curve_payload)
    _write_json(paths["storage"], storage_payload)
    return paths
