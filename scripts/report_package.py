"""Create and verify a static local report package from reviewed aggregate evidence."""
from __future__ import annotations
import argparse
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import html
import json
import math
import re
import shutil
import textwrap
from pathlib import Path
from urllib.parse import urlparse

TEMPLATES = {'weekly': '주간 시장 브리핑', 'buyer': '매수 후보 비교', 'rent': '전세·월세 비교'}
BASE_ASSETS = {'report.json', 'chart.svg', 'index.html', 'summary.txt'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def format_value(value):
    with localcontext() as ctx:
        ctx.prec = 340
        result = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if result == 0: return '0'
    return f'{result:,.2f}'.rstrip('0').rstrip('.')


def validate_report(template, title, summary, evidence, scenario=None):
    if template not in TEMPLATES or not title.strip() or not summary.strip() or not evidence:
        raise ValueError('제목·요약·템플릿·근거가 필요합니다')
    releases, ids = {}, set()
    for e in evidence:
        for key in ('id', 'source_id', 'release_id', 'period', 'scope', 'unit', 'source_url'):
            if not isinstance(e.get(key), str) or not e[key].strip():
                raise ValueError(f'근거에 {key} 필요')
        if e['id'] in ids or (e['source_id'] in releases and releases[e['source_id']] != e['release_id']):
            raise ValueError('중복 근거 또는 동일 출처 릴리스 혼합')
        ids.add(e['id']); releases[e['source_id']] = e['release_id']
        if e.get('is_sample') is not False or e.get('rights') != 'allowed' or e.get('coverage_verified') is not True or e.get('identity_verified') is not True or not str(e.get('reviewed_by', '')).strip() or (e.get('sample_n') is None and e.get('kind') not in ('price_index','sentiment_index')) or (e.get('sample_n') is not None and (type(e['sample_n']) is not int or e['sample_n'] < 1)):
            raise ValueError('샘플·이용권·표본 검증 필요')
        u = urlparse(e['source_url'])
        if u.scheme != 'https' or not u.netloc:
            raise ValueError('HTTPS 출처 필요')
        if not e.get('facts') or any(not isinstance(f.get('label'), str) or not f['label'].strip() or type(f.get('value')) not in (int, float) or not math.isfinite(f['value']) for f in e['facts']):
            raise ValueError('유한한 숫자 근거 필요')
        if len({f['label'] for f in e['facts']}) != len(e['facts']):
            raise ValueError('중복 지표 이름')
    if template == 'weekly':
        periods = [e for e in evidence if e.get('kind') == 'trade_distribution']
        if not periods and len(evidence) == 2 and all('kind' not in e for e in evidence): periods = evidence
        if len(periods) != 2 or any(e['sample_n'] is None or e['sample_n'] < 30 or not {'Q25','중간값','Q75'} <= {f['label'] for f in e['facts']} for e in periods):
            raise ValueError('기간별 30건 이상의 가격 분포 두 개가 필요합니다')
        a, b = periods
        keys = ('region', 'band', 'canceled_excluded')
        qa, qb = a.get('query_spec', {}), b.get('query_spec', {})
        if not qa.get('region') or not qa.get('band') or qa.get('canceled_excluded') is not True or any(qa.get(k) != qb.get(k) for k in keys) or a['source_id'] != b['source_id'] or a['unit'] != b['unit'] or a['period'] == b['period']:
            raise ValueError('기간 비교의 지역·면적·출처·단위 불일치')
    if template == 'rent':
        for e in evidence:
            if e.get('kind') == 'jeonse_distribution': continue
            q = e.get('query_spec', {})
            vals = [q.get(k) for k in ('deposit','monthly','annual_rate')]
            facts = {f['label']: f['value'] for f in e['facts']}
            if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in vals) or not {'실제 월세','가정 환산 월비용'} <= facts.keys():
                raise ValueError('임대 원값과 환산 가정 필요')
            if not math.isclose(facts['실제 월세'], vals[1]) or not math.isclose(facts['가정 환산 월비용'], vals[1] + vals[0]*vals[2]/1200):
                raise ValueError('임대 환산값 불일치')
    if template in ('buyer', 'weekly', 'rent'):
        for e in evidence:
            if template == 'weekly' and e not in periods and e.get('kind') != 'jeonse_distribution': continue
            if template == 'rent' and e.get('kind') != 'jeonse_distribution': continue
            facts = {f['label']: f['value'] for f in e['facts']}
            if not {'Q25', '중간값', 'Q75'} <= facts.keys():
                raise ValueError('매수 분포 분위수 필요')
            if {'Q25', '중간값', 'Q75'} <= facts.keys():
                if e['sample_n'] is None or e['sample_n'] < (30 if template == 'weekly' and e in periods else 5) or not 0 < facts['Q25'] <= facts['중간값'] <= facts['Q75']:
                    raise ValueError('분포 표본 또는 분위수 오류')
                budget = e.get('query_spec', {}).get('budget')
                if budget is not None and (type(budget) not in (int,float) or not math.isfinite(budget) or budget < 0):
                    raise ValueError('집값 상한 오류')
    if scenario is not None:
        if template != 'buyer' or not isinstance(scenario, dict) or scenario.get('include') is not True or not scenario.get('fields') or len(scenario['fields']) > 3:
            raise ValueError('개인 시나리오의 명시적 포함 선택 필요')
        if any(not isinstance(f.get('label'), str) or not f['label'].strip() or not isinstance(f.get('unit'), str) or not f['unit'].strip() or type(f.get('value')) not in (int,float) or not math.isfinite(f['value']) for f in scenario['fields']):
            raise ValueError('개인 시나리오 값 오류')
    return releases


def content_blocks(template, evidence, scenario=None):
    kinds = {'weekly': [('공식 가격 지표','price_index'), ('시장 심리','sentiment_index'), ('최근 완결월 거래','trade_volume'), ('전월세 관측','jeonse_distribution'), ('거래가격 분포','trade_distribution')],
             'buyer': [('매수 거래 분포','trade_distribution'), ('전세 거래집단','jeonse_distribution')],
             'rent': [('전세 보증금 분포','jeonse_distribution'), ('실제 계약과 가정 월비용','rent_contract')]}
    blocks = []
    for title, kind in kinds[template]:
        selected = [e['id'] for e in evidence if e.get('kind', {'buyer':'trade_distribution','rent':'rent_contract'}.get(template,'')) == kind]
        blocks.append({'title':title, 'evidence_ids':selected, 'status':'available' if selected else 'missing'})
    if template == 'buyer':
        blocks.append({'title':'개인 시나리오', 'evidence_ids':[], 'status':'available' if scenario else 'missing'})
    if template == 'rent':
        blocks.append({'title':'계약 확인사항', 'evidence_ids':[], 'status':'available', 'text':'등기·권리관계, 보증금 반환 조건과 보증 가입 가능 여부를 공식 자료와 전문가에게 확인하세요.'})
    return blocks


def export_cards(evidence, scenario):
    cards = list(evidence)
    if scenario:
        cards.extend({'scope':'개인 가정 · 명시적 포함', 'unit':'', 'period':'사용자 시나리오', 'source_id':'개인 가정', 'source_url':'', 'sample_n':None, 'facts':[field]} for field in scenario['fields'])
    return cards


def export_names(evidence, scenario):
    count = len(export_cards(evidence, scenario))
    def name(base, index): return base + (f'-{index+1}' if index else '') + '.svg'
    return [name('card-1080x1350', i) for i in range(count)] + [name('chart-1600x900', i) for i in range(count)]


def render_export_svg(title, cards, all_cards, width, height):
    esc = lambda value: html.escape(str(value), quote=True)
    columns = 1
    margin, gap = 48, 24
    font_size = 36 if width < height else 50
    line_step = 40 if width < height else 54
    card_width = (width - margin * 2 - gap * (columns - 1)) / columns
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui, Apple SD Gothic Neo, Noto Sans KR, sans-serif" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#f4f7f8"/>']
    title_lines = textwrap.wrap(title, width=26 if width < height else 27) or ['리포트']
    if len(title_lines) > 2: raise ValueError('이미지 제목이 너무 깁니다')
    for i, line in enumerate(title_lines): out.append(f'<text x="{margin}" y="{55 + i*48}" font-size="{font_size}" fill="#1e293b">{esc(line)}</text>')
    top = 120
    for i, e in enumerate(cards):
        x = margin + i * (card_width + gap); y = top
        out.append(f'<rect x="{x}" y="{y}" width="{card_width}" height="{height-top-margin}" rx="14" fill="white" stroke="#cbd5d7"/>')
        sample = e.get('sample_n'); sample_text = str(sample) if sample is not None else '미공표'
        q = e.get('query_spec', {})
        conditions = []
        for key, label, unit in [('budget','집값 상한','만원'),('deposit','보증금','만원'),('monthly','실제 월세','만원'),('annual_rate','가정 연 금리','%')]:
            if q.get(key) is not None: conditions.append(f"{label} {format_value(q[key])}{unit}")
        if q.get('canceled_excluded') is True: conditions.append('취소 제외')
        sample_line = '확률 없는 사용자 가정' if e['source_id'] == '개인 가정' else f"표본 {sample_text} · {e['unit']} · 출처 {e['source_id']}"
        metadata = [e['scope'], e['period'], sample_line, e['source_url'], " · ".join(conditions)]
        lines = []
        for part in metadata:
            if part: lines.extend(textwrap.wrap(str(part), width=26 if width < height else 27, break_long_words=True, break_on_hyphens=False))
        facts = [f"{f['label']} {format_value(f['value'])} {f.get('unit', e['unit'])}" for f in e['facts']]
        if len(facts) > 3: raise ValueError('이미지에는 근거당 숫자 3개까지 허용합니다')
        fact_lines = [line for fact in facts for line in textwrap.wrap(fact, width=26 if width < height else 27)]
        line_count = len(lines) + len(fact_lines)
        if y + font_size + line_count * line_step > height - margin - 95: raise ValueError('출처·조건이 이미지에 들어가지 않습니다')
        yy = y + font_size
        for line in fact_lines:
            out.append(f'<text x="{x+20}" y="{yy}" font-size="{font_size}" fill="#087f80">{esc(line)}</text>'); yy += line_step
        for line in lines:
            out.append(f'<text x="{x+20}" y="{yy}" font-size="{font_size}" fill="#1e293b">{esc(line)}</text>'); yy += line_step
        if e['source_id'] != '개인 가정':
            budgets = [other.get('query_spec', {}).get('budget') or 0 for other in all_cards if other['unit'] == e['unit']]
            scale = max([abs(f['value']) for other in all_cards if other['unit'] == e['unit'] for f in other['facts']] + budgets + [1])
            span = max(0, card_width - 40)
            factmap = {f['label']: f['value'] for f in e['facts']}
            if {'Q25','중간값','Q75'} <= factmap.keys():
                position = lambda value: x + 20 + span * value / scale
                out.append(f'<line data-range="true" x1="{position(factmap["Q25"])}" x2="{position(factmap["Q75"])}" y1="{yy+12}" y2="{yy+12}" stroke="#087f80" stroke-width="10"/>')
                out.append(f'<circle cx="{position(factmap["중간값"])}" cy="{yy+12}" r="9" fill="#1e293b"/>')
                if q.get('budget') is not None:
                    out.append(f'<line x1="{position(q["budget"])}" x2="{position(q["budget"])}" y1="{yy-4}" y2="{yy+28}" stroke="#c23531" stroke-width="4"/>')
            else:
                for j, fact in enumerate(e['facts']):
                    bar_width = span * abs(fact['value']) / scale
                    out.append(f'<rect data-fact-bar="true" x="{x+20}" y="{yy+6+j*28}" width="{bar_width}" height="12" fill="{["#087f80", "#8b5ba7", "#a46b1c"][j]}"/>')
    out.append('</svg>')
    return '\n'.join(out).encode()


def create_package(path, template, title, summary, evidence, scenario=None):
    path = Path(path)
    if path.exists():
        raise ValueError('패키지 경로가 이미 있습니다')
    releases = validate_report(template, title, summary, evidence, scenario)
    esc = lambda x: html.escape(str(x), quote=True)
    fmt = format_value
    rows = [(e, f) for e in evidence for f in e['facts']]
    ranges = template in ('buyer', 'weekly') and len({e['unit'] for e in evidence}) == 1 and all({'Q25','중간값','Q75'} <= {f['label'] for f in e['facts']} for e in evidence)
    def condition(e):
        q = e.get('query_spec', {})
        if template == 'rent' and e.get('kind') != 'jeonse_distribution':
            return f"보증금 {fmt(q['deposit'])}만원 · 실제 월세 {fmt(q['monthly'])}만원 · 가정 연 {fmt(q['annual_rate'])}%"
        if template == 'buyer' and q.get('budget') is not None:
            return f"집값 상한 {fmt(q['budget'])}만원 · 세로선"
        return '' 
    details = [line for e in evidence for line in textwrap.wrap(f'{e["scope"]} · {e["period"]} · n={e["sample_n"] if e["sample_n"] is not None else '미공표'} · {e["unit"]} · {e["source_id"]} · {e["source_url"]} · {condition(e)}', width=23)]
    plot_height = 65 + (len(evidence) * 105 if ranges else len(rows) * 86)
    height = plot_height + 20 * len(details) + 10
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui, Apple SD Gothic Neo, Noto Sans KR, sans-serif" width="320" height="{height}" viewBox="0 0 320 {height}">', '<rect width="100%" height="100%" fill="white"/>', '<text x="12" y="24" font-size="14" fill="#172e35">고정 근거 · 단위와 범위를 확인하세요</text>']
    if ranges:
        factmap = lambda e: {f['label']: f['value'] for f in e['facts']}
        bound = max([factmap(e)['Q75'] for e in evidence] + [e.get('query_spec', {}).get('budget') or 0 for e in evidence] + [1])
        for i, e in enumerate(evidence):
            facts = factmap(e); y = 55 + i * 105
            pos = lambda value: 20 + max(0, min(1, value / bound)) * 275
            lines.append(f'<text x="12" y="{y}" font-size="13">{esc(e["scope"][:28])} · n={e["sample_n"] if e["sample_n"] is not None else '미공표'}</text>')
            lines.append(f'<line data-range="true" x1="{pos(facts["Q25"])}" x2="{pos(facts["Q75"])}" y1="{y+22}" y2="{y+22}" stroke="#087f80" stroke-width="7"/>')
            lines.append(f'<circle cx="{pos(facts["중간값"])}" cy="{y+22}" r="5" fill="#173c46"/>')
            budget = e.get('query_spec', {}).get('budget')
            if isinstance(budget, (int,float)) and math.isfinite(budget) and budget >= 0:
                lines.append(f'<line x1="{pos(budget)}" x2="{pos(budget)}" y1="{y+10}" y2="{y+34}" stroke="#ad3d32" stroke-width="2"/>')
            lines.append(f'<text x="12" y="{y+48}" font-size="12">{esc(fmt(facts["Q25"]))} / {esc(fmt(facts["중간값"]))} / {esc(fmt(facts["Q75"]))} {esc(e["unit"])}</text>')
            lines.append(f'<text x="12" y="{y+68}" font-size="11">{esc(e["period"][:38])} · {esc(e["source_id"])}</text>')
    else:
        for i, (e, f) in enumerate(rows):
            scale = max(abs(float(fact['value'])) for other in evidence if other['unit'] == e['unit'] for fact in other['facts']) or 1
            width = 130 * abs(float(f['value'])) / scale
            x = 160 if f['value'] >= 0 else 160 - width
            y = 54 + 86*i
            lines.append(f'<text x="12" y="{y}" font-size="13">{esc(f["label"][:20])}: {esc(fmt(f["value"]))} {esc(e["unit"])}</text>')
            lines.append(f'<rect data-fact-bar="true" x="{x}" y="{y+8}" width="{width}" height="13" fill="#087f80"/>')
            lines.append(f'<text x="12" y="{y+43}" font-size="11">n={e["sample_n"] if e["sample_n"] is not None else '미공표'} · {esc(e["period"][:30])} · {esc(e["source_id"])}</text>')
    for i, line in enumerate(details):
        lines.append(f'<text x="12" y="{plot_height + 18*i}" font-size="12">{esc(line)}</text>')
    lines.append('</svg>')
    svg = '\n'.join(lines).encode()
    sections = ''.join(f'<li>{esc(e["scope"])} · {esc(e["period"])} · n={e["sample_n"] if e["sample_n"] is not None else '미공표'} · <a href="{esc(e["source_url"])}">{esc(e["source_id"])}</a> · {esc(condition(e))}</li>' for e in evidence)
    table = ''.join(f'<tr><th scope="row">{esc(e["scope"])} · {esc(f["label"])}</th><td>{esc(fmt(f["value"]))} {esc(e["unit"])}</td><td>{e["sample_n"] if e["sample_n"] is not None else '미공표'}</td></tr>' for e, f in rows)
    notes = {'weekly': '관측 기간이 서로 다를 수 있습니다. 각 출처의 기준일을 확인하세요.', 'buyer': '과거 거래는 현재 매물이나 대출 승인 가능성을 뜻하지 않습니다.', 'rent': '서로 다른 계약의 비교이며 보증금 반환 안전성을 뜻하지 않습니다.'}
    page = f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{esc(title)}</title><style>body{{font:16px/1.6 system-ui;margin:0 auto;padding:16px;max-width:760px;color:#243e46}}img{{max-width:100%;height:auto}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #cbd5d7}}@media(max-width:420px){{table,tbody,tr,th,td{{display:block}}thead{{display:none}}}}</style><main><p>{esc(TEMPLATES[template])}</p><h1>{esc(title)}</h1><p>{esc(summary)}</p><img src="chart.svg" alt="고정된 근거 그래픽. 상세 숫자는 아래 표에 있습니다."><h2>근거 숫자</h2><table><thead><tr><th>항목</th><th>값</th><th>표본</th></tr></thead><tbody>{table}</tbody></table><h2>확인할 점</h2><p>{esc(notes[template])}</p><h2>조건과 출처</h2><ul>{sections}</ul></main></html>'.encode()
    blocks = content_blocks(template, evidence, scenario)
    report = json.dumps({'template':template, 'title':title, 'summary':summary, 'evidence':evidence, 'blocks':blocks, 'scenario':scenario}, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode()
    block_text = ''.join(f'<li>{esc(b["title"])}: {esc(b.get('text') or ('자료 있음' if b['status'] == 'available' else '자료 없음'))}</li>' for b in blocks)
    page = page.replace('<h2>조건과 출처</h2>'.encode(), f'<h2>템플릿 근거</h2><ul>{block_text}</ul><h2>조건과 출처</h2>'.encode())
    scenario_text = ' · '.join(f"{f['label']} {fmt(f['value'])}{f['unit']}" for f in scenario['fields']) if scenario else ''
    if scenario:
        page = page.replace('<h2>조건과 출처</h2>'.encode(), f'<h2>개인 가정 · 명시적 포함</h2><p>{esc(scenario_text)}</p><h2>조건과 출처</h2>'.encode())
    summary_text = ('\n'.join([title, summary, scenario_text, *[f"{b['title']}: {b.get('text') or ('자료 있음' if b['status'] == 'available' else '자료 없음')}" for b in blocks], *[f"{e['scope']} · {e['period']} · n={e['sample_n'] if e['sample_n'] is not None else '미공표'} · {e['source_id']} · {e['source_url']} · {condition(e)}: " + ', '.join(f"{f['label']} {fmt(f['value'])} {e['unit']}" for f in e['facts']) for e in evidence]]) + '\n').encode()

    files = {'report.json':report, 'chart.svg':svg, 'index.html':page, 'summary.txt':summary_text}
    cards = export_cards(evidence, scenario)
    names = export_names(evidence, scenario)
    for i, card in enumerate(cards):
        files[names[i]] = render_export_svg(title, [card], cards, 1080, 1350)
    for i, card in enumerate(cards):
        files[names[len(cards) + i]] = render_export_svg(title, [card], cards, 1600, 900)
    path.mkdir(parents=True)
    for name, data in files.items(): (path/name).write_bytes(data)
    manifest = {'capture_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'dataset_releases':releases, 'assets':{k:digest(v) for k,v in files.items()}}
    (path/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding='utf-8')


def verify_package(path):
    try:
        path = Path(path)
        m = json.loads((path/'manifest.json').read_text(encoding='utf-8'))
        report = json.loads((path/'report.json').read_text(encoding='utf-8'))
        expected = BASE_ASSETS | set(export_names(report['evidence'], report.get('scenario')))
        if set(m['assets']) != expected: return False
        if {p.name for p in path.iterdir()} != set(m['assets']) | {'manifest.json'}: return False
        if any(p.is_symlink() or not p.is_file() for p in path.iterdir()): return False
        if not all(digest((path/name).read_bytes()) == value for name, value in m['assets'].items()): return False
        releases = validate_report(report['template'], report['title'], report['summary'], report['evidence'], report.get('scenario'))
        if report.get('blocks') != content_blocks(report['template'], report['evidence'], report.get('scenario')): return False
        return releases == m['dataset_releases']
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def report_page(slug, report):
    # 사용자 글은 JSON 데이터로만 불러와 Observable 코드에 삽입하지 않는다.
    return """---
title: 고정 리포트
---

```js
import {num} from "../components/format.js";
const report = await FileAttachment("./__SLUG__/report.json").json();
const picture = await FileAttachment("./__SLUG__/chart.svg").url();
__EXPORT_DECLARATIONS__
const summaryExport = await FileAttachment("./__SLUG__/summary.txt").url();
```

${html`<h1>${report.title}</h1><p class="lead">${report.summary}</p><img src=${picture} alt="발행 시점에 고정한 근거 그래픽"><h2>템플릿 근거</h2><ul>${report.blocks.map((b) => html`<li>${b.title}: ${b.text ?? (b.status === "available" ? "자료 있음" : "자료 없음")}</li>`)}</ul><p>${exportLinks.map((e) => html`<a href=${e.url} download>${e.label}</a> `)} · <a href=${summaryExport} download>문장 텍스트</a></p><h2>근거 숫자</h2><table class="compare-table" tabindex="0"><thead><tr><th>범위와 항목</th><th>값</th><th>표본</th></tr></thead><tbody>${report.evidence.flatMap((e) => e.facts.map((f) => html`<tr><th>${e.scope} · ${f.label}</th><td data-label="값">${num(f.value)} ${e.unit}</td><td data-label="표본">${e.sample_n ?? "미공표"}</td></tr>`))}</tbody></table>${report.scenario ? html`<h2>개인 가정 · 명시적 포함</h2><p>${report.scenario.fields.map((f) => `${f.label} ${num(f.value)}${f.unit}`).join(" · ")}</p>` : ""}<h2>조건과 출처</h2><ul>${report.evidence.map((e) => html`<li>${e.scope} · ${e.period} · n=${e.sample_n ?? "미공표"} · <a href=${e.source_url}>${e.source_id}</a>${report.template === "rent" && e.kind !== "jeonse_distribution" ? ` · 보증금 ${num(e.query_spec.deposit)}만원 · 실제 월세 ${num(e.query_spec.monthly)}만원 · 가정 연 ${num(e.query_spec.annual_rate)}%` : report.template === "buyer" && e.query_spec?.budget != null ? ` · 집값 상한 ${num(e.query_spec.budget)}만원 · 세로선` : ""}</li>`)}</ul>`}

<p>관측값은 현재 매물, 대출 승인 또는 보증금 안전성을 뜻하지 않습니다.</p>
""".replace('__SLUG__', slug).replace('__EXPORT_DECLARATIONS__', 'const exportLinks = [' + ','.join('{label:' + json.dumps(name, ensure_ascii=False) + ',url:await FileAttachment(' + json.dumps('./' + slug + '/' + name) + ').url()}' for name in export_names(report['evidence'], report.get('scenario'))) + '];')


def prepare_package(package, site, slug):
    """검증된 패키지와 데이터 전용 읽기 페이지를 로컬 사이트에 추가한다."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', slug):
        raise ValueError('슬러그는 영문 소문자·숫자·하이픈만 허용합니다')
    if not verify_package(package):
        raise ValueError('패키지 검증 실패')
    site = Path(site)
    target, page = site / slug, site / f'{slug}.md'
    if target.exists() or page.exists():
        raise FileExistsError('이미 존재하는 리포트입니다')
    doc = json.loads((Path(package)/'report.json').read_text(encoding='utf-8'))
    template = report_page(slug, doc)
    created = False
    try:
        target.mkdir()
        created = True
        for name in sorted(BASE_ASSETS | set(export_names(doc['evidence'], doc.get('scenario'))) | {'manifest.json'}):
            shutil.copyfile(Path(package)/name, target/name)
        with page.open('x', encoding='utf-8') as f:
            f.write(template)
    except Exception:
        if created: shutil.rmtree(target)
        raise
    return page


def main():
    parser = argparse.ArgumentParser(description='로컬 고정 리포트 패키지 생성·검증·발행 준비 (배포 없음)')
    sub = parser.add_subparsers(dest='action', required=True)
    create = sub.add_parser('create'); create.add_argument('input'); create.add_argument('output'); create.add_argument('--include-scenario', action='store_true'); create.add_argument('--scenario-file')
    preview = sub.add_parser('preview'); preview.add_argument('input')
    verify = sub.add_parser('verify'); verify.add_argument('package')
    prepare = sub.add_parser('prepare'); prepare.add_argument('package'); prepare.add_argument('slug')
    args = parser.parse_args()
    if args.action in ('create', 'preview'):
        doc = json.loads(Path(args.input).read_text(encoding='utf-8'))
        if args.action == 'preview':
            print(json.dumps(doc if doc.get('include') is True else doc.get('scenario'), ensure_ascii=False, indent=2))
            return
        if args.scenario_file and not args.include_scenario:
            raise ValueError('시나리오 파일은 --include-scenario 선택이 필요합니다')
        scenario = (json.loads(Path(args.scenario_file).read_text(encoding='utf-8')) if args.scenario_file else doc.get('scenario')) if args.include_scenario else None
        if args.include_scenario and scenario is None:
            raise ValueError('포함할 개인 시나리오 없음')
        create_package(args.output, doc['template'], doc['title'], doc['summary'], doc['evidence'], scenario=scenario)
    elif not verify_package(args.package):
        raise SystemExit('패키지 검증 실패')
    elif args.action == 'prepare':
        prepare_package(args.package, Path(__file__).resolve().parents[1] / 'src' / 'reports', args.slug)
    print('완료: 로컬 파일만 생성/검증했습니다. 공개 또는 배포된 상태가 아닙니다.')


if __name__ == '__main__': main()
