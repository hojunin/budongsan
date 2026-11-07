---
title: 내 리포트
---

```js
import {enhanceUI} from "../components/appearance.js";
import {heading} from "../components/ui.js";
const disposeUI = enhanceUI(invalidation);
const posts = await FileAttachment("../data/reports.json").json();
```

# 내 리포트

<p class="lead">이 사이트의 데이터로 직접 쓴 시장 리포트입니다. 숫자는 글을 쓴 시점에 고정되지 않고, 글 안의 차트는 배치가 돌 때마다 최신 데이터로 다시 그려집니다.</p>

<div class="card grid-1">
  ${heading(`발행한 리포트 — ${posts.length}편`, "src/reports 폴더에 있는 글입니다. 최신순입니다.")}
  ${posts.length ? html`<ul class="article-list">${posts.map((p) => html`<li>
    <a href=${`./${p.slug}`}>${p.title}</a>
    <span class="article-meta">${p.date}${p.tags ? ` · ${p.tags}` : ""}</span>
    ${p.summary ? html`<span class="article-meta">${p.summary}</span>` : ""}
  </li>`)}</ul>` : html`<p class="note">아직 발행한 리포트가 없습니다.</p>`}
</div>

## 리포트를 쓰는 방법

1. 초안을 만듭니다. 그 시점의 핵심 인사이트, 관련 리포트 기사, 차트가 채워진 파일이 `content/drafts/` 에 생깁니다. 이 폴더는 사이트에 올라가지 않습니다.
   ```bash
   .venv/bin/python scripts/new_report.py "11월 첫째 주 서울 아파트 시장"
   ```
2. 초안의 `내 해석`, `SNS용 요약` 을 직접 씁니다. 숫자 문장은 출처와 기준일이 붙어 있으니 그대로 인용해도 됩니다.
3. 발행할 때 파일을 옮깁니다. 다음 배치(또는 `npm run clean && npm run build && npm run deploy`)에서 이 목록과 사이트에 올라갑니다. `clean` 을 빼면 이전 목록이 캐시에서 그대로 나옵니다.
   ```bash
   git mv content/drafts/2026-11-07-예시.md src/reports/
   ```
