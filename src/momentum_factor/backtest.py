"""Lightweight vectorized quantile-portfolio backtester."""

import pandas as pd


def run_backtest(
    prices: pd.DataFrame,
    signal: pd.DataFrame,
    quantile: float = 0.2,
) -> pd.Series:
    """Long-only top-quantile momentum backtest.

    At each rebalance date (rows of `signal`), rank tickers by signal score,
    equal-weight the top `quantile` fraction, and hold to the next rebalance
    date. Returns a monthly portfolio return series.
    """
    monthly_prices = prices.resample("ME").last()
    forward_returns = monthly_prices.pct_change().shift(-1)

    portfolio_returns = {}
    for date in signal.index:
        scores = signal.loc[date].dropna()
        if scores.empty:
            continue
        n_holdings = max(1, int(len(scores) * quantile))
        holdings = scores.sort_values(ascending=False).index[:n_holdings]

        if date not in forward_returns.index:
            continue
        period_returns = forward_returns.loc[date, holdings].dropna()
        if period_returns.empty:
            continue
        portfolio_returns[date] = period_returns.mean()

    return pd.Series(portfolio_returns).sort_index()
