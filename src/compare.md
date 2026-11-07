---
title: 매매와 임대 비교
---

```js
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
import {heading} from "./components/ui.js";
const disposeUI = enhanceUI(invalidation);
import {distribution, rentCost, periodComparison, completedWindow, withinSelectionLimit, areaRange, rentPoint} from "./components/graphics.js";
import {won, num, pct} from "./components/format.js";
const trades = Array.from(await FileAttachment("data/trades.parquet").parquet());
const rents = Array.from(await FileAttachment("data/rents.parquet").parquet());
const rone = Array.from(await FileAttachment("data/rone.parquet").parquet());
```

# 같은 돈, 다른 선택

<p class="lead">과거 거래의 가운데 50%와 집값 상한을 비교합니다. 현재 매물이나 구매 가능성을 뜻하지 않습니다.</p>
<p>최근 6개월, 취소 제외. 수집 완결성과 단지 식별은 미확인 상태여서 결과는 탐색용입니다.</p>

```js
const {start, end} = completedWindow();
const within = (d) => { const t = new Date(d.deal_date); return t >= start && t < end; };
const eligible = trades.filter((d) => d.is_sample === false && !d.canceled && within(d) && d.price > 0 && d.area > 0);
const regions = [...new Set(eligible.map((d) => d.sgg_name))].sort((a, b) => a.localeCompare(b, "ko"));
```

<div class="filters compare-filters">

<div class="compare-filter-slot">

```js
const region = view(Inputs.select(regions, {label: "지역", disabled: !regions.length}));
```

</div>

<div class="compare-filter-slot">

```js
const band = view(Inputs.select(["59", "74", "84", "100"], {label: "면적대 (㎡)", value: "84"}));
```

</div>

```js
const groups = new Map();
for (const d of eligible.filter((d) => d.sgg_name === region && d.band === band)) {
  const old = groups.get(d.complex_key);
  groups.set(d.complex_key, {label:`${d.apt} · ${d.umd}`, n:(old?.n ?? 0) + 1});
}
const candidates = [...groups].sort((a, b) => b[1].n - a[1].n || a[1].label.localeCompare(b[1].label, "ko")).map(([id, v]) => [id, `${v.label} · ${v.n}건`]);
```

<div class="compare-filter-slot compare-filter-multi">

```js
const selected = view(Inputs.select(candidates.map(([id]) => id), {label: "단지 (최대 3곳)", multiple: 3, format: (id) => candidates.find(([key]) => key === id)?.[1], value: candidates.slice(0, 2).map(([id]) => id), disabled: !candidates.length}));
```

</div>

<div class="compare-filter-slot">

```js
const budget = view(Inputs.number({label: "집값 상한 (만원)", min: 0, value: 100000, step: 1000}));
```

</div>

</div>

```js
const budgetOk = Number.isFinite(budget) && budget >= 0;
const selectionOk = withinSelectionLimit(selected);
const summaries = (selectionOk ? selected : []).map((key) => {
  const rows = eligible.filter((d) => d.complex_key === key && d.band === band);
  return {key, name: candidates.find(([id]) => id === key)?.[1], rows, stats: budgetOk ? distribution(rows.map((d) => Number(d.price)), budget) : null};
});
const valid = summaries.filter((d) => d.stats);
```

<p class="compare-period">${`${selectionOk ? "" : "단지는 최대 3곳까지 선택하세요. "}${budgetOk ? "" : "집값 상한에 0 이상의 유한한 값을 입력하세요. "}기간 ${start.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만 · 단위 만원 · 각 단지 n<5는 분포를 숨깁니다. n 5–19는 적은 표본입니다.`}</p>
<div class="card">${heading("단지별 거래 분포", "선은 25–75분위, 점은 중간값, 세로선은 집값 상한입니다. 같은 축이며 최근 6개월 실거래를 나타냅니다.")}<div class="chart-slot">${chart({xAxis:{type:"value", name:"만원", min:0, max:Math.max(budgetOk ? Number(budget) : 0, ...valid.map((d) => d.stats.q3), 1) * 1.1}, yAxis:{type:"category", data:valid.map((d) => d.name)}, series:[{name:"가운데 50%와 중간값", type:"custom", encode:{x:[1,2,3], y:0}, renderItem:(params, api) => { const y = api.coord([0, api.value(0)])[1], a = api.coord([api.value(1), api.value(0)])[0], b = api.coord([api.value(2), api.value(0)])[0], m = api.coord([api.value(3), api.value(0)])[0]; return {type:"group", children:[{type:"line", shape:{x1:a,y1:y,x2:b,y2:y}, style:{stroke:matchMedia("(prefers-color-scheme: dark)").matches ? "#64d4c9" : "#087f80",lineWidth:8}},{type:"circle",shape:{cx:m,cy:y,r:6},style:{fill:matchMedia("(prefers-color-scheme: dark)").matches ? "#f6cc8a" : "#173c46"}}]}; }, data:valid.map((d,i) => [i,d.stats.q1,d.stats.q3,d.stats.median]), markLine:{symbol:"none", data:budgetOk ? [{xAxis:Number(budget), label:{formatter:"집값 상한"}}] : []}}]}, invalidation)}</div></div>

${summaries.length ? html`<table class="compare-table" tabindex="0"><thead><tr><th>단지</th><th>표본</th><th>Q25 / 중간 / Q75</th><th>상한 이하</th></tr></thead><tbody>${summaries.map((d) => html`<tr><th>${d.name}</th><td data-label="표본">${d.rows.length}건${d.rows.length >= 5 && d.rows.length < 20 ? " · 적은 표본" : ""}</td><td data-label="Q25 / 중간 / Q75">${d.stats ? `${won(d.stats.q1)} / ${won(d.stats.median)} / ${won(d.stats.q3)}` : "표본 부족"}</td><td data-label="상한 이하">${d.stats ? `${d.stats.below}건 (${num(d.stats.share*100)}%)` : "–"}</td></tr>`)}</tbody></table>` : html`<p>조건에 맞는 실제 거래가 없습니다. 합성 표본은 표시하지 않습니다.</p>`}

```js
const downloadEvidence = async (template, title, evidence) => {
  const attachments = {"molit-trades":FileAttachment("data/trades.parquet"), "molit-rents":FileAttachment("data/rents.parquet"), "rone":FileAttachment("data/rone.parquet")};
  const hashes = {};
  for (const source of new Set(evidence.map((e) => e.source_id))) {
    const bytes = await attachments[source].arrayBuffer();
    hashes[source] = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (b) => b.toString(16).padStart(2, "0")).join("");
  }
  for (const e of evidence) e.release_id = `sha256:${hashes[e.source_id]}`;
  const blob = new Blob([JSON.stringify({template, title, summary:"검토 후 작성", evidence}, null, 2)], {type:"application/json"});
  const url = URL.createObjectURL(blob), a = document.createElement("a");
  a.href = url; a.download = `${template}-evidence-draft.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
const jeonseEvidence = () => identityConfirmed.length ? summaries.flatMap((d,i) => {
  const rows = matchedJeonse(d.key), stat = distribution(rows.map((r) => Number(r.deposit)), 0);
  return stat ? [{id:`jeonse-${i+1}`,kind:"jeonse_distribution",source_id:"molit-rents",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${start.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만`,scope:`${region} ${d.name} ${band}㎡대 전세`,unit:"만원",sample_n:stat.n,source_url:"https://rt.molit.go.kr/",query_spec:{complex_key:d.key,band,start:start.toISOString().slice(0,10),end_exclusive:end.toISOString().slice(0,10)},facts:[{label:"Q25",value:stat.q1},{label:"중간값",value:stat.median},{label:"Q75",value:stat.q3}]}] : [];
}) : [];
const otherAreaEvidence = () => summaries.flatMap((d,i) => ["59","84"].filter((b) => b !== band).flatMap((b) => {
  const rows = eligible.filter((r) => r.complex_key === d.key && r.band === b);
  const stat = distribution(rows.map((r) => Number(r.price)), budget), area = stat ? areaRange(rows.map((r) => Number(r.area))) : null;
  return stat && area ? [{id:`area-${i+1}-${b}`,kind:"trade_distribution",source_id:"molit-trades",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${start.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만`,scope:`${region} ${d.name} ${b}㎡대`,unit:"만원",sample_n:stat.n,source_url:"https://rt.molit.go.kr/",query_spec:{complex_key:d.key,band:b,start:start.toISOString().slice(0,10),end_exclusive:end.toISOString().slice(0,10),canceled_excluded:true,budget,area_min:area.min,area_max:area.max},facts:[{label:"Q25",value:stat.q1},{label:"중간값",value:stat.median},{label:"Q75",value:stat.q3}]}] : [];
}));
const saveEvidence = () => downloadEvidence("buyer", "매수 후보 비교", [...valid.map((d, i) => ({id:`trade-${i+1}`, kind:"trade_distribution", source_id:"molit-trades", is_sample:false, rights:"unknown", coverage_verified:false, identity_verified:false, reviewed_by:"", period:`${start.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만`, scope:`${region} ${d.name} ${band}㎡대`, unit:"만원", sample_n:d.stats.n, source_url:"https://rt.molit.go.kr/", query_spec:{complex_key:d.key, band, start:start.toISOString().slice(0,10), end_exclusive:end.toISOString().slice(0,10), canceled_excluded:true, budget, area_min:areaRange(d.rows.map((r) => Number(r.area)))?.min, area_max:areaRange(d.rows.map((r) => Number(r.area)))?.max}, facts:[{label:"Q25",value:d.stats.q1},{label:"중간값",value:d.stats.median},{label:"Q75",value:d.stats.q3}]})), ...otherAreaEvidence(), ...jeonseEvidence()]);
```

${html`<button type="button" disabled=${!valid.length} onclick=${saveEvidence}>선택 분포를 근거 초안으로 저장</button>`}
<p>저장되는 초안은 완결성·단지 식별·이용권 미확인 상태입니다. 검토자가 확인하기 전 리포트 패키지 생성이 차단됩니다. 집값 상한은 입력 조건으로만 저장됩니다.</p>

## 같은 지역의 가격과 거래

```js
const previousEnd = new Date(end); previousEnd.setUTCFullYear(previousEnd.getUTCFullYear() - 1);
const currentStart = new Date(end); currentStart.setUTCMonth(currentStart.getUTCMonth() - 3);
const previousStart = new Date(previousEnd); previousStart.setUTCMonth(previousStart.getUTCMonth() - 3);
const regionRows = trades.filter((d) => d.is_sample === false && !d.canceled && d.sgg_name === region && d.band === band && d.price > 0 && d.area > 0);
const unitPrices = (from, to) => regionRows.filter((d) => new Date(d.deal_date) >= from && new Date(d.deal_date) < to).map((d) => Number(d.price) / Number(d.area));
const change = periodComparison(unitPrices(currentStart, end), unitPrices(previousStart, previousEnd));
```

<p>최근 ${currentStart.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만 · 전년 ${previousStart.toISOString().slice(0,10)} 이상 ~ ${previousEnd.toISOString().slice(0,10)} 미만 · 출처 국토교통부 실거래.</p>
<div class="card">${heading("㎡당 거래가격 분포", "각 기간 거래의 25–75분위와 중간값입니다. 두 기간 모두 30건 이상일 때 표시합니다.")}<div class="chart-slot">${chart({xAxis:{type:"value", name:"만원/㎡", min:0}, yAxis:{type:"category", data:["전년 같은 기간", "최근 3개월"]}, series:[{name:"㎡당 거래가격 가운데 50%", type:"custom", encode:{x:[1,2,3], y:0}, renderItem:(params, api) => {const y = api.coord([0, api.value(0)])[1], a = api.coord([api.value(1), api.value(0)])[0], b = api.coord([api.value(2), api.value(0)])[0], m = api.coord([api.value(3), api.value(0)])[0]; return {type:"group", children:[{type:"line",shape:{x1:a,y1:y,x2:b,y2:y},style:{stroke:matchMedia("(prefers-color-scheme: dark)").matches ? "#64d4c9" : "#087f80",lineWidth:8}},{type:"circle",shape:{cx:m,cy:y,r:6},style:{fill:matchMedia("(prefers-color-scheme: dark)").matches ? "#f6cc8a" : "#173c46"}}]};}, data:change ? [[0,change.previous.q1,change.previous.q3,change.previous.median],[1,change.current.q1,change.current.q3,change.current.median]] : []}]}, invalidation)}</div></div>

<div class="card">${heading("가격과 거래의 동행", "가로축은 거래수 변화, 세로축은 ㎡당 중간 거래가격 변화입니다. 원점은 변화 없음이며 각 기간 표본이 30건 이상일 때만 표시합니다.")}<div class="chart-slot">${chart({xAxis:{type:"value", name:"거래수 변화 (%)", min:change ? -Math.max(1,Math.abs(change.volumeChange*100)*1.2) : -1, max:change ? Math.max(1,Math.abs(change.volumeChange*100)*1.2) : 1}, yAxis:{type:"value", name:"㎡당 중간가격 변화 (%)", min:change ? -Math.max(1,Math.abs(change.priceChange*100)*1.2) : -1, max:change ? Math.max(1,Math.abs(change.priceChange*100)*1.2) : 1}, series:[{name:region, type:"scatter", symbolSize:14, data:change ? [[change.volumeChange*100, change.priceChange*100]] : [], markLine:{symbol:"none", label:{show:false}, data:[{xAxis:0},{yAxis:0}]}}]}, invalidation)}</div><p>왼쪽은 거래 감소, 오른쪽은 증가 · 아래는 가격 하락, 위는 상승입니다.</p></div>

${change ? html`<table class="compare-table" tabindex="0"><thead><tr><th>지역·면적대</th><th>거래수 변화</th><th>㎡당 중간가격 변화</th><th>각 기간 표본</th></tr></thead><tbody><tr><th>${region} · ${band}㎡대</th><td data-label="거래수 변화">${pct(change.volumeChange)}</td><td data-label="㎡당 중간가격 변화">${pct(change.priceChange)}</td><td data-label="각 기간 표본">전년 ${change.previous.n}건 · 최근 ${change.current.n}건</td></tr></tbody></table>` : html`<p>두 기간 표본이 각각 30건 미만이거나 자료가 없으면 4분면을 비웁니다.</p>`}

${change ? html`<div class="card"><p>최근 3개월 거래 ${change.current.n}건 · 전년 같은 기간 ${change.previous.n}건. 거래 수 ${pct(change.volumeChange)}, ㎡당 중간 거래가격 ${pct(change.priceChange)} 변화.</p><p>㎡당 가운데 50%: 전년 ${won(change.previous.q1)}–${won(change.previous.q3)}, 최근 ${won(change.current.q1)}–${won(change.current.q3)}. 거래 구성 변화가 포함되며 같은 집의 가격 변화가 아닙니다.</p><p>중간값 대비 가운데 50% 구간 폭: 전년 ${change.previousSpread == null ? "–" : pct(change.previousSpread)}, 최근 ${change.currentSpread == null ? "–" : pct(change.currentSpread)} · 차이 ${change.spreadDifference == null ? "–" : `${num(change.spreadDifference*100)}%p`}. 거래표본의 분산이며 가격 전망이 아닙니다.</p></div>` : html`<p>두 기간의 유효 거래가 각각 30건 이상이어야 비교합니다. 표본이 부족하거나 자료가 없습니다.</p>`}

```js
const provinceCode = regionRows[0]?.sgg?.slice(0,2);
const province = provinceCode === "11" ? "서울" : provinceCode === "41" ? "경기" : null;
const latestRone = (metric) => {
  const rows = rone.filter((d) => d.metric === metric && d.value != null && Number.isFinite(Number(d.value)));
  const exact = rows.filter((d) => d.region === region);
  const background = rows.filter((d) => d.region_full === province);
  return (exact.length ? exact : background).sort((a,b) => new Date(b.date) - new Date(a.date))[0];
};
const completedMonthStart = new Date(end); completedMonthStart.setUTCMonth(completedMonthStart.getUTCMonth()-1);
const monthRows = regionRows.filter((d) => new Date(d.deal_date) >= completedMonthStart && new Date(d.deal_date) < end);
const regionalSgg = new Set(trades.filter((d) => d.is_sample === false && d.sgg_name === region).map((d) => d.sgg));
const regionalJeonse = rents.filter((d) => d.is_sample === false && within(d) && d.band === band && d.jeonse === true && d.monthly != null && Number(d.monthly) === 0 && Number(d.deposit) > 0 && regionalSgg.has(d.sgg));
const jeonseStats = distribution(regionalJeonse.map((d) => Number(d.deposit)), 0);
const weeklyEvidence = change ? [
  ...[{id:"previous", stats:change.previous, from:previousStart, to:previousEnd}, {id:"current", stats:change.current, from:currentStart, to:end}].map(({id,stats,from,to}) => ({id,kind:"trade_distribution",source_id:"molit-trades",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${from.toISOString().slice(0,10)} 이상 ~ ${to.toISOString().slice(0,10)} 미만`,scope:`${region} ${band}㎡대`,unit:"만원/㎡",sample_n:stats.n,source_url:"https://rt.molit.go.kr/",query_spec:{region,band,canceled_excluded:true},facts:[{label:"Q25",value:stats.q1},{label:"중간값",value:stats.median},{label:"Q75",value:stats.q3}]})),
  {id:"price-volume-change",kind:"change_comparison",source_id:"molit-trades",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${previousStart.toISOString().slice(0,10)}~${previousEnd.toISOString().slice(0,10)} / ${currentStart.toISOString().slice(0,10)}~${end.toISOString().slice(0,10)} (종료일 제외)`,scope:`${region} ${band}㎡대`,unit:"%",sample_n:change.current.n,source_url:"https://rt.molit.go.kr/",query_spec:{region,band,baseline_n:change.previous.n,current_n:change.current.n,formula:"동일 면적대 양기간 거래수·㎡당 중간값 변화"},chart_spec:{type:"quadrant",x:"거래수 변화",y:"㎡당 중간가격 변화"},facts:[{label:"거래수 변화",value:change.volumeChange*100},{label:"㎡당 중간가격 변화",value:change.priceChange*100}]},
  ...[{id:"spread-previous",stats:change.previous,spread:change.previousSpread,from:previousStart,to:previousEnd},{id:"spread-current",stats:change.current,spread:change.currentSpread,from:currentStart,to:end}].filter((v) => v.spread != null).map(({id,stats,spread,from,to}) => ({id,kind:"relative_spread",source_id:"molit-trades",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${from.toISOString().slice(0,10)} 이상 ~ ${to.toISOString().slice(0,10)} 미만`,scope:`${region} ${band}㎡대`,unit:"%",sample_n:stats.n,source_url:"https://rt.molit.go.kr/",query_spec:{region,band,reference_id:id === "spread-previous" ? "previous" : "current",formula:"(Q75-Q25)/중간값"},facts:[{label:"중간값 대비 구간 폭",value:spread*100}]})),
  ...(change.spreadDifference == null ? [] : [{id:"spread-change",kind:"relative_spread_change",source_id:"molit-trades",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${previousStart.toISOString().slice(0,10)}~${previousEnd.toISOString().slice(0,10)} / ${currentStart.toISOString().slice(0,10)}~${end.toISOString().slice(0,10)} (종료일 제외)`,scope:`${region} ${band}㎡대`,unit:"%p",sample_n:change.current.n,source_url:"https://rt.molit.go.kr/",query_spec:{region,band,baseline_n:change.previous.n,current_n:change.current.n,formula:"두 기간 상대 구간 폭의 차이"},facts:[{label:"상대 구간 폭 변화",value:change.spreadDifference*100}]}]),
  ...[["wk_sale_index","price_index","매매가격지수"],["wk_sale_supply","sentiment_index","매매수급지수"]].flatMap(([metric,kind,label]) => {const d=latestRone(metric); return d ? [{id:kind,kind,source_id:"rone",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:new Date(d.date).toISOString().slice(0,10),scope:`${d.region_full} · ${label}${d.region === region ? "" : " (광역 배경)"}`,unit:d.unit || "지수",sample_n:null,source_url:"https://www.reb.or.kr/r-one/",query_spec:{metric,cycle:"주간"},facts:[{label,value:Number(d.value)}]}] : []; }),
  ...(monthRows.length ? [{id:"volume",kind:"trade_volume",source_id:"molit-trades",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${completedMonthStart.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만`,scope:`${region} ${band}㎡대`,unit:"건",sample_n:monthRows.length,source_url:"https://rt.molit.go.kr/",query_spec:{region,band,canceled_excluded:true},facts:[{label:"매매 거래",value:monthRows.length}]}] : []),
  ...(jeonseStats ? [{id:"regional-jeonse",kind:"jeonse_distribution",source_id:"molit-rents",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:`${start.toISOString().slice(0,10)} 이상 ~ ${end.toISOString().slice(0,10)} 미만`,scope:`${region} ${band}㎡대 전세`,unit:"만원",sample_n:jeonseStats.n,source_url:"https://rt.molit.go.kr/",query_spec:{region,band},facts:[{label:"Q25",value:jeonseStats.q1},{label:"중간값",value:jeonseStats.median},{label:"Q75",value:jeonseStats.q3}]}] : [])
] : [];
const saveWeekly = () => downloadEvidence("weekly", "거래와 가격 변화", weeklyEvidence);
```

${html`<button type="button" disabled=${!change} onclick=${saveWeekly}>기간 비교를 근거 초안으로 저장</button>`}

## 같은 이름의 면적대 비교

```js
const areaSeries = (selectionOk ? selected : []).map((key) => ({name:candidates.find(([id]) => id === key)?.[1], type:"line", showSymbol:true, data:["59","84"].map((b) => distribution(eligible.filter((d) => d.complex_key === key && d.band === b).map((d) => Number(d.price)), 0)?.median ?? null)}));
```

<div class="card">${heading("면적대별 중간 거래가격", "같은 이름으로 묶인 거래를 비교합니다. 각 면적대 n<5는 값을 비우며 동일 단지인지는 주소 확인이 필요합니다.")}<div class="chart-slot">${chart({xAxis:{type:"category", data:["59㎡대", "84㎡대"]}, yAxis:{type:"value", name:"만원", scale:true}, series:areaSeries}, invalidation)}</div></div>

${selectionOk && selected.length ? html`<table class="compare-table" tabindex="0"><thead><tr><th>단지명 · 면적대</th><th>표본</th><th>실제 전용면적 범위</th><th>중간 거래가격</th><th>㎡당 중간가격</th></tr></thead><tbody>${selected.flatMap((key) => ["59", "84"].map((b) => {const rows = eligible.filter((d) => d.complex_key === key && d.band === b); const total = distribution(rows.map((d) => Number(d.price)), 0); const unit = distribution(rows.map((d) => Number(d.price) / Number(d.area)), 0); const area = total ? areaRange(rows.map((d) => Number(d.area))) : null; return html`<tr><th>${candidates.find(([id]) => id === key)?.[1]} · ${b}㎡대</th><td data-label="표본">${rows.length}건${rows.length >= 5 && rows.length < 20 ? " · 적은 표본" : ""}</td><td data-label="실제 전용면적 범위">${area ? `${num(area.min)}–${num(area.max)}㎡` : "표본 부족"}</td><td data-label="중간 거래가격">${total ? won(total.median) : "표본 부족"}</td><td data-label="㎡당 중간가격">${unit ? won(unit.median) : "표본 부족"}</td></tr>`;}))}</tbody></table>` : html`<p>단지를 선택하세요.</p>`}
<p>단지명과 동 이름만으로 묶은 탐색 결과입니다. 동일 단지인지 주소·식별자를 확인하기 전 확정 비교나 발행 근거로 사용할 수 없습니다.</p>

## 매매와 전세 거래집단

<p>이름 기반 연결은 동일 단지를 보장하지 않습니다. 주소와 단지 식별자를 직접 대조한 경우에만 집단 중간값을 비교하세요. 두 거래집단의 비율은 보증금 안전성이나 같은 집의 전세가율이 아닙니다.</p>

```js
const identityConfirmed = view(Inputs.checkbox(["주소와 단지 식별자를 직접 대조했습니다"], {label:`단지 확인 (${selected.length}곳 · ${band}㎡대)`}));
const matchedJeonse = (key) => rents.filter((d) => d.is_sample === false && within(d) && d.band === band && d.complex_key === key && d.jeonse === true && d.monthly != null && Number(d.monthly) === 0 && Number(d.deposit) > 0);
```

```js
const saleRentSeries = identityConfirmed.length ? summaries.map((d) => {const j = distribution(matchedJeonse(d.key).map((r) => Number(r.deposit)), 0); return {name:d.name, type:"bar", data:d.stats && j ? [d.stats.median, j.median] : []};}) : [];
```

<div class="card">${heading("매매·전세 거래집단", "같은 단지·면적대의 별도 거래집단 중간값입니다. 두 집단이 각각 5건 이상이고 단지 식별을 확인한 경우에만 표시합니다.")}<div class="chart-slot">${chart({xAxis:{type:"category", data:["매매", "전세"]}, yAxis:{type:"value", name:"만원", min:0}, series:saleRentSeries}, invalidation)}</div></div>

${identityConfirmed.length ? html`<table class="compare-table" tabindex="0"><thead><tr><th>단지</th><th>매매 중간값 · n</th><th>전세 중간값 · n</th><th>집단 비율</th></tr></thead><tbody>${summaries.map((d) => {const rs = matchedJeonse(d.key); const j = distribution(rs.map((r) => Number(r.deposit)), 0); return html`<tr><th>${d.name}</th><td data-label="매매 중간값 · n">${d.stats ? `${won(d.stats.median)} · ${d.stats.n}건` : "표본 부족"}</td><td data-label="전세 중간값 · n">${j ? `${won(j.median)} · ${j.n}건` : "표본 부족"}</td><td data-label="집단 비율">${d.stats && j ? pct(j.median / d.stats.median) : "–"}</td></tr>`;})}</tbody></table>` : html`<p>동일 단지 확인 전 비교를 보류합니다.</p>`}

## 보증금과 월 부담

<p>선택한 단지의 최근 거래 최대 100건 중에서 서로 다른 거래를 비교합니다. 환산 월비용은 사용자가 입력한 연 금리 가정이며 실제 납부액이나 동일 주택의 전환 제안이 아닙니다. 월세가 미상인 거래는 제외합니다.</p>

<div class="filters compare-rent-controls">

```js
const rentRows = rents.filter((d) => rentPoint(d) && within(d) && d.band === band && selectionOk && selected.includes(d.complex_key)).sort((a,b) => new Date(b.deal_date)-new Date(a.deal_date)).slice(0, 100);
const rentIds = rentRows.map((_, i) => i);
```

```js
const rentPick = view(Inputs.select(rentIds, {label:"실제 임대 거래 (최대 3건)", multiple:3, format:(i) => `${rentRows[i].apt} · ${rentRows[i].ym} · 보증금 ${won(rentRows[i].deposit)} / 월 ${won(rentRows[i].monthly)}`, disabled: !rentIds.length}));
```

```js
const rate = view(Inputs.text({label:"가정 연 금리 (%) · 직접 입력", placeholder:"예: 4", type:"number"}));
```

</div>

```js
const rentSelectionOk = withinSelectionLimit(rentPick);
const selectedRents = (rentSelectionOk ? rentPick : []).map((i) => rentRows[i]);
const costs = selectedRents.map((d) => rentCost(d, rate));
const validCosts = costs.length && costs.every((v) => v != null);
```

<div class="card">${heading("가정 월비용 비교", "보증금에 같은 연 금리 가정을 적용한 환산값입니다. 실제 납부 월세와는 다르고 계약별 원값은 아래 표에 있습니다.")}<div class="chart-slot">${chart({xAxis:{type:"value", name:"만원/월", min:0}, yAxis:{type:"category", data:validCosts ? selectedRents.map((_,i) => `계약 ${i+1}`) : []}, series:[{name:"가정 환산 월비용", type:"bar", data:validCosts ? costs : [], itemStyle:{color:"#07857d"}}]}, invalidation)}</div></div>

<details class="card rent-scatter-details">
  <summary>보증금과 월세 분포 보기</summary>
  <p>같은 지역·면적대·기간의 선택 단지 거래 최대100건입니다. 전세는 월세 0원으로 별도 표시하며 선택한 계약은 점을 크게 표시합니다. 서로 다른 계약을 같은 집의 전환 조건으로 연결하지 않습니다. 계약 선택은 위 선택기를 사용하세요.</p>
  <div class="chart-slot">${chart({xAxis:{type:"value", name:"보증금 (만원)", min:0}, yAxis:{type:"value", name:"월세 (만원)", min:0}, tooltip:{trigger:"item"}, series:["전세","월세"].map((kind) => ({name:kind, type:"scatter", data:rentRows.flatMap((d,i) => {const point=rentPoint(d); return point?.kind === kind ? [{name:`${d.apt} · ${d.ym}`, value:[point.deposit,point.monthly], symbolSize:rentPick.includes(i) ? 13 : 7}] : [];})}))}, invalidation)}</div>
  <details><summary>분포의 계약 원값 표</summary>${rentRows.length ? html`<table class="compare-table" tabindex="0"><thead><tr><th>계약</th><th>구분</th><th>보증금</th><th>월세</th></tr></thead><tbody>${rentRows.map((d) => {const point=rentPoint(d); return html`<tr><th>${d.apt} · ${d.ym}</th><td data-label="구분">${point.kind}</td><td data-label="보증금">${won(point.deposit)}</td><td data-label="월세">${won(point.monthly)}</td></tr>`;})}</tbody></table>` : html`<p>표시할 거래가 없습니다.</p>`}</details>
</details>

${!withinSelectionLimit(rentPick) ? html`<p role="alert">임대 거래는 최대 3건까지 선택하세요.</p>` : rentPick.length ? html`<table class="compare-table" tabindex="0"><thead><tr><th>계약</th><th>보증금</th><th>실제 월세</th><th>가정 환산 월비용</th></tr></thead><tbody>${rentPick.map((i) => { const d = rentRows[i], cost = rentCost(d, rate); return html`<tr><td data-label="계약">${d.apt} · ${d.ym}</td><td data-label="보증금">${won(d.deposit)}</td><td data-label="실제 월세">${won(d.monthly)}</td><td data-label="가정 환산 월비용">${cost == null ? "금리 입력 필요" : won(cost)}</td></tr>`; })}</tbody></table>` : html`<p>선택할 수 있는 거래가 없습니다. 자료 범위 또는 이름 일치를 확인하세요.</p>`}

```js
const saveRent = () => downloadEvidence("rent", "보증금과 월 부담", [...selectedRents.map((d,i) => ({id:`rent-${i+1}`,kind:"rent_contract",chart_spec:{type:"scatter",x:"보증금",y:"월세"},source_id:"molit-rents",is_sample:false,rights:"unknown",coverage_verified:false,identity_verified:false,reviewed_by:"",period:d.ym,scope:`${d.sgg} ${d.umd} ${d.apt} ${d.area}㎡`,unit:"만원/월",sample_n:1,source_url:"https://rt.molit.go.kr/",query_spec:{deposit:Number(d.deposit),monthly:Number(d.monthly),annual_rate:Number(rate),assumption:"보증금 기회비용"},facts:[{label:"실제 월세",value:Number(d.monthly)},{label:"가정 환산 월비용",value:costs[i]}]})), ...jeonseEvidence()]);
```

${html`<button type="button" disabled=${!selectedRents.length || costs.some((v) => v == null)} onclick=${saveRent}>임대 비교를 근거 초안으로 저장</button>`}

<p><a href="./personal">내 조건으로 현금흐름 계산 →</a> · <a href="https://rt.molit.go.kr/">국토교통부 실거래가 공개시스템</a></p>
