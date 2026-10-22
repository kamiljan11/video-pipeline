// Network guard of webshot.mjs: every connection of a "web" capture goes to a PUBLIC address only. A host name alone
// proves nothing (127.0.0.1.nip.io, a Tailscale name, a redirect or DNS rebinding all lead to a local service), so the
// address is checked after DNS and the socket connects to exactly that checked address (no second lookup).
// Node's own requests use guardedLookup; Chrome is sent through startGuardProxy (Playwright also routes loopback
// through a proxy: "<-loopback>"), so redirects, scripts, frames and service workers are covered too.
import dns from 'dns'; import http from 'http'; import net from 'net';
import { blockedIp } from './webshot_lib.mjs';
export { blockedIp };

const refuse = (host, ip) => Object.assign(new Error(`adres lokalny/prywatny: ${host}${ip && ip !== host ? ` -> ${ip}` : ''}`), { code: 'EPRIVATE' });

// a dns.lookup replacement for net/http/https: refuses a name when ANY of its addresses is private
export function guardedLookup(resolve = dns.lookup, isPrivate = blockedIp) {
  return (host, opts, cb) => {
    if (typeof opts === 'function') { cb = opts; opts = {}; }
    resolve(host, { all: true }, (err, addrs) => {
      if (err) return cb(err);
      const bad = addrs.find(a => isPrivate(a.address));
      if (bad || !addrs.length) return cb(refuse(host, bad?.address));
      if (opts.all) return cb(null, addrs);
      cb(null, addrs[0].address, addrs[0].family);
    });
  };
}

// an address literal never reaches lookup(): check it here
const target = (host, isPrivate) => {
  const h = host.replace(/^\[|\]$/g, '');
  if (net.isIP(h) && isPrivate(h)) throw refuse(h);
  return h;
};

// HTTP proxy on 127.0.0.1 (random port) for Chrome: CONNECT (https, wss) and plain http, both through the guard
export function startGuardProxy({ lookup = guardedLookup(), isPrivate = blockedIp } = {}) {
  const srv = http.createServer((req, res) => {
    let u, host;
    try { u = new URL(req.url); if (u.protocol !== 'http:') throw new Error('bad'); host = target(u.hostname, isPrivate); }
    catch { res.writeHead(403).end(); return; }
    const headers = { ...req.headers }; delete headers['proxy-connection']; delete headers['proxy-authorization'];
    const up = http.request({ host, port: u.port || 80, path: u.pathname + u.search, method: req.method, headers, lookup }, r => {
      res.writeHead(r.statusCode, r.headers); r.pipe(res);
    });
    up.on('error', () => { if (!res.headersSent) res.writeHead(403); res.end(); });
    req.pipe(up);
  });
  srv.on('connect', (req, sock, head) => {
    sock.on('error', () => {});
    const m = /^(\[[^\]]+\]|[^:]+):(\d+)$/.exec(req.url || '');
    let host;
    try { if (!m) throw new Error('bad'); host = target(m[1], isPrivate); }
    catch { sock.end('HTTP/1.1 403 Forbidden\r\n\r\n'); return; }
    let open = false;
    const up = net.connect({ host, port: Number(m[2]), lookup }, () => {
      open = true; sock.write('HTTP/1.1 200 Connection Established\r\n\r\n'); up.write(head); up.pipe(sock); sock.pipe(up);
    });
    up.on('error', () => { if (open) sock.destroy(); else sock.end('HTTP/1.1 403 Forbidden\r\n\r\n'); });
    sock.on('close', () => up.destroy());
  });
  return new Promise((ok, fail) => { srv.once('error', fail); srv.listen(0, '127.0.0.1', () => ok(srv)); });
}

// Chrome flags that keep traffic inside the proxy: no QUIC (UDP would skip it), WebRTC only through the proxy
export const chromeArgs = ['--disable-gpu', '--disable-quic', '--force-webrtc-ip-handling-policy=disable_non_proxied_udp'];
export const chromeProxy = (srv) => ({ server: `http://127.0.0.1:${srv.address().port}`, bypass: '<-loopback>' });
