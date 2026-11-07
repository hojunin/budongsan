import assert from 'node:assert/strict';
import {PALETTE, regionColor} from '../src/components/colors.js';
assert.equal(regionColor('서울 전체'), regionColor('서울'));
assert.equal(regionColor('서울>강북지역>종로구'), regionColor('서울 · 종로구'));
assert.notEqual(regionColor('서울'),regionColor('경기'));
assert.ok(!PALETTE.includes('#c23531') && !PALETTE.includes('#2459aa'));
console.log('ok');
