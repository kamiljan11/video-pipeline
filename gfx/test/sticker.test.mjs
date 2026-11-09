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

// "toon": our own animated drawing (gfx/toons) instead of a meme picture; CSS keyframes are seeked frame by frame
const toons = path.join(work, 'toons'); fs.mkdirSync(toons);
fs.writeFileSync(path.join(toons, 'slide.svg'), '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><style>'
  + '.m{animation:sl 2s linear both}@keyframes sl{from{transform:translateX(0)}to{transform:translateX(200px)}}</style>'
  + '<rect class="m" x="0" y="0" width="200" height="400" fill="#f00"/></svg>');
fs.writeFileSync(path.join(toons, 'evil.svg'), '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><script>alert(1)</script></svg>');
fs.writeFileSync(path.join(toons, 'link.svg'), '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><image href="https://x.y/a.png"/></svg>');
const VB = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"';
const sneaky = {  // every way out of the drawing the check must stop, beside <script> and a double-quoted href
  link1: `${VB}><image href='https://x.y/a.png'/></svg>`, link2: `${VB}><image href=https://x.y/a.png /></svg>`,
  link3: `${VB}><image xlink:href = '//x.y/a'/></svg>`, css1: `${VB}><style>.a{fill:url(https://x.y/p.svg)}</style></svg>`,
  css2: `${VB}><style>@import 'a.css';</style></svg>`, fo: `${VB}><foreignObject/></svg>`, handler: `${VB}><rect onload="x()"/></svg>`,
};
for (const [n, svg] of Object.entries(sneaky)) fs.writeFileSync(path.join(toons, `${n}.svg`), svg);
fs.writeFileSync(path.join(toons, 'novb.svg'), '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>');
fs.writeFileSync(path.join(toons, 'rootstyle.svg'), `${VB} style="width:1px"><rect/></svg>`);
fs.writeFileSync(path.join(toons, 'inner.svg'), `${VB}><defs><linearGradient id="g"/></defs><rect fill="url(#g)"/><use href='#g'/></svg>`);
const renderToon = specs => {
  const specFile = path.join(work, `${specs[0].id}.json`); fs.writeFileSync(specFile, JSON.stringify(specs));
  return spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000, env: { ...process.env, VP_TOONS: toons } });
};

test('a toon sits beside the speaker and moves frame by frame', CHROME, () => {
  const r = renderToon([{ id: 't1', type: 'sticker', toon: 'slide', dur: 3, at: [0] }]);
  assert.equal(r.status, 0, r.stderr);
  const mov = path.join(work, 'gfx', 't1.mov'), early = frameAt(mov, 0.6), late = frameAt(mov, 2.2);
  const x = 1620 + 615, y = 150 + 400;  // right part of the 820 px box: the red bar reaches it only after sliding
  assert.ok(early(x, y)[3] < 40, `the bar is already on the right at 0.6 s: ${early(x, y)}`);
  assert.ok(late(x, y)[0] > 180 && late(x, y)[3] > 200, `the bar did not slide right by 2.2 s: ${late(x, y)}`);
  for (const px of [900, 1150, 1450]) assert.equal(late(px, 500)[3], 0, `the speaker's middle is covered at x ${px}`);
});

test('a toon with a script, an outside link or no file stops by name', () => {
  for (const [id, toon, msg] of [['t2', 'evil', /t2.*drawing and CSS only/s], ['t3', 'link', /t3.*drawing and CSS only/s], ['t4', 'nope', /t4.*toon "nope": not in/s]]) {
    const r = renderToon([{ id, type: 'sticker', toon, dur: 2 }]);
    assert.notEqual(r.status, 0); assert.match(r.stderr, msg);
  }
});

test('every way out of a toon stops by name, links inside the drawing pass', () => {
  for (const n of Object.keys(sneaky)) {
    const r = renderToon([{ id: `x_${n}`, type: 'sticker', toon: n, dur: 2 }]);
    assert.notEqual(r.status, 0, `${n} passed`); assert.match(r.stderr, new RegExp(`x_${n}.*drawing and CSS only`, 's'));
  }
  for (const [n, msg] of [['novb', /viewBox="0 0 W H"/], ['rootstyle', /no style="" on the root/]]) {
    const r = renderToon([{ id: `y_${n}`, type: 'sticker', toon: n, dur: 2 }]);
    assert.notEqual(r.status, 0); assert.match(r.stderr, msg);
  }
  for (const [id, sp, msg] of [['z1', { side: 'top' }, /"side" = "right" or "left"/], ['z2', { canvas: 'v' }, /16:9/],
    ['z3', { text: [1] }, /list of strings/], ['z4', { at: [5] }, /"at" = seconds/]]) {
    const r = renderToon([{ id, type: 'sticker', toon: 'inner', dur: 2, ...sp }]);
    assert.notEqual(r.status, 0); assert.match(r.stderr, msg);
  }
});

test('a toon linking only inside itself renders', CHROME, () => {
  const r = renderToon([{ id: 'in1', type: 'sticker', toon: 'inner', dur: 1 }]);
  assert.equal(r.status, 0, r.stderr);
});

test('the toons in the repo pass the drawing-only check', CHROME, () => {
  for (const f of fs.readdirSync(path.join(GFX, 'toons')).filter(n => n.endsWith('.svg'))) {
    const id = `repo_${f.slice(0, -4)}`, specFile = path.join(work, `${id}.json`);
    fs.writeFileSync(specFile, JSON.stringify([{ id, type: 'sticker', toon: f.slice(0, -4), dur: 1 }]));
    const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, path.join(work, 'gfx')], { encoding: 'utf8', timeout: 120000 });
    assert.equal(r.status, 0, `${f}: ${r.stderr}`);
  }
});

test('"cut": true shows the character without its rectangle; a missing or stale cut-out stops by name', CHROME, () => {
  // cut.png: the picture's left half keeps only a red square in its middle, the rest transparent (cutout.py writes the same shape)
  const sq = 'between(X,50,149)*between(Y,150,249)*255';  // drawbox would leave the alpha at 0
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=400x400', '-vf',
    `format=rgba,geq=r='${sq}':g=0:b=0:a='${sq}'`, '-frames:v', '1', path.join(lib, 'cutme.cut.png')]);
  fs.copyFileSync(path.join(lib, 'rg.png'), path.join(lib, 'cutme.png'));
  const sha = execFileSync('sha256sum', [path.join(lib, 'cutme.png')], { encoding: 'utf8' }).split(' ')[0];
  const meta = { ...pic, img: 'cutme.png', sticker: [[0, 0, 0.5, 1]] };
  fs.writeFileSync(path.join(lib, 'cutme.json'), JSON.stringify({ ...meta, cut: { file: 'cutme.cut.png', method: 'flat', src_sha256: sha } }));
  const r = render([{ id: 'c1', type: 'sticker', dur: 2, meme: 'cutme', cut: true }]);
  assert.equal(r.status, 0, r.stderr);
  const f = frameAt(path.join(work, 'gfx', 'c1.mov'), 1.0);
  // the right box (STICKER_BOX right: x 1620, w 820): the crop is 200x400, the square sits in its middle third
  let red = 0, clear = 0;
  for (let y = 150; y < 1300; y += 10) for (let x = 1620; x < 2440; x += 10) {
    const [rr, g, b, a] = f(x, y);
    if (a > 200 && rr > 180 && g < 80 && b < 80) red++;
    if (a === 0) clear++;
  }
  assert.ok(red > 50, `the red square shows (${red} samples)`);
  assert.ok(clear > red * 3, `around it the card is see-through, not a white rectangle (${clear} clear vs ${red} red)`);
  fs.writeFileSync(path.join(lib, 'cutme.json'), JSON.stringify({ ...meta, cut: { file: 'cutme.cut.png', method: 'flat', src_sha256: 'x' } }));
  assert.match(render([{ id: 'c2', type: 'sticker', dur: 2, meme: 'cutme', cut: true }]).stderr + '', /"cut": made from another picture .*cutout\.py cutme/);
  fs.writeFileSync(path.join(lib, 'cutme.json'), JSON.stringify(meta));
  assert.match(render([{ id: 'c3', type: 'sticker', dur: 2, meme: 'cutme', cut: true }]).stderr + '', /"cut": no cut-out yet/);
  assert.match(render([{ id: 'c4', type: 'sticker', dur: 2, meme: 'rg', cut: 'yes' }]).stderr + '', /"cut" = true/);
});
