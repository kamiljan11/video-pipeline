// carousel_gfx.mjs <post dir>...: the Instagram carousel (carousel.json -> slide_01.png ... slide_NN.png + slide_NN.txt, 1080x1350, 4:5).
// One idea per slide. carousel.json says what (ig_carousel.py derives it from the post); the look of the LinkedIn graphic
// (theme, font, footer, CSP) is reused from post_gfx.mjs, so a carousel and the graphic of one post look like one brand:
//   {"theme": "cetus", "author": "Kamil Jan · Higher Minds",
//    "slides": [{"type": "hook", "kicker": "small label", "title": "the thesis", "sub": "swipe hint"},
//               {"type": "idea", "head": "optional small label", "text": "one idea, 1-3 sentences"}, ... 3-8 of them,
//               {"type": "call", "title": "the closing question", "call": "the ONE call", "bio": "line with 'link w bio'"}]}
// Out per slide: slide_NN.png and slide_NN.txt (its words: ig_check.py reads the numbers and the call from them). The page
// counter is drawn as dots, never as digits, so no number appears that the film never says.
import { chromium } from 'playwright-core';
import fs from 'fs'; import os from 'os'; import path from 'path'; import { pathToFileURL } from 'url';
import { prose, esc } from './html_lib.mjs';
import { CSP, W, H, css } from './post_gfx.mjs';
import { isMain } from './cli.mjs';

export const SLIDES = [5, 10];  // slides_ok in style/platform_limits.json "instagram" (ig_check warns outside)
export const IDEA_MAX = 260;    // characters of one idea: longer is two ideas
const FIELDS = { hook: ['kicker', 'title', 'sub'], idea: ['head', 'text'], call: ['title', 'call', 'bio'] };

// every word a slide shows, in reading order (what slide_NN.txt holds)
export function slideWords(s) {
  return (FIELDS[s.type] ?? []).map(k => s[k]).filter(x => typeof x === 'string' && x.trim()).join(' ').split(/\s+/).filter(Boolean);
}

// the spec before a browser starts; returns the problems (empty = fine)
export function checkCarousel(c) {
  if (!c || typeof c !== 'object' || Array.isArray(c)) return ['carousel.json = an object {"slides": [...]}'];
  const sl = c.slides;
  if (!Array.isArray(sl) || sl.some(s => !s || typeof s !== 'object' || Array.isArray(s))) return ['"slides" = a list of objects'];
  const bad = [];
  if (sl.length < SLIDES[0] || sl.length > SLIDES[1]) bad.push(`${sl.length} slides, want ${SLIDES[0]}-${SLIDES[1]} (a hook, 3-8 ideas, a call)`);
  if (sl[0]?.type !== 'hook') bad.push('the first slide = {"type": "hook"}');
  if (sl.at(-1)?.type !== 'call') bad.push('the last slide = {"type": "call"}');
  sl.forEach((s, i) => {
    const at = `slide ${i + 1}`;
    if (!FIELDS[s.type]) return bad.push(`${at}: "type" = hook, idea or call`);
    if (i > 0 && i < sl.length - 1 && s.type !== 'idea') bad.push(`${at}: only the first slide is a hook and the last a call, the rest ideas`);
    for (const k of FIELDS[s.type]) if (s[k] !== undefined && typeof s[k] !== 'string') bad.push(`${at}: "${k}" = a string`);
    const need = { hook: 'title', idea: 'text', call: 'call' }[s.type];
    if (typeof s[need] !== 'string' || !s[need].trim()) bad.push(`${at}: "${need}" is empty`);
    if (s.type === 'idea' && typeof s.text === 'string' && s.text.length > IDEA_MAX) bad.push(`${at}: ${s.text.length} characters, one idea is at most ${IDEA_MAX}: split it`);
    if (s.type === 'hook' && typeof s.title === 'string' && s.title.length > 160) bad.push(`${at}: the hook is ${s.title.length} characters, at most 160`);
  });
  if (c.theme !== undefined && (typeof c.theme !== 'string' || !/^[a-z0-9-]{1,40}$/.test(c.theme))) bad.push('"theme" = a name from style/themes, like "cetus"');
  if (c.author !== undefined && typeof c.author !== 'string') bad.push('"author" = a string');
  if (/[—–]/.test(JSON.stringify(c))) bad.push('a long dash (— or –): use a comma, a colon or a full stop');
  return bad;
}

const slideCss = `
.pg{padding:84px 80px 0}
.dots{display:flex;gap:12px;align-items:center}.dots b{width:14px;height:14px;border-radius:50%;background:var(--line)}.dots b.on{background:var(--acc);width:34px;border-radius:7px}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:190px}
.hook .title{font-size:var(--s);line-height:1.08}
.sub{margin-top:54px;font-size:36px;font-weight:700;color:var(--acc);letter-spacing:.04em}
.hd{font-size:32px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--acc);margin-bottom:30px}
.tx{font-size:var(--s);font-weight:800;line-height:1.22;color:#fff;letter-spacing:-.01em}
.idea.card .tx{background:rgba(var(--acc-rgb),.12);border-left:12px solid var(--acc);border-radius:0 26px 26px 0;padding:52px 52px}
.idea.plain .tx{font-weight:700;color:var(--soft)}.idea.plain .tx::before{content:"";display:block;width:150px;height:10px;border-radius:5px;background:var(--acc);margin-bottom:44px}
.btn{align-self:flex-start;margin-top:56px;padding:26px 46px;border-radius:60px;background:var(--acc);color:var(--ink);font-size:42px;font-weight:900}
.bio{margin-top:40px;font-size:36px;font-weight:600;color:var(--mute);line-height:1.3}`;

export function slideHtml(c, i) {
  const s = c.slides[i];
  const dots = `<div class="dots">${c.slides.map((_, j) => `<b${j === i ? ' class="on"' : ''}></b>`).join('')}</div>`;
  const foot = `<div class="foot"><span>${esc(c.author ?? 'Kamil Jan')}</span><i></i>${dots}</div>`;
  let mid;
  if (s.type === 'hook') {
    mid = `<div class="mid hook">${s.kicker ? `<div class="kick">${prose(s.kicker)}</div>` : ''}<div class="title tx-fit">${prose(s.title)}</div>` +
      `<div class="rule"></div>${s.sub ? `<div class="sub">${prose(s.sub)}</div>` : ''}</div>`;
  } else if (s.type === 'idea') {
    mid = `<div class="mid idea ${i % 2 ? 'card' : 'plain'}">${s.head ? `<div class="hd">${prose(s.head)}</div>` : ''}<div class="tx tx-fit">${prose(s.text)}</div></div>`;
  } else {
    mid = `<div class="mid call">${s.title ? `<div class="tx tx-fit">${prose(s.title)}</div>` : ''}<div class="btn">${prose(s.call)}</div>${s.bio ? `<div class="bio">${prose(s.bio)}</div>` : ''}</div>`;
  }
  return `<style>${css(c.theme ?? 'cetus')}${slideCss}</style><div class="pg">${mid}</div>${foot}`;
}

// runs inside the page: the largest text size at which no word is cut at a box edge and the text clears the footer
export const FIT = `(() => {
  const sizes = [96, 88, 80, 72, 66, 60, 54, 50, 46, 42];
  const run = px => {
    document.documentElement.style.setProperty('--s', px + 'px');
    const bad = [...document.querySelectorAll('.tx-fit,.btn,.bio,.sub,.hd,.kick')]
      .filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.className + ' "' + e.textContent.slice(0, 24) + '" is ' + (e.scrollWidth - e.clientWidth) + ' px wider than its box');
    const last = [...document.querySelector('.mid').children].at(-1);
    if (last.getBoundingClientRect().bottom > document.querySelector('.foot').getBoundingClientRect().top - 20) bad.push('the text runs into the footer');
    if (document.querySelector('.mid > *').getBoundingClientRect().top < 40) bad.push('the text runs over the top edge');
    return bad;
  };
  let bad = [];
  for (const px of sizes) { bad = run(px); if (!bad.length) return px; }
  throw new Error(bad.join('; ') + ' even at ' + sizes[sizes.length - 1] + 'px: shorter text');
})()`;

async function main() {
  const dirs = process.argv.slice(2);
  if (!dirs.length) { console.error('usage: node gfx/carousel_gfx.mjs <post dir with carousel.json>...'); process.exit(2); }
  const read = d => { const f = path.join(d, 'carousel.json'); try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { console.error(`carousel_gfx.mjs: ${f}: ${e.message}`); process.exit(1); } };
  const specs = dirs.map(d => [d, read(d)]);
  const bad = specs.flatMap(([d, c]) => checkCarousel(c).map(b => `${d}: ${b}`));
  if (bad.length) { console.error(`carousel_gfx.mjs:\n  ${bad.join('\n  ')}`); process.exit(1); }
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'carousel-gfx-'));
  let browser;
  try {
    browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
    for (const [d, c] of specs) {
      for (const f of fs.readdirSync(d)) if (/^slide_\d\d\.(png|txt)$/.test(f)) fs.rmSync(path.join(d, f));  // a shorter carousel leaves no old slide behind
      const page = await browser.newPage({ viewport: { width: W, height: H }, javaScriptEnabled: false });
      for (let i = 0; i < c.slides.length; i++) {
        const f = path.join(tmp, 'p.html');
        fs.writeFileSync(f, `<!doctype html><meta charset="utf-8">${CSP}${slideHtml(c, i)}`);
        await page.goto(pathToFileURL(f).href, { waitUntil: 'load' });
        await page.evaluate(() => document.fonts.ready);
        let size;
        try { size = await page.evaluate(FIT); } catch (e) { throw new Error(`${d} slide ${i + 1}: ${e.message}`); }
        const nn = String(i + 1).padStart(2, '0');
        await page.screenshot({ path: path.join(d, `slide_${nn}.png`) });
        fs.writeFileSync(path.join(d, `slide_${nn}.txt`), `${slideWords(c.slides[i]).join(' ')}\n`);
        console.log(`carousel_gfx: ${path.join(d, `slide_${nn}.png`)} (${c.slides[i].type}, ${size}px)`);
      }
      await page.close();
    }
  } finally {
    await browser?.close(); fs.rmSync(tmp, { recursive: true, force: true });
  }
}

if (isMain(import.meta.url)) await main();
