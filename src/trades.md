---
title: 실거래 분석
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
const disposeUI = enhanceUI(invalidation);
```


```js
import {regionOptions, bandWhere, sinceWhere, card, sampleTag, won, pct, signed, num, BANDS, BAND_LABEL, COLOR} from "./components/ui.js";
const regions = await FileAttachment("data/regions.json").json();
const db = await DuckDBClient.of({trades: FileAttachment("data/trades.parquet")});
const meta = await db.queryRow(`SELECT bool_or(is_sample) AS sample, max(deal_date) AS last FROM trades`);
```

# 실거래 분석

<p class="lead lead--overview">고른 지역의 아파트 거래량과 가격, 보조지표를 최근 순으로 봅니다.</p>

<div class="data-indicator">${sampleTag(meta.sample)}</div>

<div class="filters filters--index">

<div class="filter-field filter-field--standard">

```js
const OPTS = regionOptions(regions);
const region = view(Inputs.select(OPTS, {label: "지역", format: (d) => d.label, value: OPTS[0]}));
```

</div>

<div class="filter-field filter-field--bands">

```js
const bands = view(Inputs.checkbox(BANDS, {label: "평형", value: ["59", "84"], format: (b) => BAND_LABEL[b]}));
```

</div>

<div class="filter-field filter-field--standard">

```js
const months = view(Inputs.radio([12, 24, 36], {label: "기간(개월)", value: 24}));
```

</div>

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
  <div class="kpi-slot">${card("최근 월 거래량", num(last?.n), `${last?.ym ?? ""} · 해제 ${num(last?.n_canceled)}건`)}</div>
  <div class="kpi-slot">${card("㎡당 중위가", last ? `${num(last.ppm2_med)}만` : "–", "평형 필터 적용")}</div>
  <div class="kpi-slot">${card("12개월 변화", signed(prev12 ? last.ppm2_med / prev12.ppm2_med - 1 : null), "㎡당 중위가 기준", prev12 && last.ppm2_med > prev12.ppm2_med ? "up" : "down")}</div>
  <div class="kpi-slot">${card("신고가 비율", pct(last?.new_high_rate), "같은 단지·평형 직전 최고가 초과")}</div>
</div>

<div class="grid-2">
  <div class="card">
    <div class="chart-heading"><h2>거래량 × 가격 흐름</h2><details class="chart-info"><summary aria-label="거래량 × 가격 흐름 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">막대는 월별 정상 거래와 해제 건수, 선은 3개월 평균 거래량과 ㎡당 중위가입니다. 가격은 오른쪽 축을 사용하므로 단위를 구분해 보세요. 범례로 지표를 숨기거나 아래 슬라이더로 기간을 확대할 수 있습니다.</div></details></div>
    <div class="chart-slot">${chart({
      xAxis: {data: rows.map((d) => d.ym)},
      yAxis: [{name: "거래 (건)"}, {name: "만 원/㎡", splitLine: {show: false}}],
      series: [
        {name: "정상 거래", type: "bar", stack: "거래", data: rows.map((d) => d.n), itemStyle: {borderRadius: [3, 3, 0, 0]}},
        {name: "해제", type: "bar", stack: "거래", data: rows.map((d) => d.n_canceled), itemStyle: {color: "#9ca3af"}},
        {name: "3개월 평균", type: "line", data: rows.map((d, i) => ma[i]?.ma ?? null)},
        {name: "㎡당 중위가", type: "line", yAxisIndex: 1, data: rows.map((d) => d.ppm2_med)}
      ]
    }, invalidation)}</div>
    <p class="note">막대: 정상 거래·해제 · 선: 3개월 평균과 ㎡당 중위가(오른쪽 축). 범례를 눌러 지표를 선택하세요. 마지막 달은 신고가 덜 들어온 상태입니다.</p>
  </div>
  <div class="card">
    <div class="chart-heading"><h2>㎡당 실거래가 (중위 · 사분위 범위)</h2><details class="chart-info"><summary aria-label="㎡당 실거래가 (중위 · 사분위 범위) 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">선은 월별 ㎡당 중위 실거래가, 띠는 거래 가격의 25~75% 구간입니다. 해제 거래는 가격 통계에서 제외합니다. 평형이 다른 거래를 면적당 가격으로 비교하는 지표입니다.</div></details></div>
    <div class="chart-slot">${chart({
      xAxis: {data: rows.map((d) => d.ym)}, yAxis: {name: "만 원/㎡"},
      series: [
        {name: "25%", type: "line", stack: "범위", data: rows.map((d) => d.ppm2_q1), lineStyle: {opacity: 0}, itemStyle: {color: "#8ab3ce"}, tooltip: {show: false}},
        {name: "25–75% 범위", type: "line", stack: "범위", data: rows.map((d) => d.ppm2_q3 == null || d.ppm2_q1 == null ? null : d.ppm2_q3 - d.ppm2_q1), lineStyle: {opacity: 0}, areaStyle: {color: "#8ab3ce", opacity: .25}, tooltip: {show: false}},
        {name: "중위가", type: "line", data: rows.map((d) => d.ppm2_med)}
      ], legend: {data: ["중위가"]},
      tooltip: {trigger: "axis", confine: true, renderMode: "richText", valueFormatter: (value) => `${num(value)}만/㎡`}
    }, invalidation)}</div>
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
```

<div class="grid-2">
  <div class="card">
    <div class="chart-heading"><h3>신고가 · 직거래 · 해제 비율</h3><details class="chart-info"><summary aria-label="신고가 · 직거래 · 해제 비율 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">월별 신고가·직거래·해제 거래의 비율을 함께 보여줍니다. 범례를 눌러 관심 지표만 남길 수 있습니다. 최근 달은 신고가 덜 접수되어 수치가 바뀔 수 있습니다.</div></details></div>
    <div class="chart-slot">${chart({
      xAxis: {data: rows.map((d) => d.ym)}, yAxis: {name: "%", axisLabel: {formatter: "{value}%", fontSize: 10}},
      tooltip: {trigger: "axis", confine: true, renderMode: "richText", valueFormatter: (v) => `${Number(v).toFixed(1)}%`},
      series: [["신고가", "new_high_rate"], ["직거래", "direct_rate"], ["해제", "cancel_rate"]].map(([name, key]) => ({name, type: "line", data: rows.map((d) => d[key] == null ? null : d[key] * 100)}))
    }, invalidation)}</div>
    <p class="note">신고가 비율이 오르면 매도자 우위입니다. 해제·직거래 비율이 튀면 이상 거래를 의심해 볼 신호입니다.</p>
  </div>
  <div class="card">
    <div class="chart-heading"><h3>평형별 ㎡당 중위가 — 최근 6개월 vs 이전 6개월</h3><details class="chart-info"><summary aria-label="평형별 ㎡당 중위가 — 최근 6개월 vs 이전 6개월 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">각 평형의 ㎡당 중위 실거래가를 최근 6개월과 그 이전 6개월로 나눠 비교합니다. 막대가 없는 평형은 해당 기간에 비교할 거래가 부족한 경우입니다.</div></details></div>
    <div class="chart-slot">${chart({
      xAxis: {data: BANDS.filter((b) => bandRows.some((d) => d.band === b)).map((b) => BAND_LABEL[b]), boundaryGap: true},
      yAxis: {name: "만 원/㎡"},
      series: [false, true].map((recent) => ({name: recent ? "최근 6개월" : "이전 6개월", type: "bar", barMaxWidth: 28,
        data: BANDS.filter((b) => bandRows.some((d) => d.band === b)).map((b) => bandRows.find((d) => d.band === b && Boolean(d.recent) === recent)?.med ?? null), itemStyle: {borderRadius: [4, 4, 0, 0]}}))
    }, invalidation)}</div>
  </div>
</div>

<p class="note">마지막 거래일: ${meta.last?.toLocaleDateString?.("ko-KR") ?? meta.last}. 해제 거래는 가격 통계에서 빼고, 거래량에는 회색으로만 표시합니다.</p>
