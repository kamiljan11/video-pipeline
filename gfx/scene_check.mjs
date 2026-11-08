// node gfx/scene_check.mjs <specs.json> [id ...]: every "scene" card laid out in Chrome (no frames rendered) and checked for
// pieces whose drawn boxes (labels included, they overflow the piece) cover each other while both are on screen.
// Film 2 long, s14_hooki (2026-11-04): three node labels ran into each other ("polecpokażdej zmianie plikugdy") and nobody saw
// it until a contact sheet. Exit 1 with every clash named; 0 when clean. Fast: one page, no screenshots.
// Cards with "motion": "tokens" also get the motion lint (gfx/motion_tokens.mjs): no entrance that eases both ways, no
// stagger step over 12 frames. Cards without it keep the timings from before tokens and are only counted.
import { chromium } from 'playwright-core';
import fs from 'fs'; import path from 'path';
import { camKeyframes, colFollow, drawnEls, resolveExtends, scene, sceneFit, sceneSafe, soloKeys, zoomStops } from './scene_lib.mjs';
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
const NEAR = 40, STROKE = 4;  // px: a line end this near a piece is on it; half the ring stroke (7) rounded up
export function drawProblems(sp, rects, texts) {
  const out = [], on = (e, f) => { const [a0, a1] = window_(e, sp.dur), [b0, b1] = window_(f, sp.dur); return a0 < b1 && b0 < a1; };
  const label = i => `${sp.els[i].id ?? `#${i}`} (${sp.els[i].k})`;
  sp.els.forEach((e, i) => {
    if (e.k === 'ring') {  // the ring is drawn as an ellipse (scene_lib ring: pad 24, radius 0.97-1.03, ry up to +5 %, stroke 7)
      const pad = e.pad ?? 24, cx = e.x + e.w / 2, cy = e.y + e.h / 2, rx = e.w / 2 + pad, ry = e.h / 2 + pad;
      const inner = ([x, y]) => ((x - cx) / (rx * 0.97 - STROKE)) ** 2 + ((y - cy) / (ry * 0.97 - STROKE)) ** 2 <= 1;
      const ox = rx * 1.03 + STROKE, oy = ry * 1.03 * 1.05 + STROKE;  // nearest point of a box to the centre, in the circle space of the outer ellipse
      const reaches = B => Math.hypot((Math.min(Math.max(cx, B.x), B.x + B.w) - cx) / ox, (Math.min(Math.max(cy, B.y), B.y + B.h) - cy) / oy) < 1;
      const corners = B => [[B.x, B.y], [B.x + B.w, B.y], [B.x, B.y + B.h], [B.x + B.w, B.y + B.h]];
      let held = 0;
      for (const T of texts) {
        if (T.i === i || !on(e, sp.els[T.i]) || !reaches(T)) continue;
        if (corners(T).every(inner)) held++;
        else out.push(`${sp.id}: ring ${label(i)} cuts the words of ${label(T.i)} (line ${Math.round(T.x)},${Math.round(T.y)} ${Math.round(T.w)}x${Math.round(T.h)} is not inside the drawn ellipse): circle the whole line or move it`);
      }
      const box = rects.some(B => B.i !== i && !OVERLAY_KINDS.has(sp.els[B.i].k) && on(e, sp.els[B.i])
        && B.x >= e.x - pad && B.y >= e.y - pad && B.x + B.w <= e.x + e.w + pad && B.y + B.h <= e.y + e.h + pad);  // a whole piece in the ring's box
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

// phone readability (Kamil 2026-11-05 note 15: "tablice boczne za małe na telefon"; design 2026-11-05 step 1): a line of
// words, after the camera scale, is at least 40 px on the 1440 frame while it is read, i.e. its first READ_S seconds on
// screen (the camera may pull back later, once it is read). A phone shows a 16:9 frame held sideways over its short side
// (1440 px) and a 9:16 frame upright over the same side (1080 px), so the same size there is 40 * 1080 / 1440 = 30 px.
// cam = [[t, scale]] sampled in the page; texts carry s = the words, for the message.
export const MIN_TEXT_PX = { h: 40, v: 30 }, READ_S = 1.5, READ_MIN_S = 1.2;  // READ_MIN_S: the shortest time a piece of words is up
export function readProblems(sp, texts, cam) {
  const min = MIN_TEXT_PX[sp.canvas === 'v' ? 'v' : 'h'], out = [], seen = new Set();
  // and long enough on screen to be read: a punch line that comes in 0.8 s before the card ends cannot be (s08 2026-11-08)
  // a text node that wraps gives one rect per line, each with the whole node's words: count a node once (T.node)
  const words = new Map(), counted = new Set();
  for (const T of texts) {
    const key = `${T.i}:${T.node ?? counted.size}`;
    if (counted.has(key)) continue;
    counted.add(key); words.set(T.i, (words.get(T.i) ?? 0) + String(T.s ?? '').split(/\s+/).filter(Boolean).length);
  }
  for (const [i, n] of words) {
    const [a0, a1] = window_(sp.els[i], sp.dur), need = Math.max(READ_MIN_S, 0.6 + 0.25 * n);
    if (a1 - a0 < need - 1e-6) out.push(`${sp.id}: ${sp.els[i].id ?? `#${i}`} (${sp.els[i].k}, ${n} words) is on screen ${(a1 - a0).toFixed(1)} s, it needs ${need.toFixed(1)} s to be read: earlier, or a longer card`);
  }
  for (const T of texts) {
    const [a0, a1] = window_(sp.els[T.i], sp.dur), from = a0 + 0.5, to = Math.min(a1, a0 + 0.5 + READ_S);
    const got = cam.filter(([t]) => t >= from - 1e-6 && t <= to + 1e-6).map(c => c[1]);
    const k = got.length ? Math.min(...got) : (cam.find(([t]) => t >= a0)?.[1] ?? 1), h = T.h * k;
    const key = `${T.i}|${T.s}`;
    if (h < min && !seen.has(key)) {
      seen.add(key);
      out.push(`${sp.id}: "${String(T.s ?? '').slice(0, 30)}" (${sp.els[T.i].k}) is ${Math.round(h)} px on the frame (line ${Math.round(T.h)} px x camera ${k.toFixed(2)}), at least ${min} on a phone: fewer pieces, bigger text or a full screen`);
    }
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
      // the camera as render.mjs builds it (sceneFit: stops "on" pieces -> one move, the side column fitted into its board)
      await page.evaluate(([fit, kf, safe, solo, zoom, follow]) => { new Function(`return ${fit}`)()(safe, kf, solo, zoom, follow); },
        [sceneFit.toString(), camKeyframes.toString(), sceneSafe(sp), soloKeys.toString(), zoomStops.toString(), colFollow.toString()]);
      // no animation: every piece in its laid-out place (the pieces' keyframes only move them in and out of it)
      const { rects, texts, cam } = await page.evaluate(dur => {
        const world = document.querySelector('.scene .world');
        // the camera: the world's own animation, sampled every 0.1 s -> [t, scale] (1 = no camera move)
        const camAnims = document.getAnimations().filter(a => a.effect?.target === world), cam = [];
        for (const a of document.getAnimations()) if (!camAnims.includes(a)) a.cancel();
        for (let t = 0; t <= dur + 1e-6; t += 0.1) {
          for (const a of camAnims) { a.pause(); a.currentTime = t * 1000; }
          const tf = getComputedStyle(world).transform;
          cam.push([+t.toFixed(2), tf && tf !== 'none' ? new DOMMatrixReadOnly(tf).a : 1]);
        }
        for (const a of camAnims) a.cancel();
        const wr = world.getBoundingClientRect();
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
          for (let n = walk.nextNode(), node = 0; n; n = walk.nextNode(), node++) {
            if (!n.textContent.trim()) continue;
            const rg = document.createRange(); rg.selectNodeContents(n);
            for (const r of rg.getClientRects()) if (r.width > 2 && r.height > 2) texts.push({ i, node, x: r.left - wr.left, y: r.top - wr.top, w: r.width, h: r.height, s: n.textContent.trim() });
          }
        });
        return { rects, texts, cam };
      }, sp.dur);
      // the measured index runs over the pieces as drawn: kept pieces of "extends" first, a side column sorted (drawnEls)
      const all = { ...sp, els: drawnEls(sp).els };
      bad.push(...clashes(all, rects), ...drawProblems(all, rects, texts));
      bad.push(...readProblems(all, texts, cam));
      await page.close();
    }
  } finally { await browser.close(); }
  for (const b of bad) console.log(`CLASH ${b}`);
  for (const m of motion) console.log(`MOTION ${m}`);
  console.log(`scene_check: ${specs.length} scenes, ${bad.length} clashes, ${motion.length} motion problems (${legacy} without "motion": "tokens", not linted)`);
  process.exit(bad.length || motion.length ? 1 : 0);
}

if (isMain(import.meta.url)) await main();
