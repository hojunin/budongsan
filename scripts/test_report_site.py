"""Build three synthetic report packages in an isolated temporary site; no collection."""
import json
import os
import shutil
import socket
import sys
import subprocess
import tempfile
from pathlib import Path
from report_package import create_package, prepare_package

ROOT = Path(__file__).resolve().parents[1]

def evidence():
    return {'id':'base','source_id':'molit','release_id':'fixture','is_sample':False,'rights':'allowed','coverage_verified':True,'identity_verified':True,'reviewed_by':'fixture','period':'2026-01–2026-06','scope':'합성 검증 범위','unit':'만원','sample_n':5,'source_url':'https://example.org/','facts':[{'label':'Q25','value':100},{'label':'중간값','value':200},{'label':'Q75','value':300}]}

with tempfile.TemporaryDirectory(prefix='apt-insight-site-') as tmp:
    root=Path(tmp)
    shutil.copytree(ROOT/'src',root/'src')
    (root/'scripts').mkdir()
    for name in ('report_package.py','verify_reports.py','refresh_loaders.py','duckdb_wasm_cdn.js'):
        shutil.copyfile(ROOT/'scripts'/name,root/'scripts'/name)
    for name in ('package.json','observablehq.config.js'):
        shutil.copyfile(ROOT/name,root/name)
    (root/'node_modules').symlink_to(ROOT/'node_modules',target_is_directory=True)
    base=evidence(); sale=base | {'id':'sale','kind':'trade_distribution'}
    rent=base | {'id':'jeonse','kind':'jeonse_distribution','source_id':'rent','release_id':'fixture-rent'}
    q={'deposit':12000,'monthly':50,'annual_rate':4}
    contract=rent | {'id':'contract','kind':'rent_contract','sample_n':1,'unit':'만원/월','query_spec':q,'facts':[{'label':'실제 월세','value':50},{'label':'가정 환산 월비용','value':90}]}
    pairs=[sale | {'id':'prev','period':'2025-01–2025-03','sample_n':30,'unit':'만원/㎡','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}, sale | {'id':'current','period':'2026-01–2026-03','sample_n':30,'unit':'만원/㎡','query_spec':{'region':'서울','band':'84','canceled_excluded':True}}]
    official=base | {'source_id':'rone','release_id':'fixture-rone','sample_n':None,'unit':'지수','facts':[{'label':'지수','value':101.2}]}
    price=official | {'id':'price','kind':'price_index'}; sentiment=official | {'id':'sentiment','kind':'sentiment_index'}
    volume=base | {'id':'volume','kind':'trade_volume','unit':'건','facts':[{'label':'거래','value':40}]}
    fixtures={'weekly':pairs+[price,sentiment,volume,rent], 'buyer':[sale,rent], 'rent':[rent,contract]}
    for template, rows in fixtures.items():
        package=root/('draft-'+template)
        scenario={'include':True,'fields':[{'label':'월 잔여','value':170,'unit':'만원'}]} if template=='buyer' else None
        create_package(package,template,'합성 제목 ${1+1}','합성 fixture 요약',rows,scenario=scenario)
        prepare_package(package,root/'src/reports','fixture-'+template)
    env=os.environ.copy(); env['OBSERVABLE_TELEMETRY_DISABLE']='true'
    subprocess.run(['npm','run','build'],cwd=root,env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=180)
    posts=json.loads((root/'src/.observablehq/cache/data/reports.json').read_text())
    assert {p['slug'] for p in posts} >= {'fixture-weekly','fixture-buyer','fixture-rent'}
    for name in fixtures:
        assert (root/'dist/reports'/f'fixture-{name}.html').exists()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(root/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        def browser(*args): return subprocess.check_output(['agent-browser','--session','terra-implementation',*args],text=True,timeout=60).strip()
        for name in fixtures:
            browser('open',f'http://127.0.0.1:{port}/reports/fixture-{name}.html'); browser('tab','t1'); browser('wait','#observablehq-main h1')
            raw=browser('eval', "JSON.stringify({title:document.querySelector('#observablehq-main h1').textContent,errors:[...document.querySelectorAll('.observablehq--error')].map(e=>e.textContent),image:[...document.querySelectorAll('#observablehq-main img')].some(i=>i.complete&&i.naturalWidth===320),exports:[...document.querySelectorAll('#observablehq-main a[download]')].length})")
            result=json.loads(json.loads(raw))
            assert result['title']=='합성 제목 ${1+1}' and result['errors']==[] and result['image'] and result['exports']>=5, (name,result)
            if name == 'weekly':
                assert '미공표' in browser('eval', "document.querySelector('#observablehq-main').innerText")
    finally:
        server.terminate(); server.wait(timeout=5)
    print('PASS synthetic weekly/buyer/rent package → list → site build and browser')
