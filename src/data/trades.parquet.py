"""데이터 로더: 국토부 매매 실거래 캐시 → 브라우저용 정제 Parquet (stdout).

캐시가 비어 있으면(인증키 없이 로컬 빌드) 화면 개발용 **가짜 샘플**을 만들고 is_sample=True 로 표시한다.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache" / "molit" / "trade"
REGIONS = json.loads((ROOT / "src" / "data" / "regions.json").read_text(encoding="utf-8"))
WATCH = json.loads((ROOT / "src" / "data" / "watchlist.json").read_text(encoding="utf-8"))
SGG_NAME = {r["code"]: r["name"] for r in REGIONS}

BANDS = [(0, 50, "~49"), (50, 67, "59"), (67, 80, "74"), (80, 90, "84"), (90, 115, "100"), (115, 1e9, "115+")]


def band_of(a: float) -> str:
    for lo, hi, name in BANDS:
        if lo <= a < hi:
            return name
    return "기타"


def load_cache() -> pd.DataFrame:
    files = list(CACHE.glob("*/*.parquet"))
    frames = [pd.read_parquet(f) for f in files]
    frames = [f for f in frames if len(f)]
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame({
        "sgg": raw["sggCd"].astype(str).str.zfill(5),
        "umd": raw["umdNm"].astype(str).str.strip(),
        "apt": raw["aptNm"].astype(str).str.strip(),
        "apt_seq": raw.get("aptSeq", pd.Series([""] * len(raw))).astype(str),
        "jibun": raw["jibun"].astype(str),
        "area": pd.to_numeric(raw["excluUseAr"], errors="coerce"),
        "price": pd.to_numeric(raw["dealAmount"].astype(str).str.replace(",", ""), errors="coerce"),
        "floor": pd.to_numeric(raw["floor"], errors="coerce"),
        "build_year": pd.to_numeric(raw["buildYear"], errors="coerce"),
        "canceled": raw.get("cdealType", pd.Series([""] * len(raw))).astype(str).str.strip().eq("O"),
        "direct": raw.get("dealingGbn", pd.Series([""] * len(raw))).astype(str).str.contains("직거래"),
        "buyer": raw.get("buyerGbn", pd.Series([""] * len(raw))).astype(str).str.strip(),
    })
    out["deal_date"] = pd.to_datetime(dict(year=raw["dealYear"].astype(int), month=raw["dealMonth"].astype(int), day=raw["dealDay"].astype(int)), errors="coerce")
    out["is_sample"] = False
    return out.dropna(subset=["area", "price", "deal_date"])


def make_sample() -> pd.DataFrame:
    """가짜 데이터. 실제 시세가 아님 — 화면 구성 확인용."""
    rng = np.random.default_rng(7)
    months = pd.date_range(end=pd.Timestamp.today().normalize(), periods=36, freq="MS")
    codes = sorted({w["sgg"] for w in WATCH} | {"11215", "11230", "11290", "41135", "41465", "41450"})
    rows = []
    for code in codes:
        base = rng.uniform(450, 1300)  # 만원/㎡ 수준의 가짜 기준값
        apts = [f"샘플단지{code[-3:]}-{i}" for i in range(6)] + [w["match"] for w in WATCH if w["sgg"] == code]
        for i, m in enumerate(months):
            trend = 1 + 0.004 * i + 0.03 * np.sin(i / 6)
            n = int(rng.poisson(60 * (1 + 0.5 * np.sin(i / 5 + int(code) % 7))))
            for _ in range(n):
                area = float(rng.choice([39.7, 49.9, 59.9, 74.5, 84.9, 101.2, 134.8], p=[.08, .1, .3, .12, .3, .06, .04]))
                apt = rng.choice(apts)
                ppm2 = base * trend * rng.normal(1, 0.08)
                rows.append(dict(sgg=code, umd="샘플동", apt=apt, apt_seq=f"{code}-{apt}", jibun="0",
                                 area=area, price=round(ppm2 * area / 100) * 100, floor=int(rng.integers(1, 25)),
                                 build_year=int(rng.integers(1988, 2023)), canceled=bool(rng.random() < 0.04),
                                 direct=bool(rng.random() < 0.08), buyer="개인",
                                 deal_date=m + pd.Timedelta(days=int(rng.integers(0, 27))), is_sample=True))
    return pd.DataFrame(rows)


df = load_cache()
if df.empty:
    df = make_sample()

df["sgg_name"] = df["sgg"].map(SGG_NAME).fillna(df["sgg"])
df["sido"] = df["sgg"].str[:2]
df["band"] = df["area"].map(band_of)
df["ppm2"] = (df["price"] / df["area"]).round(1)  # 만 원/㎡
df["ym"] = df["deal_date"].dt.strftime("%Y-%m")
df["complex_key"] = df["sgg"] + "|" + df["umd"] + "|" + df["apt"]

# 신고가: 같은 단지·평형에서 이전(해제 제외) 최고가를 넘은 거래
df = df.sort_values("deal_date")
valid = ~df["canceled"]
prev_max = df[valid].groupby(["complex_key", "band"])["price"].transform(lambda s: s.shift().cummax())
df["new_high"] = False
df.loc[prev_max.index, "new_high"] = (df.loc[prev_max.index, "price"] > prev_max).fillna(False)

cols = ["deal_date", "ym", "sido", "sgg", "sgg_name", "umd", "apt", "complex_key", "area", "band",
        "price", "ppm2", "floor", "build_year", "canceled", "direct", "buyer", "new_high", "is_sample"]
df["deal_date"] = df["deal_date"].dt.date  # date32 → 브라우저에서 Date
df[cols].to_parquet(sys.stdout.buffer, index=False, compression="zstd")
