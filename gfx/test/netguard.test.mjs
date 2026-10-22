// node --test gfx/test/*.test.mjs   (network guard of the "web" card; no internet: names are resolved by a fake DNS,
// 127.0.0.1 plays the public internet, 127.0.0.2 a local service)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'fs'; import http from 'http'; import net from 'net';
import { guardedLookup, startGuardProxy, chromeArgs, chromeProxy, blockedIp } from '../netguard.mjs';
import os from 'os';
import { allowedRequest, checkUrl } from '../webshot_lib.mjs';

const DNS = { 'public.test': '127.0.0.1', 'local.test': '127.0.0.2', 'mixed.test': ['127.0.0.1', '127.0.0.2'] };
const fakeResolve = (host, opts, cb) => {
  const a = DNS[host];
  if (!a) return cb(Object.assign(new Error(`ENOTFOUND ${host}`), { code: 'ENOTFOUND' }));
  cb(null, [].concat(a).map(address => ({ address, family: 4 })));
};
const isPrivate = (ip) => ip !== '127.0.0.1';
const lookup = guardedLookup(fakeResolve, isPrivate);
const listen = (srv, host) => new Promise(ok => srv.listen(0, host, () => ok(srv.address().port)));

test('a name is refused when any of its addresses is private', async () => {
  const look = (h, o) => new Promise(ok => lookup(h, o, (e, a) => ok(e ? e.code : a)));
  assert.equal(await look('public.test', {}), '127.0.0.1');
  assert.deepEqual(await look('public.test', { all: true }), [{ address: '127.0.0.1', family: 4 }]);
  assert.equal(await look('local.test', {}), 'EPRIVATE');
  assert.equal(await look('mixed.test', { all: true }), 'EPRIVATE');  // DNS rebinding: one good address is not enough
});

test("this computer's own addresses are refused even when public (a public IPv6 of the laptop)", () => {
  for (const a of Object.values(os.networkInterfaces()).flat()) assert.equal(blockedIp(a.address), true, a.address);
  assert.equal(blockedIp('8.8.8.8'), false);
  const real = os.networkInterfaces;
  os.networkInterfaces = () => ({ eth0: [{ address: '203.0.113.5' }, { address: '2001:4860::5' }, { address: 'fe80::1%eth0' }] });
  try {  // the same address in any spelling (a page can write it as a URL literal)
    for (const ip of ['203.0.113.5', '::ffff:203.0.113.5', '::ffff:cb00:7105', '2001:4860::5', '2001:4860:0:0:0:0:0:5']) assert.equal(blockedIp(ip), true, ip);
    assert.equal(blockedIp('203.0.113.6'), false);
    assert.throws(() => checkUrl('https://[2001:4860::5]:8790/'), /lokalny\/prywatny/);  // Node's own requests: a literal never meets lookup
  } finally { os.networkInterfaces = real; }
});

test('the proxy tunnels only to checked addresses', async () => {
  const local = net.createServer(s => s.end('SECRET')); const lport = await listen(local, '127.0.0.2');
  const proxy = await startGuardProxy({ lookup, isPrivate }); const pport = proxy.address().port;
  const connect = (target) => new Promise(ok => {
    const s = net.connect(pport, '127.0.0.1', () => s.write(`CONNECT ${target} HTTP/1.1\r\nHost: ${target}\r\n\r\n`));
    let out = ''; s.on('data', d => { out += d; }); s.on('close', () => ok(out)); setTimeout(() => s.destroy(), 1500);
  });
  try {
    for (const t of [`local.test:${lport}`, `127.0.0.2:${lport}`, `[::1]:${lport}`, `nope.test:${lport}`]) {
      const out = await connect(t);
      assert.match(out, /^HTTP\/1\.1 403/, t); assert.doesNotMatch(out, /SECRET/, t);
    }
  } finally { proxy.close(); local.close(); }
});

const CHROME = '/usr/bin/google-chrome';
test('Chrome: a redirect or script to a local service never connects (the proxy checks every hop)', { skip: !fs.existsSync(CHROME) && 'no Chrome' }, async () => {
  const { chromium } = await import('/home/kamil-jan/video-pipeline/node_modules/playwright-core/index.mjs');
  const hits = [];
  const local = http.createServer((q, r) => { hits.push(q.url); r.end('<p>SECRET local service</p>'); });
  const lport = await listen(local, '127.0.0.2');
  const site = http.createServer((q, r) => {
    if (q.url === '/redirect') { r.writeHead(302, { location: `http://local.test:${lport}/via-redirect` }); r.end(); return; }
    if (q.url === '/script') { r.end(`<p>public page</p><script>fetch('http://local.test:${lport}/via-fetch');location='http://local.test:${lport}/via-script'</script>`); return; }
    r.end('<p>public page ok</p>');
  });
  const sport = await listen(site, '127.0.0.1');
  const proxy = await startGuardProxy({ lookup, isPrivate });
  const browser = await chromium.launch({ executablePath: CHROME, args: chromeArgs, proxy: chromeProxy(proxy) });
  try {
    const ctx = await browser.newContext();
    await ctx.route('**/*', r => allowedRequest(r.request().url()) ? r.continue() : r.abort());
    const pg = await ctx.newPage();
    await pg.goto(`http://public.test:${sport}/`);  // control: the proxy does carry public traffic
    assert.match(await pg.textContent('body'), /public page ok/);
    await assert.rejects(pg.goto(`http://public.test:${sport}/redirect`));
    await pg.goto(`http://public.test:${sport}/script`).catch(() => {});
    await pg.waitForTimeout(800);
    assert.deepEqual(hits, []);
  } finally { await browser.close(); proxy.close(); site.close(); local.close(); }
});
