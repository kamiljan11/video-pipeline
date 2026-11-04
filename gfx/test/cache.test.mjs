// node --test gfx/test/*.test.mjs   (render.mjs cache: a card's .mov is rendered again when its spec changes, kept when not)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'cache-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));

const render = sp => {
  const specFile = path.join(work, 'specs.json'); fs.writeFileSync(specFile, JSON.stringify([sp]));
  const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
  assert.equal(r.status, 0, r.stderr);
  return fs.statSync(path.join(work, 'gfx', `${sp.id}.mov`)).mtimeMs;
};

test('a changed scene renders again, the same scene does not', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const sc = { id: 's1', type: 'scene', dur: 0.4, cam: 'none', pip: false, els: [{ k: 'text', x: 100, y: 100, t: 'raz', at: 0 }] };
  const first = render(sc);
  assert.equal(render(sc), first, 'the same spec was rendered again');
  const third = render({ ...sc, els: [{ ...sc.els[0], at: 0.1 }] });
  assert.notEqual(third, first, 'a retimed scene kept its old .mov');
  assert.equal(render({ ...sc, els: [{ ...sc.els[0], at: 0.1 }], behind: { edl: 'x.json' } }), third, '"behind" alone re-rendered the front card');
});
