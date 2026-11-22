// post_gfx.mjs <post dir>...: the LinkedIn post graphic that stands alone (grafika.json -> grafika.png, 1080x1350, 4:5).
// Kamil 2026-11-05: the v2 post graphics "realnie nic dużo nie mówią": the graphic alone, without the post text, must carry a
// complete message. style/REF-posts-top.md (94 posts, 13 creators): a standalone graphic (a thesis on top, then a list,
// a chart, a comparison or a table; no photo; high contrast; the author small) is the best measured format. This file only
// draws; grafika.json says what: {"type": "list"|"bars"|"split"|"table"|"quote", "title": "2-11 words, the thesis",
//   "kicker": "small label above", "note": "one line under the content", "theme": "cetus", "author": "Kamil Jan · …",
//   list:  "items": [{"h": "head", "t": "one line"}]            bars:  "items": [{"label", "value", "tone": "bad"|"good"}], "unit": "%"
//   split: "cols": [{"head", "tone", "lines": []}] x 2           table: "head": [a, b], "rows": [[a, b]], ramp from calm to alert
//   quote: "quote": "the sentence to copy", "items": [{"h", "t"}]}
// Out: grafika.png and grafika.txt (its words), which post_check.py looks for in the picture by OCR.
import { chromium } from 'playwright-core';
import fs from 'fs'; import os from 'os'; import path from 'path'; import { pathToFileURL } from 'url';
import { esc, prose } from './html_lib.mjs';
import { readTheme } from './theme_lib.mjs';
import { isMain } from './cli.mjs';
import { FONT } from './font.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
export const W = 1080, H = 1350;
// the page loads nothing but its inline style and the font: no frame, image, script or other file, so whatever reaches
// the markup cannot draw a local file into the graphic that gets published (review 2026-11-05: an <iframe> of /etc/passwd)
export const CSP = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src file:">`;  // file: = the scheme; a font cannot draw another file's text
export const WORDS = [15, 230];  // REF-posts-top: class A graphics carry 3-35 (diagram) or 60-230 (list) words; < 15 says too little alone
const TYPES = ['list', 'bars', 'split', 'table', 'quote'];
const TONES = ['bad', 'good', 'calm'];  // a CSS class: anything else could close the class attribute and add markup
const SCALES = [1.5, 1.4, 1.3, 1.2, 1.1, 1];  // body scale tried largest first

// every word the picture shows, in reading order (post_check.py counts the same)
export function gfxWords(g) {
  const parts = [g.kicker, g.title, g.quote, g.note, ...(g.head ?? []), ...(g.rows ?? []).flat()];
  for (const it of g.items ?? []) parts.push(it.h, it.t, it.label, it.value === undefined ? '' : `${it.value}${g.unit ?? ''}`);
  for (const c of g.cols ?? []) parts.push(c.head, ...(c.lines ?? []));
  return parts.filter(x => typeof x === 'string' && x.trim()).join(' ').split(/\s+/).filter(Boolean);
}

// the spec before a browser starts; returns the problems (empty = fine)
export function checkPostGfx(g) {
  // shape first: a null entry or a non-list would throw a bare TypeError further on (review 2026-11-05 r2)
  if (!g || typeof g !== 'object' || Array.isArray(g)) return ['grafika.json = an object {"type", "title", ...}'];
  const obj = x => x && typeof x === 'object' && !Array.isArray(x);
  for (const k of ['items', 'cols', 'rows', 'head']) if (g[k] !== undefined && !Array.isArray(g[k])) return [`"${k}" = a list`];
  if ((g.items ?? []).some(x => !obj(x)) || (g.cols ?? []).some(x => !obj(x))) return ['every entry of "items" / "cols" = an object'];
  if ((g.rows ?? []).some(r => !Array.isArray(r))) return ['every row of "rows" = a list of cells'];
  const text = x => x === undefined || typeof x === 'string';  // every drawn field a string (a value a number): no object reaches the page
  if ((g.items ?? []).some(it => ![it.h, it.t, it.label].every(text) || !(it.value === undefined || typeof it.value === 'number'))
    || (g.cols ?? []).some(c => !text(c.head) || !(c.lines === undefined || (Array.isArray(c.lines) && c.lines.every(text))))
    || (g.rows ?? []).some(r => !r.every(text)) || (g.head ?? []).some(x => !text(x)) || ![g.kicker, g.title, g.quote, g.note, g.unit].every(text))
    return ['every text field a string, "value" a number, "lines" a list of strings'];
  const bad = [];
  if (!TYPES.includes(g.type)) bad.push(`"type" = one of ${TYPES.join(', ')}`);
  const tw = typeof g.title === 'string' ? g.title.trim().split(/\s+/).length : 0;
  if (tw < 2 || tw > 11) bad.push(`"title" = the thesis in 2-11 words, got ${tw}`);
  const many = (k, lo, hi) => { const a = g[k]; if (!Array.isArray(a) || a.length < lo || a.length > hi) bad.push(`"${k}": ${lo}-${hi} entries`); };
  if (g.type === 'list') many('items', 2, 8);
  if (g.type === 'quote') { many('items', 1, 4); if (typeof g.quote !== 'string' || !g.quote.trim()) bad.push('"quote": the sentence to copy'); }
  if (g.type === 'bars') { many('items', 2, 5); if ((g.items ?? []).some(it => typeof it.value !== 'number' || it.value < 0)) bad.push('bars: every "value" a number >= 0'); }
  if (g.type === 'split') { many('cols', 2, 2); if ((g.cols ?? []).some(c => !c.head || !Array.isArray(c.lines) || !c.lines.length)) bad.push('split: each column a "head" and "lines"'); }
  if (g.type === 'table') { many('rows', 2, 6); if (!Array.isArray(g.head) || g.head.length !== 2 || (g.rows ?? []).some(r => r.length !== 2)) bad.push('table: "head" and every row = 2 cells'); }
  const tones = [...(g.items ?? []), ...(g.cols ?? [])].map(x => x?.tone).filter(x => x !== undefined);
  if (tones.some(x => !TONES.includes(x))) bad.push(`"tone" = one of ${TONES.join(', ')}`);
  if (g.theme !== undefined && (typeof g.theme !== 'string' || !/^[a-z0-9-]{1,40}$/.test(g.theme))) bad.push('"theme" = a name from style/themes, like "cetus"');
  const n = gfxWords(g).length;
  if (n < WORDS[0] || n > WORDS[1]) bad.push(`${n} words on the graphic, want ${WORDS[0]}-${WORDS[1]} (alone it must say the whole idea)`);
  const all = JSON.stringify(g);
  if (/[—–]/.test(all)) bad.push('a long dash (— or –): use a comma, a colon or a full stop');
  return bad;
}

export const css = (theme) => {
  const c = readTheme(theme, undefined, 'grafika.json').css;  // name and tokens checked: one goes into a path, the other into <style>
  return `@font-face{font-family:M;src:url(${pathToFileURL(FONT).href})}
:root{${Object.entries(c).map(([k, v]) => `${k}:${v}`).join(';')}}
html,body{margin:0;width:${W}px;height:${H}px;overflow:hidden;font-family:M,sans-serif;background:var(--ink);color:var(--soft)}
.pg{position:absolute;inset:0;padding:84px 80px 0;display:flex;flex-direction:column;
  background:radial-gradient(120% 70% at 85% 0%,rgba(var(--acc-rgb),.16),transparent 60%)}
.kick{font-size:30px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin-bottom:22px}
.title{font-weight:900;color:#fff;letter-spacing:-.02em;line-height:1.02}
.rule{width:150px;height:10px;border-radius:5px;background:var(--acc);margin:34px 0 46px}
.body{flex:0 0 auto;--k:1}
.note{margin-top:40px;font-size:34px;line-height:1.3;color:var(--mute);font-weight:600}
.foot{position:absolute;left:80px;right:80px;bottom:62px;display:flex;align-items:center;gap:18px;font-size:30px;font-weight:700;color:var(--acc)}
.foot i{flex:1;height:2px;background:var(--line)}
.li{display:flex;gap:calc(30px*var(--k));align-items:flex-start;margin-bottom:calc(34px*var(--k))}
.num{flex:0 0 calc(76px*var(--k));height:calc(76px*var(--k));border-radius:50%;background:var(--acc);color:var(--ink);font-size:calc(42px*var(--k));font-weight:900;display:flex;align-items:center;justify-content:center}
.h{font-size:calc(44px*var(--k));font-weight:800;color:#fff;line-height:1.12}.t{font-size:calc(34px*var(--k));line-height:1.3;color:var(--mute);margin-top:8px;font-weight:500}
.bar{margin-bottom:calc(40px*var(--k))}.bl{font-size:calc(38px*var(--k));font-weight:700;color:var(--soft);margin-bottom:calc(14px*var(--k))}
.track{height:calc(118px*var(--k));border-radius:calc(18px*var(--k));background:var(--track);position:relative;overflow:hidden}
.fill{position:absolute;left:0;top:0;bottom:0;border-radius:calc(18px*var(--k));display:flex;align-items:center;justify-content:flex-end;padding-right:calc(26px*var(--k));box-sizing:border-box;
  font-size:calc(76px*var(--k));font-weight:900;color:#fff}
.val{position:absolute;top:0;bottom:0;display:flex;align-items:center;padding-left:calc(26px*var(--k));font-size:calc(76px*var(--k));font-weight:900;color:#fff}
.bad{background:var(--alert)}.good{background:var(--acc-dim)}.calm{background:var(--track)}
.cols{display:flex;gap:calc(30px*var(--k))}.col{flex:1;border-radius:calc(26px*var(--k));padding:calc(34px*var(--k)) calc(30px*var(--k));background:var(--card);border:3px solid var(--line)}
.col.good{border-color:var(--acc);background:rgba(var(--acc-rgb),.10)}.col.bad{border-color:var(--alert);background:rgba(224,90,79,.10)}
.ch{font-size:calc(50px*var(--k));font-weight:900;color:#fff;margin-bottom:calc(24px*var(--k))}.cl{font-size:calc(34px*var(--k));line-height:1.28;margin-bottom:calc(20px*var(--k));font-weight:600;color:var(--soft)}
.col.bad .ch{color:var(--alert)}.col.good .ch{color:var(--acc)}
.tb{width:100%;border-collapse:separate;border-spacing:0 calc(14px*var(--k));font-size:calc(36px*var(--k))}
.tb th{text-align:left;font-size:calc(28px*var(--k));letter-spacing:.1em;text-transform:uppercase;color:var(--mute-2);padding:0 calc(22px*var(--k))}
.tb td{padding:calc(24px*var(--k)) calc(22px*var(--k));background:var(--card);font-weight:700;color:#fff;line-height:1.2}
.tb td:first-child{border-radius:calc(18px*var(--k)) 0 0 calc(18px*var(--k));border-left:12px solid var(--c)}.tb td:last-child{border-radius:0 calc(18px*var(--k)) calc(18px*var(--k)) 0;color:var(--soft);font-weight:600}
.q{font-size:calc(50px*var(--k));font-weight:800;line-height:1.22;color:#fff;background:rgba(var(--acc-rgb),.12);border-left:12px solid var(--acc);border-radius:0 calc(24px*var(--k)) calc(24px*var(--k)) 0;padding:calc(34px*var(--k)) calc(36px*var(--k));margin-bottom:calc(44px*var(--k))}
.qi{display:flex;gap:calc(26px*var(--k));align-items:baseline;margin-bottom:calc(26px*var(--k))}.qi .h{flex:0 0 auto;color:var(--acc);font-size:calc(44px*var(--k))}.qi .t{margin:0;font-size:calc(36px*var(--k));color:var(--soft)}`;
};

// the title steps down with its length so a short thesis reads big and a long one still fits in 3 lines
const titleSize = t => (t.length <= 22 ? 104 : t.length <= 40 ? 88 : t.length <= 60 ? 74 : 62);

function body(g) {
  if (g.type === 'list') return g.items.map((it, i) => `<div class="li"><div class="num">${i + 1}</div><div><div class="h">${prose(it.h)}</div>${it.t ? `<div class="t">${prose(it.t)}</div>` : ''}</div></div>`).join('');
  if (g.type === 'bars') {
    const top = Math.max(...g.items.map(it => it.value)) || 1;
    // a short bar carries its number outside, right of the fill: inside it would be cut at the left edge (18 % of 920 px)
    return g.items.map(it => {
      const pct = Math.max(3, (100 * it.value) / top), v = esc(`${it.value}${g.unit ?? ''}`), out = pct < 45;
      return `<div class="bar"><div class="bl">${prose(it.label)}</div><div class="track"><div class="fill ${esc(it.tone ?? 'good')}" style="width:${pct}%">${out ? '' : v}</div>${out ? `<div class="val" style="left:${pct}%">${v}</div>` : ''}</div></div>`;
    }).join('');
  }
  if (g.type === 'split') return `<div class="cols">${g.cols.map(c => `<div class="col ${esc(c.tone ?? '')}"><div class="ch">${prose(c.head)}</div>${c.lines.map(l => `<div class="cl">${prose(l)}</div>`).join('')}</div>`).join('')}</div>`;
  if (g.type === 'table') {
    const ramp = g.rows.map((_, i) => `color-mix(in srgb, var(--alert) ${Math.round((100 * i) / Math.max(1, g.rows.length - 1))}%, var(--acc))`);
    return `<table class="tb"><tr>${g.head.map(h => `<th>${prose(h)}</th>`).join('')}</tr>${g.rows.map((r, i) => `<tr style="--c:${ramp[i]}"><td>${prose(r[0])}</td><td>${prose(r[1])}</td></tr>`).join('')}</table>`;
  }
  return `<div class="q">${prose(g.quote)}</div>${g.items.map(it => `<div class="qi"><div class="h">${prose(it.h)}</div><div class="t">${prose(it.t)}</div></div>`).join('')}`;
}

export const postHtml = (g) => `<style>${css(g.theme ?? 'cetus')}</style>
<div class="pg">${g.kicker ? `<div class="kick">${prose(g.kicker)}</div>` : ''}<div class="title" style="font-size:${titleSize(g.title)}px">${prose(g.title)}</div>
<div class="rule"></div><div class="body">${body(g)}</div>${g.note ? `<div class="note">${prose(g.note)}</div>` : ''}</div>
<div class="foot"><span>${esc(g.author ?? 'Kamil Jan')}</span><i></i></div>`;

// measured in the browser: words cut at a box edge, content running into the footer, or a picture that is half empty
// (REF-posts-top P1: no empty field over 35 % of the area)
export function overflow(m) {
  const bad = [];
  for (const [what, sc, cl] of m.wide) if (sc > cl + 1) bad.push(`${what} is ${sc - cl} px wider than its box`);
  if (m.bottom > m.foot - 20) bad.push(`the content runs ${Math.round(m.bottom - m.foot + 20)} px into the footer: fewer or shorter entries`);
  return bad;
}
export function fitProblems(m) {
  const bad = overflow(m);
  if (!bad.length && m.foot - m.bottom > 0.35 * H) bad.push(`${Math.round(m.foot - m.bottom)} px empty above the footer (> 35 % of the height): more content`);
  return bad;
}

async function main() {
  const dirs = process.argv.slice(2);
  if (!dirs.length) { console.error('usage: node gfx/post_gfx.mjs <post dir with grafika.json>...'); process.exit(2); }
  const read = d => { const f = path.join(d, 'grafika.json'); try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { console.error(`post_gfx.mjs: ${f}: ${e.message}`); process.exit(1); } };
  const specs = dirs.map(d => [d, read(d)]);
  const bad = specs.flatMap(([d, g]) => checkPostGfx(g).map(b => `${d}: ${b}`));
  if (bad.length) { console.error(`post_gfx.mjs:\n  ${bad.join('\n  ')}`); process.exit(1); }
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'post-gfx-'));
  let browser;
  try {
    browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
    for (const [d, g] of specs) {
      const page = await browser.newPage({ viewport: { width: W, height: H }, javaScriptEnabled: false });
      const f = path.join(tmp, 'p.html');
      fs.writeFileSync(f, `<!doctype html><meta charset="utf-8">${CSP}${postHtml(g)}`);
      await page.goto(pathToFileURL(f).href, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const measure = k => page.evaluate(k => {
        document.querySelector('.body').style.setProperty('--k', k);
        const els = [...document.querySelectorAll('.title,.h,.t,.cl,.ch,.bl,.q,td,.fill,.val,.note')];
        const last = [...document.querySelector('.pg').children].at(-1);
        return { wide: els.map(e => [`${e.className || e.tagName} "${e.textContent.slice(0, 24)}"`, e.scrollWidth, e.clientWidth]),
                 bottom: last.getBoundingClientRect().bottom, foot: document.querySelector('.foot').getBoundingClientRect().top };
      }, k);
      // the content grows to fill the page (a short list reads bigger): the largest scale that does not overflow wins
      let m;
      for (const k of SCALES) { m = await measure(k); if (!overflow(m).length) break; }
      const fit = fitProblems(m);
      if (fit.length) throw new Error(`${d}: ${fit.join('; ')}`);
      await page.screenshot({ path: path.join(d, 'grafika.png') });
      fs.writeFileSync(path.join(d, 'grafika.txt'), `${gfxWords(g).join(' ')}\n`);  // what post_check.py looks for in the picture
      await page.close();
      console.log(`post_gfx: ${path.join(d, 'grafika.png')} (${g.type}, ${gfxWords(g).length} words)`);
    }
  } finally {
    await browser?.close(); fs.rmSync(tmp, { recursive: true, force: true });
  }
}

if (isMain(import.meta.url)) await main();
