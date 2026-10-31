// node --test gfx/test/*.test.mjs   (pure helpers of the "web" card; the browser part is checked by hand, see README)
import test from 'node:test';
import assert from 'node:assert/strict';
import { checkUrl, allowedRequest, privateIp, findQuote, lines, motion, pdfWords, cacheKey, vZoom, V_MIN_WIN } from '../webshot_lib.mjs';

test('only public https pages are captured', () => {
  assert.equal(checkUrl('https://en.wikipedia.org/wiki/Teleprompter').hostname, 'en.wikipedia.org');
  for (const bad of ['http://example.com/', 'file:///home/kamil-jan/.ssh/id_rsa', 'https://localhost/', 'https://127.0.0.1:8790/',
    'https://10.0.0.1/', 'https://192.168.1.1/', 'https://172.20.0.5/', 'https://169.254.169.254/latest', 'https://[::1]/',
    'https://[fd00::1]/', 'https://router/', 'https://nas.local/', 'https://100.64.0.7/', 'javascript:alert(1)', 'nie adres',
    'https://localhost./', 'https://nas.local./', 'https://metadata.google.internal./', 'https://router./', 'https://2130706433/',
    'https://0x7f.1/', 'https://[::ffff:127.0.0.1]/', 'https://[64:ff9b::7f00:1]/', 'https://[2002:7f00:1::]/', 'https://[::]/']) {
    assert.throws(() => checkUrl(bad), Error, bad);
  }
});

test('addresses: only the public internet passes (a name is checked again after DNS, see netguard)', () => {
  for (const ip of ['8.8.8.8', '151.101.1.69', '2a00:1450:400f:80c::200e']) assert.equal(privateIp(ip), false, ip);
  for (const ip of ['127.0.0.1', '127.0.0.2', '10.1.2.3', '100.127.255.1', '192.168.0.1', '172.31.255.255', '169.254.169.254', '0.0.0.0',
    '224.0.0.1', '::1', '::', '::ffff:10.0.0.1', '64:ff9b::a00:1', '2002:c0a8:101::', '2001:0:4136:e378::', 'fe80::1', 'fd12::1', 'nie-ip']) {
    assert.equal(privateIp(ip), true, ip);
  }
});

test('page subrequests: web and inline data only', () => {
  assert.ok(allowedRequest('https://upload.wikimedia.org/a.png'));
  assert.ok(allowedRequest('http://cdn.example.com/x.js'));
  assert.ok(allowedRequest('data:image/png;base64,AAAA'));
  assert.ok(!allowedRequest('http://127.0.0.1:8790/api/plan'));
  assert.ok(!allowedRequest('file:///etc/passwd'));
  assert.ok(!allowedRequest('ws://localhost:5678/'));
});

test('a quote is found across text nodes, quotes, dashes and line breaks', () => {
  const pieces = [{ text: 'Według raportu ' }, { text: '„95 procent' }, { text: '­ firm\n' }, { text: 'nie widzi zwrotu” — pisze MIT.' }];
  const spans = findQuote(pieces, '95 procent firm nie widzi zwrotu');
  assert.deepEqual(spans.map(s => s.piece), [1, 2, 3]);
  assert.equal(pieces[1].text.slice(spans[0].start, spans[0].end), '95 procent');
  assert.equal(pieces[3].text.slice(spans[2].start, spans[2].end), 'nie widzi zwrotu');
  assert.equal(findQuote(pieces, 'tego zdania tu nie ma'), null);
  assert.throws(() => findQuote(pieces, 'MIT'), /za krótki/);
  const nfd = [{ text: 'Zażółć gęślą jaźń'.normalize('NFD') }];  // decomposed letters (some PDFs and pages)
  const hit = findQuote(nfd, 'gęślą jaźń');
  assert.equal(nfd[0].text.slice(hit[0].start, hit[0].end).normalize('NFC'), 'gęślą jaźń');
  assert.ok(findQuote([{ text: 'Raport ﬁrmy doradczej' }], 'raport firmy'));  // ligature
});

test('rects of one line merge, lines stay apart', () => {
  assert.deepEqual(lines([[10, 100, 50, 20], [60, 102, 40, 18], [0, 130, 30, 20], [0, 0, 0, 0]]), [[10, 100, 90, 20], [0, 130, 30, 20]]);
});

test('motion: scroll to the quote, none when it is already in view, refuse a too short card', () => {
  const far = motion({ height: 6000, rects: [[0, 4000, 100, 30]] }, 1000, 8);
  assert.equal(far.target, 3600);
  assert.ok(far.scroll >= 0.9 && far.scroll <= 2.6 && far.mark > far.start + far.scroll);
  assert.equal(motion({ height: 3000, rects: [[0, 200, 100, 30]] }, 1000, 5).scroll, 0);
  assert.equal(motion({ height: 1200, rects: [[0, 1150, 10, 10]] }, 1000, 6).target, 200);  // never past the end of the shot
  assert.throws(() => motion({ height: 9000, rects: [[0, 8000, 10, 10]] }, 1000, 3), /za krótka/);
});

test('pdftotext words keep page and box', () => {
  const x = '<doc><page width="612"><flow><word xMin="72.0" yMin="100.5" xMax="110.2" yMax="112.0">Ala</word><word xMin="1" yMin="2" xMax="3" yMax="4">&amp;co</word></flow></page><page><word xMin="5" yMin="6" xMax="9" yMax="10">kot</word></page></doc>';
  const w = pdfWords(x);
  assert.deepEqual(w.map(a => [a.page, a.text.trim()]), [[1, 'Ala'], [1, '&co'], [2, 'kot']]);
  assert.deepEqual([w[0].x, w[0].y, Math.round(w[0].w * 10) / 10], [72, 100.5, 38.2]);
});

test('cache key changes with what is captured, not with timing', () => {
  const a = { id: 'w1', type: 'web', dur: 6, url: 'https://a.pl/', find: 'zdanie testowe' };
  assert.equal(cacheKey(a), cacheKey({ ...a, id: 'w2', dur: 9, src: 'inny podpis' }));
  assert.notEqual(cacheKey(a), cacheKey({ ...a, find: 'inne zdanie testowe' }));
  const own = { id: 'w3', type: 'web', dur: 6, img: 'zrzut.png' };
  for (const b of [{ ...own, box: [1, 2, 3, 4] }, { ...own, title: 'Raport' }]) assert.notEqual(cacheKey(own), cacheKey(b));
  assert.notEqual(cacheKey(own, 'aaa'), cacheKey(own, 'bbb'));  // a new file under the same name
});

test('9:16 card: zoomed on the quote, never past the capture edges', () => {
  // a short quote in the middle of a 2400 px capture: the narrowest window (40 % = 960 px) centred on it
  const mid = vZoom({ width: 2400, height: 6000, rects: [[1000, 3000, 400, 40]] }, 960);
  assert.equal(mid.x0, 1200 - 2400 * V_MIN_WIN / 2);
  assert.equal(mid.s, 960 / (2400 * V_MIN_WIN));
  assert.deepEqual(mid.rects[0], [(1000 - mid.x0) * mid.s, 3000 * mid.s, 400 * mid.s, 40 * mid.s]);
  assert.equal(mid.height, 6000 * mid.s);
  // a quote at the left edge: the window starts at 0, not before the page
  assert.equal(vZoom({ width: 2400, height: 3000, rects: [[40, 100, 300, 40]] }, 960).x0, 0);
  // a quote at the right edge: the window ends at the page edge
  const right = vZoom({ width: 2400, height: 3000, rects: [[2200, 100, 180, 40]] }, 960);
  assert.equal(right.x0, 2400 - 2400 * V_MIN_WIN);
  // a quote wider than the narrowest window: wide enough for all its lines plus 5 % each side
  const wide = vZoom({ width: 2400, height: 3000, rects: [[200, 100, 1600, 40], [200, 150, 900, 40]] }, 960);
  assert.equal(wide.s, 960 / (1600 * 1.1));
  assert.ok(wide.rects.every(([x, , w]) => x >= 0 && x + w <= 960));
  // nothing to mark (own screenshot without a box) or a quote as wide as the page: the whole capture
  assert.equal(vZoom({ width: 2400, height: 3000, rects: [] }, 960).s, 960 / 2400);
  assert.equal(vZoom({ width: 1000, height: 3000, rects: [[0, 0, 1000, 40]] }, 960).x0, 0);
});
