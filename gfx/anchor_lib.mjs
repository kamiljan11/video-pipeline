// Pieces attached to ids (docs/designs/2026-11-05-visual-upgrade.md item 2): a line runs `from: "e1"` `to: "e2"`, a ring
// circles `on: "md.0"`, a stamp lands `on: "term"`, a cursor moves `to: "btn"`, measured in the DOM, no hand coordinates.
// Kamil 2026-11-05 (NOTES_LOG 15/16/18): a ring placed by numbers missed its row in s13, a stamp floated in empty space.
// resolveAnchors() runs before scene(): it lays the scene out once without the attached pieces, measures every piece with
// an id (and its rows) in world pixels, then writes plain numbers into the spec, so every drawer and check stays as it was.
import { scene, drawnEls } from './scene_lib.mjs';

export const ON_KINDS = ['ring', 'stamp', 'check'];  // placed on a box
export const END_KINDS = ['line', 'cursor'];  // from / to: a point or a piece
export const GAP = 14;  // px between a line end and the box it leaves or reaches

const isRef = v => typeof v === 'string' && v.length > 0;
export const attached = e => !!e && ((ON_KINDS.includes(e.k) && isRef(e.on)) || (END_KINDS.includes(e.k) && (isRef(e.from) || isRef(e.to))));
export const hasAnchors = sp => sp?.type === 'scene' && drawnEls(sp).els.some(attached);

// where a ray from the box centre towards (tx, ty) leaves the box, `gap` px further out
export function edgePoint(b, tx, ty, gap = GAP) {
  const cx = b.x + b.w / 2, cy = b.y + b.h / 2, dx = tx - cx, dy = ty - cy;
  if (!dx && !dy) return [cx, cy];
  const s = Math.min(dx ? (b.w / 2) / Math.abs(dx) : Infinity, dy ? (b.h / 2) / Math.abs(dy) : Infinity);
  const len = Math.hypot(dx, dy);
  return [Math.round(cx + dx * s + (dx / len) * gap), Math.round(cy + dy * s + (dy / len) * gap)];
}

const centre = b => [b.x + b.w / 2, b.y + b.h / 2];

// the numbers for one attached piece; boxes = {"id": {x, y, w, h}, "id.0": row 0, ...}; own = this piece's size (a stamp)
export function place(e, boxes, own = { w: 0, h: 0 }) {
  const box = ref => {
    const b = boxes[ref];
    if (!b) throw new Error(`"${ref}": no piece with this id on the scene (ids: ${Object.keys(boxes).join(', ') || 'none'})`);
    return b;
  };
  const out = { ...e };  // the ids it was attached to stay readable in _on / _from / _to (stills, debugging)
  for (const k of ['on', 'from', 'to']) if (isRef(e[k])) out[`_${k}`] = e[k];
  if (ON_KINDS.includes(e.k) && isRef(e.on)) {
    const b = box(e.on);
    if (e.k === 'ring') Object.assign(out, { x: b.x, y: b.y, w: b.w, h: b.h });
    // a stamp on the upper right of its piece: a quarter of it over the piece's top edge, the piece's middle left readable
    else if (e.k === 'stamp') Object.assign(out, { x: Math.round(b.x + b.w * 0.5), y: Math.round(b.y - own.h * 0.75) });
    else Object.assign(out, { x: Math.round(b.x + b.w + GAP), y: Math.round(b.y + (b.h - own.h) / 2) });  // a check right beside it
    delete out.on;
  }
  if (END_KINDS.includes(e.k)) {
    const a = isRef(e.from) ? centre(box(e.from)) : e.from, z = isRef(e.to) ? centre(box(e.to)) : e.to;
    if (isRef(e.from)) out.from = e.k === 'cursor' ? a.map(Math.round) : edgePoint(box(e.from), ...z);
    if (isRef(e.to)) out.to = e.k === 'cursor' ? z.map(Math.round) : edgePoint(box(e.to), ...a);
  }
  return out;
}

// in the page: every [data-id] piece and its rows (win/file rows and placeholder lines, term output lines, chat messages) in world pixels, camera and entrances off
export function measureIds() {
  for (const a of document.getAnimations()) a.cancel();
  const world = document.querySelector('.scene .world'), wr = world.getBoundingClientRect(), k = wr.width / world.offsetWidth || 1;
  const rel = r => ({ x: Math.round((r.left - wr.left) / k), y: Math.round((r.top - wr.top) / k), w: Math.round(r.width / k), h: Math.round(r.height / k) });
  const out = {};
  for (const el of world.querySelectorAll('[data-id]')) {
    const id = el.getAttribute('data-id');
    out[id] = rel(el.getBoundingClientRect());
    [...el.querySelectorAll(':scope .bd > :is(.row, .sk, .ol), :scope .msg')].forEach((r, i) => { out[`${id}.${i}`] = rel(r.getBoundingClientRect()); });
  }
  return out;
}

// a page with gfx/template.html for the scene's canvas, as render.mjs and scene_check.mjs open it
export const opener = browser => async sp => {
  const v = sp.canvas === 'v', page = await browser.newPage({ viewport: v ? { width: 1080, height: 1920 } : { width: 2560, height: 1440 } });
  await page.goto(new URL('./template.html', import.meta.url).href);
  if (v) await page.evaluate(() => document.documentElement.classList.add('v'));
  return page;
};

// resolve every attached piece of the scenes in `specs` (in place, also the pieces an "extends" scene keeps in _held);
// open = async sp -> a page with gfx/template.html loaded for the scene's canvas
export async function resolveAnchors(specs, open, esc, icon) {
  for (const sp of specs.filter(hasAnchors)) {
    // a stamp or check is laid out once at 0,0 under its own id to learn its size; lines and rings wait for their targets
    const probe = list => (list ?? []).map((e, i) => (attached(e) && e.k !== 'ring' && ON_KINDS.includes(e.k)
      ? { ...e, on: undefined, x: 0, y: 0, id: `__a${i}` } : e)).filter(e => !attached(e));
    const page = await open(sp);
    try {
      const held = sp._held ? { _held: probe(sp._held).map(e => ({ ...e, id: e.id?.startsWith('__a') ? `__h${e.id}` : e.id })) } : {};
      await page.evaluate(h => { document.getElementById('root').innerHTML = h; }, scene({ ...sp, ...held, els: probe(sp.els) }, esc, icon));
      await page.evaluate(() => document.fonts.ready);
      const boxes = await page.evaluate(measureIds);
      const fix = (list, pre) => list.map((e, i) => (attached(e) ? place(e, boxes, boxes[`${pre}__a${i}`]) : e));
      if (sp._held) sp._held = fix(sp._held, '__h');
      sp.els = fix(sp.els, '');
    } catch (err) { throw new Error(`"${sp.id}": attached piece: ${err.message}`); } finally { await page.close(); }
  }
  return specs;
}
