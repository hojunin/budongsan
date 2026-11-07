"""서울·경기 시군구 코드표(src/data/regions.json)를 다시 만든다.

국토부 실거래 API의 LAWD_CD 는 법정동코드 앞 5자리이고, 구가 있는 시는 구 단위로 조회해야 한다.
그래서 하위 구가 있는 시(예: 성남시 41130)는 빼고 구(41131·41133·41135)만 남긴다.
행정구역이 바뀌면(예: 화성시 구 신설) 이 스크립트를 다시 돌린다.
"""
import json
from pathlib import Path

import PublicDataReader as pdr

OUT = Path(__file__).resolve().parents[1] / "src" / "data" / "regions.json"

df = pdr.code_bdong()
live = df[df["말소일자"].isna() | (df["말소일자"] == "")]
sgg = live[live["시도코드"].isin(["11", "41"]) & (live["읍면동명"] == "") & (live["시군구명"] != "")]
sgg = sgg[["시군구코드", "시도코드", "시도명", "시군구명"]].drop_duplicates("시군구코드")

codes = set(sgg["시군구코드"])
rows = []
for r in sgg.itertuples():
    has_children = any(c != r.시군구코드 and c.startswith(r.시군구코드[:4]) and r.시군구코드.endswith("0") for c in codes)
    if has_children:
        continue
    name = r.시군구명
    city = name.split(" ")[0] if " " in name else name
    rows.append({"code": r.시군구코드, "sido": r.시도코드, "sidoName": r.시도명, "name": name, "city": city})

OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(rows)}개 시군구 → {OUT}")
