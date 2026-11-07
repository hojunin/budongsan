---
title: 10년 추이
---

```js
import {chart} from "./components/charts.js";
import {dataTable} from "./components/table.js";
import {enhanceUI} from "./components/appearance.js";
import {heading, num, signed, regionColor} from "./components/ui.js";
const disposeUI = enhanceUI(invalidation);
const trend = Array.from(await FileAttachment("data/trend.parquet").parquet(), (d) => ({...d, n: Number(d.n), n84: Number(d.n84)}));
```

# 10년 추이

<p class="lead">최근 10년 서울·경기 아파트 실거래를 월별로 묶었습니다. 해제 거래는 빼고 계산합니다. 시도 전체 값은 시군구 값을 다시 묶지 않고 거래 원본에서 바로 계산합니다.</p>

```js
const regions = [...new Map(trend.map((d) => [d.code, {code: d.code, name: d.name, level: d.level}])).values()]
  .sort((a, b) => (a.level === b.level ? a.name.localeCompare(b.name, "ko") : a.level === "sido" ? -1 : 1));
const METRICS = {
  ppm2_med: {label: "㎡당 중위 거래가", unit: "만 원/㎡"},
  price84_med: {label: "84㎡ 중위 거래가", unit: "만 원"},
  n: {label: "거래량", unit: "건"}
};
```

<div class="filters">
<div class="filter-field filter-field--standard">

```js
const picked = view(Inputs.select(regions, {label: "지역 (최대 6곳)", multiple: 6, format: (r) => r.name, valueof: (r) => r.code,
  value: ["11", "41"].filter((c) => regions.some((r) => r.code === c))}));
```

</div>
<div class="filter-field filter-field--standard">

```js
const metric = view(Inputs.radio(Object.keys(METRICS), {label: "지표", value: "ppm2_med", format: (k) => METRICS[k].label}));
```

</div>
<div class="filter-field filter-field--toggle">

```js
const smooth = view(Inputs.toggle({label: "12개월 이동평균", value: true}));
```

</div>
</div>

```js
const months = [...new Set(trend.map((d) => d.ym))].sort();
const lastFull = months.at(-3);  // 최근 두 달은 신고가 덜 들어와서 비교에서 뺀다
const shown = months.filter((m) => m <= lastFull);
const valueOf = (code, key) => {
  const s = new Map(trend.filter((d) => d.code === code).map((d) => [d.ym, d[key]]));
  const raw = shown.map((m) => s.get(m) ?? null);
  if (!smooth) return raw;
  return raw.map((_, i) => {
    const w = raw.slice(Math.max(0, i - 11), i + 1).filter((v) => v != null);
    return i >= 11 && w.length >= 9 ? w.reduce((a, b) => a + b, 0) / w.length : null;
  });
};
const nameOf = (code) => regions.find((r) => r.code === code)?.name ?? code;
```

<div class="card grid-1">
  ${heading(`${METRICS[metric].label} — ${smooth ? "12개월 이동평균" : "월별"}`, "시군구는 거래가 적은 달에 중위가가 크게 흔들립니다. 12개월 이동평균을 켜면 계절·구성 효과가 줄어 장기 방향이 잘 보입니다. 최근 두 달은 신고가 덜 들어와 그래프에서 뺐습니다.")}
  <div class="chart-slot">${chart({
    xAxis: {data: shown.map((m) => m)}, yAxis: {name: METRICS[metric].unit},
    series: picked.map((code, i) => ({name: nameOf(code), type: "line", itemStyle: {color: regionColor(nameOf(code))}, data: valueOf(code, metric)}))
  }, invalidation)}</div>
</div>

## 지역별 장기 변화

```js
// 비교 시점은 계절 영향을 없애려고 '직전 12개월 합산 중위'끼리 비교한다: 최근 12개월 vs 5년 전 12개월 vs 10년 전 12개월
const trailing = (code, key, endIdx) => {
  const ms = new Set(shown.slice(Math.max(0, endIdx - 11), endIdx + 1));
  const rows = trend.filter((d) => d.code === code && ms.has(d.ym) && d[key] != null);
  if (rows.length < 9) return null;
  if (key === "n") return rows.reduce((a, d) => a + d.n, 0);
  const w = rows.reduce((a, d) => a + d.n, 0);
  return rows.reduce((a, d) => a + d[key] * d.n, 0) / w;  // 거래량 가중 평균 (월 중위값의 근사 합산)
};
const end = shown.length - 1;
const table = regions.map((r) => {
  const now = trailing(r.code, "ppm2_med", end), y5 = trailing(r.code, "ppm2_med", end - 60), y10 = trailing(r.code, "ppm2_med", end - 120);
  const n = trailing(r.code, "n", end), nPrev = trailing(r.code, "n", end - 12);
  return {name: r.name, level: r.level === "sido" ? "시도" : "시군구", ppm2: now,
    chg5: now && y5 ? now / y5 - 1 : null, chg10: now && y10 ? now / y10 - 1 : null,
    n, nChg: n && nPrev ? n / nPrev - 1 : null};
}).filter((d) => d.ppm2 != null);
```

<div class="card grid-1">
  ${heading("지역별 ㎡당 가격 변화와 거래량", `최근 12개월(~${lastFull?.replace("-", "년 ")}월)을 5년 전·10년 전 같은 12개월과 비교합니다. 월별 중위가를 거래량으로 가중 평균한 근사값입니다. 열 제목을 눌러 정렬하세요.`)}
  <div class="table-slot">${dataTable(table, [
    {title: "지역", field: "name"},
    {title: "구분", field: "level"},
    {title: "㎡당 가격 (최근 12개월)", field: "ppm2", sorter: "number", format: (v) => `${num(v)}만`},
    {title: "5년 변화", field: "chg5", sorter: "number", format: (v) => signed(v), signed: true},
    {title: "10년 변화", field: "chg10", sorter: "number", format: (v) => signed(v), signed: true},
    {title: "거래 (최근 12개월)", field: "n", sorter: "number", format: num},
    {title: "거래 1년 변화", field: "nChg", sorter: "number", format: (v) => signed(v), signed: true}
  ], invalidation)}</div>
</div>
