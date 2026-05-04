"""Intraday Trend Detection & Regime Monitoring research package.

Two-stage ML pipeline for high-beta US equities:
- Stage 1: regime classification (Gaussian HMM, HDBSCAN)
- Stage 2: conditional 5-30 min directional forecast (LightGBM)

Data via Alpaca Markets (IEX free feed). See research/README.md.
"""
