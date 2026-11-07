"""한국부동산원 R-ONE 통계 → data/apt.duckdb 의 rone 테이블 (긴 형식, 표마다 통째로 교체).

전국·수도권·서울·경기 지역만 남긴다. 첫 실행은 최근 10년을, 이후에는 표마다 마지막 4개 시점부터만 다시 받는다(수정 반영). KB 가격지수 API 가 자동 접근을 막아서, 매매·전세 지수는 여기 공식 통계를 쓴다.

환경변수 REB_API_KEY  R-ONE 오픈API 인증키
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("APT_DB") or ROOT / "data" / "apt.duckdb")
URL = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"
PAGE = 1000
KEEP = ("전국", "수도권", "서울", "경기")  # CLS_FULLNM 의 첫 마디

# metric: (STATBL_ID, 주기)
TABLES = {
    "wk_sale_index": ("T244183132827305", "WK"),     # (주) 매매가격지수
    "wk_jeonse_index": ("T247713133046872", "WK"),   # (주) 전세가격지수
    "wk_sale_supply": ("T248163133074619", "WK"),    # (주) 매매수급동향 (100 = 균형)
    "wk_jeonse_supply": ("T245423133086632", "WK"),  # (주) 전세수급동향
    "mm_sale_index": ("A_2024_00178", "MM"),         # (월) 매매지수_아파트
    "mm_jeonse_index": ("A_2024_00182", "MM"),       # (월) 전세지수_아파트
    "mm_sale_median": ("A_2024_00189", "MM"),        # (월) 매매 중위가격_아파트
    "mm_jeonse_median": ("A_2024_00193", "MM"),      # (월) 전세 중위가격_아파트
    "mm_conversion": ("A_2024_00156", "MM"),         # 전월세 전환율_아파트
    "mm_buyer_residence": ("A_2024_00609", "MM"),    # (월) 매입자거주지별 아파트매매거래
    "mm_buyer_age": ("A_2024_00610", "MM"),          # (월) 매입자연령대별 아파트매매거래
}
# 지역이 GRP 에 있는 표. 전국 시군구라 통째로 받으면 수십만 행이어서, 서울·경기 GRP_ID 만 골라 받는다.
BY_GROUP = {"mm_buyer_residence", "mm_buyer_age"}


def redact(text: str) -> str:
    return re.sub(r"KEY=[^&\s'\"]+", "KEY=***", text)


def fetch_rows(key: str, statbl: str, cycle: str, **filters) -> list[dict]:
    rows, page, total = [], 1, None
    while total is None or len(rows) < total:
        for attempt in range(3):
            try:
                r = requests.get(URL, params={"KEY": key, "Type": "json", "pIndex": page, "pSize": PAGE,
                                              "STATBL_ID": statbl, "DTACYCLE_CD": cycle, **filters}, timeout=60)
                r.raise_for_status()
                body = r.json()["SttsApiTblData"]
                break
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(redact(str(e))) from None
                time.sleep(3 * (attempt + 1))
        count = int(body[0]["head"][0]["list_total_count"])
        if count < 0 or (total is not None and count != total):
            raise ValueError("R-ONE 전체 건수 변경")
        total = count
        chunk = body[1]["row"] if total else []
        if not isinstance(chunk, list) or (not chunk and len(rows) < total) or len(rows) + len(chunk) > total:
            raise ValueError("R-ONE 페이지 불완전")
        rows += chunk
        page += 1
    return rows


def fetch_table(key: str, statbl: str, cycle: str, start: str, by_group: bool = False) -> pd.DataFrame:
    if by_group:
        recent = time.strftime("%Y%m", time.localtime(time.time() - 120 * 86400))  # 최근 몇 달로 지역 목록만 얻는다
        groups = {r["GRP_ID"] for r in fetch_rows(key, statbl, cycle, START_WRTTIME=recent)
                  if r.get("GRP_FULLNM") and r["GRP_FULLNM"].split(">")[0] in KEEP}
        if not groups:
            raise ValueError("R-ONE 지역 목록 없음")
        rows = [r for g in sorted(groups) for r in fetch_rows(key, statbl, cycle, START_WRTTIME=start, GRP_ID=g)]
    else:
        rows = fetch_rows(key, statbl, cycle, START_WRTTIME=start)
    if not rows:
        return pd.DataFrame(columns=["period", "period_desc", "region", "region_full", "item", "unit", "value"])
    df = pd.DataFrame(rows)
    # 지수·가격 표는 지역이 CLS 에 있고, 매입자 표(거주지·연령대)는 지역이 GRP, 매입자 구분이 CLS 에 있다.
    grouped = df["GRP_FULLNM"].notna() if "GRP_FULLNM" in df else pd.Series(False, index=df.index)
    full = df["GRP_FULLNM"].where(grouped, df["CLS_FULLNM"].fillna(df["CLS_NM"])).astype(str)
    name = df["GRP_NM"].where(grouped, df["CLS_NM"]).astype(str)
    item = df["CLS_NM"].where(grouped, df["ITM_FULLNM"].fillna(df["ITM_NM"])).astype(str)
    keep = full.str.split(">").str[0].isin(KEEP)
    df, full, name, item = df[keep], full[keep], name[keep], item[keep]
    return pd.DataFrame({
        "period": df["WRTTIME_IDTFR_ID"].astype(str),
        "period_desc": df["WRTTIME_DESC"].astype(str),
        "region": name,
        "region_full": full,
        "item": item,
        "unit": df["UI_NM"].astype(str),
        "value": pd.to_numeric(df["DTA_VAL"], errors="coerce"),
    })


def main() -> int:
    key = os.environ.get("REB_API_KEY")
    if not key:
        print("[rone] REB_API_KEY 가 없어 수집을 건너뜁니다.")
        return 0
    DB.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB)) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS rone (metric VARCHAR, cycle VARCHAR, period VARCHAR, period_desc VARCHAR,
            region VARCHAR, region_full VARCHAR, item VARCHAR, unit VARCHAR, value DOUBLE)""")
        for metric, (statbl, cycle) in TABLES.items():
            t = time.time()
            start = con.execute("""SELECT period FROM (SELECT DISTINCT period FROM rone WHERE metric = ?)
                                   ORDER BY period DESC LIMIT 1 OFFSET 3""", [metric]).fetchall()
            # 처음 받는 표는 최근 10년부터만 받는다 (WK=YYYYWW, MM=YYYYMM 모두 'YYYY01' 로 시작점을 줄 수 있다)
            start = start[0][0] if start else f"{time.localtime().tm_year - 10}01"
            try:
                df = fetch_table(key, statbl, cycle, start, metric in BY_GROUP)
            except Exception as e:  # 표 하나가 실패해도 나머지는 받고, 실패한 표는 기존 값을 유지한다
                print(f"[rone] {metric} 실패: {redact(str(e))}", file=sys.stderr)
                continue
            df.insert(0, "cycle", cycle)
            df.insert(0, "metric", metric)
            if df.empty:
                print(f"[rone] {metric}: 검증할 행이 없어 기존 자료를 유지합니다.", file=sys.stderr)
                continue
            con.begin()
            try:
                con.execute("DELETE FROM rone WHERE metric = ? AND period >= ?", [metric, start])
                con.execute("INSERT INTO rone BY NAME SELECT * FROM df")
                con.commit()
            except Exception:
                con.rollback()
                raise
            print(f"[rone] {metric}: {len(df)}행, {df['period'].min()}~{df['period'].max()} ({time.time() - t:.0f}초)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
