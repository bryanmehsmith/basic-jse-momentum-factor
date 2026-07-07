import pandas as pd

from momentum_factor.backtest import run_backtest


def test_run_backtest_picks_top_quantile():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")

    # Monthly prices: A doubles each month, B stays flat, C halves each month.
    daily_dates = pd.date_range("2020-01-01", "2020-05-31", freq="D")
    prices = pd.DataFrame(index=daily_dates)
    prices["A"] = [2 ** (i / 30) for i in range(len(daily_dates))]
    prices["B"] = 1.0
    prices["C"] = [0.5 ** (i / 30) for i in range(len(daily_dates))]

    # Signal strongly favors A at every rebalance date.
    signal = pd.DataFrame(
        {"A": [3, 3, 3, 3], "B": [2, 2, 2, 2], "C": [1, 1, 1, 1]},
        index=dates,
    )

    returns = run_backtest(prices, signal, quantile=0.34)  # top 1 of 3

    assert not returns.empty
    # Top-quantile-only portfolio (holding A) should have positive returns
    # since A's price is strictly increasing.
    assert (returns > 0).all()


def test_run_backtest_handles_empty_signal_row():
    dates = pd.date_range("2020-01-31", periods=2, freq="ME")
    daily_dates = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    prices = pd.DataFrame({"A": 1.0}, index=daily_dates)

    signal = pd.DataFrame({"A": [float("nan"), 1.0]}, index=dates)

    returns = run_backtest(prices, signal, quantile=1.0)

    assert len(returns) <= 1
