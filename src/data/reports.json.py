"""데이터 로더: 발행한 리포트(src/reports/*.md)의 머리말 목록 → JSON. index.md 와 _ 로 시작하는 파일은 뺀다."""
import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parents[1] / "reports"


def front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    head = text.split("---", 2)[1]
    meta = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip():
            meta[key.strip()] = value.strip().strip('"')
    return meta


posts = []
for f in sorted(DIR.glob("*.md"), reverse=True):
    if f.name == "index.md" or f.name.startswith("_"):
        continue
    meta = front_matter(f.read_text(encoding="utf-8"))
    posts.append({"slug": f.stem, "title": meta.get("title", f.stem), "date": meta.get("date", f.stem[:10]),
                  "summary": meta.get("summary", ""), "tags": meta.get("tags", "")})
json.dump(posts, sys.stdout, ensure_ascii=False)
