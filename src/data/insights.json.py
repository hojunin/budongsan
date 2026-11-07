"""데이터 로더: 자동 인사이트(문장형 사실) 목록 → JSON. 계산은 _insights.py."""
import json
import sys
from pathlib import Path

from _insights import build

ROOT = Path(__file__).resolve().parents[2]
names = {r["code"]: r["name"] for r in json.loads((ROOT / "src" / "data" / "regions.json").read_text(encoding="utf-8"))}
json.dump(build(names), sys.stdout, ensure_ascii=False)
