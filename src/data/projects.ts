export interface Project {
  slug: string;
  code: string;
  title: string;
  subtitle: string;
  category: string;
  period: string;
  tags: string[];
  summary: string;
  sections: {
    title: string;
    content: string;
  }[];
  highlights: string[];
  /** If true, the detail page has a custom implementation (e.g. embedded dashboard). */
  custom?: boolean;
}

export const projects: Project[] = [
  {
    slug: "intraday-ml-research",
    code: "P0",
    title: "Intraday Trend Detection & Regime Monitoring (ML)",
    subtitle:
      "Two-stage ML pipeline for high-beta U.S. equities — HMM regime classifier + LightGBM conditional forecaster",
    category: "Machine Learning Research",
    period: "2026",
    tags: [
      "HMM",
      "HDBSCAN",
      "LightGBM",
      "Walk-Forward CV",
      "Alpaca",
      "Python",
    ],
    summary:
      "ML in Finance final project (EN.553.640): a two-stage architecture for forecasting 5–30 minute directional drift on high-beta U.S. equities. Stage 1 fits a Gaussian HMM (with HDBSCAN as a non-parametric comparison) on 5-minute windowed features to classify the current intraday regime. Stage 2 trains a per-regime LightGBM forecaster. The headline trading strategy is a regime-swing rule: enter the top-N forecast names when the bullish regime posterior crosses an entry threshold, hold through the regime block, and exit only on regime flip — collapsing turnover by 1-2 orders of magnitude vs. per-bar trading so realistic transaction costs do not eat the edge. All entry/exit thresholds and selection parameters are configurable for re-tuning. Evaluated with 6-fold walk-forward cross-validation using purged 5-day embargoes.",
    sections: [
      {
        title: "Universe and Data",
        content:
          "25 high-beta US equities (β > 1.3 vs SPY, including TSLA, NVDA, COIN, MSTR, PLTR, HOOD, MARA, RIOT, plus mega-cap growth such as META/AMZN/GOOGL/MSFT/AAPL/NFLX) plus SPY, QQQ, and VXX as market-state covariates. Data is 1-minute OHLCV from Alpaca Markets (IEX free feed) covering 2022-01-01 through 2026-03-31, partitioned to parquet by symbol/year-month for resumable backfill. VXX serves as an Alpaca-native VIX proxy since CBOE indices are not on the Alpaca tape.",
      },
      {
        title: "Stage 1 — Regime Classification",
        content:
          "A Gaussian Hidden Markov Model (K∈{3,4}, full covariance) is fit on standardized 5-minute window features: log returns at 1/5/15-minute horizons, realized volatility, Parkinson range volatility, VWAP deviation, rolling intraday β vs SPY (60-minute window), Amihud illiquidity, and a Lee–Ready tick-rule order-flow imbalance. HMM states are relabeled by mean forward 5-minute return so label 0 is the most bearish regime and label K-1 the most bullish. HDBSCAN is fit as a non-parametric alternative.",
      },
      {
        title: "Stage 2 — Conditional Trend Forecasting",
        content:
          "For each regime label, a separate LightGBM regressor predicts the forward 5-minute log return; a parallel binary classifier predicts the sign for Brier and log-loss evaluation. A global LightGBM serves as a fallback when a regime has too few training rows. Baselines: a single-stage LightGBM (no regime conditioning) and a naive momentum rule with shrinkage. All models share the same feature set so head-to-head comparisons are clean.",
      },
      {
        title: "Regime-Swing Trading Strategy",
        content:
          "Rather than betting on noisy 5-minute directional forecasts, the headline strategy uses HMM regime persistence to time longer holding periods. State machine per symbol: enter long when the bullish posterior p_K-1 ≥ entry_long_p AND the symbol is in the top-N by Stage-2 expected return at that timestamp; exit when p_K-1 falls below exit_long_p OR the bearish posterior p_0 ≥ exit_long_on_bear_p. This collapses average turnover by 1-2 orders of magnitude versus per-bar trading and lets a small forecast edge survive realistic transaction costs. All thresholds (entry_long_p, exit_long_p, exit_long_on_bear_p, top_n_per_regime, short_enabled, cost_bps_per_side, vol_target_annual) are command-line flags so the strategy can be re-tuned without code changes.",
      },
      {
        title: "Walk-Forward Evaluation",
        content:
          "Six expanding-window walk-forward folds across the 2022–2026 sample with a 5-day embargo between train and test (López de Prado 2018) to prevent forward-return leakage. Each fold reports forecast quality (directional accuracy, Brier score, log-loss, MAE in basis points, Spearman rank IC) and trading economics (annualized return, Sharpe, max drawdown, Calmar, hit rate, average holding period in bars, total trade count). Both a per-bar minute backtest and the regime-swing backtest are computed on every fold's out-of-sample test window with 1 bp per-side transaction costs.",
      },
      {
        title: "Implementation",
        content:
          "Python package research/ with submodules data, features, models, evaluation, pipeline, export. Uses alpaca-py, hmmlearn, hdbscan, lightgbm, and scikit-learn. The pipeline is resumable: parquet caches survive interruptions, and walk-forward folds can be replayed independently. Dashboard JSON is exported to src/data/research/ and rendered by this page; the build is fully static.",
      },
    ],
    highlights: [
      "25 high-beta US equities + SPY/QQQ/VXX, 4+ years of 1-min bars",
      "Two-stage architecture: HMM regime → per-regime LightGBM",
      "Regime-swing strategy: hold through regime block, not per-bar",
      "All entry/exit thresholds configurable for re-tuning",
      "Walk-forward CV with 5-day purged embargo",
      "Alpaca-only data (IEX free feed, VXX as VIX proxy)",
    ],
    custom: true,
  },
  {
    slug: "intraday-regime-monitor",
    code: "P1",
    title: "Intraday Regime-Aware Watchlist Monitor",
    subtitle:
      "Real-time decision-support system for intraday trading on a focused high-beta watchlist",
    category: "Systematic Trading",
    period: "2026",
    tags: ["Regime Detection", "Ranking", "Alpaca", "Python", "Next.js"],
    summary:
      "A regime-aware monitoring and ranking system built to support personal intraday trading. The system ingests 1-minute bars from Alpaca market data for a focused universe of high-beta equities (TSLA, NVDA, PLTR, MU, HOOD, AMD) plus QQQ and SPY benchmarks, classifies the current session into bullish, bearish, or mixed regimes, and produces a scored watchlist ranking that adapts its factor weights to the prevailing market environment.",
    sections: [
      {
        title: "Market Regime Classification",
        content:
          "The regime classifier scores QQQ and SPY independently across five intraday signal dimensions: price versus session VWAP, short-to-long moving average alignment, first-15m and first-30m directional persistence, intraday momentum (DTD + last-30m trend), and opening range breakout behavior. Each signal is scored on a [-1, +1] scale and weighted into a composite. The QQQ and SPY composites are averaged to produce a final regime label with a confidence score.",
      },
      {
        title: "Watchlist Ranking Engine",
        content:
          "Each watchlist symbol is scored across eight factors: excess return versus benchmarks, RSI strength, price relative to VWAP, moving average alignment, relative volume versus 5-day intraday average, golden/death cross events, trend quality (directional consistency and monotonicity across return windows), and opening range breakout direction. Factor weights shift by regime — bullish rewards strength leaders, bearish rewards weakness for short candidates, and mixed emphasizes breakout potential and volume conviction.",
      },
      {
        title: "Feature Computation",
        content:
          "The feature pipeline computes 5/10/20/60-period moving averages, 14-period Wilder RSI, session VWAP from OHLCV, 5m/15m/30m/DTD returns with excess versus QQQ and SPY, relative volume against a 5-day time-of-day average, and opening range breakout status based on the first 30 minutes of regular trading hours. All features are computed from 1-minute bars with proper timezone handling for ET market hours.",
      },
      {
        title: "Alert Generation",
        content:
          "The system generates severity-prioritized alerts for actionable intraday events: large DTD moves (>2%), opening range breakouts (above or below), golden/death cross events, elevated relative volume (>1.3x), and extreme RSI readings (overbought >70 or oversold <30). Alerts are sorted by severity and presented alongside the ranked watchlist for rapid decision support.",
      },
      {
        title: "Architecture and Infrastructure",
        content:
          "Built as a modular Python package (monitor/watchlist/) with clean separation of ingestion, feature computation, regime classification, ranking, and persistence. Data is ingested via Alpaca Market Data REST API with credentials managed through environment variables. The dashboard is served as a Next.js page with Recharts-based mini charts showing price action, VWAP, moving averages, and ORB reference levels for each watchlist symbol.",
      },
    ],
    highlights: [
      "Regime-adaptive ranking with three distinct weight profiles",
      "Eight-factor scoring model with per-symbol explanations",
      "Real-time 1-minute bar ingestion from Alpaca Market Data",
      "Severity-prioritized alert feed for intraday event detection",
      "Interactive dashboard with per-stock VWAP/MA mini charts",
      "Clean modular Python backend with typed Next.js frontend",
    ],
    custom: true,
  },
  {
    slug: "exotic-options-research",
    code: "P2",
    title: "Exotic Options & Structured Derivatives Research",
    subtitle:
      "Monte Carlo pricing and scenario analysis for multi-asset structured products",
    category: "Derivatives Research",
    period: "2025",
    tags: [
      "Monte Carlo",
      "Structured Products",
      "Exotic Options",
      "Python",
    ],
    summary:
      "Quantitative research on pricing and risk analysis of exotic options and structured derivatives using Monte Carlo simulation. The primary case study is an Auto-Callable Reverse Convertible (worst-of) note linked to a basket of three U.S. equities (TSLA, META, NFLX), combining barrier features, autocall triggers, and worst-of payoff mechanics that require simulation-based valuation.",
    sections: [
      {
        title: "Product Structure",
        content:
          "The note is a 2-year Auto-Callable Reverse Convertible linked to TSLA, META, and NFLX. It pays a 14% p.a. coupon quarterly while outstanding. On monthly observation dates, if all underlyings are at or above their initial levels (100% trigger), the note autocalls at par plus accrued coupon. At maturity, the worst-performing underlying determines redemption: full principal if the worst-of ratio is above the 70% strike barrier, otherwise principal scales proportionally to the worst performer's terminal return.",
      },
      {
        title: "Monte Carlo Methodology",
        content:
          "Pricing employs correlated geometric Brownian motion under the risk-neutral measure, with a Cholesky-decomposed correlation matrix estimated from historical daily log-returns. The simulation handles path-dependent features: monthly autocall barrier monitoring, continuous coupon accrual, and terminal worst-of payoff evaluation. The risk-free rate is calibrated to the 2-year U.S. Treasury yield (3.54% as of issue date). Variance reduction techniques including antithetic variates are applied to improve convergence.",
      },
      {
        title: "Market Calibration",
        content:
          "Annualized volatilities are estimated from historical returns: TSLA 57.7%, META 37.9%, NFLX 43.4%. The correlation structure shows moderate cross-correlation (0.33–0.45), which is critical for worst-of pricing since lower correlations increase the probability of barrier breach. Sensitivity analysis examines how the note's fair value responds to shifts in volatility, correlation, and the risk-free rate.",
      },
      {
        title: "Risk and Scenario Analysis",
        content:
          "Scenario analysis covers three canonical outcomes: early autocall under bullish conditions (all stocks above trigger), moderate decline with principal protection (worst-of above 70%), and significant decline with principal loss (worst-of below barrier). Greek sensitivities and probability distributions of terminal payoffs are computed to characterize the risk-return profile from both the investor and issuer perspective.",
      },
    ],
    highlights: [
      "Multi-asset worst-of payoff with autocall and barrier features",
      "Correlated GBM simulation with Cholesky decomposition",
      "Calibrated to real market data (TSLA, META, NFLX)",
      "Scenario analysis across autocall, protection, and loss regimes",
      "Issuer economics: volatility and correlation premia monetization",
    ],
  },
  {
    slug: "crypto-market-intelligence",
    code: "P3",
    title: "Crypto Market Intelligence Research",
    subtitle:
      "Alternative data, NLP, and event-driven analysis for digital asset markets",
    category: "Alternative Data",
    period: "2025 – Present",
    tags: ["Crypto", "NLP", "Whale Alerts", "Sentiment", "Python"],
    summary:
      "Research and system design work at the intersection of crypto market intelligence, natural language processing, and alternative data analysis. This work was conducted in a professional capacity with CTO-level ownership of the research-to-execution pipeline, covering sentiment scoring, event detection, whale activity monitoring, and signal integration for systematic crypto trading.",
    sections: [
      {
        title: "Selected Themes",
        content:
          "Work spanned several interconnected research areas: NLP-based sentiment analysis applied to crypto-specific news and social media sources, whale alert monitoring and large-transfer event detection, price behavior research around significant on-chain and off-chain events, and systematic integration of alternative data signals into trading decision frameworks. The research emphasized practical signal construction under the noisy, 24/7 conditions of digital asset markets.",
      },
      {
        title: "Research Directions",
        content:
          "Key technical contributions included building confidence-weighted sentiment scoring pipelines using transformer-based models, developing event taxonomies for crypto-specific catalysts (exchange flows, governance proposals, regulatory announcements), and researching the decay profiles and information content of whale activity signals. The work balanced systematic rigor with the operational realities of a small, fast-moving research team.",
      },
      {
        title: "System Design",
        content:
          "Designed and maintained the end-to-end research pipeline: data ingestion from multiple alternative data providers, feature engineering and signal construction, backtesting infrastructure with realistic transaction cost assumptions, and performance monitoring dashboards for live strategy tracking. The infrastructure supported rapid iteration from research hypothesis to validated signal to deployment.",
      },
      {
        title: "Disclosure",
        content:
          "This project reflects work conducted in a professional role. Specific strategy logic, proprietary signal details, and performance metrics are not disclosed due to confidentiality obligations. The descriptions above are limited to general research themes and publicly observable capabilities.",
      },
    ],
    highlights: [
      "NLP sentiment scoring for crypto-specific text sources",
      "Whale alert and on-chain event detection pipelines",
      "Research-to-execution pipeline with CTO-level ownership",
      "Alternative data signal integration for systematic trading",
    ],
  },
  {
    slug: "financial-bubble-detection",
    code: "P4",
    title: "Financial Bubble Detection with HLPPL",
    subtitle:
      "Identifying and quantifying U.S. equity bubbles using the Hyped Log-Periodic Power Law model",
    category: "Quantitative Research",
    period: "2024 – 2025",
    tags: [
      "LPPL",
      "Behavioral Finance",
      "Transformer",
      "Monte Carlo",
      "Python",
    ],
    summary:
      "Co-first-authored research on identifying and quantifying financial bubbles in U.S. equity markets using a novel extension of the Log-Periodic Power Law (LPPL) framework. The Hyped LPPL model integrates sentiment-driven behavioral signals with the classical LPPL oscillatory crash-hazard structure, producing a dual-stream architecture for bubble detection and crash-time forecasting.",
    sections: [
      {
        title: "Research Question",
        content:
          "Classical LPPL models capture the super-exponential price growth and log-periodic oscillations that characterize speculative bubbles, but they rely solely on price dynamics and are sensitive to fitting windows. This work asks: can incorporating NLP-derived sentiment signals improve both the detection accuracy and the timing precision of bubble identification? The HLPPL framework proposes a confidence-weighted sentiment stream fused with the traditional LPPL technical stream.",
      },
      {
        title: "Methodology",
        content:
          "The model has three components. First, a 7-parameter LPPL model is fitted via multi-start constrained optimization to identify bubble regimes and estimate critical times. Second, a confidence-weighted sentiment analysis pipeline using FinBERT and BERTopic extracts behavioral signals from financial text. Third, a Dual-Stream Transformer architecture fuses the LPPL-derived features with sentiment features through a regime-dependent BubbleScore that quantifies bubble intensity. The full pipeline is implemented in Python with PyTorch, featuring YAML-driven configuration and checkpoint-based resumability.",
      },
      {
        title: "Results and Contribution",
        content:
          "The Dual-Stream Transformer achieves an MSE of 0.087 and a correlation of 0.625 on BubbleScore prediction. Trading strategies derived from the model produce 34.1% annualized returns with a Sharpe ratio of 1.13 in backtesting. The work demonstrates that sentiment-augmented bubble detection meaningfully improves upon pure price-based LPPL models in both identification precision and economic value.",
      },
      {
        title: "Publication and Presentation",
        content:
          "Published as a preprint on arXiv (2510.10878). Presented at the 21st Quantitative Finance Conference 2025 in Rome and QuantMinds International 2025 in London. Co-authored with Zheng Cao, Xingran Shao, and Helyette Geman. The full implementation is available as an open-source Python package with comprehensive documentation.",
      },
    ],
    highlights: [
      "Co-first author, supervised by Prof. Helyette Geman",
      "Novel HLPPL framework fusing LPPL with NLP sentiment",
      "Dual-Stream Transformer: MSE 0.087, correlation 0.625",
      "34.1% annualized return, Sharpe 1.13 in backtesting",
      "Presented at QFC 2025 (Rome) and QuantMinds 2025 (London)",
      "Open-source implementation (arXiv: 2510.10878)",
    ],
  },
];
