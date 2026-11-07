"""데이터 로더: 한국부동산원 R-ONE 지표(최근 10년) → 긴 형식 Parquet.

컬럼: metric, cycle(WK/MM), date, region, region_full, item, unit, value
DB가 없으면 빈 파일(화면은 '데이터 없음').
"""
import sys

import pandas as pd

from _db import query

df = query("""
SELECT metric, cycle,
       CASE WHEN cycle = 'WK' THEN TRY_CAST(period_desc AS DATE)
            ELSE make_date(CAST(left(period, 4) AS INT), CAST(right(period, 2) AS INT), 1) END AS date,
       region, region_full, item, unit, value
FROM rone WHERE value IS NOT NULL
""")
if df is None or df.empty:
    df = pd.DataFrame({c: pd.Series(dtype=t) for c, t in [("metric", "string"), ("cycle", "string"), ("date", "datetime64[ns]"),
        ("region", "string"), ("region_full", "string"), ("item", "string"), ("unit", "string"), ("value", "float64")]})
else:
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= pd.Timestamp.today() - pd.DateOffset(years=10)].sort_values(["metric", "region_full", "item", "date"])

df["date"] = df["date"].dt.date
sys.stdout.buffer.write(df.to_parquet(index=False, compression="zstd"))
