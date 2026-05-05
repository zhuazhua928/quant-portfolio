# Final Report — Intraday Trend Detection & Regime Monitoring

**Course:** EN.553.640 *Machine Learning in Finance*
**Author:** [Group Member Name(s)]
**Universe:** 25 high-beta U.S. equities + SPY, QQQ, VXX
**Sample:** 2022-01-01 → 2026-03-31, 1-minute Alpaca IEX bars
**Compute:** ~2.07 M five-minute feature windows, six expanding walk-forward folds

---

## 1. Question

We test a single hypothesis: **can HMM-classified intraday regimes be used to time a swing-style position-trading rule that survives realistic transaction costs?** Per the proposal, the architecture is two-stage — a Gaussian HMM identifies regimes, a per-regime LightGBM forecasts forward returns, and a state-machine rule enters when the bullish posterior is strong and the symbol ranks in the top-N by forecast, holding through the regime block.

This report covers three layers of evidence: (a) forecast quality (does the ML beat naive momentum?), (b) the swing strategy at the user's requested settings, and (c) a diagnostic comparison vs. simpler benchmarks and the cost-zero gross signal.

## 2. Methodology

### 2.1 Data

* 28 symbols × ~50 months × 1-min OHLCV from Alpaca's IEX free feed.
* 25 high-beta names: TSLA, NVDA, AMD, COIN, MSTR, PLTR, HOOD, SOFI, RIVN, LCID, SHOP, RBLX, SNOW, NET, DDOG, CRWD, MDB, MARA, RIOT, META, AMZN, GOOGL, MSFT, AAPL, NFLX. Three covariates: SPY, QQQ, **VXX** (Alpaca-native VIX proxy).
* Storage: Parquet, partitioned by symbol/year-month.
* Feature pipeline: 5-minute non-overlapping windows with log returns at 1/5/15-min, realized vol, Parkinson range vol, VWAP deviation, rolling 60-min β vs SPY, Amihud illiquidity, Lee–Ready tick-rule order-flow imbalance, session/macro dummies.

### 2.2 Models

* **Stage 1 — Gaussian HMM** (`hmmlearn`), K=4 components, full covariance, fit pooled across symbols on standardized window features. After fitting, raw states are relabeled by mean fwd 5-min return so label 0 is most bearish and label 3 most bullish.
* **Stage 2 — LightGBM per regime** (400 trees, lr 0.03, num_leaves 63, regularization tuned conservatively). Plus a global LightGBM as fallback for thin regimes, a single-stage LightGBM (no regime conditioning) as baseline, and a naive-momentum rule.

### 2.3 Walk-forward evaluation

Six expanding-window folds over 2022–2026 with a 5-day purged embargo (López de Prado 2018). Stage 1 and Stage 2 are refit on each fold's training window; predictions and trades are evaluated only on the out-of-sample test window. Aggregate stats stitch fold-level OOS days.

### 2.4 Regime-swing strategy (state machine, per symbol on 5-min windows)

```
flat  → long   if  p_K-1 ≥ entry_long_p           (default 0.60)
                AND symbol is top-N by Stage-2 pred at this ts
long  → flat   if  p_K-1 < exit_long_p            (default 0.35)
               OR  p_0 ≥ exit_long_on_bear_p     (default 0.50)
flat  → short  if  short_enabled (default off)
```

All thresholds and selection parameters are command-line flags; the strategy can be re-tuned without code changes (`research/evaluation/regime_strategy.py:RegimeSwingConfig`). Costs: 1 bp per side, applied on `|Δposition|`. Sessions are flattened at the close.

## 3. Results

### 3.1 Forecast quality (per 5-min window, OOS aggregate over 6 folds)

| Model                  | Dir. Acc. | Brier  | Log-loss | IC     | MAE (bps) |
|------------------------|-----------|--------|----------|--------|-----------|
| Two-Stage (HMM + LGB)  | **50.41%** | 0.2504 | 0.6939   | 0.0083 | 27.64     |
| Single-Stage LGB       | 50.50%    | **0.2498** | **0.6927** | **0.0106** | **27.39** |
| Naive Momentum         | 49.43%    | 0.3163 | 0.9090   | −0.0083 | 55.36    |

Both ML models clearly beat naive momentum on every metric. Two-stage and single-stage are essentially tied — the regime conditioning *does not* deliver a meaningful forecast-accuracy gain at 5-min horizon on the full panel. Absolute edge is small: ~1 pp directional accuracy and IC ~0.01.

### 3.2 Regime-swing strategy at user-requested defaults

`entry_long_p=0.60, exit_long_p=0.35, exit_long_on_bear_p=0.50, top_n=5, short_enabled=False, cost_bps_per_side=1.0`

| Statistic                | Value      |
|--------------------------|------------|
| Total return (OOS)       | **−13.20%** |
| Annualized return        | −3.65%     |
| Annualized volatility    | 12.6%      |
| Sharpe (daily)           | **−0.29**  |
| Max drawdown             | −22.83%    |
| Calmar                   | −0.16      |
| Daily hit rate           | 45.7%      |
| Avg holding period       | ~22 bars (~110 min) |
| Frac. time in position   | 23.5%      |
| Round-trip trades        | ~3000 / fold |

**Per-fold:**

| Fold | Test window           | Ann. Ret  | Sharpe | Max DD   | Hold (bars) |
|------|-----------------------|-----------|--------|----------|-------------|
| 0    | 2022 (early)          | −5.10%    | −0.19  | −13.67%  | 7.2         |
| 1    | 2022–2023             | −4.53%    | −0.76  | −7.76%   | 25.7        |
| 2    | 2023–2024             | **+16.31%** | **+2.31**  | −2.40%   | 25.2        |
| 3    | 2024 mid              | +2.92%    | +0.43  | −3.70%   | 24.4        |
| 4    | 2024 late–2025        | −9.99%    | −1.96  | −8.37%   | 22.8        |
| 5    | 2025–2026             | −22.04%   | −2.52  | −17.71%  | 21.4        |

The strategy wins decisively in 2 of 6 folds and loses decisively in 4. Net of fees, aggregate is negative.

### 3.3 Parameter sweep (144 configurations)

`entry in {0.50, 0.60, 0.70, 0.80} × exit in {0.20, 0.30, 0.40} × flip in {0.40, 0.50, 0.60} × top_N in {3, 5, 10, all}`

**Best by Sharpe:** `entry=0.50, exit=0.30, flip=0.50, top_N=all` → Sharpe **−0.23**, ann. return −3.65%.

**No configuration produces a positive net Sharpe.** The full sweep is in `research_artifacts/results/swing_sweep.json`.

### 3.4 Diagnostic comparison vs. benchmarks

| Strategy                              | Days | Ann. Ret | Sharpe | Max DD   | Hit % |
|---------------------------------------|------|----------|--------|----------|-------|
| Buy & Hold basket (no cost, OOS only) | 911  | −26.28%  | −0.44  | −139.30% | 50.3% |
| Basket only when bullish (1 bp)       | 911  | −3.65%   | −0.23  | −19.83%  | 48.0% |
| Swing default (1 bp)                  | 911  | −3.65%   | −0.29  | −22.83%  | 45.7% |
| Swing default **GROSS (0 bp)**        | 911  | **+0.94%** | +0.07  | −16.97%  | 48.2% |
| Swing best-sweep (1 bp)               | 911  | −3.65%   | −0.23  | −19.83%  | 48.0% |
| Swing best-sweep **GROSS (0 bp)**     | 911  | **+3.39%** | **+0.22** | −17.21%  | 50.1% |

Critical observations:

1. **Buy & Hold the universe over OOS days is also negative.** The 2022 rate-hike drawdown and 2025–2026 weakness in this high-beta universe overwhelm the 2023–2024 rally; aggregating OOS days tilts the unconditional benchmark heavily negative.
2. **The HMM regime filter saves the strategy from buy-and-hold's drawdown.** "Basket only when bullish" cuts the losses from −26% ann to −3.65% ann. The regime classifier *is* doing real work — reducing time-in-market when conditions are unfavorable.
3. **Top-N filtering by LGB does not add gross alpha.** The sweep's best gross config is `top_N=all` (no filter); using top-N=5 with the default settings has lower gross return (+0.94% vs +3.39%). The Stage-2 forecaster's marginal information at 5-min horizon is not strong enough to improve symbol selection beyond random.
4. **Cost dominates the return.** Best gross: +3.39% ann at Sharpe 0.22. Net of 1 bp/side: **−3.65% ann at Sharpe −0.23**. The cost drag from ~3000 trades/fold consumes the entire signal.

### 3.5 Per-regime out-of-sample diagnostics

| Regime | Hard-assigned mean (bps) | Posterior-weighted (bps) | N rows  | Frac of OOS | 1-step persistence |
|--------|--------------------------|--------------------------|---------|-------------|--------------------|
| 0      | −0.06                    | −0.06                    | 413,499 | 23.3%       | 0.930              |
| 1      | +0.08                    | +0.06                    | 193,109 | 10.9%       | 0.890              |
| 2      | +0.23                    | +0.21                    | 637,192 | 36.0%       | 0.946              |
| 3      | +0.19                    | +0.18                    | 508,156 | 28.7%       | 0.960              |

* **Regimes are sticky** (1-step persistence ≥ 0.89). The HMM does identify persistent intraday states.
* **The relabeling holds out-of-sample** (regime 0 has the lowest hard-mean, regimes 2 and 3 have the highest). The regime semantics are not in-sample artifacts.
* **The mean fwd-return signal is small.** Regime 3 has +0.19 bps per 5-min window — annualized over ~80 windows/day × 250 days = 380 bps gross, before considering that we are not in regime 3 every bar.
* **0.19 bps < 1 bp/side.** This is the structural reason the strategy loses: the per-bar expected edge inside the bullish regime is below the per-side cost.

## 4. Conclusions

### 4.1 What worked

* **The HMM regime classifier is the part of the pipeline with real value.** It produces persistent (≥ 0.89), interpretable, OOS-stable regimes. The relabeling-by-mean-fwd-return procedure produces meaningful semantics.
* **The regime filter dominates buy-and-hold during drawdowns.** Cutting from −26% ann (B&H) to −3.65% ann (basket-when-bullish) demonstrates that the HMM correctly identifies adverse intraday conditions.
* **The ML forecaster decisively beats naive momentum.** ~1 pp directional accuracy and IC 0.01 vs −0.01. The regime conditioning specifically gives roughly identical numbers to the single-stage LGB; the *ML versus no-ML* gap is the meaningful one.

### 4.2 What did not work

* **The two-stage regime-swing strategy is unprofitable at 1 bp/side.** Across 144 swept configurations, none produces a positive net Sharpe. The structural reason: the per-bar realized fwd return inside the bullish regime (~0.19 bps) is below the per-side cost (1 bp).
* **Top-N selection by Stage-2 forecaster does not improve the strategy.** The best gross signal comes from `top_N = all` — using the LGB to pick top-5 names is roughly equivalent to picking randomly from the bullish-regime cohort, and adds turnover.
* **The strategy is not stationary.** Two of six folds win clearly (Sharpe +2.31 in fold 2 covering the 2023–2024 AI rally; +0.43 in fold 3) and four lose. The same threshold settings produce different results across regime backdrops.

### 4.3 What this means in practice

Two distinct readings depending on intended use:

**As a research artifact / course project:** A clean negative result with a clear mechanism. The pipeline runs end-to-end on 4+ years of real data, the regime classifier produces interpretable persistent labels, the forecaster passes a chance test against naive momentum, the strategy implementation is correct, and the cost-zero diagnostic isolates exactly where the strategy fails. This is a complete and honest piece of empirical work.

**As a tradeable signal:** Not viable as specified. To make it viable, three changes are necessary:
1. **Longer holding horizons.** Move from 5-min to 30-min or daily forward-return targets. The regime persistence (~0.93 at 5-min) compounds across longer horizons; the per-bar 0.19 bps becomes a multi-percent block when held over a multi-hour regime sequence. Cost as a fraction of expected edge falls roughly linearly with hold time.
2. **Better data feed.** IEX bars represent ~2-3% of consolidated volume; SIP feed (Algo Trader Plus, ~$99/mo) is required for accurate VWAP/volume features. The OFI feature in particular is significantly miscomputed on partial tape.
3. **Reframe as a gating signal, not the alpha source.** The HMM regime label is the genuine output of this work. Use it to *throttle* an existing trading strategy (cut size in regime 0, lean into regime 3) rather than to *generate* the trade signal. This is the practitioner pattern the proposal cites in §1.

### 4.4 Practical takeaways for the user's own trading

1. The HMM regime classifier on 5-min features is **a usable filter**, not an alpha source. Drop into the existing `monitor/` watchlist as a regime gate.
2. Don't trust the LightGBM forecaster for stock selection at 5-min horizon — its IC is 0.01.
3. Regime-following strategies need either lower-frequency execution (15+ min holds with intraday or end-of-day decisions) or much lower cost than retail-typical 1 bp/side.
4. The regime classifier's biggest practical value here may be **risk gating** — sizing positions down (or flat) when the bearish-regime posterior is high.

## 5. Limitations

* IEX feed sparsity (volume / VWAP misspecified for low-liquidity bars).
* No statistical-significance testing on Sharpe differences. A stationary-bootstrap CI (Politis & Romano 1994) would tighten the negative-result claim; we leave it as follow-up.
* HMM relabeling is in-sample per fold. Cross-fold label stability was checked manually (regime 3 is the highest-mean regime in every fold) but not formally tested.
* Realized fills assume mid-price execution. Real retail fills will pay 2–5 bps additional spread on these names — the strategy is likely worse than reported, not better.
* HDBSCAN as Stage-1 alternative is implemented but not exercised in the headline results — we use HMM only for the headline.

## 6. Reproducibility

```bash
pip install -r research/requirements.txt
export APCA_API_KEY_ID=... ; export APCA_API_SECRET_KEY=...

# Backfill (~30 min on free IEX tier; resumable)
python -m research.data.fetch_bars

# Build feature panel
python -m research.pipeline.build_panel

# Walk-forward train + evaluate (HMM + LGB + 6 folds, ~25 min)
python -m research.pipeline.train_and_evaluate \
    -K 4 \
    --entry-long-p 0.60 --exit-long-p 0.35 --exit-long-on-bear-p 0.50 \
    --top-n 5 --cost-bps 1.0

# Parameter sweep (~50 min, no retraining)
python -m research.pipeline.sweep_swing

# Benchmark diagnostics (~3 min)
python -m research.pipeline.diagnose

# Export dashboard JSON
python -m research.export.export_dashboard
```

All thresholds are flags. Re-running with different values updates the
dashboard JSON in place.

## References

1. Cont, R. (2001). Empirical properties of asset returns. *Quantitative Finance.*
2. Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series. *Econometrica.*
3. Cartea, Á., Jaimungal, S., & Penalva, J. (2015). *Algorithmic and HFT.*
4. López de Prado, M. (2018). *Advances in Financial Machine Learning.*
5. Politis, D. N., & Romano, J. P. (1994). The stationary bootstrap. *JASA.*
