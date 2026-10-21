// node render.mjs specs.json outdir  -> outdir/<id>.mov (ProRes 4444 + alpha, 2560x1440@30; spec canvas "v" -> 1080x1920)
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import fs from 'fs'; import { execFileSync } from 'child_process';
const [specFile, outDir] = process.argv.slice(2);
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const FPS = 30, esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;');
const icon = n => n ? fs.readFileSync(`/home/kamil-jan/video-pipeline/node_modules/lucide-static/icons/${n}.svg`, 'utf8').replace(/<!--[\s\S]*?-->/g, '') : '';
const html = sp => {
  if (sp.type === 'kw') return `<div class="kw ${sp.side||'right'}">${sp.icon?`<div class="ic">${icon(sp.icon)}</div>`:''}<div class="t">${esc(sp.text)}</div><div class="bar"></div>${sp.sub?`<div class="s">${esc(sp.sub)}</div>`:''}</div>`;
  if (sp.type === 'lower') return `<div class="lower"><div class="acc"></div><div class="box"><div class="n">${esc(sp.text)}</div><div class="r">${esc(sp.sub)}</div></div></div>`;
  if (sp.type === 'list') return `<div class="list"><div class="h">${esc(sp.text)}</div>${sp.items.map((x,i)=>`<div class="i" style="animation:slide .45s ${(sp.delays||[])[i]??i}s both">${(sp.icons||[])[i]?`<span class="li">${icon(sp.icons[i])}</span>`:`<b>${i+1}</b>`}<span>${esc(x)}</span></div>`).join('')}</div>`;
  if (sp.type === 'end') return `<div class="endc"><div class="t">${esc(sp.text)}</div><div class="bar"></div><div class="s">${esc(sp.sub)}</div></div>`;
  if (sp.type === 'cta') return `<div class="cta"><div class="btn">${icon('bell')}${esc(sp.text)}</div><div class="s">${esc(sp.sub)}</div></div>`;
  if (sp.type === 'slide') return `<div class="slide"><div class="in">${sp.html}</div>${sp.src?`<div class="src">${esc(sp.src)}</div>`:''}</div>`;
  if (sp.type === 'chap') return `<div class="chap"><div class="no">${esc(sp.sub)}</div><div class="t">${esc(sp.text)}</div></div>`;
};
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--disable-gpu'] });
fs.mkdirSync(outDir, { recursive: true });
async function one(sp) {
  const out = `${outDir}/${sp.id}.mov`; if (fs.existsSync(out)) return;
  // canvas "v" = 9:16 graphic for shorts (1080x1920, own layout in template.html under html.v); default 16:9
  const v = sp.canvas === 'v';
  const page = await browser.newPage({ viewport: v ? { width: 1080, height: 1920 } : { width: 2560, height: 1440 } });
  await page.goto('file:///home/kamil-jan/video-pipeline/gfx/template.html');
  if (v) await page.evaluate(() => document.documentElement.classList.add('v'));
  await page.evaluate(h => { document.getElementById('root').innerHTML = h; }, html(sp).replace(/\{\{icon:([a-z0-9-]+)\}\}/g, (m, n) => icon(n)));
  await page.evaluate(() => document.fonts.ready);
  const dir = `${outDir}/${sp.id}_frames`; fs.mkdirSync(dir, { recursive: true });
  const n = Math.round(sp.dur * FPS);
  for (let f = 0; f < n; f++) {
    const t = f / FPS;
    await page.evaluate(([t, dur]) => {
      document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
      const r = document.getElementById('root'); const fo = 0.35;
      r.style.opacity = (window.__noout) ? 1 : t > dur - fo ? Math.max(0, (dur - t) / fo) : 1;
    }, [t, sp.dur]);
    await page.screenshot({ path: `${dir}/${String(f).padStart(4, '0')}.png`, omitBackground: true });
  }
  await page.close();
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', `${dir}/%04d.png`, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', out]);
  fs.rmSync(dir, { recursive: true });
  console.log('gfx', sp.id);
}
const q = [...specs]; await Promise.all([0,1,2,3,4,5].map(async () => { while (q.length) await one(q.shift()); }));
await browser.close();
