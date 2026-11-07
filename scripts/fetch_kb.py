"""KB부동산 데이터허브(주택가격동향조사)에서 서울·경기 월간 아파트 지표를 받는다.

PublicDataReader.Kbland 는 KB 공식 API가 아니라 공개 웹 데이터를 읽는 라이브러리다.
응답 구조가 바뀌면 실패할 수 있으므로, 실패 시 기존 캐시를 그대로 둔다.

결과: data/apt.duckdb 의 kb_{jeonse_ratio,buyer_index,trade_activity} 테이블 (매번 전체 시계열로 교체)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "apt.duckdb"
SIDO = ["11", "41"]  # 서울, 경기


def save_partition(con, name, code, df):
    if name not in {"jeonse_ratio", "buyer_index", "trade_activity"} or code not in SIDO:
        raise ValueError("잘못된 KB partition")
    if df.empty or "지역코드" not in df or not df["지역코드"].astype(str).str.startswith(code).all():
        raise ValueError("KB 지역 partition 불완전")
    table = f"kb_{name}"
    con.register("kb_incoming", df)
    con.begin()
    try:
        exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchone()[0]
        if exists:
            con.execute(f'DELETE FROM {table} WHERE CAST("지역코드" AS VARCHAR) LIKE ?', [code + "%"])
            con.execute(f"INSERT INTO {table} BY NAME SELECT * FROM kb_incoming")
        else:
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM kb_incoming")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.unregister("kb_incoming")


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
        # 매매·전세 가격지수(priceIndex)는 KB 가 자동 접근을 끊어서 받지 않는다. R-ONE 공식 지수(fetch_rone.py)로 대신한다.
        "jeonse_ratio": lambda c: api.get_jeonse_price_ratio(매물종별구분="01", 지역코드=c),
        "buyer_index": lambda c: api.get_market_trend(메뉴코드="01", 월간주간구분코드="01", 지역코드=c),
        "trade_activity": lambda c: api.get_market_trend(메뉴코드="02", 월간주간구분코드="01", 지역코드=c),
    }
    for name, fn in jobs.items():
        for c in SIDO:
            try:
                df = fn(c)
                if df is None or df.empty:
                    raise ValueError("새 데이터 없음")
                save_partition(con, name, c, df)
                print(f"[kb] {name} {c}: {len(df)}행")
            except Exception as e:
                print(f"[kb] {name} {c} 실패; 기존 지역 유지: {e}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
