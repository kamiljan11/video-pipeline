// node render.mjs specs.json outdir  -> outdir/<id>.mov (ProRes 4444 + alpha, 2560x1440@30; spec canvas "v" -> 1080x1920)
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import crypto from 'crypto'; import fs from 'fs'; import { execFileSync } from 'child_process';
import { PER_CARD, keyOf, motion } from './webshot_lib.mjs';
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
const html = sp => {
  if (sp.type === 'kw') return kwBox(sp, esc(sp.text));
  if (sp.type === 'count') return kwBox(sp, countParts(sp.text).map(p => typeof p === 'string' ? esc(p)
    : `<span class="num" data-to="${p.value}" data-dec="${p.dec}" data-group="${p.group ? 1 : ''}" data-final="${esc(p.final)}" style="min-width:${numWidth(p.final)}ch">${fmtNum(0, p.dec, p.group)}</span>`).join(''), 'kw count');
  if (sp.type === 'lower') return `<div class="lower"><div class="acc"></div><div class="box"><div class="n">${esc(sp.text)}</div><div class="r">${esc(sp.sub)}</div></div></div>`;
  if (sp.type === 'list') return `<div class="list"><div class="h">${esc(sp.text)}</div>${sp.items.map((x,i)=>`<div class="i" style="animation:slide .45s ${(sp.delays||[])[i]??i}s both">${(sp.icons||[])[i]?`<span class="li">${icon(sp.icons[i])}</span>`:`<b>${i+1}</b>`}<span>${esc(x)}</span></div>`).join('')}</div>`;
  if (sp.type === 'end') return `<div class="endc"><div class="t">${esc(sp.text)}</div><div class="bar"></div><div class="s">${esc(sp.sub)}</div></div>`;
  if (sp.type === 'cta') return `<div class="cta"><div class="btn">${icon('bell')}${esc(sp.text)}</div><div class="s">${esc(sp.sub)}</div></div>`;
  if (sp.type === 'slide') return `<div class="slide"><div class="in">${sp.html}</div>${sp.src?`<div class="src">${esc(sp.src)}</div>`:''}</div>`;
  if (sp.type === 'web') return web(sp);
  if (sp.type === 'maxim') return maxim(sp);
  if (sp.type === 'chap') return `<div class="chap"><div class="no">${esc(sp.sub)}</div><div class="t">${esc(sp.text)}</div></div>`;
};
// "maxim": the sentence typed while it is said (gfx/maxim_lib.mjs); every letter is in the layout from the start (hidden) and the
// caret takes no width, so the lines never re-wrap or shift while typing; window.__seek = maximSeek shows the state at time t
function maxim(sp) {
  const words = maximWords(sp.text), times = wordTimes(words, sp.dur, sp.at), chars = charTimes(words, times, sp.dur);
  const body = words.map(({ w, hl }, i) => `<span class="w${hl ? ' hl' : ''}">${[...w].map((c, j) =>
    `<i data-t="${chars[i][j].toFixed(3)}">${esc(c)}</i>`).join('')}${hl ? `<b class="mk" data-t="${(chars[i].at(-1) + 0.05).toFixed(3)}"></b>` : ''}</span>`).join(' ');
  return `<div class="maxim"><div class="scrim"></div><div class="box"><div class="bar"></div><div class="t">${body}<span class="caret"></span></div></div></div>`;
}
// "web": the cited page in a browser window (capture: webshot.mjs), scrolled to the quote, which is then marked
const WIN = { x: 140, y: 110, w: 1720, view: 1060 };  // 16:9 canvas; the face picture-in-picture sits bottom right
function web(sp) {
  const base = `${outDir}/web/${keyOf(specFile, sp)}`;
  if (!fs.existsSync(`${base}.json`)) throw new Error(`no capture for "${sp.id}": run gfx/webshot.mjs first`);
  const m = JSON.parse(fs.readFileSync(`${base}.json`, 'utf8')), s = WIN.w / m.width;
  const shown = { height: m.height * s, rects: m.rects.map(([x, y, w, h]) => [x * s, y * s, w * s, h * s]) };
  const mo = motion(shown, WIN.view, sp.dur), id = sp.id.replace(/[^\w-]/g, '_');
  const anim = mo.scroll ? `animation:ws_${id} ${mo.scroll}s cubic-bezier(.45,0,.2,1) ${mo.start}s both` : '';
  const marks = shown.rects.map(([x, y, w, h], i) => `<div class="hl" style="left:${x - 6}px;top:${y - 4}px;width:${w + 12}px;height:${h + 8}px;animation:hl .5s ${(mo.mark + i * 0.25).toFixed(2)}s ease-out both"></div>`).join('');
  const day = new Date(m.captured).toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const addr = m.final_url ? m.final_url.replace(/^https:\/\//, '') : (m.host || '');
  const src = sp.src || `Źródło: ${m.host || m.title}${m.title && m.host ? ` · ${m.title}` : ''}${m.kind === 'pdf' ? ` · str. ${m.page}` : ''}`;
  return `<style>@keyframes ws_${id}{from{transform:translateY(0)}to{transform:translateY(-${mo.target.toFixed(0)}px)}}</style>`
    + `<div class="web"><div class="win" style="left:${WIN.x}px;top:${WIN.y}px;width:${WIN.w}px">`
    + `<div class="top"><i></i><i></i><i></i><span class="tab">${esc(m.title || m.host)}</span></div>`
    + `<div class="addr"><span class="lock"></span>${esc(addr)}</div>`
    + `<div class="view" style="height:${WIN.view}px"><div class="shot" style="${anim}"><img src="file://${base}.png" style="width:${WIN.w}px">${marks}</div></div></div>`
    + `<div class="src">${esc(src)} · stan na ${day}</div></div>`;
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
  const out = `${outDir}/${sp.id}.mov`, base = sp.type === 'web' ? webStamp(sp) : null, stamp = `${out}.key`;
  const key = THEME ? `${base ?? ''}|${THEME.key}` : base;
  if (fs.existsSync(out) && (key ? fs.existsSync(stamp) && fs.readFileSync(stamp, 'utf8') === key : !fs.existsSync(stamp))) return;
  // canvas "v" = 9:16 graphic for shorts (1080x1920, own layout in template.html under html.v); default 16:9
  const v = sp.canvas === 'v';
  const page = await browser.newPage({ viewport: v ? { width: 1080, height: 1920 } : { width: 2560, height: 1440 } });
  await page.goto('file:///home/kamil-jan/video-pipeline/gfx/template.html');
  if (v) await page.evaluate(() => document.documentElement.classList.add('v'));
  if (THEME) await page.evaluate(css => { for (const [k, val] of Object.entries(css)) document.documentElement.style.setProperty(k, val); }, THEME.css);
  await page.evaluate(h => { document.getElementById('root').innerHTML = h; }, html(sp).replace(/\{\{icon:([a-z0-9-]+)\}\}/g, (m, n) => icon(n)));
  await page.evaluate(() => document.fonts.ready);
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
