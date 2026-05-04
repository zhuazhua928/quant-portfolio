# Energy Trading Dashboard — Henry Hub

Pipeline that exports JSON dashboards for the `energy-trading-dashboard`
page on the portfolio site.

## Data sources

- **yfinance** — `NG=F` (NYMEX Henry Hub front-month) daily close history
  and dated forward contracts (e.g. `NGM26.NYM`) for the forward curve.
- **EIA API v2** — Henry Hub spot price (series `NG.RNGWHHD.D`) and
  Lower-48 weekly working gas in storage (`NG.NW2_EPG0_SWO_R48_BCF.W`).
  Free key required: register at <https://www.eia.gov/opendata/register.php>
  and add `EIA_API_KEY=...` to `.env`. The pipeline degrades gracefully
  if the key is missing — storage panels show "EIA key not configured".

## Usage

```bash
python -m energy.pipeline.run
```

Writes four files under `src/data/energy/`:

- `summary.json` — current price, day Δ, 30-day vol, curve summary, latest storage
- `prices.json` — daily NG=F closes + log returns + rolling vol (last ~5 yr)
- `curve.json` — current forward curve, calendar spreads, H-J widow-maker series
- `storage.json` — weekly storage history + 5-year envelope

## Analytics

- **Realized vol** — annualized standard deviation of log returns over 10/30-day windows
- **Calendar spreads** — `H-J` (Mar-Apr widow-maker), `V-H` (Oct-Mar winter strip), summer-winter diff
- **Contango score** — sign and magnitude of `M2 - M1`
- **Storage envelope** — same-week 5-year (min, p25, mean, p75, max)
- **Storage z-score** — `(current - 5yr_mean) / 5yr_std` for the same week-of-year
