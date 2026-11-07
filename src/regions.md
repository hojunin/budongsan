---
title: 지역 비교
---

```js
import {dataTable} from "./components/table.js";
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
const disposeUI = enhanceUI(invalidation);
```


```js
import {regionOptions, bandWhere, sinceWhere, sampleTag, num, pct, signed, BANDS, BAND_LABEL, PALETTE} from "./components/ui.js";
const regions = await FileAttachment("data/regions.json").json();
const db = await DuckDBClient.of({trades: FileAttachment("data/trades.parquet")});
const isSample = (await db.queryRow(`SELECT bool_or(is_sample) AS s FROM trades`)).s;
const OPTS = regionOptions(regions);
const pick = (labels) => OPTS.filter((o) => labels.includes(o.label));
```

# 지역 비교

<p class="lead">최대 6개 지역을 골라 거래량과 가격 흐름을 같은 축에서 비교합니다.</p>

<div class="data-indicator">${sampleTag(isSample)}</div>

<div class="filters filters--regions">

<div class="filter-field filter-field--standard">

```js
const chosen = view(Inputs.select(OPTS, {label: "지역 (여러 개)", multiple: 6, format: (d) => d.label,
  value: pick(["서울 전체", "경기 전체", "서울 · 노원구", "경기 · 성남시 중원구", "경기 · 남양주시"])}));
```

</div>

<div class="filter-field filter-field--choices">

```js
const metrics = view(Inputs.checkbox(new Map([
  ["㎡당 중위가", "ppm2"], ["거래량", "n"], ["신고가 비율", "new_high_rate"], ["거래량 대비 해제율", "cancel_rate"]
]), {label: "비교 지표", value: ["ppm2", "n"]}));
```

</div>

<div class="filter-field filter-field--toggle">

```js
const indexed = view(Inputs.toggle({label: "시작 시점 = 100", value: false}));
```

</div>

<div class="filter-field filter-field--bands">

```js
const bands = view(Inputs.checkbox(BANDS, {label: "평형", value: ["59", "84"], format: (b) => BAND_LABEL[b]}));
```

</div>

<div class="filter-field filter-field--standard">

```js
const months = view(Inputs.radio([12, 24, 36], {label: "기간", value: 24, format: (m) => `${m}개월`}));
```

</div>

</div>

```js
const series = (await Promise.all(chosen.slice(0, 6).map(async (r) => {
  const q = await db.query(`
    SELECT ym, count(*) FILTER (WHERE NOT canceled) AS n,
      median(ppm2) FILTER (WHERE NOT canceled) AS ppm2,
      avg(CASE WHEN new_high AND NOT canceled THEN 1 ELSE 0 END) AS new_high_rate,
      avg(CASE WHEN canceled THEN 1 ELSE 0 END) AS cancel_rate
    FROM trades WHERE ${r.where} AND ${bandWhere(bands)} AND ${sinceWhere(months)}
    GROUP BY ym ORDER BY ym`);
  const rows = Array.from(q, (d) => ({region: r.label, date: new Date(d.ym + "-01"), ym: d.ym, n: Number(d.n), ppm2: d.ppm2, new_high_rate: d.new_high_rate, cancel_rate: d.cancel_rate})).slice(0, -1);
  return rows;
}))).flat();
const METRICS = {ppm2: "㎡당 중위가", n: "거래량", new_high_rate: "신고가 비율", cancel_rate: "해제율"};
const metricAxes = metrics.map((key, i) => ({name: indexed ? "시작=100" : key === "ppm2" ? "만 원/㎡" : key === "n" ? "건" : "%", position: i % 2 ? "right" : "left", offset: Math.floor(i / 2) * 42, splitLine: {show: i === 0}, axisLabel: {fontSize: 10}}));
const comparisonSeries = metrics.flatMap((key, metricIndex) => chosen.slice(0, 6).map((r, regionIndex) => {
  const values = series.filter((d) => d.region === r.label);
  const base = values.find((d) => d[key] > 0)?.[key];
  return {name: `${r.label} · ${METRICS[key]}`, type: "line", yAxisIndex: indexed ? 0 : metricIndex,
    lineStyle: {type: ["solid", "dashed", "dotted", "dashed"][metricIndex], width: 2}, itemStyle: {color: PALETTE[regionIndex]},
    data: values.map((d) => [d.ym, indexed ? base && d[key] != null ? d[key] / base * 100 : null : d[key] == null ? null : key.endsWith("rate") ? d[key] * 100 : d[key]])};
}));
```

<div class="card grid-1">
  <div class="chart-heading"><h2>지역별 지표 비교</h2><details class="chart-info"><summary aria-label="지역별 지표 비교 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">지역별 가격·거래량·비율을 선택해 함께 비교합니다. 색은 지역, 선 모양은 지표를 구분합니다. 지표마다 축 단위가 다르며, 시작 시점=100을 켜면 상대적인 변화 흐름을 비교할 수 있습니다. 최근 1개월은 신고 지연으로 제외합니다.</div></details></div>
  <div class="chart-slot">${chart({
    xAxis: {data: [...new Set(series.map((d) => d.ym))].sort()},
    yAxis: indexed ? [{name: "시작=100"}] : metricAxes.length ? metricAxes : [{}],
    grid: {left: metrics.length > 2 && !indexed ? 44 : 8, right: metrics.length > 3 && !indexed ? 48 : 12, top: 84, bottom: 72, containLabel: true},
    series: comparisonSeries
  }, invalidation)}</div>
  <p class="note">최근 1개월은 신고 지연으로 빼고 그렸습니다. 거래량은 지역 크기 차이가 커서 ‘시작 시점 = 100’으로 보면 흐름 비교가 쉽습니다.</p>
</div>

```js
const summary = d3.rollups(series, (v) => {
  const a = v.at(0), b = v.at(-1), m6 = v.at(-7);
  return {last: b?.ppm2, chg12: a && b ? b.ppm2 / a.ppm2 - 1 : null, chg6: m6 && b ? b.ppm2 / m6.ppm2 - 1 : null, vol3: d3.mean(v.slice(-3), (d) => d.n), vol3prev: d3.mean(v.slice(-15, -12), (d) => d.n)};
}, (d) => d.region).map(([region, s]) => ({region, ...s}));
```

<div class="card grid-1 table-wrap">
  <h2>요약</h2>
  <div class="table-slot">${dataTable(summary, [
    {field: "region", title: "지역"},
    {field: "last", title: "㎡당 중위가(만)", sorter: "number", format: num, responsive: 0},
    {field: "chg6", title: "6개월", sorter: "number", format: signed, signed: true},
    {field: "chg12", title: "기간 전체", sorter: "number", format: signed, signed: true},
    {field: "vol3", title: "최근 월평균 거래", sorter: "number", format: num},
    {field: "vol3prev", title: "1년 전 월평균", sorter: "number", format: num}
  ], invalidation)}</div>
</div>
