// node --test gfx/test/*.test.mjs   ("count" card, ADR-0005 pilot: numbers in the text count up, GSAP seeked per frame)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';
import { COUNT_DELAY, COUNT_DUR, countParts, fmtNum, numWidth, hasNumber } from '../count_lib.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });

test('numbers are found with their decimals and thousands group, the rest of the text stays', () => {
  assert.deepEqual(countParts('95%'), [{ value: 95, dec: 0, group: false, final: '95' }, '%']);
  assert.deepEqual(countParts('2,5 dnia'), [{ value: 2.5, dec: 1, group: false, final: '2,5' }, ' dnia']);
  assert.deepEqual(countParts('12 000 zł')[0], { value: 12000, dec: 0, group: true, final: '12 000' });
  assert.deepEqual(countParts('50–70%').filter(p => typeof p !== 'string').map(p => p.value), [50, 70]);
  assert.deepEqual(countParts('Koszt: 5 h'), ['Koszt: ', { value: 5, dec: 0, group: false, final: '5' }, ' h']);
  assert.equal(hasNumber('bez liczby'), false);
  const counted = t => countParts(t).filter(p => typeof p !== 'string').map(p => p.final);
  assert.deepEqual(counted('Q3 2025'), ['2025']);  // not "3 202" + "5"
  assert.deepEqual(counted('od 2 1000 zł'), ['2', '1000']);
  for (const t of ['B2B', 'v2.0', '15:30', '10.5', 'kod 007']) assert.deepEqual(counted(t), [], t);
  assert.equal(countParts('kod 007 i 5 h').map(p => p.final ?? p).join(''), 'kod 007 i 5 h');  // nothing lost or doubled
  assert.deepEqual(counted('-5%'), ['5']);  // the minus stays as text: -0% .. -5%
});

test('a number is written the Polish way while it counts', () => {
  assert.equal(fmtNum(2.46, 1, false), '2,5');
  assert.equal(fmtNum(12000, 0, true), '12\u00a0000');
  assert.equal(fmtNum(950, 0, true), '950');
  assert.equal(fmtNum(-0.01, 0, false), '0');  // an easing overshoot never shows "-0"
  assert.equal(numWidth('95'), 2);
  assert.ok(numWidth('12 000') < 6);  // a space is narrower than a digit: no gap before the number
});

const framesOf = (mov) => execFileSync('ffmpeg', ['-v', 'error', '-i', mov, '-f', 'framemd5', '-'], { encoding: 'utf8' })
  .split('\n').filter(l => l && !l.startsWith('#')).map(l => l.split(',').pop().trim());
const render = (specs) => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'count-')); made.push(work);
  const specFile = path.join(work, 'gfx_specs.json'); fs.writeFileSync(specFile, JSON.stringify(specs));
  const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
  assert.equal(r.status, 0, r.stderr);
  return path.join(work, 'gfx');
};

test('the count always ends before the fade-out; a card too short to count shows its numbers at once', () => {
  assert.equal(COUNT_DUR(0.5), 0);  // the panel minimum
  assert.ok(Math.abs(COUNT_DUR(3) - 1.2) < 1e-9);
  assert.equal(COUNT_DUR(10), 1.6);
  for (let d = 0.5; d <= 60; d += 0.05) assert.ok(COUNT_DUR(d) === 0 || COUNT_DELAY + COUNT_DUR(d) <= d - 0.35, `dur ${d}`);
});

test('the same count card gives the same frames twice, and the number really moves', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  // no icon: the icon pop of kw cards is not pixel-stable between runs (antialiasing of the rotating svg), counts are
  const spec = [{ id: 'c', type: 'count', text: '95%', sub: 'firm', dur: 2.5 }, { id: 'v', type: 'count', text: '2,5 dnia', dur: 2.5, canvas: 'v', compact: true }];
  const a = render(spec), b = render(spec);
  for (const id of ['c', 'v']) {
    const fa = framesOf(path.join(a, `${id}.mov`)), fb = framesOf(path.join(b, `${id}.mov`));
    assert.equal(fa.length, 75);
    assert.deepEqual(fa, fb, `${id}: frames differ between two renders`);
    assert.ok(new Set(fa.slice(12, 50)).size > 8, `${id}: the number does not count`);  // 0.4 s .. 1.7 s: counting ("2,5" has ~25 states)
  }
});
