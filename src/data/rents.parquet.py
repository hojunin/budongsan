"""데이터 로더: 국토부 전월세(data/apt.duckdb, 관심 단지 시군구) → 전세 중심 Parquet (stdout). 없으면 가짜 샘플."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from _db import recent

ROOT = Path(__file__).resolve().parents[2]
WATCH = json.loads((ROOT / "src" / "data" / "watchlist.json").read_text(encoding="utf-8"))

raw = recent("molit_rent")
if len(raw):
    df = pd.DataFrame({
        "sgg": raw["sggCd"].astype(str).str.zfill(5),
        "umd": raw["umdNm"].astype(str).str.strip(),
        "apt": raw["aptNm"].astype(str).str.strip(),
        "area": pd.to_numeric(raw["excluUseAr"], errors="coerce"),
        "deposit": pd.to_numeric(raw["deposit"].astype(str).str.replace(",", ""), errors="coerce"),
        "monthly": pd.to_numeric(raw["monthlyRent"].astype(str).str.replace(",", ""), errors="coerce").fillna(0),
    })
    df["deal_date"] = pd.to_datetime(dict(year=raw["dealYear"].astype(int), month=raw["dealMonth"].astype(int), day=raw["dealDay"].astype(int)), errors="coerce")
    df["is_sample"] = False
else:
    rng = np.random.default_rng(11)
    months = pd.date_range(end=pd.Timestamp.today().normalize(), periods=36, freq="MS")
    rows = []
    for w in WATCH:
        base = rng.uniform(250, 650)
        for i, m in enumerate(months):
            for _ in range(int(rng.poisson(4))):
                area = float(rng.choice([59.9, 84.9]))
                rows.append(dict(sgg=w["sgg"], umd=w["umd"], apt=w["match"], area=area,
                                 deposit=round(base * (1 + .003 * i) * area * rng.normal(1, .07) / 100) * 100,
                                 monthly=0 if rng.random() < .6 else int(rng.integers(30, 150)),
                                 deal_date=m + pd.Timedelta(days=int(rng.integers(0, 27))), is_sample=True))
    df = pd.DataFrame(rows)

df = df.dropna(subset=["area", "deposit", "deal_date"])
df["ym"] = df["deal_date"].dt.strftime("%Y-%m")
df["band"] = pd.cut(df["area"], [0, 50, 67, 80, 90, 115, 1e9], right=False,
                    labels=["~49", "59", "74", "84", "100", "115+"]).astype(str)
df["jeonse"] = df["monthly"].eq(0)
df["complex_key"] = df["sgg"] + "|" + df["umd"] + "|" + df["apt"]
df["deal_date"] = df["deal_date"].dt.date
sys.stdout.buffer.write(df.to_parquet(index=False, compression="zstd"))  # pandas 2.2.3 + pyarrow 26: to_parquet(stdout) writes 0 bytes
