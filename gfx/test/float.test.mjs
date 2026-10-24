// node --test gfx/test/*.test.mjs   ("float" card: an illustration beside the speaker, no background over the face)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });

const render = specs => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'float-')); made.push(work);
  const specFile = path.join(work, 'gfx_specs.json'); fs.writeFileSync(specFile, JSON.stringify(specs));
  const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
  assert.equal(r.status, 0, r.stderr);
  return path.join(work, 'gfx');
};
// one rgba frame at t of a 2560x1440 card; [x, y] -> [r, g, b, a]
const frameAt = (mov, t, w = 2560) => {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-ss', String(t), '-i', mov, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
    { maxBuffer: 64 << 20 });
  return (x, y) => [...raw.subarray((y * w + x) * 4, (y * w + x) * 4 + 4)];
};

test('a float piece comes in on its delay, goes out on its exit, and the face stays clear', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const piece = '<div class="p" style="left:100px;top:100px;animation:flfade .2s linear .6s both, flout .2s linear 1.6s forwards">'
    + '<div class="card" style="width:400px;height:300px;background:#fff"></div></div>';
  const dir = render([{ id: 'f', type: 'float', dur: 2.5, html: piece }]);
  const at = t => frameAt(path.join(dir, 'f.mov'), t);
  assert.equal(at(0.3)(300, 250)[3], 0, 'shown before its delay');
  assert.ok(at(1.2)(300, 250)[3] > 200, 'not shown after its delay');
  assert.equal(at(2.2)(300, 250)[3], 0, 'still shown after its exit');
  assert.equal(at(1.2)(1150, 700)[3], 0, 'the face area is covered');
});
