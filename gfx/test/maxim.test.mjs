// node --test gfx/test/*.test.mjs   ("maxim" card: a key sentence typed on screen while it is said)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';
import { CHAR_MAX, LAST_SHOWN, TYPE_START, charTimes, maximSeek, maximWords, wordTimes } from '../maxim_lib.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });

test('words in *stars* are the highlighted ones, the stars never show', () => {
  assert.deepEqual(maximWords('Pierwszy projekt ma *zbudować zaufanie*'),
    [{ w: 'Pierwszy', hl: false }, { w: 'projekt', hl: false }, { w: 'ma', hl: false }, { w: 'zbudować', hl: true }, { w: 'zaufanie', hl: true }]);
  assert.deepEqual(maximWords('to *jedno* słowo').map(x => x.hl), [false, true, false]);
  assert.deepEqual(maximWords('*pewny,* policzalny').map(x => [x.w, x.hl]), [['pewny,', true], ['policzalny', false]]);
  assert.deepEqual(maximWords('  '), []);
  assert.deepEqual(maximWords('a * b c * d').map(x => x.hl), [false, true, true, false]);  // a lone star switches, never sticks
  assert.deepEqual(maximWords('*a*b c').map(x => [x.w, x.hl]), [['ab', true], ['c', true]]);  // no star is ever shown
});

test('word times: the transcript ones never go back or past the card; without them an even pace', () => {
  const w = maximWords('a b c');
  assert.deepEqual(wordTimes(w, 4, [0.2, 0.1, 9]), [0.2, 0.2, 4 - LAST_SHOWN]);  // the last word still shows
  const even = wordTimes(w, 4, [0.1]);  // wrong length: not trusted
  assert.equal(even[0], TYPE_START);
  assert.ok(even[2] <= 4 * 0.6 + 1e-9 && even[1] > even[0] && even[2] > even[1]);
  const long = maximWords('a bbbbbbbbbb c'), t = wordTimes(long, 6);  // even pace goes by letters, not by words
  assert.ok(t[2] - t[1] > 3 * (t[1] - t[0]));
});

test('a word finishes typing before the next one starts, at most CHAR_MAX per letter', () => {
  const w = maximWords('długieslowo b'), t = wordTimes(w, 3, [0.2, 0.4]), c = charTimes(w, t, 3);
  assert.ok(c[0].at(-1) < 0.4);  // squeezed into 0.2 s
  const slow = charTimes(w, wordTimes(w, 3, [0.2, 2.5]), 3);
  assert.ok(Math.abs(slow[0][1] - slow[0][0] - CHAR_MAX) < 1e-9);  // never slower than CHAR_MAX
});

test('maximSeek: letters appear at their times, the marker draws after its word, the caret blinks out after typing', () => {
  const el = t => ({ dataset: { t: String(t) }, style: {}, after(c) { c.at = this; } });
  const letters = [el(0.1), el(0.2), el(0.3)], marks = [el(0.35)], caret = { style: {} };
  globalThis.document = { querySelectorAll: q => (q.endsWith(' i') ? letters : marks), querySelector: () => caret };
  try {
    const seek = new Function(`return ${maximSeek.toString()}`)()(0.7, 0.3);  // as render.mjs sends it into the page
    seek(0.25);
    assert.deepEqual(letters.map(l => l.style.visibility), ['visible', 'visible', 'hidden']);
    assert.equal(caret.at, letters[1]);
    assert.equal(marks[0].style.transform, 'scaleX(0)');
    seek(0.65);
    assert.equal(marks[0].style.transform, 'scaleX(1)');
    assert.equal(caret.at, letters[2]);
    seek(1.2);
    assert.equal(caret.style.opacity, 0);  // 0.7 s after the last letter
  } finally { delete globalThis.document; }
});

const framesOf = mov => execFileSync('ffmpeg', ['-v', 'error', '-i', mov, '-f', 'framemd5', '-'], { encoding: 'utf8' })
  .split('\n').filter(l => l && !l.startsWith('#')).map(l => l.split(',').pop().trim());
const render = specs => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'maxim-')); made.push(work);
  const specFile = path.join(work, 'gfx_specs.json'); fs.writeFileSync(specFile, JSON.stringify(specs));
  const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
  assert.equal(r.status, 0, r.stderr);
  return path.join(work, 'gfx');
};

test('the same maxim gives the same frames twice, types on while said, then holds', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const spec = [{ id: 'm', type: 'maxim', text: 'Jedno *ważne* zdanie', dur: 2.5, at: [0.2, 0.6, 1.0] },
    { id: 'v', type: 'maxim', canvas: 'v', text: 'Pionowo *też*', dur: 2.5 }];
  const a = render(spec), b = render(spec);
  for (const id of ['m', 'v']) {
    const fa = framesOf(path.join(a, `${id}.mov`)), fb = framesOf(path.join(b, `${id}.mov`));
    assert.equal(fa.length, 75);
    assert.deepEqual(fa, fb, `${id}: frames differ between two renders`);
    assert.ok(new Set(fa.slice(6, 40)).size > 10, `${id}: the sentence does not type on`);
  }
});

// one rgba frame at t; [x, y] -> [r, g, b, a]
const frameAt = (mov, t, w = 1080) => {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-ss', String(t), '-i', mov, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
    { maxBuffer: 64 << 20 });
  return (x, y) => [...raw.subarray((y * w + x) * 4, (y * w + x) * 4 + 4)];
};

test('"pill" puts the 9:16 maxim in a white box in the caption zone, not in the top band', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const dir = render([{ id: 'p', type: 'maxim', canvas: 'v', pill: true, text: '*95%* firm', dur: 2 },
    { id: 'q', type: 'maxim', canvas: 'v', text: '*95%* firm', dur: 2 }]);
  const pill = frameAt(path.join(dir, 'p.mov'), 1.5), plain = frameAt(path.join(dir, 'q.mov'), 1.5);
  const edge = pill(100, 1450);  // left edge of the pill at ~76 % height: white, see-through (Kamil 2026-10-24: it hid half the face)
  assert.deepEqual(edge.slice(0, 3), [255, 255, 255]);
  assert.ok(edge[3] > 140 && edge[3] < 200, `pill alpha ${edge[3]}`);
  assert.equal(pill(540, 1080)[3], 0);  // nothing at 56 %: the mouth stays free
  assert.equal(pill(540, 1250)[3], 0);  // nor at 65 %: the chin stays free
  assert.equal(pill(540, 100)[3], 0);  // nothing in the top band (no scrim)
  assert.ok(plain(540, 100)[3] > 0, 'a plain 9:16 maxim keeps its top scrim');
  assert.equal(plain(100, 1450)[3], 0);
});
