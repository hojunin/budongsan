"""Exercise compare charts and frozen evidence in an isolated synthetic site."""
import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from report_package import create_package, verify_package

ROOT = Path(__file__).resolve().parents[1]

def browser(*args):
    return subprocess.check_output(['agent-browser','--session','terra-implementation',*args],text=True,timeout=60).strip()

def read(expression):
    return json.loads(json.loads(browser('eval', f'JSON.stringify({expression})')))

with tempfile.TemporaryDirectory(prefix='apt-compare-fixture-') as tmp:
    root=Path(tmp); shutil.copytree(ROOT/'src',root/'src'); (root/'scripts').mkdir()
    for name in ('report_package.py','verify_reports.py','refresh_loaders.py','duckdb_wasm_cdn.js'):
        shutil.copyfile(ROOT/'scripts'/name,root/'scripts'/name)
    for name in ('package.json','observablehq.config.js'): shutil.copyfile(ROOT/name,root/name)
    (root/'node_modules').symlink_to(ROOT/'node_modules',target_is_directory=True)
    now=dt.datetime.now(ZoneInfo('Asia/Seoul')); first=pd.Timestamp(now.year,now.month,1)
    end=first-pd.DateOffset(months=1); current=end-pd.DateOffset(months=2); previous=current-pd.DateOffset(years=1)
    key='11110|샘플동|합성단지'
    trades=[]
    for date, prices in [(previous,[10000,30000]*15),(current,[20000,40000]*15)]:
        for price in prices:
            trades.append({'deal_date':date.date(),'sgg':'11110','sgg_name':'합성구','umd':'샘플동','apt':'합성단지','complex_key':key,'area':84.9,'band':'84','price':price,'is_sample':False,'canceled':False})
    for area in [59.12,59.2,59.3,59.4,59.5,59.98]:
        trades.append({'deal_date':current.date(),'sgg':'11110','sgg_name':'합성구','umd':'샘플동','apt':'합성단지','complex_key':key,'area':area,'band':'59','price':15000,'is_sample':False,'canceled':False})
    rents=[]
    for i,(deposit,monthly,sample) in enumerate([(10000,0,False),(12000,50,False),(9000,None,False),(11000,30,True)]):
        rents.append({'deal_date':current.date(),'ym':current.strftime('%Y-%m'),'sgg':'11110','umd':'샘플동','apt':f'합성계약{i}','complex_key':key,'area':84.9,'band':'84','deposit':deposit,'monthly':monthly,'jeonse':monthly==0 if monthly is not None else None,'is_sample':sample})
    cache=root/'src/.observablehq/cache/data'; cache.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(trades).to_parquet(cache/'trades.parquet',index=False)
    pd.DataFrame(rents).to_parquet(cache/'rents.parquet',index=False)
    env=os.environ.copy(); env['OBSERVABLE_TELEMETRY_DISABLE']='true'
    subprocess.run(['npm','run','build'],cwd=root,env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=180)
    with socket.socket() as sock: sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(root/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        browser('set','viewport','390','900'); browser('open',f'http://127.0.0.1:{port}/compare.html'); browser('tab','t1')
        browser('wait','--fn',"document.querySelector('#observablehq-main')?.innerText.includes('중간값 대비 가운데 50% 구간 폭')")
        state=read("({text:document.querySelector('#observablehq-main').innerText,errors:[...document.querySelectorAll('.observablehq--error')].map(e=>e.textContent),scroll:document.documentElement.scrollWidth,width:innerWidth})")
        assert not state['errors'] and state['scroll']==state['width'], state
        assert '59.12–59.98㎡' in state['text'] and '전년 100%' in state['text'] and '최근 66.67%' in state['text'] and '-33.33%p' in state['text'], state['text']
        browser('eval',"document.querySelector('.rent-scatter-details > summary').click()")
        browser('wait','.rent-scatter-details .interactive-chart svg')
        browser('eval',"document.querySelector('.rent-scatter-details details > summary').click()")
        text=read("document.querySelector('.rent-scatter-details').innerText")
        assert '합성계약0' in text and '합성계약1' in text and '합성계약2' not in text and '합성계약3' not in text, text
        browser('eval', "(()=>{const t=document.querySelector('.compare-rent-controls select').tomselect; t.setValue(Object.keys(t.options).slice(0,2)); const r=document.querySelector('.compare-rent-controls input[type=number]'); r.value='4'; r.dispatchEvent(new Event('input',{bubbles:true}))})()")
        browser('wait','--fn', "document.querySelector('#observablehq-main').innerText.includes('가정 환산 월비용') && document.querySelector('#observablehq-main').innerText.includes('33.33') && document.querySelector('#observablehq-main').innerText.includes('90만')")
        for theme in ('light','dark'):
            browser('set','media',theme)
            for width in (320,390,1440):
                browser('set','viewport',str(width),'900')
                check=read("({width:innerWidth,scroll:document.documentElement.scrollWidth,errors:[...document.querySelectorAll('.observablehq--error')].map(e=>e.textContent)})")
                assert check['width']==check['scroll'] and not check['errors'], (theme,width,check)
        if os.environ.get('APT_COMPARE_SCREENSHOT'):
            browser('set','media','light'); browser('set','viewport','390','900')
            browser('eval', "(()=>{const b=document.createElement('div');b.textContent='합성 테스트 데이터';b.style='position:fixed;top:0;right:0;z-index:9999;background:#fff;color:#111;padding:8px';document.body.append(b)})()")
            browser('screenshot','--full',os.environ['APT_COMPARE_SCREENSHOT'])
        snap=browser('snapshot','-i')
        def download(label, name):
            match=re.search(r'- button "'+re.escape(label)+r'" \[ref=(e\d+)\]',snap)
            assert match, snap
            path=root/name; browser('download','@'+match.group(1),str(path)); return json.loads(path.read_text())
        weekly=download('기간 비교를 근거 초안으로 저장','weekly.json')
        by_id={e['id']:e for e in weekly['evidence']}
        assert by_id['price-volume-change']['chart_spec']['type']=='quadrant'
        assert abs(by_id['spread-current']['facts'][0]['value'] - 200/3)<1e-8
        assert abs(by_id['spread-change']['facts'][0]['value'] + 100/3)<1e-8
        rent=download('임대 비교를 근거 초안으로 저장','rent.json')
        assert len(rent['evidence']) == 2 and all(e['chart_spec']=={'type':'scatter','x':'보증금','y':'월세'} for e in rent['evidence'])
        buyer=download('선택 분포를 근거 초안으로 저장','buyer.json')
        a59=next(e for e in buyer['evidence'] if e['query_spec']['band']=='59')
        assert (a59['query_spec']['area_min'],a59['query_spec']['area_max'])==(59.12,59.98)
        for doc, name in [(weekly,'weekly-package'),(buyer,'buyer-package'),(rent,'rent-package')]:
            for e in doc['evidence']: e.update(rights='allowed',coverage_verified=True,identity_verified=True,reviewed_by='synthetic fixture')
            create_package(root/name,doc['template'],doc['title'],doc['summary'],doc['evidence'])
            assert verify_package(root/name)
        assert 'data-quadrant="true"' in (root/'weekly-package'/'card-1080x1350-3.svg').read_text()
    finally:
        server.terminate(); server.wait(timeout=5)
print('PASS synthetic compare charts, area range, null/sample gates and frozen evidence')
