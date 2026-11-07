"""국토교통부 아파트 매매·전월세 실거래가를 월 단위로 받아 DuckDB(data/apt.duckdb)에 쌓는다.

- 매매: 서울·경기 전체 시군구(최하위 구 단위) × START_YM 부터 이번 달까지
- 전월세: watchlist.json 에 있는 단지의 시군구만 (호출량 절약)
- 이미 받은 달(fetch_log)은 건너뛰되, 신고가 늦게 들어오는 최근 REFRESH_MONTHS개월은 매번 다시 받아 교체한다.
- 최신 달부터 받으므로, 하루 호출 예산이 끝나면 다음 실행이 더 과거 달을 이어 받는다.

환경변수
  MOLIT_SERVICE_KEY  공공데이터포털에서 받은 일반 인증키(Decoding 키 권장)
  START_YM           수집 시작 월(기본 200601, 국토부 공개 시작 시점)
  REFRESH_MONTHS     다시 받을 최근 개월 수(기본 3)
  MOLIT_DAILY_BUDGET API별 하루 호출 상한(기본 9000, 개발계정 1만 건/일)

테이블
  molit_trade, molit_rent  API 응답 원본(모든 컬럼 VARCHAR) + _sgg, _ym
  fetch_log(kind, sgg, ym) 받은 달 기록. 거래 0건인 달도 남겨 다시 부르지 않는다.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "apt.duckdb"
REGIONS = ROOT / "src" / "data" / "regions.json"
WATCHLIST = ROOT / "src" / "data" / "watchlist.json"

START_YM = os.environ.get("START_YM", "200601")
REFRESH_MONTHS = int(os.environ.get("REFRESH_MONTHS", "3"))
DAILY_BUDGET = int(os.environ.get("MOLIT_DAILY_BUDGET", "9000"))
TABLE = {"trade": "molit_trade", "rent": "molit_rent"}
TRADE_TYPE = {"trade": "매매", "rent": "전월세"}


def month_list(start: str, today: dt.date | None = None) -> list[str]:
    d = (today or dt.date.today()).replace(day=1)
    out = []
    while f"{d.year}{d.month:02d}" >= start:
        out.append(f"{d.year}{d.month:02d}")
        d = (d - dt.timedelta(days=1)).replace(day=1)
    return out  # 최신 달이 앞


def init(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS fetch_log (
        kind VARCHAR, sgg VARCHAR, ym VARCHAR, rows INTEGER, fetched_at TIMESTAMP,
        PRIMARY KEY (kind, sgg, ym))""")


def save(con: duckdb.DuckDBPyConnection, kind: str, sgg: str, ym: str, df: pd.DataFrame | None) -> int:
    """한 시군구·한 달 분을 통째로 교체한다(같은 달을 다시 받아도 중복되지 않음)."""
    table = TABLE[kind]
    df = pd.DataFrame() if df is None else df
    # 응답 컬럼 타입이 달마다 흔들리지 않도록 원본은 문자열로 둔다. 숫자 변환은 데이터 로더가 한다.
    df = df.assign(_sgg=sgg, _ym=ym).astype("string")
    con.begin()
    try:
        exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchall()[0][0]
        if len(df.columns) > 2 or exists:
            con.register("incoming", df)
            if not exists:  # 타입을 응답에서 추론하면 행 0개짜리 응답일 때 "NULL" 타입 컬럼이 생긴다
                cols = ", ".join(f'"{c}" VARCHAR' for c in df.columns)
                con.execute(f"CREATE TABLE {table} ({cols})")
            have = {r[0] for r in con.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'").fetchall()}
            for col in df.columns.difference(list(have)):
                con.execute(f'ALTER TABLE {table} ADD COLUMN "{col}" VARCHAR')
            con.execute(f"DELETE FROM {table} WHERE _sgg = ? AND _ym = ?", [sgg, ym])
            con.execute(f"INSERT INTO {table} BY NAME SELECT * FROM incoming")
            con.unregister("incoming")
        con.execute("INSERT OR REPLACE INTO fetch_log VALUES (?, ?, ?, ?, now())", [kind, sgg, ym, len(df)])
        con.commit()
    except Exception:
        con.rollback()
        raise
    return len(df)


def call(api, kind: str, sgg: str, ym: str, tries: int = 3, backoff: float = 3.0) -> pd.DataFrame | None:
    for i in range(tries):
        try:
            return api.get_data("아파트", TRADE_TYPE[kind], sgg, year_month=ym, translate=False)
        except Exception:  # 연결 리셋 등 일시 오류는 잠시 쉬고 다시 부른다
            if i == tries - 1:
                raise
            time.sleep(backoff * (i + 1))


def collect(api, con: duckdb.DuckDBPyConnection, jobs: dict[str, list[str]], months: list[str],
            refresh: int = REFRESH_MONTHS, budget: int = DAILY_BUDGET, pause: float = 0.15, backoff: float = 3.0) -> dict:
    init(con)
    done = {(k, s, y) for k, s, y in con.execute("SELECT kind, sgg, ym FROM fetch_log").fetchall()}
    recent = set(months[:refresh])
    stats = {}
    for kind, codes in jobs.items():
        calls = failed = 0
        # 달을 바깥 루프로 돌려야 예산이 끝나도 모든 시군구가 같은 기간까지 채워진다.
        for ym in months:
            if calls >= budget:
                print(f"[molit] {kind}: 하루 호출 예산 {budget}건 도달, {ym} 이전은 다음 실행에서 받습니다.")
                break
            for code in codes:
                if (kind, code, ym) in done and ym not in recent:
                    continue
                if calls >= budget:
                    break
                calls += 1
                try:
                    df = call(api, kind, code, ym, backoff=backoff)
                except Exception as e:  # 기록하지 않으므로 다음 실행에서 다시 받는다
                    failed += 1
                    print(f"[molit] {kind} {code} {ym} 실패: {e}", file=sys.stderr)
                    continue
                save(con, kind, code, ym, df)
                time.sleep(pause)
        stats[kind] = {"calls": calls, "failed": failed}
        print(f"[molit] {kind}: 호출 {calls}건, 실패 {failed}건")
    return stats


def main() -> int:
    key = os.environ.get("MOLIT_SERVICE_KEY")
    if not key:
        print("[molit] MOLIT_SERVICE_KEY 가 없어 수집을 건너뜁니다 (샘플 데이터로 빌드됩니다).")
        return 0

    from PublicDataReader import TransactionPrice  # 지연 import

    regions = json.loads(REGIONS.read_text(encoding="utf-8"))
    watch = json.loads(WATCHLIST.read_text(encoding="utf-8")) if WATCHLIST.exists() else []
    jobs = {"trade": [r["code"] for r in regions], "rent": sorted({w["sgg"] for w in watch})}
    DB.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB)) as con:
        collect(TransactionPrice(key), con, jobs, month_list(START_YM))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
