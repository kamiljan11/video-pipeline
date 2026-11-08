// node --test gfx/test/cli.test.mjs: a gfx script started through a symlinked path still runs (2026-11-08: run_v4.sh starts
// node through ~/video-pipeline, a link to ~/Dane/video-pipeline, and scene_check / thumbs / post_gfx ended with exit 0 doing nothing)
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'child_process';
import fs from 'fs'; import os from 'os'; import path from 'path';

const GFX = fs.realpathSync(path.resolve(import.meta.dirname, '..'));

test('started through a symlink, every CLI script runs its main (usage error, not a silent exit 0)', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'gfxlink-'));
  const link = path.join(d, 'gfx');
  fs.symlinkSync(GFX, link);
  try {
    for (const s of ['thumbs.mjs', 'scene_check.mjs', 'post_gfx.mjs']) {
      const r = spawnSync(process.execPath, [path.join(link, s)], { encoding: 'utf8', timeout: 60000 });
      assert.equal(r.status, 2, `${s}: exit ${r.status}, out ${r.stdout}${r.stderr}`);
      assert.match(r.stderr + r.stdout, /usage/, s);
    }
    const w = spawnSync(process.execPath, [path.join(link, 'webshot.mjs')], { encoding: 'utf8', timeout: 60000 });
    assert.notEqual(w.status, 0, 'webshot.mjs without a spec must not pass silently');
  } finally { fs.rmSync(d, { recursive: true, force: true }); }
});
