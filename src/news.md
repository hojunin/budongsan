---
title: 뉴스·리포트
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
import {heading, articleList, PALETTE} from "./components/ui.js";
const disposeUI = enhanceUI(invalidation);
const articles = (await FileAttachment("data/articles.json").json()).map((a) => ({...a, day: a.published?.slice(0, 10)}));
```

# 뉴스·리포트

<p class="lead">언론사 RSS와 Google 뉴스 검색으로 매주 모은 부동산 기사와, 한국부동산원·KB·연구기관의 동향·전망 보고서를 다룬 기사입니다. 저작권을 지키려고 제목·언론사·날짜·원문 링크만 보여 줍니다.</p>

```js
const KEYWORDS = ["재건축", "재개발", "전세", "월세", "청약", "분양", "대출", "금리", "DSR", "공급", "입주", "토지거래허가", "규제", "신고가", "갭투자", "미분양", "공시가", "보유세", "양도세", "GTX"];
const sources = [...d3.rollup(articles, (v) => v.length, (a) => a.source)].sort((a, b) => b[1] - a[1]).map(([s]) => s);
```

<div class="filters">
<div class="filter-field filter-field--standard">

```js
const category = view(Inputs.radio(["전체", "기사", "리포트·동향"], {label: "분류", value: "전체"}));
```

</div>
<div class="filter-field filter-field--standard">

```js
const days = view(Inputs.radio([7, 14, 30, 60], {label: "기간", value: 14, format: (d) => `${d}일`}));
```

</div>
<div class="filter-field filter-field--standard">

```js
const source = view(Inputs.select(["전체", ...sources], {label: "언론사", value: "전체"}));
```

</div>
<div class="filter-field filter-field--standard">

```js
const q = view(Inputs.text({label: "제목 검색", placeholder: "예: 재건축, 강남, 전세사기", autocomplete: "off"}));
```

</div>
</div>

```js
const cutoff = new Date(); cutoff.setDate(cutoff.getDate() - days);
const cutoffDay = cutoff.toISOString().slice(0, 10);
const filtered = articles.filter((a) => (a.day ?? "") >= cutoffDay
  && (category === "전체" || (category === "기사" ? a.category === "news" : a.category === "report"))
  && (source === "전체" || a.source === source)
  && (!q || a.title.toLowerCase().includes(q.toLowerCase())));
const counts = KEYWORDS.map((k) => [k, filtered.filter((a) => a.title.includes(k)).length]).filter(([, n]) => n).sort((a, b) => b[1] - a[1]);
const topK = counts.slice(0, 5).map(([k]) => k);
const dayList = d3.timeDays(cutoff, new Date()).map((d) => d3.timeFormat("%Y-%m-%d")(d));
```

<div class="grid-2">
  <div class="card">
    ${heading(`주제어별 기사 수 — 최근 ${days}일`, "수집한 기사 제목에 주제어가 몇 번 나왔는지 셉니다. 같은 기사가 여러 주제어에 걸릴 수 있습니다.")}
    <div class="keyword-chips">${counts.slice(0, 12).map(([k, n]) => html`<span class="chip">${k} ${n}</span>`)}</div>
    <div class="chart-slot">${chart({
      xAxis: {data: dayList}, yAxis: {name: "건"},
      series: topK.map((k, i) => ({name: k, type: "line", itemStyle: {color: PALETTE[i]},
        data: dayList.map((day) => filtered.filter((a) => a.day === day && a.title.includes(k)).length)}))
    }, invalidation)}</div>
  </div>
  <div class="card">
    ${heading("언론사별 기사 수", "현재 조건에 맞는 기사를 언론사별로 셉니다. 상위 12곳만 보여 줍니다.")}
    <div class="chart-slot">${chart({
      xAxis: {type: "value"}, yAxis: {type: "category", inverse: true, data: d3.rollups(filtered, (v) => v.length, (a) => a.source).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([s]) => s), splitLine: {show: false}},
      tooltip: {trigger: "axis", axisPointer: {type: "shadow"}}, dataZoom: [], grid: {left: 8, right: 16, top: 40, bottom: 16, containLabel: true},
      series: [{name: "기사 수", type: "bar", barMaxWidth: 16, itemStyle: {borderRadius: [0, 4, 4, 0]},
        data: d3.rollups(filtered, (v) => v.length, (a) => a.source).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([, n]) => n)}]
    }, invalidation)}</div>
  </div>
</div>

<div class="card grid-1">
  ${heading(`기사 목록 — ${filtered.length.toLocaleString("ko-KR")}건`, "최신순입니다. 제목을 누르면 원문이 새 창으로 열립니다. 한 번에 150건까지 보여 줍니다.")}
  ${articleList(filtered.slice(0, 150), {empty: "조건에 맞는 기사가 없습니다"})}
</div>
