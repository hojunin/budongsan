"""DB에서 기사·리포트에 바로 쓸 수 있는 문장형 사실(인사이트)을 계산한다.

insights.json.py(홈 브리핑)와 scripts/new_report.py(내 리포트 초안)가 같이 쓴다.
각 항목은 데이터가 없으면 건너뛴다. 숫자는 모두 DB 원본에서 다시 계산한다.
"""
from __future__ import annotations

import re

import pandas as pd

from _db import query

SIDO = {"11": "서울", "41": "경기"}
KEYWORDS = ["재건축", "재개발", "전세", "월세", "청약", "분양", "대출", "금리", "DSR", "공급", "입주", "토지거래허가", "규제",
            "신고가", "갭투자", "미분양", "공시가", "보유세", "양도세", "임대차", "GTX", "신도시"]


def eok(manwon: float) -> str:
    return f"{manwon / 10000:.1f}억" if manwon >= 10000 else f"{manwon:,.0f}만"


def pct(x: float, digits: int = 1) -> str:
    return f"{'+' if x > 0 else ''}{x * 100:.{digits}f}%"


def ym_label(ym: str) -> str:
    return f"{ym[:4]}년 {int(ym[4:])}월"


def shift(ym: str, months: int) -> str:
    p = pd.Period(f"{ym[:4]}-{ym[4:]}", "M") + months
    return f"{p.year}{p.month:02d}"


def monthly() -> pd.DataFrame | None:
    """월 × (시도, 시군구) 거래량·㎡당 중위가. 해제 거래 제외."""
    return query("""
    WITH t AS (
      SELECT _ym AS ym, lpad(sggCd, 5, '0') AS sgg, left(lpad(sggCd, 5, '0'), 2) AS sido,
             TRY_CAST(replace(dealAmount, ',', '') AS DOUBLE) AS price, TRY_CAST(excluUseAr AS DOUBLE) AS area
      FROM molit_trade WHERE coalesce(trim(cdealType), '') <> 'O')
    SELECT ym, CASE WHEN GROUPING(sgg) = 0 THEN sgg ELSE sido END AS code, count(*) AS n,
           median(price / area) AS ppm2, median(price) FILTER (WHERE area >= 80 AND area < 90) AS p84
    FROM t WHERE price > 0 AND area > 0
    GROUP BY GROUPING SETS ((ym, sido, sgg), (ym, sido))""")


def item(id, group, title, value, sub="", tone="", as_of="", source="", detail=""):
    return {"id": id, "group": group, "title": title, "value": value, "sub": sub, "tone": tone,
            "as_of": as_of, "source": source, "detail": detail}


def trade_insights(names: dict[str, str]) -> list[dict]:
    m = monthly()
    if m is None or m.empty:
        return []
    out = []
    ref = shift(m["ym"].max(), -2)  # 신고 기한(30일)이 지난 최근 달
    get = lambda code, ym, col: m.loc[(m.code == code) & (m.ym == ym), col].squeeze() if ((m.code == code) & (m.ym == ym)).any() else None
    src = "국토교통부 실거래가"
    for code, name in SIDO.items():
        n, n_mom, n_yoy = get(code, ref, "n"), get(code, shift(ref, -1), "n"), get(code, shift(ref, -12), "n")
        if n:
            yoy = n / n_yoy - 1 if n_yoy else None
            mom = n / n_mom - 1 if n_mom else None
            out.append(item(f"volume-{code}", "거래", f"{name} 아파트 {ym_label(ref)} 매매 {n:,}건" + (f", 전년 동월 대비 {pct(yoy, 0)}" if yoy is not None else ""),
                            f"{n:,}건", f"전월 대비 {pct(mom, 0)}" if mom is not None else "", "up" if (yoy or 0) > 0 else "down", ym_label(ref), src))
        p, p_yoy, p_10 = get(code, ref, "ppm2"), get(code, shift(ref, -12), "ppm2"), get(code, shift(ref, -120), "ppm2")
        if p:
            yoy = p / p_yoy - 1 if p_yoy else None
            out.append(item(f"ppm2-{code}", "가격", f"{name} 아파트 ㎡당 중위 거래가 {p:,.0f}만 원" + (f", 1년 전보다 {pct(yoy)}" if yoy is not None else ""),
                            f"{p:,.0f}만/㎡", f"10년 전({ym_label(shift(ref, -120))})의 {p / p_10:.1f}배" if p_10 else "",
                            "up" if (yoy or 0) > 0 else "down", ym_label(ref), src,
                            "거래된 단지 구성에 따라 움직이므로 같은 집의 가격 변화(부동산원·KB 지수)와 다를 수 있습니다."))
        p84 = get(code, ref, "p84")
        if p84:
            out.append(item(f"p84-{code}", "가격", f"{name} 전용 84㎡ 중위 거래가 {eok(p84)} 원", eok(p84), "전용 80~89㎡ 정상 거래", "", ym_label(ref), src))
    # 1년 새 ㎡당 중위가가 많이 오른/내린 시군구 (양쪽 달 모두 30건 이상만)
    cur = m[(m.ym == ref) & (m.code.str.len() == 5) & (m.n >= 30)].set_index("code")
    old = m[(m.ym == shift(ref, -12)) & (m.code.str.len() == 5) & (m.n >= 30)].set_index("code")
    both = cur.join(old, rsuffix="_old", how="inner")
    if len(both) >= 6:
        both["chg"] = both.ppm2 / both.ppm2_old - 1
        top, bottom = both.nlargest(3, "chg"), both.nsmallest(3, "chg")
        fmt = lambda d: ", ".join(f"{names.get(c, c)} {pct(r.chg)}" for c, r in d.iterrows())
        out.append(item("sgg-top", "가격", f"1년 새 ㎡당 중위가가 가장 많이 오른 곳: {fmt(top)}", names.get(top.index[0], top.index[0]),
                        pct(top.chg.iloc[0]), "up", ym_label(ref), src, "직전 1년 같은 달 대비, 두 달 모두 30건 이상 거래된 시군구"))
        out.append(item("sgg-bottom", "가격", f"가장 약한 곳: {fmt(bottom)}", names.get(bottom.index[0], bottom.index[0]),
                        pct(bottom.chg.iloc[0]), "down", ym_label(ref), src, "직전 1년 같은 달 대비, 두 달 모두 30건 이상 거래된 시군구"))
    return out


def rone_series(metric: str, region: str, item_name: str | None = None) -> pd.DataFrame | None:
    df = query(f"""SELECT period, period_desc, value FROM rone WHERE metric = ? AND region_full = ?
                  {'AND item = ?' if item_name else ''} AND value IS NOT NULL ORDER BY period""",
               [metric, region] + ([item_name] if item_name else []))
    return None if df is None or df.empty else df


def rone_insights() -> list[dict]:
    out, src = [], "한국부동산원 R-ONE"
    for region in ("서울", "경기"):
        s = rone_series("wk_sale_index", region)
        if s is not None and len(s) > 2:
            chg = s.value.pct_change()
            sgn = lambda c: int(c > 0) - int(c < 0)
            streak, sign = 0, sgn(chg.iloc[-1])
            for c in reversed(chg.iloc[1:].tolist()):
                if sign and sgn(c) == sign:
                    streak += 1
                else:
                    break
            word = "상승" if sign > 0 else "하락" if sign < 0 else "보합"
            out.append(item(f"wk-sale-{region}", "가격", f"{region} 아파트값(부동산원 주간) {pct(chg.iloc[-1], 2)}" + (f", {streak}주 연속 {word}" if streak > 1 else ""),
                            pct(chg.iloc[-1], 2), f"{streak}주 연속 {word}" if streak > 1 else "전주 대비", "up" if sign > 0 else "down",
                            s.period_desc.iloc[-1], src))
        for metric, label in (("wk_sale_supply", "매매수급지수"), ("wk_jeonse_supply", "전세수급지수")):
            s = rone_series(metric, region)
            if s is not None:
                v = s.value.iloc[-1]
                out.append(item(f"{metric}-{region}", "수급", f"{region} {label} {v:.1f} ({'수요 우위' if v > 100 else '공급 우위'})",
                                f"{v:.1f}", "100 초과면 사려는(구하려는) 사람이 더 많음", "up" if v > 100 else "down", s.period_desc.iloc[-1], src))
        res = query("""SELECT period, period_desc, item, value FROM rone WHERE metric = 'mm_buyer_residence' AND region_full = ?""", [region])
        if res is not None and not res.empty:
            w = res.pivot_table(index=["period", "period_desc"], columns="item", values="value", aggfunc="sum").reset_index().sort_values("period")
            if {"합계", "관할시군구내", "관할시도내"} <= set(w.columns):
                w["out"] = 1 - (w["관할시군구내"] + w["관할시도내"]) / w["합계"]
                last = w.iloc[-1]
                prev = w[w.period == shift(last.period, -12)]
                yoy = f", 1년 전 {prev.out.iloc[0] * 100:.1f}%" if len(prev) else ""
                out.append(item(f"outsider-{region}", "매수자", f"{region} 아파트 매수자 중 다른 시도 거주자 {last.out * 100:.1f}%{yoy}",
                                f"{last.out * 100:.1f}%", "외지인 매수 비중", "", last.period_desc, src))
        age = query("""SELECT period, period_desc, item, value FROM rone WHERE metric = 'mm_buyer_age' AND region_full = ?""", [region])
        if age is not None and not age.empty:
            w = age.pivot_table(index=["period", "period_desc"], columns="item", values="value", aggfunc="sum").reset_index().sort_values("period")
            if {"합계", "20대이하", "30대"} <= set(w.columns):
                w["young"] = (w["20대이하"] + w["30대"]) / w["합계"]
                last = w.iloc[-1]
                out.append(item(f"young-{region}", "매수자", f"{region} 아파트 매수자 중 2030세대 {last.young * 100:.1f}%",
                                f"{last.young * 100:.1f}%", "20대 이하 + 30대", "", last.period_desc, src))
    conv = rone_series("mm_conversion", "서울")
    if conv is not None:
        out.append(item("conversion-서울", "수급", f"서울 아파트 전월세 전환율 {conv.value.iloc[-1]:.2f}%", f"{conv.value.iloc[-1]:.2f}%",
                        "전세를 월세로 바꿀 때 적용되는 연 이율", "", conv.period_desc.iloc[-1], src))
    return out


def kb_insights() -> list[dict]:
    df = query("SELECT * FROM kb_buyer_index")
    if df is None or df.empty or "매수우위지수" not in df:
        return []
    s = df[df["지역명"] == "서울"].sort_values("날짜")
    if s.empty:
        return []
    v = float(s["매수우위지수"].iloc[-1])
    return [item("kb-buyer-서울", "수급", f"KB 서울 매수우위지수 {v:.1f} ({'매수자 우위' if v > 100 else '매도자 우위'})", f"{v:.1f}",
                 "100 미만이면 매도하려는 사람이 더 많음", "up" if v > 100 else "down", str(s["날짜"].iloc[-1])[:10], "KB부동산")]


def news_insights() -> list[dict]:
    df = query("SELECT title, category FROM articles WHERE published >= now() - INTERVAL 7 DAY")
    if df is None or df.empty:
        return []
    counts = {k: int(df.title.str.contains(re.escape(k)).sum()) for k in KEYWORDS}
    top = sorted(((v, k) for k, v in counts.items() if v), reverse=True)[:5]
    out = [item("news-volume", "뉴스", f"최근 7일 부동산 기사·리포트 {len(df):,}건 수집 (리포트·동향 {int((df.category == 'report').sum()):,}건)",
                f"{len(df):,}건", "Google 뉴스·언론사 RSS", "", "최근 7일", "뉴스 수집")]
    if top:
        out.append(item("news-keywords", "뉴스", "이번 주 기사 키워드: " + ", ".join(f"{k}({v})" for v, k in top), top[0][1],
                        f"{top[0][0]}건", "", "최근 7일", "뉴스 수집", "제목에 등장한 횟수"))
    return out


def build(names: dict[str, str]) -> list[dict]:
    out = []
    for fn in (lambda: trade_insights(names), rone_insights, kb_insights, news_insights):
        try:
            out += fn()
        except Exception as e:  # 한 출처가 비거나 형식이 바뀌어도 나머지 인사이트는 낸다
            print(f"[insights] {getattr(fn, '__name__', 'trade')} 건너뜀: {e}", file=__import__("sys").stderr)
    return out
