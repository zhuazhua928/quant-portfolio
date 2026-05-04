# Intraday Trend Detection & Regime Monitoring

EN.553.640 *Machine Learning in Finance* final project — a two-stage ML
pipeline for high-beta U.S. equities. Stage 1 classifies the current intraday
regime (Gaussian HMM, with HDBSCAN as a non-parametric alternative). Stage 2
trains a per-regime LightGBM forecaster of the forward 5-minute log return.
Evaluated with 6-fold walk-forward cross-validation using a 5-day purged
embargo (López de Prado 2018) and a transaction-cost-aware backtest.

## Quick start

```bash
# 1. install
pip install -r research/requirements.txt

# 2. set credentials (or put them in .env at repo root)
export APCA_API_KEY_ID=...
export APCA_API_SECRET_KEY=...

# 3. backfill bars (resumable; ~1-2 hours on free tier for full universe)
python -m research.data.fetch_bars

# 4. build feature panel
python -m research.pipeline.build_panel

# 5. walk-forward train + evaluate
python -m research.pipeline.train_and_evaluate -K 4

# 6. export dashboard JSON
python -m research.export.export_dashboard
```

## Data

| Item            | Value                                                        |
|-----------------|--------------------------------------------------------------|
| Source          | Alpaca Markets (alpaca-py SDK), IEX free feed                |
| Bar frequency   | 1-minute OHLCV                                               |
| Window          | 2022-01-01 → 2026-03-31                                      |
| High-beta names | 25 (TSLA, NVDA, AMD, COIN, MSTR, PLTR, HOOD, … META, AMZN, GOOGL, MSFT, AAPL, NFLX) |
| Covariates      | SPY, QQQ, **VXX** (Alpaca-native VIX proxy)                  |
| Storage         | Parquet partitioned by symbol/year-month                     |

**Caveat — IEX feed:** IEX represents roughly 2–3 % of US consolidated volume.
Minute-level volume and VWAP from the free tier are partial; for a full
consolidated tape (and accurate volume / VWAP) the SIP feed (Algo Trader Plus,
~$99/mo) is required. Set `APCA_DATA_FEED=sip` in `.env` to switch.

**Caveat — VIX:** Alpaca does not serve CBOE indices, so VXX (a VIX-futures
ETF available on Alpaca) is used as a proxy. Realized volatility computed
from 1-minute returns supplements this.

## Architecture

```
research/
  data/         alpaca_client.py     Alpaca historical bars (alpaca-py)
                fetch_bars.py        CLI: monthly parquet backfill
                universe.py          rolling-60d β screen vs SPY
  features/     intraday.py          per-bar features
                windowing.py         5-min non-overlapping windows
  models/       regime_hmm.py        GaussianHMM (K=3,4)
                regime_hdbscan.py    non-parametric Stage-1
                forecaster_lgb.py    per-regime LightGBM
                baselines.py         single-stage LGB, naive momentum
  evaluation/   walkforward.py       purged k-fold + 5d embargo
                metrics.py           accuracy, Brier, log-loss, IC, MAE
                backtest.py          1bp/side cost, equity curve, Sharpe
  pipeline/     build_panel.py       bars → features → windows → panel
                train_and_evaluate.py walk-forward train + score
  export/       export_dashboard.py  writes src/data/research/*.json
```

### Stage 1 — Regime classification

Gaussian HMM (`hmmlearn`) with full covariance, K∈{3,4}, fit on the
following standardized 5-minute window features:

```
ret_1m_w  ret_5m_w  ret_15m_w   (log returns, summed over the window)
rv  pk_vol                       (realized vol + Parkinson range vol)
vwap_dev                         (close vs session VWAP)
ofi                              (Lee–Ready tick-rule order-flow imbalance)
beta_t                           (rolling 60-min β vs SPY)
spy_ret_5m                       (5-min SPY log return)
```

After fitting, raw HMM states are relabeled by their mean forward 5-min
return so label 0 is the most bearish regime and label K-1 the most bullish.
HDBSCAN is fit as a non-parametric alternative; clusters are labeled by the
same convention and the smallest clusters are demoted to noise (`-1`).

### Stage 2 — Conditional forecasting

For each regime label k, a separate `LGBMRegressor` predicts the forward
5-minute log return; a parallel `LGBMClassifier` predicts the sign for Brier
and log-loss evaluation. A global LightGBM is always trained as a fallback
when a regime has fewer than 500 training rows.

Hyperparameters: `n_estimators=400`, `learning_rate=0.03`, `num_leaves=63`,
`min_child_samples=50`, `subsample=0.85`, `colsample_bytree=0.85`,
`reg_lambda=1.0`. Tuned conservatively to reduce overfitting on the
intraday panel.

### Baselines

* **Naive momentum** — `pred_5m = 0.5 · ret_5m_w` (persistence with shrinkage).
* **Single-stage LGB** — same feature set as the conditional forecaster,
  trained without any regime conditioning.

### Walk-forward evaluation

`research/evaluation/walkforward.py` implements the López de Prado
purged-with-embargo design: the time-ordered window index is split into 7
contiguous chunks; folds 0..5 use chunks 0..k as expanding training data
(minus a 5-day embargo immediately preceding the test fold) and chunk k+1
as the test fold. This prevents target-leakage when the forward-return
horizon spans the train/test boundary.

### Backtest

Vectorized: `position_t = +1` if `pred_t > +5 bps`, `-1` if `pred_t < −5 bps`,
else 0. Realized PnL `= position_t · realized_fwd_ret − 1bp · |Δposition|`.
Aggregated equally across symbols, summed to daily, cumulated to an equity
curve.

## Smoke results (Q1 2024, 5 symbols)

End-to-end smoke run on TSLA, NVDA, AMD, QQQ, VXX over 2024-01-02 → 2024-03-29
(≈ 20 k 5-minute windows total; 6 walk-forward folds).

| Model                  | Dir. Acc. | Brier | Log-loss | IC    | MAE (bps) |
|------------------------|-----------|-------|----------|-------|-----------|
| Two-Stage (HMM + LGB)  | **51.11%** | 0.2825 | 0.7737  | **+0.021** | 21.37 |
| Single-Stage LGB       | 51.05%    | **0.2769** | **0.7591** | +0.018 | **21.18** |
| Naive Momentum         | 49.23%    | 0.3206 | 0.9221  | −0.023 | 42.29   |

**Reading:** Both ML models decisively beat naive momentum (≈ 1.9 pp dir-acc
edge, halved MAE). The two-stage model marginally edges single-stage on
directional accuracy and IC; single-stage has slightly better calibration
(Brier / log-loss). On a 3-month, 5-symbol smoke this gap is well within
sampling noise — the full 4-year × 25-name backfill is needed to produce a
statistically discriminating comparison.

## Out of scope

* **LSTM / Temporal Fusion Transformer** — listed in the proposal as Stage-2
  candidates but deferred. The two-stage HMM + LightGBM design is sufficient
  to test the *conditional-on-regime* hypothesis without the engineering
  cost of TFT (`pytorch-forecasting`).
* **Live execution** — research-only pipeline; no paper-trading wiring.
* **FOMC/CPI/NFP scrape** — calendar dummies are computed by month-day rules
  (CPI = 2nd Wed; NFP = 1st Fri) plus an explicit FOMC date list in
  `research/config.py`.

## References

1. Cont, R. (2001). *Quantitative Finance.*
2. Hamilton, J. D. (1989). *Econometrica.*
3. Cartea, Á., Jaimungal, S., & Penalva, J. (2015). *Algorithmic and HFT.*
4. Sezer, O. B. et al. (2020). *Applied Soft Computing.*
5. Lim, B. et al. (2021). *International Journal of Forecasting.*
6. López de Prado, M. (2018). *Advances in Financial ML.*
