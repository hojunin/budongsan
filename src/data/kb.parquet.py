"""데이터 로더: KB 지표(data/apt.duckdb 의 kb_* 테이블) → 긴 형식(metric, region_code, region, date, value) Parquet. 없으면 가짜 샘플."""
import sys

import numpy as np
import pandas as pd

from _db import query

VALUE_COL = {
    "price_sale": "가격지수",
    "price_jeonse": "가격지수",
    "jeonse_ratio": None,  # 마지막 숫자 컬럼 사용
    "buyer_index": "매수우위지수",
    "trade_activity": "매매거래지수",
}

tables = {m: d for m in VALUE_COL if (d := query(f"SELECT * FROM kb_{m}")) is not None}

frames = []
for metric, col in VALUE_COL.items():
    if metric not in tables:
        continue
    d = tables[metric]
    if col is None or col not in d.columns:
        num = [c for c in d.columns if pd.api.types.is_numeric_dtype(d[c]) and c not in ("지역코드",)]
        if not num:
            continue
        col = num[-1]
    frames.append(pd.DataFrame({
        "metric": metric,
        "region_code": d["지역코드"].astype(str),
        "region": d["지역명"].astype(str),
        "date": pd.to_datetime(d["날짜"]),
        "value": pd.to_numeric(d[col], errors="coerce"),
        "is_sample": False,
    }))

if frames:
    df = pd.concat(frames, ignore_index=True).dropna(subset=["value"])
else:
    rng = np.random.default_rng(3)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=60, freq="MS")
    regions = [("11", "서울"), ("41", "경기"), ("1100000001", "서울 강북14개구"), ("1100000002", "서울 강남11개구")]
    rows = []
    for code, name in regions:
        walk = np.cumsum(rng.normal(0.2, 0.6, len(dates)))
        for i, d in enumerate(dates):
            rows += [
                dict(metric="price_sale", region_code=code, region=name, date=d, value=95 + walk[i]),
                dict(metric="price_jeonse", region_code=code, region=name, date=d, value=97 + walk[i] * .6),
                dict(metric="jeonse_ratio", region_code=code, region=name, date=d, value=52 + rng.normal(0, 1.2)),
                dict(metric="buyer_index", region_code=code, region=name, date=d, value=max(5, 70 + 30 * np.sin(i / 8) + rng.normal(0, 6))),
                dict(metric="trade_activity", region_code=code, region=name, date=d, value=max(3, 30 + 20 * np.sin(i / 7) + rng.normal(0, 5))),
            ]
    df = pd.DataFrame(rows)
    df["is_sample"] = True

df["date"] = pd.to_datetime(df["date"]).dt.date  # date32
sys.stdout.buffer.write(df.to_parquet(index=False, compression="zstd"))  # pandas 2.2.3 + pyarrow 26: to_parquet(stdout) writes 0 bytes
