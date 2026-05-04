"""Henry Hub natural gas dashboard pipeline.

Pulls price + futures curve data from yfinance and storage/spot data from
the EIA API, computes a small set of canonical analytics (calendar
spreads, 5-year storage envelope, realized vol), and exports JSON
artifacts that drive the energy-trading-dashboard page on the website.
"""
