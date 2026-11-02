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
