// node --test gfx/test/*.test.mjs   (theme_lib.mjs rules; render.mjs with and without work/theme.json)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync, execFileSync } from 'child_process';
import { loadTheme } from '../theme_lib.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });
const tmp = (p) => { const d = fs.mkdtempSync(path.join(os.tmpdir(), p)); made.push(d); return d; };
const write = (f, v) => fs.writeFileSync(f, typeof v === 'string' ? v : JSON.stringify(v));

test('loadTheme: no theme.json = null; a theme file gives its tokens and a key that changes with the file', () => {
  const work = tmp('theme-work-'), dir = tmp('theme-dir-'), spec = path.join(work, 'gfx_specs.json');
  assert.equal(loadTheme(spec, dir), null);
  write(path.join(work, 'theme.json'), { theme: 'navy-2' });
  write(path.join(dir, 'navy-2.json'), { css: { '--acc': '#6FA7EC', '--acc-rgb': '111,167,236' } });
  const a = loadTheme(spec, dir);
  assert.equal(a.name, 'navy-2');
  assert.deepEqual(a.css, { '--acc': '#6FA7EC', '--acc-rgb': '111,167,236' });
  assert.match(a.key, /^theme:navy-2:[0-9a-f]{16}$/);
  write(path.join(dir, 'navy-2.json'), { css: { '--acc': '#086AD8' } });
  assert.notEqual(loadTheme(spec, dir).key, a.key);  // an edited theme renders the cards again
});

test('loadTheme: a bad theme.json or theme file stops with a named error', () => {
  const work = tmp('theme-work-'), dir = tmp('theme-dir-'), spec = path.join(work, 'gfx_specs.json');
  const pick = (theme) => write(path.join(work, 'theme.json'), { theme });
  for (const bad of ['../cetus', 'Cetus', '', 7, null]) {
    pick(bad);
    assert.throws(() => loadTheme(spec, dir), /"theme" must be a name/, String(bad));
  }
  for (const raw of ['[]', 'null', '{"theme": "cetus"', '"cetus"']) {
    write(path.join(work, 'theme.json'), raw);
    assert.throws(() => loadTheme(spec, dir), /theme\.json: (not valid JSON|expected a JSON object)/, raw);
  }
  pick('none');
  assert.throws(() => loadTheme(spec, dir), /no theme "none"/);
  pick('t');
  for (const [css, re] of [
    [undefined, /"css" must be an object/], [['#fff'], /"css" must be an object/], ['#fff', /"css" must be an object/],
    [{ acc: '#fff' }, /bad token acc/], [{ '--acc': 5 }, /bad token --acc/],
    [{ '--acc': 'red;}body{display:none' }, /bad token --acc/], [{ '--acc': 'url(https://x.y/a.png)' }, /bad token --acc/],
  ]) {
    write(path.join(dir, 't.json'), { css });
    assert.throws(() => loadTheme(spec, dir), re, JSON.stringify(css));
  }
  write(path.join(dir, 't.json'), '[1]');
  assert.throws(() => loadTheme(spec, dir), /t\.json: expected a JSON object/);
});

// share of pixels within 12 of rgb in the card's last frame (alpha > 0)
const share = (mov, rgb) => {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-sseof', '-0.1', '-i', mov, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
    { maxBuffer: 64 << 20 });  // a 1920x1080 rgba frame is 8 MB
  let hit = 0, seen = 0;
  for (let i = 0; i < raw.length; i += 4) {
    if (raw[i + 3] === 0) continue;
    seen++;
    if (Math.abs(raw[i] - rgb[0]) < 12 && Math.abs(raw[i + 1] - rgb[1]) < 12 && Math.abs(raw[i + 2] - rgb[2]) < 12) hit++;
  }
  return hit / Math.max(1, seen);
};

test('render.mjs: theme.json colors the card, a theme change or removal renders it again', { skip: !fs.existsSync('/usr/bin/google-chrome') && 'no Chrome' }, () => {
  const work = tmp('theme-render-'), specFile = path.join(work, 'gfx_specs.json'), out = path.join(work, 'gfx');
  const mov = path.join(out, 't1.mov'), stamp = `${mov}.key`, themeFile = path.join(work, 'theme.json');
  write(specFile, [{ id: 't1', type: 'kw', dur: 1, text: 'Motyw', sub: 'kolory z pliku' }]);
  const render = () => {
    const r = spawnSync('node', [path.join(GFX, 'render.mjs'), specFile, out], { encoding: 'utf8', timeout: 120000 });
    assert.equal(r.status, 0, r.stderr);
    return fs.statSync(mov).mtimeMs;
  };
  const plain = render();
  assert.ok(!fs.existsSync(stamp));
  assert.ok(share(mov, [0x2d, 0xe2, 0xc4]) > 0.001, 'template accent bar');
  assert.equal(render(), plain);  // nothing changed: reused

  write(themeFile, { theme: 'cetus' });
  const themed = render();
  assert.notEqual(themed, plain);
  assert.match(fs.readFileSync(stamp, 'utf8'), /^\|theme:cetus:[0-9a-f]{16}$/);
  assert.ok(share(mov, [0x6f, 0xa7, 0xec]) > 0.001, 'cetus accent bar');
  assert.equal(share(mov, [0x2d, 0xe2, 0xc4]), 0);
  assert.equal(render(), themed);  // same theme: reused

  fs.rmSync(themeFile);
  assert.notEqual(render(), themed);  // theme removed: back to the template colors
  assert.ok(!fs.existsSync(stamp));
  assert.ok(share(mov, [0x2d, 0xe2, 0xc4]) > 0.001);
});
