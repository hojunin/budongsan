import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_package import create_package, verify_package

def evidence():
    return {'id':'e1','source_id':'molit','release_id':'sha256:test','is_sample':False,'rights':'allowed','coverage_verified':True,'identity_verified':True,'reviewed_by':'tester','period':'2026-01–2026-06','scope':'서울 84㎡','unit':'만원','sample_n':5,'source_url':'https://rt.molit.go.kr/','facts':[{'label':'Q25','value':9000},{'label':'중간값','value':10000},{'label':'Q75','value':11000}]}
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / 'package'
    create_package(p, 'buyer', '<script>alert(1)</script> ${1+1}', '설명', [evidence()])
    assert verify_package(p)
    (p/'private.txt').write_text('secret')
    assert not verify_package(p)
    (p/'private.txt').unlink()
    html = (p/'index.html').read_text()
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert (p/'chart.svg').exists()
    assert 'data-range' in (p/'chart.svg').read_text()
    assert 'width="320"' in (p/'chart.svg').read_text()
    assert '<table' in html
    before = (p/'manifest.json').read_bytes()
    assert verify_package(p) and (p/'manifest.json').read_bytes() == before
    (p/'chart.svg').write_text('altered')
    assert not verify_package(p)
    for variant in ({'is_sample':True}, {'rights':'unknown'}, {'sample_n':0}, {'coverage_verified':False}, {'identity_verified':False}):
        e = evidence() | variant
        try: create_package(Path(d)/('bad'+str(len(list(Path(d).iterdir())))), 'buyer', 't', 's', [e])
        except ValueError: pass
        else: raise AssertionError(variant)
    try: create_package(Path(d)/'mixed', 'weekly', 't', 's', [evidence(), evidence() | {'id':'e2','release_id':'another'}])
    except ValueError: pass
    else: raise AssertionError('mixed source releases')
print('ok')
with tempfile.TemporaryDirectory() as d:
    e = evidence() | {'facts':[{'label':'Q25','value':100.12345},{'label':'중간값','value':200.23456},{'label':'Q75','value':300.34567}], 'query_spec':{'budget':150}}
    p = Path(d)/'range'
    create_package(p,'buyer','분포','검토된 요약',[e])
    svg = (p/'chart.svg').read_text()
    assert 'data-range="true"' in svg and '100.12' in svg and '100.12345' not in svg
    assert e['source_url'] in svg
    assert '집값 상한 150만원' in (p/'index.html').read_text()
    original = (p/'manifest.json').read_bytes()
    external_source = Path(d)/'new-source.json'
    external_source.write_text('new batch')
    assert verify_package(p) and (p/'manifest.json').read_bytes() == original
with tempfile.TemporaryDirectory() as d:
    for template, e in [('weekly', evidence()), ('rent', evidence())]:
        try: create_package(Path(d)/template, template, 't', 's', [e])
        except ValueError: pass
        else: raise AssertionError('incomplete template accepted: '+template)
with tempfile.TemporaryDirectory() as d:
    q = {'deposit':12000, 'monthly':50, 'annual_rate':4}
    e = evidence() | {'unit':'만원/월', 'sample_n':1, 'query_spec':q, 'facts':[{'label':'실제 월세','value':50},{'label':'가정 환산 월비용','value':90}]}
    p=Path(d)/'rent'
    create_package(p,'rent','임대','요약',[e])
    assert '12,000' in (p/'index.html').read_text() and '4%' in (p/'index.html').read_text()
    assert '12,000' in (p/'summary.txt').read_text() and '4%' in (p/'summary.txt').read_text()
    a = evidence() | {'id':'a','sample_n':30,'unit':'만원/㎡','period':'2025-01–2025-03','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}
    b = a | {'id':'b','period':'2026-01–2026-03'}
    create_package(Path(d)/'weekly','weekly','시장','요약',[a,b])
    assert 'data-range' in (Path(d)/'weekly'/'chart.svg').read_text()
with tempfile.TemporaryDirectory() as d:
    import xml.etree.ElementTree as ET
    def rent_record(i, deposit, monthly):
        cost=monthly+deposit*4/1200
        return evidence() | {'id':i,'unit':'만원/월','sample_n':1,'query_spec':{'deposit':deposit,'monthly':monthly,'annual_rate':4},'facts':[{'label':'실제 월세','value':monthly},{'label':'가정 환산 월비용','value':cost}]}
    p=Path(d)/'rentcompare'
    create_package(p,'rent','임대','요약',[rent_record('a',10000,50),rent_record('b',20000,20)])
    root=ET.parse(p/'chart.svg').getroot()
    bars=[float(x.attrib['width']) for x in root if x.attrib.get('data-fact-bar')]
    assert abs(bars[1]/bars[3] - (50+10000*4/1200)/(20+20000*4/1200)) < 1e-9
with tempfile.TemporaryDirectory() as d:
    from report_package import prepare_package
    base=Path(d); p=base/'package'; site=base/'site'; site.mkdir()
    create_package(p, 'buyer', '${globalThis.pwned=true}', '<b>문장</b>', [evidence()])
    prepare_package(p, site, 'reviewed-report')
    page=(site/'reviewed-report.md').read_text()
    assert '${globalThis.pwned=true}' not in page and 'FileAttachment("./reviewed-report/report.json")' in page
    assert verify_package(site/'reviewed-report')
    try: prepare_package(p,site,'reviewed-report')
    except FileExistsError: pass
    else: raise AssertionError('overwrote report')
with tempfile.TemporaryDirectory() as d:
    import importlib.util
    spec=importlib.util.spec_from_file_location('reports_loader', Path(__file__).resolve().parents[1]/'src/data/reports.json.py')
    loader=importlib.util.module_from_spec(spec); spec.loader.exec_module(loader)
    site=Path(d)/'site'; site.mkdir(); p=Path(d)/'package'
    create_package(p,'buyer','검토한 제목','요약',[evidence()])
    prepare_package(p,site,'report-a')
    posts=loader.list_reports(site)
    assert posts[0]['slug']=='report-a' and posts[0]['title']=='검토한 제목'
    (site/'report-a'/'chart.svg').write_text('tampered')
    try: loader.list_reports(site)
    except ValueError: pass
    else: raise AssertionError('tampered public package accepted')
with tempfile.TemporaryDirectory() as d:
    from verify_reports import verify_prepared
    root=Path(d); site=root/'reports'; site.mkdir(); p=root/'package'
    create_package(p,'buyer','t','s',[evidence()]); prepare_package(p,site,'verified')
    verify_prepared(site)
    (site/'verified'/'report.json').write_text('{}')
    try: verify_prepared(site)
    except ValueError: pass
    else: raise AssertionError('build accepted changed package')
with tempfile.TemporaryDirectory() as d:
    from verify_reports import verify_prepared
    root=Path(d); site=root/'reports'; site.mkdir(); p=root/'package'
    create_package(p,'buyer','t','s',[evidence()]); prepare_package(p,site,'verified')
    (site/'verified.md').write_text('```js\nalert(1)\n```')
    try: verify_prepared(site)
    except ValueError: pass
    else: raise AssertionError('changed report page accepted')
with tempfile.TemporaryDirectory() as d:
    a=evidence() | {'id':'a','sample_n':30,'period':'2025-01–2025-03','query_spec':{'region':'서울','band':'84','canceled_excluded':True},'facts':[{'label':'Q25','value':300},{'label':'중간값','value':200},{'label':'Q75','value':100}]}
    b=a | {'id':'b','period':'2026-01–2026-03'}
    try: create_package(Path(d)/'bad-weekly','weekly','t','s',[a,b])
    except ValueError: pass
    else: raise AssertionError('inverted weekly distribution accepted')
    dup=evidence() | {'facts':evidence()['facts']+[{'label':'Q25','value':1}]}
    try: create_package(Path(d)/'duplicate','buyer','t','s',[dup])
    except ValueError: pass
    else: raise AssertionError('duplicate fact label accepted')
with tempfile.TemporaryDirectory() as d:
    a=evidence() | {'id':'a', 'sample_n':30, 'period':'2025-01–2025-03', 'query_spec':{'region':'서울','band':'84','canceled_excluded':True}}
    b=a | {'id':'b','period':'2026-01–2026-03','query_spec':{'region':'경기','band':'84','canceled_excluded':True}}
    try: create_package(Path(d)/'mismatch','weekly','t','s',[a,b])
    except ValueError: pass
    else: raise AssertionError('mismatched period comparison accepted')
with tempfile.TemporaryDirectory() as d:
    import hashlib
    p=Path(d)/'p'; create_package(p,'buyer','t','s',[evidence()])
    doc=json.loads((p/'report.json').read_text()); doc['evidence'][0]['source_url']='javascript:alert(1)'
    data=json.dumps(doc).encode(); (p/'report.json').write_bytes(data)
    manifest=json.loads((p/'manifest.json').read_text()); manifest['assets']['report.json']=hashlib.sha256(data).hexdigest()
    (p/'manifest.json').write_text(json.dumps(manifest))
    assert not verify_package(p)
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'exports'
    create_package(p,'buyer','비교','요약',[evidence()])
    manifest=json.loads((p/'manifest.json').read_text())
    for name in ('summary.txt','card-1080x1350.svg','chart-1600x900.svg'):
        assert (p/name).exists() and name in manifest['assets']
    assert '요약' in (p/'summary.txt').read_text()
    assert 'width="1080" height="1350"' in (p/'card-1080x1350.svg').read_text()
    assert 'width="1600" height="900"' in (p/'chart-1600x900.svg').read_text()
    assert '자료 없음' in (p/'index.html').read_text()
with tempfile.TemporaryDirectory() as d:
    scenario={'include':True,'fields':[{'label':'월 잔여','value':170,'unit':'만원'}]}
    p=Path(d)/'scenario'
    create_package(p,'buyer','t','s',[evidence()], scenario=scenario)
    assert '월 잔여' in (p/'index.html').read_text() and '월 잔여' in (p/'summary.txt').read_text()
    assert '월 잔여' in (p/'card-1080x1350-2.svg').read_text()
    try: create_package(Path(d)/'no-opt-in','buyer','t','s',[evidence()], scenario=scenario | {'include':False})
    except ValueError: pass
    else: raise AssertionError('unapproved scenario included')
with tempfile.TemporaryDirectory() as d:
    a=evidence() | {'id':'a','kind':'trade_distribution','sample_n':30,'unit':'만원/㎡','period':'2025-01–2025-03','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}
    b=a | {'id':'b','period':'2026-01–2026-03'}
    official=evidence() | {'id':'index','kind':'price_index','source_id':'rone','release_id':'rone1','period':'2026-10-01','sample_n':None,'unit':'지수','facts':[{'label':'가격지수','value':101.2}]}
    p=Path(d)/'weekly-extra'; create_package(p,'weekly','주간','요약',[a,b,official])
    doc=json.loads((p/'report.json').read_text())
    assert next(x for x in doc['blocks'] if x['title']=='공식 가격 지표')['status']=='available'
    assert next(x for x in doc['blocks'] if x['title']=='시장 심리')['status']=='missing'
    assert '101.2' in (p/'summary.txt').read_text() and verify_package(p)
    for name in ('index.html','summary.txt','chart.svg','card-1080x1350-3.svg','chart-1600x900-3.svg'):
        text=(p/name).read_text(); assert '미공표' in text and 'n=None' not in text
with tempfile.TemporaryDirectory() as d:
    q={'deposit':12000,'monthly':50,'annual_rate':4}
    e=evidence() | {'kind':'rent_contract','unit':'만원/월','sample_n':1,'query_spec':q,'facts':[{'label':'실제 월세','value':50},{'label':'가정 환산 월비용','value':90}]}
    p=Path(d)/'rent-check'; create_package(p,'rent','t','s',[e])
    assert '등기' in (p/'index.html').read_text() and '등기' in (p/'summary.txt').read_text()
with tempfile.TemporaryDirectory() as d:
    a=evidence() | {'id':'a'}; b=evidence() | {'id':'b','scope':'다른 단지'}
    p=Path(d)/'multi'; create_package(p,'buyer','두 단지','요약',[a,b])
    m=json.loads((p/'manifest.json').read_text())
    assert 'card-1080x1350-2.svg' in m['assets']
    assert '다른 단지' in (p/'card-1080x1350-2.svg').read_text()
    for name in ('card-1080x1350.svg','card-1080x1350-2.svg','chart-1600x900.svg'):
        assert ('font-size="50"' if name.startswith('chart-1600') else 'font-size="36"') in (p/name).read_text()
        assert 'https://rt.molit.go.kr/' in ''.join(ET.parse(p/name).getroot().itertext()).replace('\n','').replace(' ','')
with tempfile.TemporaryDirectory() as d:
    e=evidence() | {'query_spec':{'budget':150}}
    p=Path(d)/'range-exports'; create_package(p,'buyer','t','s',[e])
    assert 'data-range="true"' in (p/'card-1080x1350.svg').read_text()
    assert '집값 상한 150' in ''.join(ET.parse(p/'card-1080x1350.svg').getroot().itertext()).replace('\n','')
with tempfile.TemporaryDirectory() as d:
    root=Path(d); site=root/'site'; site.mkdir()
    base=evidence() | {'period':'2026-01–2026-06'}
    sale=base | {'id':'sale','kind':'trade_distribution'}
    jeonse=base | {'id':'jeonse','kind':'jeonse_distribution','source_id':'molit-rents','release_id':'rent1'}
    q={'deposit':12000,'monthly':50,'annual_rate':4}
    contract=jeonse | {'id':'contract','kind':'rent_contract','sample_n':1,'unit':'만원/월','query_spec':q,'facts':[{'label':'실제 월세','value':50},{'label':'가정 환산 월비용','value':90}]}
    pairs=[sale | {'id':'prev','period':'2025-01–2025-03','sample_n':30,'kind':'trade_distribution','unit':'만원/㎡','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}, sale | {'id':'current','period':'2026-01–2026-03','sample_n':30,'kind':'trade_distribution','unit':'만원/㎡','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}]
    official=base | {'source_id':'rone','release_id':'rone1','sample_n':None,'unit':'지수','facts':[{'label':'지수','value':101.2}]}
    price=official | {'id':'price','kind':'price_index'}
    sentiment=official | {'id':'sentiment','kind':'sentiment_index'}
    volume=base | {'id':'volume','kind':'trade_volume','unit':'건','facts':[{'label':'거래','value':40}]}
    for template, rows in [('weekly',pairs+[price,sentiment,volume,jeonse]),('buyer',[sale,jeonse]),('rent',[jeonse,contract])]:
        p=root/template; create_package(p,template,'제목','요약',rows)
        assert verify_package(p)
        prepare_package(p,site,template)
        assert verify_package(site/template)
        doc=json.loads((p/'report.json').read_text())
        assert all(block['status']=='available' for block in doc['blocks'] if block['title'] != '개인 시나리오')
with tempfile.TemporaryDirectory() as d:
    import xml.etree.ElementTree as ET
    def r(i,deposit,monthly):
        return evidence() | {'id':i,'kind':'rent_contract','unit':'만원/월','sample_n':1,'query_spec':{'deposit':deposit,'monthly':monthly,'annual_rate':4},'facts':[{'label':'실제 월세','value':monthly},{'label':'가정 환산 월비용','value':monthly+deposit*4/1200}]}
    p=Path(d)/'r'; create_package(p,'rent','월 부담','요약',[r('a',10000,50),r('b',20000,20)])
    def widths(name): return [float(e.attrib['width']) for e in ET.parse(p/name).getroot() if e.attrib.get('data-fact-bar')]
    a=widths('chart-1600x900.svg'); b=widths('chart-1600x900-2.svg')
    assert len(a)==len(b)==2 and abs(a[1]/b[1] - (50+10000*4/1200)/(20+20000*4/1200))<1e-9
from report_package import format_value
assert format_value(10000) == '10,000' and format_value(-0.0001) == '0' and format_value(1.235) == '1.24'
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'format'; create_package(p,'buyer','t','s',[evidence()])
    svg=(p/'card-1080x1350.svg').read_text()
    assert 'font-family=' in svg and '9,000.00' not in svg and '9,000 만원' in svg
with tempfile.TemporaryDirectory() as d:
    import subprocess
    root=Path(d); doc={'template':'buyer','title':'t','summary':'s','evidence':[evidence()]}
    (root/'input.json').write_text(json.dumps(doc),encoding='utf-8')
    (root/'personal.json').write_text(json.dumps({'include':True,'fields':[{'label':'월 잔여','value':170,'unit':'만원'}]}),encoding='utf-8')
    command=[sys.executable,str(Path(__file__).parent/'new_report.py')]
    rejected=subprocess.run(command+['create',str(root/'input.json'),str(root/'no'), '--scenario-file',str(root/'personal.json')],capture_output=True)
    assert rejected.returncode != 0 and not (root/'no').exists()
    accepted=subprocess.run(command+['create',str(root/'input.json'),str(root/'yes'),'--include-scenario','--scenario-file',str(root/'personal.json')],capture_output=True)
    assert accepted.returncode == 0 and json.loads((root/'yes'/'report.json').read_text())['scenario']['include'] is True
with tempfile.TemporaryDirectory() as d:
    e=evidence() | {'scope':'서울 강남구 개포자이프레지던스 개포동 84㎡대','period':'2026-04-01 이상 ~ 2026-10-01 미만','query_spec':{'budget':100000,'canceled_excluded':True}}
    p=Path(d)/'long'; create_package(p,'buyer','매수 후보 비교','요약',[e])
    assert verify_package(p)
with tempfile.TemporaryDirectory() as d:
    a=evidence() | {'id':'a','kind':'trade_distribution','sample_n':30,'period':'2025-01–2025-03','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}
    b=a | {'id':'b','period':'2026-01–2026-03'}
    j=evidence() | {'id':'j','kind':'jeonse_distribution','source_id':'rent','release_id':'rent1','facts':[{'label':'Q25','value':300},{'label':'중간값','value':200},{'label':'Q75','value':100}]}
    try: create_package(Path(d)/'bad','weekly','t','s',[a,b,j])
    except ValueError: pass
    else: raise AssertionError('inverted weekly jeonse accepted')
with tempfile.TemporaryDirectory() as d:
    e=evidence() | {'query_spec':{'budget':100000,'area_min':59.12,'area_max':59.98}}
    p=Path(d)/'area'; create_package(p,'buyer','t','s',[e])
    for name in ('index.html','summary.txt','card-1080x1350.svg','chart-1600x900.svg'):
        text=(p/name).read_text()
        assert '59.12' in text and '59.98' in text
with tempfile.TemporaryDirectory() as d:
    base=evidence() | {'kind':'trade_distribution','sample_n':30,'unit':'만원/㎡','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}
    a=base | {'id':'previous','period':'2025-01–2025-03','facts':[{'label':'Q25','value':100},{'label':'중간값','value':200},{'label':'Q75','value':300}]}
    b=base | {'id':'current','period':'2026-01–2026-03','facts':[{'label':'Q25','value':120},{'label':'중간값','value':240},{'label':'Q75','value':360}]}
    c=evidence() | {'id':'change','kind':'change_comparison','unit':'%','sample_n':30,'period':'두 기간','query_spec':{'region':'서울','band':'84','baseline_n':30,'current_n':30},'chart_spec':{'type':'quadrant','x':'거래수 변화','y':'㎡당 중간가격 변화'},'facts':[{'label':'거래수 변화','value':0},{'label':'㎡당 중간가격 변화','value':20}]}
    spread=evidence() | {'id':'spread','kind':'relative_spread','unit':'%','sample_n':30,'period':a['period'],'query_spec':{'region':'서울','band':'84','reference_id':'previous','formula':'(Q75-Q25)/중간값'},'facts':[{'label':'중간값 대비 구간 폭','value':100}]}
    p=Path(d)/'weekly-derived'; create_package(p,'weekly','주간','요약',[a,b,c,spread]); assert verify_package(p)
    saved=json.loads((p/'report.json').read_text())
    assert saved['evidence'][2]['chart_spec']['type']=='quadrant' and saved['evidence'][3]['facts'][0]['value']==100
    assert 'data-quadrant="true"' in (p/'card-1080x1350-3.svg').read_text()
    for index, replacement in [(2,c | {'facts':[{'label':'거래수 변화','value':99},{'label':'㎡당 중간가격 변화','value':20}]}), (3,spread | {'facts':[{'label':'중간값 대비 구간 폭','value':99}]})]:
        rows=[a,b,c,spread]; rows[index]=replacement
        try: create_package(Path(d)/f'bad-derived-{index}','weekly','t','s',rows)
        except ValueError: pass
        else: raise AssertionError('incorrect derived evidence accepted')
with tempfile.TemporaryDirectory() as d:
    base=evidence() | {'kind':'trade_distribution','sample_n':30,'unit':'만원/㎡','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}
    a=base | {'id':'previous','period':'2025-01–2025-03','facts':[{'label':'Q25','value':100},{'label':'중간값','value':200},{'label':'Q75','value':300}]}
    b=base | {'id':'current','period':'2026-01–2026-03','facts':[{'label':'Q25','value':200},{'label':'중간값','value':300},{'label':'Q75','value':400}]}
    difference=evidence() | {'id':'spread-change','kind':'relative_spread_change','unit':'%p','sample_n':30,'period':'두 기간','query_spec':{'region':'서울','band':'84','baseline_n':30,'current_n':30,'formula':'두 기간 상대 구간 폭의 차이'},'facts':[{'label':'상대 구간 폭 변화','value':-100/3}]}
    p=Path(d)/'difference'; create_package(p,'weekly','t','s',[a,b,difference]); assert verify_package(p)
    bad=difference | {'facts':[{'label':'상대 구간 폭 변화','value':0}]}
    try: create_package(Path(d)/'bad-difference','weekly','t','s',[a,b,bad])
    except ValueError: pass
    else: raise AssertionError('wrong spread difference accepted')
with tempfile.TemporaryDirectory() as d:
    e=evidence() | {'kind':'price_index','sample_n':None,'unit':'지수','facts':[{'label':'변화','value':-10}]}
    from report_package import render_export_svg
    import xml.etree.ElementTree as ET
    svg=ET.fromstring(render_export_svg('t',[e],[e],1600,900))
    zero=next(x for x in svg if x.attrib.get('data-zero-axis')=='true')
    bar=next(x for x in svg if x.attrib.get('data-fact-bar')=='true')
    assert float(bar.attrib['x']) < float(zero.attrib['x1'])
with tempfile.TemporaryDirectory() as d:
    q={'deposit':10000,'monthly':50,'annual_rate':4}
    e=evidence() | {'kind':'rent_contract','unit':'만원/월','sample_n':1,'query_spec':q,'chart_spec':{'type':'scatter','x':'보증금','y':'월세'},'facts':[{'label':'실제 월세','value':50},{'label':'가정 환산 월비용','value':50+10000*4/1200}]}
    p=Path(d)/'rent-scatter'; create_package(p,'rent','t','s',[e]); assert verify_package(p)
    assert json.loads((p/'report.json').read_text())['evidence'][0]['chart_spec']['x']=='보증금'
    bad=e | {'chart_spec':{'type':'scatter','x':'월세','y':'보증금'}}
    try: create_package(Path(d)/'bad-rent-scatter','rent','t','s',[bad])
    except ValueError: pass
    else: raise AssertionError('swapped scatter dimensions accepted')
