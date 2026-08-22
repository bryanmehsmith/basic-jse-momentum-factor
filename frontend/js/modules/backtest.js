// Direct JS port of the Python reference implementation:
//   src/momentum_factor/signals.py    -> momentumSignal()
//   src/momentum_factor/backtest.py   -> runBacktest()
//   src/momentum_factor/performance.py -> summarize()
// Operates on already-monthly price series (both the bundled snapshot and the
// live-refresh API return month-end prices), so unlike the Python version
// there's no daily->monthly resample step here.

const PERIODS_PER_YEAR = 12;

// Classic 12-1 momentum score at month index i: cumulative return from
// (i - skip - formation) to (i - skip), skipping the most recent `skip`
// months to avoid short-term reversal. Mirrors signals.py's
// `lookback / formation_start - 1` (pandas shift semantics: shift(n)[i] ==
// original[i - n]).
function momentumScoreAt(series, i, formationMonths, skipMonths) {
  const lookbackIdx = i - skipMonths;
  const formationIdx = i - skipMonths - formationMonths;
  if (lookbackIdx < 0 || formationIdx < 0) return null;
  const lookback = series[lookbackIdx];
  const formationStart = series[formationIdx];
  if (lookback == null || formationStart == null || formationStart === 0) return null;
  return lookback / formationStart - 1;
}

// prices: { dates: string[], prices: { [ticker]: (number|null)[] } }
// Returns { dates, scores: { [ticker]: (number|null)[] } } aligned to the same dates.
export function momentumSignal(prices, { formationMonths, skipMonths }) {
  const tickers = Object.keys(prices.prices);
  const scores = {};
  for (const ticker of tickers) {
    const series = prices.prices[ticker];
    scores[ticker] = series.map((_, i) => momentumScoreAt(series, i, formationMonths, skipMonths));
  }
  return { dates: prices.dates, scores };
}

// Long-only top-quantile momentum backtest: at each month, rank tickers by
// score, equal-weight the top `quantile` fraction, hold to the next month.
// Mirrors backtest.py's run_backtest().
export function runBacktest(prices, signal, quantile) {
  const tickers = Object.keys(prices.prices);
  const dates = prices.dates;
  const n = dates.length;

  // Forward return for month i: return earned from month i to month i+1,
  // i.e. pandas' `pct_change().shift(-1)`.
  const forwardReturns = {};
  for (const ticker of tickers) {
    const series = prices.prices[ticker];
    forwardReturns[ticker] = series.map((price, i) => {
      if (i + 1 >= n) return null;
      const next = series[i + 1];
      if (price == null || next == null || price === 0) return null;
      return next / price - 1;
    });
  }

  const returnDates = [];
  const returns = [];
  for (let i = 0; i < n; i++) {
    const ranked = tickers
      .map((ticker) => ({ ticker, score: signal.scores[ticker][i] }))
      .filter((entry) => entry.score != null)
      .sort((a, b) => b.score - a.score);

    if (ranked.length === 0) continue;

    const nHoldings = Math.max(1, Math.floor(ranked.length * quantile));
    const holdings = ranked.slice(0, nHoldings).map((entry) => entry.ticker);

    const periodReturns = holdings
      .map((ticker) => forwardReturns[ticker][i])
      .filter((r) => r != null);

    if (periodReturns.length === 0) continue;

    const mean = periodReturns.reduce((sum, r) => sum + r, 0) / periodReturns.length;
    returnDates.push(dates[i]);
    returns.push(mean);
  }

  return { dates: returnDates, returns };
}

function mean(values) {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

// Sample standard deviation (ddof=1), matching pandas' default .std().
function sampleStd(values) {
  if (values.length < 2) return NaN;
  const m = mean(values);
  const variance = values.reduce((sum, v) => sum + (v - m) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

// Mirrors performance.py's summarize(). `riskFreeRate` is an annual rate,
// e.g. 0.04 for 4%.
export function summarize(returns, riskFreeRate = 0) {
  const n = returns.length;
  if (n === 0) {
    return {
      cumulativeReturn: NaN,
      annualizedReturn: NaN,
      annualizedVolatility: NaN,
      sharpeRatio: NaN,
      maxDrawdown: NaN,
    };
  }

  const growth = returns.reduce((product, r) => product * (1 + r), 1);
  const cumulativeReturn = growth - 1;
  const annualizedReturn = Math.pow(growth, PERIODS_PER_YEAR / n) - 1;
  const annualizedVolatility = sampleStd(returns) * Math.sqrt(PERIODS_PER_YEAR);

  const monthlyRiskFree = riskFreeRate / PERIODS_PER_YEAR;
  const excess = returns.map((r) => r - monthlyRiskFree);
  const excessStd = sampleStd(excess);
  const sharpeRatio =
    excessStd === 0 || Number.isNaN(excessStd) ? NaN : (mean(excess) / excessStd) * Math.sqrt(PERIODS_PER_YEAR);

  let cumulative = 1;
  let runningMax = 1;
  let maxDrawdown = 0;
  for (const r of returns) {
    cumulative *= 1 + r;
    runningMax = Math.max(runningMax, cumulative);
    maxDrawdown = Math.min(maxDrawdown, cumulative / runningMax - 1);
  }

  return { cumulativeReturn, annualizedReturn, annualizedVolatility, sharpeRatio, maxDrawdown };
}

// Growth-of-1 series aligned to `returns.dates`, for the chart.
export function cumulativeGrowth(returns) {
  let growth = 1;
  return returns.returns.map((r) => {
    growth *= 1 + r;
    return growth;
  });
}
