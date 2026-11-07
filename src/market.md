---
title: 시장 온도 (KB)
---

```js
import {sampleBanner, plotBase, num, PALETTE} from "./components/ui.js";
const kbRaw = await FileAttachment("data/kb.parquet").parquet();
const kb = Array.from(kbRaw, (d) => ({...d, date: new Date(d.date), value: Number(d.value)}));
const isSample = kb.some((d) => d.is_sample);
const regionNames = [...new Set(kb.map((d) => d.region))];
```

# 시장 온도 (KB)

<p class="lead">KB 주택가격동향조사의 지역 단위 지표입니다. 단지 판단의 보조 지표로 씁니다.</p>

${sampleBanner(isSample)}

<div class="filters">

```js
const picked = view(Inputs.select(regionNames, {label: "KB 지역", multiple: 4, value: regionNames.filter((r) => ["서울", "경기"].includes(r)).slice(0, 2)}));
const years = view(Inputs.radio([3, 5, 10], {label: "기간", value: 5, format: (y) => `${y}년`}));
```

</div>

```js
const since = d3.timeYear.offset(d3.max(kb, (d) => d.date), -years);
const sel = (metric) => kb.filter((d) => d.metric === metric && picked.includes(d.region) && d.date >= since);
const chart = (metric, {label, ref = null, refLabel = ""} = {}) => resize((width) => Plot.plot({
  ...plotBase(width),
  y: {grid: true, label},
  color: {legend: true, domain: picked, range: PALETTE},
  marks: [
    ref != null ? Plot.ruleY([ref], {stroke: "currentColor", strokeOpacity: 0.35, strokeDasharray: "4,3"}) : null,
    ref != null ? Plot.text([ref], {y: (d) => d, frameAnchor: "right", dy: -7, text: () => refLabel, fontSize: 11, fillOpacity: 0.7}) : null,
    Plot.lineY(sel(metric), {x: "date", y: "value", stroke: "region", strokeWidth: 2, curve: "monotone-x"}),
    Plot.tip(sel(metric), Plot.pointerX({x: "date", y: "value", stroke: "region", title: (d) => `${d.region} · ${d3.timeFormat("%Y-%m")(d.date)}\n${d.value.toFixed(1)}`}))
  ]
}));
```

<div class="grid-2">
  <div class="card"><h2>매매가격지수</h2>${chart("price_sale", {label: "지수"})}</div>
  <div class="card"><h2>전세가격지수</h2>${chart("price_jeonse", {label: "지수"})}</div>
  <div class="card"><h2>매수우위지수</h2>${chart("buyer_index", {label: null, ref: 100, refLabel: "100 = 매수·매도 균형"})}<p class="note">100보다 낮으면 ‘매도자가 많다’는 중개업소 응답이 많다는 뜻으로, 매수자에게 유리한 시장입니다.</p></div>
  <div class="card"><h2>매매거래활발지수</h2>${chart("trade_activity", {label: null, ref: 100, refLabel: "100 = 보통"})}</div>
  <div class="card"><h2>전세가격비율</h2>${chart("jeonse_ratio", {label: "%"})}<p class="note">매매가 대비 전세가 비율. 높을수록 하방이 단단하다고 보는 지표입니다.</p></div>
</div>
