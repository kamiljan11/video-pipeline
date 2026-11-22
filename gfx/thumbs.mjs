// thumbs.mjs <thumbs.json> <out dir>: YouTube thumbnails for the long (A/B/C variants for Test & Compare) and a cover per short.
// Kamil 2026-11-04: "miałeś mi zawsze robić a/b thumbnaile". Data, not code: thumbs.json says which frame, which words and
// which layout; this file only draws. Generalised from render/montaz/2026-10-22/work/thumbs.mjs (the film-1 thumbnails).
//
// thumbs.json: {"theme": "cetus", "long": [{"id": "A", "frame": "frames/a.png", "big": "92% → 18%", "sub": "…", "tag": "…",
//   "side": "left"|"right", "icon": "<lucide name>", "fx": 0, "fy": 0, "fw": 1600}], "shorts": [{"id": "<short id>",
//   "frame": "frames/s1.png", "big": "…", "sub": "…", "dy": 200}]}. Paths are relative to thumbs.json.
// Opt-in, left out = the picture is as before (research ledger plan2, round 2):
//   "tone": "lift" (TH6, long + cover): brighter, harder frame, no colour boost; the dark band and the text shadow in black.
//   "accent": "thumb" (TH8, long + cover): the words in the theme's "--acc-thumb" (no token = the usual --acc).
//   "layout": "object" (TH8, long only): no frame, a flat background with the words on "side" and ONE main object on the
//     other side: "object" = 1-2 of {"src": "<image>"} | {"icon": "<lucide>"}, sized by "h" (share of 720, >= 0.40,
//     default 0.55) or "w" (share of 1280, >= 0.45); or "panel" = {"kind": "steps"|"chart", "items": [3-5 labels]}
//     (chart items {"label", "value"}) in a line under the words.
//   "arrow": {"to": "icon"} (face layout) | {"to": "object", "i": 0} (layout "object"): one arrow, pointing at that.
// Other fields (fx/fy written by thumb_check.py --place with "placed", frame_pick's "pick", "no_face") pass through.
// Out: long_<id>.jpg (1280x720, the upload) + long_<id>_2560.png, <short id>_cover.jpg (1080x1920).
import { chromium } from 'playwright-core';
import fs from 'fs'; import os from 'os'; import path from 'path'; import { pathToFileURL } from 'url';
import { esc, icon, prose } from './html_lib.mjs';
import { isMain } from './cli.mjs';
import { FONT } from './font.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
// the feed (Skool CCC So5/So6, P1 task 15): a phone shows a thumbnail about SMALL px wide, so no letter under MIN_PX there;
// YouTube puts the length in the bottom-right CORNER; the Shorts shelf and the player cover SAFE_TOP / SAFE_BOTTOM of a cover
const SMALL = 320, MIN_PX = 12, CORNER = 0.12, SAFE_TOP = 220, SAFE_BOTTOM = 420;
// TH8 (wf2:thumbs-b:3, c:5): a faceless winner shows 1-2 objects at about 40-50 % of the height or across 45 % of the
// width; 3 neon logos in a row lost. A panel is a progression of 3-5 steps (c:7: a grid of equal items decayed), and one
// arrow at one target helps (a:4: loops of 4 arrows were in the bottom group)
const OBJ_H = 0.40, OBJ_W = 0.45, OBJ_MAX = 2, PANEL_MIN = 3, PANEL_MAX = 5, LABEL_WORDS = 3;
const TEXT_W_OBJ = 500, PANEL_TOP = 340, PANEL_H = 250;
// "big" starts at its size by length and shrinks to its column, in BIG_STEP px, down to BIG_FLOOR (25 px on a 320 px feed, MIN_PX is 12);
// wider than that still stops with "shorten it" (2026-11-08: "„Gotowe”?" with an icon was 445 px too wide at 190 px)
const BIG_FLOOR = 100, BIG_STEP = 4;
// boxes that hold no words (no font-size floor) and the solid ones words must not cover
const NOT_TEXT = new Set(['ic', 'obj', 'panel', 'arrow']), SOLID = new Set(['obj', 'panel']), WORDS = new Set(['big', 'sub', 'tag', 'ic']);
// Polish typesetting: no one-letter word (a, i, o, u, w, z) at a line end and no short last word (<= 3 letters) alone on the
// last line (2026-11-08: "KAŻDĄ ZMIANĘ OD / AI", "1 zdanie do / AI"); a no-break space keeps it with its neighbour
const list = (o) => (o === undefined ? [] : Array.isArray(o) ? o : [o]);
const isObj = (o) => o !== null && typeof o === 'object' && !Array.isArray(o);

// TH8 fields of one long variant
function objectProblems(v, n, base) {
  const bad = [], flat = v.layout === 'object', obj = list(v.object);
  if (v.layout !== undefined && !flat) bad.push(`${n}: "layout" = "object" or left out (the face frame)`);
  if (!flat && (v.object !== undefined || v.panel !== undefined)) bad.push(`${n}: "object" and "panel" need "layout": "object"`);
  if (flat && !obj.length && v.panel === undefined) bad.push(`${n}: layout "object" needs "object" (1-${OBJ_MAX} images or icons) or "panel"`);
  if (obj.length && v.panel !== undefined) bad.push(`${n}: "object" or "panel", not both: one main object`);
  if (obj.length > OBJ_MAX) bad.push(`${n}: ${obj.length} objects, at most ${OBJ_MAX} (3 logos in a row lost)`);
  obj.forEach((o, j) => {
    const m = `${n}.object[${j}]`;
    if (!isObj(o)) { bad.push(`${m}: {"src": "<image>"} or {"icon": "<lucide name>"}`); return; }
    if ((o.src === undefined) === (o.icon === undefined)) bad.push(`${m}: one of "src" or "icon"`);
    if (o.src !== undefined && (typeof o.src !== 'string' || !fs.existsSync(path.resolve(base, o.src)))) bad.push(`${m}: "src" = an existing image, got ${JSON.stringify(o.src)}`);
    if (o.icon !== undefined && !fs.existsSync(path.join(ROOT, 'node_modules/lucide-static/icons', `${o.icon}.svg`))) bad.push(`${m}: no lucide icon ${JSON.stringify(o.icon)}`);
    if (o.h !== undefined && o.w !== undefined) bad.push(`${m}: "h" or "w", not both`);
    if (o.h !== undefined && !(typeof o.h === 'number' && o.h >= OBJ_H && o.h <= 0.85)) bad.push(`${m}: "h" = ${OBJ_H}-0.85 of the height (a smaller object is lost in the feed)`);
    if (o.w !== undefined && !(typeof o.w === 'number' && o.w >= OBJ_W && o.w <= 0.9)) bad.push(`${m}: "w" = ${OBJ_W}-0.9 of the width (a smaller object is lost in the feed)`);
  });
  if (v.panel !== undefined) {
    const p = v.panel, items = isObj(p) && Array.isArray(p.items) ? p.items : null;
    if (!isObj(p) || !['steps', 'chart'].includes(p.kind)) bad.push(`${n}.panel: "kind" = steps or chart`);
    if (!items || items.length < PANEL_MIN || items.length > PANEL_MAX) bad.push(`${n}.panel: "items" = ${PANEL_MIN}-${PANEL_MAX} in a line (a progression, not a grid)`);
    else items.forEach((it, j) => {
      const label = typeof it === 'string' ? it : isObj(it) ? it.label : undefined;
      if (typeof label !== 'string' || !label.trim()) bad.push(`${n}.panel.items[${j}]: a label ("…" or {"label": "…"})`);
      else if (label.trim().split(/\s+/).length > LABEL_WORDS) bad.push(`${n}.panel.items[${j}]: ${JSON.stringify(label)} is over ${LABEL_WORDS} words`);
      if (p.kind === 'chart' && !(isObj(it) && typeof it.value === 'number' && it.value >= 0)) bad.push(`${n}.panel.items[${j}]: a chart item = {"label", "value": >= 0}`);
    });
  }
  if (v.arrow !== undefined) {
    const a = v.arrow, i = isObj(a) ? a.i ?? 0 : 0;
    if (Array.isArray(a)) bad.push(`${n}: "arrow" = one arrow, not a list (several arrows were in the bottom group)`);
    else if (!isObj(a) || !['icon', 'object'].includes(a.to)) bad.push(`${n}: "arrow" = {"to": "icon"} or {"to": "object", "i": 0}`);
    else if (a.to === 'icon' && (flat || v.icon === undefined)) bad.push(`${n}: an arrow to the icon needs "icon" and the face layout`);
    else if (a.to === 'object' && !(Number.isInteger(i) && i >= 0 && i < obj.length)) bad.push(`${n}: the arrow points at object ${JSON.stringify(i)}, there are ${obj.length}`);
  }
  return bad;
}

// checks the spec before a browser starts; returns the problems (empty = fine)
export function checkThumbs(t, base) {
  const bad = [];
  if (!Array.isArray(t.long) || t.long.length < 2) bad.push('"long": at least 2 variants (A/B test)');
  const ids = new Set();
  for (const [k, list] of [['long', t.long ?? []], ['shorts', t.shorts ?? []]]) list.forEach((v, i) => {
    const n = `${k}[${i}]`;
    if (typeof v.id !== 'string' || !/^[A-Za-z0-9_-]+$/.test(v.id)) bad.push(`${n}: "id" = letters, digits, _ or -`);
    else if (ids.has(`${k}:${v.id}`)) bad.push(`${n}: "id" ${v.id} twice`); else ids.add(`${k}:${v.id}`);
    if (typeof v.big !== 'string' || !v.big.trim()) bad.push(`${n}: "big" = the 1-3 words that sell the click`);
    else if (v.big.length > 18) bad.push(`${n}: "big" ${JSON.stringify(v.big)} is ${v.big.length} chars; a thumbnail reads in 1 s, keep it <= 18`);
    if (k === 'long' && v.layout === 'object') { if (v.frame !== undefined) bad.push(`${n}: layout "object" draws a flat background, no "frame" (an image goes in "object")`); }
    else if (typeof v.frame !== 'string' || !fs.existsSync(path.resolve(base, v.frame))) bad.push(`${n}: "frame" = an existing image, got ${JSON.stringify(v.frame)}`);
    if (v.icon !== undefined && !fs.existsSync(path.join(ROOT, 'node_modules/lucide-static/icons', `${v.icon}.svg`))) bad.push(`${n}: no lucide icon ${JSON.stringify(v.icon)}`);
    if (v.side !== undefined && !['left', 'right'].includes(v.side)) bad.push(`${n}: "side" = left or right`);
    if (v.tone !== undefined && v.tone !== 'lift') bad.push(`${n}: "tone" = "lift" or left out`);
    if (v.accent !== undefined && v.accent !== 'thumb') bad.push(`${n}: "accent" = "thumb" or left out`);
    if (k === 'long') bad.push(...objectProblems(v, n, base));
    else for (const f of ['layout', 'object', 'panel', 'arrow']) if (v[f] !== undefined) bad.push(`${n}: "${f}" is for long variants only`);
  });
  return bad;
}

const rgbOf = (hex) => (/^#[0-9a-f]{6}$/i.test(hex ?? '') ? [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)).join(',') : undefined);
// theme = a name in style/themes (or {css} in tests); v = the variant: its "accent" and "tone" change only tokens and the
// frame filter, so a variant without them is drawn as before
const css = (theme, v = {}) => {
  const c = { ...(isObj(theme) ? theme : JSON.parse(fs.readFileSync(path.join(ROOT, 'style/themes', `${theme}.json`), 'utf8'))).css };
  // TH8 accent "thumb": a light accent for the feed; the colour is the theme's --acc-thumb (Kamil picks it), else --acc
  if (v.accent === 'thumb' && c['--acc-thumb']) { c['--acc'] = c['--acc-thumb']; c['--acc-rgb'] = rgbOf(c['--acc-thumb']) ?? c['--acc-rgb']; }
  // TH6 tone "lift" (wf2:thumbs-b:7: more saturation was in the bottom group for 2 of 3 creators): a brighter, harder
  // frame without the colour boost; the band behind the words and the text shadow go to black, not navy
  const lift = v.tone === 'lift';
  if (lift) { c['--panel-rgb'] = '0,0,0'; c['--scrim-rgb'] = '0,0,0'; }
  return `@font-face{font-family:M;src:url(${pathToFileURL(FONT).href})}
:root{${Object.entries(c).filter(([k]) => k !== '--acc-thumb').map(([k, x]) => `${k}:${x}`).join(';')}}
html,body{margin:0;overflow:hidden;font-family:M,sans-serif;background:var(--ink)}
.bg{position:absolute;inset:0;background-repeat:no-repeat;filter:${lift ? 'contrast(1.2) saturate(1) brightness(1.1)' : 'contrast(1.1) saturate(1.15) brightness(1.02)'}}
.big{font-weight:900;color:var(--acc);letter-spacing:-.03em;line-height:.92;text-shadow:0 10px 40px rgba(var(--scrim-rgb),.65)}
.sub{font-weight:900;color:#fff;text-transform:uppercase;line-height:1.04;text-shadow:0 6px 30px rgba(var(--scrim-rgb),.75)}
.tag{display:inline-block;background:var(--acc);color:var(--ink);font-weight:800;border-radius:.4em;padding:.28em .7em}
.ic{display:inline-flex;align-items:center;justify-content:center;border-radius:28%;background:rgba(var(--acc-rgb),.16);border:5px solid var(--acc)}
.ic svg{width:62%;height:62%;stroke:var(--acc);stroke-width:2.2}`;
};

// TH8 arrow: an SVG over the page; the page script aims it once the fonts are in (shot() calls window.__arrow before it
// measures), from data-from (an x in px on the face side, level with the target) or from under the words ("text": the
// object fills its half, so a level arrow would be shorter than its head) to the near edge of data-to
const ARROW_JS = `<script>window.__arrow=()=>{const a=document.querySelector('.arrow');if(!a)return;
const t=document.querySelector(a.dataset.to).getBoundingClientRect(),cy=(t.top+t.bottom)/2;let x0,y0;
if(a.dataset.from==='text'){const r=document.createRange();r.selectNodeContents(document.querySelector('.txt'));const s=r.getBoundingClientRect();
x0=(s.left+s.right)/2;y0=s.bottom+50}else{x0=+a.dataset.from;y0=cy}
const x1=x0<t.left?t.left-24:t.right+24,y1=cy,d=Math.hypot(x1-x0,y1-y0)||1,ux=(x1-x0)/d,uy=(y1-y0)/d,bx=x1-ux*56,by=y1-uy*56;
const l=a.querySelector('line');l.setAttribute('x1',x0);l.setAttribute('y1',y0);l.setAttribute('x2',bx);l.setAttribute('y2',by);
a.querySelector('polygon').setAttribute('points',[x1,y1,bx-uy*34,by+ux*34,bx+uy*34,by-ux*34].join(' '))}</script>`;
const arrowHtml = (to, from) => `<svg class="arrow" data-to="${to}" data-from="${from}" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible">
<g style="filter:drop-shadow(0 6px 18px rgba(var(--scrim-rgb),.7))"><line stroke="var(--acc)" stroke-width="16" stroke-linecap="round"/><polygon fill="var(--acc)"/></g></svg>${ARROW_JS}`;

// TH8 layout "object": no frame (flat --ink), the words on "side", the main object on the other side: 1-2 images or icons,
// or a panel of 3-5 steps / bars in a line under the words. fitProblems checks the drawn sizes, not these numbers
const objectHtml = (v, base, theme) => {
  const left = (v.side ?? 'left') === 'left', far = left ? 'right' : 'left', obj = list(v.object);
  const room = 1280 - 60 - TEXT_W_OBJ - 40 - 60, each = Math.floor((room - 30 * (obj.length - 1)) / Math.max(obj.length, 1));
  const one = (o) => {
    const h = Math.round((o.h ?? (o.w === undefined ? 0.55 : 0)) * 720), w = Math.round((o.w ?? 0) * 1280);
    if (o.icon) { const s = h ? Math.min(h, each) : Math.min(w, 620); return `<div class="obj io" style="width:${s}px;height:${s}px">${icon(o.icon)}</div>`; }
    const size = h ? `height:${h}px;max-width:${each}px` : `width:${w}px;max-height:620px`;
    return `<img class="obj" src="${pathToFileURL(path.resolve(base, o.src)).href}" style="${size};object-fit:contain">`;
  };
  const p = v.panel, items = (p?.items ?? []).map(it => (typeof it === 'string' ? { label: it } : it));
  const top = Math.max(...items.map(it => it.value ?? 0), 1);
  const item = (it, i) => (i && p.kind === 'steps' ? `<div class="pa">${icon('arrow-right')}</div>` : '') + (p.kind === 'steps'
    ? `<div class="pi"><div class="pn">${i + 1}</div><div class="pl">${esc(it.label)}</div></div>`
    : `<div class="pi"><div class="pbar"><div class="pv" style="height:${Math.max(6, Math.round(100 * it.value / top))}%"></div></div><div class="pl">${esc(it.label)}</div></div>`);
  // the face layout's sizes for its 640 px column, scaled to this 500 px one; over a panel the words get one line
  const big = p ? (v.big.length > 9 ? 130 : 170) : (v.big.length > 9 ? 120 : v.big.length > 5 ? 150 : 190);
  return `<style>${css(theme, v)}
html,body{width:1280px;height:720px}
.txt{position:absolute;${p ? 'left:60px;right:60px;top:40px' : `${left ? 'left' : 'right'}:60px;top:${v.icon ? 70 : 110}px;width:${TEXT_W_OBJ}px`};text-align:${left ? 'left' : 'right'}}
.big{font-size:${big}px}.sub{font-size:60px;margin-top:22px}.tag{font-size:48px;margin-top:26px}
.ic{width:150px;height:150px;margin-bottom:26px}
.objs{position:absolute;top:50px;bottom:50px;${far}:60px;width:${room}px;display:flex;align-items:center;justify-content:center;gap:30px}
.obj{flex:none;display:block}.io{display:flex;align-items:center;justify-content:center}.io svg{width:100%;height:100%;stroke:var(--acc);stroke-width:1.6}
.panel{position:absolute;left:60px;right:60px;top:${PANEL_TOP}px;height:${PANEL_H}px;display:flex;align-items:stretch;gap:18px}
.pi{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:16px;background:rgba(var(--acc-rgb),.12);border:4px solid var(--acc);border-radius:24px;padding:18px 12px}
.pa{flex:none;width:60px;display:flex;align-items:center}.pa svg{width:60px;height:60px;stroke:var(--acc);stroke-width:3}
.pn{width:90px;height:90px;border-radius:50%;background:var(--acc);color:var(--ink);font-weight:900;font-size:56px;display:flex;align-items:center;justify-content:center}
.pbar{flex:1;width:60%;display:flex;align-items:flex-end}.pv{width:100%;background:var(--acc);border-radius:10px 10px 0 0}
.pl{max-width:100%;overflow:hidden;white-space:nowrap;font-weight:900;font-size:50px;color:#fff;line-height:1.1}</style>
<div class="txt">${v.icon ? `<div class="ic">${icon(v.icon)}</div>` : ''}<div class="big">${prose(v.big)}</div>
${v.sub ? `<div class="sub">${prose(v.sub)}</div>` : ''}${v.tag ? `<div class="tag">${prose(v.tag)}</div>` : ''}</div>
${obj.length ? `<div class="objs">${obj.map(one).join('')}</div>` : ''}${p ? `<div class="panel">${items.map(item).join('')}</div>` : ''}${v.arrow ? arrowHtml(`.obj:nth-child(${(v.arrow.i ?? 0) + 1})`, 'text') : ''}`;
};

// long: the face on one side, the words on a dark band on the other; fx/fy/fw move and size the frame (face position)
export const longHtml = (v, base, theme) => {
  if (v.layout === 'object') return objectHtml(v, base, theme);
  const left = (v.side ?? 'left') === 'left', img = pathToFileURL(path.resolve(base, v.frame)).href;
  return `<style>${css(theme, v)}
html,body{width:1280px;height:720px}
.bg{background-image:url(${img});background-size:${v.fw ?? 1600}px auto;background-position:${v.fx ?? (left ? 80 : -400)}px ${v.fy ?? -150}px}
.sh{position:absolute;inset:0;background:linear-gradient(${left ? 90 : 270}deg,rgba(var(--panel-rgb),.98) 0%,rgba(var(--panel-rgb),.9) 42%,rgba(var(--panel-rgb),0) 62%)}
.txt{position:absolute;${left ? 'left' : 'right'}:60px;top:${v.icon ? 70 : 110}px;width:640px;text-align:${left ? 'left' : 'right'}}
.big{font-size:${v.big.length > 9 ? 150 : v.big.length > 5 ? 190 : 240}px}.sub{font-size:60px;margin-top:22px}.tag{font-size:48px;margin-top:26px}
.ic{width:150px;height:150px;margin-bottom:26px}</style>
<div class="bg"></div><div class="sh"></div><div class="txt">${v.icon ? `<div class="ic">${icon(v.icon)}</div>` : ''}<div class="big">${prose(v.big)}</div>
${v.sub ? `<div class="sub">${prose(v.sub)}</div>` : ''}${v.tag ? `<div class="tag">${prose(v.tag)}</div>` : ''}</div>${v.arrow ? arrowHtml('.ic', left ? 768 : 512) : ''}`;
};

// short cover: the words above the head. The Shorts shelf crops covers to about 2:3 (~150 px lost at the top and the bottom,
// seen 2026-10-25), so the text starts at SAFE_TOP; dy pushes the frame down to make room above the head
export const shortHtml = (v, base, theme) => `<style>${css(theme, v)}
html,body{width:1080px;height:1920px}
.bg{background-image:url(${pathToFileURL(path.resolve(base, v.frame)).href});background-size:1080px 1920px;background-position:0 ${v.dy ?? 200}px}
.sh{position:absolute;left:0;right:0;top:0;height:900px;background:linear-gradient(rgba(var(--panel-rgb),1) 0%,rgba(var(--panel-rgb),1) 40%,rgba(var(--panel-rgb),.6) 70%,rgba(var(--panel-rgb),0))}
.txt{position:absolute;left:60px;right:60px;top:${SAFE_TOP}px;text-align:center}.big{font-size:${v.big.length > 6 ? 140 : 190}px}.sub{font-size:62px;margin-top:22px}</style>
<div class="bg"></div><div class="sh"></div><div class="txt"><div class="big">${prose(v.big)}</div>${v.sub ? `<div class="sub">${prose(v.sub)}</div>` : ''}</div>`;

// words that do not fit their thumbnail, measured in the browser: a headline wider than its column is cut at the frame
// edge and a block that runs past the bottom loses its last line (film 2, long_A and long_B, 2026-11-04). m.boxes
// [{k, x0, y0, x1, y1, fs}] (page px, fs = font size): a letter too small in the feed, anything under the length in the
// corner of a long, anything a cover's safe zones hide; TH8: an object or panel drawn under OBJ_H / OBJ_W, past the frame
// edge or under the words
export function fitProblems(file, m, h, w = 1280, cover = false) {
  const bad = [];
  for (const [k, sc, cl] of m.wide) if (sc > cl + 1) bad.push(`${file}: "${k}" is ${sc - cl} px wider than its column (shorten it)`);
  if (m.bottom > h + 1) bad.push(`${file}: the words run ${Math.round(m.bottom - h)} px past the bottom (shorter "big" or "sub")`);
  const boxes = m.boxes ?? [];
  for (const b of boxes.filter(x => NOT_TEXT.has(x.k) && x.k !== 'ic')) {
    if (b.x0 < -1 || b.y0 < -1 || b.x1 > w + 1 || b.y1 > h + 1) bad.push(`${file}: the ${b.k} reaches past the frame edge (smaller "h"/"w")`);
    if (!SOLID.has(b.k)) continue;
    if (b.y1 - b.y0 < OBJ_H * h - 1 && b.x1 - b.x0 < OBJ_W * w - 1)
      bad.push(`${file}: the ${b.k} is drawn ${Math.round(b.x1 - b.x0)}x${Math.round(b.y1 - b.y0)} px, want >= ${OBJ_H * 100}% of the height or ${OBJ_W * 100}% of the width`);
    for (const t of boxes.filter(x => WORDS.has(x.k)))
      if (t.x0 < b.x1 - 1 && b.x0 < t.x1 - 1 && t.y0 < b.y1 - 1 && b.y0 < t.y1 - 1) bad.push(`${file}: "${t.k}" overlaps the ${b.k}`);
  }
  for (const b of boxes) {
    const small = b.fs * SMALL / w;
    if (!NOT_TEXT.has(b.k) && small < MIN_PX) bad.push(`${file}: "${b.k}" is ${small.toFixed(1)} px at ${SMALL} px wide (want >= ${MIN_PX}): bigger or drop it`);
    if (!cover && b.x1 > w * (1 - CORNER) && b.y1 > h * (1 - CORNER)) bad.push(`${file}: "${b.k}" reaches the bottom-right ${CORNER * 100}% where YouTube shows the length`);
    if (cover && (b.y0 < SAFE_TOP - 1 || b.y1 > h - SAFE_BOTTOM + 1))
      bad.push(`${file}: "${b.k}" spans y ${Math.round(b.y0)}-${Math.round(b.y1)}, outside the cover's safe zone ${SAFE_TOP}-${h - SAFE_BOTTOM}`);
  }
  return bad;
}

async function main() {
  const [specPath, out] = process.argv.slice(2);
  if (!specPath || !out) { console.error('usage: node gfx/thumbs.mjs <thumbs.json> <out dir>'); process.exit(2); }
  const t = JSON.parse(fs.readFileSync(specPath, 'utf8')), base = path.dirname(path.resolve(specPath)), theme = t.theme ?? 'cetus';
  const bad = checkThumbs(t, base);
  if (bad.length) { console.error(`thumbs.mjs ${specPath}:\n  ${bad.join('\n  ')}`); process.exit(1); }
  fs.mkdirSync(out, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbs-'));
  // all or nothing: shots go to a staging dir next to out; only a run where every word fits replaces the set in out, so a
  // stop on variant B never leaves a new A next to an old B that film_check would count as an A/B pair
  const stage = fs.mkdtempSync(path.join(out, '.thumbs-'));
  const made = [];
  let browser;
  try {
    browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
    const shot = async (html, w, h, file, scale = 1, cover = false) => {
      const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
      const f = path.join(tmp, `${file}.html`);  // a file:// page: setContent (about:blank) may not load file:// images
      fs.writeFileSync(f, `<!doctype html><meta charset="utf-8">${html}`);
      await page.goto(pathToFileURL(f).href, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate(([floor, step]) => {  // "big" to its column (see BIG_FLOOR), before the arrow aims and the measure
        const e = document.querySelector('.big'); if (!e) return;
        let px = parseFloat(getComputedStyle(e).fontSize);
        while (e.scrollWidth > e.clientWidth + 1 && px - step >= floor) { px -= step; e.style.fontSize = `${px}px`; }
      }, [BIG_FLOOR, BIG_STEP]);
      await page.evaluate(() => window.__arrow?.());  // TH8: aimed after the fonts, before the measure
      const m = await page.evaluate(() => {
        const els = [...['big', 'sub', 'tag'].map(k => [k, document.querySelector(`.${k}`)]).filter(([, e]) => e),
          ...[...document.querySelectorAll('.pl')].map((e, i) => [`panel item ${i + 1}`, e])];
        const box = (k, r, fs = 0) => ({ k, x0: r.left, y0: r.top, x1: r.right, y1: r.bottom, fs });
        const drawn = (e) => {  // an object-fit: contain image: the picture, not its box
          const r = e.getBoundingClientRect();
          if (e.tagName !== 'IMG' || !e.naturalWidth) return r;
          const s = Math.min(r.width / e.naturalWidth, r.height / e.naturalHeight), iw = e.naturalWidth * s, ih = e.naturalHeight * s;
          return { left: r.left + (r.width - iw) / 2, top: r.top + (r.height - ih) / 2, right: r.left + (r.width + iw) / 2, bottom: r.top + (r.height + ih) / 2 };
        };
        const boxes = [...els, ['ic', document.querySelector('.ic')]].filter(([, e]) => e)
          .map(([k, e]) => box(k, e.getBoundingClientRect(), parseFloat(getComputedStyle(e).fontSize)));
        for (const e of document.querySelectorAll('.obj')) boxes.push(box('obj', drawn(e)));
        for (const [k, sel] of [['panel', '.panel'], ['arrow', '.arrow g']]) { const e = document.querySelector(sel); if (e) boxes.push(box(k, e.getBoundingClientRect())); }
        return { wide: els.map(([k, e]) => [k, e.scrollWidth, e.clientWidth]),
                 bottom: Math.max(...els.map(([, e]) => e.getBoundingClientRect().bottom)), boxes };
      });
      const bad = fitProblems(file, m, h, w, cover);
      if (bad.length) throw new Error(bad.join('; '));
      const jpg = file.endsWith('.jpg');
      await page.screenshot({ path: path.join(stage, file), type: jpg ? 'jpeg' : 'png', ...(jpg ? { quality: 92 } : {}) });
      await page.close(); made.push(file);
    };
    for (const v of t.long) {
      await shot(longHtml(v, base, theme), 1280, 720, `long_${v.id}.jpg`);
      await shot(longHtml(v, base, theme), 1280, 720, `long_${v.id}_2560.png`, 2);
    }
    for (const v of t.shorts ?? []) await shot(shortHtml(v, base, theme), 1080, 1920, `${v.id}_cover.jpg`, 1, true);
    for (const f of fs.readdirSync(out)) if (/^long_.+\.(jpg|png)$|_cover\.jpg$/.test(f) && !made.includes(f)) fs.rmSync(path.join(out, f));
    for (const f of made) fs.renameSync(path.join(stage, f), path.join(out, f));
  } finally {
    await browser?.close(); fs.rmSync(tmp, { recursive: true, force: true }); fs.rmSync(stage, { recursive: true, force: true });
  }
  console.log(`thumbs ok: ${t.long.length} long variants, ${(t.shorts ?? []).length} covers -> ${out}`);
}

if (isMain(import.meta.url)) await main();
