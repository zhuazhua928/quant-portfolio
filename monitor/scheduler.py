import logging
import time

from .config import BACKOFF_INTERVAL_SECONDS, POLL_INTERVAL_SECONDS, SYMBOLS
from .features import compute_all_features
from .ingest import fetch_all_intraday
from .storage import (
    ensure_directories,
    save_features_parquet,
    save_intraday_parquet,
    save_latest_json,
    save_snapshot_json,
)

logger = logging.getLogger(__name__)


def run_loop() -> None:
    ensure_directories()
    logger.info("Monitor started — tracking %d symbols", len(SYMBOLS))

    while True:
        try:
            data = fetch_all_intraday(SYMBOLS)

            if not data:
                logger.info(
                    "No data for any symbol — backing off %ds",
                    BACKOFF_INTERVAL_SECONDS,
                )
                time.sleep(BACKOFF_INTERVAL_SECONDS)
                continue

            features = compute_all_features(data)

            save_latest_json(features)
            save_snapshot_json(features)
            save_intraday_parquet(data)
            save_features_parquet(features)

            names = ", ".join(f["name"] for f in features)
            logger.info("Cycle complete — %d symbols: %s", len(features), names)

            time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Shutting down gracefully")
            break
        except Exception:
            logger.exception("Unexpected error in poll loop")
            time.sleep(POLL_INTERVAL_SECONDS)
