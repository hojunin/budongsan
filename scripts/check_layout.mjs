// Requires agent-browser on PATH and npm run dev on port 3000.
import {execFileSync} from "node:child_process";
import assert from "node:assert/strict";
const run = (...args) => execFileSync("agent-browser", args, {encoding: "utf8"}).trim();
const read = (expression) => JSON.parse(JSON.parse(run("eval", `JSON.stringify(${expression})`)));
const height = (selector) => read(`document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect().height`);
for (const width of [320, 390, 1440]) {
  run("set", "viewport", String(width), "900");
  run("open", "http://localhost:3000/complexes");
  run("wait", ".tabulator-row");
  const tableHeight = height(".data-table");
  run("fill", ".table-toolbar input", "존재하지않음");
  run("wait", "--fn", 'document.querySelectorAll(".tabulator-row").length === 0');
  assert.ok(Math.abs(height(".data-table") - tableHeight) < 1, `empty table moved at ${width}px`);
  run("click", ".table-toolbar button");
  run("wait", ".tabulator-row");
  assert.ok(Math.abs(height(".data-table") - tableHeight) < 1, `table reset moved at ${width}px`);
  run("open", "http://localhost:3000/regions");
  run("wait", ".ts-control");
  const filterHeight = height(".filters");
  run("eval", 'document.querySelector(".filters select").tomselect.clear()');
  run("wait", "--fn", 'document.querySelector(".filters select").selectedOptions.length === 0');
  assert.ok(Math.abs(height(".filters") - filterHeight) < 1, `chips moved the filters at ${width}px`);
  console.log(`PASS stable table and multi-select heights at ${width}px`);
}
