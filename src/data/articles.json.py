"""데이터 로더: 최근 수집한 기사·리포트 헤드라인 (제목·언론사·날짜·링크만) → JSON."""
import json
import sys

from _db import query

df = query("""SELECT title, source, strftime(published, '%Y-%m-%d %H:%M') AS published, category, feed, url
              FROM articles WHERE published >= now() - INTERVAL 60 DAY
              ORDER BY published DESC NULLS LAST LIMIT 1500""")
rows = [] if df is None else df.to_dict("records")
json.dump(rows, sys.stdout, ensure_ascii=False)
