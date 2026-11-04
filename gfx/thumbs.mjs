// thumbs.mjs <thumbs.json> <out dir>: YouTube thumbnails for the long (A/B/C variants for Test & Compare) and a cover per short.
// Kamil 2026-11-04: "miałeś mi zawsze robić a/b thumbnaile". Data, not code: thumbs.json says which frame, which words and
// which layout; this file only draws. Generalised from render/montaz/2026-10-22/work/thumbs.mjs (the film-1 thumbnails).
//
// thumbs.json: {"theme": "cetus", "long": [{"id": "A", "frame": "frames/a.png", "big": "92% → 18%", "sub": "…", "tag": "…",
//   "side": "left"|"right", "icon": "<lucide name>", "fx": 0, "fy": 0, "fw": 1600}], "shorts": [{"id": "<short id>",
//   "frame": "frames/s1.png", "big": "…", "sub": "…", "dy": 200}]}. Paths are relative to thumbs.json.
// Out: long_<id>.jpg (1280x720, the upload) + long_<id>_2560.png, <short id>_cover.jpg (1080x1920).
import { chromium } from 'playwright-core';
import fs from 'fs'; import os from 'os'; import path from 'path'; import { pathToFileURL } from 'url';
import { esc, icon } from './html_lib.mjs';

const FONT = '/home/kamil-jan/.local/share/fonts/Montserrat-VF.ttf';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');

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
    if (typeof v.frame !== 'string' || !fs.existsSync(path.resolve(base, v.frame))) bad.push(`${n}: "frame" = an existing image, got ${JSON.stringify(v.frame)}`);
    if (v.icon !== undefined && !fs.existsSync(path.join(ROOT, 'node_modules/lucide-static/icons', `${v.icon}.svg`))) bad.push(`${n}: no lucide icon ${JSON.stringify(v.icon)}`);
    if (v.side !== undefined && !['left', 'right'].includes(v.side)) bad.push(`${n}: "side" = left or right`);
  });
  return bad;
}

const css = (theme) => {
  const c = JSON.parse(fs.readFileSync(path.join(ROOT, 'style/themes', `${theme}.json`), 'utf8')).css;
  return `@font-face{font-family:M;src:url(${pathToFileURL(FONT).href})}
:root{${Object.entries(c).map(([k, v]) => `${k}:${v}`).join(';')}}
html,body{margin:0;overflow:hidden;font-family:M,sans-serif;background:var(--ink)}
.bg{position:absolute;inset:0;background-repeat:no-repeat;filter:contrast(1.1) saturate(1.15) brightness(1.02)}
.big{font-weight:900;color:var(--acc);letter-spacing:-.03em;line-height:.92;text-shadow:0 10px 40px rgba(var(--scrim-rgb),.65)}
.sub{font-weight:900;color:#fff;text-transform:uppercase;line-height:1.04;text-shadow:0 6px 30px rgba(var(--scrim-rgb),.75)}
.tag{display:inline-block;background:var(--acc);color:var(--ink);font-weight:800;border-radius:.4em;padding:.28em .7em}
.ic{display:inline-flex;align-items:center;justify-content:center;border-radius:28%;background:rgba(var(--acc-rgb),.16);border:5px solid var(--acc)}
.ic svg{width:62%;height:62%;stroke:var(--acc);stroke-width:2.2}`;
};

// long: the face on one side, the words on a dark band on the other; fx/fy/fw move and size the frame (face position)
export const longHtml = (v, base, theme) => {
  const left = (v.side ?? 'left') === 'left', img = pathToFileURL(path.resolve(base, v.frame)).href;
  return `<style>${css(theme)}
html,body{width:1280px;height:720px}
.bg{background-image:url(${img});background-size:${v.fw ?? 1600}px auto;background-position:${v.fx ?? (left ? 80 : -400)}px ${v.fy ?? -150}px}
.sh{position:absolute;inset:0;background:linear-gradient(${left ? 90 : 270}deg,rgba(var(--panel-rgb),.98) 0%,rgba(var(--panel-rgb),.9) 42%,rgba(var(--panel-rgb),0) 62%)}
.txt{position:absolute;${left ? 'left' : 'right'}:60px;top:${v.icon ? 70 : 110}px;width:640px;text-align:${left ? 'left' : 'right'}}
.big{font-size:${v.big.length > 9 ? 150 : v.big.length > 5 ? 190 : 240}px}.sub{font-size:60px;margin-top:22px}.tag{font-size:30px;margin-top:26px}
.ic{width:150px;height:150px;margin-bottom:26px}</style>
<div class="bg"></div><div class="sh"></div><div class="txt">${v.icon ? `<div class="ic">${icon(v.icon)}</div>` : ''}<div class="big">${esc(v.big)}</div>
${v.sub ? `<div class="sub">${esc(v.sub)}</div>` : ''}${v.tag ? `<div class="tag">${esc(v.tag)}</div>` : ''}</div>`;
};

// short cover: the words above the head. The Shorts shelf crops covers to about 2:3 (~150 px lost at the top and the bottom,
// seen 2026-10-25), so the text starts at 200 px; dy pushes the frame down to make room above the head
export const shortHtml = (v, base, theme) => `<style>${css(theme)}
html,body{width:1080px;height:1920px}
.bg{background-image:url(${pathToFileURL(path.resolve(base, v.frame)).href});background-size:1080px 1920px;background-position:0 ${v.dy ?? 200}px}
.sh{position:absolute;left:0;right:0;top:0;height:900px;background:linear-gradient(rgba(var(--panel-rgb),1) 0%,rgba(var(--panel-rgb),1) 40%,rgba(var(--panel-rgb),.6) 70%,rgba(var(--panel-rgb),0))}
.txt{position:absolute;left:60px;right:60px;top:200px;text-align:center}.big{font-size:${v.big.length > 6 ? 140 : 190}px}.sub{font-size:62px;margin-top:22px}</style>
<div class="bg"></div><div class="sh"></div><div class="txt"><div class="big">${esc(v.big)}</div>${v.sub ? `<div class="sub">${esc(v.sub)}</div>` : ''}</div>`;

// words that do not fit their thumbnail, measured in the browser: a headline wider than its column is cut at the frame
// edge and a block that runs past the bottom loses its last line (film 2, long_A and long_B, 2026-11-04)
export function fitProblems(file, m, h) {
  const bad = [];
  for (const [k, sc, cl] of m.wide) if (sc > cl + 1) bad.push(`${file}: "${k}" is ${sc - cl} px wider than its column (shorten it)`);
  if (m.bottom > h + 1) bad.push(`${file}: the words run ${Math.round(m.bottom - h)} px past the bottom (shorter "big" or "sub")`);
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
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
  try {
    const shot = async (html, w, h, file, scale = 1) => {
      const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
      const f = path.join(tmp, `${file}.html`);  // a file:// page: setContent (about:blank) may not load file:// images
      fs.writeFileSync(f, `<!doctype html><meta charset="utf-8">${html}`);
      await page.goto(pathToFileURL(f).href, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const m = await page.evaluate(() => {
        const els = ['big', 'sub', 'tag'].map(k => [k, document.querySelector(`.${k}`)]).filter(([, e]) => e);
        return { wide: els.map(([k, e]) => [k, e.scrollWidth, e.clientWidth]),
                 bottom: Math.max(...els.map(([, e]) => e.getBoundingClientRect().bottom)) };
      });
      const bad = fitProblems(file, m, h);
      if (bad.length) throw new Error(bad.join('; '));
      const jpg = file.endsWith('.jpg');
      await page.screenshot({ path: path.join(stage, file), type: jpg ? 'jpeg' : 'png', ...(jpg ? { quality: 92 } : {}) });
      await page.close(); made.push(file);
    };
    for (const v of t.long) {
      await shot(longHtml(v, base, theme), 1280, 720, `long_${v.id}.jpg`);
      await shot(longHtml(v, base, theme), 1280, 720, `long_${v.id}_2560.png`, 2);
    }
    for (const v of t.shorts ?? []) await shot(shortHtml(v, base, theme), 1080, 1920, `${v.id}_cover.jpg`);
    for (const f of fs.readdirSync(out)) if (/^long_.+\.(jpg|png)$|_cover\.jpg$/.test(f) && !made.includes(f)) fs.rmSync(path.join(out, f));
    for (const f of made) fs.renameSync(path.join(stage, f), path.join(out, f));
  } finally {
    await browser.close(); fs.rmSync(tmp, { recursive: true, force: true }); fs.rmSync(stage, { recursive: true, force: true });
  }
  console.log(`thumbs ok: ${t.long.length} long variants, ${(t.shorts ?? []).length} covers -> ${out}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname) await main();
