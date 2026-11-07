---
title: 오늘의 브리핑
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
import {card, heading, insightList, articleList, regionColor} from "./components/ui.js";
const disposeUI = enhanceUI(invalidation);
const insights = await FileAttachment("data/insights.json").json();
const articles = await FileAttachment("data/articles.json").json();
const rone = await FileAttachment("data/rone.parquet").parquet();
```

# 부동산, 무엇을 확인할까요?

<p class="lead">시장 관측과 나의 자금 가정을 구분해 살펴보세요.</p>
<div class="question-grid">
  <a class="card" href="./compare"><strong>지금 사도 될까?</strong><br>내 현금과 월 부담을 가정으로 계산</a>
  <a class="card" href="./outlook"><strong>가격은 더 오를까?</strong><br>판단 유보 · 가격 흐름과 반대 근거 확인</a>
  <a class="card" href="./market#kb-survey"><strong>사람들은 어떻게 느낄까?</strong><br>확인된 시장 지표와 거래 살펴보기</a>
  <a class="card" href="./policy"><strong>정책은 어떻게 받아들일까?</strong><br>공식 원문과 의견 자료 확인 상태</a>
</div>

## 오늘의 시장 관측

<p class="lead">국토교통부 실거래가, 한국부동산원, KB 지표와 최근 기사를 모아 기사·리포트에 바로 쓸 수 있는 문장으로 정리합니다. 문장 옆 <b>복사</b>를 누르면 출처와 기준일까지 함께 복사됩니다.</p>

```js
const byId = new Map(insights.map((d) => [d.id, d]));
const pick = (id, title) => {
  const d = byId.get(id);
  return card(title, d?.value ?? "–", d ? `${d.sub || d.title} · ${d.as_of}` : "데이터 없음", d?.tone ?? "");
};
```

<div class="kpis">
  <div class="kpi-slot">${pick("wk-sale-서울", "서울 아파트값 (주간)")}</div>
  <div class="kpi-slot">${pick("wk_sale_supply-서울", "서울 매매수급지수")}</div>
  <div class="kpi-slot">${pick("volume-11", "서울 월 매매 거래")}</div>
  <div class="kpi-slot">${pick("p84-11", "서울 84㎡ 중위 거래가")}</div>
</div>

```js
const weekly = Array.from(rone).filter((d) => d.metric === "wk_sale_index" && ["서울", "경기", "전국"].includes(d.region_full));
const since = new Date(); since.setFullYear(since.getFullYear() - 3);
const regionsWk = ["서울", "경기", "전국"];
const dates = [...new Set(weekly.filter((d) => new Date(d.date) >= since).map((d) => +new Date(d.date)))].sort((a, b) => a - b);
// 3년 전 첫 주를 100 으로 다시 맞춰서 지역끼리 상승 폭을 비교한다
const rebased = regionsWk.map((r) => {
  const s = new Map(weekly.filter((d) => d.region_full === r).map((d) => [+new Date(d.date), d.value]));
  const base = s.get(dates[0]);
  return {name: r, data: dates.map((t) => (s.has(t) && base ? s.get(t) / base * 100 : null))};
});
```

<div class="grid-2">
  <div class="card">
    ${heading("핵심 인사이트", "DB에 쌓인 실거래·지표에서 매번 다시 계산한 문장입니다. 실거래 월 통계는 신고 기한(계약 후 30일)이 지난 가장 최근 달을 기준으로 합니다.")}
    ${insightList(insights.filter((d) => d.group !== "뉴스"))}
  </div>
  <div>
    <div class="card">
      ${heading("아파트값 3년 흐름 (3년 전 = 100)", "한국부동산원 주간 아파트 매매가격지수를 3년 전 첫 주 100 기준으로 다시 맞춘 값입니다. 같은 집의 가격 변화를 추정한 지수라, 실거래 중위가와 다르게 움직일 수 있습니다.")}
      <div class="chart-slot">${chart({
        xAxis: {data: dates.map((t) => new Date(t).toISOString().slice(0, 10))}, yAxis: {name: "지수", scale: true},
        series: rebased.map((s, i) => ({...s, type: "line", itemStyle: {color: regionColor(s.name)}}))
      }, invalidation)}</div>
    </div>
    <div class="card" style="margin-top: var(--gap)">
      ${heading("이번 주 기사 흐름", "최근 7일 수집한 기사 제목에 많이 나온 주제어입니다.")}
      ${insightList(insights.filter((d) => d.group === "뉴스"))}
    </div>
  </div>
</div>

<div class="grid-2">
  <div class="card">
    ${heading("최신 기사", "언론사 RSS와 Google 뉴스 검색에서 모은 헤드라인입니다. 저작권 때문에 제목과 링크만 보여 줍니다.")}
    ${articleList(articles.filter((a) => a.category === "news").slice(0, 10))}
    <p class="note"><a href="./news">기사·리포트 전체 보기 →</a></p>
  </div>
  <div class="card">
    ${heading("리포트 · 시장 동향", "한국부동산원·KB·연구기관의 동향 발표와 전망 보고서를 다룬 기사입니다.")}
    ${articleList(articles.filter((a) => a.category === "report").slice(0, 10))}
    <p class="note"><a href="./reports/">내 리포트 쓰기 →</a></p>
  </div>
</div>
