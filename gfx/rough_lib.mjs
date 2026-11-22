// Hand-drawn annotations (docs/designs/2026-11-05-visual-upgrade.md item 3): a box, an underline or a circle drawn as two
// slightly different pen strokes, the way rough-notation draws them (MIT, mechanics only: render.ts two passes with a small
// random bow and end offset). The randomness comes from a seed (the piece's id and place), so the same spec draws the same
// strokes in every frame, every render and every still (cache keys and accepted stills stay valid).
// Kamil 2026-11-09 preview: a circle around a flat row turned into a jagged ellipse that cut the rows above and below.

// mulberry32: a small seeded PRNG, numbers in [0, 1)
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// a stable seed from any text (FNV-1a)
export function seedOf(text) {
  let h = 0x811c9dc5;
  for (const ch of String(text)) { h ^= ch.codePointAt(0); h = Math.imul(h, 0x01000193) >>> 0; }
  return h;
}

const r1 = v => Math.round(v * 10) / 10;

// one stroke from (x1, y1) to (x2, y2): the ends a few px off, the middle bowed a little to one side
function stroke(x1, y1, x2, y2, rnd, wob) {
  const len = Math.hypot(x2 - x1, y2 - y1) || 1, off = Math.min(wob, len * 0.04);
  const j = () => (rnd() * 2 - 1) * off;
  const bow = (rnd() * 2 - 1) * Math.min(wob * 1.6, len * 0.02), nx = -(y2 - y1) / len, ny = (x2 - x1) / len;
  const a = [x1 + j(), y1 + j()], b = [x2 + j(), y2 + j()];
  const m1 = [x1 + (x2 - x1) * 0.35 + nx * bow + j() * 0.5, y1 + (y2 - y1) * 0.35 + ny * bow + j() * 0.5];
  const m2 = [x1 + (x2 - x1) * 0.7 + nx * bow + j() * 0.5, y1 + (y2 - y1) * 0.7 + ny * bow + j() * 0.5];
  return `M${r1(a[0])} ${r1(a[1])} C${r1(m1[0])} ${r1(m1[1])},${r1(m2[0])} ${r1(m2[1])},${r1(b[0])} ${r1(b[1])}`;
}

// the shape that fits a box: a flat row (wider than 3x its height) gets a box, a long thin one an underline is asked for
export const autoShape = (w, h) => (w >= 3 * h ? 'box' : 'circle');

// two passes of the four sides of a box, `pad` outside it; wob = how far a pen stroke may wander, px
export function roughBox(x, y, w, h, seed, pad = 14, wob = 6) {
  const rnd = rng(seed), L = x - pad, T = y - pad, R = x + w + pad, B = y + h + pad;
  const pass = () => [stroke(L, T, R, T, rnd, wob), stroke(R, T, R, B, rnd, wob), stroke(R, B, L, B, rnd, wob), stroke(L, B, L, T, rnd, wob)].join(' ');
  return [pass(), pass()];
}

// two passes of a line under the box (the second a little shorter, as a pen goes back)
export function roughUnderline(x, y, w, h, seed, pad = 10, wob = 5) {
  const rnd = rng(seed), yy = y + h + pad;
  return [stroke(x - 4, yy, x + w + 4, yy, rnd, wob), stroke(x + w * 0.04, yy + 5, x + w * 0.96, yy + 3, rnd, wob)];
}

// two passes of an ellipse around the box, each starting at its own angle and overshooting a little
export function roughEllipse(x, y, w, h, seed, pad = 24, wob = 5) {
  const rnd = rng(seed), cx = x + w / 2, cy = y + h / 2, rx = w / 2 + pad, ry = h / 2 + pad;
  const pass = () => {
    const a0 = -2.2 + (rnd() * 2 - 1) * 0.3, n = 40, over = 0.12 + rnd() * 0.1, dr = (rnd() * 2 - 1) * 0.02;
    const pts = Array.from({ length: n + 1 }, (_, i) => {
      const t = i / n, a = a0 + t * (2 * Math.PI + over), k = 1 + dr * t + (rnd() * 2 - 1) * (wob / Math.max(rx, ry)) * 0.4;
      return `${r1(cx + Math.cos(a) * rx * k)} ${r1(cy + Math.sin(a) * ry * k)}`;
    });
    return `M${pts.join(' L')}`;
  };
  return [pass(), pass()];
}

// the paths of an annotation around the box x, y, w, h: shape box | underline | circle | auto
export function annotation(shape, x, y, w, h, seed, pad) {
  const s = shape === 'auto' || !shape ? autoShape(w, h) : shape;
  if (s === 'box') return { shape: s, paths: roughBox(x, y, w, h, seed, pad ?? 14) };
  if (s === 'underline') return { shape: s, paths: roughUnderline(x, y, w, h, seed, pad ?? 10) };
  return { shape: 'circle', paths: roughEllipse(x, y, w, h, seed, pad ?? 24) };
}
