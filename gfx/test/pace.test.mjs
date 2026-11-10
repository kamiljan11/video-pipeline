import test from 'node:test';
import assert from 'node:assert/strict';
import { PAGES_MAX, SHOT_TIMEOUTS, pageCount, shot } from '../pace_lib.mjs';

test('pages follow the free cores, 1..PAGES_MAX', () => {
  assert.equal(pageCount(32, 4), PAGES_MAX);   // idle laptop: 7 -> capped at 6
  assert.equal(pageCount(32, 20), 3);
  assert.equal(pageCount(32, 40), 1);          // the night: load ~40 on 32 cores -> 1 page, not 6
  assert.equal(pageCount(4, 0), 1);
});

test('GFX_PAGES overrides, a bad value is refused', () => {
  assert.equal(pageCount(32, 40, '4'), 4);
  assert.throws(() => pageCount(32, 4, '0'), /GFX_PAGES/);
  assert.throws(() => pageCount(32, 4, 'x'), /GFX_PAGES/);
  assert.throws(() => pageCount(32, 4, '500'), /GFX_PAGES/);  // review 2026-11-10: capped at PAGES_CAP
});

const timeout = () => Object.assign(new Error('page.screenshot: Timeout 30000ms exceeded.'), { name: 'TimeoutError' });

test('a screenshot timeout is retried with the next, longer wait', async () => {
  const seen = [], logs = [];
  const page = { screenshot: async o => { seen.push(o.timeout); if (seen.length < 3) throw timeout(); return 'png'; } };
  assert.equal(await shot(page, { path: 'a.png' }, 'c1', m => logs.push(m)), 'png');
  assert.deepEqual(seen, SHOT_TIMEOUTS);
  assert.equal(logs.length, 2);
  assert.match(logs[0], /slow gfx c1/);
});

test('the last timeout and any other error fail with the card id', async () => {
  const always = { screenshot: async () => { throw timeout(); } };
  await assert.rejects(shot(always, {}, 'c2', () => {}, [1, 2]), /c2: screenshot/);
  let n = 0;
  const other = { screenshot: async () => { n++; throw new Error('Target closed'); } };
  await assert.rejects(shot(other, {}, 'c3', () => {}), /c3: screenshot Target closed/);
  assert.equal(n, 1);  // not a timeout -> no retry
});
