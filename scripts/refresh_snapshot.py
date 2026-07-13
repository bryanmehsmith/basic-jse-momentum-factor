"""Refresh the bundled price snapshot used as a fallback when live yfinance
data is unavailable (rate-limited, network issues, etc.) in the deployed demo.

Run manually and locally, then commit the updated snapshot:

    uv run scripts/refresh_snapshot.py
    git add assets/prices_snapshot.parquet
    git commit -m "Refresh bundled price snapshot"
"""

from momentum_factor.data import SNAPSHOT_PATH, get_prices, load_universe

START_DATE = "2015-01-01"


def main() -> None:
    universe = load_universe()
    tickers = universe["ticker"].tolist()

    prices = get_prices(tickers, start=START_DATE, force_refresh=True)

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(SNAPSHOT_PATH)
    print(f"Wrote snapshot: {SNAPSHOT_PATH} ({prices.shape[0]} rows, {prices.shape[1]} tickers)")


if __name__ == "__main__":
    main()
