// node --test gfx/test/*.test.mjs   (scene_check.mjs: pieces of a scene that cover each other while both are on screen)
import test from 'node:test';
import assert from 'node:assert/strict';
import { clashes, drawProblems, window_ } from '../scene_check.mjs';

const sp = els => ({ id: 'sc', dur: 10, els });

test('two labels on top of each other while both are on screen: named with their texts', () => {
  const s = sp([{ k: 'node', id: 'a', text: 'zanim AI wykona polecenie', at: 1 }, { k: 'node', id: 'b', text: 'po zmianie', at: 2 }]);
  const out = clashes(s, [{ i: 0, x: 0, y: 0, w: 600, h: 200 }, { i: 1, x: 500, y: 0, w: 600, h: 200 }]);
  assert.equal(out.length, 1); assert.match(out[0], /sc: a \(node "zanim AI wykona poleceni"\) covers b \(node "po zmianie"\) \(100x200 px\)/);
});

test('no clash: apart, never on screen together, a stamp or ring on purpose, a sliver of overlap', () => {
  const r = [{ i: 0, x: 0, y: 0, w: 400, h: 100 }, { i: 1, x: 300, y: 0, w: 400, h: 100 }];
  assert.deepEqual(clashes(sp([{ k: 'chip', at: 0 }, { k: 'chip', at: 0 }]), [r[0], { ...r[1], x: 500 }]), []);
  assert.deepEqual(clashes(sp([{ k: 'chip', at: 0, gone: 2 }, { k: 'chip', at: 3 }]), r), []);
  assert.deepEqual(clashes(sp([{ k: 'file', at: 0 }, { k: 'stamp', at: 1 }]), r), []);
  assert.deepEqual(clashes(sp([{ k: 'chip', at: 0 }, { k: 'chip', at: 0 }]), [r[0], { ...r[1], x: 395 }]), []);
});

test('on-screen window: first moment (at, said words, messages) to gone or the end', () => {
  assert.deepEqual(window_({ words: [['a', 2], ['b', 1.5]] }, 8), [1.5, 8]);
  assert.deepEqual(window_({ msgs: [{ at: 3 }], gone: 5 }, 8), [3, 5]);
  assert.deepEqual(window_({}, 8), [0, 8]);
});

test('two chips with words overlapping a little still clash (Kamil 2026-11-05: "nałożyły się na siebie elementy")', () => {
  // s06_ksiazka: "drugi sprawdza" ran 40 px under "trzeci pilnuje wdrożenia", 7 % of the smaller box, under the share rule
  const s = sp([{ k: 'chip', id: 'b', text: 'drugi sprawdza', at: 0 }, { k: 'chip', id: 'c', text: 'trzeci pilnuje wdrożenia', at: 0 }]);
  const out = clashes(s, [{ i: 0, x: 580, y: 780, w: 540, h: 102 }, { i: 1, x: 1080, y: 780, w: 760, h: 102 }]);
  assert.equal(out.length, 1); assert.match(out[0], /b \(chip "drugi sprawdza"\) covers c/);
});

test('a stamp on another piece\'s words clashes; a stamp on its card does not (2026-11-08 s22, s28)', () => {
  const s = { id: 'x', dur: 6, els: [{ k: 'text', t: 'bez czerwonego okienka', at: 0 }, { k: 'stamp', text: 'BLOKOWANE', at: 2 }] };
  const out = clashes(s, [{ i: 0, x: 0, y: 300, w: 700, h: 40 }, { i: 1, x: 640, y: 250, w: 520, h: 110 }]);
  assert.equal(out.length, 1); assert.match(out[0], /a stamp on words/);
  const onCard = { id: 'y', dur: 6, els: [{ k: 'file', at: 0 }, { k: 'stamp', at: 2 }] };
  assert.deepEqual(clashes(onCard, [{ i: 0, x: 0, y: 0, w: 700, h: 300 }, { i: 1, x: 100, y: 100, w: 400, h: 100 }]), []);
});

test('ring: holds a whole line of words or stays off it; a ring around nothing is named (Kamil 2026-11-08 s28)', () => {
  const sp = { id: 'r', dur: 6, els: [{ k: 'file', id: 'diff', at: 0 }, { k: 'ring', x: 980, y: 210, w: 820, h: 80, at: 2 }] };
  const rects = [{ i: 0, x: 980, y: 140, w: 820, h: 254 }];
  const texts = [{ i: 0, x: 1058, y: 160, w: 411, h: 44 }, { i: 0, x: 1012, y: 260, w: 324, h: 57 }];
  const bad = drawProblems(sp, rects, texts);
  assert.ok(bad.some(b => /cuts the words of diff/.test(b))); assert.ok(bad.some(b => /circles nothing/.test(b)));
  assert.deepEqual(drawProblems({ ...sp, els: [sp.els[0], { k: 'ring', x: 994, y: 246, w: 356, h: 86, at: 2 }] }, rects, texts), []);
});

test('line: each end on a piece (<= 40 px); a "free" line (road, time axis) is not measured', () => {
  const sp = { id: 'l', dur: 6, els: [{ k: 'node', at: 0 }, { k: 'line', from: [1610, 455], to: [1760, 455], at: 1 }, { k: 'chip', at: 0 }] };
  const rects = [{ i: 0, x: 1320, y: 360, w: 213, h: 270 }, { i: 2, x: 1790, y: 418, w: 328, h: 106 }];
  const bad = drawProblems(sp, rects, []);
  assert.equal(bad.length, 1); assert.match(bad[0], /"from" 1610,455 ends 77 px/);
  assert.deepEqual(drawProblems({ ...sp, els: [sp.els[0], { ...sp.els[1], from: [1530, 455] }, sp.els[2]] }, rects, []), []);
  assert.deepEqual(drawProblems({ ...sp, els: [sp.els[0], { ...sp.els[1], free: true }, sp.els[2]] }, rects, []), []);
});
