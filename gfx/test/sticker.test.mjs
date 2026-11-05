// node --test gfx/test/*.test.mjs   (16:9 "sticker": a meme's character beside the speaker, beat by beat, no separate screen)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'sticker-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));
const lib = path.join(work, 'memes'); fs.mkdirSync(lib);
// 400x400: left half red, right half green; the picture's own json names one crop per half (no catalogue entry for "rg")
execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=red:s=400x400', '-vf', 'drawbox=x=200:y=0:w=200:h=400:color=0x00ff00:t=fill',
  '-frames:v', '1', path.join(lib, 'rg.png')]);
const pic = { name: 'RG', img: 'rg.png', width: 400, height: 400, boxes: [] };
fs.writeFileSync(path.join(lib, 'rg.json'), JSON.stringify({ ...pic, sticker: [[0, 0, 0.5, 1], [0.5, 0, 0.5, 1]] }));
fs.writeFileSync(path.join(lib, 'nocrop.json'), JSON.stringify(pic));

const render = specs => {
  const specFile = path.join(work, `${specs[0].id}.json`); fs.writeFileSync(specFile, JSON.stringify(specs));
  return spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000, env: { ...process.env, VP_MEMES: lib } });
};
const frameAt = (mov, t) => {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-ss', String(t), '-i', mov, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], { maxBuffer: 64 << 20 });
  return (x, y) => [...raw.subarray((y * 2560 + x) * 4, (y * 2560 + x) * 4 + 4)];  // px of the 2560x1440 card (= its css px)
};
const CHROME = { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' };

test('a sticker sits beside the speaker and flips to its next beat on time', CHROME, () => {
  const r = render([{ id: 's1', type: 'sticker', dur: 2.6, meme: 'rg', text: ['Raz', 'Dwa'], at: [0.1, 1.4] }]);
  assert.equal(r.status, 0, r.stderr);
  const mov = path.join(work, 'gfx', 's1.mov'), first = frameAt(mov, 1.0), second = frameAt(mov, 2.0);
  const x = 1620 + 410, y = 150 + 300;  // the middle of the right box (render.mjs STICKER_BOX), upper part
  const [r1, g1] = first(x, y), [r2, g2] = second(x, y);
  assert.ok(r1 > 180 && g1 < 80, `beat 1 is not the red half at (${x}, ${y}): ${first(x, y)}`);
  assert.ok(g2 > 180 && r2 < 80, `beat 2 is not the green half at (${x}, ${y}): ${second(x, y)}`);
  for (const f of [first, second]) for (const px of [900, 1150, 1450]) assert.equal(f(px, 500)[3], 0, `the speaker's middle is covered at x ${px}`);
});

test('a sticker without crops or with a wrong side stops by name', () => {
  let r = render([{ id: 's2', type: 'sticker', dur: 2, meme: 'nocrop' }]);
  assert.notEqual(r.status, 0); assert.match(r.stderr, /s2.*"sticker": \[\[x, y, w, h\]/s);
  r = render([{ id: 's3', type: 'sticker', dur: 2, meme: 'rg', side: 'top' }]);
  assert.notEqual(r.status, 0); assert.match(r.stderr, /s3.*"side" = "right" or "left"/s);
  r = render([{ id: 's4', type: 'sticker', dur: 2, meme: 'rg', canvas: 'v' }]);
  assert.notEqual(r.status, 0); assert.match(r.stderr, /s4.*a sticker is 16:9/s);
});
