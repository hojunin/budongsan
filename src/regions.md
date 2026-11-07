---
title: 지역 비교
---

```js
import {regionOptions, bandWhere, sinceWhere, sampleBanner, plotBase, num, pct, signed, BANDS, BAND_LABEL, PALETTE} from "./components/ui.js";
const regions = await FileAttachment("data/regions.json").json();
const db = await DuckDBClient.of({trades: FileAttachment("data/trades.parquet")});
const isSample = (await db.query(`SELECT bool_or(is_sample) AS s FROM trades`))[0].s;
const OPTS = regionOptions(regions);
const pick = (labels) => OPTS.filter((o) => labels.includes(o.label));
```

# 지역 비교

<p class="lead">최대 6개 지역을 골라 거래량과 가격 흐름을 같은 축에서 비교합니다.</p>

${sampleBanner(isSample)}

<div class="filters">

```js
const chosen = view(Inputs.select(OPTS, {label: "지역 (여러 개)", multiple: 6, format: (d) => d.label,
  value: pick(["서울 전체", "경기 전체", "서울 · 노원구", "경기 · 성남시 중원구", "경기 · 남양주시"])}));
const metric = view(Inputs.select(new Map([
  ["㎡당 중위가", "ppm2"], ["거래량", "n"], ["신고가 비율", "new_high_rate"], ["거래량 대비 해제율", "cancel_rate"]
]), {label: "지표", value: "ppm2"}));
const indexed = view(Inputs.toggle({label: "시작 시점 = 100", value: false}));
const bands = view(Inputs.select(BANDS, {label: "평형", multiple: true, value: ["59", "84"], format: (b) => BAND_LABEL[b]}));
const months = view(Inputs.radio([12, 24, 36], {label: "기간", value: 24, format: (m) => `${m}개월`}));
```

</div>

```js
const series = (await Promise.all(chosen.slice(0, 6).map(async (r) => {
  const q = await db.query(`
    SELECT ym, count(*) FILTER (WHERE NOT canceled) AS n,
      median(ppm2) FILTER (WHERE NOT canceled) AS ppm2,
      avg(CASE WHEN new_high AND NOT canceled THEN 1 ELSE 0 END) AS new_high_rate,
      avg(CASE WHEN canceled THEN 1 ELSE 0 END) AS cancel_rate
    FROM trades WHERE ${r.where} AND ${bandWhere(bands)} AND ${sinceWhere(months)}
    GROUP BY ym ORDER BY ym`);
  const rows = Array.from(q, (d) => ({region: r.label, date: new Date(d.ym + "-01"), ym: d.ym, n: Number(d.n), ppm2: d.ppm2, new_high_rate: d.new_high_rate, cancel_rate: d.cancel_rate})).slice(0, -1);
  const base = rows.find((d) => d[metric] > 0)?.[metric];
  return rows.map((d) => ({...d, value: indexed && base ? (d[metric] / base) * 100 : d[metric]}));
}))).flat();
const isRate = metric.endsWith("rate");
```

<div class="card grid-1">
  ${resize((width) => Plot.plot({
    ...plotBase(width),
    height: Math.max(280, Math.min(440, width * 0.5)),
    y: {grid: true, label: indexed ? "지수 (시작=100)" : isRate ? null : metric === "n" ? "건" : "만 원/㎡", tickFormat: isRate && !indexed ? "%" : undefined},
    color: {legend: true, range: PALETTE},
    marks: [
      indexed ? Plot.ruleY([100], {stroke: "currentColor", strokeOpacity: 0.3}) : Plot.ruleY([0]),
      Plot.lineY(series, {x: "date", y: "value", stroke: "region", strokeWidth: 2, curve: "monotone-x"}),
      Plot.text(series, Plot.selectLast({x: "date", y: "value", z: "region", text: "region", textAnchor: "start", dx: 6, fill: "region", fontSize: 11})),
      Plot.tip(series, Plot.pointerX({x: "date", y: "value", stroke: "region", title: (d) => `${d.region} · ${d.ym}\n${isRate && !indexed ? pct(d.value) : num(d.value)}`}))
    ],
    marginRight: width < 520 ? 12 : 110
  }))}
  <p class="note">최근 1개월은 신고 지연으로 빼고 그렸습니다. 거래량은 지역 크기 차이가 커서 ‘시작 시점 = 100’으로 보면 흐름 비교가 쉽습니다.</p>
</div>

```js
const summary = d3.rollups(series, (v) => {
  const a = v.at(0), b = v.at(-1), m6 = v.at(-7);
  return {last: b?.ppm2, chg12: a && b ? b.ppm2 / a.ppm2 - 1 : null, chg6: m6 && b ? b.ppm2 / m6.ppm2 - 1 : null, vol3: d3.mean(v.slice(-3), (d) => d.n), vol3prev: d3.mean(v.slice(-15, -12), (d) => d.n)};
}, (d) => d.region).map(([region, s]) => ({region, ...s}));
```

<div class="card grid-1 table-wrap">
  <h2>요약</h2>
  ${Inputs.table(summary, {
    columns: ["region", "last", "chg6", "chg12", "vol3", "vol3prev"],
    header: {region: "지역", last: "㎡당 중위가(만)", chg6: "6개월", chg12: "기간 전체", vol3: "최근 3개월 월평균 거래", vol3prev: "1년 전 같은 3개월"},
    format: {last: num, chg6: (x) => signed(x), chg12: (x) => signed(x), vol3: num, vol3prev: num},
    layout: "auto", rows: 8
  })}
</div>
