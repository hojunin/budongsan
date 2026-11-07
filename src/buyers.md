---
title: 매수자 분석
---

```js
import {chart} from "./components/charts.js";
import {dataTable} from "./components/table.js";
import {enhanceUI} from "./components/appearance.js";
import {heading, num, PALETTE} from "./components/ui.js";
const disposeUI = enhanceUI(invalidation);
const rone = Array.from(await FileAttachment("data/rone.parquet").parquet(), (d) => ({...d, date: new Date(d.date)}))
  .filter((d) => d.metric === "mm_buyer_residence" || d.metric === "mm_buyer_age");
```

# 매수자 분석

<p class="lead">누가 아파트를 사는지 봅니다. 한국부동산원의 매입자 거주지별·연령대별 아파트 매매거래 통계(신고 건수 기준)입니다. 외지인 매수가 늘면 투자 수요, 2030 비중이 늘면 실수요 이동의 신호로 자주 인용됩니다.</p>

```js
// 월 × 지역 × 항목 값을 한 행으로 펼친다
const wide = d3.rollups(rone, (v) => Object.fromEntries(v.map((d) => [`${d.metric}:${d.item}`, d.value])), (d) => d.region_full, (d) => +d.date)
  .flatMap(([region, rows]) => rows.map(([t, v]) => {
    const get = (k) => v[k] ?? 0;
    const total = get("mm_buyer_residence:합계");
    const ageTotal = get("mm_buyer_age:합계");
    const sameSgg = get("mm_buyer_residence:관할시군구내"), sameSido = get("mm_buyer_residence:관할시도내");
    return {region, date: new Date(t), total,
      outsider: total ? 1 - (sameSgg + sameSido) / total : null,
      fromSeoul: total && !region.startsWith("서울") ? get("mm_buyer_residence:관할시도외_서울") / total : null,
      young: ageTotal ? (get("mm_buyer_age:20대이하") + get("mm_buyer_age:30대")) / ageTotal : null,
      ages: Object.fromEntries(Object.entries(v).filter(([k]) => k.startsWith("mm_buyer_age:") && !k.endsWith("합계")).map(([k, x]) => [k.split(":")[1], ageTotal ? x / ageTotal : null]))};
  }))
  .sort((a, b) => a.date - b.date);
const regionNames = [...new Set(wide.map((d) => d.region))].sort((a, b) => (a.split(">").length - b.split(">").length) || a.localeCompare(b, "ko"));
const label = (r) => r.split(">").at(-1) + (r.includes(">") ? ` (${r.split(">")[0]})` : "");
```

<div class="filters">
<div class="filter-field filter-field--standard">

```js
const picked = view(Inputs.select(regionNames, {label: "지역 (최대 5곳)", multiple: 5, format: label,
  value: ["서울", "경기"].filter((r) => regionNames.includes(r))}));
```

</div>
<div class="filter-field filter-field--standard">

```js
const years = view(Inputs.radio([3, 5, 10], {label: "기간", value: 5, format: (y) => `${y}년`}));
```

</div>
</div>

```js
const since = new Date(); since.setFullYear(since.getFullYear() - years);
// 월별 값은 거래가 적은 구에서 크게 흔들려 3개월 이동평균으로 본다
const line = (key) => picked.map((region, i) => {
  const rows = wide.filter((d) => d.region === region && d.date >= since);
  const data = rows.map((d, j) => {
    const w = rows.slice(Math.max(0, j - 2), j + 1).map((x) => x[key]).filter((x) => x != null);
    return [+d.date, j >= 2 && w.length === 3 ? +(w.reduce((a, b) => a + b, 0) / 3 * 100).toFixed(2) : null];
  });
  return {name: label(region), type: "line", itemStyle: {color: PALETTE[i]}, data};
});
const pctChart = (key) => chart({xAxis: {type: "time"}, yAxis: {name: "%", axisLabel: {formatter: "{value}%", fontSize: 10}},
  tooltip: {trigger: "axis", confine: true, renderMode: "richText", valueFormatter: (v) => v == null ? "–" : `${Number(v).toFixed(1)}%`},
  series: line(key)}, invalidation);
const first = picked[0];
const ageKeys = ["20대이하", "30대", "40대", "50대", "60대", "70대이상"].filter((k) => wide.some((d) => d.ages[k] != null));
```

<div class="grid-2">
  <div class="card">${heading("외지인 매수 비중 (3개월 평균)", "그 지역 밖(다른 시도)에 사는 사람이 산 비율입니다. 시군구를 고르면 같은 시도의 다른 시군구 거주자는 외지인에서 뺍니다.")}<div class="chart-slot">${pctChart("outsider")}</div></div>
  <div class="card">${heading("2030 매수 비중 (3개월 평균)", "매수자 중 20대 이하와 30대의 비율입니다.")}<div class="chart-slot">${pctChart("young")}</div></div>
  <div class="card">${heading("서울 거주자의 매수 비중 (3개월 평균)", "서울이 아닌 지역에서, 서울에 사는 사람이 산 비율입니다. 서울 수요가 경기로 넘어가는 흐름을 볼 때 씁니다. 서울 지역은 표시하지 않습니다.")}<div class="chart-slot">${pctChart("fromSeoul")}</div></div>
  <div class="card">${heading(`연령대 구성 — ${first ? label(first) : ""}`, "고른 첫 번째 지역의 월별 매수자 연령대 구성입니다. 합이 100%가 되도록 쌓았습니다.")}<div class="chart-slot">${chart({
    xAxis: {type: "time"}, yAxis: {name: "%", max: 100, axisLabel: {formatter: "{value}%", fontSize: 10}},
    tooltip: {trigger: "axis", confine: true, renderMode: "richText", valueFormatter: (v) => v == null ? "–" : `${Number(v).toFixed(1)}%`},
    series: ageKeys.map((k, i) => ({name: k, type: "line", stack: "age", areaStyle: {opacity: .5}, itemStyle: {color: PALETTE[i % PALETTE.length]},
      data: wide.filter((d) => d.region === first && d.date >= since).map((d) => [+d.date, d.ages[k] == null ? null : +(d.ages[k] * 100).toFixed(2)])}))
  }, invalidation)}</div></div>
</div>

## 최근 달 지역별 비교

```js
const lastDate = d3.max(wide, (d) => d.date);
const yearAgo = new Date(lastDate); yearAgo.setFullYear(yearAgo.getFullYear() - 1);
const latest = regionNames.map((region) => {
  const cur = wide.find((d) => d.region === region && +d.date === +lastDate);
  const old = wide.find((d) => d.region === region && +d.date === +yearAgo);
  if (!cur) return null;
  return {region: label(region), total: cur.total, outsider: cur.outsider, outsiderChg: cur.outsider != null && old?.outsider != null ? cur.outsider - old.outsider : null,
    young: cur.young, fromSeoul: cur.fromSeoul};
}).filter(Boolean);
const pp = (v) => v == null ? "–" : `${v > 0 ? "+" : ""}${(v * 100).toFixed(1)}%p`;
const p1 = (v) => v == null ? "–" : `${(v * 100).toFixed(1)}%`;
```

<div class="card grid-1">
  ${heading(`지역별 매수자 구성 — ${lastDate ? `${lastDate.getFullYear()}년 ${lastDate.getMonth() + 1}월` : ""}`, "가장 최근 달의 신고 건수 기준입니다. 거래가 적은 지역은 비율이 크게 흔들리니 거래 건수와 함께 보세요.")}
  <div class="table-slot">${dataTable(latest, [
    {title: "지역", field: "region"},
    {title: "거래", field: "total", sorter: "number", format: num},
    {title: "외지인 비중", field: "outsider", sorter: "number", format: p1},
    {title: "외지인 1년 변화", field: "outsiderChg", sorter: "number", format: pp, signed: true},
    {title: "2030 비중", field: "young", sorter: "number", format: p1},
    {title: "서울 거주자 비중", field: "fromSeoul", sorter: "number", format: p1}
  ], invalidation)}</div>
</div>
