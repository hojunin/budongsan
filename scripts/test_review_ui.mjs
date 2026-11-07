// Local built-site regression; no collection or publication.
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const run = (...args) => execFileSync('agent-browser', ['--session', 'terra-implementation', ...args], {encoding:'utf8', timeout:60000}).trim();
const read = (expression) => JSON.parse(JSON.parse(run('eval', `JSON.stringify(${expression})`)));
const base = process.env.CLS_BASE_URL ?? 'http://127.0.0.1:8766';
for (const theme of ['light','dark']) for (const width of [320,390,1440]) {
  run('set','media',theme); run('set','viewport',String(width),'900');
  for (const [page, selector] of [['personal','#personal-calculate'],['compare','.compare-filters .ts-control'],['outlook','#observablehq-main h2']]) {
    run('open',`${base}/${page}`); run('tab','t1'); run('wait',selector); run('wait','500');
    const state=read(`({width:innerWidth,scroll:document.documentElement.scrollWidth,errors:[...document.querySelectorAll('.observablehq--error')].map(e=>e.textContent)})`);
    assert.equal(state.width,state.scroll,`${theme} ${width} /${page} overflow`);
    assert.deepEqual(state.errors,[],`${theme} ${width} /${page} runtime error`);
    if (page==='compare') {
      const limits=read(`[...document.querySelectorAll('.compare-filters select')].map(e=>e.tomselect?.settings.maxItems)`);
      assert.equal(limits.at(-1),3);
      if (theme==='dark') {
        const c=read(`(()=>{const s=getComputedStyle(document.querySelector('.compare-filters .ts-control'));return [s.color,s.backgroundColor]})()`);
        assert.notEqual(c[0],c[1]);
      }
    }
    console.log(`PASS ${theme} ${width} /${page}`);
  }
}
run('open',`${base}/personal`); run('tab','t1'); run('wait','#personal-calculate');
run('eval',`(()=>{for(const [k,v] of Object.entries({price:10000,cash:5000,income:500,living:200,debt:50,housing:30,loan:6000,rate:0,years:10,cost:200,reserve:1000})){const i=document.querySelector('[name="'+k+'"]');i.value=v;i.dispatchEvent(new Event('input',{bubbles:true}))}document.querySelector('#personal-calculate').click()})()`);
assert.match(read(`document.querySelector('#personal-result').textContent`),/월 잔여 170만원/);
run('eval',`(()=>{const i=document.querySelector('[name="income"]');i.value=400;i.dispatchEvent(new Event('input',{bubbles:true}))})()`);
assert.match(read(`document.querySelector('#personal-result').textContent`),/다시 계산/);
run('eval',`document.querySelector('#personal-calculate').focus()`); run('press','Enter');
assert.match(read(`document.querySelector('#personal-result').textContent`),/월 잔여 70만원/);
assert.equal(read(`location.search`),'');
console.log('PASS personal invalidation and keyboard calculation');
run('open',`${base}/compare`); run('tab','t1'); run('wait','--fn', `document.querySelectorAll('.interactive-chart svg').length === 5 && document.querySelectorAll('.compare-filters .ts-control').length === 3 && !!document.querySelector('.compare-period')?.textContent.includes('기간')`);
run('eval',`document.querySelector('.chart-info summary').focus()`);
const wasOpen=read(`document.querySelector('.chart-info').open`); run('press','Enter');
assert.equal(read(`document.querySelector('.chart-info').open`),!wasOpen);
if (wasOpen) { run('press','Enter'); assert.equal(read(`document.querySelector('.chart-info').open`),true); }
console.log('PASS chart explanation opens by keyboard');
