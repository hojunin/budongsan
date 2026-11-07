// Validate a fresh output from measure_cls.mjs; local regression budget is 0.01.
import {readFileSync} from "node:fs";
import assert from "node:assert/strict";
const report = JSON.parse(readFileSync(process.argv[2], "utf8"));
for (const page of ["/", "/regions", "/complexes", "/market", "/budget", "/about"]) {
  const runs = report.results.filter((result) => result.page === page);
  assert.equal(runs.length, 3, `need three valid measurements of ${page}`);
  for (const result of runs) {
    assert.deepEqual(result.initial.errors, []);
    assert.ok(result.initial.cls <= .01, `${page}: initial CLS ${result.initial.cls} exceeds 0.01`);
    assert.ok(result.totalCLS <= .01, `${page}: full-session CLS ${result.totalCLS} exceeds 0.01`);
    for (const action of result.actions) {
      assert.ok(action.entries.reduce((sum, entry) => sum + entry.value, 0) <= .001, `${page}: ${action.name} shifted`);
    }
  }
}
console.log("PASS initial/full-session CLS budget and interactive layout stability on all six pages (18 runs)");
