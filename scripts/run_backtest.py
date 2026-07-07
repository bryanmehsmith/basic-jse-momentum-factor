"""End-to-end JSE momentum factor backtest: data -> signal -> backtest -> performance."""

import matplotlib.pyplot as plt

from momentum_factor.backtest import run_backtest
from momentum_factor.data import get_prices, load_universe
from momentum_factor.performance import summarize
from momentum_factor.signals import momentum_signal

START_DATE = "2015-01-01"
QUANTILES = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6]
SELECTION_METRIC = "sharpe_ratio"  # key into performance.summarize() used to pick the best quantile


def main() -> None:
    universe = load_universe()
    tickers = universe["ticker"].tolist()

    prices = get_prices(tickers, start=START_DATE)
    signal = momentum_signal(prices)

    print("Momentum factor backtest - JSE universe")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Sweeping quantiles: {QUANTILES}\n")

    results = []
    for quantile in QUANTILES:
        returns = run_backtest(prices, signal, quantile=quantile)
        stats = summarize(returns)
        results.append((quantile, returns, stats))

        print(f"quantile={quantile}")
        print(f"  periods: {len(returns)}")
        for key, value in stats.items():
            print(f"  {key}: {value:.4f}")

    best_quantile, best_returns, best_stats = max(
        results, key=lambda result: result[2][SELECTION_METRIC]
    )

    print(f"\nBest quantile by {SELECTION_METRIC}: {best_quantile}")
    for key, value in best_stats.items():
        print(f"  {key}: {value:.4f}")

    cumulative = (1 + best_returns).cumprod()
    cumulative.plot(title=f"Momentum Portfolio - Cumulative Growth (quantile={best_quantile})")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
