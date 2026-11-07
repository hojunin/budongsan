import assert from 'node:assert/strict';
import {test} from 'node:test';
import {num, won, pct, signed} from '../src/components/format.js';

test('numbers use grouping and at most two decimals without trailing zeroes', () => {
  for (const [value, expected] of [[1234.5678, '1,234.57'], [12, '12'], [1.2, '1.2'], [1.005, '1.01'], ['12.345', '12.35'], [-0.001, '0'], [-0, '0'], [12345678901234567890n, '12,345,678,901,234,567,890']]) assert.equal(num(value), expected);
  assert.equal(num(1.2345, 8), '1.23');
  assert.equal(num(1.6, 0), '2');
});
test('missing and invalid values remain missing across units', () => {
  for (const value of [null, undefined, '', ' ', NaN, Infinity, -Infinity, 'invalid']) {
    for (const format of [num, won, pct, signed]) assert.equal(format(value), '–');
  }
});
test('money and percentages preserve units and rounded signs', () => {
  assert.equal(won(123456), '12.35억');
  assert.equal(won(9876.543), '9,876.54만');
  assert.equal(won(-123456), '-12.35억');
  assert.equal(pct(.123456), '12.35%');
  assert.equal(signed(.123456), '+12.35%');
  assert.equal(signed(-.123456), '-12.35%');
  assert.equal(signed(.000001), '0%');
  assert.equal(signed(-.000001), '0%');
});
