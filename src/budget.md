---
title: 예산 계산기
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
const disposeUI = enhanceUI(invalidation);
```


```js
import {scenario, STRESS} from "./components/budget.js";
import {card, won, COLOR} from "./components/ui.js";
```

# 예산 계산기

<p class="lead">가격·현금·소득·금리를 바꿔 가며 필요 현금과 월 상환액을 봅니다. 문서 ①탭과 같은 가정(30년 원리금균등, DSR 40%, 수도권 스트레스 3%)입니다.</p>

<div class="filters filters--budget">

<div class="filter-field filter-field--standard">

```js
const product = view(Inputs.select(["디딤돌", ...Object.keys(STRESS)], {label: "대출", value: "5년 주기형"}));
```

</div>

<div class="filter-field filter-field--range">

```js
const price = view(Inputs.range([30000, 120000], {label: "매수가 (만 원)", step: 500, value: 80000}));
```

</div>

<div class="filter-field filter-field--standard">

```js
const cash = view(Inputs.number({label: "현금 (만 원)", value: 37000, step: 500}));
```

</div>

<div class="filter-field filter-field--standard">

```js
const income = view(Inputs.number({label: "대출 명의자 연소득 (만 원)", value: product === "디딤돌" ? 5700 : 8000, step: 100}));
```

</div>

<div class="filter-field filter-field--range">

```js
const rate = view(Inputs.range([2, 7], {label: "금리 (%)", step: 0.05, value: product === "디딤돌" ? 3.5 : 4.5}));
```

</div>

</div>

```js
const s = scenario({price, cash, income, rate, product});
const curve = d3.range(30000, 120001, 1000).map((p) => ({p, ...scenario({price: p, cash, income, rate, product})}));
const maxAffordable = d3.max(curve.filter((d) => d.gap >= 0 && d.eligibleA), (d) => d.p);
```

<div class="kpis">
  <div class="kpi-slot">${card("대출 가능액", won(s.loan), s.loan === s.incomeCap ? "소득 심사(DSR·DTI)가 한도" : "LTV·상한이 한도")}</div>
  <div class="kpi-slot">${card("필요 현금", won(s.need), `취득세 ${won(s.tax)} 포함 · 중개수수료 제외`)}</div>
  <div class="kpi-slot">${card(s.gap >= 0 ? "현금 여유" : "현금 부족", won(Math.abs(s.gap)), s.gap >= 0 ? "가능" : "부족", s.gap >= 0 ? "down" : "up")}</div>
  <div class="kpi-slot">${card("월 상환액", won(s.monthly), `${rate}% · 30년`)}</div>
</div>

<div class="eligibility-note">${!s.eligibleA ? html`<div class="banner warn">디딤돌은 주택 평가액 6억 원 이하만 가능합니다.</div>` : ""}</div>

<div class="card grid-1">
  <div class="chart-heading"><h2>매수가별 필요 현금</h2><details class="chart-info"><summary aria-label="매수가별 필요 현금 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">매수가에 따라 필요한 현금·대출 가능액·월 상환액이 어떻게 달라지는지 보여줍니다. 월 상환액은 오른쪽 축을 사용합니다. 보유 현금선, 선택 매수가선과 최대 매수 가능 지점을 함께 확인할 수 있습니다. 중개수수료 등 일부 비용은 제외된 추정치입니다.</div></details></div>
  <div class="chart-slot">${chart({
    xAxis: {type: "value", name: "매수가", axisLabel: {formatter: (v) => won(v), fontSize: 10}},
    yAxis: [{name: "현금·대출 (만 원)", axisLabel: {formatter: (v) => won(v), fontSize: 10}}, {name: "월 상환 (만 원)", splitLine: {show: false}}],
    tooltip: {trigger: "axis", confine: true, renderMode: "richText", valueFormatter: (v) => won(v)},
    series: [
      {name: "필요 현금", type: "line", data: curve.map((d) => [d.p, d.need]), areaStyle: {opacity: .08},
        markLine: {symbol: "none", label: {fontSize: 10, position: "insideEndTop"}, data: [
          {yAxis: cash, label: {formatter: `보유 현금 ${won(cash)}`}, lineStyle: {color: "#626b86", type: "solid"}},
          {xAxis: price, label: {formatter: "선택 매수가"}}
        ]},
        markPoint: {symbol: "circle", symbolSize: 9, label: {show: false}, data: maxAffordable ? [{coord: [maxAffordable, scenario({price: maxAffordable, cash, income, rate, product}).need]}] : []}},
      {name: "대출 가능액", type: "line", data: curve.map((d) => [d.p, d.loan])},
      {name: "월 상환액", type: "line", yAxisIndex: 1, data: curve.map((d) => [d.p, d.monthly])}
    ]
  }, invalidation)}</div>
  <p class="note">파란 선 아래가 살 수 있는 구간입니다. ${maxAffordable ? html`이 조건의 최대 매수가는 약 <strong>${won(maxAffordable)}</strong>입니다.` : "이 조건으로는 살 수 있는 가격대가 없습니다."} 법·규정 해석이 아니라 추정치입니다.</p>
</div>
