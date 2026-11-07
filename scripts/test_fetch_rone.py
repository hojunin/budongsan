"""fetch_rone.fetch_table 변환 점검: 지수 표(지역=CLS)와 매입자 표(지역=GRP, 구분=CLS)를 같은 긴 형식으로 바꾸고 서울·경기 등만 남긴다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fetch_rone as f  # noqa: E402

ROWS = [
    {"WRTTIME_IDTFR_ID": "202608", "WRTTIME_DESC": "2026년 8월", "GRP_NM": "서울", "GRP_FULLNM": "서울", "CLS_NM": "30대", "CLS_FULLNM": "30대", "ITM_NM": "동(호)수", "ITM_FULLNM": "동(호)수", "UI_NM": "동(호)수", "DTA_VAL": 1935},
    {"WRTTIME_IDTFR_ID": "202608", "WRTTIME_DESC": "2026년 8월", "GRP_NM": "중구", "GRP_FULLNM": "부산>중구", "CLS_NM": "합계", "CLS_FULLNM": "합계", "ITM_NM": "동(호)수", "ITM_FULLNM": "동(호)수", "UI_NM": "동(호)수", "DTA_VAL": 9},
    {"WRTTIME_IDTFR_ID": "202645", "WRTTIME_DESC": "2026-11-02", "GRP_NM": None, "GRP_FULLNM": None, "CLS_NM": "종로구", "CLS_FULLNM": "서울>강북지역>도심권>종로구", "ITM_NM": "지수", "ITM_FULLNM": "지수", "UI_NM": "지수", "DTA_VAL": 101.2},
]


class Resp:
    def json(self):
        return {"SttsApiTblData": [{"head": [{"list_total_count": len(ROWS)}]}, {"row": ROWS}]}


f.requests.get = lambda *a, **k: Resp()
out = f.fetch_table("key", "T", "MM", "201601")
assert list(out.region) == ["서울", "종로구"], out
assert list(out.region_full) == ["서울", "서울>강북지역>도심권>종로구"]
assert list(out.item) == ["30대", "지수"]
assert f.redact("url?KEY=abc123&Type=json") == "url?KEY=***&Type=json"
print("ok")
