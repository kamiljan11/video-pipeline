// node --test gfx/test/*.test.mjs   (render.mjs --stills: one PNG per card at its still time; the stills gate on .mov renders)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'stills-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));
const out = path.join(work, 'gfx'), sd = path.join(out, 'stills');
const run = (specs, args = [], env = {}) => {
  const specFile = path.join(work, 'specs.json'); fs.writeFileSync(specFile, JSON.stringify(specs));
  return spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, out, ...args], { encoding: 'utf8', timeout: 120000, env: { ...process.env, ...env } });
};
const sc = (id, more = {}) => ({ id, type: 'scene', dur: 3, cam: 'none', pip: false, els: [{ k: 'text', x: 100, y: 100, t: 'raz', at: 0.5 }, { k: 'text', x: 100, y: 300, t: 'dwa', at: 1.2 }], ...more });

test('stills: a PNG, the render key and the moment per card, no .mov; only the ids asked for', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const r = run([sc('a'), sc('b', { still: 0.7 })], ['--stills', 'a', 'b']);
  assert.equal(r.status, 0, r.stderr);
  for (const id of ['a', 'b']) for (const ext of ['png', 'key', 't']) assert.ok(fs.existsSync(path.join(sd, `${id}.${ext}`)), `${id}.${ext}`);
  assert.ok(Math.abs(+fs.readFileSync(path.join(sd, 'a.t'), 'utf8') - 1.8) < 1e-9);  // last piece in at 1.2 + 0.6
  assert.equal(+fs.readFileSync(path.join(sd, 'b.t'), 'utf8'), 0.7);  // "still" in the spec
  assert.ok(!fs.existsSync(path.join(out, 'a.mov')));
  assert.equal(run([sc('c')], ['--stills', 'zz']).status, 0);
  assert.ok(!fs.existsSync(path.join(sd, 'c.png')), 'a card not asked for got a still');
});

test('gate: a card in scope.json renders only with its accepted key; a change needs a new accept; STILLS=off overrides', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const card = sc('g', { dur: 0.4, els: [{ k: 'text', x: 100, y: 100, t: 'raz', at: 0 }] });
  assert.equal(run([card], ['--stills']).status, 0);
  fs.writeFileSync(path.join(sd, 'accepted.json'), '{}');
  assert.equal(run([card]).status, 0, 'no scope.json yet: nothing gated');
  fs.rmSync(path.join(out, 'g.mov')); fs.rmSync(path.join(out, 'g.mov.key'));
  fs.writeFileSync(path.join(sd, 'scope.json'), JSON.stringify(['g']));
  const other = sc('o', { dur: 0.4, els: [{ k: 'text', x: 100, y: 100, t: 'x', at: 0 }] });
  assert.equal(run([other]).status, 0, 'a card of a film without a sheet (not in scope) was gated');
  let r = run([card]);
  assert.equal(r.status, 1); assert.match(r.stderr, /FAILED gfx g: no accepted still/);
  fs.writeFileSync(path.join(sd, 'accepted.json'), JSON.stringify({ g: fs.readFileSync(path.join(sd, 'g.key'), 'utf8') }));
  assert.equal(run([card]).status, 0, 'accepted card was refused');
  assert.ok(fs.existsSync(path.join(out, 'g.mov')));
  const changed = { ...card, els: [{ ...card.els[0], t: 'dwa' }] };
  assert.equal(run([changed]).status, 1, 'a card changed after acceptance rendered');
  fs.writeFileSync(path.join(sd, 'scope.json'), JSON.stringify(['g', 'h']));
  const h = sc('h', { dur: 0.4, els: [{ k: 'text', x: 100, y: 100, t: 'h', at: 0 }] });
  r = run([changed, h]);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /FAILED gfx g:/); assert.match(r.stderr, /FAILED gfx h:/);  // every refused card named before any render
  assert.ok(!fs.existsSync(path.join(out, 'h.mov')), 'a card rendered although another was refused');
  r = run([changed], [], { STILLS: 'off' });
  assert.equal(r.status, 0, r.stderr); assert.match(r.stderr, /WARN stills gate off/);
});
