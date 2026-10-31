// node webshot.mjs specs.json outdir  -> outdir/web/<key>.png + <key>.json for every spec of type "web"
// A "web" card shows the source the speaker cites: the page (or PDF page) in a browser window, scrolled to the quoted
// sentence, which gets marked. Spec: {id, type: "web", dur, url, find: "exact sentence from the page", src?, page?}
// or {id, type: "web", dur, img: "own_screenshot.png", box?: [x, y, w, h], url?, title?} when a site blocks robots
// (captcha / login): take the screenshot yourself, never get around the block.
// Captured once (cache key = url + find + img content + page + box + title): delete outdir/web/<key>.* to capture again.
// Network: public addresses only, checked after DNS for every connection (netguard.mjs); Chrome runs sandboxed.
import { chromium } from '/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs';
import fs from 'fs'; import https from 'https'; import path from 'path'; import { execFile } from 'child_process';
import { pathToFileURL } from 'url'; import { promisify } from 'util';
import { viewOf, BEFORE, AFTER, PER_CARD, checkUrl, allowedRequest, blockedIp, findQuote, lines, keyOf, ownImg, pdfWords } from './webshot_lib.mjs';
import { guardedLookup, startGuardProxy, chromeArgs, chromeProxy } from './netguard.mjs';

// poppler/ffmpeg on a hostile or huge file must not hang the render: 120 s each, and killed with the card when it runs
// out of time (async, so the card's timer can fire while a tool works). SIGKILL by hand: execFile's own `signal` sends
// SIGTERM, which a stuck tool may never act on.
const run = promisify(execFile);
const tool = (job, cmd, args) => {
  const p = run(cmd, args, { timeout: 120000, killSignal: 'SIGKILL', encoding: 'utf8', maxBuffer: 256 << 20 });
  const kill = () => p.child.kill('SIGKILL');
  if (job.stop.signal.aborted) kill(); else job.stop.signal.addEventListener('abort', kill, { once: true });
  return p.then(r => r.stdout, e => { throw job.dead ? new Error(`${cmd} przerwany z kartą`) : e; })
    .finally(() => job.stop.signal.removeEventListener('abort', kill));
};
const size = async (job, png) => (await tool(job, 'ffprobe', ['-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', png])).trim().split(',').map(Number);

// Captures every "web" spec not captured yet; returns the number of failed cards (each printed as FAILED webshot <id>).
// opts exist for the tests (gfx/test/webshot_net.test.mjs: fake DNS, local server, short limits); the CLI passes none.
export async function capture(specFile, outDir, opts = {}) {
  const { timeout = 45000, perCard = PER_CARD, maxPdf = 60 << 20, isPrivate = blockedIp, testCa = null } = opts;
  const lookup = guardedLookup(opts.resolve, isPrivate);
  const specs = JSON.parse(fs.readFileSync(specFile, 'utf8')).filter(s => s && s.type === 'web');
  const dir = path.join(outDir, 'web'); fs.mkdirSync(dir, { recursive: true });
  let browser = null, proxy = null;

  // <key>.json is written last and atomically: its presence is what marks a capture as complete
  const save = (job, key, meta) => {
    if (job.dead) throw new Error('karta przerwana');
    const f = path.join(dir, `${key}.json`);
    fs.writeFileSync(`${f}.tmp`, JSON.stringify({ ...meta, captured: new Date().toISOString() }, null, 1)); fs.renameSync(`${f}.tmp`, f);
    return meta.kind;
  };

  const get = (u) => new Promise((ok, fail) => {
    const req = https.get(u, { lookup, timeout, ca: testCa ?? undefined, headers: { 'Accept-Language': 'pl,en;q=0.8' } }, ok);
    req.on('timeout', () => req.destroy(new Error(`brak odpowiedzi w ${timeout / 1000} s: ${u.hostname}`)));
    req.on('error', fail);
  });

  // is it a PDF? Redirects followed by hand so every hop is checked; each connection only to a checked public address
  async function head(raw) {
    let u = checkUrl(raw);
    for (let hop = 0; hop < 6; hop++) {
      const r = await get(u);
      if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location) { r.destroy(); u = checkUrl(new URL(r.headers.location, u).href); continue; }
      return { res: r, url: u };
    }
    throw new Error('za dużo przekierowań');
  }

  async function pdf(job, sp, key, res, url) {
    const len = Number(res.headers['content-length'] || 0);
    if (len > maxPdf) { res.destroy(); throw new Error(`PDF za duży (${len} B)`); }
    const parts = []; let n = 0;
    try {
      for await (const c of res) { n += c.length; if (n > maxPdf) { res.destroy(); throw new Error(`PDF za duży (> ${maxPdf} B)`); } parts.push(c); }
    } catch (e) { throw /za duży/.test(e.message) ? e : new Error(`pobieranie PDF przerwane po ${n} B (${e.message}; brak danych przez ${timeout / 1000} s?)`); }
    if (job.dead) throw new Error('karta przerwana');
    const file = path.join(dir, `${key}.pdf`); fs.writeFileSync(file, Buffer.concat(parts));
    try { return await pdfPage(job, sp, key, url, file); } finally { fs.rmSync(file, { force: true }); }  // the PDF itself is not kept
  }

  async function pdfPage(job, sp, key, url, file) {
    const words = pdfWords(await tool(job, 'pdftotext', ['-bbox-layout', file, '-']))
      .filter(w => sp.page == null || w.page === sp.page);
    const spans = findQuote(words, sp.find);
    if (!spans) throw new Error(`nie ma cytatu w PDF${sp.page != null ? ` (str. ${sp.page})` : ''}: „${sp.find}”`);
    const page = words[spans[0].piece].page, k = 216 / 72;  // 216 dpi: a page is ~1840 px wide, the card shows 1720
    await tool(job, 'pdftoppm', ['-r', '216', '-f', String(page), '-l', String(page), '-png', '-singlefile', file, path.join(dir, key)]);
    const [width, height] = await size(job, path.join(dir, `${key}.png`));
    const rects = lines(spans.filter(s => words[s.piece].page === page).map(s => { const w = words[s.piece]; return [w.x * k, w.y * k, w.w * k, w.h * k]; }));
    const info = (await tool(job, 'pdfinfo', [file])).match(/^Title:[ \t]*(\S.*)$/m);
    return save(job, key, { kind: 'pdf', url: sp.url, final_url: url.href, host: url.hostname, title: info ? info[1].trim() : path.basename(url.pathname), page, width, height, rects });
  }

  async function page(job, sp, key, url) {
    proxy ??= await startGuardProxy({ lookup, isPrivate });
    // sandboxed: the page and its third-party scripts come from the internet (Playwright adds --no-sandbox otherwise)
    if (browser && !browser.isConnected()) browser = null;  // Chrome died (crash, out of memory): start a new one
    browser ??= await chromium.launch({ executablePath: '/usr/bin/google-chrome', chromiumSandbox: true, args: chromeArgs, proxy: chromeProxy(proxy) });
    const VIEW = viewOf(sp);  // 9:16 card: phone width (webshot_lib VIEW_V)
    const ctx = await browser.newContext({ viewport: { width: VIEW.width, height: VIEW.height }, deviceScaleFactor: VIEW.scale, locale: 'pl-PL',
      acceptDownloads: false, ignoreHTTPSErrors: Boolean(testCa) });
    try {
      await ctx.route('**/*', r => allowedRequest(r.request().url()) ? r.continue() : r.abort());
      const pg = await ctx.newPage();
      const res = await pg.goto(url.href, { waitUntil: 'load', timeout });
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
      const hideLayers = () => pg.evaluate((pieces) => {
        const quote = pieces.map(i => window.__vpNodes[i]), area = innerWidth * innerHeight;
        for (const el of document.querySelectorAll('body *')) {
          if (quote.some(n => el.contains(n))) continue;
          // a consent layer in the page flow (intelligentcio.com: div.cf_modal_container, position static) is known by its
          // id/class only: by its text it would also hit an article that talks about cookies
          if (/cookie|consent|gdpr|cmp-|cf_modal/i.test(el.id + ' ' + el.className)) { el.style.setProperty('display', 'none', 'important'); continue; }
          const cs = getComputedStyle(el);
          if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
          const r = el.getBoundingClientRect(), big = r.width * r.height > area * 0.2;
          if (big || /cookie|ciasteczk|consent|zgod|rodo|gdpr|newsletter|subscribe/i.test(el.id + ' ' + el.className + ' ' + (el.innerText || '').slice(0, 300))) el.style.setProperty('display', 'none', 'important');
        }
      }, spans.map(s => s.piece));
      await hideLayers();
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
      await hideLayers();  // a consent layer that came in while scrolling (2026-10-31: intelligentcio.com at phone width)
      const { rects, docH } = await rectsOf();
      if (!rects.length) throw new Error(`cytat jest w ukrytym elemencie strony: „${sp.find}”`);
      if (!allowedRequest(pg.url())) throw new Error(`strona przekierowała na adres lokalny: ${pg.url().slice(0, 80)}`);
      const qy = Math.min(...rects.map(r => r[1])), y0 = Math.max(0, Math.floor(qy - BEFORE)), y1 = Math.min(docH, Math.ceil(qy + AFTER));
      if (job.dead) throw new Error('karta przerwana');
      await pg.screenshot({ path: path.join(dir, `${key}.png`), fullPage: true, clip: { x: 0, y: y0, width: VIEW.width, height: Math.max(VIEW.height, y1 - y0) } });
      const [width, height] = await size(job, path.join(dir, `${key}.png`));
      const k = width / VIEW.width, final = new URL(pg.url());
      return save(job, key, { kind: 'page', url: sp.url, final_url: final.href, host: final.hostname, title: (await pg.title()).trim(), width, height, phone: sp.canvas === 'v',
        rects: lines(rects.map(([x, y, w, h]) => [x * k, (y - y0) * k, w * k, h * k])) });
    } finally {
      await ctx.close().catch(() => {});  // already gone when the card ran out of time
    }
  }

  async function own(job, sp, key) {
    // a screenshot Kamil made himself: a plain file name in the folder of the specs (the project's work directory)
    const src = ownImg(specFile, sp);
    await tool(job, 'ffmpeg', ['-v', 'error', '-y', '-f', 'image2', '-pattern_type', 'none', '-i', src, '-frames:v', '1', path.join(dir, `${key}.png`)]);
    const [width, height] = await size(job, path.join(dir, `${key}.png`));
    const box = Array.isArray(sp.box) && sp.box.length === 4 && sp.box.every(Number.isFinite) ? [sp.box] : [];
    const url = typeof sp.url === 'string' && sp.url ? checkUrl(sp.url) : null;
    return save(job, key, { kind: 'img', url: sp.url ?? null, final_url: url?.href ?? null, host: url?.hostname ?? '', title: String(sp.title ?? ''), width, height, rects: box });
  }

  async function one(job, sp, key) {
    if (sp.img) return own(job, sp, key);
    if (typeof sp.find !== 'string') throw new Error('brak "find" (zdanie ze strony do zaznaczenia)');
    const { res, url } = await head(sp.url);
    if (/pdf/i.test(res.headers['content-type'] || '') || /\.pdf$/i.test(url.pathname)) {
      if (res.statusCode >= 400) { res.destroy(); throw new Error(`PDF: serwer odpowiedział HTTP ${res.statusCode}`); }
      return pdf(job, sp, key, res, url);
    }
    res.destroy();
    return page(job, sp, key, url);  // a page's own status is what Chrome gets (a bot check on this request is not final)
  }

  // the same capture (same key) for two cards is made once
  const seen = new Set(), todo = [];
  for (const sp of specs) {
    const key = keyOf(specFile, sp);
    if (seen.has(key) || (fs.existsSync(path.join(dir, `${key}.json`)) && fs.existsSync(path.join(dir, `${key}.png`)))) continue;
    seen.add(key); todo.push([sp, key]);
  }
  let failed = 0;
  for (const [sp, key] of todo) {
    const job = { dead: false, stop: new AbortController() }; let timer;
    // one hung page or tool must not hang the render: past the limit the card fails like any other
    const limit = new Promise((_, fail) => { timer = setTimeout(() => fail(new Error(`przekroczony czas ${perCard / 1000} s (strona albo plik nie odpowiada)`)), perCard); });
    const work = one(job, sp, key);
    work.catch(() => {});  // after a timeout its own error no longer matters
    try {
      await Promise.race([work, limit]);
      console.log('webshot', sp.id, key, await work);  // + kind (page/pdf/img): the ADR's metric counts own screenshots
    } catch (e) {
      failed++; job.dead = true; job.stop.abort();  // a tool still running for this card is killed
      if (/przekroczony czas/.test(e.message)) { await browser?.close().catch(() => {}); browser = null; }  // the hung page goes with it
      for (const f of ['png', 'json', 'json.tmp', 'pdf']) fs.rmSync(path.join(dir, `${key}.${f}`), { force: true });  // never a half capture
      console.error(`FAILED webshot ${sp.id} (${sp.url ?? sp.img}): ${e.message}`);
    } finally { clearTimeout(timer); }
  }
  await browser?.close(); proxy?.close();
  return failed;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const [specFile, outDir] = process.argv.slice(2);
  process.exit(await capture(specFile, outDir) ? 1 : 0);  // exit also ends work abandoned by a timeout
}
