---
title: 시장 한눈에
---

```js
import {regionOptions, bandWhere, sinceWhere, card, sampleBanner, plotBase, won, pct, signed, num, BANDS, BAND_LABEL, COLOR} from "./components/ui.js";
const regions = await FileAttachment("data/regions.json").json();
const db = await DuckDBClient.of({trades: FileAttachment("data/trades.parquet")});
const meta = (await db.query(`SELECT bool_or(is_sample) AS sample, max(deal_date) AS last FROM trades`))[0];
```

# 시장 한눈에

<p class="lead">고른 지역의 아파트 거래량과 가격, 보조지표를 최근 순으로 봅니다.</p>

${sampleBanner(meta.sample)}

<div class="filters">

```js
const OPTS = regionOptions(regions);
const region = view(Inputs.select(OPTS, {label: "지역", format: (d) => d.label, value: OPTS[0]}));
const bands = view(Inputs.select(BANDS, {label: "평형", multiple: true, value: ["59", "84"], format: (b) => BAND_LABEL[b]}));
const months = view(Inputs.radio([12, 24, 36], {label: "기간(개월)", value: 24}));
```

</div>

```js
const where = `${region.where} AND ${bandWhere(bands)} AND ${sinceWhere(months)}`;
const monthly = await db.query(`
  SELECT ym,
    count(*) FILTER (WHERE NOT canceled)                       AS n,
    count(*) FILTER (WHERE canceled)                           AS n_canceled,
    median(ppm2) FILTER (WHERE NOT canceled)                   AS ppm2_med,
    quantile_cont(ppm2, 0.25) FILTER (WHERE NOT canceled)      AS ppm2_q1,
    quantile_cont(ppm2, 0.75) FILTER (WHERE NOT canceled)      AS ppm2_q3,
    median(price) FILTER (WHERE NOT canceled)                  AS price_med,
    avg(CASE WHEN new_high AND NOT canceled THEN 1 ELSE 0 END) AS new_high_rate,
    avg(CASE WHEN direct THEN 1 ELSE 0 END)                    AS direct_rate,
    avg(CASE WHEN canceled THEN 1 ELSE 0 END)                  AS cancel_rate
  FROM trades WHERE ${where}
  GROUP BY ym ORDER BY ym`);
const rows = Array.from(monthly, (d) => ({...d, date: new Date(d.ym + "-01"), n: Number(d.n), n_canceled: Number(d.n_canceled)}));
// 최근 1개월은 신고 지연으로 적게 잡히므로 추세 계산에서 제외
const settled = rows.slice(0, -1);
const last = settled.at(-1), prev12 = settled.at(-13), prev6 = settled.at(-7);
const ma = settled.map((d, i, a) => ({date: d.date, ma: i >= 2 ? (a[i].n + a[i - 1].n + a[i - 2].n) / 3 : null}));
```

<div class="kpis">
  ${card("최근 월 거래량", num(last?.n), `${last?.ym ?? ""} · 해제 ${num(last?.n_canceled)}건`)}
  ${card("㎡당 중위가", last ? `${num(last.ppm2_med)}만` : "–", "평형 필터 적용")}
  ${card("12개월 변화", signed(prev12 ? last.ppm2_med / prev12.ppm2_med - 1 : null), "㎡당 중위가 기준", prev12 && last.ppm2_med > prev12.ppm2_med ? "up" : "down")}
  ${card("신고가 비율", pct(last?.new_high_rate), "같은 단지·평형 직전 최고가 초과")}
</div>

<div class="grid-2">
  <div class="card">
    <h2>월별 거래량</h2>
    ${resize((width) => Plot.plot({
      ...plotBase(width),
      y: {grid: true, label: "건"},
      marks: [
        Plot.rectY(rows, {x: "date", interval: "month", y: "n", fill: COLOR.accent, fillOpacity: 0.85, tip: {format: {x: "%Y-%m"}}, title: (d) => `${d.ym}\n거래 ${d.n}건 · 해제 ${d.n_canceled}건`}),
        Plot.rectY(rows, {x: "date", interval: "month", y1: "n", y2: (d) => d.n + d.n_canceled, fill: COLOR.muted, fillOpacity: 0.5}),
        Plot.lineY(ma, {x: "date", y: "ma", stroke: "currentColor", strokeWidth: 1.5, curve: "monotone-x"}),
        Plot.ruleY([0])
      ]
    }))}
    <p class="note">막대: 정상 거래 · 회색: 해제 · 선: 3개월 이동평균. 마지막 달은 신고가 덜 들어온 상태입니다.</p>
  </div>
  <div class="card">
    <h2>㎡당 실거래가 (중위 · 사분위 범위)</h2>
    ${resize((width) => Plot.plot({
      ...plotBase(width),
      y: {grid: true, label: "만 원/㎡"},
      marks: [
        Plot.areaY(rows, {x: "date", y1: "ppm2_q1", y2: "ppm2_q3", fill: COLOR.accent2, fillOpacity: 0.15, curve: "monotone-x"}),
        Plot.lineY(rows, {x: "date", y: "ppm2_med", stroke: COLOR.accent2, strokeWidth: 2.2, curve: "monotone-x", tip: true, title: (d) => `${d.ym}\n중위 ${num(d.ppm2_med)}만/㎡\n중위 거래가 ${won(d.price_med)}`}),
        Plot.dot(rows.slice(-1), {x: "date", y: "ppm2_med", fill: COLOR.accent2, r: 4})
      ]
    }))}
    <p class="note">띠: 25~75% 구간. 평형이 섞이면 ㎡당 가격이 총액보다 비교에 안정적입니다.</p>
  </div>
</div>

## 보조지표

```js
const byBand = await db.query(`
  WITH t AS (SELECT *, deal_date >= (SELECT max(deal_date) FROM trades) - INTERVAL 6 MONTH AS recent
             FROM trades WHERE ${region.where} AND NOT canceled AND ${sinceWhere(12)})
  SELECT band, recent, median(ppm2) AS med, count(*) AS n FROM t GROUP BY band, recent`);
const bandRows = Array.from(byBand, (d) => ({...d, period: d.recent ? "최근 6개월" : "이전 6개월", n: Number(d.n)}));
const ratioRows = rows.flatMap((d) => [
  {date: d.date, k: "신고가", v: d.new_high_rate},
  {date: d.date, k: "직거래", v: d.direct_rate},
  {date: d.date, k: "해제", v: d.cancel_rate}
]);
```

<div class="grid-2">
  <div class="card">
    <h3>신고가 · 직거래 · 해제 비율</h3>
    ${resize((width) => Plot.plot({
      ...plotBase(width),
      y: {grid: true, tickFormat: "%", label: null},
      color: {legend: true, domain: ["신고가", "직거래", "해제"], range: [COLOR.accent, COLOR.accent2, COLOR.warn]},
      marks: [Plot.lineY(ratioRows, {x: "date", y: "v", stroke: "k", strokeWidth: 1.8, curve: "monotone-x", tip: {format: {y: ".1%"}}})]
    }))}
    <p class="note">신고가 비율이 오르면 매도자 우위입니다. 해제·직거래 비율이 튀면 이상 거래를 의심해 볼 신호입니다.</p>
  </div>
  <div class="card">
    <h3>평형별 ㎡당 중위가 — 최근 6개월 vs 이전 6개월</h3>
    ${resize((width) => Plot.plot({
      ...plotBase(width),
      fx: {label: null, domain: BANDS.filter((b) => bandRows.some((d) => d.band === b)), tickFormat: (b) => BAND_LABEL[b], padding: 0.15},
      x: {axis: null, domain: ["이전 6개월", "최근 6개월"]},
      y: {grid: true, label: "만 원/㎡"},
      color: {legend: true, domain: ["이전 6개월", "최근 6개월"], range: [COLOR.muted, COLOR.accent]},
      marks: [
        Plot.barY(bandRows, {fx: "band", x: "period", y: "med", fill: "period", tip: true, title: (d) => `${BAND_LABEL[d.band]} · ${d.period}\n${num(d.med)}만/㎡ (${d.n}건)`}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
</div>

<p class="note">마지막 거래일: ${meta.last?.toLocaleDateString?.("ko-KR") ?? meta.last}. 해제 거래는 가격 통계에서 빼고, 거래량에는 회색으로만 표시합니다.</p>
