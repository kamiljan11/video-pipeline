// node --test gfx/test/*.test.mjs   (pieces attached to ids: gfx/anchor_lib.mjs, docs/designs/2026-11-05-visual-upgrade.md item 2)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawnSync } from 'child_process';
import { chromium } from 'playwright-core';
import { attached, edgePoint, hasAnchors, opener, place, resolveAnchors } from '../anchor_lib.mjs';
import { esc, icon } from '../html_lib.mjs';

const GFX = path.resolve(import.meta.dirname, '..');
const made = [];
test.after(() => { for (const d of made) fs.rmSync(d, { recursive: true, force: true }); });

const SCENE = () => ({ id: 's', type: 'scene', dur: 6, els: [
  { k: 'win', id: 'md', x: 200, y: 200, w: 900, h: 520, title: 'plan.md', rows: ['~80', '~55', '~70'] },
  { k: 'node', id: 'db', x: 1700, y: 300, text: 'baza' },
  { k: 'line', from: 'md', to: 'db', at: 1 },
  { k: 'ring', on: 'md.1', at: 2 },
  { k: 'stamp', on: 'db', text: 'OK', at: 3 },
] });

test('a line leaves the box towards the other one, a gap off its edge', () => {
  assert.deepEqual(edgePoint({ x: 0, y: 0, w: 100, h: 50 }, 300, 25), [114, 25]);
  assert.deepEqual(edgePoint({ x: 0, y: 0, w: 100, h: 50 }, 50, 400), [50, 64]);
  const l = place({ k: 'line', from: 'a', to: [600, 25] }, { a: { x: 0, y: 0, w: 100, h: 50 } });
  assert.deepEqual([l.from, l.to, l._from], [[114, 25], [600, 25], 'a']);  // a point stays a point
});

test('a ring takes its target box, a stamp lands on its upper right, a cursor goes to the centre', () => {
  const boxes = { 'md.1': { x: 220, y: 300, w: 860, h: 60 }, db: { x: 1700, y: 300, w: 200, h: 200 } };
  assert.deepEqual((({ x, y, w, h }) => ({ x, y, w, h }))(place({ k: 'ring', on: 'md.1' }, boxes)), boxes['md.1']);
  const st = place({ k: 'stamp', on: 'db', text: 'OK' }, boxes, { w: 100, h: 60 });
  assert.deepEqual([st.x, st.y, st.on, st._on], [1800, 255, undefined, 'db']);
  assert.deepEqual(place({ k: 'cursor', from: [0, 0], to: 'db' }, boxes).to, [1800, 400]);
  assert.throws(() => place({ k: 'ring', on: 'nope' }, boxes), /"nope": no piece with this id on the scene/);
  assert.throws(() => place({ k: 'line', from: 'db' }, boxes), /line: "to" = \[x, y\] or a piece id, got undefined/);
});

test('only pieces given an id string are attached; a scene without them is left alone', () => {
  assert.equal(attached({ k: 'line', from: [0, 0], to: [1, 1] }), false);
  assert.equal(attached({ k: 'ring', on: 'md' }), true);
  assert.equal(attached({ k: 'chip', on: 'md' }), false);  // "on" is a camera word elsewhere, not an anchor for a chip
  assert.equal(hasAnchors({ type: 'scene', els: [{ k: 'chip', x: 1, y: 1 }] }), false);
  assert.equal(hasAnchors({ type: 'kw', els: [{ k: 'ring', on: 'md' }] }), false);
});

test('in Chrome: the ring circles the measured row, the line joins the two pieces, the stamp sits on its node', async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
  try {
    const specs = [SCENE(), { id: 'k', type: 'kw', text: 'x' }];
    await resolveAnchors(specs, opener(browser), esc, icon);
    const [win, node, line, ring, stamp] = specs[0].els;
    assert.ok(ring.y > win.y + 40 && ring.y + ring.h < win.y + win.h, `row 1 inside the window body: ${JSON.stringify(ring)}`);
    assert.ok(ring.w > 300 && ring.h > 10 && ring.h < 140, `a row, not the whole window: ${JSON.stringify(ring)}`);
    assert.ok(line.from[0] > win.x + win.w && line.from[0] < win.x + win.w + 40, `leaves the window's right edge: ${line.from}`);
    assert.ok(line.to[0] < node.x && line.to[0] > node.x - 40, `reaches the node's left edge: ${line.to}`);
    assert.ok(stamp.x > node.x && stamp.y < node.y, `on the node's upper right, above its middle: ${stamp.x},${stamp.y}`);
    assert.deepEqual(specs[1], { id: 'k', type: 'kw', text: 'x' });
    const bad = SCENE(); bad.els[3].on = 'md.9';
    await assert.rejects(resolveAnchors([bad], opener(browser), esc, icon), /"s": attached piece: "md.9": no piece with this id/);
  } finally { await browser.close(); }
});

test('in Chrome: a ring on a text row takes the text, not the full window width (a highlight band is left out)', async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
  try {
    const sp = { id: 't', type: 'scene', dur: 6, els: [
      { k: 'win', id: 'md', x: 200, y: 200, w: 900, h: 520, title: 'plan.md', rows: ['Krok 1', { t: 'Krok 2: montaż', hl: true }] },
      { k: 'ring', on: 'md.1', at: 2 }, { k: 'ring', on: 'md.0', shape: 'underline', at: 2 },
    ] };
    await resolveAnchors([sp], opener(browser), esc, icon);
    const [win, box, under] = sp.els;
    assert.ok(box.w > 150 && box.w < win.w / 2, `as wide as "Krok 2: montaż": ${JSON.stringify(box)}`);
    assert.ok(under.w > 60 && under.w < box.w, `"Krok 1" is shorter: ${JSON.stringify(under)}`);
    assert.ok(box.x >= win.x && box.x < win.x + 60, `starts where the text starts: ${box.x}`);
  } finally { await browser.close(); }
});

test('scene_check measures the attached scene, a stamp on a missing id stops it by name', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'anchor-')); made.push(d);
  const f = path.join(d, 'specs.json');
  fs.writeFileSync(f, JSON.stringify([SCENE()]));
  const ok = spawnSync('node', [path.join(GFX, 'scene_check.mjs'), f], { encoding: 'utf8' });
  assert.doesNotMatch(ok.stdout + ok.stderr, /attached piece|floats/, ok.stdout + ok.stderr);
  const bad = SCENE(); bad.els[4].on = 'ghost'; fs.writeFileSync(f, JSON.stringify([bad]));
  const r = spawnSync('node', [path.join(GFX, 'scene_check.mjs'), f], { encoding: 'utf8' });
  assert.equal(r.status, 1);
  assert.match(r.stdout, /CLASH "s": attached piece: "ghost": no piece with this id/);
});

test('a ring placed by hand coordinates is refused, a ring "on" a piece is not', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'anchor-')); made.push(d);
  const f = path.join(d, 'specs.json'), hand = SCENE();
  hand.els[3] = { k: 'ring', x: 220, y: 300, w: 860, h: 60, at: 2 };
  hand.els[2] = { k: 'line', from: [1110, 400], to: [1690, 400], at: 1 };
  fs.writeFileSync(f, JSON.stringify([hand]));
  const r = spawnSync('node', [path.join(GFX, 'scene_check.mjs'), f], { encoding: 'utf8' });
  assert.equal(r.status, 1);
  assert.match(r.stdout, /CLASH s: els\[3\] \(ring\) placed by hand at x\/y: give it "on"/);
  assert.match(r.stdout, /CLASH s: els\[2\] \(line\) joins two hand points/);
});
