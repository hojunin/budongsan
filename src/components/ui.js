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

export function sampleTag(isSample) {
  return isSample
    ? html`<span class="mock-data-tag" role="status" aria-label="목데이터: 실제 판단에 사용하지 마세요" title="실제 판단에 사용하지 마세요">목데이터</span>`
    : "";
}

// ---------- 제목 + 설명 팝오버 (appearance.js 가 열고 닫는다) ----------
const INFO_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg>';
export function heading(title, info, level = 2) {
  const h = document.createElement(`h${level}`);
  h.textContent = title;
  const node = html`<div class="chart-heading">${h}${info ? html`<details class="chart-info"><summary aria-label=${`${title} 설명`}></summary><div class="chart-info-panel">${info}</div></details>` : ""}</div>`;
  if (info) node.querySelector("summary").innerHTML = INFO_ICON;
  return node;
}

// ---------- 기사·리포트 링크 목록 ----------
export function articleList(rows, {empty = "표시할 기사가 없습니다"} = {}) {
  if (!rows.length) return html`<p class="note">${empty}</p>`;
  return html`<ul class="article-list">${rows.map((a) => html`<li>
    <a href=${a.url} target="_blank" rel="noopener noreferrer">${a.title}</a>
    <span class="article-meta">${a.source} · ${a.published?.slice(0, 16) ?? ""}${a.category === "report" ? html` · <span class="chip">리포트·동향</span>` : ""}</span>
  </li>`)}</ul>`;
}

// ---------- 인사이트 문장 (복사 버튼 포함) ----------
export function insightList(items) {
  if (!items.length) return html`<p class="note">아직 계산할 데이터가 없습니다. 배치(scripts/batch.sh)를 돌린 뒤 다시 빌드하세요.</p>`;
  return html`<ul class="insight-list">${items.map((d) => {
    const sentence = `${d.title} (출처: ${d.source}, ${d.as_of} 기준)`;
    const copy = html`<button type="button" class="copy-btn" aria-label="문장 복사">복사</button>`;
    copy.onclick = async () => {
      try { await navigator.clipboard.writeText(sentence); copy.textContent = "복사됨"; } catch { copy.textContent = "복사 실패"; }
      setTimeout(() => (copy.textContent = "복사"), 1500);
    };
    return html`<li class=${`insight ${d.tone ?? ""}`}>
      <div class="insight-body">
        <span class="chip">${d.group}</span>
        <p class="insight-title">${d.title}</p>
        <p class="insight-meta">${d.sub ? `${d.sub} · ` : ""}${d.source} · ${d.as_of}</p>
        ${d.detail ? html`<p class="insight-detail">${d.detail}</p>` : ""}
      </div>${copy}
    </li>`;
  })}</ul>`;
}
