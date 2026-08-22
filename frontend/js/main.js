import { wireDisclosureControls } from "./utils/disclosure.js";
import { bindSliderOutput } from "./utils/sliderOutput.js";
import { formatPercent, formatRatio, formatMonthLabel } from "./utils/format.js";
import { momentumSignal, runBacktest, summarize, cumulativeGrowth } from "./modules/backtest.js";
import { renderGrowthChart } from "./modules/chart.js";

const LIVE_REFRESH_START = "2015-01-01";
const API_PATH = "/demos/momentum-factor/api/prices";

wireDisclosureControls(document.body);

renderMathInElement(document.querySelector("main"), {
  delimiters: [
    { left: "\\[", right: "\\]", display: true },
    { left: "\\(", right: "\\)", display: false },
  ],
});

const quantileSlider = document.getElementById("quantile-slider");
const quantileOutput = document.getElementById("quantile-output");
const formationSlider = document.getElementById("formation-slider");
const formationOutput = document.getElementById("formation-output");
const skipSlider = document.getElementById("skip-slider");
const skipOutput = document.getElementById("skip-output");
const riskfreeSlider = document.getElementById("riskfree-slider");
const riskfreeOutput = document.getElementById("riskfree-output");
const startSlider = document.getElementById("start-slider");
const startOutput = document.getElementById("start-output");
const universeGrid = document.getElementById("universe-grid");
const liveRefreshToggle = document.getElementById("live-refresh");
const liveStatus = document.getElementById("live-status");
const emptyWarning = document.getElementById("empty-warning");
const metricsRow = document.getElementById("metrics");
const chartWrap = document.getElementById("growth-chart");

let baseData = null;
let liveData = null;

function activeData() {
  return liveData ?? baseData;
}

function selectedTickers() {
  return [...universeGrid.querySelectorAll("input[type=checkbox]")]
    .filter((box) => box.checked)
    .map((box) => box.dataset.ticker);
}

function buildUniverseGrid(data) {
  universeGrid.innerHTML = "";
  for (const ticker of data.tickers) {
    const label = document.createElement("label");
    label.className = "universe-item";
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = true;
    box.dataset.ticker = ticker;
    box.addEventListener("change", recompute);
    label.appendChild(box);
    label.append(` ${ticker}`);
    label.title = data.names[ticker] ?? ticker;
    universeGrid.appendChild(label);
  }
}

function syncStartSlider(data) {
  const maxIndex = Math.max(0, data.dates.length - 1);
  startSlider.max = String(maxIndex);
  if (Number(startSlider.value) > maxIndex) startSlider.value = String(maxIndex);
  startOutput.textContent = formatMonthLabel(data.dates[Number(startSlider.value)]);
}

function sliceData(data, tickers, startIdx) {
  return {
    dates: data.dates.slice(startIdx),
    prices: Object.fromEntries(tickers.map((ticker) => [ticker, data.prices[ticker].slice(startIdx)])),
  };
}

function isDarkMode() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function recompute() {
  const data = activeData();
  if (!data) return;

  const tickers = selectedTickers();
  const startIdx = Number(startSlider.value);
  startOutput.textContent = formatMonthLabel(data.dates[Math.min(startIdx, data.dates.length - 1)] ?? "");

  const quantile = Number(quantileSlider.value);
  const formationMonths = Number(formationSlider.value);
  const skipMonths = Number(skipSlider.value);
  const riskFreeRate = Number(riskfreeSlider.value) / 100;

  if (tickers.length === 0) {
    emptyWarning.style.display = "block";
    metricsRow.style.display = "none";
    chartWrap.innerHTML = "";
    return;
  }

  const sliced = sliceData(data, tickers, startIdx);
  const signal = momentumSignal(sliced, { formationMonths, skipMonths });
  const returns = runBacktest(sliced, signal, quantile);

  if (returns.dates.length === 0) {
    emptyWarning.style.display = "block";
    metricsRow.style.display = "none";
    chartWrap.innerHTML = "";
    return;
  }

  emptyWarning.style.display = "none";
  metricsRow.style.display = "flex";

  const stats = summarize(returns.returns, riskFreeRate);
  document.getElementById("metric-sharpe").textContent = formatRatio(stats.sharpeRatio);
  document.getElementById("metric-annualized").textContent = formatPercent(stats.annualizedReturn);
  document.getElementById("metric-drawdown").textContent = formatPercent(stats.maxDrawdown);
  document.getElementById("metric-cumulative").textContent = formatPercent(stats.cumulativeReturn);

  const growth = cumulativeGrowth(returns);
  renderGrowthChart(chartWrap, {
    dates: returns.dates,
    growth,
    isDark: isDarkMode(),
    title: `Cumulative growth (quantile=${quantile}, formation=${formationMonths}m, skip=${skipMonths}m)`,
  });
}

async function fetchLiveData() {
  const tickers = baseData.tickers.join(",");
  const url = `${API_PATH}?tickers=${encodeURIComponent(tickers)}&start=${LIVE_REFRESH_START}`;
  const response = await fetch(url);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `HTTP ${response.status}`);
  return body;
}

liveRefreshToggle.addEventListener("change", async () => {
  if (!liveRefreshToggle.checked) {
    liveData = null;
    liveStatus.textContent = "";
    syncStartSlider(activeData());
    recompute();
    return;
  }

  liveRefreshToggle.disabled = true;
  liveStatus.textContent = "Fetching live prices for the whole universe, this can take a while...";
  try {
    const body = await fetchLiveData();
    liveData = { tickers: baseData.tickers, names: baseData.names, dates: body.dates, prices: body.prices };
    liveStatus.textContent = `Live data loaded, through ${formatMonthLabel(body.dates[body.dates.length - 1])}.`;
    syncStartSlider(activeData());
    recompute();
  } catch (err) {
    liveStatus.textContent = `Live refresh failed (${err.message}); showing the bundled snapshot instead.`;
    liveRefreshToggle.checked = false;
    liveData = null;
  } finally {
    liveRefreshToggle.disabled = false;
  }
});

document.getElementById("universe-select-all").addEventListener("click", () => {
  universeGrid.querySelectorAll("input[type=checkbox]").forEach((box) => { box.checked = true; });
  recompute();
});
document.getElementById("universe-select-none").addEventListener("click", () => {
  universeGrid.querySelectorAll("input[type=checkbox]").forEach((box) => { box.checked = false; });
  recompute();
});

bindSliderOutput(quantileSlider, quantileOutput, { format: (v) => `${Math.round(Number(v) * 100)}%`, onChange: recompute });
bindSliderOutput(formationSlider, formationOutput, { onChange: recompute });
bindSliderOutput(skipSlider, skipOutput, { onChange: recompute });
bindSliderOutput(riskfreeSlider, riskfreeOutput, { format: (v) => `${Number(v).toFixed(2)}%`, onChange: recompute });
startSlider.addEventListener("input", recompute);

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", recompute);

fetch("js/data/prices.json")
  .then((response) => response.json())
  .then((data) => {
    baseData = data;
    buildUniverseGrid(data);
    syncStartSlider(data);
    recompute();
  })
  .catch(() => {
    liveStatus.textContent = "Could not load the bundled price snapshot.";
  });
