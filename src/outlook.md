---
title: 가격은 더 오를까?
---

```js
import {num} from "./components/format.js";
const observations = Array.from(await FileAttachment("data/rone.parquet").parquet()).filter((d) => d.region_full === "서울" && ["wk_sale_index", "wk_sale_supply"].includes(d.metric) && Number.isFinite(Number(d.value))).sort((a,b) => new Date(b.date) - new Date(a.date));
const latest = (metric) => observations.find((d) => d.metric === metric);
const price = latest("wk_sale_index"), supply = latest("wk_sale_supply");
```

# 가격은 더 오를까?

<p class="lead">서울 아파트 · 향후 6개월: <strong>판단 유보</strong></p>

<div class="card">
  <h2>현재 견해</h2>
  <p>방향을 판단할 만큼 검토된 전망 조사와 반대 근거가 아직 없습니다. 아래 관측은 전망이나 상승 확률이 아닙니다.</p>
  <p>편집 검토자와 작성 시점: 미지정 · 검토된 전망 발행 전 상태</p>
</div>

<h2>확인된 관측</h2>
<ul>
  <li>한국부동산원 주간 매매가격지수: ${price ? `${num(price.value)} · ${new Date(price.date).toISOString().slice(0,10)}` : "자료 없음"}</li>
  <li>한국부동산원 주간 매매수급지수: ${supply ? `${num(supply.value)} · ${new Date(supply.date).toISOString().slice(0,10)}` : "자료 없음"}</li>
</ul>
<p>두 관측은 서로 다른 지표입니다. 지수 수준을 미래 상승확률이나 개인의 매수 적기로 바꾸지 않습니다. 기준일과 상세 정의는 <a href="./market">시장 지표</a>에서 확인하세요.</p>

<h2>반대·미확인 근거</h2>
<p>검증된 가격전망 조사, 거래 구성의 변화, 공급 자료와 자료의 완결성이 부족합니다. 가격지수의 방향만으로 이 빈칸을 채우지 않습니다.</p>

<h2>다시 살펴볼 조건</h2>
<p>같은 지역·대상·기간의 거래량과 가격 분포가 완결되고, 조사 대상과 문항이 확인된 전망 자료 및 반대 근거가 확보되면 작성자가 견해를 다시 검토합니다.</p>
<p><a href="./compare">거래 분포와 거래량 살펴보기 →</a> · <a href="https://www.reb.or.kr/r-one/">한국부동산원 R-ONE</a></p>
