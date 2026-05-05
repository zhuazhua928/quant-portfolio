"""HMM regime overlay for the live watchlist scan.

Loads the frozen production HMM bundle (research_artifacts/hmm/production.joblib),
takes the same OHLCV bars the scan already fetched, builds 5-minute window
features that match the research pipeline, and emits a per-symbol + market
regime label with posterior probabilities.

Designed to run on a **5-minute cadence** that matches the HMM's window
granularity. Re-running every 60s would re-predict the same window N times
and produce duplicate posteriors, so the overlay is gated on the latest
window-end timestamp: if it has not advanced since the last call, the
cached result is returned.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_BUNDLE = PROJECT_ROOT / "research_artifacts" / "hmm" / "production.joblib"

HUMAN_LABELS = {
    0: "Trending Down",
    1: "Mean-Reverting",
    2: "High-Vol Breakout",
    3: "Trending Up",
}


@dataclass
class OverlayResult:
    """Per-target output: market or per-symbol HMM regime."""
    label: int
    label_name: str
    posterior: dict[str, float]   # {"p_0": .., "p_1": .., ...}
    timestamp: str                # ISO UTC of the window end this prediction is based on
    n_windows_used: int           # how many 5-min windows fed into the latest predict


@dataclass
class HMMOverlayCache:
    """Memoizes the last result keyed by latest-window-end timestamp."""
    last_window_end: dict[str, pd.Timestamp] = field(default_factory=dict)
    last_result: dict[str, OverlayResult] = field(default_factory=dict)


class HMMRegimeOverlay:
    """Live HMM scoring layer.

    Usage::

        overlay = HMMRegimeOverlay()
        market = overlay.classify_market(qqq_df, spy_df)
        per_sym = {sym: overlay.classify_symbol(sym, df, spy_df) for sym, df in bars.items()}
    """

    def __init__(self, bundle_path: Path | str = DEFAULT_BUNDLE) -> None:
        self.bundle_path = Path(bundle_path)
        self._bundle = None
        self._meta: dict | None = None
        self._cache = HMMOverlayCache()

    # ------------------------------------------------------------------
    # Lazy bundle loading (avoid importing research.* unless needed)
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._bundle is not None:
            return
        if not self.bundle_path.exists():
            raise FileNotFoundError(
                f"Production HMM bundle not found: {self.bundle_path}\n"
                "Run: python -m research.pipeline.freeze_production"
            )
        # Add the project root to sys.path so joblib can deserialize the
        # research.models.regime_hmm.HMMRegimeBundle class.
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from research.models import regime_hmm  # noqa: F401  (registers class for joblib)
        import joblib

        self._bundle = joblib.load(self.bundle_path)
        meta_path = self.bundle_path.with_suffix(".meta.json")
        if meta_path.exists():
            import json
            self._meta = json.loads(meta_path.read_text())
        logger.info("loaded HMM bundle: %s (K=%d)", self.bundle_path, self._bundle.n_components)

    @property
    def bundle(self):
        self._load()
        return self._bundle

    @property
    def meta(self) -> dict:
        self._load()
        return self._meta or {}

    # ------------------------------------------------------------------
    # Feature pipeline (delegates to research/features)
    # ------------------------------------------------------------------

    def _build_windows(self, bars: pd.DataFrame, spy_bars: pd.DataFrame | None) -> pd.DataFrame:
        """Wrap the research feature pipeline. Returns a windowed DataFrame.

        Empty DataFrame returned if bars are insufficient (need ~60+ minutes
        for the rolling beta window).
        """
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from research.features.intraday import build_features
        from research.features.windowing import make_windows

        if bars is None or bars.empty:
            return pd.DataFrame()
        feats = build_features(bars, spy_bars=spy_bars)
        if feats.empty:
            return pd.DataFrame()
        return make_windows(feats)

    # ------------------------------------------------------------------
    # Single-target classification
    # ------------------------------------------------------------------

    def _classify(self, key: str, bars: pd.DataFrame, spy_bars: pd.DataFrame | None) -> OverlayResult | None:
        windows = self._build_windows(bars, spy_bars)
        if windows.empty:
            return None
        latest_end = windows.index[-1]

        # cache hit: latest 5-min window unchanged since last call → reuse
        cached_end = self._cache.last_window_end.get(key)
        if cached_end is not None and cached_end == latest_end:
            cached = self._cache.last_result.get(key)
            if cached is not None:
                return cached

        labels, probs = self.bundle.predict(windows.iloc[[-1]])
        lbl = int(labels.iloc[0])
        if lbl < 0:
            return None
        post = {f"p_{j}": float(probs.iloc[0][f"p_{j}"]) for j in range(self.bundle.n_components)}
        result = OverlayResult(
            label=lbl,
            label_name=HUMAN_LABELS.get(lbl, f"regime_{lbl}"),
            posterior=post,
            timestamp=pd.Timestamp(latest_end).isoformat(),
            n_windows_used=int(len(windows)),
        )
        self._cache.last_window_end[key] = latest_end
        self._cache.last_result[key] = result
        return result

    def classify_market(
        self,
        qqq_bars: pd.DataFrame,
        spy_bars: pd.DataFrame,
    ) -> OverlayResult | None:
        """Apply the HMM to QQQ bars (proxy for market regime).

        SPY is used as the cross-asset for the rolling beta feature.
        """
        return self._classify("MARKET_QQQ", qqq_bars, spy_bars)

    def classify_symbol(
        self,
        symbol: str,
        bars: pd.DataFrame,
        spy_bars: pd.DataFrame,
    ) -> OverlayResult | None:
        """Apply the HMM to a single watchlist symbol."""
        return self._classify(symbol, bars, spy_bars)


# ---------------------------------------------------------------------------
# Functional helpers for callers that don't want to manage the class
# ---------------------------------------------------------------------------

_SINGLETON: Optional[HMMRegimeOverlay] = None


def get_overlay(bundle_path: Path | str | None = None) -> HMMRegimeOverlay:
    """Return a process-wide singleton overlay (avoids re-loading the bundle)."""
    global _SINGLETON
    if _SINGLETON is None or (bundle_path is not None and Path(bundle_path) != _SINGLETON.bundle_path):
        _SINGLETON = HMMRegimeOverlay(bundle_path or DEFAULT_BUNDLE)
    return _SINGLETON


def serialize_result(r: OverlayResult | None) -> dict | None:
    if r is None:
        return None
    return {
        "label": r.label,
        "label_name": r.label_name,
        "posterior": r.posterior,
        "timestamp": r.timestamp,
        "n_windows": r.n_windows_used,
    }
