// Requires agent-browser on PATH and npm run dev on port 3000.
import {execFileSync} from "node:child_process";
import assert from "node:assert/strict";
const run = (...args) => execFileSync("agent-browser", args, {encoding: "utf8"}).trim();
const base = process.env.CLS_BASE_URL ?? "http://localhost:3000";
const read = (expression) => JSON.parse(JSON.parse(run("eval", `JSON.stringify(${expression})`)));
for (const reduced of [false, true]) {
  run("set", "media", "light", reduced ? "reduced-motion" : "no-preference");
  run("set", "viewport", "390", "844");
  run("open", `${base}/regions`);
  run("tab", "t1");
  run("wait", ".tabulator");
  run("wait", "--fn", 'document.fonts.status === "loaded"');
  run("wait", "500");
  run("eval", 'window.chipShifts=[];new PerformanceObserver(list=>{for(const e of list.getEntries())if(e.sources.some(s=>s.node?.closest?.(".ts-control")))window.chipShifts.push(e.value)}).observe({type:"layout-shift"})');
  for (const index of [2, 0, -1]) {
    const before = read('document.querySelector(".filters select").tomselect.items.length');
    run("eval", `const select${index < 0 ? 'last' : index}=document.querySelector(".filters select").tomselect;select${index < 0 ? 'last' : index}.removeItem(select${index < 0 ? 'last' : index}.items.at(${index}))`);
    run("wait", "400");
    assert.equal(read('document.querySelector(".filters select").tomselect.items.length'), before - 1);
  }
  assert.equal(read('window.chipShifts.reduce((sum, value)=>sum+value,0)'), 0);
  run("eval", 'document.querySelector(".filters select").tomselect.clear()');
  run("fill", ".ts-control input", "강남");
  run("wait", "--fn", '[...document.querySelectorAll(".ts-dropdown .option")].length>0 && [...document.querySelectorAll(".ts-dropdown .option")].every(e=>e.textContent.includes("강남"))');
  run("press", "Enter");
  assert.ok(read('[...document.querySelector(".filters select").selectedOptions].some(e=>e.textContent.includes("강남"))'));
  console.log(`PASS first/middle/last chip deletion: zero shift, search after clear; reducedMotion=${reduced}`);
}
