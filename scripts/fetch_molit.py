"""국토교통부 아파트 매매·전월세 실거래가를 월 단위로 받아 캐시에 쌓는다.

- 매매: 서울·경기 전체 시군구(최하위 구 단위) × 최근 MONTHS개월
- 전월세: watchlist.json 에 있는 단지의 시군구만 (호출량 절약)
- 이미 받은 달은 건너뛰되, 신고가 늦게 들어오는 최근 REFRESH_MONTHS개월은 매번 다시 받는다.

환경변수
  MOLIT_SERVICE_KEY  공공데이터포털에서 받은 일반 인증키(Decoding 키 권장)
  MONTHS             수집 기간(기본 36)
  REFRESH_MONTHS     다시 받을 최근 개월 수(기본 3)

캐시 위치: data/cache/molit/{trade|rent}/{시군구코드}/{YYYYMM}.parquet
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache" / "molit"
REGIONS = ROOT / "src" / "data" / "regions.json"
WATCHLIST = ROOT / "src" / "data" / "watchlist.json"

MONTHS = int(os.environ.get("MONTHS", "36"))
REFRESH_MONTHS = int(os.environ.get("REFRESH_MONTHS", "3"))
DAILY_BUDGET = int(os.environ.get("MOLIT_DAILY_BUDGET", "9000"))  # 개발계정 1만 건/일 여유분


def month_list(n: int) -> list[str]:
    today = dt.date.today().replace(day=1)
    out = []
    y, m = today.year, today.month
    for _ in range(n):
        out.append(f"{y}{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out  # 최신 달이 앞


def main() -> int:
    key = os.environ.get("MOLIT_SERVICE_KEY")
    if not key:
        print("[molit] MOLIT_SERVICE_KEY 가 없어 수집을 건너뜁니다 (샘플 데이터로 빌드됩니다).")
        return 0

    from PublicDataReader import TransactionPrice  # 지연 import

    api = TransactionPrice(key)
    regions = json.loads(REGIONS.read_text(encoding="utf-8"))
    trade_codes = [r["code"] for r in regions]
    watch = json.loads(WATCHLIST.read_text(encoding="utf-8")) if WATCHLIST.exists() else []
    rent_codes = sorted({w["sgg"] for w in watch})

    months = month_list(MONTHS)
    refresh = set(months[:REFRESH_MONTHS])
    calls = 0

    for kind, codes in (("trade", trade_codes), ("rent", rent_codes)):
        trade_type = "매매" if kind == "trade" else "전월세"
        for code in codes:
            for ym in months:
                path = CACHE / kind / code / f"{ym}.parquet"
                if path.exists() and ym not in refresh:
                    continue
                if calls >= DAILY_BUDGET:
                    print(f"[molit] 일일 호출 예산 {DAILY_BUDGET}건 도달 — 다음 실행에서 이어 받습니다.")
                    return 0
                try:
                    df = api.get_data("아파트", trade_type, code, year_month=ym, translate=False)
                except Exception as e:  # 네트워크·키 오류는 다음 실행에서 재시도
                    print(f"[molit] {kind} {code} {ym} 실패: {e}", file=sys.stderr)
                    calls += 1
                    continue
                calls += 1
                path.parent.mkdir(parents=True, exist_ok=True)
                (df if df is not None else pd.DataFrame()).to_parquet(path, index=False)
                time.sleep(0.15)
        print(f"[molit] {kind}: {len(codes)}개 시군구 완료")
    print(f"[molit] 호출 {calls}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
