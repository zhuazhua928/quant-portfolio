"""Classification metrics from Eqs (10)-(12) of the paper.

p  = (1/HT) sum 1{Y_ht == Y_hat_ht}                       overall accuracy
q0 = mean(Y == Y_hat | Y_hat == 0)                         conditional acc on DA pick
q1 = mean(Y == Y_hat | Y_hat == 1)                         conditional acc on RT pick
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def classification_stats(y_true: pd.Series, y_hat: pd.Series) -> dict:
    a = pd.concat([y_true.rename("t").astype("Int64"), y_hat.rename("p").astype("Int64")], axis=1).dropna()
    if a.empty:
        return {"n": 0, "p": float("nan"), "q0": float("nan"), "q1": float("nan")}
    n = int(len(a))
    p = float((a["t"] == a["p"]).mean())
    mask0 = a["p"] == 0
    mask1 = a["p"] == 1
    q0 = float((a.loc[mask0, "t"] == 0).mean()) if int(mask0.sum()) > 0 else float("nan")
    q1 = float((a.loc[mask1, "t"] == 1).mean()) if int(mask1.sum()) > 0 else float("nan")
    return {"n": n, "p": p, "q0": q0, "q1": q1}
