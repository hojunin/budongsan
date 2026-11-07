"""fetch_molit.collect 자체 점검 (가짜 API, 임시 DB). 실행: .venv/bin/python scripts/test_fetch_molit.py"""
import datetime as dt
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from fetch_molit import collect, month_list  # noqa: E402


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.flaky = {("11110", "202410")}  # 첫 호출은 연결 리셋

    def get_data(self, _prop, kind, code, year_month, translate):
        self.calls.append((kind, code, year_month))
        if (code, year_month) in self.flaky:
            self.flaky.discard((code, year_month))
            raise ConnectionResetError(104, "Connection reset by peer")
        if year_month == "202408":
            return None  # 거래 0건인 달
        n = 2 if kind == "매매" else 1
        return pd.DataFrame({"sggCd": [code] * n, "dealAmount": ["90,000"] * n, "dealYear": [year_month[:4]] * n,
                             "aptSeq": [f"{code}-{i}" for i in range(n)]})


assert month_list("202408", dt.date(2024, 10, 15)) == ["202410", "202409", "202408"]
months = month_list("202408", dt.date(2024, 10, 15))
jobs = {"trade": ["11110", "11140"], "rent": ["11110"]}
con = duckdb.connect()  # 메모리 DB
api = FakeAPI()

s = collect(api, con, jobs, months, refresh=1, pause=0, backoff=0)
assert s == {"trade": {"calls": 6, "failed": 0}, "rent": {"calls": 3, "failed": 0}}, s
assert len(api.calls) == 10  # 재시도 1회 포함
assert con.execute("SELECT count(*) FROM molit_trade").fetchall()[0][0] == 2 * 2 * 2  # 2개 구 × 2개 달(빈 달 제외) × 2건
assert con.execute("SELECT count(*) FROM fetch_log WHERE ym = '202408'").fetchall()[0][0] == 3  # 빈 달도 기록

api.calls.clear()
s = collect(api, con, jobs, months, refresh=1, pause=0, backoff=0)
assert sorted(api.calls) == [("매매", "11110", "202410"), ("매매", "11140", "202410"), ("전월세", "11110", "202410")], api.calls
assert con.execute("SELECT count(*) FROM molit_trade").fetchall()[0][0] == 8  # 최근 달은 교체되어 중복 없음

con2 = duckdb.connect()
s = collect(FakeAPI(), con2, {"trade": ["11110", "11140"]}, months, refresh=0, budget=3, pause=0, backoff=0)
assert s["trade"]["calls"] == 3, s
assert con2.execute("SELECT count(DISTINCT ym) FROM fetch_log").fetchall()[0][0] == 2  # 최신 달부터 채운다
print("ok")
