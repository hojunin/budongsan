"""데이터 로더: 매매 실거래 전 기간(최근 10년) 월별 집계 → 장기 추이용 작은 Parquet.

한 행 = (월, 지역). 지역은 시군구(level=sgg)와 시도 전체(level=sido: 11 서울, 41 경기).
시도 값을 시군구 중위값으로 다시 집계하면 틀리므로 시도도 거래 원본에서 직접 계산한다.
DB가 없으면 빈 파일을 낸다(화면은 '데이터 없음').
"""
import json
import sys
from pathlib import Path

import pandas as pd

from _db import query

ROOT = Path(__file__).resolve().parents[2]
NAMES = {r["code"]: r["name"] for r in json.loads((ROOT / "src" / "data" / "regions.json").read_text(encoding="utf-8"))}
NAMES.update({"11": "서울 전체", "41": "경기 전체"})

df = query("""
WITH t AS (
  SELECT _ym AS ym, lpad(sggCd, 5, '0') AS sgg, left(lpad(sggCd, 5, '0'), 2) AS sido,
         TRY_CAST(replace(dealAmount, ',', '') AS DOUBLE) AS price,
         TRY_CAST(excluUseAr AS DOUBLE) AS area
  FROM molit_trade
  WHERE coalesce(trim(cdealType), '') <> 'O'
)
SELECT ym, CASE WHEN GROUPING(sgg) = 0 THEN sgg ELSE sido END AS code,
       CASE WHEN GROUPING(sgg) = 0 THEN 'sgg' ELSE 'sido' END AS level,
       count(*) AS n,
       median(price / area) AS ppm2_med,
       median(price) AS price_med,
       median(price) FILTER (WHERE area >= 80 AND area < 90) AS price84_med,
       count(*) FILTER (WHERE area >= 80 AND area < 90) AS n84
FROM t WHERE price > 0 AND area > 0
GROUP BY GROUPING SETS ((ym, sido, sgg), (ym, sido))
""")

if df is None or df.empty:
    df = pd.DataFrame({c: pd.Series(dtype=t) for c, t in
                       [("ym", "string"), ("code", "string"), ("level", "string"), ("name", "string"), ("n", "int64"),
                        ("ppm2_med", "float64"), ("price_med", "float64"), ("price84_med", "float64"), ("n84", "int64")]})
else:
    df["name"] = df["code"].map(NAMES).fillna(df["code"])
    df["ym"] = df["ym"].str[:4] + "-" + df["ym"].str[4:]
    df = df.sort_values(["level", "code", "ym"])

sys.stdout.buffer.write(df.to_parquet(index=False, compression="zstd"))
