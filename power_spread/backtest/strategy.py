"""Decision rule: from a forecasted spread (or probability), produce Y_hat.

ARX-style: Y_hat = 1{spread_hat > 0}
Probit-style: Y_hat = 1{Phi > mu}
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def decide_from_spread(spread_hat: pd.Series) -> pd.Series:
    return (spread_hat > 0).astype("Int64").rename("y_hat")


def decide_from_probit(prob: pd.Series, mu: float) -> pd.Series:
    return (prob > mu).astype("Int64").rename("y_hat")
