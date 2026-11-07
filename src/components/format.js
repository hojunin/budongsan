// Presentation only: calculations, chart series and table sorting keep their raw values.
const formatters = [0, 1, 2].map((maximumFractionDigits) => new Intl.NumberFormat("ko-KR", {maximumFractionDigits}));

export function num(value, digits = 2) {
  if (value == null || typeof value === "string" && value.trim() === "") return "–";
  const number = typeof value === "bigint" ? value : Number(value);
  if (typeof number !== "bigint" && !Number.isFinite(number)) return "–";
  const precision = Number.isInteger(digits) ? Math.max(0, Math.min(2, digits)) : 2;
  const result = formatters[precision].format(number);
  return result === "-0" ? "0" : result;
}

export function won(manwon) {
  if (num(manwon) === "–") return "–";
  const value = Number(manwon);
  return Math.abs(value) >= 10000 ? `${num(value / 10000)}억` : `${num(value)}만`;
}

export function pct(value, digits = 2) {
  if (num(value) === "–") return "–";
  return `${num(Number(value) * 100, digits)}%`;
}

export function signed(value, digits = 2) {
  const result = pct(value, digits);
  return result === "–" ? result : `${Number(value) > 0 && result !== "0%" ? "+" : ""}${result}`;
}
