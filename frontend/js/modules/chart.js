import { formatMonthLabel } from "../utils/format.js";

const LINE_COLOR = { light: "#7a4f22", dark: "#d0a46a" };
const BASELINE_COLOR = { light: "#a89f92", dark: "#6b6459" };

// "Nice" round numbers for a linear axis (1, 2, 2.5, 5, 10 x 10^n), same
// spirit as the log-tick helper in the security-anti-patterns chart, just
// linear since growth-of-1 doesn't span orders of magnitude the way crack
// times do.
function niceLinearTicks(minValue, maxValue, targetCount = 5) {
  const range = maxValue - minValue || 1;
  const roughStep = range / targetCount;
  const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
  const normalized = roughStep / magnitude;
  const niceNormalized = normalized < 1.5 ? 1 : normalized < 3 ? 2 : normalized < 7 ? 5 : 10;
  const step = niceNormalized * magnitude;

  const start = Math.floor(minValue / step) * step;
  const end = Math.ceil(maxValue / step) * step;
  const ticks = [];
  for (let v = start; v <= end + step / 2; v += step) ticks.push(Math.round(v * 1000) / 1000);
  return ticks;
}

function selectDateTicks(dates, maxTicks = 8) {
  if (dates.length <= maxTicks) return dates.map((_, i) => i);
  const step = (dates.length - 1) / (maxTicks - 1);
  const indices = new Set();
  for (let i = 0; i < maxTicks; i++) indices.add(Math.round(i * step));
  return [...indices].sort((a, b) => a - b);
}

export function renderGrowthChart(container, { dates, growth, isDark, title }) {
  const width = 720;
  const height = 320;
  const padding = { top: 16, right: 20, bottom: 34, left: 52 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const lineColor = isDark ? LINE_COLOR.dark : LINE_COLOR.light;
  const baselineColor = isDark ? BASELINE_COLOR.dark : BASELINE_COLOR.light;

  const minValue = Math.min(1, ...growth);
  const maxValue = Math.max(1, ...growth);
  const ticks = niceLinearTicks(minValue, maxValue);
  const loTick = ticks[0];
  const hiTick = ticks[ticks.length - 1];

  const n = dates.length;
  const xFor = (i) => padding.left + (n <= 1 ? 0 : (i / (n - 1)) * plotWidth);
  const yFor = (v) => padding.top + plotHeight - ((v - loTick) / (hiTick - loTick || 1)) * plotHeight;

  const gridlines = ticks
    .map((tick) => {
      const y = yFor(tick);
      return `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" class="viz-grid" />
        <text x="${padding.left - 6}" y="${y + 3}" text-anchor="end" class="viz-tick">${tick.toFixed(1)}x</text>`;
    })
    .join("");

  const baselineY = yFor(1);
  const baseline = `<line x1="${padding.left}" y1="${baselineY}" x2="${width - padding.right}" y2="${baselineY}" class="viz-baseline" />`;

  const dateTickIndices = selectDateTicks(dates);
  const dateTicks = dateTickIndices
    .map((i) => `<text x="${xFor(i)}" y="${height - 4}" text-anchor="middle" class="viz-tick">${formatMonthLabel(dates[i])}</text>`)
    .join("");

  const path = growth.map((v, i) => `${i === 0 ? "M" : "L"}${xFor(i)},${yFor(v)}`).join(" ");

  const lastX = xFor(n - 1);
  const lastY = yFor(growth[n - 1]);
  const endDot = `<circle cx="${lastX}" cy="${lastY}" r="4" fill="${lineColor}" stroke="var(--viz-surface)" stroke-width="2" />`;

  container.innerHTML = `
    <div class="viz-root">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${title ?? "Cumulative growth of 1 unit invested"}">
        ${gridlines}
        ${baseline}
        <path d="${path}" fill="none" stroke="${lineColor}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
        ${endDot}
        ${dateTicks}
      </svg>
    </div>`;
}

function ensureChartStyles() {
  if (document.getElementById("momentum-chart-styles")) return;
  const style = document.createElement("style");
  style.id = "momentum-chart-styles";
  style.textContent = `
    .viz-root { --viz-surface: var(--card-background); color-scheme: light dark; }
    .viz-grid { stroke: var(--border-color); stroke-width: 1; }
    .viz-baseline { stroke: var(--muted-text); stroke-width: 1; stroke-dasharray: 4 3; opacity: 0.6; }
    .viz-tick { font-size: 10px; fill: var(--muted-text); font-family: inherit; }
  `;
  document.head.appendChild(style);
}

ensureChartStyles();
