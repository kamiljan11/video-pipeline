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
