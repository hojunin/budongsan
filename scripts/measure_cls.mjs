// Chrome must be running with remote debugging; e.g. agent-browser get cdp-url.
// Usage: node scripts/measure_cls.mjs http://127.0.0.1:53626 [output.json] [runs]
import {writeFileSync} from "node:fs";
const endpoint = process.argv[2];
const base = process.env.CLS_BASE_URL ?? "http://localhost:3000";
if (!endpoint) throw new Error("Pass Chrome's HTTP remote-debugging endpoint");
const targets = await (await fetch(`${endpoint}/json/list`)).json();
const target = targets.find((t) => t.type === "page" && t.url.startsWith("http://localhost:3000")) ?? targets.find((t) => t.type === "page");
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve) => socket.addEventListener("open", resolve, {once: true}));
let id = 0;
const pending = new Map();
socket.addEventListener("message", ({data}) => {
  const message = JSON.parse(data);
  const request = pending.get(message.id);
  if (!request) return;
  pending.delete(message.id);
  message.error ? request.reject(new Error(JSON.stringify(message.error))) : request.resolve(message.result);
});
const send = (method, params = {}) => new Promise((resolve, reject) => { const key = ++id; pending.set(key, {resolve, reject}); socket.send(JSON.stringify({id: key, method, params})); });
const evaluate = async (expression) => {
  const result = await send("Runtime.evaluate", {expression, returnByValue: true, awaitPromise: true});
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
};
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const instrumentation = `
window.clsEntries = [];
new PerformanceObserver(list => {
  for (const entry of list.getEntries()) window.clsEntries.push({time:entry.startTime,value:entry.value,recent:entry.hadRecentInput,sources:entry.sources.map(s=>({tag:s.node?.nodeName,class:s.node?.className?.baseVal??s.node?.className,text:s.node?.textContent?.slice(0,80),from:s.previousRect.toJSON(),to:s.currentRect.toJSON()}))});
}).observe({type:'layout-shift',buffered:true});
window.clsScore = (entries=window.clsEntries) => {
  let max=0,sum=0,start=0,last=0;
  for(const e of entries){if(e.recent)continue;if(sum && e.time-last<1000 && e.time-start<5000)sum+=e.value;else{sum=e.value;start=e.time;}last=e.time;max=Math.max(max,sum);}
  return max;
};
if(window.clsScore([{time:0,value:.1},{time:500,value:.2},{time:1800,value:.4},{time:1900,value:.9,recent:true}])!==.4)throw new Error('CLS session-window self-check failed');
if(Math.abs(window.clsScore(Array.from({length:7},(_,i)=>({time:i*900,value:.1})))-.6)>1e-8)throw new Error('CLS five-second cap self-check failed');`;
const results = [];
let instrumentationId;
try {
  await send("Page.enable"); await send("Network.enable");
  await send("Emulation.setDeviceMetricsOverride", {width: 390, height: 844, deviceScaleFactor: 3, mobile: true});
  await send("Emulation.setTouchEmulationEnabled", {enabled: true});
  await send("Emulation.setCPUThrottlingRate", {rate: 4});
  await send("Network.setCacheDisabled", {cacheDisabled: true});
  await send("Network.emulateNetworkConditions", {offline: false, latency: 50, downloadThroughput: 1125000, uploadThroughput: 187500, connectionType: "cellular4g"});
  instrumentationId = (await send("Page.addScriptToEvaluateOnNewDocument", {source: instrumentation})).identifier;
  await send("Emulation.setEmulatedMedia", {features: [{name: "prefers-color-scheme", value: "light"}, {name: "prefers-reduced-motion", value: "no-preference"}]});
  for (let run = 1; run <= Number(process.argv[4] ?? 3); run++) {
    for (const page of ["", "regions", "complexes", "market", "budget", "about"]) {
      await send("Page.navigate", {url: `${base}/${page}`});
      const deadline = Date.now() + 45000;
      let ready = false;
      while (Date.now() < deadline) {
        await delay(200);
        ready = await evaluate(`document.readyState==='complete' && document.fonts.status==='loaded' && ${page === "about" ? '!!document.querySelector("#observablehq-main h2")' : '!!document.querySelector(".interactive-chart svg") && !!document.querySelector(".ts-control")'}`);
        if (ready) break;
      }
      await delay(1500);
      const initial = await evaluate('({cls:window.clsScore(),entries:window.clsEntries,errors:[...document.querySelectorAll(".observablehq--error")].map(e=>e.textContent)})');
      if (!ready || initial.errors.length) throw new Error(`${page} failed to settle: ${JSON.stringify(initial.errors)}`);
      const actions = [];
      const act = async (name, expression) => {
        const before = await evaluate('window.clsEntries.length');
        await evaluate(expression); await delay(1200);
        actions.push({name, ...await evaluate(`({cls:window.clsScore(),entries:window.clsEntries.slice(${before})})`)});
      };
      if (page === "regions" || page === "market") {
        await act("remove chip", 'document.querySelector(".filters select").tomselect.removeItem(document.querySelector(".filters select").tomselect.items[0])');
      }
      if (page === "regions" || page === "complexes") {
        await evaluate('document.querySelector(".data-table").scrollIntoView({block:"center"})');
        await delay(200);
        await act("empty table search", 'const input=document.querySelector(".table-toolbar input");input.focus();input.value="존재하지않음";input.dispatchEvent(new Event("input",{bubbles:true}))');
        await act("reset table search", 'document.querySelector(".table-toolbar button").click()');
      }
      if (page === "budget") await act("change interest", 'const input=document.querySelector("input[type=number][step=\\"0.05\\"]");input.value=5.5;input.dispatchEvent(new Event("input",{bubbles:true}))');
      if (page !== "about") {
        await evaluate('document.querySelector(".interactive-chart").scrollIntoView({block:"center"})');
        await delay(200);
        await act("chart zoom and legend", `(async()=>{const url=performance.getEntriesByType('resource').find(r=>r.name.includes('/_npm/echarts@')&&r.name.endsWith('.js'))?.name;const e=await import(url);const chart=e.getInstanceByDom(document.querySelector('.interactive-chart'));chart.dispatchAction({type:'dataZoom',start:25,end:75});if(chart.getOption().series.length)chart.dispatchAction({type:'legendToggleSelect',name:chart.getOption().series[0].name})})()`);
      }
      const result = {run, page: `/${page}`, initial, actions, totalCLS: await evaluate('window.clsScore()')};
      results.push(result);
      writeFileSync(process.argv[3] ?? '/tmp/apt-cls-mobile.json', JSON.stringify({conditions: {viewport: '390x844', dpr: 3, cpuSlowdown: 4, network: '9 Mbps / 50ms latency', baseURL: base, browserCache: 'disabled', interactions: 'programmatic, no recent-input exclusion benefit'}, results}, null, 2));
      console.log(JSON.stringify({run, page: result.page, initial: initial.cls, total: result.totalCLS}));
    }
  }
} finally {
  if (instrumentationId) await send("Page.removeScriptToEvaluateOnNewDocument", {identifier: instrumentationId});
  await send("Emulation.setCPUThrottlingRate", {rate: 1});
  await send("Network.setCacheDisabled", {cacheDisabled: false});
  await send("Network.emulateNetworkConditions", {offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1});
  socket.close();
}
