// round 2 pieces: the thought drawn, not written (style/REF-shorts-arjay.md › Gramatyka obrazu, 2026-11-16)
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkScene, resolveExtends, scene, shiftPiece } from '../scene_lib.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const icon = n => `<svg data-i="${n}"></svg>`;
const sc = (els, more = {}) => ({ id: 'x', type: 'scene', dur: 10, els, ...more });
const flow = { k: 'flow', id: 'f', x: 0, y: 0, at: 0.2, steps: [{ text: 'Server', icon: 'server' }, { text: 'db' }, { text: 'queue' }],
  packet: [[1.3, 0]], fail: [[2, 2]], lit: [[2.8, 1]] };

test('flow: numbered steps come in one by one, an arrow before each, a dot runs, a broken arrow, a lit step', () => {
  assert.deepEqual(checkScene(sc([flow])), []);
  const h = scene(sc([flow]), esc, icon);
  assert.equal((h.match(/class="fst"/g) || []).length, 3);
  assert.equal((h.match(/class="fc"/g) || []).length, 2, 'an arrow between each pair, none before the first');
  assert.match(h, /<span class="fsn">3<\/span>/);
  assert.match(h, /class="fcp" style="animation:scrun 0?\.60s [^"]* 1\.30s both"/);
  assert.match(h, /class="fcx" style="animation:scpop [^"]* 2\.00s both"/);
  assert.match(h, /class="fsl" style="animation:scfade \.25s [^"]* 2\.80s both"/);
  const v = scene(sc([{ ...flow, dir: 'col', num: false }]), esc, icon);
  assert.ok(v.includes('class="bd col"') && v.includes('scrunv') && !v.includes('class="fsn"'));
});

test('flow: a step out of range, a broken arrow into step 0, one step only are named', () => {
  const bad = checkScene(sc([{ ...flow, lit: [[1, 3]], fail: [[1, 0]], packet: [[1, 2]] }, { k: 'flow', x: 0, y: 0, steps: [{ text: 'a' }] }]));
  assert.ok(bad.some(b => b.includes('"lit"')) && bad.some(b => b.includes('step 0 has no arrow in')) && bad.some(b => b.includes('"packet"')));
  assert.ok(bad.some(b => b.includes('one step is a chip')));
});

test('grid: one tile per thing, tiles show in steps and fill in groups of a colour', () => {
  const g = { k: 'grid', id: 'g', x: 0, y: 0, at: 0.5, n: 48, cols: 12, show: [[1, 16], [2, 48]], fill: [[3, 46, 'ok'], [4, 2, 'bad']] };
  assert.deepEqual(checkScene(sc([g])), []);
  const h = scene(sc([g]), esc, icon);
  assert.equal((h.match(/class="gc"/g) || []).length, 48);
  assert.equal((h.match(/<b style="background:#3ecf8e/g) || []).length, 46);
  assert.equal((h.match(/<b style="background:#ff5f57/g) || []).length, 2);
  assert.match(h, /grid-template-columns:repeat\(12,40px\)/);
  const bad = checkScene(sc([{ ...g, n: 500, show: [[2, 16], [1, 8]], fill: [[3, 60]] }]));
  assert.ok(bad.some(b => b.includes('"n"')) && bad.some(b => b.includes('"show"')));
  assert.ok(checkScene(sc([{ ...g, fill: [[3, 60]] }])).some(b => b.includes('"fill"')), 'more tiles filled than there are');
});

test('bars: a bar grows to its share, two dots on a track for before -> after, a lit row', () => {
  const b = { k: 'bars', id: 'b', x: 0, y: 0, at: 0, items: [{ label: 'All', v: 0.57, text: '57%' }, { label: 'asked', v: 0.61, b: 0.1, text: '61 -> 10' }], lit: [[4, 0]] };
  assert.deepEqual(checkScene(sc([b])), []);
  const h = scene(sc([b]), esc, icon);
  assert.match(h, /class="brf" style="width:57\.0%/);
  assert.equal((h.match(/class="bro/g) || []).length, 2);
  assert.match(h, /class="brd" style="left:10\.0%;width:calc\(61\.0% - 10\.0%\)[^"]*transform-origin:right/);
  assert.ok(checkScene(sc([{ ...b, items: [{ label: 'a', v: 2 }] }])).some(x => x.includes('"items"')));
  assert.ok(checkScene(sc([{ ...b, items: [{ label: 'a', v: 0.5, b: 0.2, b_at: 999 }] }])).some(x => x.includes('"items"')));  // b_at in the scene
  assert.ok(checkScene(sc([{ k: 'code', x: 0, y: 0, lines: ['x'], type_at: 999 }])).some(x => x.includes('"type_at"')));
});

test('timeline: ticks, lanes with segments, a now-line gliding between places; narrow = names above the tracks', () => {
  const t = { k: 'timeline', id: 't', x: 0, y: 0, at: 0, ticks: ['open', 'edit', 'save'], lanes: [{ label: 'Pess', segs: [{ from: 0, to: 1, text: 'locked' }] }], head: [[1, 0], [3, 1]] };
  assert.deepEqual(checkScene(sc([t])), []);
  const h = scene(sc([t]), esc, icon);
  assert.equal((h.match(/class="tlk"/g) || []).length, 3);
  assert.match(h, /@keyframes th_u\w+_1\{from\{left:calc\(var\(--pl\) \+ \(100% - var\(--pl\)\) \* 0\)\}to\{left:calc\(var\(--pl\) \+ \(100% - var\(--pl\)\) \* 1\)\}\}/);
  assert.ok(!h.includes('class="tlx top"'));
  assert.ok(scene(sc([{ ...t, w: 1100 }]), esc, icon).includes('class="tlx top"'));
  assert.ok(checkScene(sc([{ ...t, head: [[1, 0], [1.2, 1]] }])).some(x => x.includes('"head"')), 'a glide needs its 0.6 s');
});

test('quiz: options lettered, the one people pick lit, then the right one green and the rest dimmed', () => {
  const q = { k: 'quiz', id: 'q', x: 0, y: 0, at: 0, q: 'Fix?', opts: ['lock', 'version', 'queue'], pick: [[2, 0]], reveal: { at: 4, right: 1, pct: ['10%', '24%', '66%'] } };
  assert.deepEqual(checkScene(sc([q])), []);
  const h = scene(sc([q]), esc, icon);
  assert.equal((h.match(/class="qo"/g) || []).length, 3);
  assert.equal((h.match(/scdim \.4s ease-out 4\.00s forwards/g) || []).length, 2);
  assert.match(h, /class="tst ok" style="animation:scfade \.25s 4\.00s both"/);
  assert.ok(checkScene(sc([{ ...q, reveal: { at: 4, right: 5 } }])).some(x => x.includes('"reveal"')));
});

test('form: a card with fields whose value changes on the word, a button pressed, a note landing', () => {
  const f = { k: 'form', id: 'pr', x: 0, y: 0, at: 0.5, title: 'Product #42', fields: [{ label: 'version', value: '5', set: [[3, '6']] }],
    button: { text: 'Save', press_at: 2 }, note: { text: 'saved', at: 3.2 } };
  assert.deepEqual(checkScene(sc([f])), []);
  const h = scene(sc([f]), esc, icon);
  assert.match(h, /class="swv" style="animation:scswin \.32s [^"]* 3\.00s both">6<\/span>/);
  assert.match(h, /class="ffb"[^>]*scpulse \.45s [^"]* 2\.00s/);
  assert.match(h, /class="ffn"[^>]*scpop \.3s [^"]* 3\.20s both/);
  const bad = checkScene(sc([{ ...f, title: '', fields: [{ label: 'v', value: '5', set: [[0.2, '6']] }] }]));
  assert.ok(bad.some(x => x.includes('"title"')) && bad.some(x => x.includes('"fields"')), 'a value cannot change before the card is in');
});

test('extends: every time inside a round 2 piece moves back with the piece', () => {
  const s = shiftPiece({ ...flow, at: 1 }, -10);
  assert.deepEqual([s.at, s.packet[0][0], s.fail[0][0], s.lit[0][0]], [-9, -8.7, -8, -7.2]);
  const f = shiftPiece({ k: 'form', at: 1, title: 'a', fields: [{ label: 'v', value: '5', set: [[3, '6']] }], button: { text: 'b', press_at: 2 }, note: { text: 'n', at: 4 } }, -10);
  assert.deepEqual([f.fields[0].set[0][0], f.button.press_at, f.note.at], [-7, -8, -6]);
  const t = shiftPiece({ k: 'timeline', at: 1, lanes: [{ label: 'a', segs: [{ from: 0, to: 1, at: 2 }] }], head: [[3, 0.5]] }, -10);
  assert.deepEqual([t.lanes[0].segs[0].at, t.head[0][0]], [-8, -7]);
  const b = shiftPiece({ k: 'bars', at: 1, items: [{ label: 'a', v: 0.5, b: 0.2, at: 2, b_at: 3 }] }, -10);
  assert.deepEqual([b.items[0].at, b.items[0].b_at], [-8, -7]);
});

test('extends: round 1 times move too and a table keeps its rows as lists (pg-review 2026-11-16 code-1, code-2)', () => {
  const tb = shiftPiece({ k: 'table', at: 1, cols: ['a'], rows: [['x'], ['y']], state: [[3, 0, 'bad']], set_cell: [[4, 1, 0, 'z']] }, -10);
  assert.deepEqual(tb.rows, [['x'], ['y']]);
  assert.deepEqual([tb.state[0], tb.set_cell[0]], [[-7, 0, 'bad'], [-6, 1, 0, 'z']]);
  const cd = shiftPiece({ k: 'code', at: 1, lines: ['a b'], type_at: 1.5, mark: [[3, 0, 'b']] }, -10);
  assert.deepEqual([cd.type_at, cd.mark[0]], [-8.5, [-7, 0, 'b']]);
  assert.deepEqual(shiftPiece({ k: 'chip', at: 1, text: 'a', set: [[2, 'b']] }, -10).set, [[-8, 'b']]);
  const sp = { id: 'b', type: 'scene', dur: 6, extends: 'a', els: [{ k: 'chip', x: 0, y: 400, at: 0.5, text: 'c' }] };
  const [, ext] = resolveExtends([{ id: 'a', type: 'scene', dur: 5, els: [{ k: 'table', id: 't', x: 0, y: 0, at: 0.5, cols: ['a'], rows: [['x']], state: [[2, 0, 'hl']] }] }, sp]);
  assert.ok(scene(ext, esc, icon).includes('class="trw td"'), 'a scene that extends a table scene draws it');
});

test('a scene with only old pieces still gets none of the round 2 CSS', () => {
  const h = scene(sc([{ k: 'chip', x: 0, y: 0, text: 'a' }]), esc, icon);
  assert.ok(!h.includes('.scene .fst{') && !h.includes('@keyframes scrun'));
});
