"""데이터 로더 공용: data/apt.duckdb 읽기. 수집은 scripts/fetch_*.py 가 한다."""
import os
from pathlib import Path

import duckdb
import pandas as pd

# 배치가 쓰는 중에는 같은 파일을 열 수 없어서, 복사본으로 미리 볼 때 APT_DB 로 경로를 바꾼다.
DB = Path(os.environ.get("APT_DB") or Path(__file__).resolve().parents[2] / "data" / "apt.duckdb")
SITE_MONTHS = int(os.environ.get("SITE_MONTHS", "36"))  # 화면에 보낼 기간. 길수록 Parquet 이 커진다(25 MiB 제한)


def query(sql: str, params: list | None = None) -> pd.DataFrame | None:
    """DB나 테이블이 없으면 None (→ 로더가 샘플을 만든다)."""
    if not DB.exists():
        return None
    with duckdb.connect(str(DB), read_only=True) as con:
        try:
            return con.execute(sql, params or []).df()
        except duckdb.CatalogException:
            return None


def recent(table: str) -> pd.DataFrame:
    since = (pd.Timestamp.today() - pd.DateOffset(months=SITE_MONTHS)).strftime("%Y%m")
    df = query(f"SELECT * FROM {table} WHERE _ym >= ?", [since])
    return pd.DataFrame() if df is None else df
