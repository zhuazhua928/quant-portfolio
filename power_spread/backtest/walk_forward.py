"""Walk-forward backtest engine.

For each (model_type, calibration_window T, X_subset) and each OOS day t:
  1. Fit on rows in [t - T, t - 1] of the daily panel (lookback = T calendar days).
  2. Predict for day t.
  3. Apply the decision rule and accumulate per-day P&L.

Outputs a long-format DataFrame:
    config_id, date, y_hat, spread, pnl, prob (probit only), pred_spread (ARX),
    p, q0, q1 are computed downstream from this frame.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np
import pandas as pd

from ..features.transform import DETERMINISTIC, build_design
from ..models.arx import fit_predict_arx_levels, fit_predict_arx_spread
from ..models.probit import fit_predict_probit

logger = logging.getLogger(__name__)


ModelType = Literal["arx_levels", "arx_spread", "probit"]


@dataclass(frozen=True)
class BacktestConfig:
    model: ModelType
    window: int  # T calibration window in days
    x_cols: tuple[str, ...]  # subset of {'demand_fcst_mean', 'wind_mean', 'solar_mean'}
    lag_set: tuple[int, ...] = (2, 7)

    @property
    def id(self) -> str:
        x_label = "_".join(c.replace("_mean", "").replace("_fcst", "fcst") for c in self.x_cols) or "none"
        return f"{self.model}__T{self.window}__X-{x_label}"


def run_one_config(
    daily: pd.DataFrame,
    cfg: BacktestConfig,
    oos_start: str,
) -> pd.DataFrame:
    """Run a walk-forward backtest for one config. Returns daily forecasts."""
    df = build_design(daily, x_cols=cfg.x_cols, lag_set=cfg.lag_set)
    x_cols = list(df.attrs["x_cols"])
    lag_cols = list(df.attrs["lag_cols"])

    oos_dates = df.index[df.index >= pd.Timestamp(oos_start)]
    if len(oos_dates) == 0:
        return pd.DataFrame()

    rows: list[dict] = []
    for d in oos_dates:
        # Train on the trailing T calendar days strictly before d
        train_end_excl = d
        train_start = d - pd.Timedelta(days=cfg.window)
        train = df.loc[(df.index >= train_start) & (df.index < train_end_excl)]
        if len(train) < cfg.window // 2:
            # not enough history yet
            rows.append({
                "date": d,
                "spread": float(df.at[d, "spread"]) if d in df.index else np.nan,
                "pred": np.nan,
                "prob": np.nan,
            })
            continue

        test_row = df.loc[d]
        if cfg.model == "arx_levels":
            pred = fit_predict_arx_levels(train, test_row, DETERMINISTIC, x_cols, lag_cols)
            prob = np.nan
        elif cfg.model == "arx_spread":
            pred = fit_predict_arx_spread(train, test_row, DETERMINISTIC, x_cols, lag_cols)
            prob = np.nan
        elif cfg.model == "probit":
            prob = fit_predict_probit(train, test_row, DETERMINISTIC, x_cols, lag_cols)
            pred = np.nan
        else:
            raise ValueError(cfg.model)

        rows.append({
            "date": d,
            "spread": float(df.at[d, "spread"]),
            "pred": pred,
            "prob": prob,
        })

    out = pd.DataFrame(rows).set_index("date")
    return out


def run_grid(
    daily: pd.DataFrame,
    configs: Iterable[BacktestConfig],
    oos_start: str,
) -> dict[str, pd.DataFrame]:
    """Run all configs sequentially. Returns dict[cfg.id -> forecast frame]."""
    results: dict[str, pd.DataFrame] = {}
    cfgs = list(configs)
    for i, cfg in enumerate(cfgs, 1):
        logger.info("[%d/%d] %s ...", i, len(cfgs), cfg.id)
        out = run_one_config(daily, cfg, oos_start)
        results[cfg.id] = out
    return results
