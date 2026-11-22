// "scene" card: a full-screen explainer drawn as a dark canvas of small app pieces (windows, files, a terminal, chips, chat,
// lines between them) that come in one by one while they are named, with an optional camera that pans and zooms between
// them. The face sits in the PiP circle bottom right (gfx_types.PIP), so the canvas keeps that corner free.
// Every piece animates with CSS keyframes and inline delays, so render.mjs seeks any frame (document.getAnimations()).
// Spec: {"id", "type": "scene", "dur", "els": [piece…], "cam": [stop…] | "none"}; piece kinds and keys: README › Scena.
// Camera: without "cam" the whole drawing is framed to fill the free part of the frame (left of the face circle). A stop is
// {t, on: "<piece id>" | [ids] | "*", pad, zmax, move} (frame these pieces) or {t, x, y, z} (world point x, y at the top
// left, zoom z). Pieces are measured in the browser (render.mjs calls sceneFit), so nobody has to guess their size.

import { EASE, F, STAGGER, sec } from './motion_tokens.mjs';
import { keepTogether as kt } from './html_lib.mjs';  // a short Polish word stays with its neighbour when a line wraps (side column)
import { annotation, autoShape, seedOf } from './rough_lib.mjs';  // rough box / underline (visual upgrade item 3)

export const W = 2560, H = 1440;
// the PiP circle (assemble.py: pip_size 600, margin 72, 20 px up) + its 40 px frame, with some air
export const PIP_ZONE = { x: W - 600 - 72 - 60, y: H - 600 - 72 - 20 - 60 };
// where a framed drawing goes: left of the face circle (PiP on) or the whole frame ("pip": false), with a margin
// 9:16 (canvas "v", a short): the part above the face box (layout split: gfx_types.SPLIT, box from y 1240, captions at 1150) or
// above the captions over the corner circle (layout corner); 130 px kept free at the top (the Shorts shelf crops covers there)
// 16:9 layout "side" (Kamil 2026-11-05: "zagospodarować dookoła mnie przestrzeń… rzeczy latające dookoła mnie"): the drawing
// on a see-through board in the free field right of the speaker (head x 0.29-0.61 in film 2), he stays full frame, no PiP
export const SIDE = { x: 1640, y: 150, w: 820, h: 1000 };
export const sceneSafe = sp => (sp.canvas === 'v' ? { x: 60, y: 130, w: 960, h: sp.layout === 'corner' ? 1010 : 930 }
  : sp.layout === 'side' ? { x: SIDE.x + 40, y: SIDE.y + 40, w: SIDE.w - 80, h: SIDE.h - 80 }
  : sp.pip === false ? { x: 120, y: 100, w: W - 240, h: H - 200 } : { x: 110, y: 100, w: PIP_ZONE.x - 140, h: H - 200 });
export const TONES = { acc: 'var(--acc)', ok: '#3ecf8e', bad: '#ff5f57', warn: '#f5b84a', blue: '#6ea8fe', orange: '#ff8a3d', mute: '#8b9096',
  lime: '#c6f135' };  // lime = the highlighter on a paper scene (arjay rozbiór 2026-11-16: one lime marker colour, style/REF-shorts-arjay.md)
// pieces tied to another piece's place (a line between two, a cursor path, a ring around a box): a scene with one stays laid
// out as drawn, so it cannot be stacked into the column beside the speaker (screen_grammar keeps it full screen)
export const TIED = ['line', 'cursor', 'ring', 'stamp', 'check', 'tag'];  // pieces placed on another piece (screen_grammar.py TIED, tests/test_screen_grammar.py checks both match)
export const KINDS = ['win', 'file', 'term', 'chip', 'node', 'chat', 'you', 'line', 'stamp', 'text', 'bar', 'stat', 'check', 'cursor', 'ring', 'say', 'toggle', 'steps',
  'table', 'code', 'big', 'tag', 'flow', 'grid', 'bars', 'timeline', 'quiz', 'form'];
// explainer pieces (style/REF-shorts-arjay.md, 2026-11-16): a table with real rows whose cells change, code typed line by line
// with a marker on the phrase being said, a big number, a callout tag with a leader line; their CSS goes into a scene only
// when one is used, so scenes without them are drawn byte for byte as before
export const EXPLAIN = ['table', 'code', 'big', 'tag', 'flow', 'grid', 'bars', 'timeline', 'quiz', 'form'];
// pieces whose shown value can change while the scene is on ("set": [[s, "new value"], ...]): the old value leaves, the
// new one lands with a lime flash behind it (arjay: "version 5" -> "6" on the word, the same box, not a new card)
export const SETTABLE = ['chip', 'text', 'big', 'stat'];
export const LOOKS = ['paper'];
// "cam": "grow": the camera frames only what is on screen at each moment, so the first piece fills the free area and the
// framing widens as pieces come in (the drawing is always whole: NOTES_LOG 50), instead of the whole final drawing small
// from second 0 (2026-11-16: our s_gotowe window filled ~15 % of the frame for 10 s); zoom capped at GROW_ZMAX
export const GROW_ZMAX = 1.5;
// pieces placed by two points or a box, not by x/y alone
const FREE = ['line', 'cursor'];
const ANIMS = { pop: 'scpop .5s cubic-bezier(.2,1.4,.4,1)', up: 'scup .55s cubic-bezier(.2,.9,.2,1)', fade: 'scfade .45s ease-out',
  left: 'scleft .55s cubic-bezier(.2,.9,.2,1)', right: 'scright .55s cubic-bezier(.2,.9,.2,1)', drop: 'scdrop .6s cubic-bezier(.2,1.3,.4,1)',
  blur: 'scblur .4s cubic-bezier(.215,.61,.355,1)' };
// motion budget (render/ref/research/motion.md › 9): word blur-in 0.3 s power3.out, phrase out 0.18 s, cursor move 0.7 s,
// press 0.09 s, ripple 0.5 s, check ring 0.28 s + tick 0.22 s + burst 0.4 s, highlighter 0.4 s, strike 0.25 s
const EASE_IN = 'cubic-bezier(.215,.61,.355,1)', EASE_MOVE = 'cubic-bezier(.45,0,.55,1)', EASE_POP = 'cubic-bezier(.34,1.56,.64,1)';
export const BGS = ['dots', 'blobs'];
const MOVE = 0.9;      // default seconds a camera move takes, ending at its stop's "t"
// L17 (research ledger) "canvas_zoom": a punch-in inside the drawing, the camera closes 1.0 -> 1.25 onto a piece's box in 0.4 s,
// so a long scene gets the emphasis beat a talking shot gets from a punch-in; build_edl.py lists its times (overlay "zooms")
export const CANVAS_ZOOM = { k: 1.25, d: 0.4 };
// S11 (research ledger): a list item ("item": n on a piece) stays at least this long, else it is gone before it is read
export const ITEM_HOLD = 3;
const TYPE_CPS = 28;   // terminal typing speed, characters per second
const LINE_STEP = 0.09; // terminal output lines come in this far apart
// how pieces move: "legacy" = the timings every card had before motion tokens (cards without "motion" draw byte for byte
// as before, so finished films do not change), "tokens" = gfx/motion_tokens.mjs (opt in per card: "motion": "tokens")
const MOTION = {
  legacy: { anims: ANIMS, mark: 'scpop .4s cubic-bezier(.2,1.6,.4,1)', hl: 'scgrow .45s ease-out', rowStep: 0.12, lineStep: LINE_STEP,
    chatStep: 0.5, outLine: 'scfade .15s', msg: 'scup .4s cubic-bezier(.2,.9,.2,1)', draw: EASE_MOVE, lineDraw: 'cubic-bezier(.4,0,.2,1)',
    strike: EASE_MOVE, gone: 'scgone .35s ease-in', out: 'scblurout .18s ease-in', fadeOut: 'scfadeout .3s ease-in' },
  tokens: { anims: { pop: `scpop ${sec(F.base)}s ${EASE.pop}`, up: `scup ${sec(F.base)}s ${EASE.land}`, fade: `scfade ${sec(F.fast)}s ${EASE.land}`,
    left: `scleft ${sec(F.base)}s ${EASE.land}`, right: `scright ${sec(F.base)}s ${EASE.land}`, drop: `scdrop ${sec(F.base)}s ${EASE.pop}`,
    blur: `scblur ${sec(F.base)}s ${EASE.land}` },
    mark: `scpop ${sec(F.base)}s ${EASE.pop}`, hl: `scgrow ${sec(F.base)}s ${EASE.land}`, rowStep: sec(STAGGER.step), lineStep: sec(STAGGER.word),
    chatStep: sec(STAGGER.object), outLine: `scfade ${sec(F.micro)}s ${EASE.land}`, msg: `scup ${sec(F.base)}s ${EASE.land}`, draw: EASE.land,
    lineDraw: EASE.land, strike: EASE.land, gone: `scgone ${sec(F.fast)}s ${EASE.leave}`, out: `scblurout ${sec(F.fast)}s ${EASE.leave}`,
    fadeOut: `scfadeout ${sec(F.fast)}s ${EASE.leave}` },
};
export const MOTIONS = Object.keys(MOTION);

const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d);
const tone = t => TONES[t] ?? TONES.acc;
const f2 = x => (+x).toFixed(2);
// when a piece comes in: its "at", a kinetic line just before its first word, else the card start
const pieceAt = e => num(e.at, e.k === 'say' && Array.isArray(e.words) && e.words.length ? Math.max(0, Math.min(...e.words.map(w => w[1])) - 0.05) : 0);
// lines a "read_along" may point at: a terminal's output lines, a window's or file's rows
const readLines = e => (e.k === 'term' ? (Array.isArray(e.out) ? e.out.length : 0) : (Array.isArray(e.rows) ? e.rows : ['~80', '~55', '~70']).length);

// camera stops -> one keyframes rule over the whole card; each move eases in the "move" seconds before its stop's t
// (self-contained: render.mjs ships its source into the page, where the stops are resolved)
export function camKeyframes(cam, dur) {
  if (!cam || !cam.length) return null;
  const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d), MOVE = 0.9;
  const pts = [];
  const put = (t, s) => pts.push([Math.min(Math.max(t, 0), dur), s]);
  cam.forEach((s, i) => {
    const prev = cam[i - 1];
    if (i === 0) { put(0, s); return; }
    const mv = num(s.move, MOVE), start = Math.max(prev.t, s.t - mv);
    put(start, prev); put(s.t, s);
  });
  put(dur, cam.at(-1));
  const tf = s => `transform:translate(${-num(s.x, 0) * num(s.z, 1)}px,${-num(s.y, 0) * num(s.z, 1)}px) scale(${num(s.z, 1)})`;
  return pts.map(([t, s]) => `${((t / dur) * 100).toFixed(3)}%{${tf(s)};animation-timing-function:cubic-bezier(.65,0,.35,1)}`).join('');
}

// L17 canvas_zoom: each zoom {t, d, k, cx, cy} (cx, cy = world centre of the pieces it frames, measured by sceneFit) becomes
// one more camera stop: from the framing in effect at t, d seconds to the same framing k times closer, the centre staying
// where it is on screen ((c - x') z k = (c - x) z). The next stop of "cam" moves on from there. Self-contained: render.mjs
// ships its source into the page like camKeyframes.
// view (optional, the visible area in scene px) and z.box ([x0, y0, x1, y1] of the pieces it frames): k stops where those pieces
// would leave the view (a push-in on a wide line cut it at both edges, stills 2026-11-08); a zoom left under 1.03 is skipped.
// z.keep (piece indexes) goes on the stop: soloKeys never hides the pieces a stop frames.
export function zoomStops(stops, zooms, view) {
  const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d);
  const out = [...stops];
  for (const z of zooms) {
    let i = 0;
    out.forEach((s, j) => { if (num(s.t, 0) <= z.t) i = j; });
    const b = out[i], bz = num(b.z, 1), bx = num(b.x, 0), by = num(b.y, 0);
    let k = z.k;
    if (view && z.box) {
      const sx = (z.cx - bx) * bz, sy = (z.cy - by) * bz, hw = ((z.box[2] - z.box[0]) / 2) * bz, hh = ((z.box[3] - z.box[1]) / 2) * bz;
      k = Math.min(k, (Math.min(sx - view.x, view.x + view.w - sx) / hw) * 0.97, (Math.min(sy - view.y, view.y + view.h - sy) / hh) * 0.97);
      if (!(k >= 1.03)) continue;
    }
    out.splice(i + 1, 0, { t: z.t + z.d, move: z.d, z: bz * k, x: z.cx - (z.cx - bx) / k, y: z.cy - (z.cy - by) / k, zoom: true, keep: z.keep });
  }
  return out;
}

// 9:16 "solo" (a short): a camera that frames the piece being said in a narrow frame cuts its wide neighbours at the edge
// (film 2 shorts, 2026-11-04: "same się odpalają" half off screen). So in a 9:16 scene a piece that does not fit the free area
// at a camera stop fades out for that stop and back in when a stop frames it again; the last stop ("*") shows the whole
// drawing. pieces: [{x, y, w, h}] in world px; stops: resolved {t, x, y, z, move}; returns per piece [[t, opacity], ...]
// or null when it never hides. Self-contained: render.mjs ships its source into the page like camKeyframes.
export function soloKeys(pieces, stops, dur, safe, tol = 24, keepCut = false) {
  const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d), FADE = 0.25, MOVE = 0.9;
  const fits = (p, s) => {
    const z = num(s.z, 1), x0 = (p.x - num(s.x, 0)) * z, y0 = (p.y - num(s.y, 0)) * z;
    return x0 >= safe.x - tol && y0 >= safe.y - tol && x0 + p.w * z <= safe.x + safe.w + tol && y0 + p.h * z <= safe.y + safe.h + tol;
  };
  return pieces.map((p, i) => {
    const vis = stops.map(s => (Array.isArray(s.keep) && s.keep.includes(i)) || fits(p, s));  // a stop never hides what it frames
    if (vis.every(Boolean) || (keepCut && !vis.some(Boolean))) return null;  // keepCut (16:9, board): never whole stays, scene_check names it
    const keys = [[0, vis[0] ? 1 : 0]];
    for (let i = 1; i < stops.length; i++) {
      if (vis[i] === vis[i - 1]) continue;
      const t = num(stops[i].t, 0), start = Math.max(num(stops[i - 1].t, 0), t - num(stops[i].move, MOVE));
      const [a, b] = vis[i] ? [Math.max(t - FADE, start), t] : [start, Math.min(start + FADE, t)];
      keys.push([a, vis[i] ? 0 : 1], [b, vis[i] ? 1 : 0]);
    }
    keys.push([dur, vis.at(-1) ? 1 : 0]);
    return keys.map(([t, o]) => [Math.min(Math.max(t, 0), dur), o]);
  });
}

// checks the spec by name before anything is drawn; returns the list of problems (empty = fine)
export function checkScene(sp) {
  const bad = [], dur = sp.dur;
  if (!(dur > 0)) bad.push('dur must be > 0');
  if (!Array.isArray(sp.els) || !sp.els.length) bad.push('"els": a list of pieces is required');
  (sp.els || []).forEach((e, i) => {
    const n = `els[${i}]${e && e.k ? ` (${e.k})` : ''}`;
    if (!e || !KINDS.includes(e.k)) { bad.push(`${n}: "k" must be one of ${KINDS.join(', ')}`); return; }
    for (const key of ['at', 'gone', 'dim'])
      if (e[key] !== undefined && !(typeof e[key] === 'number' && e[key] >= 0 && e[key] < dur)) bad.push(`${n}: "${key}" = seconds 0..dur, got ${JSON.stringify(e[key])}`);
    const pt = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
    if (FREE.includes(e.k)) {
      if (!pt(e.from) || !pt(e.to)) bad.push(`${n}: "from" and "to" = [x, y] or a piece id ("e1", a row "md.0"; gfx/anchor_lib.mjs resolveAnchors places it)`);
    } else if (!Number.isFinite(e.x) || !Number.isFinite(e.y)) bad.push(`${n}: "x" and "y" are required${['ring', 'stamp', 'check'].includes(e.k) ? ' (or "on": a piece id, placed by gfx/anchor_lib.mjs resolveAnchors)' : ''}`);
    for (const key of ['click_at', 'on_at', 'back_at', 'out_at', 'out_start', 'strike_at', 'hl_at', 'packet_at', 'x_at'])
      if (e[key] !== undefined && !(typeof e[key] === 'number' && e[key] >= 0 && e[key] < dur)) bad.push(`${n}: "${key}" = seconds 0..dur, got ${JSON.stringify(e[key])}`);
    if (e.pulse_at !== undefined && ![].concat(e.pulse_at).every(t => typeof t === 'number' && t >= 0 && t < dur)) bad.push(`${n}: "pulse_at" = seconds 0..dur (one or a list)`);
    if (e.k === 'check' && e.x_at !== undefined && !(e.x_at >= num(e.at, 0) + 0.6)) bad.push(`${n}: "x_at" = after the tick has drawn ("at" + 0.6 s or later)`);
    if (e.out_start !== undefined && e.out_at !== undefined && !(e.out_start < e.out_at)) bad.push(`${n}: "out_start" (the output starts) = before "out_at" (the terminal leaves)`);
    if (e.k === 'toggle' && e.back_at !== undefined && !(e.back_at > num(e.on_at, num(e.at, 0) + 0.8))) bad.push(`${n}: "back_at" = after the switch flips on ("on_at")`);
    if (e.k === 'ring' && !(e.w > 0 && e.h > 0)) bad.push(`${n}: "w" and "h" = the box to circle`);
    if (e.k === 'ring' && e.shape !== undefined && !['circle', 'box', 'underline'].includes(e.shape)) bad.push(`${n}: "shape" = "circle", "box" or "underline", got ${JSON.stringify(e.shape)}`);
    if (e.k === 'say') {
      if (!Array.isArray(e.words) || !e.words.length || !e.words.every(w => Array.isArray(w) && typeof w[0] === 'string' && typeof w[1] === 'number' && w[1] >= 0 && w[1] < dur))
        bad.push(`${n}: "words" = [["word", seconds], ...], each said inside the card`);
      for (const w of e.words ?? []) if (typeof w?.[0] === 'string' && /^[*[~!]/.test(w[0]) && !/^([*[~!]).+[*\]~!]$/.test(w[0]))
        bad.push(`${n}: word ${JSON.stringify(w[0])} opens a marker it does not close; each word carries its own (*a* *b*, not *a b*)`);
    }
    if (e.k === 'steps') {
      if (!(Number.isInteger(e.total) && e.total > 0)) bad.push(`${n}: "total" = how many items the list has`);
      if (!Array.isArray(e.steps) || !e.steps.length || !e.steps.every(s => Array.isArray(s) && s[0] >= 0 && s[0] < dur && Number.isInteger(s[1])))
        bad.push(`${n}: "steps" = [[seconds, number], ...]`);
    }
    if (e.read_along !== undefined) {  // L16b: the line lights up when it is said
      const lines = readLines(e);
      if (!['term', 'win', 'file'].includes(e.k)) bad.push(`${n}: "read_along" only on a term, win or file (its lines)`);
      else if (!Array.isArray(e.read_along) || !e.read_along.length || !e.read_along.every((s, j, a) => Array.isArray(s) && typeof s[0] === 'number'
        && s[0] >= 0 && s[0] < dur && Number.isInteger(s[1]) && s[1] >= 0 && s[1] < lines && (!j || s[0] > a[j - 1][0])))
        bad.push(`${n}: "read_along" = [[seconds, line], ...] forward in time, line 0..${lines - 1}, said inside the card`);
      else if (e.k !== 'term') for (const [, i] of e.read_along) {  // a grey "~" line stands for text nobody reads
        const r = (e.rows ?? ['~80', '~55', '~70'])[i], t = typeof r === 'string' ? r : r?.t;
        if (typeof t !== 'string' || /^~\d*$/.test(t)) bad.push(`${n}: "read_along" row ${i} is a placeholder line, nothing to read`);
      }
    }
    if (e.item !== undefined) {  // S11: a list item stays long enough to be read
      if (!(Number.isInteger(e.item) && e.item > 0)) bad.push(`${n}: "item" = its number in the list (1, 2, ...)`);
      else {
        const on = Math.min(dur, ...[e.gone, e.out_at].filter(t => typeof t === 'number')) - pieceAt(e);
        if (on < ITEM_HOLD - 1e-9) bad.push(`${n}: list item ${e.item} is on ${on.toFixed(2)} s, it needs ${ITEM_HOLD} s (S11)`);
      }
    }
    if (e.k === 'stat' && e.count !== undefined && !(e.count && Number.isFinite(e.count.to))) bad.push(`${n}: "count" = {"from", "to", "d"} numbers`);
    if (e.k === 'term' && typeof e.cmd !== 'string') bad.push(`${n}: "cmd" = the command, as it was typed`);
    if (e.k === 'term' && e.out !== undefined && !(Array.isArray(e.out) && e.out.every(l => typeof l === 'string'))) bad.push(`${n}: "out" = the real output, a list of lines`);
    const sec0 = v => typeof v === 'number' && v >= 0 && v < dur;
    if (e.set !== undefined) {  // a value that changes on the word
      if (!SETTABLE.includes(e.k)) bad.push(`${n}: "set" only on ${SETTABLE.join(', ')}`);
      else if (e.k === 'stat' && e.count) bad.push(`${n}: "set" and "count" both change the number; use one`);
      else if (!Array.isArray(e.set) || !e.set.length || !e.set.every((v, j, a) => Array.isArray(v) && sec0(v[0]) && v[0] > pieceAt(e)
        && typeof v[1] === 'string' && (!j || v[0] > a[j - 1][0]))) bad.push(`${n}: "set" = [[seconds, "new value"], ...] forward in time, after the piece came in`);
    }
    if (e.k === 'table') {
      const nc = Array.isArray(e.cols) ? e.cols.length : 0;
      if (!nc || !e.cols.every(c => typeof c === 'string')) bad.push(`${n}: "cols" = the column names`);
      if (!Array.isArray(e.rows) || !e.rows.length || !e.rows.every(r => Array.isArray(r) && r.length === nc && r.every(c => typeof c === 'string')))
        bad.push(`${n}: "rows" = [["cell", ...], ...], ${nc} cells each (real rows, not placeholders)`);
      const nr = Array.isArray(e.rows) ? e.rows.length : 0;
      for (const x of Array.isArray(e.state) ? e.state : []) if (!Array.isArray(x)) bad.push(`${n}: "state" entries are lists [seconds, row, state], got ${JSON.stringify(x)}`);
      for (const x of Array.isArray(e.set_cell) ? e.set_cell : []) if (!Array.isArray(x)) bad.push(`${n}: "set_cell" entries are lists [seconds, row, column, value], got ${JSON.stringify(x)}`);
      for (const [t, r, st] of Array.isArray(e.state) ? e.state.filter(Array.isArray) : []) if (!(sec0(t) && Number.isInteger(r) && r >= 0 && r < nr && ['bad', 'ok', 'hl', 'off'].includes(st)))
        bad.push(`${n}: "state" = [[seconds, row 0..${nr - 1}, "bad"|"ok"|"hl"|"off"], ...]`);
      for (const [t, r, c, v] of Array.isArray(e.set_cell) ? e.set_cell.filter(Array.isArray) : []) if (!(sec0(t) && Number.isInteger(r) && r >= 0 && r < nr && Number.isInteger(c) && c >= 0 && c < nc && typeof v === 'string'))
        bad.push(`${n}: "set_cell" = [[seconds, row, column, "new value"], ...]`);
      if (e.state !== undefined && !Array.isArray(e.state)) bad.push(`${n}: "state" is a list`);
      if (e.set_cell !== undefined && !Array.isArray(e.set_cell)) bad.push(`${n}: "set_cell" is a list`);
    }
    if (e.k === 'code') {
      if (!Array.isArray(e.lines) || !e.lines.length || !e.lines.every(l => typeof l === 'string')) bad.push(`${n}: "lines" = the code, one string per line`);
      if (e.lang !== undefined && !['sql', 'js', 'py', 'sh', 'txt'].includes(e.lang)) bad.push(`${n}: "lang" one of sql, js, py, sh, txt`);
      for (const m of Array.isArray(e.mark) ? e.mark : [])
        if (!(Array.isArray(m) && sec0(m[0]) && Number.isInteger(m[1]) && typeof m[2] === 'string' && (e.lines?.[m[1]] ?? '').includes(m[2])))
          bad.push(`${n}: "mark" = [[seconds, line, "text on that line"], ...]; ${JSON.stringify(m?.[2])} is not on line ${m?.[1]}`);
    }
    if (e.k === 'big' && !(typeof e.t === 'string' && e.t)) bad.push(`${n}: "t" = the number or word, as text`);
    if (e.k === 'tag') {
      if (!(typeof e.text === 'string' && e.text)) bad.push(`${n}: "text" = what the tag says`);
      const pt = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
      if (e.to !== undefined && !pt(e.to)) bad.push(`${n}: "to" = [x, y] or a piece id (gfx/anchor_lib.mjs places it)`);
    }
    // round 2 pieces: every list of [seconds, index] names a real step / tile count / row / option, forward from the piece
    const at0 = pieceAt(e), str = v => typeof v === 'string' && v.length > 0, fr01 = v => typeof v === 'number' && v >= 0 && v <= 1;
    const evs = (key, max, what) => {
      if (e[key] === undefined) return;
      if (!Array.isArray(e[key]) || !e[key].every(x => Array.isArray(x) && sec0(x[0]) && Number.isInteger(x[1]) && x[1] >= 0 && x[1] < max))
        bad.push(`${n}: "${key}" = [[seconds, ${what} 0..${max - 1}], ...]`);
    };
    if (e.k === 'flow') {
      const ns = Array.isArray(e.steps) ? e.steps.length : 0;
      if (!(ns >= 2 && ns <= 8 && e.steps.every(s => s && str(s.text) && (s.at === undefined || sec0(s.at)))))
        bad.push(`${n}: "steps" = 2..8 of {"text", "icon", "sub", "at"} (a process drawn as steps; one step is a chip)`);
      if (e.dir !== undefined && !['row', 'col'].includes(e.dir)) bad.push(`${n}: "dir" = "row" or "col"`);
      evs('lit', ns, 'step'); evs('packet', Math.max(ns - 1, 0), 'step it leaves');
      evs('fail', ns, 'step its arrow goes into');
      if ((e.fail ?? []).some(x => Array.isArray(x) && x[1] === 0)) bad.push(`${n}: "fail" names the step the broken arrow goes into (1..${ns - 1}); step 0 has no arrow in`);
    }
    if (e.k === 'grid') {
      if (!(Number.isInteger(e.n) && e.n >= 1 && e.n <= 400)) bad.push(`${n}: "n" = how many tiles, 1..400 (one tile = one thing)`);
      if (e.cols !== undefined && !(Number.isInteger(e.cols) && e.cols >= 1 && e.cols <= 40)) bad.push(`${n}: "cols" = 1..40`);
      const sh = e.show;
      if (sh !== undefined && !(Array.isArray(sh) && sh.length && sh.every((x, j) => Array.isArray(x) && sec0(x[0]) && x[0] >= at0 && Number.isInteger(x[1]) && x[1] >= 1 && x[1] <= e.n
        && (!j || (x[0] > sh[j - 1][0] && x[1] > sh[j - 1][1]))))) bad.push(`${n}: "show" = [[seconds, tiles shown], ...], both growing, up to "n"`);
      const fl = e.fill;
      if (fl !== undefined && !(Array.isArray(fl) && fl.every(x => Array.isArray(x) && sec0(x[0]) && Number.isInteger(x[1]) && x[1] > 0 && (x[2] === undefined || x[2] in TONES))
        && fl.reduce((a, x) => a + (Array.isArray(x) ? x[1] : 0), 0) <= e.n)) bad.push(`${n}: "fill" = [[seconds, how many, tone], ...], together at most "n"`);
    }
    if (e.k === 'bars') {
      const ok = Array.isArray(e.items) && e.items.length >= 1 && e.items.length <= 8
        && e.items.every(it => it && str(it.label) && fr01(it.v) && (it.b === undefined || fr01(it.b)) && (it.at === undefined || sec0(it.at)) && (it.tone === undefined || it.tone in TONES));
      if (!ok) bad.push(`${n}: "items" = 1..8 of {"label", "v": 0..1, "text", "b": 0..1 (two dots), "at", "tone"}`);
      evs('lit', ok ? e.items.length : 0, 'row');
    }
    if (e.k === 'timeline') {
      const ok = Array.isArray(e.lanes) && e.lanes.length >= 1 && e.lanes.length <= 4 && e.lanes.every(l => l && str(l.label) && Array.isArray(l.segs ?? [])
        && (l.segs ?? []).every(g => g && fr01(g.from) && fr01(g.to) && g.to > g.from && (g.at === undefined || sec0(g.at)) && (g.tone === undefined || g.tone in TONES)));
      if (!ok) bad.push(`${n}: "lanes" = 1..4 of {"label", "segs": [{"from": 0..1, "to": 0..1, "text", "tone", "at"}]}`);
      if (e.ticks !== undefined && !(Array.isArray(e.ticks) && e.ticks.every(str))) bad.push(`${n}: "ticks" = the moments written on top, as text`);
      if (e.w !== undefined && !(Number.isFinite(e.w) && e.w >= 700 && e.w <= 2400)) bad.push(`${n}: "w" = width 700..2400 (under 1400 the lane names go above the tracks)`);
      if (e.head !== undefined && !(Array.isArray(e.head) && e.head.every((x, j, a) => Array.isArray(x) && sec0(x[0]) && fr01(x[1]) && (!j || x[0] > a[j - 1][0] + 0.6))))
        bad.push(`${n}: "head" = [[seconds, place 0..1], ...], at least 0.6 s apart`);
    }
    if (e.k === 'quiz') {
      const no = Array.isArray(e.opts) ? e.opts.length : 0;
      if (!(no >= 2 && no <= 6 && e.opts.every(str))) bad.push(`${n}: "opts" = 2..6 options, as text`);
      evs('pick', no, 'option');
      const rv = e.reveal;
      if (rv !== undefined && !(rv && sec0(rv.at) && Number.isInteger(rv.right) && rv.right >= 0 && rv.right < no && (rv.pct === undefined || (Array.isArray(rv.pct) && rv.pct.length === no))))
        bad.push(`${n}: "reveal" = {"at": seconds, "right": option 0..${no - 1}, "pct": [one per option]}`);
    }
    if (e.k === 'form') {
      if (!str(e.title)) bad.push(`${n}: "title" = what the card is ("Product #42")`);
      if (!(Array.isArray(e.fields) && e.fields.every(f => f && str(f.label) && typeof f.value === 'string'
        && (f.set === undefined || (Array.isArray(f.set) && f.set.every((v, j, a) => Array.isArray(v) && sec0(v[0]) && v[0] > at0 && typeof v[1] === 'string' && (!j || v[0] > a[j - 1][0])))))))
        bad.push(`${n}: "fields" = [{"label", "value", "set": [[seconds, "new value"], ...]}]`);
      if (e.button !== undefined && !(e.button && str(e.button.text) && (e.button.press_at === undefined || sec0(e.button.press_at)))) bad.push(`${n}: "button" = {"text", "press_at"}`);
      if (e.note !== undefined && !(e.note && str(e.note.text) && sec0(e.note.at))) bad.push(`${n}: "note" = {"text", "at": seconds, "tone", "icon"}`);
    }
    if (e.tone !== undefined && !(e.tone in TONES)) bad.push(`${n}: "tone" one of ${Object.keys(TONES).join(', ')}`);
    if (e.anim !== undefined && !(e.anim in ANIMS)) bad.push(`${n}: "anim" one of ${Object.keys(ANIMS).join(', ')}`);
  });
  // pieces kept from the scene it "extends" (resolveExtends) can be framed too
  const ids = new Set([...(sp._held || []), ...(sp.els || [])].map(e => e && e.id).filter(Boolean));
  if (Array.isArray(sp.cam)) {
    if (!sp.cam.length) bad.push('"cam": a list of stops, "none" or nothing (frame the whole drawing)');
    sp.cam.forEach((s, i) => {
      if (!(typeof s.t === 'number' && s.t >= 0 && s.t <= dur)) bad.push(`cam[${i}]: "t" = seconds 0..dur`);
      if (i && s.t < sp.cam[i - 1].t) bad.push(`cam[${i}]: stops go forward in time`);
      if (s.z !== undefined && !(s.z >= 0.3 && s.z <= 4)) bad.push(`cam[${i}]: "z" = zoom 0.3..4`);
      if (s.zmax !== undefined && !(s.zmax >= 0.3 && s.zmax <= 4)) bad.push(`cam[${i}]: "zmax" = zoom 0.3..4`);
      for (const on of s.on === undefined || s.on === '*' ? [] : [].concat(s.on))
        if (!ids.has(on)) bad.push(`cam[${i}]: "on" names ${JSON.stringify(on)}, no piece has that "id"`);
    });
  } else if (sp.cam !== undefined && sp.cam !== 'none' && sp.cam !== 'grow') bad.push('"cam": a list of stops, "none", "grow" or nothing (frame the whole drawing)');
  if (sp.cam === 'grow') {
    if (sp.canvas_zoom !== undefined) bad.push('"cam": "grow" frames what is on screen; "canvas_zoom" would fight it');
    if (sp.layout === 'side' && sp.canvas !== 'v') bad.push('"cam": "grow" with layout "side": the side column scrolls on its own');
  }
  if (sp.grow_zmax !== undefined && !(sp.grow_zmax >= 0.5 && sp.grow_zmax <= 3)) bad.push('"grow_zmax" = the largest zoom of "cam": "grow", 0.5..3');
  if (sp.look !== undefined && !LOOKS.includes(sp.look)) bad.push(`"look" one of ${LOOKS.join(', ')} (or nothing: the dark canvas)`);
  if (sp.extends !== undefined && !(typeof sp.extends === 'string' && sp.extends && sp.extends !== sp.id))
    bad.push('"extends" = the id of another scene, whose pieces still on at its end stay on here');
  if (sp.canvas_zoom !== undefined) {  // L17
    if (sp.cam === 'none') bad.push('"canvas_zoom" moves the camera, "cam": "none" has none');
    if (!Array.isArray(sp.canvas_zoom) || !sp.canvas_zoom.length) bad.push('"canvas_zoom" = [{"t", "on", "k", "d"}, ...]');
    else sp.canvas_zoom.forEach((z, i) => {
      const d = num(z?.d, CANVAS_ZOOM.d), k = num(z?.k, CANVAS_ZOOM.k), prev = sp.canvas_zoom[i - 1];
      if (!(typeof z?.t === 'number' && z.t >= 0 && z.t + d <= dur)) bad.push(`canvas_zoom[${i}]: "t" = seconds, the zoom (${d} s) ends inside the card`);
      if (i && !(z?.t >= num(prev?.t, 0) + num(prev?.d, CANVAS_ZOOM.d))) bad.push(`canvas_zoom[${i}]: zooms go forward in time, one after the other`);
      if (!(d >= 0.2 && d <= 1)) bad.push(`canvas_zoom[${i}]: "d" = seconds 0.2..1`);
      if (!(k >= 1.05 && k <= 1.6)) bad.push(`canvas_zoom[${i}]: "k" = how much closer, 1.05..1.6`);
      if (z?.on === undefined) bad.push(`canvas_zoom[${i}]: "on" = the piece id (or ids, or "*") to zoom onto`);
      for (const on of z?.on === undefined || z.on === '*' ? [] : [].concat(z.on))
        if (!ids.has(on)) bad.push(`canvas_zoom[${i}]: "on" names ${JSON.stringify(on)}, no piece has that "id"`);
      // the zoom is one more camera stop (zoomStops): inside a move of "cam" the two would fight over the frame
      if (typeof z?.t === 'number' && Array.isArray(sp.cam)) sp.cam.forEach((s, j) => {
        if (!j || typeof s?.t !== 'number') return;
        const m0 = Math.max(num(sp.cam[j - 1]?.t, 0), s.t - num(s.move, MOVE));
        if (z.t < s.t && z.t + d > m0) bad.push(`canvas_zoom[${i}]: runs into the camera move to cam[${j}] (${m0.toFixed(2)}-${s.t.toFixed(2)} s)`);
      });
    });
  }
  if (sp.bg !== undefined && !BGS.includes(sp.bg)) bad.push(`"bg" one of ${BGS.join(', ')}`);
  if (sp.motion !== undefined && sp.motion !== 'tokens') bad.push('"motion" = "tokens" (gfx/motion_tokens.mjs) or nothing (the timings before tokens)');
  if (sp.canvas === 'v' && sp.cam === 'none') bad.push('canvas "v": the camera frames the drawing above the face box, "cam": "none" has no place there');
  if (sp.canvas === 'v' && !['split', 'corner'].includes(sp.layout)) bad.push('canvas "v": "layout" = "split" or "corner"');
  if (sp.canvas !== 'v' && sp.layout !== undefined && sp.layout !== 'side') bad.push('16:9: "layout" = "side" (beside the speaker) or none (full screen)');
  if (sp.layout === 'side' && sp.cam === 'none') bad.push('layout "side": the camera fits the drawing into the field beside the speaker, "cam": "none" has no place there');
  if (sp.cam === 'none' && sp.pip !== false && sp.canvas !== 'v') {
    // no camera: the frame is the canvas, so a piece reaching into the PiP corner would sit under the face
    (sp.els || []).forEach((e, i) => {
      if (!e || FREE.includes(e.k) || e.k === 'text' || e.k === 'say' || !Number.isFinite(e.x)) return;
      const w = num(e.w, 0), h = num(e.h, 0);
      if (e.x + w > PIP_ZONE.x && e.y + h > PIP_ZONE.y && w && h) bad.push(`els[${i}] (${e.k}): reaches the face corner (x+w > ${PIP_ZONE.x} and y+h > ${PIP_ZONE.y}); move it or give "pip": false`);
    });
  }
  return bad;
}

// one row of a window or file: "~" / "~60" = a placeholder line (60 % wide), "text" = a line of text, or
// {t, mark: "ok"|"bad"|"warn", mark_at, hl, hl_at, tone}
function row(r, esc, icon, at, m = MOTION.legacy) {
  if (typeof r === 'string' && /^~\d*$/.test(r)) return `<div class="sk" style="width:${r.length > 1 ? +r.slice(1) : 70}%"></div>`;
  const o = typeof r === 'string' ? { t: r } : r;
  const mk = o.mark ? `<span class="mk ${o.mark}" style="animation:${m.mark} ${f2(num(o.mark_at, at + 0.4))}s both">${icon({ ok: 'check', bad: 'x', warn: 'triangle-alert' }[o.mark] ?? 'check')}</span>` : '';
  const hl = o.hl ? `<span class="rhl" style="background:${tone(o.tone ?? (o.mark === 'bad' ? 'bad' : 'acc'))};animation:${m.hl} ${f2(num(o.hl_at, at + 0.6))}s both"></span>` : '';
  const body = typeof o.t === 'string' && /^~\d*$/.test(o.t) ? `<div class="sk" style="width:${o.t.length > 1 ? +o.t.slice(1) : 70}%"></div>` : `<span class="rt">${esc(kt(o.t))}</span>`;
  return `<div class="row">${hl}${body}${mk}</div>`;
}

// L16b read_along: [[t, line], ...] -> per line the [from, until] spans it is lit (until = the next step, null = to the end)
const readSpans = e => {
  const out = {};
  (e.read_along ?? []).forEach(([t, i], j, a) => { (out[i] ??= []).push([t, a[j + 1]?.[0] ?? null]); });
  return out;
};
// the band behind a line while it is said: grows in on the word, fades when the next line is said (motion tokens: land / leave)
const readBand = spans => (spans ?? []).map(([t, u]) => `<span class="rhl rd" style="background:${TONES.acc};opacity:.34;animation:scgrow ${sec(F.fast)}s ${EASE.land} ${f2(t)}s both`
  + `${u === null ? '' : `,scfadeout ${sec(F.fast)}s ${EASE.leave} ${f2(u)}s forwards`}"></span>`).join('');

// a short stable id from a piece's spec (keyframes per piece need a unique name; same spec = same name, renders repeat)
const uid = e => 'u' + Math.abs([...JSON.stringify(e)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 7)).toString(36);
const DEF_ANIM = { stamp: 'drop', line: 'fade', check: 'fade', cursor: 'fade', ring: 'fade', say: 'fade', steps: 'blur' };

// one drawer per piece kind (KINDS): (e, c) -> { inner, style } for a piece in the common box (entrance, pulse, dim, gone added
// by piece()), or { html } for a kind that draws its own box (cursor, ring, line). c = { esc, icon, at, tn }.
// A new kind = one entry here + its name in KINDS + its keys in checkScene (and README "Scena").
const idAttr = (e, esc) => (e.id ? ` data-id="${esc(e.id)}"` : '');
const winFile = (e, { esc, icon, at, m }) => {
  const head = e.k === 'win'
    ? `<div class="tb"><i></i><i></i><i></i><span class="ti">${e.icon ? icon(e.icon) : ''}${esc(e.title ?? '')}</span></div>`
    : `<div class="tb fb">${icon(e.icon ?? 'file-text')}<span class="ti">${esc(e.name ?? e.title ?? '')}</span>${e.badge ? `<span class="bdg" style="color:${tone(e.badge.tone)};border-color:${tone(e.badge.tone)};animation:${m.mark} ${f2(num(e.badge.at, at + 0.5))}s both">${esc(e.badge.text)}</span>` : ''}</div>`;
  const rd = readSpans(e);
  const rows = (e.rows ?? ['~80', '~55', '~70']).map((r, i) => {
    const h = row(r, esc, icon, at + 0.15 + i * num(e.step, m.rowStep), m);
    // no read_along on this row: drawn as before; a read row is a text row (checkScene), its band goes first in the row box
    return rd[i] ? h.replace('<div class="row">', `<div class="row">${readBand(rd[i])}`) : h;
  }).join('');
  return { inner: `${head}<div class="bd">${rows}</div>` };
};
// "set": the values a piece shows over time, stacked in one grid cell (the box is as wide as the widest, so nothing jumps);
// each value lands when it is said and leaves when the next one does, a lime flash behind every change. vals = [[t | null, html]]
const swap = (vals, m) => {
  if (vals.length < 2) return vals[0][1];
  return `<span class="sw">${vals.map(([t, h], i) => {
    const nx = vals[i + 1]?.[0], parts = [];
    if (i) parts.push(`scswin .32s ${EASE_POP} ${f2(t)}s both`);
    if (nx !== undefined) parts.push(`${m.fadeOut} ${f2(nx)}s forwards`);
    const flash = i ? `<i class="swf" style="animation:scflash .9s ${EASE_IN} ${f2(t)}s both"></i>` : '';
    return `${flash}<span class="swv"${parts.length ? ` style="animation:${parts.join(',')}"` : ''}>${h}</span>`;
  }).join('')}</span>`;
};
const setVals = (e, first, fmt) => [[null, first], ...(Array.isArray(e.set) ? e.set.map(([t, v]) => [t, fmt(v)]) : [])];
// code colouring: keywords, strings, numbers, comments (a token at a time, each escaped)
const KW = {
  sql: 'select|from|where|and|or|not|null|update|set|insert|into|values|delete|join|left|inner|on|group|by|order|limit|begin|commit|rollback|create|table|index|returning|as|in|is|for|lock|exists|primary|key|unique|transaction',
  js: 'const|let|var|function|return|if|else|for|while|await|async|new|import|from|export|class|try|catch|throw|true|false|null|undefined|of',
  py: 'def|return|if|else|elif|for|while|import|from|class|try|except|raise|True|False|None|with|as|in|not|and|or|lambda|yield|async|await',
  sh: 'git|npm|npx|node|python3?|cd|ls|echo|sudo|rm|cat|grep|curl|export|claude',
  txt: '',
};
export function codeHtml(line, lang, esc) {
  const kw = KW[lang] ?? '', ci = lang === 'sql' ? 'i' : '';
  const re = new RegExp(`(--.*$|//.*$|#.*$)|('[^']*'|"[^"]*"|\`[^\`]*\`)|\\b(\\d+(?:\\.\\d+)?)\\b${kw ? `|\\b(${kw})\\b` : ''}`, `g${ci}`);
  let out = '', last = 0;
  for (const mt of line.matchAll(re)) {
    if (mt[1] && !((lang === 'sql' && mt[1].startsWith('--')) || (['js'].includes(lang) && mt[1].startsWith('//')) || (['py', 'sh'].includes(lang) && mt[1].startsWith('#')))) continue;
    out += esc(line.slice(last, mt.index));
    const cls = mt[1] ? 'cc' : mt[2] ? 'cs' : mt[3] ? 'cn' : 'ck';
    out += `<span class="${cls}">${esc(mt[0])}</span>`;
    last = mt.index + mt[0].length;
  }
  return out + esc(line.slice(last));
}
const PIECES = {
  win: winFile,
  file: winFile,
  term: (e, { esc, at, tn, m }) => {
    const cmdAt = num(e.cmd_at, at + 0.5), typed = e.cmd.length / TYPE_CPS, outAt = num(e.out_start, num(e.out_at, cmdAt + typed + 0.35));  // out_start = the output starts; out_at = the terminal leaves (old specs: out_at alone still starts the output too)
    const rd = readSpans(e);
    const lines = (e.out ?? []).map((l, i) => `<div class="ol${(e.hl ?? []).includes(i) ? ' hot' : ''}" style="animation:${m.outLine} ${f2(outAt + i * m.lineStep)}s both">`
      + `${readBand(rd[i])}${(e.hl ?? []).includes(i) ? `<span class="rhl" style="background:${tn};animation:${m.hl} ${f2(num(e.hl_at, outAt + (e.out.length) * m.lineStep + 0.4))}s both"></span>` : ''}<span>${esc(l)}</span></div>`).join('');
    return { inner: `<div class="tb"><i></i><i></i><i></i><span class="ti">${esc(e.title ?? 'terminal')}</span></div>`
      + `<div class="bd"><div class="cl"><span class="ps">${esc(e.prompt ?? '$')}</span> <span class="cmd" style="--n:${e.cmd.length};animation:sctype ${f2(Math.max(typed, 0.1))}s steps(${Math.max(e.cmd.length, 1)}) ${f2(cmdAt)}s both">${esc(e.cmd)}</span></div>${lines}</div>` };
  },
  chip: (e, { esc, icon, tn, m }) => ({ inner: `<span class="ci" style="background:${tn}">${icon(e.icon ?? 'zap')}</span><span>${e.set ? swap(setVals(e, esc(kt(e.text)), v => esc(kt(v))), m) : esc(kt(e.text))}</span>` }),
  node: (e, { esc, icon, tn }) => {
    const s = num(e.size, 200);
    return { inner: `<div class="nt" style="width:${s}px;height:${s}px;color:${tn};border-color:${tn}">${icon(e.icon ?? 'box')}</div>${e.text ? `<div class="nl">${esc(kt(e.text))}</div>` : ''}${e.sub ? `<div class="ns">${esc(kt(e.sub))}</div>` : ''}` };
  },
  you: (e, { esc, icon }) => ({ inner: `<div class="nt you">${icon('user')}</div><div class="nl">${esc(kt(e.text ?? 'Ty'))}</div>` }),
  chat: (e, { esc, at, m }) => ({
    inner: (e.msgs ?? []).map((g, i) => {
      const t = num(g.at, at + i * num(e.step, m.chatStep)), sk = typeof g.t !== 'string' || /^~\d*$/.test(g.t);
      return `<div class="msg ${g.who === 'me' ? 'me' : 'ai'}" style="animation:${m.msg} ${f2(t)}s both">${sk ? `<div class="sk" style="width:${((g.t ?? '~').length > 1 ? +(g.t ?? '~').slice(1) : 70) * 6}px"></div>` : esc(g.t)}</div>`;
    }).join(''),
  }),
  stamp: (e, { esc, tn }) => ({ style: `color:${tn};border-color:${tn};--r:${num(e.rot, -6)}deg;`, inner: esc(e.text ?? '') }),
  text: (e, { esc, tn, m, pp }) => {
    const fmt = v => esc(kt(v)).replace(/\*([^*]+)\*/g, '<b>$1</b>');
    return { style: `font-size:${num(e.size, 64)}px;color:${e.tone ? tn : pp ? '#16181d' : '#f1f2f4'};${e.w ? '' : 'white-space:nowrap;'}`,
      inner: e.set ? swap(setVals(e, fmt(e.t), fmt), m) : fmt(e.t) };
  },
  bar: (e, { esc, at, tn }) => {
    const v = Math.min(Math.max(num(e.v, 1), 0), 1);
    return { inner: `${e.label ? `<div class="bl">${esc(kt(e.label))}</div>` : ''}<div class="tr"><div class="fl" style="width:${(v * 100).toFixed(1)}%;background:${tn};animation:scgrow ${f2(num(e.d, 1))}s cubic-bezier(.2,.8,.2,1) ${f2(at + 0.3)}s both"></div></div>` };
  },
  stat: (e, { esc, at, tn, m }) => {
    if (!e.count) return { inner: `<div class="sv" style="color:${tn}">${e.set ? swap(setVals(e, esc(e.value ?? ''), esc), m) : esc(e.value ?? '')}</div><div class="sl">${esc(kt(e.label))}</div>` };
    const c = e.count, u = uid(e), d = num(c.d, 1);  // the number counts up to its value while it is said (@property --cnt, seekable)
    return { inner: `<style>@keyframes cnt_${u}{from{--cnt:${Math.round(num(c.from, 0))}}to{--cnt:${Math.round(c.to)}}}</style>`
      + `<div class="sv cnt" data-pre="${esc(c.pre ?? '')}" data-suf="${esc(c.suf ?? '')}" style="color:${tn};animation:cnt_${u} ${f2(d)}s ${EASE_IN} ${f2(num(c.at, at + 0.2))}s both"></div><div class="sl">${esc(kt(e.label))}</div>` };
  },
  check: (e, { at, tn, m }) => {  // ring draws, tick draws, a burst ring and ten sparks fly out (deterministic angles)
    const sz = num(e.size, 120), r = sz / 2 - 6, c = (2 * Math.PI * r).toFixed(0), tk = (sz * 0.9).toFixed(0);
    const sparks = Array.from({ length: 10 }, (_, i) => {
      const a = (i * 36 + 13) * Math.PI / 180, d = sz * (0.62 + 0.09 * (i % 3));
      return `<i class="pt" style="background:${tn};--dx:${(Math.cos(a) * d).toFixed(0)}px;--dy:${(Math.sin(a) * d).toFixed(0)}px;animation:scpart .45s ${EASE_IN} ${f2(at + 0.3)}s both"></i>`;
    }).join('');
    // x_at (visual upgrade item 4, "action instead of a word"): the tick turns into an X, the mark goes red and shakes once;
    // the same two-segment path (M L M L) on both sides so CSS interpolates "d"; without x_at the card is drawn byte for byte as before
    const xa = e.x_at !== undefined ? num(e.x_at, at + 1) : null, u = uid(e), P = (x, y) => `${f2(sz * x)} ${f2(sz * y)}`;
    const xcss = xa === null ? '' : `<style>@keyframes ${u}x{to{d:path("M${P(0.33, 0.33)} L${P(0.67, 0.67)} M${P(0.67, 0.33)} L${P(0.33, 0.67)}");stroke:${TONES.bad}}}`
      + `@keyframes ${u}c{to{stroke:${TONES.bad};fill:${TONES.bad}}}@keyframes ${u}s{0%,100%{transform:none}25%{transform:translateX(-9px)}75%{transform:translateX(9px)}}</style>`;
    const tick = xa === null
      ? `<path d="M${f2(sz * 0.3)} ${f2(sz * 0.52)} L${f2(sz * 0.45)} ${f2(sz * 0.66)} L${f2(sz * 0.72)} ${f2(sz * 0.36)}" fill="none" stroke="${tn}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" style="stroke-dasharray:${tk};stroke-dashoffset:${tk};animation:scdraw .22s ${m.draw} ${f2(at + 0.26)}s forwards"/>`
      : `<path d="M${P(0.3, 0.52)} L${P(0.45, 0.66)} M${P(0.45, 0.66)} L${P(0.72, 0.36)}" fill="none" stroke="${tn}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" style="stroke-dasharray:${(sz * 1.2).toFixed(0)};stroke-dashoffset:${(sz * 1.2).toFixed(0)};animation:scdraw .22s ${m.draw} ${f2(at + 0.26)}s forwards,${u}x .32s ${EASE_POP} ${f2(xa)}s forwards"/>`;
    return { style: `width:${sz}px;height:${sz}px;`,
      inner: `${xcss}<svg viewBox="0 0 ${sz} ${sz}" width="${sz}" height="${sz}" style="overflow:visible${xa === null ? '' : `;animation:${u}s .3s ease-out ${f2(xa + 0.1)}s both`}">`
        + `<circle cx="${sz / 2}" cy="${sz / 2}" r="${r}" fill="${tn}" fill-opacity=".14" stroke="${tn}" stroke-width="7" style="stroke-dasharray:${c};stroke-dashoffset:${c};transform:rotate(-90deg);transform-origin:center;animation:scdraw .28s ${m.draw} ${f2(at)}s forwards${xa === null ? '' : `,${u}c .24s ${EASE_IN} ${f2(xa)}s forwards`}"/>`
        + `${tick}</svg>`
        + `<i class="bst" style="border-color:${tn};animation:scburst .4s ${EASE_IN} ${f2(at + 0.3)}s both"></i>${sparks}` };
  },
  cursor: (e, { esc, at, tn, m }) => {  // moves from -> to, arriving at click_at; presses; a ripple where it clicked
    const [x1, y1] = e.from, [x2, y2] = e.to, ca = num(e.click_at, at + 0.75), mv = Math.min(0.7, Math.max(0.2, ca - at - 0.05));
    const gone = e.gone !== undefined ? `,${m.fadeOut} ${f2(e.gone)}s forwards` : '';
    return { html: `<div class="p cursor"${idAttr(e, esc)} data-bb="${Math.min(x1, x2)} ${Math.min(y1, y2)} ${Math.abs(x2 - x1) + 60} ${Math.abs(y2 - y1) + 60}" style="left:0;top:0">`
      + `<i class="rip" style="left:${x2}px;top:${y2}px;border-color:${tn};animation:scrip .5s ${EASE_IN} ${f2(ca)}s both"></i>`
      + `<div class="cur" style="--fx:${x1}px;--fy:${y1}px;--tx:${x2}px;--ty:${y2}px;animation:scfade .2s ${f2(at)}s both,sccur ${f2(mv)}s ${EASE_MOVE} ${f2(ca - mv)}s both${gone}">`
      + `<svg viewBox="0 0 32 32" style="animation:scpress .18s ease-out ${f2(ca)}s"><path d="M5 3 L5 26 L11 20 L15 29 L19 27 L15 18 L23 18 Z" fill="#fff" stroke="#0c0d0f" stroke-width="2" stroke-linejoin="round"/></svg></div></div>` };
  },
  ring: (e, { esc, at, tn, m }) => {  // a hand-drawn circle around a box: one turn and a bit, the radius wobbling a few per cent
    // a flat box (a row: wider than 3x its height) gets a rough box instead, "shape": "underline" a rough underline (item 3)
    const shape = e.shape ?? autoShape(e.w, e.h);
    if (shape !== 'circle') {
      const { paths } = annotation(shape, e.x, e.y, e.w, e.h, seedOf(JSON.stringify([e.x, e.y, e.w, e.h, e._on ?? '', e.id ?? ''])), e.pad);
      const d = num(e.d, 0.6), gone = e.gone !== undefined ? `;animation:${m.fadeOut} ${f2(e.gone)}s forwards` : '', p = shape === 'box' ? num(e.pad, 14) : 0;
      const bb = shape === 'box' ? `${e.x - p} ${e.y - p} ${e.w + 2 * p} ${e.h + 2 * p}` : `${e.x} ${e.y + e.h} ${e.w} ${num(e.pad, 10) + 8}`;
      // two pen passes, each revealed along its own length (pathLength 1), the second starting before the first ends
      const strokes = paths.map((pd, i) => { const t0 = f2(at + i * d * 0.55); return `<path d="${pd}" pathLength="1" stroke="${tn}" style="stroke-width:${i ? 4 : 6};stroke-dasharray:1 2;stroke-dashoffset:1;opacity:0;`
        + `animation:scdraw ${f2(d * (i ? 0.8 : 1))}s ${m.draw} ${t0}s forwards,scon .01s linear ${t0}s forwards"/>`; }).join('');
      return { html: `<svg class="ln"${idAttr(e, esc)} data-bb="${bb}" viewBox="0 0 ${W} ${H}" style="overflow:visible${gone}">${strokes}</svg>` };
    }
    const pad = num(e.pad, 24), cx = e.x + e.w / 2, cy = e.y + e.h / 2, rx = e.w / 2 + pad, ry = e.h / 2 + pad;
    const pts = Array.from({ length: 57 }, (_, i) => {
      const a = -2.2 + (i / 50) * 2 * Math.PI, w = 1 + 0.03 * Math.sin(i * 1.7);
      return `${(cx + Math.cos(a) * rx * w).toFixed(1)} ${(cy + Math.sin(a) * ry * w * (1 + (i / 56) * 0.05)).toFixed(1)}`;
    });
    // pathLength 1: the dash is exactly the path (a length estimate was short on a flat ellipse, so the circle's end showed
    // before it was drawn, Kamil 2026-11-15 note 49 "jakby ktoś markerem zaznaczył, gdzie kółko będzie"); hidden until "at"
    // so no round cap dot shows either
    const gone = e.gone !== undefined ? `;animation:${m.fadeOut} ${f2(e.gone)}s forwards` : '';
    return { html: `<svg class="ln"${idAttr(e, esc)} data-bb="${e.x - pad} ${e.y - pad} ${e.w + 2 * pad} ${e.h + 2 * pad}" viewBox="0 0 ${W} ${H}" style="overflow:visible${gone}"><path d="M${pts.join(' L')}" pathLength="1" stroke="${tn}" style="stroke-width:7;stroke-dasharray:1 2;stroke-dashoffset:1;opacity:0;animation:scdraw ${f2(num(e.d, 0.6))}s ${m.draw} ${f2(at)}s forwards,scon .01s linear ${f2(at)}s forwards"/></svg>` };
  },
  say: (e, { esc, tn, m }) => ({  // a kinetic line: each word blurs in when it is said; *em* serif accent, [pill], ~strike~, !red!
    style: `font-size:${num(e.size, 84)}px;${e.w ? '' : 'white-space:nowrap;'}`,
    inner: e.words.map(([w, t]) => {
      const mk = /^([*[~!])(.+)([*\]~!])$/.exec(w), cls = mk ? { '*': 'em', '[': 'pill', '~': 'strk', '!': 'bad' }[mk[1]] : '', txt = mk ? mk[2] : w;
      const extra = cls === 'pill' ? `<i class="hlp" style="background:${tn};animation:scgrow .4s ${EASE_IN} ${f2(t + 0.15)}s both"></i>`
        : cls === 'strk' ? `<i class="sk2" style="animation:scgrow .25s ${m.strike} ${f2(t + 0.35)}s both"></i>` : '';
      // a word said before the card (a piece kept by "extends", t < 0) stays in the past, not clamped to 0 where it would come in again
      return `<span class="w ${cls}" style="animation:scword .3s ${EASE_IN} ${f2(t >= 0 ? Math.max(0, t - 0.03) : t - 0.03)}s both">${extra}<span>${esc(txt)}</span></span>`;
    }).join(' '),
  }),
  toggle: (e, { esc, at, tn, m }) => {  // a switch flips on at on_at: knob slides with a little overshoot, the track takes the colour
    // back_at (Kamil 2026-11-05 "ODMOWA" -> a switch that snaps back and glows red): the knob returns, the track stays red
    const on = num(e.on_at, at + 0.8), back = e.back_at !== undefined ? num(e.back_at, on + 1) : null;
    const bg = `sctgbg .2s ${m.draw} ${f2(on)}s both${back !== null ? `,sctgbad .6s ${EASE_IN} ${f2(back)}s forwards` : ''}`;
    const kn = `sctgk .25s ${EASE_POP} ${f2(on)}s both${back !== null ? `,sctgkback .3s ${EASE_POP} ${f2(back)}s forwards` : ''}`;
    // its keyframes only with back_at: a card without it is drawn byte for byte as before (motion.test golden)
    const css = back !== null ? '<style>@keyframes sctgkback{from{transform:translateX(60px)}to{transform:none}}'
      + '@keyframes sctgbad{0%{background:var(--on)}35%{background:#ff5f57;box-shadow:0 0 48px #ff5f57}100%{background:#c8423c;box-shadow:0 0 26px rgba(255,95,87,.7)}}</style>' : '';
    return { inner: `${css}<span class="tg"><i class="tgb" style="--on:${tn};animation:${bg}"></i><i class="tgk" style="animation:${kn}"></i></span>${e.text ? `<span class="tgl">${esc(kt(e.text))}</span>` : ''}` };
  },
  steps: (e, { esc, tn }) => {  // a progress pill "label N / total": the number changes and the bar grows at each step
    const st = e.steps;
    const nums = st.map(([t, n], i) => `<b class="sn" style="animation:scfade .15s ${f2(t)}s both${i + 1 < st.length ? `,scfadeout .12s ${f2(st[i + 1][0])}s forwards` : ''}">${n}</b>`).join('');
    const fills = st.map(([t, n], i) => `<i class="sf" style="background:${tn};--w0:${(((st[i - 1]?.[1]) ?? 0) / e.total * 100).toFixed(1)}%;--w1:${(n / e.total * 100).toFixed(1)}%;animation:scfill .35s ${EASE_IN} ${f2(t)}s both"></i>`).join('');
    return { inner: `<span class="stl">${esc(e.label ?? '')}</span><span class="sbox">${nums}</span><span class="stot">/ ${e.total}</span><span class="str">${fills}</span>` };
  },
  // a table with real rows (arjay: "products: 41 Red kettle 3 / 42 Blue mug 5"): rows come in one by one, a row lights up
  // ("state": bad = red, ok = green, hl = lime, off = back to plain) and a cell changes its value ("set_cell") on the word
  table: (e, { esc, icon, at, m }) => {
    const nc = e.cols.length, step = num(e.step, m.rowStep);
    const fr = e.cols.map((c, j) => Math.max(c.length, ...e.rows.map(r => r[j].length)) + 2);
    const tpl = `grid-template-columns:${fr.map(f => `${f}fr`).join(' ')}`;
    const st = {}, sc = {};
    for (const [t, r, v] of e.state ?? []) (st[r] ??= []).push([t, v]);
    for (const [t, r, c, v] of e.set_cell ?? []) (sc[`${r}.${c}`] ??= []).push([t, v]);
    const head = e.title ? `<div class="tbt">${icon(e.icon ?? 'database')}<span>${esc(e.title)}</span></div>` : '';
    const rows = e.rows.map((r, i) => {
      const lit = (st[i] ?? []).sort((a, b) => a[0] - b[0]).map(([t, v], j, a) => (v === 'off' ? '' : `<i class="tst ${v}" style="animation:scfade .25s ${EASE_IN} ${f2(t)}s both${a[j + 1] ? `,scfadeout .2s ${f2(a[j + 1][0])}s forwards` : ''}"></i>`)).join('');
      const cells = r.map((c, j) => `<span class="tc">${swap([[null, esc(c)], ...(sc[`${i}.${j}`] ?? []).sort((a, b) => a[0] - b[0]).map(([t, v]) => [t, esc(v)])], m)}</span>`).join('');
      return `<div class="trw td" style="${tpl};animation:scfade .3s ${EASE_IN} ${f2(at + 0.2 + i * step)}s both">${lit}${cells}</div>`;
    }).join('');
    return { inner: `${head}<div class="tbx"><div class="trw th" style="${tpl}">${e.cols.map(c => `<span class="tc">${esc(c)}</span>`).join('')}</div><div class="bd">${rows}</div></div>` };
  },
  // code typed line by line (monospace: a line reveals 1ch per character), coloured; "mark": [[s, line, "phrase"]] = a lime
  // marker grows under that phrase when it is said (arjay: "AND version = 5" marked on "only if the version is still 5")
  code: (e, { esc, at, m }) => {
    const lang = e.lang ?? 'sql', cps = num(e.cps, 40), typed = e.type !== false;
    let t = num(e.type_at, at + 0.3);
    const starts = e.lines.map(l => { const s0 = t; t += (typed ? Math.max(l.length / cps, 0.05) : 0) + num(e.step, typed ? 0.1 : m.rowStep); return s0; });
    const marks = {};
    for (const [mt, li, ph] of e.mark ?? []) (marks[li] ??= []).push([mt, ph]);
    const lines = e.lines.map((l, i) => {
      const band = (marks[i] ?? []).map(([mt, ph]) => `<i class="cdm" style="left:${l.indexOf(ph)}ch;width:${ph.length}ch;animation:scgrow .35s ${EASE_IN} ${f2(mt)}s both"></i>`).join('');
      const anim = typed ? `sctype ${f2(Math.max(l.length / cps, 0.05))}s steps(${Math.max(l.length, 1)}) ${f2(starts[i])}s both` : `${m.outLine} ${f2(starts[i])}s both`;
      return `<div class="cdl">${band}<span class="cdt" style="--n:${l.length};animation:${anim}">${codeHtml(l, lang, esc) || ' '}</span></div>`;
    }).join('');
    return { inner: `${e.title ? `<div class="cdh">${esc(e.title)}</div>` : ''}<div class="bd">${lines}</div>` };
  },
  // a big number or word with a label under it (arjay: a red serif "0 rows", "55% got it wrong"); "set" changes it on the word
  big: (e, { esc, tn, m, pp }) => ({
    inner: `<div class="bgv" style="font-size:${num(e.size, 220)}px;color:${e.tone ? tn : pp ? '#16181d' : '#f1f2f4'}">${e.set ? swap(setVals(e, esc(e.t), esc), m) : esc(e.t)}</div>`
      + `${e.sub ? `<div class="bgs">${esc(kt(e.sub))}</div>` : ''}`,
  }),
  // a callout tag in a person's / thing's colour with a leader line to what it is about (arjay: "Sam: "Blue mug, 350 ml""
  // pointing at the row); the line starts under the tag (inside it), so the tag's width needs no measuring
  tag: (e, { esc, at, tn, m }) => {
    const fs = num(e.size, 52), wEst = e.text.length * fs * 0.55 + 56, sx = e.x + Math.round(wEst * 0.3), sy = e.y + Math.round(fs * 0.62 + 14);
    const gone = e.gone !== undefined ? `,${m.gone} ${f2(e.gone)}s forwards` : '';
    const line = Array.isArray(e.to) ? (() => {
      const [x2, y2] = e.to, len = Math.hypot(x2 - sx, y2 - sy) + 20;
      // inside the tag's own box (one DOM piece per spec piece: scene_check and soloKeys pair them by index), drawn in world px
      return `<svg class="tagl" viewBox="0 0 ${W} ${H}" style="left:${-e.x}px;top:${-e.y}px;overflow:visible${e.gone !== undefined ? `;animation:${m.fadeOut} ${f2(e.gone)}s forwards` : ''}">`
        + `<path d="M${sx} ${sy} L${x2} ${y2}" stroke="${tn}" style="stroke-width:4;stroke-dasharray:${len.toFixed(0)};stroke-dashoffset:${len.toFixed(0)};animation:scdraw .35s ${m.lineDraw} ${f2(at + 0.15)}s forwards"/>`
        + `<circle cx="${x2}" cy="${y2}" r="8" fill="${tn}" style="animation:scfade .15s ${f2(at + 0.5)}s both"/></svg>`;
    })() : '';
    return { html: `<div class="p tag"${idAttr(e, esc)} data-at="${f2(at)}"${typeof e.gone === 'number' ? ` data-gone="${f2(e.gone)}"` : ''} style="left:${e.x}px;top:${e.y}px">${line}`
      + `<div class="pi" style="font-size:${fs}px;background:${tn};animation:${m.anims[e.anim ?? 'pop']} ${f2(at)}s both${gone}">${esc(kt(e.text))}</div></div>` };
  },
  // round 2 (style/REF-shorts-arjay.md › "Gramatyka obrazu", 2026-11-16): the thought drawn, not written. A process = numbered
  // steps joined by arrows, a step lights on the word ("lit"), a dot runs to the next ("packet"), an arrow breaks ("fail");
  // arjay qH2kD: Server -> 1. db transaction -> 2. read outbox -> worker -> 3. mq, "server crashes" on the arrow
  flow: (e, { esc, icon, at, m }) => {
    const col = e.dir === 'col', sAt = e.steps.map((s, i) => num(s.at, at + i * num(e.step, 0.5)));
    const ev = k => { const o = {}; for (const [t, i] of e[k] ?? []) (o[i] ??= []).push(t); return o; };
    const lit = ev('lit'), fail = ev('fail'), pk = ev('packet');
    return { inner: `<div class="bd${col ? ' col' : ''}">${e.steps.map((s, i) => {
      const lits = (lit[i] ?? []).map(t => `<i class="fsl" style="animation:scfade .25s ${EASE_IN} ${f2(t)}s both"></i>`).join('');
      const box = `<div class="fst" style="animation:${m.anims.pop} ${f2(sAt[i])}s both">${lits}<div class="fsi" style="color:${tone(s.tone ?? e.tone)}">${icon(s.icon ?? 'box')}`
        + `${e.num === false ? '' : `<span class="fsn">${i + 1}</span>`}</div><div class="fsx">${esc(kt(s.text))}</div>${s.sub ? `<div class="fss">${esc(kt(s.sub))}</div>` : ''}</div>`;
      if (!i) return box;
      const c0 = Math.max(sAt[i - 1], sAt[i] - 0.25);
      const runs = (pk[i - 1] ?? []).map(t => `<i class="fcp" style="animation:scrun${col ? 'v' : ''} ${f2(num(e.packet_d, 0.6))}s ${EASE_MOVE} ${f2(t)}s both"></i>`).join('');
      const brk = (fail[i] ?? []).map(t => `<i class="fcb" style="animation:scfade .2s ${f2(t)}s both"></i><span class="fcx" style="animation:scpop .3s ${EASE_POP} ${f2(t)}s both">${icon('x')}</span>`).join('');
      return `<div class="fc"><i class="fcl" style="animation:scgrow${col ? 'v' : ''} .3s ${EASE_IN} ${f2(c0)}s both"></i>${runs}${brk}</div>${box}`;
    }).join('')}</div>` };
  },
  // a quantity as things you can count: one tile = one answer / request / user (arjay: "144 answers, 1 tile each", waffle 55 %);
  // "show": [[s, n]] = tiles 1..n are there from s (16 x 8 x 4 x 3 grows to 144), "fill": [[s, n, tone]] = the next n turn a colour
  grid: (e, { esc, at, m }) => {
    const n = e.n, cols = num(e.cols, Math.ceil(Math.sqrt(n))), cs = num(e.cell, 40), shows = e.show ?? [[at + 0.2, n]];
    const appear = [], filled = [];
    let prev = 0;
    for (const [t, c] of shows) { const st = Math.min(0.012, 0.6 / Math.max(c - prev, 1)); for (let i = prev; i < c; i++) appear[i] = t + (i - prev) * st; prev = c; }
    let from = 0;
    for (const [t, c, tn] of e.fill ?? []) { const st = Math.min(0.012, 0.6 / Math.max(c, 1)); for (let i = from; i < from + c && i < n; i++) filled[i] = [t + (i - from) * st, tone(tn ?? 'acc')]; from += c; }
    const cells = Array.from({ length: n }, (_, i) => `<i class="gc" style="animation:scpop .2s ${EASE_POP} ${f2(appear[i] ?? at)}s both">`
      + `${filled[i] ? `<b style="background:${filled[i][1]};animation:scfade .15s ${f2(filled[i][0])}s both"></b>` : ''}</i>`).join('');
    return { inner: `${e.title ? `<div class="gtt">${esc(kt(e.title))}</div>` : ''}<div class="gg" style="grid-template-columns:repeat(${cols},${cs}px);gap:${Math.round(cs * 0.22)}px">${cells}</div>` };
  },
  // a comparison you see by length: one bar per thing ("v" 0..1, the value written at its end); with "b" two dots on one track,
  // "v" -> "b" (arjay: "asked 61 % -> built 10 %"); "lit": [[s, row]] puts the lime band behind a row on the word
  bars: (e, { esc, at, m }) => {
    const ev = {}; for (const [t, i] of e.lit ?? []) (ev[i] ??= []).push(t);
    return { inner: `${e.title ? `<div class="gtt">${esc(kt(e.title))}</div>` : ''}<div class="bd">${e.items.map((it, i) => {
      const a = num(it.at, at + 0.2 + i * num(e.step, 0.35)), tn = tone(it.tone ?? e.tone), pc = x => `${(Math.min(Math.max(x, 0), 1) * 100).toFixed(1)}%`;
      const lits = (ev[i] ?? []).map(t => `<i class="tst hl" style="animation:scfade .25s ${EASE_IN} ${f2(t)}s both"></i>`).join('');
      const track = it.b === undefined
        ? `<i class="brf" style="width:${pc(it.v)};background:${tn};animation:scgrow .6s ${EASE_IN} ${f2(a)}s both"></i>`
        : (() => { const bAt = num(it.b_at, a + 0.6), l = Math.min(it.v, it.b), r = Math.max(it.v, it.b);
          return `<i class="brd" style="left:${pc(l)};width:calc(${pc(r)} - ${pc(l)});background:${tn};transform-origin:${it.b < it.v ? 'right' : 'left'};animation:scgrow .45s ${EASE_IN} ${f2(bAt)}s both"></i>`
            + `<i class="bro" style="left:${pc(it.v)};border-color:${tn};animation:scpop .25s ${EASE_POP} ${f2(a)}s both"></i><i class="bro on" style="left:${pc(it.b)};background:${tn};border-color:${tn};animation:scpop .25s ${EASE_POP} ${f2(bAt + 0.4)}s both"></i>`; })();
      return `<div class="brw" style="animation:scfade .25s ${EASE_IN} ${f2(a - 0.1)}s both">${lits}<span class="brl">${esc(kt(it.label))}</span><span class="brt">${track}</span>`
        + `<span class="brv" style="animation:scfade .3s ${f2((it.b === undefined ? a : num(it.b_at, a + 0.6)) + 0.45)}s both">${esc(kt(it.text ?? ''))}</span></div>`;
    }).join('')}</div>` };
  },
  // time and how long something holds: ticks on top ("open", "editing...", "save"), one lane per way of doing it, a segment grows
  // from its start ("locked the whole time"); "head": [[s, x]] = a now-line that glides to x (0..1) on the word
  timeline: (e, { esc, at, m }) => {
    const pc = x => `${(Math.min(Math.max(x, 0), 1) * 100).toFixed(1)}%`, u = uid(e), hs = [...(e.head ?? [])].sort((a, b) => a[0] - b[0]);
    const ticks = (e.ticks ?? []).map((tk, i, a) => `<span class="tlk" style="left:${pc(a.length > 1 ? i / (a.length - 1) : 0)}">${esc(kt(tk))}</span>`).join('');
    const lanes = e.lanes.map((ln, li) => `<div class="tll" style="animation:scfade .25s ${f2(at + 0.2 + li * 0.3)}s both"><span class="tln">${esc(kt(ln.label))}</span><span class="tlt">`
      + (ln.segs ?? []).map((sg, j) => `<span class="tls" style="left:${pc(sg.from)};width:calc(${pc(sg.to)} - ${pc(sg.from)});background:${tone(sg.tone ?? 'warn')};animation:scgrow .6s ${EASE_IN} ${f2(num(sg.at, at + 0.5 + li * 0.3 + j * 0.3))}s both">${sg.text ? esc(kt(sg.text)) : ''}</span>`).join('')
      + `</span></div>`).join('');
    const head = hs.length ? `<style>${hs.map(([, x], k) => `@keyframes th_${u}_${k}{from{left:calc(var(--pl) + (100% - var(--pl)) * ${k ? hs[k - 1][1] : x})}to{left:calc(var(--pl) + (100% - var(--pl)) * ${x})}}`).join('')}</style>`
      + `<i class="tlh" style="animation:${hs.map(([t], k) => `th_${u}_${k} ${k ? '.6s' : '.01s'} ${EASE_MOVE} ${f2(t)}s ${k ? 'forwards' : 'both'}`).join(',')}"></i>` : '';
    // narrow (a short's panel): each lane's name goes above its track, the track takes the whole width
    const w = num(e.w, 1830), top = w < 1400;
    return { inner: `<div class="tlx${top ? ' top' : ''}" style="width:${w}px"><div class="tlr">${ticks}</div><div class="bd">${lanes}</div>${head}</div>` };
  },
  // a choice made visible (arjay: a question, options A-D, the one people pick lit, then the right one green with the share)
  quiz: (e, { esc, icon, at, m }) => {
    const rv = e.reveal, pick = {}; for (const [t, i] of e.pick ?? []) (pick[i] ??= []).push(t);
    return { inner: `${e.q ? `<div class="qq">${esc(kt(e.q))}</div>` : ''}<div class="bd">${e.opts.map((o, i) => {
      const a = at + 0.3 + i * num(e.step, 0.25), right = rv && rv.right === i;
      const lits = (pick[i] ?? []).map(t => `<i class="tst hl" style="animation:scfade .25s ${EASE_IN} ${f2(t)}s both"></i>`).join('');
      const out = rv ? (right ? `<i class="tst ok" style="animation:scfade .25s ${f2(rv.at)}s both"></i>` : '') : '';
      const dim = rv && !right ? `,scdim .4s ease-out ${f2(rv.at)}s forwards` : '';
      return `<div class="qo" style="animation:scfade .25s ${EASE_IN} ${f2(a)}s both${dim}">${lits}${out}<span class="qk">${right ? `<b style="animation:scpop .3s ${EASE_POP} ${f2(rv.at)}s both">${icon('check')}</b>` : ''}<span>${'ABCDEFGH'[i]}</span></span>`
        + `<span class="qt">${esc(kt(o))}</span>${rv?.pct?.[i] ? `<span class="qp" style="animation:scfade .3s ${f2(rv.at + 0.3)}s both">${esc(rv.pct[i])}</span>` : ''}</div>`;
    }).join('')}</div>` };
  },
  // the thing on screen as the user sees it (arjay: "Product #42", Description "Blue mug", version 5, [Save]): fields whose value
  // changes on the word ("set"), a button pressed on the word, a note that lands under it ("saved", "Stale edit detected")
  form: (e, { esc, icon, at, m }) => {
    const bt = e.button, nt = e.note;
    const fields = (e.fields ?? []).map((f, i) => `<div class="ffd" style="animation:scfade .25s ${EASE_IN} ${f2(at + 0.25 + i * 0.2)}s both"><span class="ffl">${esc(kt(f.label))}</span>`
      + `<span class="ffv">${f.set ? swap(setVals(f, esc(f.value), esc), m) : esc(f.value)}</span></div>`).join('');
    const btn = bt ? `<span class="ffb" style="background:${tone(bt.tone ?? 'lime')};animation:scfade .25s ${f2(at + 0.4)}s both${bt.press_at !== undefined ? `,scpulse .45s ${EASE_POP} ${f2(bt.press_at)}s` : ''}">${esc(kt(bt.text))}</span>` : '';
    const note = nt ? `<div class="ffn" style="color:${tone(nt.tone ?? 'ok')};animation:scpop .3s ${EASE_POP} ${f2(nt.at)}s both">${icon(nt.icon ?? 'circle-check')}<span>${esc(kt(nt.text))}</span></div>` : '';
    return { inner: `<div class="ffh">${e.icon ? icon(e.icon) : ''}<span>${esc(kt(e.title))}</span></div><div class="bd">${fields}${btn}${note}</div>` };
  },
  line: (e, { esc, at, tn, m }) => {
    const [x1, y1] = e.from, [x2, y2] = e.to, len = Math.hypot(x2 - x1, y2 - y1) * 1.3 + 40;
    const c = num(e.curve, 0.35), mx = x1 + (x2 - x1) * c, d = `M${x1} ${y1} C${mx} ${y1},${x2 - (x2 - x1) * c} ${y2},${x2} ${y2}`;
    let dx = (x2 - x1) * c, dy = 0;  // the curve ends level with its last control point; a straight vertical line has no such tangent
    if (Math.abs(dx) < 1) { dx = x2 - x1; dy = y2 - y1; }
    const ang = (Math.atan2(dy, dx) * 180 / Math.PI).toFixed(1), hat = f2(at + num(e.d, 0.7) - 0.05);
    const head = e.arrow === false ? '' : e.head === 'arrow'
      ? `<g transform="translate(${x2} ${y2}) rotate(${ang})"><path d="M4 0 L-30 -17 L-22 0 L-30 17 Z" style="fill:${tn};stroke:none;transform-box:fill-box;transform-origin:right center;animation:scpop .14s ${EASE_POP} ${hat}s both"/></g>`
      : `<circle cx="${x2}" cy="${y2}" r="9" fill="${tn}" style="animation:scfade .2s ${f2(at + num(e.d, 0.7))}s both"/>`;
    const pk = e.packet_at !== undefined ? `<i class="pk" style="background:${tn};color:${tn};offset-path:path('${d}');animation:scpath ${f2(num(e.packet_d, 0.8))}s ${EASE_MOVE} ${f2(e.packet_at)}s both"></i>` : '';
    return { html: `<svg class="ln"${idAttr(e, esc)} data-bb="${Math.min(x1, x2)} ${Math.min(y1, y2)} ${Math.abs(x2 - x1)} ${Math.abs(y2 - y1)}" viewBox="0 0 ${W} ${H}" style="overflow:visible"><path d="${d}" stroke="${tn}" style="stroke-dasharray:${len.toFixed(0)};stroke-dashoffset:${len.toFixed(0)};animation:scdraw ${f2(num(e.d, 0.7))}s ${m.lineDraw} ${f2(at)}s forwards"/>${head}</svg>${pk}` };
  },
};

// the common box of a piece: place and size, then the drawer's inner HTML wrapped in its entrance and later moves
function piece(e, esc, icon, m = MOTION.legacy, pp = false) {
  const at = pieceAt(e);
  const anim = m.anims[e.anim ?? DEF_ANIM[e.k] ?? 'up'];
  const tn = tone(e.tone);
  const drawn = PIECES[e.k]?.(e, { esc, icon, at, tn, m, pp }) ?? { inner: '' };
  if (drawn.html !== undefined) return drawn.html;
  const style = `left:${e.x}px;top:${e.y}px;${e.w ? `width:${e.w}px;` : ''}${e.h ? `height:${e.h}px;` : ''}${drawn.style ?? ''}`;
  let inner = drawn.inner;
  if (e.hl_at !== undefined) inner = `<i class="ghl" style="background:${tn};animation:scgrow .4s ${EASE_IN} ${f2(e.hl_at)}s both"></i><span class="ght">${inner}</span>`;
  if (e.strike_at !== undefined) inner += `<i class="gstrk" style="animation:scgrow .25s ${m.strike} ${f2(e.strike_at)}s both"></i>`;
  const outs = [`${anim} ${f2(at)}s both`];
  for (const t of [].concat(e.pulse_at ?? [])) outs.push(`scpulse .45s ${EASE_POP} ${f2(t)}s`);  // no fill: the entrance's end state stays
  if (e.strike_at !== undefined) outs.push(`scdimh .25s ease-out ${f2(e.strike_at + 0.1)}s forwards`);
  if (e.out_at !== undefined) outs.push(`${m.out} ${f2(e.out_at)}s forwards`);
  if (e.dim !== undefined) outs.push(`scdim .4s ease-out ${f2(e.dim)}s forwards`);
  if (e.gone !== undefined) outs.push(`${m.gone} ${f2(e.gone)}s forwards`);
  // data-at / data-gone: when it comes in and leaves, so the camera (sceneFit) keeps a piece in the picture while it is read
  const when = ` data-at="${f2(pieceAt(e))}"${typeof e.gone === 'number' ? ` data-gone="${f2(e.gone)}"` : ''}`;
  return `<div class="p ${e.k}"${idAttr(e, esc)}${when} style="${style}"><div class="pi" style="animation:${outs.join(',')}">${inner}</div></div>`;
}

// S11 "extends": a scene that goes on from an earlier one ("extends": "<its id>") starts with that scene's pieces still on at its
// end, already in their final state (typed, marked, counted), and adds its own; so a list or a diagram grows over several
// cards without coming in again each time. Every time of a kept piece is moved back by the earlier scene's "dur" plus PAST:
// times derived from "at" (a command typing at + 0.5, chat messages, rows) are not in the spec, so a piece that came in late
// must still land before 0; a seeked frame shows its final state. render.mjs and scene_check.mjs call this on the whole
// specs file; a spec without "extends" comes back as the same object (drawn byte for byte as before).
const PAST = 600;
const TIME_KEYS = ['gone', 'dim', 'click_at', 'on_at', 'back_at', 'out_at', 'out_start', 'strike_at', 'hl_at', 'packet_at', 'cmd_at'];
export function shiftPiece(e, d) {
  const add = v => (typeof v === 'number' ? +(v + d).toFixed(3) : v), s = JSON.parse(JSON.stringify(e));
  s.at = +(pieceAt(e) + d).toFixed(3);
  for (const k of TIME_KEYS) if (k in s) s[k] = add(s[k]);
  if (s.pulse_at !== undefined) s.pulse_at = Array.isArray(s.pulse_at) ? s.pulse_at.map(add) : add(s.pulse_at);
  if (Array.isArray(s.words)) s.words = s.words.map(w => (Array.isArray(w) ? [w[0], add(w[1])] : w));
  for (const k of ['steps', 'read_along']) if (Array.isArray(s[k])) s[k] = s[k].map(x => (Array.isArray(x) ? [add(x[0]), x[1]] : x));
  if (Array.isArray(s.msgs)) s.msgs = s.msgs.map(g => (g && typeof g.at === 'number' ? { ...g, at: add(g.at) } : g));
  // a row object (win / file) gets its times moved; a table row is a list of cells and stays as it is
  if (Array.isArray(s.rows)) s.rows = s.rows.map(r => (r && typeof r === 'object' && !Array.isArray(r) ? { ...r, ...(typeof r.mark_at === 'number' ? { mark_at: add(r.mark_at) } : {}),
    ...(typeof r.hl_at === 'number' ? { hl_at: add(r.hl_at) } : {}) } : r));
  for (const k of ['badge', 'count']) if (s[k] && typeof s[k].at === 'number') s[k] = { ...s[k], at: add(s[k].at) };
  // round 2 pieces: [[s, ...]] lists, times inside steps / items / fields / lanes, reveal, note, button
  if (typeof s.type_at === 'number') s.type_at = add(s.type_at);
  for (const k of ['set', 'state', 'set_cell', 'mark', 'lit', 'fail', 'packet', 'show', 'fill', 'pick', 'head']) if (Array.isArray(s[k])) s[k] = s[k].map(x => (Array.isArray(x) ? [add(x[0]), ...x.slice(1)] : x));
  const atOf = o => (o && typeof o === 'object' ? { ...o, ...(typeof o.at === 'number' ? { at: add(o.at) } : {}), ...(typeof o.b_at === 'number' ? { b_at: add(o.b_at) } : {}),
    ...(Array.isArray(o.set) ? { set: o.set.map(x => (Array.isArray(x) ? [add(x[0]), x[1]] : x)) } : {}),
    ...(Array.isArray(o.segs) ? { segs: o.segs.map(atOf) } : {}) } : o);
  if (s.k !== 'steps') for (const k of ['steps', 'items', 'fields', 'lanes']) if (Array.isArray(s[k]) && s[k].some(x => x && typeof x === 'object' && !Array.isArray(x))) s[k] = s[k].map(atOf);
  for (const k of ['reveal', 'note']) if (s[k] && typeof s[k].at === 'number') s[k] = { ...s[k], at: add(s[k].at) };
  if (s.button && typeof s.button.press_at === 'number') s.button = { ...s.button, press_at: add(s.button.press_at) };
  return s;
}
export function resolveExtends(specs) {
  const byId = new Map(specs.map(s => [s?.id, s])), done = new Map();
  const resolve = (sp, seen) => {
    if (sp?.type !== 'scene' || sp.extends === undefined) return sp;
    if (done.has(sp.id)) return done.get(sp.id);
    if (seen.includes(sp.id)) throw new Error(`"${sp.id}": scene: "extends" goes round in a circle (${[...seen, sp.id].join(' -> ')})`);
    const p = byId.get(sp.extends);
    if (!p || p.type !== 'scene' || !(p.dur > 0)) throw new Error(`"${sp.id}": scene: "extends" names ${JSON.stringify(sp.extends)}, no scene (with a "dur") has that "id"`);
    const pr = resolve(p, [...seen, sp.id]);
    // still on at its end: no "gone", no "out_at" (both take a piece off before the card ends)
    const kept = [...(pr._held ?? []), ...(pr.els ?? [])].filter(e => e && e.gone === undefined && e.out_at === undefined);
    const out = { ...sp, _held: kept.map(e => shiftPiece(e, -(pr.dur + PAST))) };
    done.set(sp.id, out);
    return out;
  };
  return specs.map(s => resolve(s, []));
}

// the pieces in the order they are drawn (DOM order; scene_check measures by this index). Beside the speaker the pieces
// stack in one column in reading order (top to bottom, then left to right), so the camera fits a tall narrow block into
// the tall narrow board and the text stays big (Kamil 2026-11-05: on a phone held sideways a wide drawing shrunk into the
// side field cannot be read; "większe i pionowo narysowane"). Kept pieces of "extends" come first: under the new ones.
export function drawnEls(sp) {
  const all = [...(sp._held ?? []), ...sp.els];
  const col = sp.layout === 'side' && sp.canvas !== 'v' && all.every(e => !TIED.includes(e.k));
  return { els: col ? [...all].sort((a, b) => (a.y ?? 0) - (b.y ?? 0) || (a.x ?? 0) - (b.x ?? 0)) : all, col };
}

export function scene(sp, esc, icon) {
  const bad = checkScene(sp);
  if (sp.extends !== undefined && !Array.isArray(sp._held)) bad.push('"extends": run resolveExtends(specs) on the specs file first');
  if (bad.length) throw new Error(`"${sp.id}": scene: ${bad.join('; ')}`);
  const safeIcon = n => { try { return icon(n); } catch { throw new Error(`"${sp.id}": no icon "${n}" in lucide-static`); } };
  const cam = sp.cam === 'none' ? null : sp.cam ?? [{ t: 0, on: '*' }];
  const side = sp.layout === 'side' && sp.canvas !== 'v', { els, col } = drawnEls(sp), pp = sp.look === 'paper';
  const world = els.map(e => piece(e, esc, safeIcon, MOTION[sp.motion ?? 'legacy'], pp)).join('');
  // extra CSS only for a scene that uses it: every scene without these keys stays byte for byte as before (motion.test golden)
  const extra = (els.some(e => EXPLAIN.includes(e.k) || e.set !== undefined) ? EXPLAIN_CSS : '') + (pp ? PAPER_CSS : '');
  const grow = sp.cam === 'grow' ? ` data-growz="${num(sp.grow_zmax, GROW_ZMAX)}"` : '';
  const bg = side ? `<div class="board" style="left:${SIDE.x}px;top:${SIDE.y}px;width:${SIDE.w}px;height:${SIDE.h}px"></div>`
    : sp.bg === 'blobs' ? '<div class="blobs"><i class="b1"></i><i class="b2"></i><i class="b3"></i></div>' : '';
  const zoom = sp.canvas_zoom ? ` data-zoom="${esc(JSON.stringify(sp.canvas_zoom.map(z => ({ t: z.t, on: z.on, k: num(z.k, CANVAS_ZOOM.k), d: num(z.d, CANVAS_ZOOM.d) }))))
    .replace(/"/g, '&quot;')}"` : '';
  return `${SCENE_CSS}${extra}<div class="scene${side ? ' side' : ''}${col ? ' col' : ''}${pp ? ' paper' : ''}"${side ? ` style="clip-path:inset(${SIDE.y}px ${W - SIDE.x - SIDE.w}px ${H - SIDE.y - SIDE.h}px ${SIDE.x}px round 48px)"` : ''}>${bg}<div class="world"${cam ? ` data-cam="${esc(JSON.stringify(cam)).replace(/"/g, '&quot;')}" data-dur="${sp.dur}"${sp.canvas === 'v' ? ' data-solo="1"' : ''}${zoom}${grow}` : ''}>${world}</div></div>`;
}

// a side column follows the newest pieces: each stop frames what came in since the stop before (cumulative "on" lists
// from the plan), so the column scrolls inside its board; framed whole, a tall stack fell to 0.5-0.7 scale and its text
// under 40 px on a phone (2026-11-08). Self-contained: render.mjs ships its source into the page like zoomStops.
export function colFollow(cam) {
  return cam.map((s, i) => {
    const p = cam[i - 1];
    if (!i || !Array.isArray(s.on) || !Array.isArray(p && p.on)) return s;
    const fresh = s.on.filter(x => !p.on.includes(x));
    return fresh.length ? { ...s, on: fresh } : s;
  });
}

// the framing of the camera stops from the measured pieces [{id, x, y, w, h, ln?, at?, gone?}] (world px), safe = the free area,
// view = the visible part in scene px or null; -> {frame(stop) -> {t, move, z, x, y, keep}, centre(on, t)}. Pure: sceneFit runs
// it in the page from its source, tests run it in Node.
export function frameStops(pieces, safe, view) {
  // the pieces being read at t (in for less than READ_HOLD s, not gone): a stop frames them too, so the camera does not cut
  // or hide a line the viewer is still reading when it moves on to the next piece (64 such pieces, 2026-11-08)
  // (+ the 0.9 s move: the camera leaves the old framing when its move to t starts)
  const READ_HOLD = 2.0, MOVE = 0.9;
  const reading = t => pieces.filter(p => !p.ln && p.at !== undefined && p.at <= t + 0.6 && p.at >= t - MOVE - READ_HOLD && !(p.gone <= t - MOVE));
  const fit = (got, s) => {
    const x0 = Math.min(...got.map(p => p.x)), y0 = Math.min(...got.map(p => p.y));
    const x1 = Math.max(...got.map(p => p.x + p.w)), y1 = Math.max(...got.map(p => p.y + p.h));
    const pad = s.pad ?? 50, bw = x1 - x0 + 2 * pad, bh = y1 - y0 + 2 * pad;
    const z = Math.min(safe.w / bw, safe.h / bh, s.zmax ?? 1.8);
    return { t: s.t, move: s.move, z, x: (x0 + x1) / 2 - (safe.x + safe.w / 2) / z, y: (y0 + y1) / 2 - (safe.y + safe.h / 2) / z };
  };
  // a piece the framing cuts at the edge of the view is taken into the framing (a word half off the frame reads as a mistake,
  // stills 2026-11-08), while the camera stays at >= 0.85 of its zoom (text size on a phone, scene_check readProblems); what is
  // still cut then hides for that stop (soloKeys)
  const frame = s => {
    const want = s.on === undefined || s.on === '*' ? null : [].concat(s.on);
    // s.idx (cam "grow"): exactly these pieces, the ones on screen; nothing still to come is framed or read-held
    let got = s.idx ? pieces.filter((p, i) => s.idx.includes(i)) : pieces.filter(p => !want || want.includes(p.id) || reading(s.t ?? 0).includes(p)), st = fit(got, s);
    const z0 = st.z;
    for (let k = 0; view && !s.idx && k < 6; k++) {  // grow stops (idx): a piece still to come is not on screen to be cut
      const v0 = st.x + view.x / st.z, v1 = st.x + (view.x + view.w) / st.z, w0 = st.y + view.y / st.z, w1 = st.y + (view.y + view.h) / st.z;
      const cut = pieces.filter(p => !p.ln && !got.includes(p) && p.x < v1 && p.x + p.w > v0 && p.y < w1 && p.y + p.h > w0 &&
        !(p.x >= v0 - 2 && p.x + p.w <= v1 + 2 && p.y >= w0 - 2 && p.y + p.h <= w1 + 2));
      if (!cut.length) break;
      const wider = fit([...got, ...cut], s);
      if (wider.z < z0 * 0.85) break;
      got = [...got, ...cut]; st = wider;
    }
    return { ...st, keep: got.map(p => pieces.indexOf(p)) };
  };
  // canvas_zoom's target: the centre and box of the pieces it names plus those still being read at t
  const centre = (on, t) => {
    const want = on === '*' ? null : [].concat(on), got = pieces.filter(p => !want || want.includes(p.id) || reading(t).includes(p));
    const box = [Math.min(...got.map(p => p.x)), Math.min(...got.map(p => p.y)), Math.max(...got.map(p => p.x + p.w)), Math.max(...got.map(p => p.y + p.h))];
    return { cx: (box[0] + box[2]) / 2, cy: (box[1] + box[3]) / 2, box, keep: got.map(p => pieces.indexOf(p)) };
  };
  // "cam": "grow": a stop at each entrance (entrances closer than GAP s share one, framing all of them), framing the pieces on
  // screen then; the camera's move ends as the first piece of the group lands, so the room for it is made before it comes in
  const grow = (dur, zmax) => {
    const GAP = 0.6, MV = 0.55, on = t => pieces.map((p, i) => [p, i])
      .filter(([p]) => !p.ln && (p.at ?? 0) <= t + 1e-6 && !(p.gone !== undefined && p.gone <= t)).map(([, i]) => i);
    const ev = [...new Set(pieces.filter(p => !p.ln).flatMap(p => [p.at ?? 0, ...(p.gone !== undefined ? [p.gone] : [])]))]
      .filter(t => t >= 0 && t < dur).sort((a, b) => a - b);
    const groups = [];
    for (const t of ev) { const g = groups.at(-1); if (g && t - g[1] < GAP) g[1] = t; else groups.push([t, t]); }
    const stops = [];
    for (const [a, b] of groups) {
      const idx = on(b), last = stops.at(-1);
      if (!idx.length || (last && last.idx.join() === idx.join())) continue;
      const t = last ? Math.min(dur, a + 0.05) : 0;
      stops.push({ t, move: last ? Math.max(0.2, Math.min(MV, t - last.t)) : undefined, idx, zmax });
    }
    return stops.length ? stops.map(frame) : [frame({ t: 0, zmax })];
  };
  return { frame, centre, grow };
}

// in the page, before the first frame (render.mjs): measures the pieces as laid out (their final place, not mid-animation),
// turns every "on" stop into x, y, z that put those pieces in the middle of the free area, and starts the camera animation.
// Self-contained: its source is evaluated in the page with the sources of camKeyframes, soloKeys, zoomStops, colFollow and
// frameStops as arguments (render.mjs, scene_check.mjs).
export function sceneFit(safe, kfSrc, soloSrc, zoomSrc, followSrc, fitSrc) {
  if (!fitSrc) throw new Error('sceneFit needs the source of frameStops');  // before any page access: a missing source never frames silently
  const camKeyframes = new Function(`return ${kfSrc}`)();
  const world = document.querySelector('.scene .world');
  if (!world || !world.dataset.cam) return null;
  const cam0 = JSON.parse(world.dataset.cam), dur = +world.dataset.dur, growing = cam0 === 'grow', cam = growing ? [] : cam0;
  const pieces = [...world.querySelectorAll(':scope > .p, :scope > svg.ln')].map(el => {
    if (el.dataset.bb) { const [x, y, w, h] = el.dataset.bb.split(' ').map(Number); return { id: el.dataset.id, x, y, w, h, ln: true }; }
    // with what sticks out of it (a node's label is wider than its icon: "Księgarnia" was cut, 2026-11-08); offset geometry,
    // so an entrance animation's transform does not move the box
    let x0 = 0, y0 = 0, x1 = el.offsetWidth, y1 = el.offsetHeight;
    for (const d of el.querySelectorAll ? el.querySelectorAll('*') : []) {
      if (!(d.offsetWidth > 0 && d.offsetHeight > 0)) continue;
      let x = 0, y = 0, n = d;
      for (; n && n !== el; n = n.offsetParent) { x += n.offsetLeft; y += n.offsetTop; }
      if (n !== el) continue;
      x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + d.offsetWidth); y1 = Math.max(y1, y + d.offsetHeight);
    }
    const at = el.dataset.at === undefined ? undefined : +el.dataset.at, gone = el.dataset.gone === undefined ? undefined : +el.dataset.gone;
    return { id: el.dataset.id, x: el.offsetLeft + x0, y: el.offsetTop + y0, w: x1 - x0, h: y1 - y0, at, gone };
  });
  // what the viewer sees, in the scene's own px: the frame, or a side scene's board (its clip-path inset)
  const sc = world.parentElement, view = (() => {  // null outside a page (a test's stand-in world): no closure, no 16:9 solo
    if (!sc || typeof sc.getBoundingClientRect !== 'function' || typeof getComputedStyle !== 'function') return null;
    const sr = sc.getBoundingClientRect(), ins = (getComputedStyle(sc).clipPath.match(/inset\(([^)]*)\)/) || [])[1];
    const [it, ir, ib, il] = ins ? ins.split('round')[0].trim().split(/\s+/).map(parseFloat) : [0, 0, 0, 0];
    return { x: il, y: it, w: sr.width - il - ir, h: sr.height - it - ib };
  })();
  const col = world.parentElement && world.parentElement.classList.contains('col');
  if (col && !followSrc) throw new Error('side column: sceneFit needs the source of colFollow');
  const follow = col ? new Function(`return ${followSrc}`)()(cam) : cam;
  const fr = new Function(`return ${fitSrc}`)()(pieces, safe, view);
  if (growing && !fr.grow) throw new Error('"cam": "grow": sceneFit needs the source of frameStops with grow');
  let stops = growing ? fr.grow(dur, +world.dataset.growz || 1.5)
    : follow.map(s => (s.on !== undefined || (s.x === undefined && s.y === undefined) ? fr.frame(s) : s));
  if (world.dataset.zoom) {  // L17 canvas_zoom: one more stop per zoom, onto the centre of the pieces it names (zoomStops)
    if (!zoomSrc) throw new Error('canvas_zoom: sceneFit needs the source of zoomStops');
    const zoomStops = new Function(`return ${zoomSrc}`)();
    stops = zoomStops(stops, JSON.parse(world.dataset.zoom).map(z => ({ ...z, ...fr.centre(z.on, z.t + (z.d ?? 0)) })), view);
  }
  const st = document.createElement('style');
  st.textContent = `@keyframes cam_fit{${camKeyframes(stops, dur)}}`;
  document.head.appendChild(st);
  world.style.animation = `cam_fit ${dur}s linear both`;
  if (soloSrc && (world.dataset.solo || view)) {  // a piece cut by the edge hides for that stop (soloKeys): 9:16 against its free area, else the view
    const soloKeys = new Function(`return ${soloSrc}`)();
    const els = [...world.querySelectorAll(':scope > .p, :scope > svg.ln')];
    const v = !!world.dataset.solo;
    soloKeys(pieces, stops, dur, v ? safe : view, v ? 24 : 4, !v).forEach((keys, i) => {
      const el = els[i];
      if (!keys || !el.classList.contains('p') || el.style.animation) return;  // lines stay: a cut line reads as going on
      st.textContent += `@keyframes solo_${i}{${keys.map(([t, o]) => `${((t / dur) * 100).toFixed(3)}%{opacity:${o}}`).join('')}}`;
      el.style.animation = `solo_${i} ${dur}s linear both`;
    });
  }
  return stops;
}

// the look: near-black canvas with a faint dot grid, flat dark cards with thin borders, skeleton lines for text that does
// not need reading, colour only where the eye should go (accent, ok, bad); Montserrat for UI, a monospace for the terminal
const SCENE_CSS = `<style>
.scene{position:absolute;inset:0;overflow:hidden;background:#0c0d0f;background-image:radial-gradient(rgba(255,255,255,.055) 2px,transparent 2.5px);background-size:56px 56px;animation:scfade .35s both}
.scene.side{background:none}
.scene.col .world{display:flex;flex-direction:column;align-items:flex-start;gap:48px;padding:60px}
.scene.col .p{position:relative;left:auto!important;top:auto!important;flex:none}
.scene.col .p.file,.scene.col .p.term,.scene.col .p.win,.scene.col .p.bar,.scene.col .p.chat{max-width:640px}
.scene.col .p.text,.scene.col .p.say{max-width:640px;white-space:normal!important}
.scene.col .chip .pi{max-width:640px;white-space:normal;border-radius:44px}
.scene.side .board{position:absolute;border-radius:48px;background:rgba(12,13,15,.72);box-shadow:0 30px 90px rgba(0,0,0,.45);border:2px solid rgba(255,255,255,.08);animation:scboard .5s cubic-bezier(.2,1.3,.4,1) both}
@keyframes scboard{from{opacity:0;transform:translateX(80px) scale(.92)}to{opacity:1;transform:none}}
.scene .world{position:absolute;left:0;top:0;width:${W}px;height:${H}px;transform-origin:0 0}
.scene .p{position:absolute}
.scene .pi{position:relative;width:100%;height:100%}
.scene .blobs i{position:absolute;width:1200px;height:1200px;border-radius:50%;filter:blur(110px);opacity:.30}
.scene .blobs .b1{left:-300px;top:-420px;background:var(--acc);animation:scb1 17s ease-in-out infinite alternate}
.scene .blobs .b2{left:1500px;top:200px;background:#6ea8fe;animation:scb2 21s ease-in-out infinite alternate}
.scene .blobs .b3{left:500px;top:820px;background:#a78bfa;opacity:.22;animation:scb3 15s ease-in-out infinite alternate}
.scene .ghl{position:absolute;left:-14px;right:-14px;top:10%;bottom:4%;border-radius:14px;opacity:.32;transform-origin:left;transform:rotate(-1deg)}
.scene .ght{position:relative}
.scene .gstrk{position:absolute;left:-8px;right:-8px;top:50%;height:9px;margin-top:-4px;border-radius:5px;background:#ff5f57;transform-origin:left}
.scene .check .pi{overflow:visible}
.scene .check .bst{position:absolute;inset:0;border:5px solid;border-radius:50%}
.scene .check .pt{position:absolute;left:50%;top:50%;width:14px;height:14px;margin:-7px;border-radius:50%}
.scene .cursor{width:0;height:0}
.scene .cur{position:absolute;left:0;top:0;width:76px;height:76px}
.scene .cur svg{width:76px;height:76px;transform-origin:16% 10%;filter:drop-shadow(0 8px 14px rgba(0,0,0,.5))}
.scene .rip{position:absolute;width:90px;height:90px;margin:-45px 0 0 -45px;border:6px solid;border-radius:50%}
.scene .say .pi{font-weight:800;line-height:1.15;letter-spacing:-1px;color:#f1f2f4}
.scene .say .w{position:relative;display:inline-block}
.scene .say .w>span{position:relative}
.scene .say .w.em>span{font-family:Georgia,'DejaVu Serif',serif;font-style:italic;font-weight:700;color:var(--acc)}
.scene .say .w.bad>span{color:#ff5f57}
.scene .say .w.strk>span{opacity:.6}
.scene .say .hlp{position:absolute;left:-10px;right:-10px;top:12%;bottom:4%;border-radius:12px;opacity:.38;transform-origin:left;transform:rotate(-1deg)}
.scene .say .sk2{position:absolute;left:-4px;right:-4px;top:52%;height:9px;border-radius:5px;background:#ff5f57;transform-origin:left}
.scene .toggle .pi{display:inline-flex;align-items:center;gap:26px;width:auto;height:auto;color:#eef0f2;font-weight:700;font-size:46px;white-space:nowrap}
.scene .tg{position:relative;width:132px;height:72px;flex:none}
.scene .tgb{position:absolute;inset:0;border-radius:36px;background:#3a3e45}
.scene .tgk{position:absolute;left:8px;top:8px;width:56px;height:56px;border-radius:50%;background:#fff;box-shadow:0 4px 10px rgba(0,0,0,.4)}
.scene .steps .pi{display:inline-flex;align-items:center;gap:16px;width:auto;height:auto;padding:18px 36px 24px;background:#16181c;border:2px solid #2a2d33;border-radius:999px;color:#eef0f2;font-weight:700;font-size:44px;white-space:nowrap;overflow:hidden}
.scene .sbox{position:relative;display:inline-block;width:1.6em;height:1.2em}
.scene .sn{position:absolute;right:0;top:0;color:var(--acc)}
.scene .stot{color:#8b9096}
.scene .str{position:absolute;left:0;right:0;bottom:0;height:8px;background:#23262b}
.scene .sf{position:absolute;left:0;top:0;bottom:0}
.scene .pk{position:absolute;left:0;top:0;width:26px;height:26px;border-radius:50%;box-shadow:0 0 26px currentColor}
.scene .sv.cnt{counter-reset:cnt var(--cnt)}
.scene .sv.cnt::after{content:attr(data-pre) counter(cnt) attr(data-suf)}
.scene .win .pi,.scene .file .pi,.scene .term .pi{background:#16181c;border:2px solid #2a2d33;border-radius:22px;box-shadow:0 30px 80px rgba(0,0,0,.45);overflow:hidden}
.scene .tb{display:flex;align-items:center;gap:14px;height:80px;padding:0 28px;border-bottom:2px solid #24272c;color:#c9ccd1;font-weight:600;font-size:42px}
.scene .tb i{width:18px;height:18px;border-radius:50%;background:#ff5f57}.scene .tb i:nth-child(2){background:#febc2e}.scene .tb i:nth-child(3){background:#28c840;margin-right:14px}
.scene .tb svg{width:34px;height:34px;stroke:#9aa0a8;stroke-width:2;vertical-align:-6px;margin-right:10px}
.scene .tb .ti{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.scene .tb.fb svg{margin-right:0}
.scene .bdg{flex:none;font-size:26px;font-weight:700;padding:6px 18px;border:2px solid;border-radius:999px}
.scene .bd{padding:22px 30px 28px}
.scene .row{position:relative;display:flex;align-items:center;gap:20px;min-height:78px;padding:0 14px;margin:4px -14px;border-radius:12px}
.scene .rt{position:relative;flex:1;color:#e7e9ec;font-weight:500;font-size:46px;line-height:1.2}
.scene .sk{position:relative;height:16px;border-radius:8px;background:#2b2e34}
.scene .row .sk{flex:none}
.scene .rhl{position:absolute;inset:0;border-radius:12px;opacity:.18;transform-origin:left}
.scene .mk{position:relative;margin-left:auto;flex:none;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.scene .mk svg{width:30px;height:30px;stroke:#0c0d0f;stroke-width:3.4}
.scene .mk.ok{background:#3ecf8e}.scene .mk.bad{background:#ff5f57}.scene .mk.warn{background:#f5b84a}
.scene .term .bd{font-family:'DejaVu Sans Mono',monospace;font-size:42px;line-height:1.5;color:#d6d9de}
.scene .term .cl{white-space:pre;margin-bottom:10px}
.scene .term .ps{color:#3ecf8e}
.scene .term .cmd{display:inline-block;vertical-align:bottom;overflow:hidden;white-space:pre;color:#fff}
.scene .term .ol{position:relative;white-space:pre-wrap;padding:2px 12px;margin:0 -12px;border-radius:10px}
.scene .term .ol span{position:relative}
.scene .term .ol.hot span{color:#fff;font-weight:700}
.scene .chip .pi{display:inline-flex;align-items:center;gap:22px;width:auto;height:auto;padding:16px 34px 16px 16px;background:#16181c;border:2px solid #2a2d33;border-radius:999px;color:#eef0f2;font-weight:700;font-size:46px;white-space:nowrap}
.scene .chip .ci{width:70px;height:70px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.scene .chip .ci svg{width:40px;height:40px;stroke:#0c0d0f;stroke-width:2.6}
.scene .node .pi,.scene .you .pi{display:flex;flex-direction:column;align-items:center;width:auto;height:auto}
.scene .nt{display:flex;align-items:center;justify-content:center;border:3px solid;border-radius:30%;background:#16181c}
.scene .nt svg{width:52%;height:52%;stroke:currentColor;stroke-width:2}
.scene .nt.you{width:150px;height:150px;border-radius:50%;border-color:#3a3e45;color:#c9ccd1}
.scene .nl{margin-top:20px;color:#f1f2f4;font-weight:800;font-size:44px;white-space:nowrap}
.scene .ns{margin-top:6px;color:#8b9096;font-weight:600;font-size:38px;white-space:nowrap}
.scene .chat .pi{display:flex;flex-direction:column;gap:18px}
.scene .msg{max-width:78%;padding:24px 32px;border-radius:26px;font-weight:600;font-size:42px;line-height:1.25;color:#eef0f2;background:#1d2025;border:2px solid #2a2d33}
.scene .msg.me{align-self:flex-end;background:#232a35;border-color:#2f3a4a;border-bottom-right-radius:8px}
.scene .msg.ai{align-self:flex-start;border-bottom-left-radius:8px}
.scene .stamp .pi{display:inline-block;width:auto;height:auto;padding:18px 44px;border:7px solid;border-radius:18px;font-weight:900;font-size:84px;letter-spacing:6px;background:rgba(12,13,15,.86)}
.scene .stamp{transform:rotate(var(--r))}
.scene .text .pi{font-weight:800;line-height:1.12;letter-spacing:-1px}
.scene .text b{color:var(--acc)}
.scene .bl{color:#c9ccd1;font-weight:700;font-size:40px;margin-bottom:14px}
.scene .tr{height:30px;border-radius:15px;background:#23262b;overflow:hidden}
.scene .fl{height:100%;border-radius:15px;transform-origin:left}
.scene .stat .pi{display:flex;flex-direction:column;width:auto;height:auto}
.scene .sv{font-weight:900;font-size:140px;line-height:1;letter-spacing:-3px}
.scene .sl{color:#c9ccd1;font-weight:600;font-size:46px;margin-top:10px}
.scene svg.ln{position:absolute;left:0;top:0;width:${W}px;height:${H}px;pointer-events:none}
.scene svg.ln path{fill:none;stroke-width:5;stroke-linecap:round}
@keyframes scpop{from{opacity:0;transform:scale(.6)}to{opacity:1;transform:none}}
@keyframes scup{from{opacity:0;transform:translateY(46px)}to{opacity:1;transform:none}}
@keyframes scleft{from{opacity:0;transform:translateX(-120px)}to{opacity:1;transform:none}}
@keyframes scright{from{opacity:0;transform:translateX(120px)}to{opacity:1;transform:none}}
@keyframes scdrop{0%{opacity:0;transform:scale(2.2)}60%{opacity:1;transform:scale(.94)}to{opacity:1;transform:scale(1)}}
@keyframes scfade{from{opacity:0}to{opacity:1}}
@keyframes scdim{to{opacity:.28}}
@keyframes scgone{to{opacity:0;transform:scale(.92)}}
@keyframes scgrow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes sctype{from{width:0}to{width:calc(var(--n) * 1ch)}}
@keyframes scdraw{to{stroke-dashoffset:0}}
@keyframes scon{to{opacity:1}}
@property --cnt{syntax:'<integer>';inherits:false;initial-value:0}
@keyframes scblur{from{opacity:0;filter:blur(12px);transform:translateX(24px)}to{opacity:1;filter:none;transform:none}}
@keyframes scword{from{opacity:0;filter:blur(12px);transform:translateX(24px)}to{opacity:1;filter:none;transform:none}}
@keyframes scblurout{to{opacity:0;filter:blur(8px);transform:translateY(-8px)}}
@keyframes scfadeout{to{opacity:0}}
@keyframes scdimh{to{opacity:.55}}
@keyframes scpulse{0%{transform:none}40%{transform:scale(1.09)}100%{transform:none}}
@keyframes scpart{from{opacity:1;transform:none}to{opacity:0;transform:translate(var(--dx),var(--dy)) scale(.4)}}
@keyframes scburst{from{opacity:.6;transform:scale(.6)}to{opacity:0;transform:scale(1.6)}}
@keyframes sccur{from{transform:translate(var(--fx),var(--fy))}to{transform:translate(var(--tx),var(--ty))}}
@keyframes scpress{0%{transform:none}50%{transform:scale(.86)}100%{transform:none}}
@keyframes scrip{from{opacity:.6;transform:scale(0)}to{opacity:0;transform:scale(2.4)}}
@keyframes sctgbg{to{background:var(--on)}}
@keyframes sctgk{to{transform:translateX(60px)}}
@keyframes scfill{from{width:var(--w0)}to{width:var(--w1)}}
@keyframes scpath{0%{offset-distance:0%;opacity:0}8%{opacity:1}88%{opacity:1}100%{offset-distance:100%;opacity:0}}
@keyframes scb1{to{transform:translate(160px,120px)}}
@keyframes scb2{to{transform:translate(-180px,-100px)}}
@keyframes scb3{to{transform:translate(120px,-140px)}}
</style>`;

// explainer pieces (table, code, big, tag) and "set" values: only in scenes that use them (scene())
const EXPLAIN_CSS = `<style>
.scene .sw{position:relative;display:inline-grid;vertical-align:top}
.scene .sw>*{grid-area:1/1}
.scene .swf{position:absolute;inset:-4px -12px;border-radius:10px;background:#c6f135}
.scene .swv{position:relative}
@keyframes scswin{from{opacity:0;transform:translateY(-.35em) scale(1.25)}to{opacity:1;transform:none}}
@keyframes scflash{0%{opacity:0;transform:scaleX(.2)}22%{opacity:.9;transform:none}70%{opacity:.75}100%{opacity:0}}
.scene .table .pi{width:auto;height:auto;min-width:900px}
.scene .tbt{display:flex;align-items:center;gap:18px;margin-bottom:22px;font-family:'DejaVu Sans Mono',monospace;font-weight:700;font-size:50px;color:#f1f2f4}
.scene .tbt svg{width:56px;height:56px;stroke:currentColor;stroke-width:2}
.scene .tbx{background:#16181c;border:2px solid #2a2d33;border-radius:18px;overflow:hidden}
.scene .trw{position:relative;display:grid;align-items:center;column-gap:28px;padding:0 34px;min-height:96px;border-top:2px solid #24272c}
.scene .trw.th{min-height:88px;border-top:none;background:#1e2126;font-family:'DejaVu Sans Mono',monospace;font-weight:700;font-size:40px;color:#c9ccd1}
.scene .trw .tc{position:relative;font-size:46px;font-weight:500;color:#e7e9ec;white-space:nowrap}
.scene .table .bd{padding:0}
.scene .tst{position:absolute;inset:0}
.scene .tst.bad{background:rgba(229,72,77,.32);box-shadow:inset 0 0 0 4px #e5484d}
.scene .tst.ok{background:rgba(62,207,142,.26);box-shadow:inset 0 0 0 4px #3ecf8e}
.scene .tst.hl{background:rgba(198,241,53,.55)}
.scene .code .pi{width:auto;height:auto;background:#16181c;border:2px solid #2a2d33;border-radius:18px;overflow:hidden}
.scene .cdh{padding:18px 34px;border-bottom:2px solid #24272c;font-weight:700;font-size:44px;color:#9aa0a8}
.scene .code .bd{padding:30px 40px 34px;font-family:'DejaVu Sans Mono',monospace;font-size:50px;line-height:1.45;color:#e7e9ec}
.scene .cdl{position:relative;white-space:pre}
.scene .cdt{position:relative;display:inline-block;vertical-align:bottom;overflow:hidden;white-space:pre}
.scene .cdm{position:absolute;top:6%;bottom:2%;margin-left:-.25ch;padding-right:.5ch;box-sizing:content-box;border-radius:8px;background:#c6f135;opacity:.85;transform-origin:left}
.scene .ck{color:#6ea8fe;font-weight:700}.scene .cs{color:#3ecf8e}.scene .cn{color:#ff8a3d}.scene .cc{color:#8b9096;font-style:italic}
.scene .big .pi{display:flex;flex-direction:column;width:auto;height:auto}
.scene .bgv{font-family:Georgia,'DejaVu Serif',serif;font-weight:400;line-height:.95;letter-spacing:-4px}
.scene .bgs{margin-top:16px;font-weight:700;font-size:54px;color:#c9ccd1}
.scene .tagl{position:absolute;width:${W}px;height:${H}px;pointer-events:none}.scene .tagl path{fill:none;stroke-linecap:round}
.scene .tag .pi{display:inline-block;width:auto;height:auto;padding:14px 28px;border-radius:12px;color:#111;font-weight:800;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.18)}
.scene :is(.flow,.grid,.bars,.timeline,.quiz,.form) .pi{width:auto;height:auto}
.scene .flow .bd{display:flex;align-items:flex-start;padding:0}.scene .flow .bd.col{flex-direction:column;align-items:center}
.scene .fst{position:relative;display:flex;flex-direction:column;align-items:center;width:300px;padding:10px 6px 14px;border-radius:22px}
.scene .fsl{position:absolute;inset:0;border-radius:22px;background:rgba(198,241,53,.5)}
.scene .fsi{position:relative;display:flex;align-items:center;justify-content:center;width:150px;height:150px;border:4px solid currentColor;border-radius:30%;background:#16181c}
.scene .fsi svg{width:78px;height:78px;stroke:currentColor;stroke-width:2}
.scene .fsn{position:absolute;left:-16px;top:-16px;display:flex;align-items:center;justify-content:center;width:56px;height:56px;border-radius:50%;background:#c6f135;color:#111;font-weight:800;font-size:34px}
.scene .fsx{position:relative;margin-top:18px;font-weight:700;font-size:46px;line-height:1.15;text-align:center;color:#f1f2f4}
.scene .fss{position:relative;margin-top:6px;font-size:34px;text-align:center;color:#9aa0a8}
.scene .fc{position:relative;flex:none;width:130px;height:150px;margin-top:10px}
.scene .flow .col .fc{width:150px;height:90px;margin-top:0}
.scene .fcl{position:absolute;left:8px;right:8px;top:73px;height:5px;border-radius:3px;background:#8b9096;transform-origin:left}
.scene .flow .col .fcl{left:73px;right:auto;top:6px;bottom:6px;width:5px;height:auto;transform-origin:top}
.scene .fcl::after{content:'';position:absolute;right:-6px;top:-10px;border:12px solid transparent;border-left:16px solid #8b9096;border-right:0}
.scene .flow .col .fcl::after{right:-10px;top:auto;bottom:-6px;border:12px solid transparent;border-top:16px solid #8b9096;border-bottom:0}
.scene .fcp{position:absolute;left:0;top:64px;width:24px;height:24px;margin-left:-12px;border-radius:50%;background:#c6f135;box-shadow:0 0 18px #c6f135}
.scene .flow .col .fcp{left:75px;top:0;margin-top:-12px}
@keyframes scrun{0%{left:8px;opacity:0}12%{opacity:1}85%{opacity:1}100%{left:calc(100% - 8px);opacity:0}}
@keyframes scrunv{0%{top:6px;opacity:0}12%{opacity:1}85%{opacity:1}100%{top:calc(100% - 6px);opacity:0}}
@keyframes scgrowv{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.scene .fcb{position:absolute;left:8px;right:8px;top:72px;height:7px;background:repeating-linear-gradient(90deg,#ff5f57 0 16px,transparent 16px 26px)}
.scene .flow .col .fcb{left:72px;right:auto;top:6px;bottom:6px;width:7px;height:auto;background:repeating-linear-gradient(180deg,#ff5f57 0 16px,transparent 16px 26px)}
.scene .fcx{position:absolute;left:50%;top:50%;width:76px;height:76px;margin:-38px 0 0 -38px;border-radius:50%;background:#ff5f57;display:flex;align-items:center;justify-content:center}
.scene .fcx svg{width:52px;height:52px;stroke:#fff;stroke-width:3.5}
.scene .gtt{margin-bottom:24px;font-family:'DejaVu Sans Mono',monospace;font-weight:700;font-size:40px;color:#c9ccd1}
.scene .gg{display:grid}
.scene .gc{position:relative;display:block;aspect-ratio:1;border-radius:22%;background:#3a3d43;overflow:hidden}
.scene .gc b{position:absolute;inset:0}
.scene .bars .bd,.scene .quiz .bd,.scene .form .bd{padding:0}
.scene .brw{position:relative;display:grid;grid-template-columns:340px 1fr 220px;align-items:center;column-gap:30px;min-height:104px;padding:0 20px;border-radius:14px}
.scene .brl{position:relative;font-weight:700;font-size:46px;color:#f1f2f4;white-space:nowrap}
.scene .brt{position:relative;height:40px;border-radius:20px;background:#2a2d33}
.scene .brf,.scene .brd{position:absolute;left:0;top:0;bottom:0;border-radius:20px;transform-origin:left}
.scene .brd{top:16px;bottom:16px}
.scene .bro{position:absolute;top:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:6px solid;background:#16181c;box-sizing:border-box}
.scene .brv{position:relative;font-family:Georgia,'DejaVu Serif',serif;font-size:54px;color:#f1f2f4;text-align:right}
.scene .tlx{--pl:330px;position:relative;box-sizing:border-box;padding-left:var(--pl)}.scene .tlx.top{--pl:0px}
.scene .tlr{position:relative;height:80px;margin-bottom:10px}
.scene .tlk{position:absolute;top:0;transform:translateX(-50%);font-family:'DejaVu Sans Mono',monospace;font-size:46px;color:#9aa0a8;white-space:nowrap}
.scene .tlk:first-child{transform:none}.scene .tlk:last-child{transform:translateX(-100%)}
.scene .timeline .bd{padding:0}
.scene .tll{position:relative;display:flex;align-items:center;height:140px}.scene .tlx.top .tll{height:200px;padding-top:60px;box-sizing:border-box}
.scene .tln{position:absolute;left:-330px;width:300px;font-weight:700;font-size:50px;color:#f1f2f4}.scene .tlx.top .tln{left:0;top:0;width:auto}
.scene .tlt{position:relative;flex:1;height:8px;border-radius:4px;background:#3a3d43}
.scene .tls{position:absolute;top:-30px;height:84px;margin-top:-8px;border-radius:12px;transform-origin:left;display:flex;align-items:center;padding:0 22px;box-sizing:border-box;font-weight:800;font-size:46px;color:#111;white-space:nowrap;overflow:hidden}
.scene .tlh{position:absolute;top:60px;bottom:-10px;width:5px;margin-left:-2px;background:#ff5f57;border-radius:3px}
.scene .qq{max-width:1500px;margin-bottom:30px;font-weight:800;font-size:56px;line-height:1.2;color:#f1f2f4}
.scene .qo{position:relative;display:flex;align-items:center;gap:30px;min-height:110px;margin-top:14px;padding:0 30px;border:3px solid #2a2d33;border-radius:18px;background:#16181c;max-width:1500px}
.scene .qk{position:relative;flex:none;display:flex;align-items:center;justify-content:center;width:64px;height:64px;border-radius:12px;background:#2a2d33;color:#f1f2f4;font-weight:800;font-size:36px}
.scene .qk b{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;border-radius:12px;background:#3ecf8e}.scene .qk b svg{width:44px;height:44px;stroke:#fff;stroke-width:3.5}
.scene .qt{position:relative;flex:1;font-size:44px;line-height:1.25;color:#e7e9ec}
.scene .qp{position:relative;font-family:Georgia,'DejaVu Serif',serif;font-size:52px;color:#f1f2f4}
.scene .form .pi{min-width:760px;background:#16181c;border:2px solid #2a2d33;border-radius:22px;overflow:hidden}
.scene .ffh{display:flex;align-items:center;gap:18px;padding:26px 36px;border-bottom:2px solid #24272c;font-weight:800;font-size:48px;color:#f1f2f4}
.scene .ffh svg{width:52px;height:52px;stroke:currentColor;stroke-width:2}
.scene .form .bd{padding:26px 36px 34px}
.scene .ffd{margin-bottom:26px}
.scene .ffl{display:block;margin-bottom:10px;font-size:34px;color:#9aa0a8}
.scene .ffv{display:block;padding:16px 22px;border:2px solid #2a2d33;border-radius:12px;font-size:44px;color:#f1f2f4}
.scene .ffb{display:inline-block;padding:16px 40px;border-radius:12px;font-weight:800;font-size:42px;color:#111}
.scene .ffn{display:flex;align-items:center;gap:14px;margin-top:24px;font-weight:800;font-size:40px}.scene .ffn svg{width:46px;height:46px;stroke:currentColor;stroke-width:2.5}
</style>`;

// "look": "paper\" (style/REF-shorts-arjay.md): a warm off-white page, white cards with hairline borders, near-black ink, one lime
// marker; a terminal stays dark (it is a real terminal). Only in a scene with the key.
const PAPER_CSS = `<style>
.scene.paper{background:#f4f3ee;background-image:none}
.scene.paper .win .pi,.scene.paper .file .pi,.scene.paper .code .pi,.scene.paper .tbx{background:#fff;border:2px solid #e2e0d8;border-radius:16px;box-shadow:0 14px 40px rgba(40,36,20,.08)}
.scene.paper .tb{border-bottom-color:#ecebe4;color:#2a2c31}.scene.paper .tb svg{stroke:#6b6f76}
.scene.paper .rt{color:#1d1f24}.scene.paper .sk{background:#e6e4dc}
.scene.paper .rhl{opacity:.32}
.scene.paper .chip .pi,.scene.paper .steps .pi{background:#fff;border-color:#e2e0d8;color:#16181d}
.scene.paper .nt{background:#fff}.scene.paper .nt.you{border-color:#cfcdc4;color:#3a3d43}
.scene.paper .nl{color:#16181d}.scene.paper .ns{color:#6b6f76}
.scene.paper .msg{background:#fff;border-color:#e2e0d8;color:#1d1f24}.scene.paper .msg.me{background:#e8f0fe;border-color:#c9dbf7}
.scene.paper .stamp .pi{background:rgba(244,243,238,.94)}
.scene.paper .say .pi{color:#16181d}
.scene.paper .toggle .pi{color:#16181d}.scene.paper .tgb{background:#d9d7cf}
.scene.paper .stot{color:#6b6f76}.scene.paper .str{background:#e6e4dc}
.scene.paper .bl{color:#3a3d43}.scene.paper .tr{background:#e6e4dc}.scene.paper .sl{color:#4a4e55}
.scene.paper .mk svg{stroke:#fff}
.scene.paper .cur svg{filter:drop-shadow(0 6px 10px rgba(0,0,0,.25))}
.scene.paper .tbt{color:#16181d}
.scene.paper .trw{border-top-color:#ecebe4}.scene.paper .trw.th{background:#f0efe9;color:#2a2c31}.scene.paper .trw .tc{color:#1d1f24}
.scene.paper .cdh{border-bottom-color:#ecebe4;color:#6b6f76}
.scene.paper .code .bd{color:#1d1f24}
.scene.paper .ck{color:#1f4fd1}.scene.paper .cs{color:#16884a}.scene.paper .cn{color:#c2410c}.scene.paper .cc{color:#8b9096}
.scene.paper .bgs{color:#3a3d43}
.scene.paper .fsi,.scene.paper .bro{background:#fff}.scene.paper .fsx{color:#16181d}.scene.paper .fss{color:#6b6f76}
.scene.paper .fcl{background:#3a3d43}.scene.paper .fcl::after{border-left-color:#3a3d43}.scene.paper .flow .col .fcl::after{border-left-color:transparent;border-top-color:#3a3d43}
.scene.paper .gtt{color:#3a3d43}.scene.paper .gc{background:#dddbd2}
.scene.paper .brl,.scene.paper .brv,.scene.paper .tln,.scene.paper .qq,.scene.paper .qp{color:#16181d}.scene.paper .brt,.scene.paper .tlt{background:#e6e4dc}
.scene.paper .tlk{color:#6b6f76}
.scene.paper .qo{background:#fff;border-color:#e2e0d8}.scene.paper .qk{background:#f0efe9;color:#16181d}.scene.paper .qt{color:#1d1f24}
.scene.paper .form .pi{background:#fff;border-color:#e2e0d8;box-shadow:0 14px 40px rgba(40,36,20,.08)}.scene.paper .ffh{border-bottom-color:#ecebe4;color:#16181d}
.scene.paper .ffl{color:#6b6f76}.scene.paper .ffv{border-color:#e2e0d8;color:#16181d}
.scene.paper .term .pi{box-shadow:0 14px 40px rgba(40,36,20,.18)}
</style>`;
