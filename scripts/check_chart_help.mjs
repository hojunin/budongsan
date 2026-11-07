// Requires agent-browser and the local preview on port 3000.
import {execFileSync} from "node:child_process";
import assert from "node:assert/strict";
const run = (...args) => execFileSync("agent-browser", args, {encoding: "utf8"}).trim();
const read = (expression) => JSON.parse(JSON.parse(run("eval", `JSON.stringify(${expression})`)));
for (const [page, count] of [["",4],["regions",1],["complexes",1],["market",5],["budget",1]]) {
  run("open", `http://localhost:3000/${page}`);
  run("tab", "t1");
  run("wait", ".interactive-chart svg");
  assert.equal(read('document.querySelectorAll(".chart-info").length'), count);
  assert.ok(read('[...document.querySelectorAll(".chart-info summary")].every(e=>e.getAttribute("aria-label")?.endsWith("설명"))'));
}
run("set", "viewport", "390", "844");
run("open", "http://localhost:3000/market");
run("tab", "t1");
run("wait", ".interactive-chart svg");
run("scrollintoview", ".chart-info summary");
run("wait", "--fn", 'document.fonts.status === "loaded" && document.getAnimations().every(a=>a.playState!=="running")');
const chartTop = read('document.querySelector(".chart-slot").getBoundingClientRect().top');
run("hover", ".chart-info summary");
run("wait", ".chart-info[open]");
assert.ok(read('document.querySelector(".chart-info-panel").getBoundingClientRect().width <= innerWidth-32'));
assert.equal(read('document.querySelector(".chart-slot").getBoundingClientRect().top'), chartTop);
run("press", "Escape");
assert.equal(read('document.querySelectorAll(".chart-info[open]").length'), 0);
run("focus", ".chart-info summary");
run("press", "Escape");
run("press", "Enter");
run("wait", ".chart-info[open]");
run("click", ".chart-heading h2");
assert.equal(read('document.querySelectorAll(".chart-info[open]").length'), 0);
run("eval", 'const field=document.createElement("div");field.id="placeholder-probe";field.className="filter-field";document.querySelector(".filters").append(field)');
assert.equal(read('getComputedStyle(document.querySelector("#placeholder-probe"),"::before").content'), "none");
assert.equal(read('getComputedStyle(document.querySelector("#placeholder-probe"),"::after").content'), "none");
run("eval", 'document.querySelector("#placeholder-probe").remove()');
console.log("PASS 12 chart explanations, hover, keyboard, Escape/outside dismissal, stable layout, no filter loading placeholders");
