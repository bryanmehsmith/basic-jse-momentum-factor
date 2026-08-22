export function formatPercent(value, decimals = 1) {
  if (value == null || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatRatio(value, decimals = 2) {
  if (value == null || Number.isNaN(value)) return "-";
  return value.toFixed(decimals);
}

export function formatMonthLabel(dateStr) {
  const [year, month] = dateStr.split("-");
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${names[Number(month) - 1]} ${year}`;
}
