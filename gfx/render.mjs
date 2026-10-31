// node render.mjs specs.json outdir  -> outdir/<id>.mov (ProRes 4444 + alpha, 2560x1440@30; spec canvas "v" -> 1080x1920)
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import crypto from 'crypto'; import fs from 'fs'; import path from 'path'; import { pathToFileURL } from 'url'; import { execFileSync } from 'child_process';
import { PER_CARD, keyOf, motion, vZoom } from './webshot_lib.mjs';
import { COUNT_DELAY, FADE_OUT, countParts, countSeconds, fmtNum, numWidth } from './count_lib.mjs';
import { CARET_HOLD, MARK_DUR, charTimes, maximSeek, maximWords, wordTimes } from './maxim_lib.mjs';
import { loadTheme } from './theme_lib.mjs';
const [specFile, outDir] = process.argv.slice(2);
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const THEME = loadTheme(specFile);  // work/theme.json -> style/themes/<name>.json colors; null = the template's own
const GSAP = '/home/kamil-jan/video-pipeline/node_modules/gsap/dist/gsap.min.js';
const FPS = 30, esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;');
const icon = n => n ? fs.readFileSync(`/home/kamil-jan/video-pipeline/node_modules/lucide-static/icons/${n}.svg`, 'utf8').replace(/<!--[\s\S]*?-->/g, '') : '';
// "kw" box; "count" is the same box with counting numbers in its title
const kwBox = (sp, title, cls = 'kw') => `<div class="${cls} ${sp.side||'right'}${sp.compact&&sp.canvas==='v'?' compact':''}">${sp.icon&&!(sp.compact&&sp.canvas==='v')?`<div class="ic">${icon(sp.icon)}</div>`:''}<div class="t">${title}</div><div class="bar"></div>${sp.sub?`<div class="s">${esc(sp.sub)}</div>`:''}</div>`;
// "end" card: optional brand row under the address, "logo" = image file (path relative to the specs file), "logo_sub" = its line
// (e.g. the company site). A logo that is not there stops the render with its name, never an end card with a broken image.
const logoFile = sp => path.resolve(path.dirname(specFile), sp.logo);
const endBrand = sp => {
  if (!sp.logo) return '';
  const f = logoFile(sp);
  if (!fs.existsSync(f)) { console.error(`FAILED gfx ${sp.id}: logo ${f} not found`); process.exit(1); }
  return `<div class="brand"><img src="${pathToFileURL(f).href.replace(/"/g, '%22')}">${sp.logo_sub ? `<div class="u">${esc(sp.logo_sub)}</div>` : ''}</div>`;
};
const html = sp => {
  if (sp.type === 'kw') return kwBox(sp, esc(sp.text));
  if (sp.type === 'count') return kwBox(sp, countParts(sp.text).map(p => typeof p === 'string' ? esc(p)
    : `<span class="num" data-to="${p.value}" data-dec="${p.dec}" data-group="${p.group ? 1 : ''}" data-final="${esc(p.final)}" style="min-width:${numWidth(p.final)}ch">${fmtNum(0, p.dec, p.group)}</span>`).join(''), 'kw count');
  if (sp.type === 'lower') return `<div class="lower"><div class="acc"></div><div class="box"><div class="n">${esc(sp.text)}</div><div class="r">${esc(sp.sub)}</div></div></div>`;
  if (sp.type === 'list') return `<div class="list"><div class="h">${esc(sp.text)}</div>${sp.items.map((x,i)=>`<div class="i" style="animation:slide .45s ${(sp.delays||[])[i]??i}s both">${(sp.icons||[])[i]?`<span class="li">${icon(sp.icons[i])}</span>`:`<b>${i+1}</b>`}<span>${esc(x)}</span></div>`).join('')}</div>`;
  if (sp.type === 'end') return `<div class="endc"><div class="t">${esc(sp.text)}</div><div class="bar"></div><div class="s">${esc(sp.sub)}</div>${endBrand(sp)}</div>`;
  if (sp.type === 'cta') return `<div class="cta"><div class="btn">${icon('bell')}${esc(sp.text)}</div><div class="s">${esc(sp.sub)}</div></div>`;
  if (sp.type === 'slide') return `<div class="slide"><div class="in">${sp.html}</div>${sp.src?`<div class="src">${esc(sp.src)}</div>`:''}</div>`;
  if (sp.type === 'web') return web(sp);
  if (sp.type === 'meme') return meme(sp);
  if (sp.type === 'maxim') return maxim(sp);
  if (sp.type === 'float') return `<div class="float">${sp.html}</div>`;  // illustration beside the speaker: the spec's own pieces (template.html › float)
  if (sp.type === 'chap') return `<div class="chap"><div class="no">${esc(sp.sub)}</div><div class="t">${esc(sp.text)}</div></div>`;
};
// "maxim": the sentence typed while it is said (gfx/maxim_lib.mjs); every letter is in the layout from the start (hidden) and the
// caret takes no width, so the lines never re-wrap or shift while typing; window.__seek = maximSeek shows the state at time t
// "pill": true (9:16 hook card): a white pill in the caption zone instead of the top band; build_edl pauses captions under it
function maxim(sp) {
  const words = maximWords(sp.text), times = wordTimes(words, sp.dur, sp.at), chars = charTimes(words, times, sp.dur);
  const body = words.map(({ w, hl }, i) => `<span class="w${hl ? ' hl' : ''}">${[...w].map((c, j) =>
    `<i data-t="${chars[i][j].toFixed(3)}">${esc(c)}</i>`).join('')}${hl ? `<b class="mk" data-t="${(chars[i].at(-1) + 0.05).toFixed(3)}"></b>` : ''}</span>`).join(' ');
  return `<div class="maxim${sp.pill ? ' pill' : ''}"><div class="scrim"></div><div class="box"><div class="bar"></div><div class="t">${body}<span class="caret"></span></div></div></div>`;
}
// "web": the cited page in a browser window (capture: webshot.mjs), scrolled to the quote, which is then marked
const WIN = { x: 140, y: 110, w: 1720, view: 1060 };  // 16:9 canvas; the face picture-in-picture sits bottom right
// 9:16 (shorts): "split" (default) = the card in the top part over a light background; assemble.py puts the face in a box under
// it (gfx_types.SPLIT) and build_edl.py moves the captions into the gap; "full" = the card alone on the dark background
const WIN_V = { split: { x: 60, y: 110, w: 960, view: 760 }, full: { x: 50, y: 230, w: 980, view: 780 } };
const CHROME = 122;  // tab row 64 + address bar 58 (template.html .web .top/.addr)
function web(sp) {
  const base = `${outDir}/web/${keyOf(specFile, sp)}`;
  if (!fs.existsSync(`${base}.json`)) throw new Error(`no capture for "${sp.id}": run gfx/webshot.mjs first`);
  const v = sp.canvas === 'v', layout = sp.layout ?? 'split', W = v ? WIN_V[layout] : WIN;
  if (!W || (!v && sp.layout !== undefined)) throw new Error(`"${sp.id}": layout "split" or "full", only on a 9:16 card (canvas "v"), got ${JSON.stringify(sp.layout)}`);
  const m = JSON.parse(fs.readFileSync(`${base}.json`, 'utf8'));
  const z = v ? vZoom(m, W.w) : { s: W.w / m.width, x0: 0 };
  const shown = v ? z : { height: m.height * z.s, rects: m.rects.map(([x, y, w, h]) => [x * z.s, y * z.s, w * z.s, h * z.s]) };
  const mo = motion(shown, W.view, sp.dur), id = sp.id.replace(/[^\w-]/g, '_');
  const anim = mo.scroll ? `animation:ws_${id} ${mo.scroll}s cubic-bezier(.45,0,.2,1) ${mo.start}s both` : '';
  const marks = shown.rects.map(([x, y, w, h], i) => `<div class="hl" style="left:${x - 6}px;top:${y - 4}px;width:${w + 12}px;height:${h + 8}px;animation:hl .5s ${(mo.mark + i * 0.25).toFixed(2)}s ease-out both"></div>`).join('');
  const day = new Date(m.captured).toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const addr = m.final_url ? m.final_url.replace(/^https:\/\//, '') : (m.host || '');
  const src = sp.src || `Źródło: ${m.host || m.title}${m.title && m.host ? ` · ${m.title}` : ''}${m.kind === 'pdf' ? ` · str. ${m.page}` : ''}`;
  return `<style>@keyframes ws_${id}{from{transform:translateY(0)}to{transform:translateY(-${mo.target.toFixed(0)}px)}}</style>`
    + `<div class="web${v ? ` ${layout}` : ''}"><div class="win" style="left:${W.x}px;top:${W.y}px;width:${W.w}px">`
    + `<div class="top"><i></i><i></i><i></i><span class="tab">${esc(m.title || m.host)}</span></div>`
    + `<div class="addr"><span class="lock"></span>${esc(addr)}</div>`
    + `<div class="view" style="height:${W.view}px"><div class="shot" style="${anim}"><img src="file://${base}.png" style="width:${(m.width * z.s).toFixed(1)}px;margin-left:${(-z.x0 * z.s).toFixed(1)}px">${marks}</div></div></div>`
    + `<div class="src"${v ? ` style="left:${W.x}px;top:${W.y + CHROME + W.view + 18}px"` : ''}>${esc(src)} · stan na ${day}</div></div>`;
}
// "meme": a known meme picture with the spec's own words in the template's boxes, 9:16 only, "split" (the face box under it,
// as a "web" card) or "full". Catalogue (boxes, imgflip id) = style/memes.json; the pictures are third-party, so they live in
// render/memes/ (memes.py add <slug>), never in the public repo. "text" i comes in at "at"[i] s (default 0.25 + 0.7 i).
const MEMES = process.env.VP_MEMES ?? path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'render', 'memes');  // VP_MEMES: tests
const MEME_BOX = { split: { y: 120, h: 880 }, full: { y: 260, h: 1240 } };  // split: ends above the captions (gfx_types.SPLIT)
const CATALOGUE = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', 'style', 'memes.json');
// the picture's own json (name, size, file) + the text boxes of the catalogue in the repo (a fixed box works without a new
// fetch; a picture placed by hand keeps the boxes of its own json); every field checked, so a bad one stops the card by name
const memeLib = sp => {
  const f = `${MEMES}/${sp.meme}.json`, bad = why => new Error(`"${sp.id}": meme ${JSON.stringify(sp.meme)}: ${why}`);
  if (typeof sp.meme !== 'string' || !/^[a-z0-9_]+$/.test(sp.meme) || !fs.existsSync(f)) throw bad(`not in ${MEMES} (python3 memes.py add <slug>)`);
  let m; try { m = JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { throw bad(`${f}: ${e.message}`); }
  const cat = JSON.parse(fs.readFileSync(CATALOGUE, 'utf8'))[sp.meme];
  if (cat?.boxes) m.boxes = cat.boxes;
  const box = b => Array.isArray(b) && b.length === 5 && b.slice(0, 4).every(x => typeof x === 'number' && x >= 0 && x <= 1) && ['dark', 'light'].includes(b[4]);
  if (!(m.width > 0 && m.height > 0) || !Array.isArray(m.boxes) || !m.boxes.every(box)) throw bad(`${f}: needs width, height and boxes [x, y, w, h, "dark"|"light"]`);
  if (typeof m.img !== 'string' || !/^[a-z0-9_]+\.(jpg|png)$/.test(m.img) || !fs.existsSync(`${MEMES}/${m.img}`)) throw bad(`picture ${JSON.stringify(m.img)} missing in ${MEMES}`);
  return m;
};
function meme(sp) {
  const layout = sp.layout ?? 'split', B = MEME_BOX[layout];
  if (sp.canvas !== 'v' || !B) throw new Error(`"${sp.id}": a meme is a 9:16 card (canvas "v"), layout "split" or "full", got ${JSON.stringify(sp.layout)}`);
  const m = memeLib(sp), texts = sp.text ?? [];
  if (!Array.isArray(texts) || texts.length > m.boxes.length) throw new Error(`"${sp.id}": "${sp.meme}" has ${m.boxes.length} text box(es), got ${JSON.stringify(sp.text)}`);
  if (sp.at !== undefined && !(Array.isArray(sp.at) && sp.at.every(t => typeof t === 'number' && t >= 0 && t < sp.dur)))
    throw new Error(`"${sp.id}": "at" = seconds from the card's start, each 0..dur, got ${JSON.stringify(sp.at)}`);
  const s = Math.min(960 / m.width, B.h / m.height), w = Math.round(m.width * s), h = Math.round(m.height * s);
  const left = Math.round((1080 - w) / 2), top = Math.round(B.y + (B.h - h) / 2);
  const boxes = texts.map((t, i) => {
    const [fx, fy, fw, fh, style] = m.boxes[i], at = (sp.at ?? [])[i] ?? 0.25 + 0.7 * i;
    const size = Math.round(Math.min(fh * h * 0.34, 64));
    return `<div class="tx ${style}" style="left:${(fx * w).toFixed(0)}px;top:${(fy * h).toFixed(0)}px;width:${(fw * w).toFixed(0)}px;height:${(fh * h).toFixed(0)}px;font-size:${size}px;animation:pop .35s ${at.toFixed(2)}s cubic-bezier(.2,1.5,.4,1) both">${esc(t)}</div>`;
  }).join('');
  return `<div class="web ${layout} meme"><div class="mm" style="left:${left}px;top:${top}px;width:${w}px;height:${h}px">`
    + `<img src="${pathToFileURL(`${MEMES}/${m.img}`).href}" style="animation:mmzoom ${sp.dur}s linear both">${boxes}</div>`
    + `<div class="src" style="left:${left}px;top:${top + h + 14}px">${esc(sp.src ?? `mem: ${m.name}`)}</div></div>`;
}
function memeStamp(sp) {
  const m = memeLib(sp), shown = JSON.stringify(m, (k, v) => (k === 'fetched' ? undefined : v));  // download date: a re-fetch is no change
  return crypto.createHash('sha1').update(JSON.stringify(sp)).update(shown).update(fs.readFileSync(`${MEMES}/${m.img}`)).digest('hex');
}
function logoStamp(sp) {
  const f = logoFile(sp), bytes = fs.existsSync(f) ? fs.readFileSync(f) : '';  // missing: endBrand stops the render by name
  return crypto.createHash('sha1').update(JSON.stringify(sp)).update(bytes).digest('hex');
}
function webStamp(sp) {
  const meta = `${outDir}/web/${keyOf(specFile, sp)}.json`;
  const captured = fs.existsSync(meta) ? JSON.parse(fs.readFileSync(meta, 'utf8')).captured : '';
  return crypto.createHash('sha1').update(JSON.stringify([sp, keyOf(specFile, sp), captured])).digest('hex');
}
// "web" cards need their capture first (network): webshot.mjs skips the ones already captured, fails loudly otherwise
if (specs.some(s => s.type === 'web')) {
  const limit = specs.filter(s => s.type === 'web').length * PER_CARD + 60000;  // webshot fails a card itself first
  try { execFileSync('node', [new URL('./webshot.mjs', import.meta.url).pathname, specFile, outDir], { stdio: 'inherit', timeout: limit, killSignal: 'SIGKILL' }); }
  catch { console.error('FAILED gfx: page capture for "web" cards (lines FAILED webshot above)'); process.exit(1); }
}
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: ['--disable-gpu'] });
fs.mkdirSync(outDir, { recursive: true });
async function one(sp) {
  // a "web" card's .mov belongs to its spec and to one capture (a new capture of the same page included): either changes
  // -> rendered again. Other types keep the old rule (the panel moves a changed graphic's .mov aside).
  // a theme belongs to every card's .mov too: a new or changed theme (or none after one) renders the card again
  // a card with a logo belongs to its spec and to the logo file's bytes: a new logo under the same name renders it again
  const out = `${outDir}/${sp.id}.mov`, base = sp.type === 'web' ? webStamp(sp) : sp.type === 'meme' ? memeStamp(sp) : sp.logo ? logoStamp(sp) : null, stamp = `${out}.key`;
  const key = THEME ? `${base ?? ''}|${THEME.key}` : base;
  if (fs.existsSync(out) && (key ? fs.existsSync(stamp) && fs.readFileSync(stamp, 'utf8') === key : !fs.existsSync(stamp))) return;
  // canvas "v" = 9:16 graphic for shorts (1080x1920, own layout in template.html under html.v); default 16:9
  const v = sp.canvas === 'v';
  const page = await browser.newPage({ viewport: v ? { width: 1080, height: 1920 } : { width: 2560, height: 1440 } });
  await page.goto(new URL('./template.html', import.meta.url).href);  // next to this file: a worktree renders with its own template
  if (v) await page.evaluate(() => document.documentElement.classList.add('v'));
  if (THEME) await page.evaluate(css => { for (const [k, val] of Object.entries(css)) document.documentElement.style.setProperty(k, val); }, THEME.css);
  await page.evaluate(h => { document.getElementById('root').innerHTML = h; }, html(sp).replace(/\{\{icon:([a-z0-9-]+)\}\}/g, (m, n) => icon(n)));
  await page.evaluate(() => document.fonts.ready);
  // images (end card logo, web capture) loaded before the first frame; one that cannot load stops the render with its name
  const broken = await page.evaluate(() => Promise.all([...document.images].map(i => i.decode().then(() => null, () => i.src))));
  if (broken.some(Boolean)) { console.error(`FAILED gfx ${sp.id}: image not loaded ${broken.filter(Boolean).join(', ')}`); process.exit(1); }
  // GSAP only on a page with a "count" card (docs/adr/0003-gsap-count-card.md): one paused timeline, seeked to each frame's time -> same frames every run
  if (sp.type === 'count') {
    await page.addScriptTag({ path: GSAP });
    await page.evaluate(([cd, delay, fmt]) => {
      const f = new Function(`return ${fmt}`)(), tl = gsap.timeline({ paused: true });
      const nums = [...document.querySelectorAll('.num')].map(el => ({ el, o: { v: 0 } }));
      nums.forEach(({ o, el }) => tl.to(o, { v: +el.dataset.to, duration: cd, ease: 'power2.out' }, delay));
      window.__seek = t => { tl.seek(t, true); nums.forEach(({ el, o }) => {
        el.textContent = cd <= 0 || t >= delay + cd ? el.dataset.final : f(o.v, +el.dataset.dec, !!el.dataset.group); }); };
    }, [countSeconds(sp.dur), COUNT_DELAY, fmtNum.toString()]);
  }
  if (sp.type === 'maxim') await page.evaluate(([src, hold, mark]) => { window.__seek = new Function(`return ${src}`)()(hold, mark); },
    [maximSeek.toString(), CARET_HOLD, MARK_DUR]);
  const dir = `${outDir}/${sp.id}_frames`; fs.mkdirSync(dir, { recursive: true });
  const n = Math.round(sp.dur * FPS);
  for (let f = 0; f < n; f++) {
    const t = f / FPS;
    await page.evaluate(([t, dur, fadeOut]) => {
      document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
      if (window.__seek) window.__seek(t);
      const r = document.getElementById('root'); const fo = fadeOut;
      r.style.opacity = (window.__noout) ? 1 : t > dur - fo ? Math.max(0, (dur - t) / fo) : 1;
      // a delayed CSS animation that starts on this frame reaches the compositor one frame later: wait for it, else the
      // screenshot can show the previous state (count test: frame 5, the bar's first grow frame, differed between runs)
      return new Promise(res => requestAnimationFrame(() => res()));
    }, [t, sp.dur, FADE_OUT]);
    await page.screenshot({ path: `${dir}/${String(f).padStart(4, '0')}.png`, omitBackground: true });
  }
  await page.close();
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', `${dir}/%04d.png`, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', out]);
  fs.rmSync(dir, { recursive: true });
  if (key) fs.writeFileSync(stamp, key); else fs.rmSync(stamp, { force: true });
  console.log('gfx', sp.id);
}
const q = [...specs]; await Promise.all([0,1,2,3,4,5].map(async () => { while (q.length) await one(q.shift()); }));
await browser.close();
// "behind" cards: behind.py cuts the speaker out of each one's alpha (text behind the head); skipped when nothing changed
if (specs.some(sp => sp.behind)) {
  const PY = '/home/kamil-jan/video-pipeline/matte/.venv/bin/python';
  if (!fs.existsSync(PY)) { console.error('FAILED gfx: "behind" cards need matte/.venv (README: text behind the speaker)'); process.exit(1); }
  try { execFileSync(PY, ['/home/kamil-jan/video-pipeline/behind.py', specFile, outDir], { stdio: 'inherit', timeout: 1800000 }); }
  catch (e) { console.error(`FAILED gfx: behind.py ${e.status ?? e.message}`); process.exit(1); }
}
