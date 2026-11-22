// node --test gfx/test/*.test.mjs   (hand-drawn box / underline around a piece: gfx/rough_lib.mjs, docs/designs/2026-11-05-visual-upgrade.md item 3)
import test from 'node:test';
import assert from 'node:assert/strict';
import { annotation, autoShape, rng, roughBox, roughUnderline, seedOf } from '../rough_lib.mjs';
import { checkScene, scene } from '../scene_lib.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const icon = n => `<svg data-i="${n}"></svg>`;
const sc = els => ({ id: 's', type: 'scene', dur: 6, els });
const nums = d => (d.match(/-?\d+(\.\d+)?/g) || []).map(Number);

test('the same seed draws the same strokes; another seed draws other ones', () => {
  const a = rng(7), b = rng(7);
  assert.deepEqual([a(), a(), a()], [b(), b(), b()]);
  assert.equal(seedOf('md.1'), seedOf('md.1'));
  assert.notEqual(seedOf('md.1'), seedOf('md.2'));
  assert.deepEqual(roughBox(100, 200, 600, 60, 42), roughBox(100, 200, 600, 60, 42));
  assert.notDeepEqual(roughBox(100, 200, 600, 60, 42), roughBox(100, 200, 600, 60, 43));
});

test('a flat row gets a box, a squarish piece keeps the circle; "auto" picks the same', () => {
  assert.equal(autoShape(600, 60), 'box');
  assert.equal(autoShape(180, 60), 'box');  // exactly 3x
  assert.equal(autoShape(200, 200), 'circle');
  assert.equal(annotation('auto', 0, 0, 600, 60, 1).shape, 'box');
  assert.equal(annotation(undefined, 0, 0, 200, 200, 1).shape, 'circle');
  assert.equal(annotation('underline', 0, 0, 200, 200, 1).shape, 'underline');
});

test('two passes, each a closed run of four sides near the padded box; the wobble stays small', () => {
  const [p1, p2] = roughBox(100, 200, 600, 60, 9, 14, 6);
  for (const d of [p1, p2]) {
    assert.equal((d.match(/M/g) || []).length, 4, 'four strokes, one per side');
    const v = nums(d), xs = v.filter((_, i) => i % 2 === 0), ys = v.filter((_, i) => i % 2 === 1);
    assert.ok(Math.min(...xs) > 100 - 14 - 12 && Math.max(...xs) < 700 + 14 + 12, `x inside the box + wobble: ${Math.min(...xs)}..${Math.max(...xs)}`);
    assert.ok(Math.min(...ys) > 200 - 14 - 12 && Math.max(...ys) < 260 + 14 + 12, `y inside the box + wobble: ${Math.min(...ys)}..${Math.max(...ys)}`);
  }
  assert.notEqual(p1, p2, 'the second pass is not a copy of the first');
});

test('an underline sits under the box, about as wide as it', () => {
  const [a, b] = roughUnderline(100, 200, 400, 50, 3);
  for (const d of [a, b]) {
    const v = nums(d), xs = v.filter((_, i) => i % 2 === 0), ys = v.filter((_, i) => i % 2 === 1);
    assert.ok(Math.min(...ys) > 250, `below the text: ${Math.min(...ys)}`);
    assert.ok(Math.max(...ys) < 250 + 10 + 20, `close under it: ${Math.max(...ys)}`);
    assert.ok(Math.max(...xs) - Math.min(...xs) > 400 * 0.85, 'about as wide as the box');
  }
});

test('in a scene: a ring on a flat box draws two revealed strokes, a square one keeps one circle, the same spec draws the same', () => {
  const flat = sc([{ k: 'ring', id: 'r', x: 100, y: 200, w: 600, h: 60, at: 1 }]);
  assert.deepEqual(checkScene(flat), []);
  const h = scene(flat, esc, icon);
  assert.equal((h.match(/<path /g) || []).length, 2, 'two pen passes on a flat box');
  assert.match(h, /data-bb="86 186 628 88"/, 'the box it takes = the row + pad 14');
  assert.equal(h, scene(flat, esc, icon), 'deterministic: stills and the render match');
  const round = scene(sc([{ k: 'ring', x: 100, y: 200, w: 200, h: 200, at: 1 }]), esc, icon);
  assert.equal((round.match(/<path /g) || []).length, 1, 'a square box keeps one circle');
  assert.match(round, /stroke-dashoffset:1;opacity:0;/, 'the circle is hidden until drawn (note 49: no end showing before the pen)');
  const forced = scene(sc([{ k: 'ring', x: 100, y: 200, w: 600, h: 60, shape: 'circle', at: 1 }]), esc, icon);
  assert.equal((forced.match(/<path /g) || []).length, 1, '"shape": "circle" keeps one circle on a flat box');
  const under = scene(sc([{ k: 'ring', x: 100, y: 200, w: 600, h: 60, shape: 'underline', at: 1 }]), esc, icon);
  assert.match(under, /data-bb="100 260 600 18"/);
});

test('an unknown shape is named by checkScene', () => {
  const bad = checkScene(sc([{ k: 'ring', x: 100, y: 200, w: 600, h: 60, shape: 'star', at: 1 }]));
  assert.ok(bad.some(m => /"shape" = "circle", "box" or "underline", got "star"/.test(m)), bad.join('\n'));
});
