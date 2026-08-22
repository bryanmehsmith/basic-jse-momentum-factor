# Momentum Factor

Momentum factor research and backtesting on the JSE (Johannesburg Stock Exchange), using `yfinance` for price data.

## How the momentum factor works

Momentum is the observation that stocks which have performed well recently tend to keep performing well over the following months, and stocks which have performed poorly tend to keep lagging. It's one of the most persistent, widely documented factors in equity markets (Jegadeesh & Titman, 1993), and shows up across most markets and time periods, including the JSE.

**Why it (allegedly) works**: the standard explanations are behavioral rather than risk-based:
- **Underreaction**: investors are slow to fully price in new information (earnings surprises, changing fundamentals), so prices drift toward fair value over months rather than adjusting instantly.
- **Herding / trend-following**: as a stock's price move becomes visible, more investors pile in, reinforcing the trend for a while.
- **Disposition effect**: investors are quick to sell winners and slow to sell losers, which can suppress a stock's price reaction and let momentum persist longer.

These effects fade and eventually reverse over longer horizons (multi-year), which is why momentum strategies define a specific formation window rather than just "the stock has always gone up."

**The classic signal - "12-1" momentum:**
1. Look back over a **formation period**, typically the trailing 12 months.
2. **Skip the most recent month.** Returns in the last month tend to *reverse* (short-term reversal), so including it would work against the momentum effect. This is why the signal in [`signals.py`](src/momentum_factor/signals.py) computes the return from 13 months ago to 1 month ago, not 12 months ago to today.
3. Rank all stocks in the universe by that 12-1 return.

**Turning the signal into a portfolio:**
- Split the ranked universe into buckets, e.g. quintiles or deciles.
- A classic momentum strategy goes **long the top bucket (winners) and short the bottom bucket (losers)**; a "long-short" or "winners-minus-losers" (WML) portfolio, which is roughly market-neutral.
- Since shorting is impractical for most JSE participants, this project runs a **long-only top-quantile** portfolio instead ([`backtest.py`](src/momentum_factor/backtest.py)): equal-weight the top-ranked names, rebalance monthly, hold until the next rebalance.
- **Rebalancing and turnover matter**: monthly rebalancing keeps the portfolio aligned with the current ranking, but each rebalance incurs (unmodeled, in this simple backtester) transaction costs, so turnover is worth tracking, not just returns.

**Risks to know going in:**
- Momentum is prone to sharp, sudden **crashes**; e.g. in a market rebound after a crash, yesterday's beaten-down "losers" can rally hardest, hurting a long-winners/short-losers position badly.
- It has meaningfully higher volatility and drawdowns than a simple market-cap-weighted benchmark, as reflected in the `max_drawdown` metric this project reports.
- On a small universe like the JSE (fewer liquid names than the S&P 500), quantile buckets are coarser and results are more sensitive to individual stock idiosyncrasies; a reason the stub `config/universe.csv` should be expanded before drawing real conclusions.

## Setup

```bash
uv sync
```

## Usage

Run the end-to-end backtest (data download → momentum signal → quantile backtest → performance report):

```bash
uv run scripts/run_backtest.py
```

Run tests:

```bash
uv run pytest
```

The interactive version of this is a static JS frontend (`frontend/`), not a
Streamlit app: it ports the signal/backtest/performance math from
`src/momentum_factor/` directly into JS and runs client-side against a bundled
monthly price snapshot. Open `frontend/index.html` through any static file
server, e.g.:

```bash
cd frontend && python -m http.server
```

`app/api.py` is a small companion JSON API, used only by that frontend's "try
live yfinance refresh" toggle:

```bash
uv run python app/api.py --port=8000
# GET http://127.0.0.1:8000/prices?tickers=NPN.JO,MTN.JO&start=2015-01-01
```

Regenerate the bundled frontend snapshot after `refresh_snapshot.py` updates
the parquet snapshot:

```bash
uv run scripts/export_snapshot_json.py
```

## Universe

`config/universe.csv` holds the JSE ticker universe (`ticker,name`), using yfinance's `.JO` suffix convention (e.g. `NPN.JO`). It currently contains a handful of large-cap placeholders; maintain this list by hand to expand or refine the universe.

## Project layout

- `src/momentum_factor/data.py` - loads the universe and downloads/caches adjusted close prices
- `src/momentum_factor/signals.py` - momentum signal calculation (formation window with a skip period)
- `src/momentum_factor/backtest.py` - quantile portfolio construction and vectorized backtest
- `src/momentum_factor/performance.py` - return/risk metrics (Sharpe, drawdown, etc.)
- `scripts/run_backtest.py` - CLI entrypoint wiring the pipeline together
- `scripts/export_snapshot_json.py` - exports the bundled snapshot as monthly JSON for the frontend
- `app/api.py` - tiny JSON API backing the frontend's live-refresh toggle, wraps `data.py`'s fallback chain
- `frontend/` - the static JS demo: `signals.py`/`backtest.py`/`performance.py` ported to `frontend/js/modules/backtest.js`
- `data/` - gitignored cache of downloaded price data

## Scope

Personal project using public data only; not affiliated with or representative of my employer.
