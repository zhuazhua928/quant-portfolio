"""Global configuration for the research pipeline."""

from __future__ import annotations

from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------

# 25 high-beta US equities (CAPM beta > 1.3 vs SPY, growth-tilted, sufficient
# liquidity for IEX coverage). The screen is sanity-checked at runtime by
# research/data/universe.py against rolling 60-day daily returns.
HIGH_BETA = [
    "TSLA", "NVDA", "AMD", "COIN", "MSTR", "PLTR", "HOOD", "SOFI", "RIVN",
    "LCID", "SHOP", "RBLX", "SNOW", "NET", "DDOG", "CRWD", "MDB", "MARA",
    "RIOT", "META", "AMZN", "GOOGL", "MSFT", "AAPL", "NFLX",
]

# Market-state covariates. VXX is used as an Alpaca-available proxy for VIX
# (CBOE indices are not served by Alpaca).
COVARIATES = ["SPY", "QQQ", "VXX"]

UNIVERSE = HIGH_BETA + COVARIATES

# ---------------------------------------------------------------------------
# Date window
# ---------------------------------------------------------------------------

START = date(2022, 1, 1)
END = date(2026, 3, 31)

# ---------------------------------------------------------------------------
# Feature / windowing parameters
# ---------------------------------------------------------------------------

RETURN_HORIZONS_MIN = (1, 5, 15)
RV_WINDOW_MIN = 30                 # realized-volatility window
BETA_WINDOW_MIN = 60               # rolling intraday beta vs SPY
AMIHUD_WINDOW_MIN = 30
WINDOW_SIZE_MIN = 5                # 5-min feature windows fed to HMM/HDBSCAN
FORECAST_HORIZONS_MIN = (5, 30)    # Stage-2 prediction horizons

# ---------------------------------------------------------------------------
# Walk-forward CV
# ---------------------------------------------------------------------------

CV_N_SPLITS = 6
CV_EMBARGO_DAYS = 5

# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------

COST_BPS_PER_SIDE = 1.0            # 1 bp transaction cost per side
SIGNAL_THRESHOLD_BPS = 5.0         # only trade when |predicted return| > 5 bps

# ---------------------------------------------------------------------------
# Macro-event calendar (FOMC / CPI / NFP) — hardcoded, public schedule.
# Keys are ISO date strings. Values are sets of event tags.
# ---------------------------------------------------------------------------

MACRO_EVENTS: dict[str, tuple[str, ...]] = {
    # FOMC meeting decision dates (Wed, 2pm ET)
    "2022-01-26": ("FOMC",), "2022-03-16": ("FOMC",), "2022-05-04": ("FOMC",),
    "2022-06-15": ("FOMC",), "2022-07-27": ("FOMC",), "2022-09-21": ("FOMC",),
    "2022-11-02": ("FOMC",), "2022-12-14": ("FOMC",),
    "2023-02-01": ("FOMC",), "2023-03-22": ("FOMC",), "2023-05-03": ("FOMC",),
    "2023-06-14": ("FOMC",), "2023-07-26": ("FOMC",), "2023-09-20": ("FOMC",),
    "2023-11-01": ("FOMC",), "2023-12-13": ("FOMC",),
    "2024-01-31": ("FOMC",), "2024-03-20": ("FOMC",), "2024-05-01": ("FOMC",),
    "2024-06-12": ("FOMC",), "2024-07-31": ("FOMC",), "2024-09-18": ("FOMC",),
    "2024-11-07": ("FOMC",), "2024-12-18": ("FOMC",),
    "2025-01-29": ("FOMC",), "2025-03-19": ("FOMC",), "2025-05-07": ("FOMC",),
    "2025-06-18": ("FOMC",), "2025-07-30": ("FOMC",), "2025-09-17": ("FOMC",),
    "2025-10-29": ("FOMC",), "2025-12-10": ("FOMC",),
    "2026-01-28": ("FOMC",), "2026-03-18": ("FOMC",),
}
# CPI and NFP are typically the second Friday / second Wednesday of each month;
# the feature pipeline approximates these by month-day rules in features/intraday.py
# rather than enumerating every release here.

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "research_data"
BARS_DIR = DATA_DIR / "bars"                # research_data/bars/{SYMBOL}/{YYYY-MM}.parquet
FEATURES_DIR = DATA_DIR / "features"
WINDOWS_DIR = DATA_DIR / "windows"

ARTIFACTS_DIR = PROJECT_ROOT / "research_artifacts"
HMM_DIR = ARTIFACTS_DIR / "hmm"
HDBSCAN_DIR = ARTIFACTS_DIR / "hdbscan"
LGB_DIR = ARTIFACTS_DIR / "lgb"
RESULTS_DIR = ARTIFACTS_DIR / "results"

DASHBOARD_DATA_DIR = PROJECT_ROOT / "src" / "data" / "research"
DASHBOARD_SESSIONS_DIR = DASHBOARD_DATA_DIR / "sessions"


def ensure_dirs() -> None:
    """Create all data / artifact directories on demand."""
    for p in [
        DATA_DIR, BARS_DIR, FEATURES_DIR, WINDOWS_DIR,
        ARTIFACTS_DIR, HMM_DIR, HDBSCAN_DIR, LGB_DIR, RESULTS_DIR,
        DASHBOARD_DATA_DIR, DASHBOARD_SESSIONS_DIR,
    ]:
        p.mkdir(parents=True, exist_ok=True)
