// node --test gfx/test/*.test.mjs   (research ledger L16b read_along, L17 canvas_zoom, S11 list items / extends / count "from",
// S14 camera stops; all opt-in: a spec without the keys draws byte for byte as before, motion.test.mjs keeps that golden)
import test from 'node:test';
import assert from 'node:assert/strict';
import { CANVAS_ZOOM, ITEM_HOLD, camKeyframes, checkScene, frameStops, resolveExtends, scene, sceneFit, shiftPiece, soloKeys, zoomStops } from '../scene_lib.mjs';
import { countFrom } from '../count_lib.mjs';
import { markTimes, motion } from '../webshot_lib.mjs';
import { ALL } from './motion_fixture.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const icon = n => `<svg data-i="${n}"></svg>`;
const ok = (els, more = {}) => ({ id: 's1', type: 'scene', dur: 8, els, ...more });
const term = (more = {}) => ({ k: 'term', id: 't', x: 0, y: 0, w: 1400, cmd: 'cat plan.md', out: ['a', 'b', 'c'], ...more });

// every delay of every inline animation list in the html ("name dur [curve] delay ..."; commas inside curves kept)
const delays = h => [...h.matchAll(/animation:([^";]+)/g)].flatMap(([, list]) => list.split(/,(?![^(]*\))/)
  .map(one => one.trim().split(/\s+(?![^(]*\))/).filter(t => /^-?[\d.]+s$/.test(t)).map(parseFloat))
  .filter(ts => ts.length > 1).map(ts => ts[1]));

test('L16b read_along: a terminal line and a window row light up when said and go dark on the next one', () => {
  const sp = ok([term({ read_along: [[2, 0], [3.5, 2]] }), { k: 'win', id: 'w', x: 0, y: 600, rows: ['x', { t: 'y', mark: 'ok' }, '~60'], read_along: [[5, 1]] }]);
  assert.deepEqual(checkScene(sp), []);
  const h = scene(sp, esc, icon);
  assert.match(h, /class="rhl rd" style="[^"]*scgrow 0\.2s cubic-bezier\(\.16,1,\.3,1\) 2\.00s both,scfadeout 0\.2s [^ ]+ 3\.50s forwards/);
  assert.match(h, /class="rhl rd" style="[^"]*scgrow 0\.2s [^ ]+ 3\.50s both"/);  // the last one stays lit
  assert.match(h, /<div class="row"><span class="rhl rd"[^>]*5\.00s both"><\/span><span class="rt">y<\/span><span class="mk ok"/);  // an object row
  assert.equal((h.match(/class="rhl rd"/g) || []).length, 3);
  assert.doesNotMatch(scene(ok([term()]), esc, icon), /class="rhl rd"/);
});

test('L16b read_along: a bad step is named', () => {
  for (const [e, want] of [[term({ read_along: [[2, 5]] }), 'line 0..2'], [term({ read_along: [[3, 0], [2, 1]] }), 'forward in time'],
    [term({ read_along: [[9, 0]] }), 'said inside'], [{ k: 'chip', x: 0, y: 0, read_along: [[1, 0]] }, 'only on a term'],
    [{ k: 'file', x: 0, y: 0, rows: ['a', '~60'], read_along: [[1, 1]] }, 'placeholder line'], [{ k: 'win', x: 0, y: 0, read_along: [[1, 0]] }, 'placeholder line']])
    assert.ok(checkScene(ok([e])).some(b => b.includes(want)), `${want}: ${checkScene(ok([e])).join('; ')}`);
});

test('L16b web card: quote lines marked at their spoken times, the default stays 0.25 s apart', () => {
  const mo = motion({ rects: [[0, 3000, 100, 20], [0, 3030, 100, 20]], height: 6000 }, 760, 9);
  assert.deepEqual(markTimes(mo, 3, undefined, 9), [0, 1, 2].map(i => mo.mark + i * 0.25));
  assert.deepEqual(markTimes(mo, 3, [4, 5.5], 9), [4, 5.5, 5.75]);
  for (const bad of [[1], [5, 4], [4, 5, 6, 6.5], [7.9], 'x'])
    assert.throws(() => markTimes(mo, 3, bad, 9), /"read_along"/, JSON.stringify(bad));
});

test('L17 canvas_zoom: one more camera stop, 1.25 times closer onto the piece, its centre stays put on screen', () => {
  const base = [{ t: 0, x: 100, y: 50, z: 1.2 }, { t: 6, x: 0, y: 0, z: 1, move: 0.9 }];
  const st = zoomStops(base, [{ t: 2, d: CANVAS_ZOOM.d, k: CANVAS_ZOOM.k, cx: 700, cy: 450 }]);
  assert.equal(st.length, 3);
  assert.deepEqual([st[1].t, st[1].move, st[1].zoom], [2.4, 0.4, true]);
  assert.ok(Math.abs(st[1].z - 1.5) < 1e-9);
  const screen = (s, p) => [(p[0] - s.x) * s.z, (p[1] - s.y) * s.z];
  screen(st[1], [700, 450]).forEach((v, i) => assert.ok(Math.abs(v - screen(base[0], [700, 450])[i]) < 1e-9));
  // keyframes: hold until 2 s, zoom in by 2.4 s, hold until the next stop's move (5.1 s)
  const pct = [...camKeyframes(st, 8).matchAll(/([\d.]+)%\{/g)].map(m => +m[1]);
  assert.deepEqual(pct, [0, 25, 30, 63.75, 75, 100]);
});

test('L17 canvas_zoom: sceneFit measures the piece and adds the stop (render.mjs passes the zoomStops source)', () => {
  const sp = ok([{ k: 'chip', id: 'a', x: 100, y: 100, text: 'x' }, { k: 'chip', id: 'b', x: 1500, y: 900, text: 'y' }],
    { canvas_zoom: [{ t: 3, on: 'b' }] });
  assert.deepEqual(checkScene(sp), []);
  const h = scene(sp, esc, icon);
  const zoom = /data-zoom="([^"]+)"/.exec(h)[1].replace(/&quot;/g, '"');
  assert.deepEqual(JSON.parse(zoom), [{ t: 3, on: 'b', k: 1.25, d: 0.4 }]);
  const el = (id, x, y) => ({ dataset: { id }, offsetLeft: x, offsetTop: y, offsetWidth: 200, offsetHeight: 100, classList: { contains: () => true }, style: {} });
  const world = { dataset: { cam: JSON.stringify([{ t: 0, on: '*' }]), dur: '8', zoom }, querySelectorAll: () => [el('a', 100, 100), el('b', 1500, 900)], style: {} };
  const head = [];
  globalThis.document = { querySelector: () => world, createElement: () => ({ textContent: '' }), head: { appendChild: s => head.push(s) } };
  try {
    const safe = { x: 110, y: 100, w: 1800, h: 1240 };
    const stops = sceneFit(safe, camKeyframes.toString(), null, zoomStops.toString(), null, frameStops.toString());
    assert.equal(stops.length, 2);
    assert.equal(stops[1].t, 3.4);
    const c = [1600, 950], s0 = stops[0], s1 = stops[1];  // centre of "b"
    assert.ok(Math.abs((c[0] - s1.x) * s1.z - (c[0] - s0.x) * s0.z) < 1e-6 && Math.abs(s1.z / s0.z - 1.25) < 1e-9);
    assert.match(head[0].textContent, /^@keyframes cam_fit\{/);
    assert.throws(() => sceneFit(safe, camKeyframes.toString(), null, null, null, frameStops.toString()), /zoomStops/);  // a zoom never silently dropped
  } finally { delete globalThis.document; }
});

test('L17 canvas_zoom: no camera, unknown piece, a zoom inside a camera move or past the end are named', () => {
  const els = [{ k: 'chip', id: 'a', x: 0, y: 0, text: 'x' }];
  for (const [more, want] of [[{ cam: 'none', canvas_zoom: [{ t: 1, on: 'a' }] }, '"cam": "none"'],
    [{ canvas_zoom: [{ t: 1, on: 'zz' }] }, 'no piece has that "id"'], [{ canvas_zoom: [{ t: 7.8, on: 'a' }] }, 'ends inside the card'],
    [{ cam: [{ t: 0, on: 'a' }, { t: 4, on: '*' }], canvas_zoom: [{ t: 2.9, on: 'a' }] }, 'camera move to cam[1]'],
    [{ canvas_zoom: [{ t: 1, on: 'a', k: 3 }] }, '"k"'], [{ canvas_zoom: [{ t: 2, on: 'a' }, { t: 2.1, on: 'a' }] }, 'forward in time'],
    [{ canvas_zoom: [{ t: 1 }] }, '"on" = the piece']])
    assert.ok(checkScene(ok(els, more)).some(b => b.includes(want)), `${want}: ${checkScene(ok(els, more)).join('; ')}`);
  assert.deepEqual(checkScene(ok(els, { cam: [{ t: 0, on: 'a' }, { t: 4, on: '*' }], canvas_zoom: [{ t: 1, on: 'a' }, { t: 4, on: '*' }] })), []);
});

test(`S11 list items: a piece with "item" must stay ${ITEM_HOLD} s`, () => {
  const it = (more) => ok([{ k: 'chip', id: 'a', x: 0, y: 0, text: '1. plan', item: 1, at: 1, ...more }]);
  assert.deepEqual(checkScene(it({})), []);
  assert.deepEqual(checkScene(it({ gone: 4 })), []);
  for (const [more, want] of [[{ gone: 3.5 }, 'on 2.50 s'], [{ out_at: 2 }, 'needs 3 s'], [{ at: 6 }, 'on 2.00 s'], [{ item: 0 }, '"item" = its number']])
    assert.ok(checkScene(it(more)).some(b => b.includes(want)), `${want}: ${checkScene(it(more)).join('; ')}`);
});

test('S11 extends: the next scene starts with the pieces still on, already finished; gone ones stay gone', () => {
  const a = { ...ALL, id: 'a' }, b = ok([{ k: 'chip', id: 'new', x: 1400, y: 600, text: 'nowy', at: 1.23 }], { id: 'b', extends: 'a', cam: [{ t: 0, on: 'p' }] });
  const c = ok([{ k: 'chip', id: 'c3', x: 0, y: 1200, text: 'trzeci', at: 0.5 }], { id: 'c', extends: 'b' });
  const [ra, rb, rc] = resolveExtends([a, b, c]);
  assert.equal(ra, a);  // no "extends": the same object, drawn as before
  const kept = ALL.els.filter(e => e.gone === undefined && e.out_at === undefined);
  assert.deepEqual(rb._held.map(e => e.k), kept.map(e => e.k));
  assert.equal(rc._held.length, kept.length + 1);
  assert.deepEqual(checkScene(rb), []);  // a camera stop may frame a kept piece ("p")
  const ds = delays(scene(rb, esc, icon));
  assert.deepEqual(ds.filter(d => d >= 0), [1.23], 'only the new piece animates: every kept animation lies before 0');
  assert.ok(ds.length > 20, `kept pieces drawn: ${ds.length} delays`);
  assert.ok(delays(scene(rc, esc, icon)).filter(d => d >= 0).every(d => d === 0.5));
  assert.throws(() => scene({ ...b }, esc, icon), /resolveExtends/);  // never drawn without its kept pieces
  assert.throws(() => resolveExtends([b]), /names "a", no scene/);
  assert.throws(() => resolveExtends([{ ...b, extends: 'c' }, { ...c, extends: 'b' }]), /circle/);
  assert.equal(shiftPiece({ k: 'say', x: 0, y: 0, words: [['a', 1]] }, -8).at, -7.05);
  // pieces that came in just before the end: their times derived from "at" (typing, chat messages, rows) are in the past too
  const late = { id: 'p', type: 'scene', dur: 5, els: [{ k: 'term', id: 't', x: 0, y: 0, at: 4.5, cmd: 'npm run build -- --verbose --watch', out: ['a', 'b'], hl: [1] },
    { k: 'chat', id: 'c', x: 900, y: 0, at: 4.8, msgs: Array.from({ length: 12 }, (_, i) => ({ who: i % 2 ? 'ai' : 'me', t: `m${i}` })) },
    { k: 'file', id: 'f', x: 0, y: 600, at: 4.9, rows: Array.from({ length: 20 }, () => ({ t: 'r', mark: 'ok', hl: true })), badge: { text: 'n' } },
    { k: 'toggle', id: 'g', x: 0, y: 900, at: 4.9 }, { k: 'stat', id: 's', x: 0, y: 1000, at: 4.9, count: { to: 9 } },
    { k: 'cursor', from: [0, 0], to: [99, 99], at: 4.9 }, { k: 'bar', x: 0, y: 1200, at: 4.95, v: 0.5 }] };
  const [, next] = resolveExtends([late, ok([{ k: 'chip', id: 'n', x: 1400, y: 0, text: 'n', at: 1 }], { id: 'n', extends: 'p' })]);
  assert.deepEqual(delays(scene(next, esc, icon)).filter(d => d >= 0), [1]);
});

test('S11 count card "from": one start for all numbers or one per number; none = 0 as before', () => {
  assert.deepEqual(countFrom({ id: 'c' }, 2), [0, 0]);
  assert.deepEqual(countFrom({ id: 'c', from: 3 }, 2), [3, 3]);
  assert.deepEqual(countFrom({ id: 'c', from: [3, 40] }, 2), [3, 40]);
  for (const from of [-1, [1], 'x', [1, NaN]]) assert.throws(() => countFrom({ id: 'c', from }, 2), /"c": count "from"/, JSON.stringify(from));
});

test('canvas_zoom is capped so its box (the piece + what is still being read) stays in view, and skipped below 1.03', () => {
  const base = [{ t: 0, x: 0, y: 0, z: 1 }], view = { x: 0, y: 0, w: 1000, h: 1000 };
  // box 400..600 around centre 500: room to 1000 = 500 / half 100 -> up to 5x, so the asked 1.25 stays
  const roomy = zoomStops(base, [{ t: 1, d: 0.4, k: 1.25, cx: 500, cy: 500, box: [400, 400, 600, 600], keep: [2] }], view);
  assert.ok(Math.abs(roomy[1].z - 1.25) < 1e-9);
  assert.deepEqual(roomy[1].keep, [2]);  // the stop carries what it frames, soloKeys never fades it
  // box 20..980: half 480, room 500 -> 500 / 480 x 0.97 = 1.01 < 1.03: no zoom at all rather than cut a word
  assert.equal(zoomStops(base, [{ t: 1, d: 0.4, k: 1.25, cx: 500, cy: 500, box: [20, 20, 980, 980] }], view).length, 1);
  // box 300..700: half 200 -> 500 / 200 x 0.97 = 2.43 > 1.25, and a 1.6 ask on box 250..750 -> 1.94; a wide box caps it
  const capped = zoomStops(base, [{ t: 1, d: 0.4, k: 1.6, cx: 500, cy: 500, box: [150, 150, 850, 850] }], view);
  assert.ok(Math.abs(capped[1].z - (500 / 350) * 0.97) < 1e-9);
});

test('soloKeys: a piece a stop frames ("keep") never fades, even when the fit test says it is outside', () => {
  const safe = { x: 0, y: 0, w: 500, h: 500 }, far = { x: 900, y: 0, w: 200, h: 100 };
  const stops = [{ t: 0, x: 0, y: 0, z: 1 }, { t: 3, x: 0, y: 0, z: 1, move: 0.9 }];
  assert.ok(soloKeys([far], stops, 5, safe)[0]);  // outside the safe area at both stops: hidden
  assert.equal(soloKeys([far], stops.map(s => ({ ...s, keep: [0] })), 5, safe)[0], null);  // kept: never hidden
});
