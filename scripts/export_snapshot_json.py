"""Export the bundled price snapshot as monthly JSON for the static frontend.

The frontend does its own monthly resampling client-side once it has monthly
prices, but there's no reason to ship 2900+ daily rows per ticker to the
browser when the backtest only ever looks at month-end prices. This collapses
the snapshot to month-end before writing it out.

Run whenever `refresh_snapshot.py` updates the bundled parquet snapshot:

    uv run scripts/export_snapshot_json.py
    git add frontend/js/data/prices.json
    git commit -m "Refresh frontend price snapshot"
"""

import json
from pathlib import Path

from momentum_factor.data import SNAPSHOT_PATH, load_universe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "frontend" / "js" / "data" / "prices.json"


def main() -> None:
    import pandas as pd

    universe = load_universe()
    names = dict(zip(universe["ticker"], universe["name"]))

    snapshot = pd.read_parquet(SNAPSHOT_PATH)
    monthly = snapshot.resample("ME").last()

    payload = {
        "tickers": monthly.columns.tolist(),
        "names": {ticker: names.get(ticker, ticker) for ticker in monthly.columns},
        "dates": [d.strftime("%Y-%m-%d") for d in monthly.index],
        "prices": {
            ticker: [None if pd.isna(v) else round(float(v), 4) for v in monthly[ticker]]
            for ticker in monthly.columns
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {OUTPUT_PATH} ({len(payload['dates'])} months, {len(payload['tickers'])} tickers)")


if __name__ == "__main__":
    main()
