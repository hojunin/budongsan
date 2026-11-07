"""데이터 로더: KB 캐시 → 긴 형식(metric, region_code, region, date, value) Parquet. 없으면 가짜 샘플."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache" / "kb"

VALUE_COL = {
    "price_sale": "가격지수",
    "price_jeonse": "가격지수",
    "jeonse_ratio": None,  # 마지막 숫자 컬럼 사용
    "buyer_index": "매수우위지수",
    "trade_activity": "매매거래지수",
}

frames = []
for metric, col in VALUE_COL.items():
    f = CACHE / f"{metric}.parquet"
    if not f.exists():
        continue
    d = pd.read_parquet(f)
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
df.to_parquet(sys.stdout.buffer, index=False, compression="zstd")
