---
title: 예산 계산기
---

```js
import {scenario, STRESS} from "./components/budget.js";
import {card, won, plotBase, COLOR} from "./components/ui.js";
```

# 예산 계산기

<p class="lead">가격·현금·소득·금리를 바꿔 가며 필요 현금과 월 상환액을 봅니다. 문서 ①탭과 같은 가정(30년 원리금균등, DSR 40%, 수도권 스트레스 3%)입니다.</p>

<div class="filters">

```js
const product = view(Inputs.select(["디딤돌", ...Object.keys(STRESS)], {label: "대출", value: "5년 주기형"}));
const price = view(Inputs.range([30000, 120000], {label: "매수가 (만 원)", step: 500, value: 80000}));
const cash = view(Inputs.number({label: "현금 (만 원)", value: 37000, step: 500}));
const income = view(Inputs.number({label: "대출 명의자 연소득 (만 원)", value: product === "디딤돌" ? 5700 : 8000, step: 100}));
const rate = view(Inputs.range([2, 7], {label: "금리 (%)", step: 0.05, value: product === "디딤돌" ? 3.5 : 4.5}));
```

</div>

```js
const s = scenario({price, cash, income, rate, product});
const curve = d3.range(30000, 120001, 1000).map((p) => ({p, ...scenario({price: p, cash, income, rate, product})}));
const maxAffordable = d3.max(curve.filter((d) => d.gap >= 0 && d.eligibleA), (d) => d.p);
```

<div class="kpis">
  ${card("대출 가능액", won(s.loan), s.loan === s.incomeCap ? "소득 심사(DSR·DTI)가 한도" : "LTV·상한이 한도")}
  ${card("필요 현금", won(s.need), `취득세 ${won(s.tax)} 포함 · 중개수수료 제외`)}
  ${card(s.gap >= 0 ? "현금 여유" : "현금 부족", won(Math.abs(s.gap)), s.gap >= 0 ? "가능" : "부족", s.gap >= 0 ? "down" : "up")}
  ${card("월 상환액", won(s.monthly), `${rate}% · 30년`)}
</div>

${!s.eligibleA ? html`<div class="banner warn">디딤돌은 주택 평가액 6억 원 이하만 가능합니다.</div>` : ""}

<div class="card grid-1">
  <h2>매수가별 필요 현금</h2>
  ${resize((width) => Plot.plot({
    ...plotBase(width),
    x: {label: "매수가", tickFormat: (v) => won(v)},
    y: {grid: true, label: "만 원", tickFormat: (v) => won(v)},
    marks: [
      Plot.areaY(curve, {x: "p", y: "need", fill: COLOR.accent, fillOpacity: 0.12}),
      Plot.lineY(curve, {x: "p", y: "need", stroke: COLOR.accent, strokeWidth: 2, tip: true, title: (d) => `매수가 ${won(d.p)}\n필요 현금 ${won(d.need)}\n대출 ${won(d.loan)} · 월 ${won(d.monthly)}`}),
      Plot.ruleY([cash], {stroke: COLOR.accent2, strokeWidth: 2}),
      Plot.text([cash], {y: (d) => d, frameAnchor: "left", dy: -8, text: () => `보유 현금 ${won(cash)}`, fill: COLOR.accent2, fontSize: 11}),
      Plot.ruleX([price], {stroke: "currentColor", strokeOpacity: 0.4}),
      maxAffordable ? Plot.dot([{p: maxAffordable, need: scenario({price: maxAffordable, cash, income, rate, product}).need}], {x: "p", y: "need", r: 5, fill: COLOR.accent2}) : null
    ]
  }))}
  <p class="note">파란 선 아래가 살 수 있는 구간입니다. ${maxAffordable ? html`이 조건의 최대 매수가는 약 <strong>${won(maxAffordable)}</strong>입니다.` : "이 조건으로는 살 수 있는 가격대가 없습니다."} 법·규정 해석이 아니라 추정치입니다.</p>
</div>
