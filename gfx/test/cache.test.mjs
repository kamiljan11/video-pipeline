// node --test gfx/test/*.test.mjs   (render.mjs cache: a card's .mov is rendered again when its spec changes, kept when not)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'cache-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));

const render = (sp, gfx = GFX) => {
  const specFile = path.join(work, 'specs.json'); fs.writeFileSync(specFile, JSON.stringify([sp]));
  const r = spawnSync('node', [path.join(gfx, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
  assert.equal(r.status, 0, r.stderr);
  return fs.statSync(path.join(work, 'gfx', `${sp.id}.mov`)).mtimeMs;
};

test('a changed scene renders again, the same scene does not', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, t => {
  const sc = { id: 's1', type: 'scene', dur: 0.4, cam: 'none', pip: false, els: [{ k: 'text', x: 100, y: 100, t: 'raz', at: 0 }] };
  const first = render(sc);
  assert.equal(render(sc), first, 'the same spec was rendered again');
  const third = render({ ...sc, els: [{ ...sc.els[0], at: 0.1 }] });
  assert.notEqual(third, first, 'a retimed scene kept its old .mov');
  // a "behind" card then runs behind.py, which needs the optional matte/.venv (README: text behind the speaker); CI has none
  if (!fs.existsSync('/home/kamil-jan/video-pipeline/matte/.venv/bin/python')) return t.diagnostic('no matte/.venv: the "behind" case not checked');
  assert.equal(render({ ...sc, els: [{ ...sc.els[0], at: 0.1 }], behind: { edl: 'x.json' } }), third, '"behind" alone re-rendered the front card');
});

test('a scene is rendered again when scene_lib.mjs changes (its source is in the key)', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  // a copy of gfx/ whose scene_lib.mjs gets one more byte: same spec, other library = a new .mov
  const copy = path.join(work, 'gfxcopy');
  fs.cpSync(GFX, copy, { recursive: true, filter: f => !/\/(test|test_out)(\/|$)/.test(f.slice(GFX.length)) });
  const sc = { id: 'lib1', type: 'scene', dur: 0.4, cam: 'none', pip: false, els: [{ k: 'text', x: 100, y: 100, t: 'raz', at: 0 }] };
  const first = render(sc, copy);
  assert.equal(render(sc, copy), first, 'the same spec and library were rendered again');
  fs.appendFileSync(path.join(copy, 'scene_lib.mjs'), '\n// changed\n');
  assert.notEqual(render(sc, copy), first, 'a changed scene_lib.mjs kept the old .mov');
});
