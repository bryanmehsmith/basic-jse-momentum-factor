import pandas as pd

from momentum_factor.signals import momentum_signal


def test_momentum_signal_basic_growth():
    dates = pd.date_range("2020-01-01", periods=450, freq="D")
    # Ticker A grows steadily, Ticker B is flat.
    prices = pd.DataFrame(
        {
            "A": [100 * (1.001**i) for i in range(len(dates))],
            "B": [100.0] * len(dates),
        },
        index=dates,
    )

    signal = momentum_signal(prices, formation_months=12, skip_months=1)

    last_valid = signal.dropna().iloc[-1]
    assert last_valid["A"] > 0
    assert last_valid["B"] == 0


def test_momentum_signal_skip_excludes_most_recent_month():
    dates = pd.date_range("2020-01-01", periods=450, freq="D")
    prices = pd.DataFrame({"A": range(1, len(dates) + 1)}, index=dates, dtype=float)

    signal_with_skip = momentum_signal(prices, formation_months=12, skip_months=1)
    signal_no_skip = momentum_signal(prices, formation_months=12, skip_months=0)

    # Skipping the most recent month should shift which data is used,
    # producing a different score at the same evaluation date.
    common_idx = signal_with_skip.dropna().index.intersection(signal_no_skip.dropna().index)
    assert len(common_idx) > 0
    assert not signal_with_skip.loc[common_idx].equals(signal_no_skip.loc[common_idx])
