"""Performance metrics for a backtested return series."""

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 12


def cumulative_return(returns: pd.Series) -> float:
    return (1 + returns).prod() - 1


def annualized_return(returns: pd.Series) -> float:
    n_periods = len(returns)
    if n_periods == 0:
        return float("nan")
    total_growth = (1 + returns).prod()
    return total_growth ** (PERIODS_PER_YEAR / n_periods) - 1


def annualized_volatility(returns: pd.Series) -> float:
    return returns.std() * np.sqrt(PERIODS_PER_YEAR)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    excess = returns - risk_free_rate / PERIODS_PER_YEAR
    vol = excess.std()
    if vol == 0 or np.isnan(vol):
        return float("nan")
    return (excess.mean() / vol) * np.sqrt(PERIODS_PER_YEAR)


def max_drawdown(returns: pd.Series) -> float:
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    return drawdown.min()


def summarize(returns: pd.Series) -> dict:
    return {
        "cumulative_return": cumulative_return(returns),
        "annualized_return": annualized_return(returns),
        "annualized_volatility": annualized_volatility(returns),
        "sharpe_ratio": sharpe_ratio(returns),
        "max_drawdown": max_drawdown(returns),
    }
