"""Fit a single HMM on the full historical panel and persist as the
production bundle for live use.

Output:
  research_artifacts/hmm/production.joblib  — joblib bundle (HMMRegimeBundle)
  research_artifacts/hmm/production.meta.json — training metadata

The bundle is loaded at runtime by monitor/watchlist/regime_overlay.py to
score live 5-minute windows. Re-run monthly (or whenever the panel gets a
fresh backfill) to refresh the classifier.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from research import config
from research.models import regime_hmm

logger = logging.getLogger(__name__)


HUMAN_LABELS = {
    0: "Trending Down",
    1: "Mean-Reverting",
    2: "High-Vol Breakout",
    3: "Trending Up",
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", default=str(config.WINDOWS_DIR / "panel.parquet"))
    p.add_argument("-K", type=int, default=4)
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    config.ensure_dirs()

    panel_path = Path(args.panel)
    if not panel_path.exists():
        logger.error("panel not found: %s — run research.pipeline.build_panel first", panel_path)
        return 1

    panel = pd.read_parquet(panel_path)
    logger.info("loaded panel rows=%d cols=%d", len(panel), panel.shape[1])

    train = panel.dropna(subset=[c for c in regime_hmm.HMM_FEATURE_COLS if c in panel.columns])
    if len(train) < args.K * 200:
        logger.error("too few rows (%d) to fit a production HMM with K=%d", len(train), args.K)
        return 1

    logger.info("fitting HMM K=%d on full panel (%d rows)...", args.K, len(train))
    bundle = regime_hmm.fit_hmm(train, n_components=args.K)

    out_dir = config.HMM_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / "production.joblib"
    regime_hmm.save_bundle(bundle, bundle_path)

    # Sanity check: per-regime mean fwd 5m return on the SAME panel,
    # so users can see the in-sample semantics of each label.
    train_lbl, _ = bundle.predict(train)
    if "fwd_ret_5m" in train.columns:
        means = train.assign(lbl=train_lbl).groupby("lbl")["fwd_ret_5m"].agg(["mean", "count"])
        means["human_label"] = means.index.map(HUMAN_LABELS)
        means["mean_bps"] = means["mean"] * 1e4
        regime_summary = means[["human_label", "mean_bps", "count"]].to_dict(orient="index")
    else:
        regime_summary = {}

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "panel_rows": int(len(panel)),
        "training_rows": int(len(train)),
        "n_components": args.K,
        "feature_cols": bundle.feature_cols,
        "label_perm": bundle.label_perm.tolist(),
        "human_labels": HUMAN_LABELS,
        "panel_path": str(panel_path),
        "panel_first_ts": str(panel.index.get_level_values("ts").min()),
        "panel_last_ts": str(panel.index.get_level_values("ts").max()),
        "in_sample_regime_summary": regime_summary,
    }
    meta_path = out_dir / "production.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str))

    logger.info("saved production HMM bundle: %s", bundle_path)
    logger.info("saved metadata: %s", meta_path)
    print("\n=== In-sample regime summary ===")
    print(f"{'Label':<6} {'Human':<22} {'Mean fwd 5m (bps)':>18} {'N':>10}")
    for lbl, row in regime_summary.items():
        print(f"  {lbl:<4} {row['human_label']:<22} {row['mean_bps']:>17.2f} {row['count']:>10d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
