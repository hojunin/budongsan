export function distribution(values, budget) {
  const sorted = values.filter((v) => Number.isFinite(v) && v > 0).sort((a, b) => a - b);
  if (sorted.length < 5) return null;
  const quantile = (p) => { const i = (sorted.length - 1) * p, lo = Math.floor(i); return sorted[lo] + (sorted[Math.ceil(i)] - sorted[lo]) * (i - lo); };
  const below = sorted.filter((v) => v <= budget).length;
  return {n: sorted.length, q1: quantile(.25), median: quantile(.5), q3: quantile(.75), below, share: below / sorted.length};
}

export function rentCost(row, rate) {
  if (rate === '' || rate == null || row.deposit == null || row.monthly == null) return null;
  const [d, m, r] = [row.deposit, row.monthly, rate].map(Number);
  if (![d, m, r].every(Number.isFinite) || d < 0 || m < 0 || r < 0) return null;
  const cost = m + d * r / 1200;
  return Number.isFinite(cost) ? cost : null;
}

export function periodComparison(current, previous) {
  const a = distribution(current, 0), b = distribution(previous, 0);
  if (!a || !b || a.n < 30 || b.n < 30 || b.median <= 0) return null;
  const priceChange = a.median / b.median - 1;
  return Number.isFinite(priceChange) ? {current:a, previous:b, priceChange, volumeChange:a.n / b.n - 1} : null;
}

export function completedWindow(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-US', {timeZone:'Asia/Seoul', year:'numeric', month:'numeric'}).formatToParts(now);
  const year = Number(parts.find((p) => p.type === 'year').value);
  const month = Number(parts.find((p) => p.type === 'month').value);
  return {start:new Date(Date.UTC(year, month - 8, 1)), end:new Date(Date.UTC(year, month - 2, 1))};
}

export function withinSelectionLimit(values) {
  return Array.isArray(values) && values.length <= 3;
}
