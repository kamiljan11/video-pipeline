// node webshot.mjs specs.json outdir  -> outdir/web/<key>.png + <key>.json for every spec of type "web"
// A "web" card shows the source the speaker cites: the page (or PDF page) in a browser window, scrolled to the quoted
// sentence, which gets marked. Spec: {id, type: "web", dur, url, find: "exact sentence from the page", src?, page?}
// or {id, type: "web", dur, img: "own_screenshot.png", box?: [x, y, w, h], url?, title?} when a site blocks robots
// (captcha / login): take the screenshot yourself, never get around the block.
// Captured once (cache key = url + find + img + page): delete outdir/web/<key>.* to capture the page again.
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import fs from 'fs'; import path from 'path'; import { execFileSync } from 'child_process';
import { VIEW, BEFORE, AFTER, checkUrl, allowedRequest, findQuote, lines, cacheKey, pdfWords } from './webshot_lib.mjs';

const [specFile, outDir] = process.argv.slice(2);
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8')).filter(s => s && s.type === 'web');
const dir = path.join(outDir, 'web'); fs.mkdirSync(dir, { recursive: true });
const TIMEOUT = 45000, MAX_PDF = 60 << 20;
let browser = null;

const size = (png) => execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', png], { encoding: 'utf8' }).trim().split(',').map(Number);
const save = (key, meta) => fs.writeFileSync(path.join(dir, `${key}.json`), JSON.stringify({ ...meta, captured: new Date().toISOString() }, null, 1));

// follow redirects by hand so every hop is checked (fetch would connect to a private host before we could look)
async function head(url) {
  let u = checkUrl(url);
  for (let hop = 0; hop < 6; hop++) {
    const r = await fetch(u, { redirect: 'manual', signal: AbortSignal.timeout(TIMEOUT), headers: { 'Accept-Language': 'pl,en;q=0.8' } });
    if (r.status >= 300 && r.status < 400 && r.headers.get('location')) { await r.body?.cancel(); u = checkUrl(new URL(r.headers.get('location'), u).href); continue; }
    return { res: r, url: u };
  }
  throw new Error('za dużo przekierowań');
}

async function pdf(sp, key, res, url) {
  const len = Number(res.headers.get('content-length') || 0);
  if (len > MAX_PDF) { await res.body?.cancel(); throw new Error(`PDF za duży (${len} B)`); }
  const parts = []; let n = 0;
  for await (const c of res.body) { n += c.length; if (n > MAX_PDF) throw new Error(`PDF za duży (> ${MAX_PDF} B)`); parts.push(c); }
  const buf = Buffer.concat(parts);
  const file = path.join(dir, `${key}.pdf`); fs.writeFileSync(file, buf);
  const words = pdfWords(execFileSync('pdftotext', ['-bbox-layout', file, '-'], { encoding: 'utf8', maxBuffer: 256 << 20 }))
    .filter(w => sp.page == null || w.page === sp.page);
  const spans = findQuote(words, sp.find);
  if (!spans) throw new Error(`nie ma cytatu w PDF${sp.page != null ? ` (str. ${sp.page})` : ''}: „${sp.find}”`);
  const page = words[spans[0].piece].page, k = 216 / 72;  // 216 dpi: a page is ~1840 px wide, the card shows 1720
  execFileSync('pdftoppm', ['-r', '216', '-f', String(page), '-l', String(page), '-png', '-singlefile', file, path.join(dir, key)]);
  const [width, height] = size(path.join(dir, `${key}.png`));
  const rects = lines(spans.filter(s => words[s.piece].page === page).map(s => { const w = words[s.piece]; return [w.x * k, w.y * k, w.w * k, w.h * k]; }));
  const info = execFileSync('pdfinfo', [file], { encoding: 'utf8' }).match(/^Title:[ \t]*(\S.*)$/m);
  save(key, { kind: 'pdf', url: sp.url, final_url: url.href, host: url.hostname, title: info ? info[1].trim() : path.basename(url.pathname), page, width, height, rects });
}

async function page(sp, key, url) {
  browser ??= await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--disable-gpu'] });
  const ctx = await browser.newContext({ viewport: { width: VIEW.width, height: VIEW.height }, deviceScaleFactor: VIEW.scale, locale: 'pl-PL', acceptDownloads: false });
  try {
    await ctx.route('**/*', r => allowedRequest(r.request().url()) ? r.continue() : r.abort());
    const pg = await ctx.newPage();
    const res = await pg.goto(url.href, { waitUntil: 'load', timeout: TIMEOUT });
    if (res && res.status() >= 400) throw new Error(`strona odpowiedziała HTTP ${res.status()}`);
    await pg.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});  // busy pages: go on with what loaded
    const texts = await pg.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']); const nodes = [];
      const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: n => !n.parentElement || skip.has(n.parentElement.tagName) || !n.parentElement.checkVisibility() ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
      while (tw.nextNode()) nodes.push(tw.currentNode);
      window.__vpNodes = nodes;
      return nodes.map(n => n.textContent);
    });
    const spans = findQuote(texts.map(text => ({ text: text + ' ' })), sp.find);
    if (!spans) throw new Error(`nie ma cytatu na stronie (sprawdź brzmienie albo daj własny zrzut "img"): „${sp.find}”`);
    // cookie/newsletter layers are hidden, never answered (no consent is given on Kamil's behalf); never the quote's own box
    await pg.addStyleTag({ content: '#onetrust-banner-sdk,#onetrust-consent-sdk,#CybotCookiebotDialog,#didomi-host,#usercentrics-root,.fc-consent-root,.qc-cmp2-container,.cc-window,#cookie-law-info-bar,.cmplz-cookiebanner{display:none!important}html,body{overflow:visible!important}' });
    await pg.evaluate((pieces) => {
      const quote = pieces.map(i => window.__vpNodes[i]), area = innerWidth * innerHeight;
      for (const el of document.querySelectorAll('body *')) {
        const cs = getComputedStyle(el);
        if ((cs.position !== 'fixed' && cs.position !== 'sticky') || quote.some(n => el.contains(n))) continue;
        const r = el.getBoundingClientRect(), big = r.width * r.height > area * 0.2;
        if (big || /cookie|ciasteczk|consent|zgod|rodo|gdpr|newsletter|subscribe/i.test(el.id + ' ' + el.className + ' ' + (el.innerText || '').slice(0, 300))) el.style.setProperty('display', 'none', 'important');
      }
    }, spans.map(s => s.piece));
    const rectsOf = () => pg.evaluate((spans) => {
      const out = [];
      for (const s of spans) {
        const n = window.__vpNodes[s.piece], r = document.createRange();
        r.setStart(n, Math.min(s.start, n.length)); r.setEnd(n, Math.min(s.end, n.length));
        for (const c of r.getClientRects()) out.push([c.left + scrollX, c.top + scrollY, c.width, c.height]);
      }
      return { rects: out, docH: document.documentElement.scrollHeight };
    }, spans);
    // lazy images above the quote load only when scrolled past: walk down to it, then measure again
    const first = await rectsOf(), qy0 = Math.min(...first.rects.map(r => r[1]));
    for (let y = 0; y < qy0 + AFTER; y += 700) { await pg.evaluate(y => scrollTo(0, y), y); await pg.waitForTimeout(120); }
    await pg.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {});
    await pg.evaluate(() => scrollTo(0, 0)); await pg.waitForTimeout(300);
    const { rects, docH } = await rectsOf();
    if (!rects.length) throw new Error(`cytat jest w ukrytym elemencie strony: „${sp.find}”`);
    const qy = Math.min(...rects.map(r => r[1])), y0 = Math.max(0, Math.floor(qy - BEFORE)), y1 = Math.min(docH, Math.ceil(qy + AFTER));
    await pg.screenshot({ path: path.join(dir, `${key}.png`), fullPage: true, clip: { x: 0, y: y0, width: VIEW.width, height: Math.max(VIEW.height, y1 - y0) } });
    const [width, height] = size(path.join(dir, `${key}.png`));
    const k = width / VIEW.width;
    const final = new URL(pg.url());
    save(key, { kind: 'page', url: sp.url, final_url: final.href, host: final.hostname, title: (await pg.title()).trim(), width, height,
      rects: lines(rects.map(([x, y, w, h]) => [x * k, (y - y0) * k, w * k, h * k])) });
  } finally {
    await ctx.close();
  }
}

function own(sp, key) {
  // a screenshot Kamil made himself: only from the folder of the specs (the project's work directory)
  const root = fs.realpathSync(path.dirname(path.resolve(specFile)));
  const src = fs.realpathSync(path.resolve(root, String(sp.img)));
  if (!src.startsWith(root + path.sep)) throw new Error(`"img" spoza katalogu projektu: ${sp.img}`);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', src, '-frames:v', '1', path.join(dir, `${key}.png`)]);
  const [width, height] = size(path.join(dir, `${key}.png`));
  const box = Array.isArray(sp.box) && sp.box.length === 4 && sp.box.every(Number.isFinite) ? [sp.box] : [];
  const url = typeof sp.url === 'string' && sp.url ? checkUrl(sp.url) : null;
  save(key, { kind: 'img', url: sp.url ?? null, final_url: url?.href ?? null, host: url?.hostname ?? '', title: String(sp.title ?? ''), width, height, rects: box });
}

let failed = 0;
for (const sp of specs) {
  const key = cacheKey(sp);
  if (fs.existsSync(path.join(dir, `${key}.json`)) && fs.existsSync(path.join(dir, `${key}.png`))) continue;
  try {
    if (sp.canvas === 'v') throw new Error('karta "web" jest na razie tylko do filmu 16:9 (canvas "v" nie obsługiwany)');
    if (sp.img) own(sp, key);
    else {
      if (typeof sp.find !== 'string') throw new Error('brak "find" (zdanie ze strony do zaznaczenia)');
      const { res, url } = await head(sp.url);
      if (res.status >= 400) { await res.body?.cancel(); throw new Error(`strona odpowiedziała HTTP ${res.status}`); }
      if (/pdf/i.test(res.headers.get('content-type') || '') || /\.pdf$/i.test(url.pathname)) await pdf(sp, key, res, url);
      else { await res.body?.cancel(); await page(sp, key, url); }
    }
    console.log('webshot', sp.id, key);
  } catch (e) {
    failed++;
    for (const f of ['png', 'json']) fs.rmSync(path.join(dir, `${key}.${f}`), { force: true });  // never a half capture
    console.error(`FAILED webshot ${sp.id} (${sp.url ?? sp.img}): ${e.message}`);
  }
}
await browser?.close();
process.exit(failed ? 1 : 0);
