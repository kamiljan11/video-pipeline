// node --test gfx/test/*.test.mjs   ("scene" card: explainer canvas with a camera, the face in the PiP circle)
import test from 'node:test';
import assert from 'node:assert/strict';
import { PIP_ZONE, camKeyframes, checkScene, scene, sceneFit, sceneSafe } from '../scene_lib.mjs';

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

test('motion pieces: bad times and shapes are named', () => {
  const bad = checkScene(ok([
    { k: 'say', x: 0, y: 0, words: [['a', 9]] }, { k: 'cursor', from: [0, 0] }, { k: 'ring', x: 0, y: 0 },
    { k: 'steps', x: 0, y: 0, total: 0, steps: [] }, { k: 'chip', x: 0, y: 0, strike_at: 7, pulse_at: [1, 99] },
    { k: 'stat', x: 0, y: 0, count: { from: 0 } }], { bg: 'neon' }));
  for (const want of ['"words"', '"from" and "to"', '"w" and "h"', '"total"', '"steps"', '"strike_at"', '"pulse_at"', '"count"', '"bg" one of'])
    assert.ok(bad.some(b => b.includes(want)), `missing: ${want}\n${bad.join('\n')}`);
});
