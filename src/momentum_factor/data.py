"""Price data loading: JSE universe from CSV, yfinance download, parquet cache."""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNIVERSE_PATH = PROJECT_ROOT / "config" / "universe.csv"
CACHE_PATH = PROJECT_ROOT / "data" / "prices.parquet"
CACHE_MAX_AGE = timedelta(days=1)


def load_universe(path: Path = UNIVERSE_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def _is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < CACHE_MAX_AGE


def get_prices(
    tickers: list[str],
    start: str,
    end: str | None = None,
    cache_path: Path = CACHE_PATH,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Adjusted close prices for `tickers`, indexed by date, one column per ticker.

    Cached to `cache_path` and reused if the cache is fresh, to avoid
    re-hitting yfinance on every run.
    """
    if not force_refresh and _is_cache_fresh(cache_path):
        return pd.read_parquet(cache_path)

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(tickers[0])

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(cache_path)
    return prices
