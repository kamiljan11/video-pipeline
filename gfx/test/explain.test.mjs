// explainer pieces, "set", "look": "paper" and "cam": "grow" (style/REF-shorts-arjay.md, 2026-11-16)
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkScene, codeHtml, frameStops, scene, sceneFit, camKeyframes, soloKeys } from '../scene_lib.mjs';
import { attached, place } from '../anchor_lib.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const icon = n => `<svg data-i="${n}"></svg>`;
const sc = (els, more = {}) => ({ id: 'x', type: 'scene', dur: 10, els, ...more });
const table = { k: 'table', id: 't', x: 0, y: 0, title: 'products', cols: ['id', 'description', 'version'],
  rows: [['41', 'Red kettle', '3'], ['42', 'Blue mug', '5']], at: 0.5, state: [[3, 1, 'bad'], [5, 1, 'off']], set_cell: [[4, 1, 2, '6']] };

test('a scene without the new keys has none of the new CSS (finished films draw byte for byte as before)', () => {
  const h = scene(sc([{ k: 'chip', x: 0, y: 0, text: 'a' }]), esc, icon);
  assert.ok(!h.includes('.scene .sw{') && !h.includes('.scene.paper{') && !h.includes('data-growz'));
});

test('table: real rows come in one by one, a row lights up and goes back, a cell changes its value with a flash', () => {
  assert.deepEqual(checkScene(sc([table])), []);
  const h = scene(sc([table]), esc, icon);
  assert.ok(h.includes('.scene .trw{'), 'explainer CSS in');
  assert.equal((h.match(/class="trw td"/g) || []).length, 2);
  assert.match(h, /class="tst bad" style="animation:scfade \.25s [^"]* 3\.00s both,scfadeout \.2s 5\.00s forwards"/);
  assert.ok(!h.includes('tst off'), '"off" ends the light, it draws nothing');
  assert.match(h, /<i class="swf" style="animation:scflash \.9s [^"]* 4\.00s both"><\/i><span class="swv" style="animation:scswin \.32s [^"]* 4\.00s both">6<\/span>/);
  assert.match(h, /<span class="swv" style="animation:scfadeout \.3s ease-in 4\.00s forwards">5<\/span>/);
});

test('table: bad rows, cells and states are named', () => {
  const bad = checkScene(sc([{ ...table, rows: [['1', '2']], state: [[3, 5, 'red']], set_cell: [[4, 0, 9, 'x']] }]));
  assert.ok(bad.some(b => b.includes('"rows"')));
  assert.ok(bad.some(b => b.includes('"state"')));
  assert.ok(bad.some(b => b.includes('"set_cell"')));
  const flat = checkScene(sc([{ ...table, state: [5], set_cell: ['x'] }]));  // a named problem, not a TypeError
  assert.ok(flat.some(b => b.includes('"state" entries are lists')) && flat.some(b => b.includes('"set_cell" entries are lists')));
});

test('code: lines type at 1ch per character, keywords coloured, a mark grows under the phrase it names', () => {
  const code = { k: 'code', x: 0, y: 0, lang: 'sql', lines: ['UPDATE products', "WHERE id = 42 AND version = 5;"], at: 1, mark: [[6, 1, 'AND version = 5']] };
  assert.deepEqual(checkScene(sc([code])), []);
  const h = scene(sc([code]), esc, icon);
  assert.match(h, /--n:15;animation:sctype 0\.38s steps\(15\) 1\.30s both/);
  assert.match(h, /<i class="cdm" style="left:14ch;width:15ch;animation:scgrow \.35s [^"]* 6\.00s both"><\/i>/);
  assert.ok(checkScene(sc([{ ...code, mark: [[6, 1, 'nope']] }])).some(b => b.includes('"nope" is not on line 1')));
});

test('codeHtml: keywords, strings, numbers and comments, everything escaped', () => {
  assert.equal(codeHtml("SELECT 'a<b' -- x", 'sql', esc), '<span class="ck">SELECT</span> <span class="cs">\'a&lt;b\'</span> <span class="cc">-- x</span>');
  assert.equal(codeHtml('x = 3 # hi', 'sh', esc), 'x = <span class="cn">3</span> <span class="cc"># hi</span>');
  assert.equal(codeHtml('a // b', 'sql', esc), 'a // b', 'a // is not a SQL comment');
});

test('set: a chip, text, big number or stat changes on the word; not before it came in, not with count', () => {
  for (const e of [{ k: 'chip', text: 'v5' }, { k: 'text', t: 'v5' }, { k: 'big', t: '5' }, { k: 'stat', value: '5', label: 'v' }]) {
    const p = { ...e, x: 0, y: 0, at: 1, set: [[3, '6']] };
    assert.deepEqual(checkScene(sc([p])), [], e.k);
    assert.match(scene(sc([p]), esc, icon), /scswin \.32s [^"]* 3\.00s both">6</, e.k);
    assert.ok(checkScene(sc([{ ...p, set: [[0.5, '6']] }])).length, `${e.k}: a value set before the piece came in`);
  }
  assert.ok(checkScene(sc([{ k: 'node', x: 0, y: 0, set: [[3, 'a']] }])).some(b => b.includes('"set" only on')));
  assert.ok(checkScene(sc([{ k: 'stat', x: 0, y: 0, label: 'a', count: { to: 9 }, set: [[3, 'a']] }])).some(b => b.includes('use one')));
});

test('tag: a callout with its leader line inside its own box (one DOM piece per spec piece)', () => {
  const h = scene(sc([{ k: 'tag', id: 'sam', x: 100, y: 500, text: 'Sam: "350 ml"', tone: 'blue', to: [400, 200], at: 2 }]), esc, icon);
  assert.equal((h.match(/class="p /g) || []).length, 1);
  assert.match(h, /<div class="p tag" data-id="sam" data-at="2\.00" style="left:100px;top:500px"><svg class="tagl"/);
  assert.match(h, /style="left:-100px;top:-500px/);
  assert.ok(checkScene(sc([{ k: 'tag', x: 0, y: 0, text: '' }])).some(b => b.includes('"text"')));
});

test('tag attached to a piece: the leader line ends at that box edge, facing the tag', () => {
  const e = { k: 'tag', x: 0, y: 400, text: 'a', to: 'row' };
  assert.ok(attached(e));
  const out = place(e, { row: { x: 100, y: 100, w: 200, h: 50 } }, { x: 0, y: 400, w: 100, h: 60 });
  assert.equal(out._to, 'row');
  assert.ok(out.to[1] >= 150 && out.to[1] <= 160, `ends under the row: ${out.to}`);
});

test('look paper: a class and its CSS; text drawn in ink, not white', () => {
  const h = scene(sc([{ k: 'text', x: 0, y: 0, t: 'a' }], { look: 'paper' }), esc, icon);
  assert.ok(h.includes('class="scene paper"') && h.includes('.scene.paper{'));
  assert.ok(h.includes('color:#16181d'));
  assert.ok(checkScene(sc([{ k: 'text', x: 0, y: 0, t: 'a' }], { look: 'neon' })).some(b => b.includes('"look"')));
});

test('cam grow: one stop per entrance group, each framing only what is on screen, the first piece filling the area', () => {
  const pieces = [{ id: 'a', x: 0, y: 0, w: 400, h: 200, at: 0.5 }, { id: 'b', x: 0, y: 400, w: 400, h: 200, at: 3 },
    { id: 'c', x: 0, y: 800, w: 400, h: 200, at: 3.3 }, { id: 'l', x: 0, y: 0, w: 10, h: 900, ln: true }, { id: 'd', x: 600, y: 0, w: 400, h: 200, at: 6, gone: 8 }];
  const safe = { x: 0, y: 0, w: 1000, h: 1000 };
  const st = frameStops(pieces, safe, null).grow(10, 1.5);
  assert.deepEqual(st.map(s => s.t), [0, 3.05, 6.05, 8.05]);
  assert.deepEqual(st.map(s => s.keep), [[0], [0, 1, 2], [0, 1, 2, 4], [0, 1, 2]]);
  assert.equal(st[0].z, 1.5, 'one piece alone: capped at grow_zmax');
  assert.ok(st[1].z < st[0].z, 'the framing widens as pieces come in');
  assert.ok(st[1].move <= 0.55 && st[1].move >= 0.2);
  assert.ok(camKeyframes(st, 10).includes('scale(1.5)'));
});

test('cam grow: checked and drawn', () => {
  const els = [{ k: 'chip', id: 'a', x: 0, y: 0, text: 'a', at: 0.5 }];
  assert.deepEqual(checkScene(sc(els, { cam: 'grow' })), []);
  assert.match(scene(sc(els, { cam: 'grow', grow_zmax: 1.2 }), esc, icon), /data-cam="&quot;grow&quot;" data-dur="10" data-growz="1\.2"/);
  assert.ok(checkScene(sc(els, { cam: 'grow', canvas_zoom: [{ t: 1, on: 'a' }] })).some(b => b.includes('"cam": "grow"')));
  assert.ok(checkScene(sc(els, { cam: 'grow', layout: 'side' })).some(b => b.includes('layout "side"')));
  assert.ok(checkScene(sc(els, { grow_zmax: 9 })).some(b => b.includes('"grow_zmax"')));
});

test('cam grow in the page: sceneFit builds the stops from the measured pieces', () => {
  const kids = [{ dataset: { id: 'a', at: '0.5' }, offsetLeft: 0, offsetTop: 0, offsetWidth: 400, offsetHeight: 200, querySelectorAll: () => [] },
    { dataset: { id: 'b', at: '3' }, offsetLeft: 0, offsetTop: 400, offsetWidth: 400, offsetHeight: 200, querySelectorAll: () => [] }];
  const style = {};
  const world = { dataset: { cam: '"grow"', dur: '10', growz: '1.5' }, querySelectorAll: () => kids, style, parentElement: null };
  const head = { appendChild() {} };
  global.document = { querySelector: () => world, createElement: () => ({}), head };
  try {
    const stops = sceneFit({ x: 0, y: 0, w: 1000, h: 1000 }, camKeyframes.toString(), soloKeys.toString(), null, null, frameStops.toString());
    assert.deepEqual(stops.map(s => s.t), [0, 3.05]);
    assert.match(style.animation, /^cam_fit 10s linear both$/);
  } finally { delete global.document; }
});
