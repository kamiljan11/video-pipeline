// Helpers of webshot.mjs (no browser, no network): which URLs may be captured, where a quote is,
// how the "web" card scrolls, the capture's cache key. Tested by gfx/test/webshot.test.mjs (npm test).
import crypto from 'crypto'; import fs from 'fs'; import net from 'net'; import os from 'os'; import path from 'path';

export const VIEW = { width: 1200, height: 900, scale: 2 };  // CSS px of the captured browser window (narrow = bigger text in the card), device scale
// a 9:16 card (canvas "v") captures a page at phone width: the site's own mobile layout has one column of large text, so a
// narrow column (The Register: 16 px text in a 1200 px page) no longer ends up as small print in the card; scale 3 = 1290 px
export const VIEW_V = { width: 430, height: 932, scale: 3 };
export const viewOf = sp => sp.canvas === 'v' ? VIEW_V : VIEW;
export const BEFORE = 2400, AFTER = 1000;                    // CSS px kept above / below the quote in the shot
export const PER_CARD = 150000;                               // ms a card may take (webshot fails it; render.mjs allows that many)

// Only public https pages: a spec arrives as a file (Syncthing), so it must not turn the capture into a reader of
// local services (the panel on 127.0.0.1, the router) or files (file:///home/...), which would end up in the video.
export function checkUrl(raw) {
  let u;
  try { u = new URL(raw); } catch { throw new Error(`zły adres: ${String(raw).slice(0, 80)}`); }
  if (u.protocol !== 'https:') throw new Error(`tylko https:// (jest ${u.protocol}): ${u.href.slice(0, 80)}`);
  if (privateHost(u.hostname)) throw new Error(`adres lokalny/prywatny: ${u.hostname}`);
  return u;
}

// a NAME is only a first filter: netguard.mjs checks every address it resolves to (privateIp) before connecting
export function privateHost(host) {
  const h = host.toLowerCase().replace(/^\[|\]$/g, '').replace(/\.+$/, '');  // "localhost." = "localhost"
  if (net.isIP(h)) return blockedIp(h);
  return h === 'localhost' || h.endsWith('.localhost') || h.endsWith('.local') || h.endsWith('.internal') || h.endsWith('.home.arpa')
    || !h.includes('.');
}

// everything that is not the public internet: loopback, LAN, Tailscale (100.64/10), link-local, multicast, and the IPv6
// forms that carry an IPv4 address inside (NAT64, 6to4, Teredo; BlockList itself checks IPv4-mapped ::ffff:a.b.c.d against the
// IPv4 list), so none of them is a way around it
const PRIVATE = new net.BlockList();
for (const [a, n] of [['0.0.0.0', 8], ['10.0.0.0', 8], ['100.64.0.0', 10], ['127.0.0.0', 8], ['169.254.0.0', 16], ['172.16.0.0', 12],
  ['192.0.0.0', 24], ['192.168.0.0', 16], ['198.18.0.0', 15], ['224.0.0.0', 3]]) PRIVATE.addSubnet(a, n, 'ipv4');
for (const [a, n] of [['::', 96], ['64:ff9b::', 96], ['64:ff9b:1::', 48], ['2001::', 32], ['2002::', 16],
  ['fc00::', 7], ['fe80::', 10], ['fec0::', 10], ['ff00::', 8]]) PRIVATE.addSubnet(a, n, 'ipv6');
export function privateIp(ip) {
  const v = net.isIP(ip);
  return !v || PRIVATE.check(ip, v === 4 ? 'ipv4' : 'ipv6');
}

// private ranges plus the networks this computer is on: its own public address reaches its local services, and on a
// network with public IPv6 the router, NAS and printer have public addresses in the laptop's own prefix (a cited page
// can point a frame at them). BlockList compares addresses, not spellings: ::ffff:a.b.c.d, hex, uncompressed IPv6 match.
export function blockedIp(ip) {
  if (privateIp(ip)) return true;
  const own = new net.BlockList();
  for (const a of Object.values(os.networkInterfaces()).flat()) {
    const addr = a?.address?.replace(/%.*$/, ''), v = net.isIP(addr), bits = Number(String(a?.cidr).split('/')[1]);
    if (!v) continue;
    const type = v === 4 ? 'ipv4' : 'ipv6';
    // a public IPv6 address from DHCPv6 shows as /128 (the prefix comes as a route): its /64 is still the LAN. Public only:
    // ::1/64 would cover ::ffff:0:0/96, which BlockList matches against every IPv4 address
    const n = v === 6 && !privateIp(addr) ? Math.min(Number.isInteger(bits) && bits > 0 ? bits : 128, 64) : bits;
    if (Number.isInteger(n) && n > 0) own.addSubnet(addr, n, type); else own.addAddress(addr, type);
  }
  return own.check(ip, net.isIP(ip) === 4 ? 'ipv4' : 'ipv6');
}

// requests the page itself makes (images, scripts, redirects): web only, never a private host
export function allowedRequest(raw) {
  try {
    const u = new URL(raw);
    if (u.protocol === 'data:' || u.protocol === 'blob:') return true;
    return (u.protocol === 'https:' || u.protocol === 'http:') && !privateHost(u.hostname);
  } catch { return false; }
}

// quotes are compared on lowercase letters/digits only: typographic quotes, dashes, soft hyphens and line breaks differ
// NFKC: ligatures ("ﬁ") and compatibility forms read as plain letters
export const norm = (s) => String(s).normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');

// pieces = [{text, ...}] in reading order -> [{piece index, start, end}] spans of the quote, or null
export function findQuote(pieces, quote) {
  const q = norm(quote);
  if (q.length < 8) throw new Error(`cytat "find" za krótki (min. 8 liter/cyfr): "${quote}"`);
  let joined = ''; const map = [];  // map[k] = [piece, start, end] (UTF-16 offsets in the piece) of joined[k]
  pieces.forEach((p, i) => {
    // a letter with its combining marks is one unit, so decomposed text ("e" + U+0328) matches a precomposed quote
    for (const m of p.text.matchAll(/\P{M}\p{M}*|\p{M}+/gu)) {
      for (const ch of norm(m[0])) { joined += ch; map.push([i, m.index, m.index + m[0].length]); }
    }
  });
  const at = joined.indexOf(q);
  if (at < 0) return null;
  const out = [];
  for (let k = at; k < at + q.length; k++) {
    const [i, c, e] = map[k], last = out[out.length - 1];
    if (last && last.piece === i) last.end = e; else out.push({ piece: i, start: c, end: e });
  }
  return out;
}

// rects [[x,y,w,h]] of one quote -> one rect per visual line (rects of a line touch vertically)
export function lines(rects) {
  const out = [];
  for (const [x, y, w, h] of [...rects].filter(r => r[2] > 0 && r[3] > 0).sort((a, b) => a[1] - b[1] || a[0] - b[0])) {
    const l = out.find(o => Math.abs(o[1] - y) < Math.min(o[3], h) * 0.5);
    if (l) { const r = Math.max(l[0] + l[2], x + w); l[0] = Math.min(l[0], x); l[2] = r - l[0]; l[3] = Math.max(l[3], h); }
    else out.push([x, y, w, h]);
  }
  return out;
}

// the card's motion: hold the top of the shot, scroll so the quote sits at 40 % of the window, then mark it
export function motion(meta, viewH, dur) {
  const q = meta.rects.length ? Math.min(...meta.rects.map(r => r[1])) : 0;
  const target = Math.max(0, Math.min(q - viewH * 0.4, meta.height - viewH));
  const scroll = target < 1 ? 0 : Math.min(2.6, Math.max(0.9, target / 1400));
  const start = 1.0, mark = start + scroll + 0.25;
  if (mark + 0.6 > dur - 0.8) throw new Error(`karta za krótka: przewijanie i zaznaczenie trwają ${(mark + 1.4).toFixed(1)} s, dur ${dur} s`);
  return { target, start, scroll, mark };
}

// 9:16 "web" card (shorts): a whole 1200 px page in a 960 px card would leave 13 px letters on a phone, so the card shows a
// window of the capture around the quote, at least V_MIN_WIN of its width (480 of 1200 CSS px: 16 px text -> 32 px) and
// wide enough for the quote lines plus 5 % on each side; never wider than the capture. Returns the scale, the window's
// left edge (capture px) and the shown size and marks (card px, x relative to the window) for motion() and the marks.
export const V_MIN_WIN = 0.4;
export const V_MIN_WIN_PHONE = 0.9;  // a phone-width capture (meta.phone) is one column already: only a light zoom
export function vZoom(meta, viewW) {
  const q0 = meta.rects.length ? Math.min(...meta.rects.map(r => r[0])) : 0;
  const q1 = meta.rects.length ? Math.max(...meta.rects.map(r => r[0] + r[2])) : meta.width;
  const win = Math.min(meta.width, Math.max(meta.width * (meta.phone ? V_MIN_WIN_PHONE : V_MIN_WIN), (q1 - q0) * 1.1));
  const x0 = Math.min(Math.max((q0 + q1) / 2 - win / 2, 0), meta.width - win), s = viewW / win;
  return { s, x0, height: meta.height * s, rects: meta.rects.map(([x, y, w, h]) => [(x - x0) * s, y * s, w * s, h * s]) };
}

// the capture depends on these only (not on dur/src/id); imgSum = content hash of an own screenshot, so a new file under the
// same name is captured again. render.mjs keys the card's .mov by the same value.
// a 9:16 card adds "phone" (its own capture at phone width); a 16:9 card's key is the same as before it existed
export const cacheKey = (sp, imgSum = null) => crypto.createHash('sha1').update(JSON.stringify({ v: 2, url: sp.url ?? null,
  find: sp.find ?? null, img: sp.img ?? null, page: sp.page ?? null, box: sp.box ?? null, title: sp.title ?? null, imgSum,
  ...(sp.canvas === 'v' && !sp.img ? { phone: true } : {}) })).digest('hex').slice(0, 16);

export const MAX_IMG = 50 << 20;
// an own screenshot: a plain file name (as the panel accepts it) of a regular file in the folder of the specs
export function ownImg(specFile, sp) {
  const name = String(sp.img);
  if (!name || name.startsWith('.') || /[\\/]/.test(name)) throw new Error(`"img" to sama nazwa pliku z katalogu projektu: ${name}`);
  const root = fs.realpathSync(path.dirname(path.resolve(specFile)));
  const src = fs.realpathSync(path.resolve(root, String(sp.img)));
  if (!src.startsWith(root + path.sep)) throw new Error(`"img" spoza katalogu projektu: ${sp.img}`);
  const st = fs.statSync(src);
  if (!st.isFile() || st.size > MAX_IMG) throw new Error(`"img" to nie plik obrazu do ${MAX_IMG >> 20} MB: ${sp.img}`);
  return src;
}
export const keyOf = (specFile, sp) => {
  let sum = null;
  if (sp.img) try { sum = crypto.createHash('sha1').update(fs.readFileSync(ownImg(specFile, sp))).digest('hex'); } catch { sum = 'brak'; }
  return cacheKey(sp, sum);
};

// pdftotext -bbox-layout output -> [{page, text, x, y, w, h}] words (coordinates in PDF points)
export function pdfWords(xhtml) {
  const out = []; let page = 0;
  const re = /<page\b[^>]*>|<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)<\/word>/g;
  for (const m of xhtml.matchAll(re)) {
    if (!m[1]) { page++; continue; }
    const [x0, y0, x1, y1] = m.slice(1, 5).map(Number);
    out.push({ page, text: decode(m[5]) + ' ', x: x0, y: y0, w: x1 - x0, h: y1 - y0 });
  }
  return out;
}
const decode = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
