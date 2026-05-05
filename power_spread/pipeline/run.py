"""End-to-end CLI for the ERCOT DA/RT spread replication.

Usage:
    python -m power_spread.pipeline.run [--start 2022-01-01] [--end 2025-12-31]

Steps:
    1. Build hourly + daily panels (cached parquet under power_spread/_cache/).
    2. Run walk-forward backtest grid.
    3. Export 7 JSON files to src/data/power-spread/.
"""

from __future__ import annotations

import argparse
import logging
import sys

from ..backtest.walk_forward import BacktestConfig, run_grid
from ..config import CALIBRATION_WINDOWS, END_DATE, OOS_START, START_DATE
from ..export.export_dashboard import export_all
from ..ingest.build_panel import build_daily_panel, build_hourly_panel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("power_spread")


def build_config_grid() -> list[BacktestConfig]:
    """Default model x window x X-subset grid (mirrors paper Tables 3 & 4)."""
    x_subsets: tuple[tuple[str, ...], ...] = (
        ("demand_fcst_mean", "wind_mean"),
        ("demand_fcst_mean", "wind_mean", "solar_mean"),
        ("wind_mean",),
    )
    configs: list[BacktestConfig] = []
    for model in ("arx_levels", "arx_spread", "probit"):
        for T in CALIBRATION_WINDOWS:
            if T == 30 and model == "probit":
                # paper notes probit needs more data — skip the shortest window
                continue
            for x in x_subsets:
                configs.append(BacktestConfig(model=model, window=T, x_cols=x, lag_set=(2, 7)))
    return configs


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", default=START_DATE)
    p.add_argument("--end", default=END_DATE)
    p.add_argument("--oos-start", default=OOS_START)
    args = p.parse_args()

    logger.info("=== Stage 1/3: ingest + panel ===")
    hourly = build_hourly_panel(start=args.start, end=args.end)
    daily = build_daily_panel(hourly, start=args.start, end=args.end)
    logger.info("hourly rows: %d, daily rows: %d", len(hourly), len(daily))

    logger.info("=== Stage 2/3: walk-forward backtest grid ===")
    configs = build_config_grid()
    logger.info("running %d configs ...", len(configs))
    forecasts = run_grid(daily, configs, oos_start=args.oos_start)

    logger.info("=== Stage 3/3: export JSON ===")
    paths = export_all(daily, hourly, forecasts, configs)
    print()
    for k, v in paths.items():
        print(f"  {k:12s} -> {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
