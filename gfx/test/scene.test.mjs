// node --test gfx/test/*.test.mjs   ("scene" card: explainer canvas with a camera, the face in the PiP circle)
import test from 'node:test';
import assert from 'node:assert/strict';
import { PIP_ZONE, camKeyframes, checkScene, frameStops, scene, sceneFit, sceneSafe, soloKeys } from '../scene_lib.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const icon = n => `<svg data-i="${n}"></svg>`;
const ok = (els, more = {}) => ({ id: 's1', type: 'scene', dur: 6, els, ...more });

test('a good scene has no problems and draws every piece once', () => {
  const sp = ok([
    { k: 'term', id: 't', x: 0, y: 0, cmd: 'git push --force', out: ['[bash-guard] BLOCKED'], hl: [0] },
    { k: 'chip', id: 'c', x: 0, y: 500, text: 'exit 2', tone: 'bad', at: 2 },
    { k: 'line', from: [10, 10], to: [400, 300], at: 1 },
  ], { cam: [{ t: 0, on: 't' }, { t: 3, on: '*' }] });
  assert.deepEqual(checkScene(sp), []);
  const h = scene(sp, esc, icon);
  assert.equal((h.match(/class="p /g) || []).length, 2);
  assert.equal((h.match(/class="ln"/g) || []).length, 1);
  assert.match(h, /data-id="t"/);
  assert.match(h, /data-bb="10 10 390 290"/);
  assert.match(h, /data-cam="\[\{&quot;t&quot;:0,&quot;on&quot;:&quot;t&quot;\}/);
});

test('every bad key is named, nothing is drawn', () => {
  const bad = checkScene(ok([{ k: 'video', x: 0, y: 0 }, { k: 'chip', y: 0 }, { k: 'term', x: 0, y: 0, out: 'x' }, { k: 'chip', x: 0, y: 0, at: 9, tone: 'pink' }],
    { cam: [{ t: 2, on: 'nope' }, { t: 1, z: 9 }] }));
  for (const want of ['"k" must be', '"x" and "y"', '"cmd"', '"out"', '"at"', '"tone"', 'no piece has that "id"', 'forward in time', '"z" = zoom'])
    assert.ok(bad.some(b => b.includes(want)), `missing: ${want}\n${bad.join('\n')}`);
  assert.throws(() => scene(ok([{ k: 'video', x: 0, y: 0 }]), esc, icon), /"s1": scene: .*"k" must be/);
});

test('"cam": "none" keeps world coordinates and refuses a piece under the face', () => {
  const under = ok([{ k: 'win', x: PIP_ZONE.x - 100, y: PIP_ZONE.y - 100, w: 400, h: 400 }], { cam: 'none' });
  assert.ok(checkScene(under).some(b => b.includes('face corner')));
  assert.deepEqual(checkScene({ ...under, pip: false }), []);
  assert.doesNotMatch(scene({ ...under, pip: false }, esc, icon), /data-cam/);
});

test('no "cam" = frame the whole drawing; "pip": false frames into the whole picture', () => {
  assert.match(scene(ok([{ k: 'chip', x: 0, y: 0 }]), esc, icon), /data-cam="\[\{&quot;t&quot;:0,&quot;on&quot;:&quot;\*&quot;\}\]"/);
  assert.ok(sceneSafe({}).x + sceneSafe({}).w <= PIP_ZONE.x);
  assert.equal(sceneSafe({ pip: false }).w, 2560 - 240);
});

test('camera keyframes: each move ends at its stop and eases in the "move" seconds before it', () => {
  const kf = camKeyframes([{ t: 0, x: 0, y: 0, z: 1 }, { t: 3, x: 100, y: 50, z: 2, move: 1 }], 6);
  const at = [...kf.matchAll(/([\d.]+)%\{transform:translate\(([-\d.]+)px,([-\d.]+)px\) scale\(([\d.]+)\)/g)].map(m => m.slice(1).map(Number));
  assert.deepEqual(at, [[0, 0, 0, 1], [33.333, 0, 0, 1], [50, -200, -100, 2], [100, -200, -100, 2]]);
  assert.equal(camKeyframes(undefined, 5), null);
});

test('camKeyframes and sceneFit run on their own source (render.mjs evaluates them in the page)', () => {
  const kf = new Function(`return ${camKeyframes.toString()}`)();
  assert.equal(kf([{ t: 0, x: 0, y: 0, z: 1 }], 2), camKeyframes([{ t: 0, x: 0, y: 0, z: 1 }], 2));
  assert.equal(typeof new Function(`return ${sceneFit.toString()}`)(), 'function');
});

test('motion pieces (check, cursor, ring, say, toggle, steps, counting stat) draw and animate from their own times', () => {
  const sp = ok([
    { k: 'say', x: 0, y: 0, words: [['Tabliczka', 0.2], ['~nie~', 0.8], ['[Szlaban]', 1.6], ['*zatrzyma*', 2], ['!stop!', 2.2]], out_at: 5 },
    { k: 'check', x: 0, y: 300, at: 1, tone: 'ok' },
    { k: 'cursor', from: [900, 900], to: [300, 300], at: 1, click_at: 2 },
    { k: 'ring', x: 100, y: 100, w: 200, h: 120, at: 3 },
    { k: 'toggle', x: 0, y: 700, text: 'Zgoda', on_at: 4 },
    { k: 'steps', x: 0, y: 800, label: 'Pomysł', total: 3, steps: [[0.3, 1], [2, 2]] },
    { k: 'stat', x: 600, y: 600, label: 'blizn', count: { to: 100, d: 1, suf: '+' } },
    { k: 'chip', x: 0, y: 950, text: 'tabliczka', strike_at: 2, pulse_at: [1, 3], hl_at: 1.5 },
    { k: 'line', from: [0, 0], to: [500, 0], head: 'arrow', packet_at: 1 },
  ], { bg: 'blobs' });
  assert.deepEqual(checkScene(sp), []);
  const h = scene(sp, esc, icon);
  assert.equal((h.match(/class="w /g) || []).length, 5);  // one span per said word
  for (const want of [/class="w strk"/, /class="w pill"/, /class="w em"/, /class="w bad"/, /scword \.3s [^ ]+ 1\.97s/, /scblurout \.18s ease-in 5\.00s/,
    /scburst/, /scpart/, /sccur 0\.70s [^ ]+ 1\.30s/, /scrip \.5s [^ ]+ 2\.00s/, /class="ln" data-bb="76 76 248 168"/, /sctgk \.25s [^ ]+ 4\.00s/,
    /scfill/, /--w1:66\.7%/, /@keyframes cnt_u[a-z0-9]+\{from\{--cnt:0\}to\{--cnt:100\}\}/, /data-suf="\+"/,
    /scgrow \.25s [^ ]+ 2\.00s/, /scpulse \.45s [^ ]+ 1\.00s/, /scpulse \.45s [^ ]+ 3\.00s/, /class="ghl"/, /offset-path:path\('M0 0/, /class="blobs"/])
    assert.match(h, want);
  assert.doesNotMatch(h, /scpulse[^,"]*both/);  // a pulse never fills: the entrance's end state stays
});

test('toggle back_at: the switch snaps back and glows red after it flipped on (ODMOWA, Kamil 2026-11-05)', () => {
  const sp = ok([{ k: 'toggle', x: 0, y: 0, text: 'wyłącz szlaban', at: 1, on_at: 2, back_at: 3, tone: 'ok' }], { bg: 'blobs' });
  assert.deepEqual(checkScene(sp), []);
  const h = scene(sp, esc, icon);
  assert.match(h, /sctgk \.25s [^ ]+ 2\.00s both,sctgkback \.3s [^ ]+ 3\.00s forwards/);
  assert.match(h, /sctgbad \.6s [^ ]+ 3\.00s forwards/);
  assert.match(checkScene(ok([{ k: 'toggle', x: 0, y: 0, at: 1, on_at: 2, back_at: 1.5 }], { bg: 'blobs' })).join(' '), /"back_at" = after the switch flips on/);
  assert.doesNotMatch(scene(ok([{ k: 'toggle', x: 0, y: 0, on_at: 2 }], { bg: 'blobs' }), esc, icon), /sctgkback/);  // keyframes and animation only with back_at
});

test('motion pieces: bad times and shapes are named', () => {
  const bad = checkScene(ok([
    { k: 'say', x: 0, y: 0, words: [['a', 9]] }, { k: 'cursor', from: [0, 0] }, { k: 'ring', x: 0, y: 0 },
    { k: 'steps', x: 0, y: 0, total: 0, steps: [] }, { k: 'chip', x: 0, y: 0, strike_at: 7, pulse_at: [1, 99] },
    { k: 'stat', x: 0, y: 0, count: { from: 0 } }], { bg: 'neon' }));
  for (const want of ['"words"', '"from" and "to"', '"w" and "h"', '"total"', '"steps"', '"strike_at"', '"pulse_at"', '"count"', '"bg" one of'])
    assert.ok(bad.some(b => b.includes(want)), `missing: ${want}\n${bad.join('\n')}`);
});

test('a 9:16 scene (a short) frames the drawing above the face box and must name its layout', () => {
  const els = [{ k: 'chip', x: 0, y: 0, text: 'a' }];
  assert.deepEqual(checkScene(ok(els, { canvas: 'v', layout: 'split' })), []);
  const split = sceneSafe({ canvas: 'v', layout: 'split' }), corner = sceneSafe({ canvas: 'v', layout: 'corner' });
  assert.ok(split.y + split.h <= 1150 - 60, 'the split frame reaches the captions over the face box (gfx_types.SPLIT)');
  assert.ok(corner.y + corner.h <= 1215 - 60, 'the corner frame reaches the captions (gfx_types.CORNER)');
  assert.ok(split.x + split.w <= 1080 && split.y >= 120, 'outside the 1080 px frame or under the Shorts shelf crop');
  for (const [more, want] of [[{ canvas: 'v' }, '"layout"'], [{ canvas: 'v', layout: 'full' }, '"layout"'],
                              [{ canvas: 'v', layout: 'split', cam: 'none' }, '"cam": "none"']])
    assert.ok(checkScene(ok(els, more)).some(b => b.includes(want)), JSON.stringify(more));
});

test('a say marker split over two words is named (it would show the asterisk on screen)', () => {
  const bad = checkScene(ok([{ k: 'say', x: 0, y: 0, words: [['Autor', 0.1], ['*bez', 0.2], ['redaktora*', 0.3]] }]));
  assert.ok(bad.some(b => b.includes('"*bez"')), bad.join('\n'));
  assert.deepEqual(checkScene(ok([{ k: 'say', x: 0, y: 0, words: [['*bez*', 0.2], ['[AI]', 0.3], ['~nie~', 0.4], ['!nic!', 0.5]] }])), []);
});

test('9:16 solo: a piece cut by the frame hides for that stop and comes back when a stop frames it', () => {
  const safe = { x: 60, y: 130, w: 960, h: 1010 };
  const narrow = { t: 0, x: 0, y: 0, z: 1 }, wide = { t: 5, x: -100, y: -400, z: 0.4, move: 1 };
  const inside = { x: 100, y: 200, w: 400, h: 100 }, cut = { x: 100, y: 400, w: 1800, h: 100 };
  const [a, b] = soloKeys([inside, cut], [narrow, wide], 8, safe);
  assert.equal(a, null);                                   // always fits: never animated
  assert.deepEqual(b, [[0, 0], [4.75, 0], [5, 1], [8, 1]]);   // hidden while cut, fades in at the end of the move to the whole picture
  const [c] = soloKeys([cut], [wide, { t: 6, x: 0, y: 0, z: 1, move: 1 }], 8, safe);
  assert.deepEqual(c, [[0, 1], [5, 1], [5.25, 0], [8, 0]]);   // fades out as the camera starts moving in
  assert.equal(typeof new Function(`return ${soloKeys.toString()}`)(), 'function');
});

test('only a 9:16 scene asks for solo', () => {
  const els = [{ k: 'chip', id: 'a', x: 100, y: 100, text: 'x', at: 0.1 }];
  assert.match(scene({ id: 'v', type: 'scene', dur: 3, els, canvas: 'v', layout: 'corner' }, String, () => '<svg></svg>'), /data-solo="1"/);
  assert.doesNotMatch(scene({ id: 'h', type: 'scene', dur: 3, els }, String, () => '<svg></svg>'), /data-solo/);
});

test('a 16:9 side scene sits on a board right of the speaker, see-through elsewhere (Kamil 2026-11-05)', () => {
  const sp = ok([{ k: 'chip', id: 'c', x: 0, y: 0, text: 'exit 2' }], { layout: 'side' });
  assert.deepEqual(checkScene(sp), []);
  const safe = sceneSafe(sp);
  assert.ok(safe.x >= 1600 && safe.x + safe.w <= 2560 && safe.y + safe.h <= 1440, JSON.stringify(safe));  // right of the head (x <= 0.61 W)
  const h = scene(sp, esc, icon);
  assert.match(h, /class="scene side col"/);
  assert.match(h, /class="board" style="left:1640px/);
  assert.doesNotMatch(h, /class="blobs"/);
  for (const [more, want] of [[{ layout: 'split' }, '"layout" = "side"'], [{ layout: 'side', cam: 'none' }, '"cam": "none" has no place']])
    assert.ok(checkScene(ok([{ k: 'chip', x: 0, y: 0, text: 'x' }], more)).some(b => b.includes(want)), want);
});

test('beside the speaker the pieces stack in one column in reading order; a scene with a line keeps its drawing', () => {
  // Kamil 2026-11-05: a wide row shrunk into the side field cannot be read on a phone: "większe i pionowo narysowane"
  const row = ok(['a', 'b', 'c', 'd'].map((t, i) => ({ k: 'chip', id: t, x: 120 + 400 * i, y: 500, text: `Zadanie ${i + 1}` })), { layout: 'side' });
  const h = scene({ ...row, els: [...row.els].reverse() }, esc, icon);
  assert.match(h, /class="scene side col"/);
  assert.ok(h.indexOf('Zadanie\u00a01') < h.indexOf('Zadanie\u00a04') && h.includes('Zadanie\u00a01'));  // left to right becomes top to bottom ("1" glued, keepTogether)
  const tied = scene({ ...row, els: [...row.els, { k: 'line', from: [10, 10], to: [400, 300], at: 1 }] }, esc, icon);
  assert.match(tied, /class="scene side"/);
});

test('a side column follows the newest pieces; the side scene is clipped to its board (2026-11-08 readability)', async () => {
  const { colFollow } = await import('../scene_lib.mjs');
  const cam = [{ t: 0, on: ['a'] }, { t: 2, on: ['a', 'b'] }, { t: 4, on: ['a', 'b'] }, { t: 6, on: '*' }];
  assert.deepEqual(colFollow(cam).map(s => s.on), [['a'], ['b'], ['a', 'b'], '*']);  // nothing new: the stop stays as it was
  const row = ok([{ k: 'chip', id: 'a', x: 120, y: 500, text: 'x' }], { layout: 'side' });
  assert.match(scene(row, esc, icon), /class="scene side col" style="clip-path:inset\(150px 100px 290px 1640px round 48px\)"/);
});

test('sceneFit takes a piece the framing would cut into the framing, down to 0.85 of the zoom; past that the piece hides for the stop (stills 2026-11-08)', () => {
  const el = (id, x, y, w = 200) => ({ dataset: { id }, offsetLeft: x, offsetTop: y, offsetWidth: w, offsetHeight: 100, classList: { contains: c => c === 'p' }, style: {} });
  const run = (pieces) => {
    const head = [];
    const world = { dataset: { cam: JSON.stringify([{ t: 0, on: ['b'], zmax: 1.8 }, { t: 4, on: '*' }]), dur: '8' }, querySelectorAll: () => pieces, style: {},
      parentElement: { classList: { contains: () => false }, getBoundingClientRect: () => ({ width: 2560, height: 1440 }) } };
    globalThis.document = { querySelector: () => world, createElement: () => ({ textContent: '' }), head: { appendChild: s => head.push(s) } };
    globalThis.getComputedStyle = () => ({ clipPath: 'none' });
    try { return [sceneFit({ x: 110, y: 100, w: 1800, h: 1240 }, camKeyframes.toString(), soloKeys.toString(), null, null, frameStops.toString()), head, pieces]; }
    finally { delete globalThis.document; delete globalThis.getComputedStyle; }
  };
  // framing "b" alone at 1.8 shows world x 1039..2461: "c" at 2350..2550 would be cut, so the camera takes it in (z 1800/1150)
  const [near] = run([el('a', 100, 100), el('b', 1500, 900), el('c', 2350, 900)]);
  assert.ok(Math.abs(near[0].z - 1800 / 1150) < 1e-9, `z ${near[0].z}`);
  // a wide neighbour would need z 0.95 (< 0.85 of 1.8): the camera keeps 1.8 and that piece fades out for the stop
  const [far, head, pieces] = run([el('a', 100, 100), el('b', 1500, 900), el('c', 2300, 900, 1000)]);
  assert.equal(far[0].z, 1.8);
  assert.match(head[0].textContent, /@keyframes solo_2\{0\.000%\{opacity:0\}/);
  assert.match(pieces[2].style.animation, /^solo_2 8s linear both$/);
});

test('sceneFit measures a piece with the label that sticks out of it (node "Księgarnia", 2026-11-08)', () => {
  const label = { offsetWidth: 300, offsetHeight: 50, offsetLeft: -90, offsetTop: 130, offsetParent: null };
  const node = { dataset: { id: 'n' }, offsetLeft: 1000, offsetTop: 500, offsetWidth: 120, offsetHeight: 120, classList: { contains: () => true }, style: {}, querySelectorAll: () => [label] };
  label.offsetParent = node;
  const world = { dataset: { cam: JSON.stringify([{ t: 0, on: ['n'], zmax: 1, pad: 0 }]), dur: '4' }, querySelectorAll: () => [node], style: {} };
  globalThis.document = { querySelector: () => world, createElement: () => ({ textContent: '' }), head: { appendChild: () => {} } };
  try {
    const safe = { x: 0, y: 0, w: 2560, h: 1440 }, [st] = sceneFit(safe, camKeyframes.toString(), null, null, null, frameStops.toString());
    assert.equal(st.x, 1000 - 90 + 300 / 2 - 1280);  // centred on icon + label (910..1210), not the icon alone (1000..1120)
    assert.equal(st.y, 500 + 180 / 2 - 720);
  } finally { delete globalThis.document; }
});

test('frameStops in Node: a stop frames its piece plus the one still being read; a piece read 3 s ago drops out; sceneFit without its source throws', () => {
  const pieces = [{ id: 'a', x: 0, y: 0, w: 200, h: 100, at: 1 }, { id: 'b', x: 1000, y: 0, w: 200, h: 100, at: 2.5 }, { id: 'c', x: 0, y: 600, w: 200, h: 100, at: 6 }];
  const { frame, centre } = frameStops(pieces, { x: 0, y: 0, w: 1920, h: 1080 }, null);
  assert.deepEqual(frame({ t: 3, on: ['b'] }).keep, [0, 1]);  // a came in 2 s before: still being read, stays framed
  assert.deepEqual(frame({ t: 6.5, on: ['c'] }).keep, [2]);   // a and b came in > 2.9 s before: the camera may leave them
  assert.deepEqual(centre(['c'], 6.5).box, [0, 600, 200, 700]);
  assert.throws(() => sceneFit({ x: 0, y: 0, w: 10, h: 10 }, camKeyframes.toString(), null), /frameStops/);
});

test('term: "out_start" starts the output, "out_at" makes the terminal leave; "out_at" alone keeps doing both (old specs)', () => {
  const term = more => scene(ok([{ k: 'term', id: 't', x: 0, y: 0, cmd: 'ls', out: ['a'], ...more }]), esc, icon);
  const delays = h => [...h.matchAll(/class="ol"[^>]*animation:\S+ \S+ ([\d.]+)s both/g)].map(m => m[1]);
  assert.deepEqual(delays(term({ out_start: 1.5, out_at: 4 })), ['1.50']);  // output at 1.5, leaves at 4
  assert.match(term({ out_start: 1.5, out_at: 4 }), /4\.00s forwards/);
  assert.deepEqual(delays(term({ out_at: 4 })), ['4.00']);  // legacy: out_at is the output start too
  assert.deepEqual(checkScene(ok([{ k: 'term', x: 0, y: 0, cmd: 'ls', out_start: 9 }])).length, 1);  // out_start is a time 0..dur
});

test('term: "out_start" after "out_at" is named (the output would start after the terminal left)', () => {
  const t = out_start => checkScene(ok([{ k: 'term', id: 't', x: 0, y: 0, cmd: 'ls', out: ['a'], out_start, out_at: 3 }]));
  assert.ok(t(4).some(b => b.includes('"out_start"')), t(4).join('\n'));
  assert.ok(!t(1.5).some(b => b.includes('"out_start"')));
});
