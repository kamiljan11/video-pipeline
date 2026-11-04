// node --test gfx/test/*.test.mjs   (thumbs.mjs: A/B thumbnails for the long and covers for shorts, from thumbs.json)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { checkThumbs, longHtml, shortHtml } from '../thumbs.mjs';

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
