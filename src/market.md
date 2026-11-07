---
title: 시장 지표
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
import {heading, sampleTag, regionColor} from "./components/ui.js";
const disposeUI = enhanceUI(invalidation);
const rone = Array.from(await FileAttachment("data/rone.parquet").parquet(), (d) => ({...d, date: new Date(d.date)}));
const kbRaw = await FileAttachment("data/kb.parquet").parquet();
const kb = Array.from(kbRaw, (d) => ({...d, date: new Date(d.date), value: Number(d.value)}));
```

# 시장 지표

<p class="lead">한국부동산원 주간·월간 아파트 지표와 KB 설문 지표입니다. 같은 집의 가격 변화를 추정한 지수라서, 거래된 단지 구성에 따라 흔들리는 실거래 중위가보다 시장 방향을 보기에 안정적입니다.</p>

<div class="data-indicator">${sampleTag(kb.some((d) => d.is_sample))}</div>

```js
// 서울·경기 하위 권역/구까지 고를 수 있게 지역 이름을 'region_full' 로 쓴다
const regionNames = [...new Set(rone.filter((d) => d.metric === "wk_sale_index").map((d) => d.region_full))]
  .sort((a, b) => (a.split(">").length - b.split(">").length) || a.localeCompare(b, "ko"));
const label = (r) => r.split(">").at(-1) + (r.includes(">") ? ` (${r.split(">")[0]})` : "");
```

<div class="filters filters--market">
<div class="filter-field filter-field--standard">

```js
const picked = view(Inputs.select(regionNames, {label: "지역 (최대 5곳)", multiple: 5, format: label,
  value: ["서울", "경기", "수도권"].filter((r) => regionNames.includes(r))}));
```

</div>
<div class="filter-field filter-field--standard">

```js
const years = view(Inputs.radio([1, 3, 5, 10], {label: "기간", value: 3, format: (y) => `${y}년`}));
```

</div>
</div>

```js
const since = new Date(); since.setFullYear(since.getFullYear() - years);
const series = (metric, {item = null, transform = null} = {}) => picked.map((region, i) => {
  let rows = rone.filter((d) => d.metric === metric && d.region_full === region && (!item || d.item === item) && d.date >= since).sort((a, b) => a.date - b.date);
  let data = rows.map((d) => [+d.date, d.value]);
  if (transform === "change") data = data.map(([t, v], j) => [t, j ? (v / data[j - 1][1] - 1) * 100 : null]).slice(1);
  return {name: label(region), type: "line", itemStyle: {color: regionColor(region)}, data};
});
const roneChart = (metric, {name = "지수", ref = null, refLabel = "", ...opts} = {}) => chart({
  xAxis: {type: "time"}, yAxis: {name, scale: true},
  series: series(metric, opts).map((s, i) => i === 0 && ref != null ? {...s, markLine: {symbol: "none", data: [{yAxis: ref, label: {formatter: refLabel, position: "insideEndTop", fontSize: 10}}]}} : s)
}, invalidation);
```

## 가격 (한국부동산원)

<div class="grid-2">
  <div class="card">${heading("주간 아파트 매매가격지수", "매주 표본 아파트의 시세 변화를 조사한 지수입니다. 기준 시점을 100으로 합니다. 지역 사이의 수준 비교보다 같은 지역의 흐름을 볼 때 씁니다.")}<div class="chart-slot">${roneChart("wk_sale_index")}</div></div>
  <div class="card">${heading("주간 매매가격 변동률 (%)", "직전 주 대비 매매가격지수 변동률입니다. 기사에서 말하는 '이번 주 서울 아파트값 0.1% 상승'이 이 값입니다.")}<div class="chart-slot">${roneChart("wk_sale_index", {name: "%", transform: "change", ref: 0, refLabel: "0 = 보합"})}</div></div>
  <div class="card">${heading("주간 아파트 전세가격지수", "표본 아파트 전세 시세의 변화를 조사한 지수입니다.")}<div class="chart-slot">${roneChart("wk_jeonse_index")}</div></div>
  <div class="card">${heading("주간 전세가격 변동률 (%)", "직전 주 대비 전세가격지수 변동률입니다.")}<div class="chart-slot">${roneChart("wk_jeonse_index", {name: "%", transform: "change", ref: 0, refLabel: "0 = 보합"})}</div></div>
  <div class="card">${heading("월간 아파트 매매 중위가격 (만 원/㎡)", "한국부동산원 월간 조사의 ㎡당 중위가격입니다. 표본 기반이라 실거래 중위가와 다를 수 있습니다.")}<div class="chart-slot">${roneChart("mm_sale_median", {name: "만 원/㎡"})}</div></div>
  <div class="card">${heading("월간 아파트 전세 중위가격 (만 원/㎡)", "한국부동산원 월간 조사의 ㎡당 전세 중위가격입니다.")}<div class="chart-slot">${roneChart("mm_jeonse_median", {name: "만 원/㎡"})}</div></div>
</div>

## 수급과 임대

<div class="grid-2">
  <div class="card">${heading("매매수급지수", "중개업소 설문으로 매수자와 매도자 중 어느 쪽이 많은지를 0~200으로 나타냅니다. 100보다 크면 사려는 사람이 더 많습니다.")}<div class="chart-slot">${roneChart("wk_sale_supply", {name: null, ref: 100, refLabel: "100 = 균형"})}</div></div>
  <div class="card">${heading("전세수급지수", "전세를 구하려는 사람과 내놓는 사람의 균형입니다. 100보다 크면 전세 구하기가 어렵다는 뜻입니다.")}<div class="chart-slot">${roneChart("wk_jeonse_supply", {name: null, ref: 100, refLabel: "100 = 균형"})}</div></div>
  <div class="card">${heading("아파트 전월세 전환율 (%)", "전세 보증금을 월세로 바꿀 때 적용되는 연 이율입니다. 금리와 함께 보면 월세 전환 압력을 가늠할 수 있습니다.")}<div class="chart-slot">${roneChart("mm_conversion", {name: "%"})}</div></div>
</div>

<span id="kb-survey"></span>

## KB 설문 지표

```js
const kbRegions = [...new Set(kb.map((d) => d.region))];
const kbPick = picked.map((r) => r.split(">").at(-1)).filter((r) => kbRegions.includes(r));
const kbShown = kbPick.length ? kbPick : kbRegions.filter((r) => ["서울", "경기"].includes(r));
const kbChart = (metric, {name = "지수", ref = null, refLabel = ""} = {}) => chart({
  xAxis: {type: "time"}, yAxis: {name},
  series: kbShown.map((region, i) => ({name: region, type: "line", itemStyle: {color: regionColor(region)},
    data: kb.filter((d) => d.metric === metric && d.region === region && d.date >= since).map((d) => [+d.date, d.value]),
    ...(i === 0 && ref != null ? {markLine: {symbol: "none", data: [{yAxis: ref, label: {formatter: refLabel, position: "insideEndTop", fontSize: 10}}]}} : {})}))
}, invalidation);
```

<p class="note">KB 매매·전세 가격지수는 KB 서버가 자동 수집을 막아서 받지 않고, 위의 한국부동산원 공식 지수로 대신합니다. 아래 세 지표는 고른 지역 중 KB가 제공하는 곳(서울·경기 등)만 보여 줍니다.</p>

<div class="grid-2">
  <div class="card">${heading("KB 매수우위지수", "KB 중개업소 설문에서 매수자와 매도자 중 어느 쪽이 많은지 나타냅니다. 100보다 낮으면 매도자가 많다는 응답이 우세합니다.")}<div class="chart-slot">${kbChart("buyer_index", {name: null, ref: 100, refLabel: "100 = 균형"})}</div></div>
  <div class="card">${heading("KB 매매거래활발지수", "매매 거래가 얼마나 활발한지에 대한 중개업소 응답입니다. 실제 거래 건수와는 구분해서 보세요.")}<div class="chart-slot">${kbChart("trade_activity", {name: null, ref: 100, refLabel: "100 = 보통"})}</div></div>
  <div class="card">${heading("KB 전세가격비율 (%)", "매매가격 대비 전세가격 비율입니다. 높을수록 매매가의 하방이 단단하다고 보고, 낮으면 갭투자 부담이 큽니다.")}<div class="chart-slot">${kbChart("jeonse_ratio", {name: "%"})}</div></div>
</div>
