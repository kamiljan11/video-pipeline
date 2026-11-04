// node --test gfx/test/*.test.mjs   (9:16 "meme" card: the picture in the top part, the words in the template's boxes on time)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';

const GFX = path.resolve(import.meta.dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'meme-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));
const lib = path.join(work, 'memes'); fs.mkdirSync(lib);
// a 400x400 red picture; one box over its right half (dark words)
execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=red:s=400x400', '-frames:v', '1', path.join(lib, 'red.png')]);
fs.writeFileSync(path.join(lib, 'nopic.json'), JSON.stringify({ name: 'N', img: 'gone.png', width: 10, height: 10, boxes: [] }));
fs.writeFileSync(path.join(lib, 'badbox.json'), JSON.stringify({ name: 'B', img: 'red.png', width: 400, height: 400, boxes: [[0, 0, 1, 1, 'blue']] }));
fs.writeFileSync(path.join(lib, 'red.json'), JSON.stringify({ name: 'Red', img: 'red.png', width: 400, height: 400, boxes: [[0.5, 0, 0.5, 0.5, 'dark']] }));

const render = specs => {
  const specFile = path.join(work, `${specs[0].id}.json`); fs.writeFileSync(specFile, JSON.stringify(specs));
  return spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000, env: { ...process.env, VP_MEMES: lib } });
};
const frameAt = (mov, t) => {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-ss', String(t), '-i', mov, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], { maxBuffer: 64 << 20 });
  return (x, y) => [...raw.subarray((y * 1080 + x) * 4, (y * 1080 + x) * 4 + 4)];
};

test('a split meme sits in the top part, above the face box, with its words on time', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const r = render([{ id: 'm1', type: 'meme', canvas: 'v', dur: 2.5, meme: 'red', text: ['Tekst'], at: [1.2] }]);
  assert.equal(r.status, 0, r.stderr);
  const mov = path.join(work, 'gfx', 'm1.mov');
  const early = frameAt(mov, 0.8), late = frameAt(mov, 1.8);
  const [r0, g0, b0] = early(300, 560);  // the picture: 960 px square from y 120, left half
  assert.ok(r0 > 180 && g0 < 80 && b0 < 80, `no red picture at (300, 560): ${[r0, g0, b0]}`);
  const box = (f) => { let dark = 0; for (let x = 560; x < 1000; x += 4) for (let y = 300; y < 500; y += 4) { const [r, g, b] = f(x, y); if (r < 80 && g < 80 && b < 80) dark++; } return dark; };
  assert.equal(box(early), 0, 'the words are there before their time');
  assert.ok(box(late) > 20, 'the words are not there after their time');
  assert.ok(late(540, 1300)[3] > 200, 'the split background does not reach the face box area (assemble.py draws the face there)');
});

test('a corner meme fills the top of the screen and leaves the bottom for the face circle', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const r = render([{ id: 'mc', type: 'meme', canvas: 'v', layout: 'corner', dur: 1.5, meme: 'red', text: ['T'], at: [0.2] }]);
  assert.equal(r.status, 0, r.stderr);
  const f = frameAt(path.join(work, 'gfx', 'mc.mov'), 1.0);
  const red = (x, y) => { const [r0, g0, b0] = f(x, y); return r0 > 180 && g0 < 80 && b0 < 80; };
  assert.ok(red(100, 170) && red(1000, 1100), 'the picture does not fill the box x 60..1020, y 155..1115');
  assert.ok(!red(540, 1300) && !red(540, 120), 'the picture runs out of its box (the captions and the face circle sit below it)');
});

test('a 16:9 meme sits left of the face corner, its words on time', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const r = render([{ id: 'm16', type: 'meme', dur: 2.5, meme: 'red', text: ['Tekst'], at: [1.2] }]);
  assert.equal(r.status, 0, r.stderr);
  const raw = t => execFileSync('ffmpeg', ['-v', 'error', '-ss', String(t), '-i', path.join(work, 'gfx', 'm16.mov'), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], { maxBuffer: 64 << 20 });
  const px = (f, x, y) => [...f.subarray((y * 2560 + x) * 4, (y * 2560 + x) * 4 + 4)];
  const early = raw(0.8), late = raw(1.8);
  const [r0, g0, b0] = px(early, 700, 720);  // the picture: 1140 px square centred in x 140..1840
  assert.ok(r0 > 180 && g0 < 80 && b0 < 80, `no red picture at (700, 720): ${[r0, g0, b0]}`);
  const [r1, g1] = px(late, 2200, 1200);  // the PiP corner: the card background, not the picture
  assert.ok(!(r1 > 180 && g1 < 80), 'the picture reaches the face corner');
  const dark = f => { let n = 0; for (let x = 1000; x < 1500; x += 6) for (let y = 300; y < 600; y += 6) { const [r, g, b] = px(f, x, y); if (r < 80 && g < 80 && b < 80) n++; } return n; };
  assert.equal(dark(early), 0, 'the words are there before their time');
  assert.ok(dark(late) > 20, 'the words are not there after their time');
});

test('a long word shrinks to its box instead of running out of it', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  // 16:9: picture 1140 px square at x 420..1560, the box = its right half (x 990..1560, y 150..720); one 24-letter word at the
  // old size (96 px, ~65 px a letter) would be ~1560 px wide and spill left over the picture
  const r = render([{ id: 'mlong', type: 'meme', dur: 1.5, meme: 'red', text: ['Najdłuższewyrażeniebezspacji'], at: [0.1] }]);
  assert.equal(r.status, 0, r.stderr);
  const f = execFileSync('ffmpeg', ['-v', 'error', '-ss', '1.0', '-i', path.join(work, 'gfx', 'mlong.mov'), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], { maxBuffer: 64 << 20 });
  const dark = (x0, x1) => { let n = 0; for (let x = x0; x < x1; x += 4) for (let y = 160; y < 710; y += 4) { const i = (y * 2560 + x) * 4; if (f[i] < 80 && f[i + 1] < 80 && f[i + 2] < 80) n++; } return n; };
  assert.ok(dark(1000, 1550) > 20, 'the word is not in its box');
  assert.equal(dark(430, 980), 0, 'the word runs out of its box over the picture');
});

test('an unknown meme or too many words stop the card by name', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  for (const [sp, why] of [[{ meme: 'nope' }, /meme "nope": not in/], [{ meme: 'red', text: ['a', 'b'] }, /1 text box/], [{ meme: '../x' }, /not in/],
                           [{ meme: 'red', canvas: undefined, layout: 'full' }, /no layout in 16:9/], [{ meme: 'red', text: ['a'], at: ['1'] }, /"at" = seconds/],
                           [{ meme: 'nopic' }, /picture "gone.png" missing/], [{ meme: 'badbox' }, /boxes \[x, y, w, h/]]) {
    const r = render([{ id: 'm2', type: 'meme', canvas: 'v', dur: 2, ...sp }]);
    assert.notEqual(r.status, 0, JSON.stringify(sp));
    assert.match(r.stderr, why);
  }
});

test('a re-fetch of the same picture keeps the card; new boxes re-render it', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const red = JSON.parse(fs.readFileSync(path.join(lib, 'red.json'), 'utf8'));
  const keyOf = (json) => {
    fs.writeFileSync(path.join(lib, 'red.json'), JSON.stringify(json));
    const r = render([{ id: 'm3', type: 'meme', canvas: 'v', dur: 1, meme: 'red', text: ['T'] }]);
    assert.equal(r.status, 0, r.stderr);
    return fs.readFileSync(path.join(work, 'gfx', 'm3.mov.key'), 'utf8');
  };
  try {
    const first = keyOf({ ...red, fetched: '2026-10-01' });
    assert.equal(keyOf({ ...red, fetched: '2026-10-31' }), first, 'the download date alone changed the stamp');
    assert.notEqual(keyOf({ ...red, fetched: '2026-10-31', boxes: [[0, 0, 0.5, 0.5, 'dark']] }), first, 'new boxes kept the old card');
  } finally { fs.writeFileSync(path.join(lib, 'red.json'), JSON.stringify(red)); }
});
