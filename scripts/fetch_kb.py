"""KB부동산 데이터허브(주택가격동향조사)에서 서울·경기 월간 아파트 지표를 받는다.

PublicDataReader.Kbland 는 KB 공식 API가 아니라 공개 웹 데이터를 읽는 라이브러리다.
응답 구조가 바뀌면 실패할 수 있으므로, 실패 시 기존 캐시를 그대로 둔다.

결과: data/apt.duckdb 의 kb_{price_sale,price_jeonse,jeonse_ratio,buyer_index,trade_activity} 테이블 (매번 전체 시계열로 교체)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "apt.duckdb"
SIDO = ["11", "41"]  # 서울, 경기


def main() -> int:
    try:
        import duckdb
        import pandas as pd
        from PublicDataReader import Kbland
    except ImportError as e:
        print(f"[kb] 라이브러리 없음: {e}")
        return 0

    api = Kbland()
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))

    jobs = {
        "price_sale": lambda c: api.get_price_index(월간주간구분코드="01", 매물종별구분="01", 매매전세코드="01", 지역코드=c),
        "price_jeonse": lambda c: api.get_price_index(월간주간구분코드="01", 매물종별구분="01", 매매전세코드="02", 지역코드=c),
        "jeonse_ratio": lambda c: api.get_jeonse_price_ratio(매물종별구분="01", 지역코드=c),
        "buyer_index": lambda c: api.get_market_trend(메뉴코드="01", 월간주간구분코드="01", 지역코드=c),
        "trade_activity": lambda c: api.get_market_trend(메뉴코드="02", 월간주간구분코드="01", 지역코드=c),
    }
    for name, fn in jobs.items():
        frames = []
        for c in SIDO:
            try:
                df = fn(c)
                if df is not None and len(df):
                    frames.append(df)
            except Exception as e:
                print(f"[kb] {name} {c} 실패: {e}")
        if frames:
            df = pd.concat(frames, ignore_index=True)  # noqa: F841 (duckdb 가 이름으로 읽는다)
            con.execute(f"CREATE OR REPLACE TABLE kb_{name} AS SELECT * FROM df")
            print(f"[kb] {name}: {sum(len(f) for f in frames)}행")
        else:
            print(f"[kb] {name}: 새 데이터 없음 — 기존 테이블 유지")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
