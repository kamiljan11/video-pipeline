// node --test gfx/test/*.test.mjs   (thumbs.mjs: A/B thumbnails for the long and covers for shorts, from thumbs.json)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { checkThumbs, fitProblems, longHtml, shortHtml } from '../thumbs.mjs';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-test-'));
fs.writeFileSync(path.join(dir, 'f.png'), '');
const v = (id, more = {}) => ({ id, frame: 'f.png', big: '92% → 18%', sub: 'błędów AI', ...more });

test('a good spec: two long variants and a cover', () => {
  assert.deepEqual(checkThumbs({ long: [v('A'), v('B', { side: 'right', icon: 'construction' })], shorts: [v('s1')] }, dir), []);
});

test('one variant, a long headline, a missing frame or icon, a bad id: each named', () => {
  const bad = checkThumbs({ long: [v('A b', { big: 'zdecydowanie za długi napis', frame: 'nope.png', icon: 'no-such-icon', side: 'up' })] }, dir);
  for (const want of ['at least 2 variants', '"id"', 'keep it <= 18', '"frame"', 'no lucide icon', '"side"'])
    assert.ok(bad.some(b => b.includes(want)), `missing: ${want}\n${bad.join('\n')}`);
  assert.ok(checkThumbs({ long: [v('A'), v('A')] }, dir).some(b => b.includes('twice')));
});

test('html: words escaped, side and frame position used, theme colours inlined', () => {
  const h = longHtml(v('A', { big: '<b>x', side: 'right', fx: -300, fy: -100 }), dir, 'cetus');
  assert.match(h, /&lt;b&gt;x/); assert.doesNotMatch(h, /<b>x/);
  assert.match(h, /right:60px/); assert.match(h, /background-position:-300px -100px/); assert.match(h, /--acc:#6FA7EC/);
  assert.match(shortHtml(v('s1', { dy: 150 }), dir, 'cetus'), /background-position:0 150px/);
});

test('fit: a headline wider than its column or words past the bottom are named, a fitting one passes', () => {
  assert.deepEqual(fitProblems('long_A.jpg', { wide: [['big', 640, 640], ['sub', 600, 640]], bottom: 700 }, 720), []);
  const bad = fitProblems('long_B.jpg', { wide: [['big', 860, 640]], bottom: 760 }, 720);
  assert.ok(bad.some(b => b.includes('"big" is 220 px wider')), bad.join('\n'));
  assert.ok(bad.some(b => b.includes('40 px past the bottom')), bad.join('\n'));
});

test('the feed: a word too small at 320 px, a word under the length in the corner, cover text outside the safe zone', () => {
  const box = (k, x0, y0, x1, y1, fs) => ({ k, x0, y0, x1, y1, fs });
  const fit = { wide: [], bottom: 600 };
  assert.deepEqual(fitProblems('long_A.jpg', { ...fit, boxes: [box('big', 60, 110, 700, 300, 150), box('tag', 60, 500, 400, 560, 48)] }, 720), []);
  const small = fitProblems('long_A.jpg', { ...fit, boxes: [box('tag', 60, 500, 400, 540, 30)] }, 720);
  assert.ok(small.some(b => b.includes('"tag" is 7.5 px at 320 px')), small.join('\n'));
  const corner = fitProblems('long_B.jpg', { ...fit, boxes: [box('sub', 580, 560, 1220, 690, 60)] }, 720);
  assert.ok(corner.some(b => b.includes('bottom-right 12%')), corner.join('\n'));
  assert.deepEqual(fitProblems('s1_cover.jpg', { ...fit, bottom: 700, boxes: [box('big', 60, 220, 1020, 400, 140)] }, 1920, 1080, true), []);
  const low = fitProblems('s1_cover.jpg', { ...fit, bottom: 1800, boxes: [box('sub', 60, 1700, 1020, 1800, 62)] }, 1920, 1080, true);
  assert.ok(low.some(b => b.includes('outside the cover\'s safe zone 220-1500')), low.join('\n'));
  assert.match(shortHtml(v('s1'), dir, 'cetus'), /top:220px/);
});

test('a run that stops on variant B leaves out as it was: no new A next to an old B', { skip: !fs.existsSync('/usr/bin/google-chrome') }, async () => {
  const { execFileSync, spawnSync } = await import('child_process');
  const w = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-run-')), out = path.join(w, 'out');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=gray:s=320x180', '-frames:v', '1', path.join(w, 'f.png')]);
  fs.mkdirSync(out); fs.writeFileSync(path.join(out, 'long_A.jpg'), 'old A'); fs.writeFileSync(path.join(out, 'long_B.jpg'), 'old B');
  fs.writeFileSync(path.join(w, 't.json'), JSON.stringify({ long: [v('A'), v('B', { sub: 'x'.repeat(90) })] }));
  const r = spawnSync('node', [new URL('../thumbs.mjs', import.meta.url).pathname, path.join(w, 't.json'), out], { encoding: 'utf8' });
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /long_B/);
  assert.equal(fs.readFileSync(path.join(out, 'long_A.jpg'), 'utf8'), 'old A');
  assert.deepEqual(fs.readdirSync(out).sort(), ['long_A.jpg', 'long_B.jpg']);  // no staging dir left behind
  fs.rmSync(w, { recursive: true, force: true });
});
