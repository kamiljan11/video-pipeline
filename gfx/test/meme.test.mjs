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

test('an unknown meme or too many words stop the card by name', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  for (const [sp, why] of [[{ meme: 'nope' }, /meme "nope": not in/], [{ meme: 'red', text: ['a', 'b'] }, /1 text box/], [{ meme: '../x' }, /not in/],
                           [{ meme: 'red', canvas: undefined }, /9:16 card/], [{ meme: 'red', text: ['a'], at: ['1'] }, /"at" = seconds/],
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
