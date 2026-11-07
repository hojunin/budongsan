// 공용 UI·쿼리 도우미. 페이지에서 import 해서 쓴다.
import {html} from "npm:htl";

// ---------- 포맷 ----------
export const won = (manwon) => {
  if (manwon == null || isNaN(manwon)) return "–";
  const eok = manwon / 10000;
  return eok >= 1 ? `${eok.toFixed(eok >= 10 ? 1 : 2).replace(/\.?0+$/, "")}억` : `${Math.round(manwon).toLocaleString("ko-KR")}만`;
};
export const pct = (x, digits = 1) => (x == null || isNaN(x) ? "–" : `${(x * 100).toFixed(digits)}%`);
export const signed = (x, digits = 1) => (x == null || isNaN(x) ? "–" : `${x > 0 ? "+" : ""}${(x * 100).toFixed(digits)}%`);
export const num = (x) => (x == null || isNaN(x) ? "–" : Math.round(x).toLocaleString("ko-KR"));

// ---------- 색 (라이트/다크 모두 대비 확인한 값; style.css 토큰과 맞춤) ----------
export const COLOR = {
  accent: "var(--accent)",
  accent2: "var(--accent-2)",
  muted: "var(--theme-foreground-faint)",
  good: "var(--good)",
  warn: "var(--warn)"
};
export const PALETTE = ["#c8553d", "#2a6f97", "#6a994e", "#bc6c25", "#7b5ea7", "#2d8a8a"];
export const BANDS = ["~49", "59", "74", "84", "100", "115+"];
export const BAND_LABEL = {"~49": "~49㎡", "59": "59㎡대", "74": "74㎡대", "84": "84㎡대", "100": "100㎡대", "115+": "115㎡+"};

// ---------- 지역 선택지 ----------
// 서울 전체 / 경기 전체 / 경기 시(구 묶음) / 각 시군구
export function regionOptions(regions) {
  const opts = [
    {label: "서울 전체", where: "sido = '11'"},
    {label: "경기 전체", where: "sido = '41'"}
  ];
  const cities = new Map();
  for (const r of regions) if (r.sido === "41" && r.name.includes(" ")) {
    if (!cities.has(r.city)) cities.set(r.city, []);
    cities.get(r.city).push(r.code);
  }
  for (const [city, codes] of cities) opts.push({label: `경기 · ${city} 전체`, where: `sgg IN (${codes.map((c) => `'${c}'`).join(",")})`});
  for (const r of regions) opts.push({label: `${r.sido === "11" ? "서울" : "경기"} · ${r.name}`, where: `sgg = '${r.code}'`});
  return opts;
}

export function bandWhere(bands) {
  if (!bands?.length || bands.length === BANDS.length) return "TRUE";
  return `band IN (${bands.map((b) => `'${b.replace(/'/g, "")}'`).join(",")})`;
}

export function sinceWhere(months) {
  return `deal_date >= (SELECT max(deal_date) FROM trades) - INTERVAL ${Number(months) | 0} MONTH`;
}

// ---------- 카드 ----------
export function card(title, value, sub = "", tone = "") {
  return html`<div class="card kpi ${tone}">
    <div class="kpi-title">${title}</div>
    <div class="kpi-value">${value}</div>
    ${sub ? html`<div class="kpi-sub">${sub}</div>` : ""}
  </div>`;
}

export function sampleBanner(isSample) {
  return isSample
    ? html`<div class="banner warn" role="status"><strong>샘플 데이터</strong> — 인증키 없이 빌드되어 가짜 숫자가 표시되고 있습니다. 실제 판단에 쓰지 마세요.</div>`
    : "";
}

// 차트 공통 옵션: 모바일에서 글자 크기 유지, 여백 최소화
export const plotBase = (width) => ({
  width,
  height: Math.max(220, Math.min(360, width * 0.55)),
  marginLeft: 48,
  marginRight: 12,
  style: {fontSize: width < 520 ? "12px" : "13px", fontFamily: "var(--sans-serif)", overflow: "visible"},
  x: {label: null},
  y: {grid: true, label: null}
});
