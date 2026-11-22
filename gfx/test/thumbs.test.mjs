// node --test gfx/test/*.test.mjs   (thumbs.mjs: A/B thumbnails for the long and covers for shorts, from thumbs.json)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { checkThumbs, fitProblems, longHtml, shortHtml } from '../thumbs.mjs';
import { keepTogether } from '../html_lib.mjs';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-test-'));
fs.writeFileSync(path.join(dir, 'f.png'), '');
const v = (id, more = {}) => ({ id, frame: 'f.png', big: '92% → 18%', sub: 'błędów AI', ...more });

test('a good spec: two long variants and a cover', () => {
  assert.deepEqual(checkThumbs({ long: [v('A'), v('B', { side: 'right', icon: 'construction' })], shorts: [v('s1')] }, dir), []);
});

test('one variant, a long headline, a missing frame or icon, a bad id: each named', () => {
  const bad = checkThumbs({ long: [v('A b', { big: 'zdecydowanie za długi napis', frame: 'nope.png', icon: 'no-such-icon', side: 'up' })] }, dir);
  for (const want of ['at least 2 variants', '"id"', 'keep it <= 18', '"frame"', 'no lucide icon', '"side"'])
    assert.ok(bad.some(b => b.includes(want)), `missing: ${want}\n${bad.join('\n')}`);
  assert.ok(checkThumbs({ long: [v('A'), v('A')] }, dir).some(b => b.includes('twice')));
});

test('html: words escaped, side and frame position used, theme colours inlined', () => {
  const h = longHtml(v('A', { big: '<b>x', side: 'right', fx: -300, fy: -100 }), dir, 'cetus');
  assert.match(h, /&lt;b&gt;x/); assert.doesNotMatch(h, /<b>x/);
  assert.match(h, /right:60px/); assert.match(h, /background-position:-300px -100px/); assert.match(h, /--acc:#6FA7EC/);
  assert.match(shortHtml(v('s1', { dy: 150 }), dir, 'cetus'), /background-position:0 150px/);
});

test('fit: a headline wider than its column or words past the bottom are named, a fitting one passes', () => {
  assert.deepEqual(fitProblems('long_A.jpg', { wide: [['big', 640, 640], ['sub', 600, 640]], bottom: 700 }, 720), []);
  const bad = fitProblems('long_B.jpg', { wide: [['big', 860, 640]], bottom: 760 }, 720);
  assert.ok(bad.some(b => b.includes('"big" is 220 px wider')), bad.join('\n'));
  assert.ok(bad.some(b => b.includes('40 px past the bottom')), bad.join('\n'));
});

test('the feed: a word too small at 320 px, a word under the length in the corner, cover text outside the safe zone', () => {
  const box = (k, x0, y0, x1, y1, fs) => ({ k, x0, y0, x1, y1, fs });
  const fit = { wide: [], bottom: 600 };
  assert.deepEqual(fitProblems('long_A.jpg', { ...fit, boxes: [box('big', 60, 110, 700, 300, 150), box('tag', 60, 500, 400, 560, 48)] }, 720), []);
  const small = fitProblems('long_A.jpg', { ...fit, boxes: [box('tag', 60, 500, 400, 540, 30)] }, 720);
  assert.ok(small.some(b => b.includes('"tag" is 7.5 px at 320 px')), small.join('\n'));
  const corner = fitProblems('long_B.jpg', { ...fit, boxes: [box('sub', 580, 560, 1220, 690, 60)] }, 720);
  assert.ok(corner.some(b => b.includes('bottom-right 12%')), corner.join('\n'));
  assert.deepEqual(fitProblems('s1_cover.jpg', { ...fit, bottom: 700, boxes: [box('big', 60, 220, 1020, 400, 140)] }, 1920, 1080, true), []);
  const low = fitProblems('s1_cover.jpg', { ...fit, bottom: 1800, boxes: [box('sub', 60, 1700, 1020, 1800, 62)] }, 1920, 1080, true);
  assert.ok(low.some(b => b.includes('outside the cover\'s safe zone 220-1500')), low.join('\n'));
  assert.match(shortHtml(v('s1'), dir, 'cetus'), /top:220px/);
});

test('a run that stops on variant B leaves out as it was: no new A next to an old B', { skip: !fs.existsSync('/usr/bin/google-chrome') }, async () => {
  const { execFileSync, spawnSync } = await import('child_process');
  const w = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-run-')), out = path.join(w, 'out');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=gray:s=320x180', '-frames:v', '1', path.join(w, 'f.png')]);
  fs.mkdirSync(out); fs.writeFileSync(path.join(out, 'long_A.jpg'), 'old A'); fs.writeFileSync(path.join(out, 'long_B.jpg'), 'old B');
  fs.writeFileSync(path.join(w, 't.json'), JSON.stringify({ long: [v('A'), v('B', { sub: 'x'.repeat(90) })] }));
  const r = spawnSync('node', [new URL('../thumbs.mjs', import.meta.url).pathname, path.join(w, 't.json'), out], { encoding: 'utf8' });
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /long_B/);
  assert.equal(fs.readFileSync(path.join(out, 'long_A.jpg'), 'utf8'), 'old A');
  assert.deepEqual(fs.readdirSync(out).sort(), ['long_A.jpg', 'long_B.jpg']);  // no staging dir left behind
  fs.rmSync(w, { recursive: true, force: true });
});

// --- research ledger plan2 TH6 / TH8: opt-in fields; a variant without them is drawn exactly as before (the hashes are
// of the HTML at 3338af5; an edit of style/themes/cetus.json or of the default layout changes them on purpose; the font's URL
// depends on where the repo is cloned, so it reads as FONT: same HTML at d70d552 and after fonts/ moved into the repo, 2026-11-17)
test('default output unchanged: the HTML of a plain long, a long with icon/fx and a cover is the same as before TH6/TH8', async () => {
  const { createHash } = await import('crypto'); const { pathToFileURL } = await import('url'); const { FONT_URL } = await import('../font.mjs');
  // no-break spaces of keepTogether (2026-11-08) read as spaces: the layout itself is what must not change
  const d = '/tmp/x-golden', norm = (h) => h.split(pathToFileURL(d).href).join('DIR').split(FONT_URL).join('FONT').replaceAll('\u00a0', ' ');
  const sha = (h) => createHash('sha256').update(norm(h)).digest('hex');
  assert.equal(sha(longHtml(v('A'), d, 'cetus')), '453edc9147f57ee1a501124ff71b139c9006256c391e143ca9cc4e3490dd0a9c');
  assert.equal(sha(longHtml(v('B', { side: 'right', icon: 'construction', tag: 'x', fx: -300, fy: -100, fw: 1800 }), d, 'cetus')),
    'eee829ed5cc656a28d15099044c2c98f65d2c9e39cf045169d62e51fd56f7fe0');
  assert.equal(sha(shortHtml(v('s1', { dy: 150 }), d, 'cetus')), '74b0944c6a079bad78e2d441d098a991bc6436fecda9ded09aca2688d5100a35');
});

test('TH6 tone "lift": harder, brighter frame without the colour boost, band and shadow in black; long and cover', () => {
  const h = longHtml(v('A', { tone: 'lift' }), dir, 'cetus');
  assert.match(h, /filter:contrast\(1\.2\) saturate\(1\) brightness\(1\.1\)/);
  assert.match(h, /--panel-rgb:0,0,0/); assert.match(h, /--scrim-rgb:0,0,0/); assert.doesNotMatch(h, /saturate\(1\.15\)/);
  assert.match(shortHtml(v('s1', { tone: 'lift' }), dir, 'cetus'), /--panel-rgb:0,0,0/);
  assert.match(longHtml(v('A'), dir, 'cetus'), /saturate\(1\.15\)/);
  assert.ok(checkThumbs({ long: [v('A', { tone: 'flat' }), v('B')] }, dir).some(b => b.includes('"tone" = "lift"')));
  assert.deepEqual(checkThumbs({ long: [v('A', { tone: 'lift' }), v('B')], shorts: [v('s1', { tone: 'lift' })] }, dir), []);
});

test('TH8 accent "thumb": reads --acc-thumb from the theme (rgb follows), no token = the usual accent', () => {
  const theme = { css: { '--acc': '#6FA7EC', '--acc-rgb': '111,167,236', '--acc-thumb': '#FFD400', '--ink': '#0A1430' } };
  const h = longHtml(v('A', { accent: 'thumb' }), dir, theme);
  assert.match(h, /--acc:#FFD400/); assert.match(h, /--acc-rgb:255,212,0/); assert.doesNotMatch(h, /--acc-thumb/);
  assert.match(longHtml(v('A'), dir, theme), /--acc:#6FA7EC;--acc-rgb:111,167,236/);  // not asked for: unchanged
  assert.match(longHtml(v('A', { accent: 'thumb' }), dir, 'cetus'), /--acc:#6FA7EC/);  // cetus has no --acc-thumb yet (Kamil's colour)
  assert.ok(checkThumbs({ long: [v('A', { accent: 'gold' }), v('B')] }, dir).some(b => b.includes('"accent" = "thumb"')));
});

test('TH8 spec: layout "object" with 1-2 objects or a 3-5 item panel, one arrow at a real target', () => {
  fs.writeFileSync(path.join(dir, 'o.png'), '');
  const flat = (id, more) => ({ id, big: '18%', layout: 'object', ...more });
  const good = [flat('A', { object: { src: 'o.png', w: 0.5 }, arrow: { to: 'object' } }), flat('B', { object: [{ icon: 'terminal' }, { icon: 'file-check', h: 0.4 }], arrow: { to: 'object', i: 1 } }),
    flat('C', { panel: { kind: 'steps', items: ['92%', '40%', '18%'] } }), flat('D', { panel: { kind: 'chart', items: [1, 2, 3, 4, 5].map(n => ({ label: `${n}`, value: n })) } }),
    v('E', { icon: 'construction', arrow: { to: 'icon' } })];
  assert.deepEqual(checkThumbs({ long: good }, dir), []);
  const cases = [
    [flat('A', {}), 'needs "object"'],
    [flat('A', { frame: 'f.png', object: { icon: 'terminal' } }), 'no "frame"'],
    [flat('A', { object: [{ icon: 'terminal' }, { icon: 'terminal' }, { icon: 'file' }] }), '3 objects, at most 2'],
    [flat('A', { object: { icon: 'terminal' }, panel: { kind: 'steps', items: ['a', 'b', 'c'] } }), 'not both'],
    [flat('A', { object: { icon: 'terminal', h: 0.3 } }), '"h" = 0.4'],
    [flat('A', { object: { src: 'o.png', w: 0.3 } }), '"w" = 0.45'],
    [flat('A', { object: { src: 'o.png', icon: 'terminal' } }), 'one of "src" or "icon"'],
    [flat('A', { object: { src: 'none.png' } }), '"src" = an existing image'],
    [flat('A', { panel: { kind: 'steps', items: ['a', 'b'] } }), '"items" = 3-5'],
    [flat('A', { panel: { kind: 'steps', items: ['a', 'b', 'c', 'd', 'e', 'f'] } }), '"items" = 3-5'],
    [flat('A', { panel: { kind: 'grid', items: ['a', 'b', 'c'] } }), '"kind" = steps or chart'],
    [flat('A', { panel: { kind: 'steps', items: ['a', 'b', 'jeden dwa trzy cztery'] } }), 'over 3 words'],
    [flat('A', { panel: { kind: 'chart', items: ['a', 'b', 'c'] } }), 'a chart item'],
    [flat('A', { object: { icon: 'terminal' }, arrow: [{ to: 'object' }, { to: 'object' }] }), 'one arrow, not a list'],
    [flat('A', { object: { icon: 'terminal' }, arrow: { to: 'object', i: 1 } }), 'points at object 1, there are 1'],
    [flat('A', { panel: { kind: 'steps', items: ['a', 'b', 'c'] }, arrow: { to: 'panel' } }), '"arrow" = {"to": "icon"}'],
    [v('A', { arrow: { to: 'icon' } }), 'needs "icon"'],
    [v('A', { object: { icon: 'terminal' } }), 'need "layout": "object"'],
    [v('A', { layout: 'grid' }), '"layout" = "object"'],
  ];
  for (const [bad, want] of cases) {
    const got = checkThumbs({ long: [bad, v('Z')] }, dir);
    assert.ok(got.some(b => b.includes(want)), `missing: ${want}\n${got.join('\n')}`);
  }
  const s = checkThumbs({ long: [v('A'), v('B')], shorts: [v('s1', { layout: 'object', arrow: { to: 'icon' } })] }, dir);
  assert.ok(s.some(b => b.includes('"layout" is for long variants only')) && s.some(b => b.includes('"arrow" is for long variants only')), s.join('\n'));
});

test('TH8 fit: an object drawn small, past the edge or under the words is named; a panel label obeys the 320 px floor', () => {
  const box = (k, x0, y0, x1, y1, fs = 0) => ({ k, x0, y0, x1, y1, fs });
  const fit = { wide: [], bottom: 400 }, big = box('big', 60, 110, 560, 300, 190);
  assert.deepEqual(fitProblems('long_B.jpg', { ...fit, boxes: [big, box('obj', 640, 160, 1220, 560), box('arrow', 300, 350, 620, 400)] }, 720), []);
  const small = fitProblems('long_B.jpg', { ...fit, boxes: [big, box('obj', 800, 260, 1000, 460)] }, 720);
  assert.ok(small.some(b => b.includes('the obj is drawn 200x200 px')), small.join('\n'));
  const over = fitProblems('long_B.jpg', { ...fit, boxes: [big, box('obj', 500, 100, 1100, 500)] }, 720);
  assert.ok(over.some(b => b.includes('"big" overlaps the obj')), over.join('\n'));
  const edge = fitProblems('long_B.jpg', { ...fit, boxes: [box('obj', 700, 100, 1320, 500)] }, 720);
  assert.ok(edge.some(b => b.includes('the obj reaches past the frame edge')), edge.join('\n'));
  const label = fitProblems('long_C.jpg', { ...fit, boxes: [box('panel', 60, 340, 1220, 590), box('panel item 1', 100, 500, 200, 550, 30)] }, 720);
  assert.ok(label.some(b => b.includes('"panel item 1" is 7.5 px')), label.join('\n'));
  assert.ok(!label.some(b => b.includes('overlaps')), label.join('\n'));  // the labels sit inside the panel
});

test('TH6/TH8 render: lift + arrow to the icon, an image object with an arrow, a steps panel; a panel that does not fit stops', { skip: !fs.existsSync('/usr/bin/google-chrome') }, async () => {
  const { execFileSync, spawnSync } = await import('child_process');
  const w = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-th8-')), out = path.join(w, 'out');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=640x360', '-frames:v', '1', path.join(w, 'f.png')]);
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=white:s=480x270', '-frames:v', '1', path.join(w, 'o.png')]);
  const spec = { long: [v('A', { icon: 'construction', arrow: { to: 'icon' }, tone: 'lift', accent: 'thumb', pick: { t: 1, score: 0.9 } }),
    { id: 'B', big: '18%', sub: 'bez błędów', layout: 'object', object: { src: 'o.png', w: 0.45 }, arrow: { to: 'object' }, no_face: true },
    { id: 'C', big: '3 kroki', layout: 'object', panel: { kind: 'steps', items: ['92%', '40%', '18%'] } }] };
  const cli = new URL('../thumbs.mjs', import.meta.url).pathname;
  fs.writeFileSync(path.join(w, 't.json'), JSON.stringify(spec));
  const r = spawnSync('node', [cli, path.join(w, 't.json'), out], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  for (const f of ['long_A.jpg', 'long_B.jpg', 'long_C.jpg']) assert.ok(fs.statSync(path.join(out, f)).size > 1000, f);
  fs.writeFileSync(path.join(w, 't.json'), JSON.stringify({ long: [v('A'), { id: 'C', big: 'x', layout: 'object', panel: { kind: 'steps', items: ['przeglądanie', 'b', 'c', 'd', 'e'] } }] }));
  const r2 = spawnSync('node', [cli, path.join(w, 't.json'), out], { encoding: 'utf8' });
  assert.notEqual(r2.status, 0); assert.match(r2.stderr, /"panel item 1" is \d+ px wider than its column/);
  fs.rmSync(w, { recursive: true, force: true });
});

test('a long "big" shrinks to its column down to the floor; past the floor it still stops', { skip: !fs.existsSync('/usr/bin/google-chrome') }, async () => {
  const { execFileSync, spawnSync } = await import('child_process');
  const w = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-fit-')), out = path.join(w, 'out');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=gray:s=640x360', '-frames:v', '1', path.join(w, 'f.png')]);
  const cli = new URL('../thumbs.mjs', import.meta.url).pathname;
  fs.writeFileSync(path.join(w, 't.json'), JSON.stringify({ long: [v('A', { big: '„Gotowe”?', sub: 'a nic nie działa', icon: 'badge-x' }), v('B')] }));
  const r = spawnSync('node', [cli, path.join(w, 't.json'), out], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);  // 2026-11-08: 445 px too wide at the size by length
  fs.writeFileSync(path.join(w, 't.json'), JSON.stringify({ long: [v('A', { big: 'Niezrozumiałe' }), v('B')] }));
  const r2 = spawnSync('node', [cli, path.join(w, 't.json'), out], { encoding: 'utf8' });
  assert.notEqual(r2.status, 0); assert.match(r2.stderr, /"big" is \d+ px wider than its column/);
  fs.rmSync(w, { recursive: true, force: true });
});

test('no orphan: a one-letter word, a short preposition, "nie" or a short last word stays with its neighbour (no-break space)', () => {
  assert.equal(keepTogether('każdą zmianę od AI'), 'każdą zmianę od\u00a0AI');
  assert.equal(keepTogether('1 zdanie do AI'), '1 zdanie do\u00a0AI');
  assert.equal(keepTogether('zmian od AI bez przeglądu'), 'zmian od\u00a0AI bez\u00a0przeglądu');
  assert.equal(keepTogether('a nic nie działa'), 'a\u00a0nic nie\u00a0działa');
  assert.equal(keepTogether('Nad i pod'), 'Nad\u00a0i\u00a0pod');
  assert.equal(keepTogether('dobrze'), 'dobrze');
  assert.equal(keepTogether('Szlaban tak.'), 'Szlaban\u00a0tak.');  // punctuation does not count (2026-11-08 post p02)
  assert.equal(keepTogether('to działa.'), 'to działa.');
  assert.equal(keepTogether('AI mówi „gotowe”, a nic nie działa'), 'AI mówi „gotowe”, a\u00a0nic nie\u00a0działa');
  assert.equal(keepTogether('w szybę'), 'w\u00a0szybę');
  assert.equal(keepTogether('Kto sprawdza?'), 'Kto sprawdza?');  // a long last word: nothing to keep
  assert.equal(keepTogether(undefined), '');
});
