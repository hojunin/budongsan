// Requires agent-browser on PATH and npm run dev on port 3000.
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const run=(...args)=>execFileSync('agent-browser',args,{encoding:'utf8'}).trim();
const base = process.env.CLS_BASE_URL ?? "http://localhost:3000";
for (const width of [320,390,1440]) {
 run('set','viewport',String(width),'900');
 for(const page of ['', 'regions','complexes','market','budget','about']) {
  run('open',`${base}/${page}`);
  run("tab", "t1");
  run('wait',page==='about'?'#observablehq-main h2':'.filters form');
  if(page!=='about') run('wait','.interactive-chart svg');
  const raw=run('eval',`JSON.stringify({width:innerWidth,scroll:document.documentElement.scrollWidth,errors:[...document.querySelectorAll('.observablehq--error')].map(e=>e.textContent),controls:[...document.querySelectorAll('.filters input[type=number],.filters .ts-control')].every(e=>e.getBoundingClientRect().height>=34)})`);
  const data=JSON.parse(JSON.parse(raw));
  assert.equal(data.scroll,data.width,`${page} overflow at ${width}`);
  assert.deepEqual(data.errors,[],`${page} runtime error`);
  assert.ok(data.controls,`${page} touch targets`);
  console.log(`PASS ${width}px /${page}`);
 }
}
