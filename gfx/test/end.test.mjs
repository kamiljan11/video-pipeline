// node --test gfx/test/*.test.mjs   ("end" card: optional brand row = "logo" image + "logo_sub" line under the address)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });
const noChrome = !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome';

const logo = (work, color) => execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i', `color=c=${color}:s=400x60`, '-frames:v', '1', path.join(work, 'logo #1 dir.png')]);
const render = (work, specs) => {
  const specFile = path.join(work, 'gfx_specs.json'); fs.writeFileSync(specFile, JSON.stringify(specs));
  const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
  return { r, gfx: path.join(work, 'gfx') };
};
const run = (specs, withLogo = true) => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'end-')); made.push(work);
  if (withLogo) logo(work, 'red');
  return { work, ...render(work, specs) };
};
// pixels of one frame at t that are pure-ish red (the test logo); blue = the same check on the blue channel
const redPixels = (mov, t, ch = 0) => {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-ss', String(t), '-i', mov, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
    { maxBuffer: 64 * 1024 * 1024 });
  let n = 0;
  for (let i = 0; i < raw.length; i += 4) if (raw[i + ch] > 200 && raw[i + (ch + 1) % 3] < 60 && raw[i + (ch + 2) % 3] < 60 && raw[i + 3] > 200) n++;
  return n;
};
const card = { id: 'end', type: 'end', text: 'Dzięki', sub: 'example.com', dur: 3 };  // brand row fully in at 1.1 s; the card fades out at its end

test('"logo" puts the image (path relative to the specs file) under the address, "logo_sub" under it', { skip: noChrome }, () => {
  const { r, gfx } = run([{ ...card, logo: 'logo #1 dir.png', logo_sub: 'brand.example' }, { ...card, id: 'plain' }]);
  assert.equal(r.status, 0, r.stderr);
  const n = redPixels(path.join(gfx, 'end.mov'), 1.6);
  assert.ok(n > 0.8 * 640 * 96, `logo drawn 96 px high (400x60 -> 640x96), got ${n} red pixels`);
  assert.equal(redPixels(path.join(gfx, 'plain.mov'), 1.6), 0);  // no "logo": the end card as before
});

test('a new logo file under the same name renders the card again, an unchanged one does not', { skip: noChrome }, () => {
  const specs = [{ ...card, logo: 'logo #1 dir.png' }];
  const { work, gfx } = run(specs);
  const mov = path.join(gfx, 'end.mov'), first = fs.statSync(mov).mtimeMs;
  assert.equal(render(work, specs).r.status, 0);
  assert.equal(fs.statSync(mov).mtimeMs, first);  // same spec, same logo bytes: kept
  logo(work, 'blue');
  assert.equal(render(work, specs).r.status, 0);
  assert.ok(redPixels(mov, 1.6, 2) > 0.8 * 640 * 96, 'the blue logo is in the new render');
});

test('a logo file that is not there stops the render with its name', { skip: noChrome }, () => {
  const { r } = run([{ ...card, logo: 'missing.png' }], false);
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /FAILED gfx end: logo .*missing\.png not found/);
});
