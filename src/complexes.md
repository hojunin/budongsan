---
title: 타겟 단지
---

```js
import {dataTable} from "./components/table.js";
import {chart} from "./components/charts.js";
import {enhanceUI} from "./components/appearance.js";
const disposeUI = enhanceUI(invalidation);
```


```js
import {regionOptions, sampleTag, card, won, num, signed, pct, BAND_LABEL, COLOR, PALETTE} from "./components/ui.js";
const regions = await FileAttachment("data/regions.json").json();
const watch = await FileAttachment("data/watchlist.json").json();
const listings = (await FileAttachment("data/listings.csv").csv({typed: true})).filter((d) => d.min_ask || d.median_ask);
const esc = (s) => String(s).replace(/'/g, "''");
const SEARCH_OPTS = regionOptions(regions).slice(2);
```

```js
const db = await DuckDBClient.of({trades: FileAttachment("data/trades.parquet")});
const isSample = (await db.queryRow(`SELECT bool_or(is_sample) AS s FROM trades`)).s;
```

# 타겟 단지

<p class="lead">관심 단지를 고르거나 직접 검색해서, 실거래 흐름과 예산선(6억·9억)을 한 화면에서 봅니다.</p>

<div class="data-indicator">${sampleTag(isSample)}</div>

<div class="filters filters--complexes">

<div class="filter-field filter-field--mode">

```js
const mode = view(Inputs.radio(["관심 단지", "직접 검색"], {label: "찾는 방법", value: "관심 단지"}));
```

</div>

<div class="filter-field filter-field--watch">

```js
const watchPick = mode === "관심 단지"
  ? view(Inputs.select(watch, {label: "단지", format: (w) => `${w.track} · ${w.name}`, value: watch.find((w) => w.track === "B")}))
  : null;
```

</div>

<div class="filter-field filter-field--search">

```js
const searchRegion = mode === "직접 검색"
  ? view(Inputs.select(SEARCH_OPTS, {label: "지역", format: (d) => d.label, value: SEARCH_OPTS.find((o) => o.label.includes("노원구"))}))
  : null;
```

</div>

<div class="filter-field filter-field--search">

```js
const query = mode === "직접 검색" ? view(Inputs.text({label: "단지명", placeholder: "예: 주공, 자이, 래미안", autocomplete: "off"})) : null;
```

</div>

<div class="filter-field filter-field--search">

```js
const candidates = mode === "직접 검색"
  ? Array.from(await db.query(`
      SELECT complex_key, any_value(apt) AS apt, any_value(umd) AS umd, count(*) AS n, max(build_year) AS built
      FROM trades WHERE ${searchRegion.where} AND apt ILIKE '%${esc(query ?? "")}%'
      GROUP BY complex_key ORDER BY n DESC LIMIT 40`), (c) => ({...c, n: Number(c.n), built: Number(c.built)}))
  : [];
const searchPick = mode === "직접 검색" && candidates.length
  ? view(Inputs.select(candidates, {label: "검색 결과", format: (c) => `${c.apt} (${c.umd}, ${c.built}년, ${num(c.n)}건)`}))
  : null;
if (mode === "직접 검색" && !candidates.length) display(html`<p class="filter-empty" role="status">검색 결과가 없습니다.</p>`);
```

</div>

</div>

```js
// 선택된 단지를 같은 형태로 맞춤
const target = mode === "관심 단지"
  ? {label: watchPick.name, where: `sgg = '${watchPick.sgg}' AND apt ILIKE '%${esc(watchPick.match)}%'`, meta: watchPick}
  : searchPick ? {label: searchPick.apt, where: `complex_key = '${esc(searchPick.complex_key)}'`, meta: null} : null;
```

```js
const deals = target ? Array.from(await db.query(`
  SELECT deal_date, ym, apt, umd, area, band, price, floor, build_year, canceled, new_high
  FROM trades WHERE ${target.where} ORDER BY deal_date`), (d) => ({...d, deal_date: new Date(d.deal_date), area: Number(d.area), price: Number(d.price), floor: Number(d.floor)})) : [];
const bandsHere = [...new Set(deals.map((d) => d.band))].sort((a, b) => parseFloat(a) - parseFloat(b));
```

```js
// A nested promise keeps optional rent loading from blocking the page and reuses its client.
const rentSource = {client: DuckDBClient.of({rents: FileAttachment("data/rents.parquet")}).catch((error) => {
  console.warn("전월세 데이터를 읽지 못했습니다.", error);
  return null;
})};
```

```js
const rentResult = Generators.observe((notify) => {
  let disposed = false;
  notify({rows: [], failed: false, pending: Boolean(target)});
  if (target) (async () => {
    try {
      const rentDb = await rentSource.client;
      if (!rentDb) {
        if (!disposed) notify({rows: [], failed: true, pending: false});
        return;
      }
      const rows = await rentDb.query(`SELECT ym, band, median(deposit) AS dep FROM rents WHERE ${target.where} AND jeonse GROUP BY ym, band ORDER BY ym`);
      if (!disposed) notify({rows: Array.from(rows, (r) => ({...r, dep: Number(r.dep)})), failed: false, pending: false});
    } catch (error) {
      console.warn("전월세 데이터를 읽지 못했습니다.", error);
      if (!disposed) notify({rows: [], failed: true, pending: false});
    }
  })();
  return () => { disposed = true; };
});
```

```js
const rentRows = rentResult.rows;
const jeonse = d3.median(rentRows.filter((r) => r.band === band).slice(-3), (r) => r.dep);
```

<div class="filters inline-filters"><div class="filter-field filter-field--bands">

```js
const band = bandsHere.length ? view(Inputs.radio(bandsHere, {label: "평형", value: bandsHere.includes("84") ? "84" : bandsHere.includes("59") ? "59" : bandsHere[0], format: (b) => BAND_LABEL[b] ?? b})) : null;
if (!bandsHere.length) display(html`<p class="filter-empty" role="status">표시할 평형이 없습니다.</p>`);
```

</div></div>

```js
const valid = deals.filter((d) => !d.canceled && d.band === band);
const maxDate = d3.max(valid, (v) => v.deal_date);
const last3 = valid.filter((d) => d.deal_date >= d3.timeMonth.offset(maxDate, -3));
const med3 = d3.median(last3, (d) => d.price);
const yaEnd = d3.timeMonth.offset(maxDate, -12);
const yearAgo = valid.filter((d) => d.deal_date <= yaEnd && d.deal_date >= d3.timeMonth.offset(yaEnd, -3));
const medYA = d3.median(yearAgo, (d) => d.price);
const ask = target?.meta ? listings.filter((l) => l.complex_id === target.meta.id && String(l.area_band) === band).at(-1) : null;
// 월별 중위가
const monthlyMed = d3.rollups(valid, (v) => d3.median(v, (d) => d.price), (d) => d.ym).map(([ym, p]) => ({date: new Date(ym + "-01"), p})).sort((a, b) => a.date - b.date);
```

<div class="target-heading">${target ? html`<h2>${target.label} <span class="chip ${target.meta?.track === "B" ? "b" : ""}">${target.meta ? `${target.meta.track} 트랙 · ${target.meta.station} · 성수 ${target.meta.commute}` : "직접 검색"}</span></h2>` : html`<p>단지를 골라 주세요.</p>`}</div>

<div class="kpis">
  <div class="kpi-slot">${card("최근 3개월 중위 실거래", won(med3), `${BAND_LABEL[band] ?? ""} · ${last3.length}건`)}</div>
  <div class="kpi-slot">${card("1년 전 대비", signed(medYA ? med3 / medYA - 1 : null), medYA ? `1년 전 ${won(medYA)}` : "비교 거래 부족", med3 > medYA ? "up" : "down")}</div>
  <div class="kpi-slot">${card("전세가율", pct(jeonse && med3 ? jeonse / med3 : null), rentResult.pending ? "전월세 데이터 확인 중" : rentResult.failed ? "전월세 데이터를 불러오지 못했습니다" : jeonse ? `전세 중위 ${won(jeonse)}` : "전월세 데이터 없음")}</div>
  <div class="kpi-slot">${card("호가 괴리율", signed(ask?.median_ask && med3 ? ask.median_ask / med3 - 1 : null), ask ? `${ask.date} 기록 · 매물 ${ask.listing_count ?? "–"}건` : "listings.csv 에 호가를 적으면 계산")}</div>
</div>

<div class="card grid-1">
  <div class="chart-heading"><h2>실거래 흐름</h2><details class="chart-info"><summary aria-label="실거래 흐름 설명"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v6m0-10h.01"></path></svg></summary><div class="chart-info-panel">점은 선택한 평형의 개별 매매 거래이며 정상·신고가·해제를 구분합니다. 선은 월별 매매 중위가이며, 전월세 데이터가 있으면 전세 중위가도 표시합니다. 점선은 예산 기준선, 기록된 호가가 있으면 해당 가격선도 표시합니다. 범례로 거래 종류를 선택할 수 있습니다.</div></details></div>
  <div class="chart-slot">${chart({
    xAxis: {type: "time"}, yAxis: {name: "만 원", axisLabel: {formatter: (v) => won(v), fontSize: 10}},
    tooltip: {trigger: "item", confine: true, renderMode: "richText", valueFormatter: (v) => typeof v === "number" ? won(v) : v},
    series: [
      ...["정상", "신고가", "해제"].map((name) => ({name, type: "scatter", symbolSize: 7,
        data: deals.filter((d) => d.band === band && (d.canceled ? "해제" : d.new_high ? "신고가" : "정상") === name).map((d) => ({value: [+d.deal_date, d.price], name: `${d.deal_date.toLocaleDateString("ko-KR")} · ${d.area}㎡ · ${d.floor}층`}))})),
      {name: "월별 중위가", type: "line", data: monthlyMed.map((d) => [+d.date, d.p]),
        markLine: {symbol: "none", label: {position: "insideEndTop", fontSize: 10}, data: [
          {yAxis: 60000, name: "6억 · 디딤돌", label: {formatter: "6억 · 디딤돌"}},
          {yAxis: 90000, name: "9억 · 특례", label: {formatter: "9억 · 특례"}},
          ...(ask?.median_ask ? [{yAxis: ask.median_ask, label: {formatter: "기록한 호가"}, lineStyle: {type: "solid", color: "#c8553d"}}] : [])
        ]}},
      {name: "전세 중위가", type: "line", data: rentRows.filter((d) => d.band === band).map((d) => [+new Date(d.ym + "-01"), d.dep])}
    ]
  }, invalidation)}</div>
  <p class="note">점: 개별 실거래 · 선: 월별 중위가 · 실선(빨강): 기록한 호가 중위값 · 점선: 예산선. 디딤돌은 거래가가 아니라 담보 평가액으로 6억을 봅니다.</p>
</div>

<div class="card grid-1 table-wrap">
  <h2>최근 거래 20건</h2>
  <div class="table-slot">${dataTable(deals.slice().reverse().slice(0, 20), [
    {field: "deal_date", title: "계약일", sorter: (a, b) => +a - +b, format: (d) => d.toLocaleDateString("ko-KR")},
    {field: "price", title: "거래가", sorter: "number", format: won, responsive: 0},
    {field: "area", title: "전용(㎡)", sorter: "number"},
    {field: "floor", title: "층", sorter: "number"},
    {field: "canceled", title: "해제 여부", format: (v) => v ? "해제" : "정상"}
  ], invalidation)}</div>
</div>
