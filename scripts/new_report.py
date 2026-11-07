"""내 리포트 초안 만들기: 지금 DB의 인사이트·관련 리포트 기사·차트를 채운 Markdown 을 content/drafts/ 에 쓴다.

사용: .venv/bin/python scripts/new_report.py "11월 첫째 주 서울 아파트 시장"
발행: git mv content/drafts/<파일> src/reports/   (다음 빌드부터 /reports 에 올라간다)
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "data"))
from _db import query  # noqa: E402
from _insights import build  # noqa: E402

CHART = '''```js
import {chart} from "../components/charts.js";
import {enhanceUI} from "../components/appearance.js";
import {PALETTE} from "../components/ui.js";
const disposeUI = enhanceUI(invalidation);
const rone = Array.from(await FileAttachment("../data/rone.parquet").parquet(), (d) => ({...d, date: new Date(d.date)}));
const since = new Date(); since.setFullYear(since.getFullYear() - 1);
const weekly = (region) => rone.filter((d) => d.metric === "wk_sale_index" && d.region_full === region && d.date >= since).sort((a, b) => a.date - b.date);
```'''


def slugify(title: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "-", title).strip("-")[:60] or "report"


def main() -> int:
    print("고정 스냅샷 발행이 구현될 때까지 초안 생성은 중단합니다.", file=sys.stderr)
    return 1


def legacy_main() -> int:
    title = " ".join(sys.argv[1:]).strip() or "주간 부동산 시장 브리핑"
    today = dt.date.today().isoformat()
    path = ROOT / "content" / "drafts" / f"{today}-{slugify(title)}.md"
    if path.exists():
        print(f"이미 있습니다: {path.relative_to(ROOT)} (덮어쓰지 않습니다)")
        return 1
    names = {r["code"]: r["name"] for r in json.loads((ROOT / "src" / "data" / "regions.json").read_text(encoding="utf-8"))}
    insights = build(names)
    facts = [i for i in insights if i["group"] != "뉴스"]
    news = [i for i in insights if i["group"] == "뉴스"]
    reports = query("""SELECT title, source, strftime(published, '%Y-%m-%d') AS day, url FROM articles
                       WHERE category = 'report' AND published >= now() - INTERVAL 14 DAY
                       ORDER BY published DESC LIMIT 8""")
    reports = [] if reports is None else reports.to_dict("records")

    cite = lambda i: f"{i['title']} ({i['source']}, {i['as_of']} 기준)"
    # SNS 요약은 성격이 다른 숫자를 고르게: 주간 시세, 수급, 거래량, 매수자
    prefer = ["wk-sale-서울", "wk_sale_supply-서울", "volume-11", "outsider-서울", "wk-sale-경기", "young-서울"]
    by_id = {i["id"]: i for i in facts}
    sns = [f"· {by_id[k]['title']}" for k in prefer if k in by_id][:4] or [f"· {i['title']}" for i in facts[:4]]
    lines = [
        "---", f"title: {title}", f"date: {today}", "summary: 한 줄 요약을 여기에 쓰세요", "tags: 서울, 경기, 아파트", "---", "",
        CHART, "", f"# {title}", "", f'<p class="as-of">작성 {today} · 숫자는 작성 시점 DB 기준, 차트는 최신 데이터로 다시 그려집니다.</p>', "",
        "## 한 줄 요약", "", "> 이번 리포트의 결론을 한 문장으로 쓰세요.", "",
        "## 핵심 숫자", "", *[f"- {cite(i)}" + (f"  \n  <small>{i['detail']}</small>" if i["detail"] else "") for i in facts], "",
        "## 차트: 최근 1년 주간 아파트값 (한국부동산원)", "",
        '<div class="card grid-1"><div class="chart-slot">${chart({xAxis: {type: "time"}, yAxis: {name: "지수", scale: true}, '
        'series: ["서울", "경기"].map((r, i) => ({name: r, type: "line", itemStyle: {color: PALETTE[i]}, data: weekly(r).map((d) => [+d.date, d.value])}))}, invalidation)}</div></div>', "",
        "## 내 해석", "", "- 숫자들이 함께 가리키는 방향은 무엇인가?", "- 지수(부동산원·KB)와 실거래 중위가가 다르게 움직인다면 왜인가?", "- 독자가 지금 무엇을 확인해야 하는가?", "",
        "## 이번 주 기사 흐름", "", *[f"- {cite(i)}" for i in news], "",
        "## 참고한 리포트·기사", "", *[f"- [{r['title']}]({r['url']}) — {r['source']}, {r['day']}" for r in reports], "",
        "## SNS용 요약", "", "```text", f"[{title}]", *sns, "#부동산 #아파트 #집값 #부동산시장", "```", "",
        "<p class=\"note\">출처: 국토교통부 실거래가 공개시스템, 한국부동산원 R-ONE, KB부동산. 투자 자문이 아닙니다.</p>", "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"초안: {path.relative_to(ROOT)} (인사이트 {len(facts)}개, 리포트 기사 {len(reports)}건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
