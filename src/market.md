---
title: 시장 온도 (KB)
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
const disposeUI = enhanceUI(invalidation);
```


```js
import {sampleTag, num, PALETTE} from "./components/ui.js";
const kbRaw = await FileAttachment("data/kb.parquet").parquet();
const kb = Array.from(kbRaw, (d) => ({...d, date: new Date(d.date), value: Number(d.value)}));
const isSample = kb.some((d) => d.is_sample);
const regionNames = [...new Set(kb.map((d) => d.region))];
```

# 시장 온도 (KB)

<p class="lead">KB 주택가격동향조사의 지역 단위 지표입니다. 단지 판단의 보조 지표로 씁니다.</p>

<div class="data-indicator">${sampleTag(isSample)}</div>

<div class="filters filters--market">

<div class="filter-field filter-field--standard">

```js
const picked = view(Inputs.select(regionNames, {label: "KB 지역", multiple: 4, value: regionNames.filter((r) => ["서울", "경기"].includes(r)).slice(0, 2)}));
```

</div>

<div class="filter-field filter-field--standard">

```js
const years = view(Inputs.radio([3, 5, 10], {label: "기간", value: 5, format: (y) => `${y}년`}));
```

</div>

</div>

```js
const since = d3.timeYear.offset(d3.max(kb, (d) => d.date), -years);
const sel = (metric) => kb.filter((d) => d.metric === metric && picked.includes(d.region) && d.date >= since);
const kbChart = (metric, {label, ref = null, refLabel = ""} = {}) => chart({
  xAxis: {type: "time"}, yAxis: {name: label ?? "지수"},
  series: picked.map((region, i) => ({name: region, type: "line", itemStyle: {color: PALETTE[i]}, data: sel(metric).filter((d) => d.region === region).map((d) => [+d.date, d.value]),
    ...(i === 0 && ref != null ? {markLine: {symbol: "none", data: [{yAxis: ref, label: {formatter: refLabel, position: "insideEndTop", fontSize: 10}}]}} : {})}))
}, invalidation);
```

<div class="grid-2">
  <div class="card"><div class="chart-heading"><h2>매매가격지수</h2><details class="chart-info"><summary aria-label="매매가격지수 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">KB의 지역별 아파트 매매가격지수 흐름입니다. 특정 단지의 거래가격이 아닌 지역 단위 조사 지표입니다. 범례에서 지역을 선택하고 슬라이더로 비교 기간을 조절할 수 있습니다.</div></details></div><div class="chart-slot">${kbChart("price_sale", {label: "지수"})}</div></div>
  <div class="card"><div class="chart-heading"><h2>전세가격지수</h2><details class="chart-info"><summary aria-label="전세가격지수 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">KB의 지역별 아파트 전세가격지수 흐름입니다. 개별 계약의 전세금이 아닌 지역 단위 조사 지표이므로 단지 실거래와 함께 참고하세요.</div></details></div><div class="chart-slot">${kbChart("price_jeonse", {label: "지수"})}</div></div>
  <div class="card"><div class="chart-heading"><h2>매수우위지수</h2><details class="chart-info"><summary aria-label="매수우위지수 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">KB 조사에서 매수자와 매도자 중 어느 쪽이 많은지를 나타내는 지표입니다. 100은 균형 기준이며, 100보다 낮으면 매도자가 많다는 응답이 우세합니다. 가격 변화율과는 다른 지표입니다.</div></details></div><div class="chart-slot">${kbChart("buyer_index", {label: null, ref: 100, refLabel: "100 = 매수·매도 균형"})}</div><p class="note">100보다 낮으면 ‘매도자가 많다’는 중개업소 응답이 많다는 뜻으로, 매수자에게 유리한 시장입니다.</p></div>
  <div class="card"><div class="chart-heading"><h2>매매거래활발지수</h2><details class="chart-info"><summary aria-label="매매거래활발지수 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">KB 조사에서 지역의 매매거래가 얼마나 활발한지 보여주는 지표입니다. 100을 기준선으로 표시하며 실제 거래 건수와는 구분해 보아야 합니다.</div></details></div><div class="chart-slot">${kbChart("trade_activity", {label: null, ref: 100, refLabel: "100 = 보통"})}</div></div>
  <div class="card"><div class="chart-heading"><h2>전세가격비율</h2><details class="chart-info"><summary aria-label="전세가격비율 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">KB 조사 기준 매매가격 대비 전세가격 비율입니다. 지역의 전세·매매 관계를 보는 보조 지표이며 개별 단지의 실거래 전세가율과 다를 수 있습니다.</div></details></div><div class="chart-slot">${kbChart("jeonse_ratio", {label: "%"})}</div><p class="note">매매가 대비 전세가 비율. 높을수록 하방이 단단하다고 보는 지표입니다.</p></div>
</div>
