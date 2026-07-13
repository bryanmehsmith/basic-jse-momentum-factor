"""Price data loading: JSE universe from CSV, yfinance download, parquet cache."""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNIVERSE_PATH = PROJECT_ROOT / "config" / "universe.csv"
CACHE_PATH = PROJECT_ROOT / "data" / "prices.parquet"
SNAPSHOT_PATH = PROJECT_ROOT / "assets" / "prices_snapshot.parquet"
CACHE_MAX_AGE = timedelta(days=1)


def load_universe(path: Path = UNIVERSE_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def _is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < CACHE_MAX_AGE


def _download(tickers: list[str], start: str, end: str | None) -> pd.DataFrame:
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(tickers[0])
    if prices.empty or prices.isna().all(axis=None):
        raise ValueError("yfinance returned no usable price data")
    return prices


def _from_snapshot(
    tickers: list[str],
    start: str,
    end: str | None,
    snapshot_path: Path,
) -> pd.DataFrame:
    snapshot = pd.read_parquet(snapshot_path)
    available = [ticker for ticker in tickers if ticker in snapshot.columns]
    prices = snapshot.loc[start:end, available]
    if prices.empty:
        raise ValueError("bundled price snapshot has no data for the requested range")
    return prices


def get_prices(
    tickers: list[str],
    start: str,
    end: str | None = None,
    cache_path: Path = CACHE_PATH,
    snapshot_path: Path = SNAPSHOT_PATH,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Adjusted close prices for `tickers`, indexed by date, one column per ticker.

    Cached to `cache_path` and reused if the cache is fresh, to avoid
    re-hitting yfinance on every run. If a live download is required and
    fails (network issues, yfinance rate-limiting, etc.), falls back to the
    on-disk cache even if stale, then to the bundled `snapshot_path` snapshot,
    so a public demo degrades instead of crashing.
    """
    if not force_refresh and _is_cache_fresh(cache_path):
        return pd.read_parquet(cache_path)

    try:
        prices = _download(tickers, start, end)
    except Exception:
        if cache_path.exists():
            return pd.read_parquet(cache_path)
        if snapshot_path.exists():
            return _from_snapshot(tickers, start, end, snapshot_path)
        raise

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(cache_path)
    return prices
