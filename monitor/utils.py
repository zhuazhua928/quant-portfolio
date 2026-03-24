import logging
from datetime import datetime, time, timezone, timedelta

from .config import BTC_ANNUALIZATION, EQUITY_ANNUALIZATION

ET = timezone(timedelta(hours=-5))


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def is_us_market_open() -> bool:
    now_et = datetime.now(ET)
    if now_et.weekday() >= 5:
        return False
    return time(9, 30) <= now_et.time() <= time(16, 0)


def get_annualization_factor(name: str) -> float:
    if name == "BTC":
        return BTC_ANNUALIZATION
    return EQUITY_ANNUALIZATION
