"""Momentum signal calculation."""

import pandas as pd


def momentum_signal(
    prices: pd.DataFrame,
    formation_months: int = 12,
    skip_months: int = 1,
) -> pd.DataFrame:
    """Classic 12-1 momentum: cumulative return over `formation_months`,
    skipping the most recent `skip_months` to avoid short-term reversal.

    `prices` must be daily adjusted close, indexed by date, one column per ticker.
    Returns a DataFrame of monthly momentum scores, indexed by month-end date.
    """
    monthly = prices.resample("ME").last()
    lookback = monthly.shift(skip_months)
    formation_start = monthly.shift(skip_months + formation_months)
    return lookback / formation_start - 1
