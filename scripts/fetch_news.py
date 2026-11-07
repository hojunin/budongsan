"""부동산 기사·리포트 헤드라인 → data/apt.duckdb 의 articles 테이블 (url 기준 upsert).

저작권 때문에 제목·언론사·날짜·링크만 저장한다. 본문과 요약은 저장하지도 보여 주지도 않는다.
RSS 를 공개하는 곳만 기본 요청으로 읽는다. 응답이 비면(차단·주소 변경) 건너뛰고 다른 출처를 계속 받는다.
"""
from __future__ import annotations

import calendar
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

import duckdb
import feedparser
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("APT_DB") or ROOT / "data" / "apt.duckdb")


def google(q: str) -> str:
    return f"https://news.google.com/rss/search?q={quote(q)}+when:30d&hl=ko&gl=KR&ceid=KR:ko"


# (출처 이름, URL, 분류) — 분류: news(기사) / report(연구기관·정부 보고서와 그 보도)
FEEDS = [
    ("Google 뉴스: 아파트 시장", google("아파트 매매 시장"), "news"),
    ("Google 뉴스: 전세", google("아파트 전세 시장"), "news"),
    ("Google 뉴스: 부동산 정책", google("부동산 대책 OR 부동산 정책"), "news"),
    ("Google 뉴스: 청약·분양", google("청약 OR 분양 아파트"), "news"),
    ("Google 뉴스: 재건축·재개발", google("재건축 OR 재개발"), "news"),
    ("Google 뉴스: 시장 전망 리포트", google("부동산 전망 보고서 OR 리포트"), "report"),
    ("Google 뉴스: 한국부동산원 동향", google("한국부동산원 주간 아파트 가격 동향"), "report"),
    ("Google 뉴스: KB 시장동향", google("KB부동산 주택가격동향 OR KB경영연구소 부동산"), "report"),
    ("Google 뉴스: 국토연구원·주산연", google("국토연구원 OR 주택산업연구원 주택시장"), "report"),
    ("서울경제 부동산", "https://www.sedaily.com/rss/realestate", "news"),
    ("아시아경제 부동산", "https://www.asiae.co.kr/rss/realestate.htm", "news"),
]
REPORT_WORDS = re.compile(r"보고서|리포트|전망|동향|브리핑|연구원|통계|지수")
# 정책·금리 검색에는 다른 분야 기사도 섞여서, 제목에 부동산 단어가 있는 것만 남긴다
TOPIC = re.compile(r"아파트|부동산|주택|집값|전세|월세|매매|청약|분양|재건축|재개발|입주|임대|토지|공시가|LTV|DSR|주담대|대출|부동산원|KB")


def split_source(title: str, entry) -> tuple[str, str]:
    """Google 뉴스 제목은 '제목 - 언론사' 형식이다."""
    src = (entry.get("source") or {}).get("title")
    if src and title.endswith(f" - {src}"):
        return title[: -len(src) - 3].strip(), src
    if " - " in title and not src:
        head, _, tail = title.rpartition(" - ")
        if len(tail) <= 20:
            return head.strip(), tail.strip()
    return title.strip(), src or ""


def parse(feed_name: str, url: str, category: str) -> list[dict]:
    content = requests.get(url, timeout=20).content
    out = []
    for e in feedparser.parse(content).entries:
        link, title = e.get("link"), e.get("title")
        if not link or not title:
            continue
        title, source = split_source(title, e)
        if not TOPIC.search(title):
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        out.append({
            "url": link, "title": title, "source": source or feed_name.split(":")[0],
            "published": pd.Timestamp(calendar.timegm(ts), unit="s", tz="UTC").tz_convert("Asia/Seoul").tz_localize(None) if ts else pd.NaT,
            "category": "report" if category == "report" or REPORT_WORDS.search(title) else "news",
            "feed": feed_name,
        })
    return out


def main() -> int:
    rows = []
    for name, url, category in FEEDS:
        try:
            got = parse(name, url, category)
            print(f"[news] {name}: {len(got)}건")
            rows += got
        except Exception as e:  # 출처 하나가 막혀도 나머지는 받는다
            print(f"[news] {name} 실패: {e}", file=sys.stderr)
    if not rows:
        return 0
    df = pd.DataFrame(rows).drop_duplicates("url")
    # 같은 기사가 여러 검색에 걸리면 첫 분류를 유지하되, 리포트로 잡힌 적이 있으면 리포트로 둔다
    df = df.assign(fetched_at=pd.Timestamp.now())
    DB.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB)) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS articles (url VARCHAR PRIMARY KEY, title VARCHAR, source VARCHAR,
            published TIMESTAMP, category VARCHAR, feed VARCHAR, fetched_at TIMESTAMP)""")
        con.execute("""INSERT INTO articles BY NAME SELECT * FROM df
            ON CONFLICT (url) DO UPDATE SET title = excluded.title, source = excluded.source,
              category = CASE WHEN articles.category = 'report' THEN 'report' ELSE excluded.category END""")
        total = con.execute("SELECT count(*) FROM articles").fetchall()[0][0]
    print(f"[news] 새로 받은 {len(df)}건, 누적 {total}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
