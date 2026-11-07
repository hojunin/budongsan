---
title: 내 조건으로 보기
---

```js
import {personalScenario} from "./components/personal.js";
import {num} from "./components/format.js";
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
  <label>별도 임대보증금 (만원, 선택)<input name="deposit" type="number" min="0"></label>
  <label><span>잔금 전 보증금 반환을 확실히 가정</span><input name="depositBefore" type="checkbox"></label>
  <label>월 실수령 소득 감소 가정 (%, 선택)<input name="incomeDrop" type="number" min="0" max="100" step="any"></label>
  <label>집값 하락 가정 (%, 선택)<input name="priceDrop" type="number" min="0" max="100" step="any"></label>
  <label>남길 현금 기준 (만원)<input name="reserve" type="number" min="0" required></label>
  <button type="button" id="personal-calculate">계산하기</button>
</div>
<div id="personal-result" class="card" aria-live="polite">모든 항목을 입력하면 결과를 표시합니다. 해당하지 않으면 0을 입력하세요.</div>
<details class="scenario-export">
  <summary>선택한 결과 내보내기</summary>
  <p>선택한 항목만 미리 본 후 파일로 저장합니다. 기본 선택은 없으며, 저장한 파일은 개인 정보가 포함된 출력물입니다.</p>
  <label><input type="checkbox" data-scenario-field="cash"> 거래 후 현금</label>
  <label><input type="checkbox" data-scenario-field="monthly"> 월 잔여</label>
  <label><input type="checkbox" data-scenario-field="stress1"> 금리 +1%p 월 잔여</label>
  <label><input type="checkbox" data-scenario-field="stress2"> 금리 +2%p 월 잔여</label>
  <label><input type="checkbox" data-scenario-field="assessedPrice"> 가격 하락 후 평가액</label>
  <label><input type="checkbox" data-scenario-field="assessedEquity"> 대출 차감 평가자산</label>
  <button type="button" id="scenario-preview">선택 항목 미리보기</button>
  <p id="scenario-preview-text" aria-live="polite">결과 계산 후 최대 3개 항목을 선택하세요.</p>
  <button type="button" id="scenario-download" disabled>미리 본 항목 저장</button>
</details>

<p>금리 충격은 가정일 뿐 고정금리 계약의 실제 재가격을 뜻하지 않습니다. 은행 심사, 현재 정책과 실제 비용은 별도로 확인하세요.</p>
<p><a href="./complexes">단지 거래 살펴보기 →</a> · <a href="./trades">실거래 보기 →</a></p>

```js
const form = document.querySelector("#personal-form");
const result = document.querySelector("#personal-result");
const exportSection = document.querySelector(".scenario-export");
const previewText = document.querySelector("#scenario-preview-text");
const download = document.querySelector("#scenario-download");
let latest = null, previewFields = null;
const clearPreview = () => { previewFields = null; download.disabled = true; previewText.textContent = "결과 계산 후 최대 3개 항목을 선택하세요."; };
form.addEventListener("input", () => { latest = null; clearPreview(); result.textContent = "입력이 변경됐습니다. 다시 계산해 주세요."; });
exportSection.addEventListener("input", clearPreview);
document.querySelector("#scenario-preview").addEventListener("click", () => {
  const returned = form.querySelector('[name="depositBefore"]').checked;
  const priceDrop = form.querySelector('[name="priceDrop"]').value;
  const labels = {cash:returned ? "거래 후 현금 (보증금 잔금 전 반환 가정)" : "거래 후 현금 (보증금 제외)", monthly:"월 잔여", stress1:"금리 +1%p 월 잔여", stress2:"금리 +2%p 월 잔여", assessedPrice:`집값 ${num(priceDrop)}% 하락 후 평가액`, assessedEquity:`집값 ${num(priceDrop)}% 하락 후 대출 차감 평가자산`};
  const keys = Array.from(exportSection.querySelectorAll("[data-scenario-field]:checked"), (input) => input.dataset.scenarioField);
  if (!latest || !keys.length || keys.length > 3 || keys.some((key) => latest[key] == null)) { clearPreview(); previewText.textContent = "계산된 결과에서 1–3개 항목을 선택하세요."; return; }
  previewFields = keys.map((key) => ({label:labels[key], value:latest[key], unit:"만원"}));
  previewText.textContent = previewFields.map((field) => `${field.label}: ${num(field.value)}${field.unit}`).join(" · ");
  download.disabled = false;
});
download.addEventListener("click", () => {
  if (!previewFields) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify({include:true, fields:previewFields}, null, 2)], {type:"application/json"}));
  const a = document.createElement("a"); a.href = url; a.download = "personal-scenario.json"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
document.querySelector("#personal-calculate").addEventListener("click", () => {
  const inputs = Array.from(form.querySelectorAll("input"));
  const invalid = inputs.find((input) => !input.checkValidity());
  if (invalid) { result.textContent = `${invalid.closest("label").textContent.trim()} 항목을 확인하세요.`; invalid.focus(); return; }
  const values = Object.fromEntries(inputs.map((input) => [input.name, input.type === "checkbox" ? input.checked : input.value]));
  const r = personalScenario(values);
  if (!r) { latest = null; clearPreview(); result.textContent = "입력을 확인하세요. 반환을 가정했다면 보증금을 입력하고, 대출은 집값 이하, 기간은 1–50년이어야 합니다."; return; }
  latest = r; clearPreview();
  const fmt = (v) => `${num(v)}만원`;
  result.replaceChildren();
  const primary = document.createElement("p");
  primary.className = "personal-primary";
  primary.textContent = `거래 후 현금 ${fmt(r.cash)} · 월 잔여 ${fmt(r.monthly)}`;
  const reserve = document.createElement("p");
  reserve.textContent = `남길 현금 기준 대비 ${fmt(r.cashGap)}`;
  const table = document.createElement("table");
  table.setAttribute("aria-label", "가정별 월 잔여");
  for (const [label, value] of [["현재 가정", r.monthly], ["금리 +1%p", r.stress1], ["금리 +2%p", r.stress2], ...(r.incomeStress == null ? [] : [["소득 감소", r.incomeStress]])]) {
    const row = table.insertRow(), th = document.createElement("th"), td = row.insertCell();
    th.scope = "row"; th.textContent = label; td.textContent = fmt(value); row.prepend(th);
  }
  result.append(primary, reserve, table);
  if (r.assessedPrice != null) {
    const valuation = document.createElement("p");
    valuation.textContent = `가격 하락 가정 평가액 ${fmt(r.assessedPrice)} · 대출 차감 평가자산 ${fmt(r.assessedEquity)}. 처분비용 제외, 즉시 현금 손실이 아닙니다.`;
    result.append(valuation);
  }
});
```
