import assert from 'node:assert/strict';
import {distribution, rentCost} from '../src/components/graphics.js';
const d = distribution([1,2,3,4,5], 0);
assert.deepEqual(d, {n:5, q1:2, median:3, q3:4, below:0, share:0});
assert.equal(distribution([1,2,3,4], 10), null);
assert.equal(distribution([1,2,3,4,5], 10).share, 1);
assert.equal(rentCost({deposit:12000, monthly:50}, 4), 90);
assert.equal(rentCost({deposit:12000, monthly:null}, 4), null);
assert.equal(rentCost({deposit:12000, monthly:50}, ''), null);
console.log('ok');
import {periodComparison} from '../src/components/graphics.js';
assert.equal(periodComparison(Array(29).fill(2), Array(30).fill(1)), null);
const comparison = periodComparison(Array(30).fill(2), Array(30).fill(1));
assert.equal(comparison.priceChange, 1);
assert.equal(comparison.volumeChange, 0);
import {completedWindow} from '../src/components/graphics.js';
for (const t of ['2026-11-07T06:00:00Z','2026-11-07T15:00:00Z']) {
  const {start,end} = completedWindow(new Date(t));
  assert.equal(start.toISOString(), '2026-04-01T00:00:00.000Z');
  assert.equal(end.toISOString(), '2026-10-01T00:00:00.000Z');
  assert.ok(new Date('2026-04-01T00:00:00Z') >= start);
  assert.ok(!(new Date('2026-10-01T00:00:00Z') < end));
}
import {withinSelectionLimit} from '../src/components/graphics.js';
assert.equal(withinSelectionLimit([1,2,3]), true);
assert.equal(withinSelectionLimit([1,2,3,4]), false);
assert.equal(periodComparison(Array(30).fill(1e308), Array(30).fill(1e-308)), null);
