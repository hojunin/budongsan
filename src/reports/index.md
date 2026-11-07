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

## 발행 준비 상태

고정 스냅샷과 출력물 검증 도구를 준비 중입니다. 기존 초안 생성기는 최신 차트가 과거 글을 바꿀 수 있어 중단했습니다. 공개 전 근거·차트·출처를 같은 릴리스로 고정하고 검토해야 합니다.
