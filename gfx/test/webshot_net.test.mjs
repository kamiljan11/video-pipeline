// node --test gfx/test/*.test.mjs   (capture() over a real HTTPS server and Chrome, without the internet: a fake DNS maps
// site.test -> 127.0.0.1, which plays the public internet, and local.test -> 127.0.0.2, a local service)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import https from 'https'; import os from 'os'; import path from 'path';
import { execFileSync } from 'child_process';
import { capture } from '../webshot.mjs';
import { keyOf } from '../webshot_lib.mjs';

const CHROME = '/usr/bin/google-chrome';
const QUOTE = 'Dziewięćdziesiąt pięć procent firm nie widzi zwrotu z inwestycji';
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'webshot-net-'));
test.after(() => fs.rmSync(work, { recursive: true, force: true }));

const DNS = { 'site.test': '127.0.0.1', 'local.test': '127.0.0.2' };
const resolve = (host, opts, cb) => DNS[host] ? cb(null, [{ address: DNS[host], family: 4 }]) : cb(Object.assign(new Error(`ENOTFOUND ${host}`), { code: 'ENOTFOUND' }));
const isPrivate = (ip) => ip !== '127.0.0.1';

// a page with the quote far down (the card scrolls to it) and the same text as a PDF, made by Chrome
const PAGE = `<html><head><title>Raport testowy</title></head><body style="margin:0;font:16px sans-serif">
  <p>Wstęp</p><div style="height:3000px"></div><p style="position:absolute;top:3000px;left:100px">${QUOTE}.</p></body></html>`;
// a consent layer in the page flow (not fixed) that comes in only on scroll and covers the quote, as on intelligentcio.com
// (2026-10-31); the paragraph above talks about cookies and must stay: a layer is known by its id/class, not by its text
const CONSENT = `<html><head><title>Zgody</title></head><body style="margin:0;font:16px sans-serif">
  <p id="about">Ten serwis używa plików cookie.</p><div style="height:1500px"></div>
  <p style="position:absolute;top:1500px;left:20px;width:380px">${QUOTE}.</p>
  <script>addEventListener('scroll', () => { if (document.querySelector('.cf_modal_container')) return;
    const d = document.createElement('div'); d.className = 'cf_modal_container';
    d.style.cssText = 'position:absolute;top:1300px;left:0;width:100%;height:600px;background:#f00'; document.body.append(d); });</script></body></html>`;
const PDF_HTML = `<html><body style="margin:0;font:16px sans-serif"><p style="position:absolute;top:300px;left:100px;margin:0">${QUOTE}.</p></body></html>`;

let srv, port, ca, pdfBytes;
test.before(async () => {
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=site.test',
    '-addext', 'subjectAltName=DNS:site.test,DNS:local.test', '-keyout', path.join(work, 'k.pem'), '-out', path.join(work, 'c.pem')], { stdio: 'ignore' });
  ca = fs.readFileSync(path.join(work, 'c.pem'));
  const { chromium } = await import('/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs');
  const b = await chromium.launch({ executablePath: CHROME, chromiumSandbox: true });
  const p = await b.newPage(); await p.setContent(PDF_HTML);
  pdfBytes = await p.pdf({ width: '8.5in', height: '11in', margin: { top: 0, left: 0, right: 0, bottom: 0 } });
  await b.close();
  const routes = {
    '/page': (q, r) => { r.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); r.end(PAGE); },
    '/consent': (q, r) => { r.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); r.end(CONSENT); },
    '/404': (q, r) => { r.writeHead(404, { 'content-type': 'text/html' }); r.end(`<p>${QUOTE}</p>`); },
    '/r1': (q, r) => { r.writeHead(302, { location: '/r2' }); r.end(); },
    '/r2': (q, r) => { r.writeHead(301, { location: `https://site.test:${port}/page` }); r.end(); },
    '/loop': (q, r) => { r.writeHead(302, { location: '/loop' }); r.end(); },
    '/to-local': (q, r) => { r.writeHead(302, { location: `https://local.test:${port}/page` }); r.end(); },
    '/doc.pdf': (q, r) => { r.writeHead(200, { 'content-type': 'application/pdf' }); r.end(pdfBytes); },
    '/gone.pdf': (q, r) => { r.writeHead(503); r.end(); },
    '/silent': () => {},  // never answers
    '/stall.pdf': (q, r) => { r.writeHead(200, { 'content-type': 'application/pdf' }); r.write(pdfBytes.subarray(0, 100)); },  // stops sending
    '/drip.pdf': (q, r) => { r.writeHead(200, { 'content-type': 'application/pdf' }); const t = setInterval(() => r.write('%'), 300); r.on('close', () => clearInterval(t)); },
  };
  srv = https.createServer({ key: fs.readFileSync(path.join(work, 'k.pem')), cert: ca }, (q, r) => (routes[new URL(q.url, 'https://x').pathname] ?? routes['/404'])(q, r));
  await new Promise(ok => srv.listen(0, '127.0.0.1', ok)); port = srv.address().port;
});
test.after(() => { srv?.closeAllConnections(); srv?.close(); });

const card = (id, p, extra = {}) => ({ id, type: 'web', dur: 8, url: `https://site.test:${port}${p}`, find: QUOTE, ...extra });
async function run(specs, limits = {}) {
  const specFile = path.join(work, `${specs[0].id}.json`), out = path.join(work, `out_${specs[0].id}`);
  fs.writeFileSync(specFile, JSON.stringify(specs));
  const errs = [], orig = console.error, log = console.log;
  console.error = (...a) => errs.push(a.join(' ')); console.log = () => {};
  try {
    const failed = await capture(specFile, out, { resolve, isPrivate, testCa: ca, timeout: 2000, perCard: 20000, ...limits });
    const meta = (sp) => { const f = path.join(out, 'web', `${keyOf(specFile, sp)}.json`); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null; };
    return { failed, errs: errs.join('\n'), meta, files: fs.readdirSync(path.join(out, 'web')) };
  } finally { console.error = orig; console.log = log; }
}

test('a page and a PDF are captured with the mark on the quote', { skip: !fs.existsSync(CHROME) && 'no Chrome' }, async () => {
  const page = card('p1', '/r1'), pdf = card('p2', '/doc.pdf');
  const r = await run([page, pdf]);
  assert.equal(r.failed, 0, r.errs);
  const m = r.meta(page);
  assert.deepEqual([m.kind, m.host, m.title, new URL(m.final_url).pathname, m.width], ['page', 'site.test', 'Raport testowy', '/page', 2400]);
  assert.equal(m.rects.length, 1);  // one line; 2400 px wide shot = scale 2, the quote at CSS y 3000 -> 2400 px above it kept
  assert.ok(Math.abs(m.rects[0][1] - 2400 * 2) < 40 && Math.abs(m.rects[0][0] - 200) < 10, JSON.stringify(m.rects));
  const d = r.meta(pdf);  // 216 dpi: 1 CSS px = 0.75 pt = 2.25 px; the quote at CSS (100, 300)
  assert.deepEqual([d.kind, d.page, d.width], ['pdf', 1, 1836]);
  assert.ok(Math.abs(d.rects[0][0] - 225) < 15 && Math.abs(d.rects[0][1] - 675) < 30, JSON.stringify(d.rects));
  assert.ok(!r.files.some(f => f.endsWith('.pdf') || f.endsWith('.tmp')), r.files.join());  // the downloaded PDF is not kept
});

test('network failures fail the card loudly and leave nothing behind', { skip: !fs.existsSync(CHROME) && 'no Chrome' }, async () => {
  const bad = { e404: [card('e404', '/404'), /HTTP 404/], gone: [card('gone', '/gone.pdf'), /PDF: serwer odpowiedział HTTP 503/],
    loop: [card('loop', '/loop'), /za dużo przekierowań/], local: [card('local', '/to-local'), /lokalny\/prywatny: local\.test -> 127\.0\.0\.2/],
    big: [card('big', '/doc.pdf', { page: 1 }), /PDF za duży/], silent: [card('silent', '/silent'), /brak odpowiedzi w 2 s/],
    nofind: [card('nofind', '/page', { find: 'tego zdania nie ma na stronie' }), /nie ma cytatu na stronie/],
    stall: [card('stall', '/stall.pdf'), /pobieranie PDF przerwane po 100 B/], drip: [card('drip', '/drip.pdf'), /przekroczony czas 5 s/] };
  const r = await run(Object.values(bad).map(([sp]) => sp), { maxPdf: 1000, perCard: 5000 });
  assert.equal(r.failed, Object.keys(bad).length, r.errs);
  for (const [id, [, why]] of Object.entries(bad)) assert.match(r.errs, new RegExp(`FAILED webshot ${id} \\(.*\\): .*${why.source}`), id);
  assert.deepEqual(r.files, []);
});

test('a 9:16 card: phone-width shot, a consent layer that comes in on scroll is hidden, a text about cookies stays',
  { skip: !fs.existsSync(CHROME) && 'no Chrome' }, async () => {
  const sp = card('c1', '/consent', { canvas: 'v' });
  const r = await run([sp]);
  assert.equal(r.failed, 0, r.errs);
  const m = r.meta(sp);
  assert.deepEqual([m.width, m.phone], [1290, true]);  // 430 CSS px @3x
  const png = path.join(work, 'out_c1', 'web', `${keyOf(path.join(work, 'c1.json'), sp)}.png`);
  const rgb = ([x, y, w, h]) => [...execFileSync('ffmpeg', ['-v', 'error', '-i', png, '-vf', `crop=${Math.round(w)}:${Math.round(h)}:${Math.round(x)}:${Math.round(y)},scale=1:1:flags=area,format=rgb24`, '-f', 'rawvideo', '-'])];
  const [cr, cg] = rgb(m.rects[0]);
  assert.ok(!(cr > 150 && cg < 100), `the quote is under the red layer: ${cr},${cg}`);
  assert.ok(m.height > 1500 * 3 * 0.5, 'the shot still holds the page down to the quote');
});
