// node gfx/scene_check.mjs <specs.json> [id ...]: every "scene" card laid out in Chrome (no frames rendered) and checked for
// pieces whose drawn boxes (labels included, they overflow the piece) cover each other while both are on screen.
// Film 2 long, s14_hooki (2026-11-04): three node labels ran into each other ("polecpokażdej zmianie plikugdy") and nobody saw
// it until a contact sheet. Exit 1 with every clash named; 0 when clean. Fast: one page, no screenshots.
// Cards with "motion": "tokens" also get the motion lint (gfx/motion_tokens.mjs): no entrance that eases both ways, no
// stagger step over 12 frames. Cards without it keep the timings from before tokens and are only counted.
import { chromium } from 'playwright-core';
import fs from 'fs'; import path from 'path';
import { resolveExtends, scene } from './scene_lib.mjs';
import { motionProblems, staggerProblems } from './motion_tokens.mjs';
import { esc, icon } from './html_lib.mjs';
import { isMain } from './cli.mjs';

// pieces meant to sit on others: a stamp lands on a card, a check or ring marks it, a cursor points at it, a line joins them
export const OVERLAY_KINDS = new Set(['stamp', 'check', 'ring', 'cursor', 'line']);
const TEXT_KINDS = new Set(['chip', 'text', 'say', 'stat', 'steps', 'toggle', 'node', 'you']);  // pieces that carry words
const TOUCH = 8;  // px: borders that touch or graze are fine (a sliver, test)

// seconds a piece is on screen: from its first moment to "gone" (or the end of the card)
export function window_(e, dur) {
  const ats = [e.at, ...(e.words ?? []).map(w => w[1]), ...(e.msgs ?? []).map(m => m.at), ...(e.items ?? []).map(m => m?.at)]
    .filter(v => typeof v === 'number');
  return [ats.length ? Math.min(...ats) : 0, typeof e.gone === 'number' ? e.gone : dur];
}

// the motion lint for one card (no browser): problems for a "tokens" card, [] for the others
export function motionLint(sp) {
  return sp.motion === 'tokens' ? [...motionProblems(scene(sp, esc, icon)).map(p => `${sp.id}: ${p}`), ...staggerProblems(sp)] : [];
}

// rects: [{i, x, y, w, h}] (world px, as laid out); returns the clashing pairs as text. A pair clashes when both are on screen
// together and the overlap covers more than `share` of the smaller box.
export function clashes(sp, rects, share = 0.12) {
  const out = [];
  const name = i => `${sp.els[i].id ?? `#${i}`} (${sp.els[i].k}${sp.els[i].text || sp.els[i].t ? ` "${String(sp.els[i].text ?? sp.els[i].t).slice(0, 24)}"` : ''})`;
  for (let a = 0; a < rects.length; a++) for (let b = a + 1; b < rects.length; b++) {
    const A = rects[a], B = rects[b], ea = sp.els[A.i], eb = sp.els[B.i];
    const [a0, a1] = window_(ea, sp.dur), [b0, b1] = window_(eb, sp.dur);
    if (a1 <= b0 || b1 <= a0) continue;
    const ix = Math.min(A.x + A.w, B.x + B.w) - Math.max(A.x, B.x), iy = Math.min(A.y + A.h, B.y + B.h) - Math.max(A.y, B.y);
    if (ix <= 0 || iy <= 0) continue;
    // a stamp lands on its card, but never on another piece's words (2026-11-08: BLOKOWANE over "okienka", NIE PRZEMYCISZ
    // over the risk chip, both missed because every overlay was skipped)
    const stampOnWords = (ea.k === 'stamp' && TEXT_KINDS.has(eb.k)) || (eb.k === 'stamp' && TEXT_KINDS.has(ea.k));
    if (stampOnWords && ix > TOUCH && iy > TOUCH) { out.push(`${sp.id}: ${name(A.i)} covers ${name(B.i)} (${Math.round(ix)}x${Math.round(iy)} px, a stamp on words)`); continue; }
    if (OVERLAY_KINDS.has(ea.k) || OVERLAY_KINDS.has(eb.k)) continue;
    const small = Math.min(A.w * A.h, B.w * B.h);
    // two pieces with words: any overlap cuts a word (Kamil 2026-11-05: "nałożyły się na siebie elementy", a chip 5 % over
    // the next one, under the share rule)
    const words = TEXT_KINDS.has(ea.k) && TEXT_KINDS.has(eb.k) && ix > TOUCH && iy > TOUCH;
    if (words || (small > 0 && (ix * iy) / small > share)) out.push(`${sp.id}: ${name(A.i)} covers ${name(B.i)} (${Math.round(ix)}x${Math.round(iy)} px)`);
  }
  return out;
}

// drawing accuracy (Kamil 2026-11-08: "nie w tym miejscu co trzeba rysujesz np te podkreslenie w kolku"): ring and line
// boxes are typed by hand in the plan, so they are measured against the laid-out words. texts: [{i, x, y, w, h}] = one
// rect per drawn line of words (world px). A ring either holds a line of words whole or stays off it, and holds something;
// a line starts and ends on a piece, not in the air.
const NEAR = 40, SLACK = 12;
export function drawProblems(sp, rects, texts) {
  const out = [], on = (e, f) => { const [a0, a1] = window_(e, sp.dur), [b0, b1] = window_(f, sp.dur); return a0 < b1 && b0 < a1; };
  const label = i => `${sp.els[i].id ?? `#${i}`} (${sp.els[i].k})`;
  sp.els.forEach((e, i) => {
    if (e.k === 'ring') {
      const R = { x: e.x - SLACK, y: e.y - SLACK, r: e.x + e.w + SLACK, b: e.y + e.h + SLACK };
      let held = 0;
      for (const T of texts) {
        if (T.i === i || !on(e, sp.els[T.i])) continue;
        const ix = Math.min(R.r, T.x + T.w) - Math.max(R.x, T.x), iy = Math.min(R.b, T.y + T.h) - Math.max(R.y, T.y);
        if (ix <= TOUCH || iy <= TOUCH) continue;
        if (T.x >= R.x && T.x + T.w <= R.r && T.y >= R.y && T.y + T.h <= R.b) held++;
        else out.push(`${sp.id}: ring ${label(i)} cuts the words of ${label(T.i)} (${Math.round(ix)}x${Math.round(iy)} px): circle the whole line or move it`);
      }
      const box = rects.some(B => B.i !== i && !OVERLAY_KINDS.has(sp.els[B.i].k) && on(e, sp.els[B.i])
        && B.x >= R.x && B.y >= R.y && B.x + B.w <= R.r && B.y + B.h <= R.b);
      if (!held && !box) out.push(`${sp.id}: ring ${label(i)} circles nothing (no line of words, no piece inside ${e.x},${e.y} ${e.w}x${e.h})`);
    }
    if (e.k === 'line' && !e.free && Array.isArray(e.from) && Array.isArray(e.to)) {  // "free": a road or a time axis, not a link
      for (const [end, P] of [['from', e.from], ['to', e.to]]) {
        const d = Math.min(Infinity, ...rects.filter(B => B.i !== i && sp.els[B.i].k !== 'line' && on(e, sp.els[B.i]))
          .map(B => Math.hypot(Math.max(0, B.x - P[0], P[0] - B.x - B.w), Math.max(0, B.y - P[1], P[1] - B.y - B.h))));
        if (d > NEAR) out.push(`${sp.id}: line ${label(i)} "${end}" ${P.join(',')} ends ${d === Infinity ? 'with no piece on screen' : `${Math.round(d)} px from any piece`}: put it on its piece`);
      }
    }
  });
  return out;
}

async function main() {
  const [specFile, ...only] = process.argv.slice(2);
  if (!specFile) { console.error('usage: node gfx/scene_check.mjs <specs.json> [id ...]'); process.exit(2); }
  // "extends" (S11) on the whole file first: the scene it goes on from may be filtered out by [id ...]
  const specs = resolveExtends(JSON.parse(fs.readFileSync(specFile, 'utf8'))).filter(s => s.type === 'scene' && (!only.length || only.includes(s.id)));
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
  const bad = [], motion = specs.flatMap(motionLint), legacy = specs.filter(s => s.motion !== 'tokens').length;
  try {
    for (const sp of specs) {
      const v = sp.canvas === 'v';
      const page = await browser.newPage({ viewport: v ? { width: 1080, height: 1920 } : { width: 2560, height: 1440 } });
      await page.goto(new URL('./template.html', import.meta.url).href);
      if (v) await page.evaluate(() => document.documentElement.classList.add('v'));
      await page.evaluate(h => { document.getElementById('root').innerHTML = h; }, scene(sp, esc, icon));
      await page.evaluate(() => document.fonts.ready);
      // no animation: every piece in its laid-out place (the pieces' keyframes only move them in and out of it)
      const { rects, texts } = await page.evaluate(() => {
        for (const a of document.getAnimations()) a.cancel();
        const world = document.querySelector('.scene .world'), wr = world.getBoundingClientRect();
        const rects = [...world.querySelectorAll(':scope > .p, :scope > svg.ln')].map((el, i) => {
          if (el.tagName.toLowerCase() === 'svg') return null;
          const boxes = [el, ...el.querySelectorAll('*')].map(n => n.getBoundingClientRect()).filter(r => r.width > 0 && r.height > 0);
          if (!boxes.length) return null;
          const x0 = Math.min(...boxes.map(r => r.left)), y0 = Math.min(...boxes.map(r => r.top));
          const x1 = Math.max(...boxes.map(r => r.right)), y1 = Math.max(...boxes.map(r => r.bottom));
          return { i, x: x0 - wr.left, y: y0 - wr.top, w: x1 - x0, h: y1 - y0 };
        }).filter(Boolean);
        // one rect per drawn line of words, per piece (ranges over its text nodes)
        const texts = [];
        [...world.querySelectorAll(':scope > .p, :scope > svg.ln')].forEach((el, i) => {
          if (el.tagName.toLowerCase() === 'svg') return;
          const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
          for (let n = walk.nextNode(); n; n = walk.nextNode()) {
            if (!n.textContent.trim()) continue;
            const rg = document.createRange(); rg.selectNodeContents(n);
            for (const r of rg.getClientRects()) if (r.width > 2 && r.height > 2) texts.push({ i, x: r.left - wr.left, y: r.top - wr.top, w: r.width, h: r.height });
          }
        });
        return { rects, texts };
      });
      // kept pieces of an "extends" scene are drawn first (scene_lib scene()): the measured index runs over both lists
      const all = sp._held ? { ...sp, els: [...sp._held, ...sp.els] } : sp;
      bad.push(...clashes(all, rects), ...drawProblems(all, rects, texts));
      await page.close();
    }
  } finally { await browser.close(); }
  for (const b of bad) console.log(`CLASH ${b}`);
  for (const m of motion) console.log(`MOTION ${m}`);
  console.log(`scene_check: ${specs.length} scenes, ${bad.length} clashes, ${motion.length} motion problems (${legacy} without "motion": "tokens", not linted)`);
  process.exit(bad.length || motion.length ? 1 : 0);
}

if (isMain(import.meta.url)) await main();
