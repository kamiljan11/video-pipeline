// node --test gfx/test/*.test.mjs   (scene_check.mjs: pieces of a scene that cover each other while both are on screen)
import test from 'node:test';
import assert from 'node:assert/strict';
import { clashes, window_ } from '../scene_check.mjs';

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
