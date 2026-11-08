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
    if (OVERLAY_KINDS.has(ea.k) || OVERLAY_KINDS.has(eb.k)) continue;
    const [a0, a1] = window_(ea, sp.dur), [b0, b1] = window_(eb, sp.dur);
    if (a1 <= b0 || b1 <= a0) continue;
    const ix = Math.min(A.x + A.w, B.x + B.w) - Math.max(A.x, B.x), iy = Math.min(A.y + A.h, B.y + B.h) - Math.max(A.y, B.y);
    if (ix <= 0 || iy <= 0) continue;
    const small = Math.min(A.w * A.h, B.w * B.h);
    // two pieces with words: any overlap cuts a word (Kamil 2026-11-05: "nałożyły się na siebie elementy", a chip 5 % over
    // the next one, under the share rule)
    const words = TEXT_KINDS.has(ea.k) && TEXT_KINDS.has(eb.k) && ix > TOUCH && iy > TOUCH;
    if (words || (small > 0 && (ix * iy) / small > share)) out.push(`${sp.id}: ${name(A.i)} covers ${name(B.i)} (${Math.round(ix)}x${Math.round(iy)} px)`);
  }
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
      const rects = await page.evaluate(() => {
        for (const a of document.getAnimations()) a.cancel();
        const world = document.querySelector('.scene .world'), wr = world.getBoundingClientRect();
        return [...world.querySelectorAll(':scope > .p, :scope > svg.ln')].map((el, i) => {
          if (el.tagName.toLowerCase() === 'svg') return null;
          const boxes = [el, ...el.querySelectorAll('*')].map(n => n.getBoundingClientRect()).filter(r => r.width > 0 && r.height > 0);
          if (!boxes.length) return null;
          const x0 = Math.min(...boxes.map(r => r.left)), y0 = Math.min(...boxes.map(r => r.top));
          const x1 = Math.max(...boxes.map(r => r.right)), y1 = Math.max(...boxes.map(r => r.bottom));
          return { i, x: x0 - wr.left, y: y0 - wr.top, w: x1 - x0, h: y1 - y0 };
        }).filter(Boolean);
      });
      // kept pieces of an "extends" scene are drawn first (scene_lib scene()): the measured index runs over both lists
      bad.push(...clashes(sp._held ? { ...sp, els: [...sp._held, ...sp.els] } : sp, rects));
      await page.close();
    }
  } finally { await browser.close(); }
  for (const b of bad) console.log(`CLASH ${b}`);
  for (const m of motion) console.log(`MOTION ${m}`);
  console.log(`scene_check: ${specs.length} scenes, ${bad.length} clashes, ${motion.length} motion problems (${legacy} without "motion": "tokens", not linted)`);
  process.exit(bad.length || motion.length ? 1 : 0);
}

if (process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname) await main();
