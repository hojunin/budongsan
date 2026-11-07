// Requires agent-browser, Python and npm run build. Starts its own rent-failure server.
import {execFileSync, spawn} from "node:child_process";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import assert from "node:assert/strict";
const run = (...args) => execFileSync("agent-browser", args, {encoding: "utf8"}).trim();
const read = (expression) => JSON.parse(JSON.parse(run("eval", `JSON.stringify(${expression})`)));
const wait = (expression) => run("wait", "--fn", expression);
const server = spawn("python3", [fileURLToPath(new URL("./serve_ui_test.py", import.meta.url)), resolve("dist")], {stdio: ["ignore", "pipe", "inherit"]});
const base = await new Promise((resolve, reject) => {
  server.stdout.once("data", (data) => resolve(data.toString().trim()));
  server.once("error", reject);
  server.once("exit", (code) => reject(new Error(`Test server exited: ${code}`)));
});
try {
  run("open", `${base}/complexes`);
  run("tab", "t1");
  run("wait", ".tabulator-row");
  wait('document.querySelectorAll(".kpi-value").length === 4');
  assert.notEqual(read('document.querySelector(".kpi-value").textContent'), "–");
  wait('[...document.querySelectorAll(".kpi-sub")].some(e=>e.textContent.includes("전월세 데이터를 불러오지 못했습니다"))');
  assert.ok(read('[...document.querySelectorAll(".kpi-sub")].some(e=>e.textContent.includes("전월세 데이터를 불러오지 못했습니다"))'));
  assert.deepEqual(read('[...document.querySelectorAll(".observablehq--error")].map(e=>e.textContent)'), []);
  const next = read('[...document.querySelector(".filter-field--watch select").options].filter(e=>!e.selected).map(e=>({value:e.value,name:e.textContent.replace(/^[AB] · /,"" )}))[0]');
  run("eval", `document.querySelector('.filter-field--watch select').tomselect.setValue(${JSON.stringify(next.value)})`);
  wait(`document.querySelector(".target-heading").textContent.includes(${JSON.stringify(next.name)})`);
  run("wait", ".tabulator-row");
  run("eval", 'document.querySelector(\'.filters--complexes input[type=radio][value="1"]\').click()');
  run("wait", '.filters--complexes input[placeholder="예: 주공, 자이, 래미안"]');
  run("fill", '.filters--complexes input[placeholder="예: 주공, 자이, 래미안"]', "상계");
  wait('document.querySelector(".target-heading").textContent.includes("상계") && document.querySelector(".target-heading").textContent.includes("직접 검색")');
  run("wait", ".tabulator-row");
  run("fill", '.filters--complexes input[placeholder="예: 주공, 자이, 래미안"]', "존재하지않는단지xyz");
  run("wait", ".filter-field--search .filter-empty");
  assert.deepEqual(read('[...document.querySelectorAll(".observablehq--error")].map(e=>e.textContent)'), []);
  console.log("PASS trades/table/search work when rents fail; watch selection, direct search and empty results");
} finally {
  server.kill();
}
