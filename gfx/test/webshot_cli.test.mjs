// node --test gfx/test/*.test.mjs   (webshot.mjs / render.mjs as the render runs them; no network: every spec here is
// refused before a connection, or is an own screenshot)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';
import { keyOf } from '../webshot_lib.mjs';
import { capture } from '../webshot.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });
const run = (script, specs, files = {}) => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'webshot-')); made.push(work);
  for (const [f, make] of Object.entries(files)) make(path.join(work, f));
  const specFile = path.join(work, 'gfx_specs.json'); fs.writeFileSync(specFile, JSON.stringify(specs));
  const out = path.join(work, 'gfx');
  const r = spawnSync('node', [path.join(GFX, script), specFile, out], { encoding: 'utf8', timeout: 60000 });
  const web = fs.existsSync(path.join(out, 'web')) ? fs.readdirSync(path.join(out, 'web')) : [];
  return { ...r, work, specFile, web };
};
const png = (f) => execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=white:s=320x200', '-frames:v', '1', f]);

test('a refused card fails loudly and leaves no half capture', () => {
  const bad = [
    [{ id: 'w1', type: 'web', dur: 6, url: 'http://example.com/', find: 'zdanie ze strony' }, /tylko https/],
    [{ id: 'w2', type: 'web', dur: 6, url: 'https://localhost./', find: 'zdanie ze strony' }, /lokalny\/prywatny/],
    [{ id: 'w3', type: 'web', dur: 6, url: 'https://[::ffff:127.0.0.1]:8790/', find: 'zdanie ze strony' }, /lokalny\/prywatny/],
    [{ id: 'w4', type: 'web', dur: 6, img: '../poza.png' }, /sama nazwa pliku/],
    [{ id: 'w6', type: 'web', dur: 6, url: 'https://example.com/' }, /brak "find"/],
  ];
  for (const [sp, why] of bad) {
    const r = run('webshot.mjs', [sp]);
    assert.equal(r.status, 1, sp.id);
    assert.match(r.stderr, new RegExp(`FAILED webshot ${sp.id} `), sp.id);
    assert.match(r.stderr, why, sp.id);
    assert.deepEqual(r.web, [], sp.id);
  }
});

test('an own screenshot is the capture, with its box as the mark', () => {
  const sp = { id: 'w7', type: 'web', dur: 6, img: 'zrzut.png', box: [10, 20, 100, 30], url: 'https://example.com/raport', title: 'Raport' };
  const r = run('webshot.mjs', [sp], { 'zrzut.png': png });
  assert.equal(r.status, 0, r.stderr);
  const key = keyOf(r.specFile, sp);
  assert.deepEqual(r.web.sort(), [`${key}.json`, `${key}.png`]);
  assert.match(r.stdout, new RegExp(`^webshot w7 ${key} img$`, 'm'));  // the line the ADR's metric counts
  const meta = JSON.parse(fs.readFileSync(path.join(r.work, 'gfx', 'web', `${key}.json`), 'utf8'));
  assert.deepEqual([meta.kind, meta.width, meta.height, meta.rects, meta.host, meta.title], ['img', 320, 200, [[10, 20, 100, 30]], 'example.com', 'Raport']);
});

test('a tool stuck past the card limit is killed with the card (even one that ignores SIGTERM)', async (t) => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'webshot-hang-')); made.push(work);
  png(path.join(work, 'zrzut.png'));
  const bin = path.join(work, 'bin'), pidFile = path.join(work, 'ffmpeg.pid'); fs.mkdirSync(bin);
  fs.writeFileSync(path.join(bin, 'ffmpeg'), `#!/bin/sh\ntrap '' TERM\necho $$ > '${pidFile}'\nexec sleep 60\n`, { mode: 0o755 });
  const specFile = path.join(work, 'gfx_specs.json');
  fs.writeFileSync(specFile, JSON.stringify([{ id: 'w9', type: 'web', dur: 6, img: 'zrzut.png' }]));
  const realPath = process.env.PATH; process.env.PATH = `${bin}:${realPath}`;
  const err = t.mock.method(console, 'error', () => {});
  let failed, took;
  try { const t0 = Date.now(); failed = await capture(specFile, path.join(work, 'gfx'), { perCard: 1500 }); took = Date.now() - t0; }
  finally { process.env.PATH = realPath; }
  assert.equal(failed, 1);
  assert.ok(took < 5000, `took ${took} ms`);
  assert.match(err.mock.calls.map(c => c.arguments.join(' ')).join('\n'), /FAILED webshot w9 .*przekroczony czas 1.5 s/);
  assert.deepEqual(fs.readdirSync(path.join(work, 'gfx', 'web')), []);
  const pid = Number(fs.readFileSync(pidFile, 'utf8'));
  await new Promise(ok => setTimeout(ok, 300));
  assert.throws(() => process.kill(pid, 0), { code: 'ESRCH' }, `ffmpeg ${pid} still running`);
});

test('render.mjs stops before any graphic when a capture fails', () => {
  const r = run('render.mjs', [{ id: 'k1', type: 'kw', dur: 2, text: 'x' }, { id: 'w8', type: 'web', dur: 6, url: 'http://example.com/', find: 'zdanie ze strony' }]);
  assert.equal(r.status, 1);
  assert.match(r.stderr, /FAILED webshot w8 /); assert.match(r.stderr, /FAILED gfx: page capture/);
  assert.equal(fs.existsSync(path.join(r.work, 'gfx', 'k1.mov')), false);
});

test('render.mjs: a web card renders, is reused while nothing changes, and renders again after an edit', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'webshot-render-')); made.push(work);
  png(path.join(work, 'zrzut.png'));
  const specFile = path.join(work, 'gfx_specs.json'), out = path.join(work, 'gfx'), mov = path.join(out, 'w9.mov');
  const render = (sp) => {
    fs.writeFileSync(specFile, JSON.stringify([sp]));
    const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, out], { encoding: 'utf8', timeout: 120000 });
    assert.equal(r.status, 0, r.stderr);
    return fs.statSync(mov).mtimeMs;
  };
  const sp = { id: 'w9', type: 'web', dur: 2.7, img: 'zrzut.png', box: [10, 20, 100, 30], url: 'https://example.com/r' };
  const first = render(sp);
  const dur = Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mov], { encoding: 'utf8' }));
  assert.ok(Math.abs(dur - 2.7) < 0.05, String(dur));
  assert.equal(render(sp), first);  // unchanged: the .mov is reused
  assert.notEqual(render({ ...sp, src: 'Źródło: inny podpis' }), first);  // a caption edit renders again
});

test('render.mjs: a compact vertical card stays above the face', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const box = (sp) => {
    const r = run('render.mjs', [sp]);
    assert.equal(r.status, 0, r.stderr);
    const mov = path.join(r.work, 'gfx', `${sp.id}.mov`);
    const log = spawnSync('ffmpeg', ['-v', 'info', '-sseof', '-0.2', '-i', mov, '-vf', 'alphaextract,cropdetect=limit=0.1:round=2:reset=1',
      '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
    const [, h, y] = [...log.matchAll(/crop=\d+:(\d+):\d+:(\d+)/g)].pop().slice(0, 3).map(Number);
    return y + h;  // lowest painted row
  };
  const sp = { type: 'kw', dur: 1, text: 'Pytanie 1', sub: 'Kto użyje tego w poniedziałek o 8?', icon: 'clock', canvas: 'v' };
  const compact = box({ ...sp, id: 'c1', compact: true });
  assert.ok(compact < 420, `compact card reaches ${compact} px`);
  assert.ok(box({ ...sp, id: 'c2' }) > compact + 100);  // the default card is the tall one
});
