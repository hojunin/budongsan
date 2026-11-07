---
title: 타겟 단지
---

```js
import {regionOptions, sampleBanner, plotBase, card, won, num, signed, pct, BAND_LABEL, COLOR, PALETTE} from "./components/ui.js";
const regions = await FileAttachment("data/regions.json").json();
const watch = await FileAttachment("data/watchlist.json").json();
const listings = (await FileAttachment("data/listings.csv").csv({typed: true})).filter((d) => d.min_ask || d.median_ask);
const db = await DuckDBClient.of({trades: FileAttachment("data/trades.parquet"), rents: FileAttachment("data/rents.parquet")});
const isSample = (await db.queryRow(`SELECT bool_or(is_sample) AS s FROM trades`)).s;
const esc = (s) => String(s).replace(/'/g, "''");
const SEARCH_OPTS = regionOptions(regions).slice(2);
```

# 타겟 단지

<p class="lead">관심 단지를 고르거나 직접 검색해서, 실거래 흐름과 예산선(6억·9억)을 한 화면에서 봅니다.</p>

${sampleBanner(isSample)}

<div class="filters">

```js
const mode = view(Inputs.radio(["관심 단지", "직접 검색"], {label: "찾는 방법", value: "관심 단지"}));
```

```js
const watchPick = mode === "관심 단지"
  ? view(Inputs.select(watch, {label: "단지", format: (w) => `${w.track} · ${w.name}`, value: watch.find((w) => w.track === "B")}))
  : null;
const searchRegion = mode === "직접 검색"
  ? view(Inputs.select(SEARCH_OPTS, {label: "지역", format: (d) => d.label, value: SEARCH_OPTS.find((o) => o.label.includes("노원구"))}))
  : null;
const query = mode === "직접 검색" ? view(Inputs.text({label: "단지명", placeholder: "예: 주공, 자이, 래미안", autocomplete: "off"})) : null;
```

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
```

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
const rentRows = target ? Array.from(await db.query(`
  SELECT ym, band, median(deposit) AS dep FROM rents WHERE ${target.where} AND jeonse GROUP BY ym, band ORDER BY ym`), (r) => ({...r, dep: Number(r.dep)})) : [];
const bandsHere = [...new Set(deals.map((d) => d.band))].sort((a, b) => parseFloat(a) - parseFloat(b));
```

```js
const band = bandsHere.length ? view(Inputs.radio(bandsHere, {label: "평형", value: bandsHere.includes("84") ? "84" : bandsHere.includes("59") ? "59" : bandsHere[0], format: (b) => BAND_LABEL[b] ?? b})) : null;
```

```js
const valid = deals.filter((d) => !d.canceled && d.band === band);
const maxDate = d3.max(valid, (v) => v.deal_date);
const last3 = valid.filter((d) => d.deal_date >= d3.timeMonth.offset(maxDate, -3));
const med3 = d3.median(last3, (d) => d.price);
const yaEnd = d3.timeMonth.offset(maxDate, -12);
const yearAgo = valid.filter((d) => d.deal_date <= yaEnd && d.deal_date >= d3.timeMonth.offset(yaEnd, -3));
const medYA = d3.median(yearAgo, (d) => d.price);
const jeonse = d3.median(rentRows.filter((r) => r.band === band).slice(-3), (r) => r.dep);
const ask = target?.meta ? listings.filter((l) => l.complex_id === target.meta.id && String(l.area_band) === band).at(-1) : null;
// 월별 중위가
const monthlyMed = d3.rollups(valid, (v) => d3.median(v, (d) => d.price), (d) => d.ym).map(([ym, p]) => ({date: new Date(ym + "-01"), p})).sort((a, b) => a.date - b.date);
```

${target ? html`<h2>${target.label} <span class="chip ${target.meta?.track === "B" ? "b" : ""}">${target.meta ? `${target.meta.track} 트랙 · ${target.meta.station} · 성수 ${target.meta.commute}` : "직접 검색"}</span></h2>` : html`<p>단지를 골라 주세요.</p>`}

<div class="kpis">
  ${card("최근 3개월 중위 실거래", won(med3), `${BAND_LABEL[band] ?? ""} · ${last3.length}건`)}
  ${card("1년 전 대비", signed(medYA ? med3 / medYA - 1 : null), medYA ? `1년 전 ${won(medYA)}` : "비교 거래 부족", med3 > medYA ? "up" : "down")}
  ${card("전세가율", pct(jeonse && med3 ? jeonse / med3 : null), jeonse ? `전세 중위 ${won(jeonse)}` : "전월세 데이터 없음")}
  ${card("호가 괴리율", signed(ask?.median_ask && med3 ? ask.median_ask / med3 - 1 : null), ask ? `${ask.date} 기록 · 매물 ${ask.listing_count ?? "–"}건` : "listings.csv 에 호가를 적으면 계산")}
</div>

<div class="card grid-1">
  <h2>실거래 흐름</h2>
  ${resize((width) => Plot.plot({
    ...plotBase(width),
    height: Math.max(280, Math.min(440, width * 0.52)),
    y: {grid: true, label: "만 원", tickFormat: (v) => won(v)},
    color: {legend: true, domain: ["정상", "신고가", "해제"], range: [COLOR.accent2, COLOR.accent, "var(--theme-foreground-faint)"]},
    marks: [
      Plot.ruleY([60000], {stroke: COLOR.good, strokeDasharray: "4,3"}),
      Plot.text([{y: 60000}], {y: "y", frameAnchor: "left", dy: -7, text: () => "6억 · 디딤돌 상한", fill: COLOR.good, fontSize: 11}),
      Plot.ruleY([90000], {stroke: COLOR.warn, strokeDasharray: "4,3"}),
      Plot.text([{y: 90000}], {y: "y", frameAnchor: "left", dy: -7, text: () => "9억 · 신생아 특례 상한", fill: COLOR.warn, fontSize: 11}),
      Plot.dot(deals.filter((d) => d.band === band), {x: "deal_date", y: "price", r: 3.5, fill: (d) => (d.canceled ? "해제" : d.new_high ? "신고가" : "정상"), fillOpacity: 0.75,
        tip: true, title: (d) => `${d.deal_date.toLocaleDateString("ko-KR")} · ${d.area}㎡ · ${d.floor}층\n${won(d.price)}${d.canceled ? " (해제)" : ""}`}),
      Plot.lineY(monthlyMed, {x: "date", y: "p", stroke: "currentColor", strokeWidth: 1.6, curve: "monotone-x"}),
      ask?.median_ask ? Plot.ruleY([ask.median_ask], {stroke: COLOR.accent, strokeWidth: 2}) : null
    ]
  }))}
  <p class="note">점: 개별 실거래 · 선: 월별 중위가 · 실선(빨강): 기록한 호가 중위값 · 점선: 예산선. 디딤돌은 거래가가 아니라 담보 평가액으로 6억을 봅니다.</p>
</div>

<div class="card grid-1 table-wrap">
  <h2>최근 거래 20건</h2>
  ${Inputs.table(deals.slice().reverse().slice(0, 20), {
    columns: ["deal_date", "area", "floor", "price", "canceled"],
    header: {deal_date: "계약일", area: "전용(㎡)", floor: "층", price: "거래가", canceled: "해제"},
    format: {deal_date: (d) => d.toLocaleDateString("ko-KR"), price: won, canceled: (c) => (c ? "해제" : "")},
    layout: "auto", rows: 10
  })}
</div>
