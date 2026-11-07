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

<p class="lead">검토한 근거를 발행 시점의 숫자와 그림으로 고정한 리포트입니다. 기존 수동 작성 글의 고정 여부는 개별 확인이 필요합니다.</p>

<div class="card grid-1 report-list-slot" tabindex="0" aria-label="발행한 리포트 목록">
  ${heading(`발행한 리포트 — ${posts.length}편`, "src/reports 폴더에 있는 글입니다. 최신순입니다.")}
  ${posts.length ? html`<ul class="article-list">${posts.map((p) => html`<li>
    <a href=${`./${p.slug}`}>${p.title}</a>
    <span class="article-meta">${p.date}${p.tags ? ` · ${p.tags}` : ""}</span>
    ${p.summary ? html`<span class="article-meta">${p.summary}</span>` : ""}
  </li>`)}</ul>` : html`<p class="note">아직 발행한 리포트가 없습니다.</p>`}
</div>

## 발행 준비 상태

로컬 `scripts/new_report.py`는 검토한 집계 근거를 고정 패키지로 만듭니다. `create`, `verify`, `prepare` 명령은 배포하지 않습니다. 합성 표본과 이용권 미확인 근거는 차단됩니다. 수집 완결성과 이용권 검토는 운영자가 직접 확인해야 합니다.

운영자는 비교 화면에서 근거 초안을 내려받아 자료 완결성·단지 식별·이용권과 출처별 릴리스를 확인합니다. 확인 후 JSON의 `coverage_verified`, `identity_verified`, `rights`, `reviewed_by`를 기록하고 제목과 요약을 검토합니다. 검증되지 않은 항목을 승인으로 표시해서는 안 됩니다.

```bash
.venv/bin/python scripts/new_report.py create evidence-draft.json content/drafts/example-package
.venv/bin/python scripts/new_report.py verify content/drafts/example-package
.venv/bin/python scripts/new_report.py prepare content/drafts/example-package example-package
```

세 템플릿은 `weekly`, `buyer`, `rent`입니다. 패키지는 정적 HTML과 SVG, 사실 JSON, 해시 manifest를 포함합니다. `prepare`는 검증된 패키지와 읽기 페이지를 `src/reports/example-package`에 준비합니다. 다음 사이트 빌드에서 목록과 읽기 경로에 포함되며 배포는 실행하지 않습니다.

개인 조건은 기본 패키지에서 빠집니다. 개인 도구에서 항목을 선택·미리보기 후 따로 저장한 경우에만 아래 명령으로 내용을 확인하고 명시적으로 포함할 수 있습니다. 생성된 패키지와 모든 출력 이미지에는 선택한 개인 값이 들어가므로 공유 전 내용을 다시 확인하세요.

```bash
.venv/bin/python scripts/new_report.py preview personal-scenario.json
.venv/bin/python scripts/new_report.py create evidence-draft.json content/drafts/example-with-scenario --include-scenario --scenario-file personal-scenario.json
```

근거가 여러 개면 세로·가로 SVG도 여러 장으로 생성됩니다. 각 장에 해당 근거의 기간·표본·출처와 필요한 가정을 표시합니다.
