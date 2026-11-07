---
title: 내 조건으로 보기
---

```js
import {personalScenario} from "./components/personal.js";
```

# 지금 사도 될까? 내 조건으로 보기

<p class="lead">개인이 입력한 가정으로 거래 후 현금과 월 잔여를 계산합니다. 대출 승인이나 적격 판정이 아닙니다.</p>
<p>입력은 이 화면의 메모리에서만 계산되며 새로고침하면 사라집니다. 반환이 불확실한 임대보증금은 보유 현금에 넣지 마세요. 생활비에는 기존·신규 대출상환과 주거유지비를 포함하지 마세요.</p>

<div id="personal-form" class="personal-form">
  <label>집값 (만원)<input name="price" type="number" min="0" required></label>
  <label>사용 가능한 현금 (만원)<input name="cash" type="number" min="0" required></label>
  <label>월 세후 실수령액 (만원)<input name="income" type="number" min="0" required></label>
  <label>매수 후 월 생활비 (만원)<input name="living" type="number" min="0" required></label>
  <label>기존 월 대출상환 (만원)<input name="debt" type="number" min="0" required></label>
  <label>매수 후 월 주거유지비 (만원)<input name="housing" type="number" min="0" required></label>
  <label>가정 대출원금 (만원)<input name="loan" type="number" min="0" required></label>
  <label>가정 연 금리 (%)<input name="rate" type="number" min="0" max="100" step="any" required></label>
  <label>상환기간 (년, 원리금균등)<input name="years" type="number" min="1" max="50" step="1" required></label>
  <label>취득·거래 초기비용 (만원)<input name="cost" type="number" min="0" required></label>
  <label>남길 현금 기준 (만원)<input name="reserve" type="number" min="0" required></label>
  <button type="button" id="personal-calculate">계산하기</button>
</div>
<div id="personal-result" class="card" aria-live="polite">모든 항목을 입력하면 결과를 표시합니다. 해당하지 않으면 0을 입력하세요.</div>
<p>금리 충격은 가정일 뿐 고정금리 계약의 실제 재가격을 뜻하지 않습니다. 은행 심사, 현재 정책과 실제 비용은 별도로 확인하세요.</p>
<p><a href="./complexes">단지 거래 살펴보기 →</a> · <a href="./trades">실거래 보기 →</a></p>

```js
const form = document.querySelector("#personal-form");
const result = document.querySelector("#personal-result");
document.querySelector("#personal-calculate").addEventListener("click", () => {
  const values = Object.fromEntries(Array.from(form.querySelectorAll("input"), (input) => [input.name, input.value]));
  const r = personalScenario(values);
  if (!r) { result.textContent = "입력을 확인하세요. 대출은 집값 이하여야 하며 상환기간은 1–50년입니다."; return; }
  const fmt = (v) => `${new Intl.NumberFormat("ko-KR", {maximumFractionDigits: 2}).format(v)}만원`;
  result.textContent = `거래 후 현금 ${fmt(r.cash)} · 남길 현금 기준 대비 ${fmt(r.cashGap)} · 월 잔여 ${fmt(r.monthly)} · 금리 1%p 상승 시 ${fmt(r.stress1)} · 2%p 상승 시 ${fmt(r.stress2)}`;
});
```
