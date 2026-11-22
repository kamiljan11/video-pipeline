// node --test gfx/test/*.test.mjs   (a check mark turns into an X: "x_at", docs/designs/2026-11-05-visual-upgrade.md item 4)
import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { checkScene, scene } from '../scene_lib.mjs';
import { esc, icon } from '../html_lib.mjs';

const sc = el => ({ id: 'm', type: 'scene', dur: 6, cam: 'none', els: [{ k: 'check', id: 'ck', x: 400, y: 400, size: 200, at: 0.5, ...el }] });

test('without x_at the check is drawn as before; with it the tick and the X share one path shape (M L M L)', () => {
  const plain = scene(sc({}), esc, icon), morph = scene(sc({ x_at: 2 }), esc, icon);
  assert.doesNotMatch(plain, /d:path|@keyframes u\w+x/);
  const from = /<path d="(M[^"]+)"[^>]*u\w+x \.32s/.exec(morph)?.[1], to = /d:path\("([^"]+)"\)/.exec(morph)?.[1];
  assert.ok(from && to, morph.slice(0, 400));
  const cmds = d => d.replace(/[^ML]/g, '');
  assert.equal(cmds(from), 'MLML');
  assert.equal(cmds(to), cmds(from), 'same commands = CSS can interpolate "d"');
  assert.match(morph, /stroke:#ff5f57/);
});

test('x_at before the tick has drawn is named by checkScene', () => {
  assert.deepEqual(checkScene(sc({ x_at: 2 })), []);
  assert.ok(checkScene(sc({ x_at: 0.8 })).some(m => /"x_at" = after the tick has drawn/.test(m)));
  assert.ok(checkScene(sc({ x_at: 9 })).some(m => /"x_at" = seconds 0..dur/.test(m)));
});

test('in Chrome: halfway through the morph the path is between the tick and the X, at the end it is the red X', async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
  try {
    const page = await browser.newPage({ viewport: { width: 2560, height: 1440 } });
    await page.goto(new URL('../template.html', import.meta.url).href);
    await page.evaluate(h => { document.getElementById('root').innerHTML = h; }, scene(sc({ x_at: 2 }), esc, icon));
    const at = t => page.evaluate(t => {
      document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
      const p = document.querySelector('.check path, svg path[style*="x .32s"]'), cs = getComputedStyle(p);
      return { d: cs.d, stroke: cs.stroke };
    }, t);
    const [before, mid, end] = [await at(1.9), await at(2.12), await at(2.6)];
    assert.notEqual(mid.d, before.d);
    assert.notEqual(mid.d, end.d);
    assert.equal(end.stroke, 'rgb(255, 95, 87)');
  } finally { await browser.close(); }
});
