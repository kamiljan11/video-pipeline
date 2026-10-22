// node webshot.mjs specs.json outdir  -> outdir/web/<key>.png + <key>.json for every spec of type "web"
// A "web" card shows the source the speaker cites: the page (or PDF page) in a browser window, scrolled to the quoted
// sentence, which gets marked. Spec: {id, type: "web", dur, url, find: "exact sentence from the page", src?, page?}
// or {id, type: "web", dur, img: "own_screenshot.png", box?: [x, y, w, h], url?, title?} when a site blocks robots
// (captcha / login): take the screenshot yourself, never get around the block.
// Captured once (cache key = url + find + img content + page + box + title): delete outdir/web/<key>.* to capture again.
// Network: public addresses only, checked after DNS for every connection (netguard.mjs).
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import fs from 'fs'; import https from 'https'; import path from 'path'; import { execFileSync } from 'child_process';
import { VIEW, BEFORE, AFTER, checkUrl, allowedRequest, findQuote, lines, keyOf, ownImg, pdfWords } from './webshot_lib.mjs';
import { guardedLookup, startGuardProxy, chromeArgs, chromeProxy } from './netguard.mjs';

const [specFile, outDir] = process.argv.slice(2);
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8')).filter(s => s && s.type === 'web');
const dir = path.join(outDir, 'web'); fs.mkdirSync(dir, { recursive: true });
const TIMEOUT = 45000, MAX_PDF = 60 << 20, PER_CARD = 150000;
const TOOL = { timeout: 120000, killSignal: 'SIGKILL' };  // poppler/ffmpeg on a hostile or huge file must not hang the render
const lookup = guardedLookup();
let browser = null, proxy = null;

const size = (png) => execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', png], { encoding: 'utf8', ...TOOL }).trim().split(',').map(Number);
const save = (key, meta) => fs.writeFileSync(path.join(dir, `${key}.json`), JSON.stringify({ ...meta, captured: new Date().toISOString() }, null, 1));

const get = (u) => new Promise((ok, fail) => {
  const req = https.get(u, { lookup, timeout: TIMEOUT, headers: { 'Accept-Language': 'pl,en;q=0.8' } }, ok);
  req.on('timeout', () => req.destroy(new Error(`brak odpowiedzi w ${TIMEOUT / 1000} s: ${u.hostname}`)));
  req.on('error', fail);
});

// is it a PDF? Redirects followed by hand so every hop is checked; each connection only to a checked public address
async function head(url) {
  let u = checkUrl(url);
  for (let hop = 0; hop < 6; hop++) {
    const r = await get(u);
    if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location) { r.destroy(); u = checkUrl(new URL(r.headers.location, u).href); continue; }
    return { res: r, url: u };
  }
  throw new Error('za dużo przekierowań');
}

async function pdf(sp, key, res, url) {
  const len = Number(res.headers['content-length'] || 0);
  if (len > MAX_PDF) { res.destroy(); throw new Error(`PDF za duży (${len} B)`); }
  const parts = []; let n = 0;
  for await (const c of res) { n += c.length; if (n > MAX_PDF) { res.destroy(); throw new Error(`PDF za duży (> ${MAX_PDF} B)`); } parts.push(c); }
  const file = path.join(dir, `${key}.pdf`); fs.writeFileSync(file, Buffer.concat(parts));
  try { pdfPage(sp, key, url, file); } finally { fs.rmSync(file, { force: true }); }  // the PDF itself is not kept
}

function pdfPage(sp, key, url, file) {
  const words = pdfWords(execFileSync('pdftotext', ['-bbox-layout', file, '-'], { encoding: 'utf8', maxBuffer: 256 << 20, ...TOOL }))
    .filter(w => sp.page == null || w.page === sp.page);
  const spans = findQuote(words, sp.find);
  if (!spans) throw new Error(`nie ma cytatu w PDF${sp.page != null ? ` (str. ${sp.page})` : ''}: „${sp.find}”`);
  const page = words[spans[0].piece].page, k = 216 / 72;  // 216 dpi: a page is ~1840 px wide, the card shows 1720
  execFileSync('pdftoppm', ['-r', '216', '-f', String(page), '-l', String(page), '-png', '-singlefile', file, path.join(dir, key)], TOOL);
  const [width, height] = size(path.join(dir, `${key}.png`));
  const rects = lines(spans.filter(s => words[s.piece].page === page).map(s => { const w = words[s.piece]; return [w.x * k, w.y * k, w.w * k, w.h * k]; }));
  const info = execFileSync('pdfinfo', [file], { encoding: 'utf8', ...TOOL }).match(/^Title:[ \t]*(\S.*)$/m);
  save(key, { kind: 'pdf', url: sp.url, final_url: url.href, host: url.hostname, title: info ? info[1].trim() : path.basename(url.pathname), page, width, height, rects });
}

async function page(sp, key, url) {
  proxy ??= await startGuardProxy();
  browser ??= await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: chromeArgs, proxy: chromeProxy(proxy) });
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
    if (!allowedRequest(pg.url())) throw new Error(`strona przekierowała na adres lokalny: ${pg.url().slice(0, 80)}`);
    const final = new URL(pg.url());
    save(key, { kind: 'page', url: sp.url, final_url: final.href, host: final.hostname, title: (await pg.title()).trim(), width, height,
      rects: lines(rects.map(([x, y, w, h]) => [x * k, (y - y0) * k, w * k, h * k])) });
  } finally {
    await ctx.close();
  }
}

function own(sp, key) {
  // a screenshot Kamil made himself: only from the folder of the specs (the project's work directory)
  const src = ownImg(specFile, sp);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'image2', '-pattern_type', 'none', '-i', src, '-frames:v', '1', path.join(dir, `${key}.png`)], TOOL);
  const [width, height] = size(path.join(dir, `${key}.png`));
  const box = Array.isArray(sp.box) && sp.box.length === 4 && sp.box.every(Number.isFinite) ? [sp.box] : [];
  const url = typeof sp.url === 'string' && sp.url ? checkUrl(sp.url) : null;
  save(key, { kind: 'img', url: sp.url ?? null, final_url: url?.href ?? null, host: url?.hostname ?? '', title: String(sp.title ?? ''), width, height, rects: box });
}

const todo = specs.map(sp => [sp, keyOf(specFile, sp)])
  .filter(([, key]) => !(fs.existsSync(path.join(dir, `${key}.json`)) && fs.existsSync(path.join(dir, `${key}.png`))));
// one hung page or tool must not hang the whole render: past the budget, fail like any other capture
if (todo.length) setTimeout(() => { console.error(`FAILED webshot: przekroczony czas ${todo.length * PER_CARD / 1000} s (strona albo plik nie odpowiada)`); process.exit(1); },
  todo.length * PER_CARD).unref();
let failed = 0;
for (const [sp, key] of todo) {
  try {
    if (sp.canvas === 'v') throw new Error('karta "web" jest na razie tylko do filmu 16:9 (canvas "v" nie obsługiwany)');
    if (sp.img) own(sp, key);
    else {
      if (typeof sp.find !== 'string') throw new Error('brak "find" (zdanie ze strony do zaznaczenia)');
      const { res, url } = await head(sp.url);
      if (/pdf/i.test(res.headers['content-type'] || '') || /\.pdf$/i.test(url.pathname)) {
        if (res.statusCode >= 400) { res.destroy(); throw new Error(`PDF: serwer odpowiedział HTTP ${res.statusCode}`); }
        await pdf(sp, key, res, url);
      } else { res.destroy(); await page(sp, key, url); }  // a page's own status is what Chrome gets (a bot check on this request is not final)
    }
    console.log('webshot', sp.id, key);
  } catch (e) {
    failed++;
    for (const f of ['png', 'json']) fs.rmSync(path.join(dir, `${key}.${f}`), { force: true });  // never a half capture
    console.error(`FAILED webshot ${sp.id} (${sp.url ?? sp.img}): ${e.message}`);
  }
}
await browser?.close(); proxy?.close();
process.exit(failed ? 1 : 0);
