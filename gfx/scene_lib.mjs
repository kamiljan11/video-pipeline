// "scene" card: a full-screen explainer drawn as a dark canvas of small app pieces (windows, files, a terminal, chips, chat,
// lines between them) that come in one by one while they are named, with an optional camera that pans and zooms between
// them. The face sits in the PiP circle bottom right (gfx_types.PIP), so the canvas keeps that corner free.
// Every piece animates with CSS keyframes and inline delays, so render.mjs seeks any frame (document.getAnimations()).
// Spec: {"id", "type": "scene", "dur", "els": [piece…], "cam": [stop…] | "none"}; piece kinds and keys: README › Scena.
// Camera: without "cam" the whole drawing is framed to fill the free part of the frame (left of the face circle). A stop is
// {t, on: "<piece id>" | [ids] | "*", pad, zmax, move} (frame these pieces) or {t, x, y, z} (world point x, y at the top
// left, zoom z). Pieces are measured in the browser (render.mjs calls sceneFit), so nobody has to guess their size.

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
export const TONES = { acc: 'var(--acc)', ok: '#3ecf8e', bad: '#ff5f57', warn: '#f5b84a', blue: '#6ea8fe', orange: '#ff8a3d', mute: '#8b9096' };
// pieces tied to another piece's place (a line between two, a cursor path, a ring around a box): a scene with one stays laid
// out as drawn, so it cannot be stacked into the column beside the speaker (screen_grammar keeps it full screen)
export const TIED = ['line', 'cursor', 'ring', 'stamp', 'check'];  // pieces placed on another piece (screen_grammar.py TIED, tests/test_screen_grammar.py checks both match)
export const KINDS = ['win', 'file', 'term', 'chip', 'node', 'chat', 'you', 'line', 'stamp', 'text', 'bar', 'stat', 'check', 'cursor', 'ring', 'say', 'toggle', 'steps'];
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
const TYPE_CPS = 28;   // terminal typing speed, characters per second
const LINE_STEP = 0.09; // terminal output lines come in this far apart

const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d);
const tone = t => TONES[t] ?? TONES.acc;
const f2 = x => (+x).toFixed(2);

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

// 9:16 "solo" (a short): a camera that frames the piece being said in a narrow frame cuts its wide neighbours at the edge
// (film 2 shorts, 2026-11-04: "same się odpalają" half off screen). So in a 9:16 scene a piece that does not fit the free area
// at a camera stop fades out for that stop and back in when a stop frames it again; the last stop ("*") shows the whole
// drawing. pieces: [{x, y, w, h}] in world px; stops: resolved {t, x, y, z, move}; returns per piece [[t, opacity], ...]
// or null when it never hides. Self-contained: render.mjs ships its source into the page like camKeyframes.
export function soloKeys(pieces, stops, dur, safe, tol = 24) {
  const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d), FADE = 0.25, MOVE = 0.9;
  const fits = (p, s) => {
    const z = num(s.z, 1), x0 = (p.x - num(s.x, 0)) * z, y0 = (p.y - num(s.y, 0)) * z;
    return x0 >= safe.x - tol && y0 >= safe.y - tol && x0 + p.w * z <= safe.x + safe.w + tol && y0 + p.h * z <= safe.y + safe.h + tol;
  };
  return pieces.map(p => {
    const vis = stops.map(s => fits(p, s));
    if (vis.every(Boolean)) return null;
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
      if (!pt(e.from) || !pt(e.to)) bad.push(`${n}: "from" and "to" = [x, y]`);
    } else if (!Number.isFinite(e.x) || !Number.isFinite(e.y)) bad.push(`${n}: "x" and "y" are required`);
    for (const key of ['click_at', 'on_at', 'out_at', 'strike_at', 'hl_at', 'packet_at'])
      if (e[key] !== undefined && !(typeof e[key] === 'number' && e[key] >= 0 && e[key] < dur)) bad.push(`${n}: "${key}" = seconds 0..dur, got ${JSON.stringify(e[key])}`);
    if (e.pulse_at !== undefined && ![].concat(e.pulse_at).every(t => typeof t === 'number' && t >= 0 && t < dur)) bad.push(`${n}: "pulse_at" = seconds 0..dur (one or a list)`);
    if (e.k === 'ring' && !(e.w > 0 && e.h > 0)) bad.push(`${n}: "w" and "h" = the box to circle`);
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
    if (e.k === 'stat' && e.count !== undefined && !(e.count && Number.isFinite(e.count.to))) bad.push(`${n}: "count" = {"from", "to", "d"} numbers`);
    if (e.k === 'term' && typeof e.cmd !== 'string') bad.push(`${n}: "cmd" = the command, as it was typed`);
    if (e.k === 'term' && e.out !== undefined && !(Array.isArray(e.out) && e.out.every(l => typeof l === 'string'))) bad.push(`${n}: "out" = the real output, a list of lines`);
    if (e.tone !== undefined && !(e.tone in TONES)) bad.push(`${n}: "tone" one of ${Object.keys(TONES).join(', ')}`);
    if (e.anim !== undefined && !(e.anim in ANIMS)) bad.push(`${n}: "anim" one of ${Object.keys(ANIMS).join(', ')}`);
  });
  const ids = new Set((sp.els || []).map(e => e && e.id).filter(Boolean));
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
  } else if (sp.cam !== undefined && sp.cam !== 'none') bad.push('"cam": a list of stops, "none" or nothing (frame the whole drawing)');
  if (sp.bg !== undefined && !BGS.includes(sp.bg)) bad.push(`"bg" one of ${BGS.join(', ')}`);
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
function row(r, esc, icon, at) {
  if (typeof r === 'string' && /^~\d*$/.test(r)) return `<div class="sk" style="width:${r.length > 1 ? +r.slice(1) : 70}%"></div>`;
  const o = typeof r === 'string' ? { t: r } : r;
  const mk = o.mark ? `<span class="mk ${o.mark}" style="animation:scpop .4s cubic-bezier(.2,1.6,.4,1) ${f2(num(o.mark_at, at + 0.4))}s both">${icon({ ok: 'check', bad: 'x', warn: 'triangle-alert' }[o.mark] ?? 'check')}</span>` : '';
  const hl = o.hl ? `<span class="rhl" style="background:${tone(o.tone ?? (o.mark === 'bad' ? 'bad' : 'acc'))};animation:scgrow .45s ease-out ${f2(num(o.hl_at, at + 0.6))}s both"></span>` : '';
  const body = typeof o.t === 'string' && /^~\d*$/.test(o.t) ? `<div class="sk" style="width:${o.t.length > 1 ? +o.t.slice(1) : 70}%"></div>` : `<span class="rt">${esc(o.t ?? '')}</span>`;
  return `<div class="row">${hl}${body}${mk}</div>`;
}

// a short stable id from a piece's spec (keyframes per piece need a unique name; same spec = same name, renders repeat)
const uid = e => 'u' + Math.abs([...JSON.stringify(e)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 7)).toString(36);
const DEF_ANIM = { stamp: 'drop', line: 'fade', check: 'fade', cursor: 'fade', ring: 'fade', say: 'fade', steps: 'blur' };

// one drawer per piece kind (KINDS): (e, c) -> { inner, style } for a piece in the common box (entrance, pulse, dim, gone added
// by piece()), or { html } for a kind that draws its own box (cursor, ring, line). c = { esc, icon, at, tn }.
// A new kind = one entry here + its name in KINDS + its keys in checkScene (and README "Scena").
const idAttr = (e, esc) => (e.id ? ` data-id="${esc(e.id)}"` : '');
const winFile = (e, { esc, icon, at }) => {
  const head = e.k === 'win'
    ? `<div class="tb"><i></i><i></i><i></i><span class="ti">${e.icon ? icon(e.icon) : ''}${esc(e.title ?? '')}</span></div>`
    : `<div class="tb fb">${icon(e.icon ?? 'file-text')}<span class="ti">${esc(e.name ?? e.title ?? '')}</span>${e.badge ? `<span class="bdg" style="color:${tone(e.badge.tone)};border-color:${tone(e.badge.tone)};animation:scpop .4s cubic-bezier(.2,1.6,.4,1) ${f2(num(e.badge.at, at + 0.5))}s both">${esc(e.badge.text)}</span>` : ''}</div>`;
  const rows = (e.rows ?? ['~80', '~55', '~70']).map((r, i) => row(r, esc, icon, at + 0.15 + i * num(e.step, 0.12))).join('');
  return { inner: `${head}<div class="bd">${rows}</div>` };
};
const PIECES = {
  win: winFile,
  file: winFile,
  term: (e, { esc, at, tn }) => {
    const cmdAt = num(e.cmd_at, at + 0.5), typed = e.cmd.length / TYPE_CPS, outAt = num(e.out_at, cmdAt + typed + 0.35);
    const lines = (e.out ?? []).map((l, i) => `<div class="ol${(e.hl ?? []).includes(i) ? ' hot' : ''}" style="animation:scfade .15s ${f2(outAt + i * LINE_STEP)}s both">`
      + `${(e.hl ?? []).includes(i) ? `<span class="rhl" style="background:${tn};animation:scgrow .45s ease-out ${f2(num(e.hl_at, outAt + (e.out.length) * LINE_STEP + 0.4))}s both"></span>` : ''}<span>${esc(l)}</span></div>`).join('');
    return { inner: `<div class="tb"><i></i><i></i><i></i><span class="ti">${esc(e.title ?? 'terminal')}</span></div>`
      + `<div class="bd"><div class="cl"><span class="ps">${esc(e.prompt ?? '$')}</span> <span class="cmd" style="--n:${e.cmd.length};animation:sctype ${f2(Math.max(typed, 0.1))}s steps(${Math.max(e.cmd.length, 1)}) ${f2(cmdAt)}s both">${esc(e.cmd)}</span></div>${lines}</div>` };
  },
  chip: (e, { esc, icon, tn }) => ({ inner: `<span class="ci" style="background:${tn}">${icon(e.icon ?? 'zap')}</span><span>${esc(e.text ?? '')}</span>` }),
  node: (e, { esc, icon, tn }) => {
    const s = num(e.size, 200);
    return { inner: `<div class="nt" style="width:${s}px;height:${s}px;color:${tn};border-color:${tn}">${icon(e.icon ?? 'box')}</div>${e.text ? `<div class="nl">${esc(e.text)}</div>` : ''}${e.sub ? `<div class="ns">${esc(e.sub)}</div>` : ''}` };
  },
  you: (e, { esc, icon }) => ({ inner: `<div class="nt you">${icon('user')}</div><div class="nl">${esc(e.text ?? 'Ty')}</div>` }),
  chat: (e, { esc, at }) => ({
    inner: (e.msgs ?? []).map((m, i) => {
      const t = num(m.at, at + i * num(e.step, 0.5)), sk = typeof m.t !== 'string' || /^~\d*$/.test(m.t);
      return `<div class="msg ${m.who === 'me' ? 'me' : 'ai'}" style="animation:scup .4s cubic-bezier(.2,.9,.2,1) ${f2(t)}s both">${sk ? `<div class="sk" style="width:${((m.t ?? '~').length > 1 ? +(m.t ?? '~').slice(1) : 70) * 6}px"></div>` : esc(m.t)}</div>`;
    }).join(''),
  }),
  stamp: (e, { esc, tn }) => ({ style: `color:${tn};border-color:${tn};--r:${num(e.rot, -6)}deg;`, inner: esc(e.text ?? '') }),
  text: (e, { esc, tn }) => ({
    style: `font-size:${num(e.size, 64)}px;color:${e.tone ? tn : '#f1f2f4'};${e.w ? '' : 'white-space:nowrap;'}`,
    inner: esc(e.t ?? '').replace(/\*([^*]+)\*/g, '<b>$1</b>'),
  }),
  bar: (e, { esc, at, tn }) => {
    const v = Math.min(Math.max(num(e.v, 1), 0), 1);
    return { inner: `${e.label ? `<div class="bl">${esc(e.label)}</div>` : ''}<div class="tr"><div class="fl" style="width:${(v * 100).toFixed(1)}%;background:${tn};animation:scgrow ${f2(num(e.d, 1))}s cubic-bezier(.2,.8,.2,1) ${f2(at + 0.3)}s both"></div></div>` };
  },
  stat: (e, { esc, at, tn }) => {
    if (!e.count) return { inner: `<div class="sv" style="color:${tn}">${esc(e.value ?? '')}</div><div class="sl">${esc(e.label ?? '')}</div>` };
    const c = e.count, u = uid(e), d = num(c.d, 1);  // the number counts up to its value while it is said (@property --cnt, seekable)
    return { inner: `<style>@keyframes cnt_${u}{from{--cnt:${Math.round(num(c.from, 0))}}to{--cnt:${Math.round(c.to)}}}</style>`
      + `<div class="sv cnt" data-pre="${esc(c.pre ?? '')}" data-suf="${esc(c.suf ?? '')}" style="color:${tn};animation:cnt_${u} ${f2(d)}s ${EASE_IN} ${f2(num(c.at, at + 0.2))}s both"></div><div class="sl">${esc(e.label ?? '')}</div>` };
  },
  check: (e, { at, tn }) => {  // ring draws, tick draws, a burst ring and ten sparks fly out (deterministic angles)
    const sz = num(e.size, 120), r = sz / 2 - 6, c = (2 * Math.PI * r).toFixed(0), tk = (sz * 0.9).toFixed(0);
    const sparks = Array.from({ length: 10 }, (_, i) => {
      const a = (i * 36 + 13) * Math.PI / 180, d = sz * (0.62 + 0.09 * (i % 3));
      return `<i class="pt" style="background:${tn};--dx:${(Math.cos(a) * d).toFixed(0)}px;--dy:${(Math.sin(a) * d).toFixed(0)}px;animation:scpart .45s ${EASE_IN} ${f2(at + 0.3)}s both"></i>`;
    }).join('');
    return { style: `width:${sz}px;height:${sz}px;`,
      inner: `<svg viewBox="0 0 ${sz} ${sz}" width="${sz}" height="${sz}" style="overflow:visible">`
        + `<circle cx="${sz / 2}" cy="${sz / 2}" r="${r}" fill="${tn}" fill-opacity=".14" stroke="${tn}" stroke-width="7" style="stroke-dasharray:${c};stroke-dashoffset:${c};transform:rotate(-90deg);transform-origin:center;animation:scdraw .28s ${EASE_MOVE} ${f2(at)}s forwards"/>`
        + `<path d="M${f2(sz * 0.3)} ${f2(sz * 0.52)} L${f2(sz * 0.45)} ${f2(sz * 0.66)} L${f2(sz * 0.72)} ${f2(sz * 0.36)}" fill="none" stroke="${tn}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" style="stroke-dasharray:${tk};stroke-dashoffset:${tk};animation:scdraw .22s ${EASE_MOVE} ${f2(at + 0.26)}s forwards"/></svg>`
        + `<i class="bst" style="border-color:${tn};animation:scburst .4s ${EASE_IN} ${f2(at + 0.3)}s both"></i>${sparks}` };
  },
  cursor: (e, { esc, at, tn }) => {  // moves from -> to, arriving at click_at; presses; a ripple where it clicked
    const [x1, y1] = e.from, [x2, y2] = e.to, ca = num(e.click_at, at + 0.75), mv = Math.min(0.7, Math.max(0.2, ca - at - 0.05));
    const gone = e.gone !== undefined ? `,scfadeout .3s ease-in ${f2(e.gone)}s forwards` : '';
    return { html: `<div class="p cursor"${idAttr(e, esc)} data-bb="${Math.min(x1, x2)} ${Math.min(y1, y2)} ${Math.abs(x2 - x1) + 60} ${Math.abs(y2 - y1) + 60}" style="left:0;top:0">`
      + `<i class="rip" style="left:${x2}px;top:${y2}px;border-color:${tn};animation:scrip .5s ${EASE_IN} ${f2(ca)}s both"></i>`
      + `<div class="cur" style="--fx:${x1}px;--fy:${y1}px;--tx:${x2}px;--ty:${y2}px;animation:scfade .2s ${f2(at)}s both,sccur ${f2(mv)}s ${EASE_MOVE} ${f2(ca - mv)}s both${gone}">`
      + `<svg viewBox="0 0 32 32" style="animation:scpress .18s ease-out ${f2(ca)}s"><path d="M5 3 L5 26 L11 20 L15 29 L19 27 L15 18 L23 18 Z" fill="#fff" stroke="#0c0d0f" stroke-width="2" stroke-linejoin="round"/></svg></div></div>` };
  },
  ring: (e, { esc, at, tn }) => {  // a hand-drawn circle around a box: one turn and a bit, the radius wobbling a few per cent
    const pad = num(e.pad, 24), cx = e.x + e.w / 2, cy = e.y + e.h / 2, rx = e.w / 2 + pad, ry = e.h / 2 + pad;
    const pts = Array.from({ length: 57 }, (_, i) => {
      const a = -2.2 + (i / 50) * 2 * Math.PI, w = 1 + 0.03 * Math.sin(i * 1.7);
      return `${(cx + Math.cos(a) * rx * w).toFixed(1)} ${(cy + Math.sin(a) * ry * w * (1 + (i / 56) * 0.05)).toFixed(1)}`;
    });
    const len = (Math.PI * (rx + ry) * 1.2).toFixed(0), gone = e.gone !== undefined ? `;animation:scfadeout .3s ease-in ${f2(e.gone)}s forwards` : '';
    return { html: `<svg class="ln"${idAttr(e, esc)} data-bb="${e.x - pad} ${e.y - pad} ${e.w + 2 * pad} ${e.h + 2 * pad}" viewBox="0 0 ${W} ${H}" style="overflow:visible${gone}"><path d="M${pts.join(' L')}" stroke="${tn}" style="stroke-width:7;stroke-dasharray:${len};stroke-dashoffset:${len};animation:scdraw ${f2(num(e.d, 0.6))}s ${EASE_MOVE} ${f2(at)}s forwards"/></svg>` };
  },
  say: (e, { esc, tn }) => ({  // a kinetic line: each word blurs in when it is said; *em* serif accent, [pill], ~strike~, !red!
    style: `font-size:${num(e.size, 84)}px;${e.w ? '' : 'white-space:nowrap;'}`,
    inner: e.words.map(([w, t]) => {
      const m = /^([*[~!])(.+)([*\]~!])$/.exec(w), cls = m ? { '*': 'em', '[': 'pill', '~': 'strk', '!': 'bad' }[m[1]] : '', txt = m ? m[2] : w;
      const extra = cls === 'pill' ? `<i class="hlp" style="background:${tn};animation:scgrow .4s ${EASE_IN} ${f2(t + 0.15)}s both"></i>`
        : cls === 'strk' ? `<i class="sk2" style="animation:scgrow .25s ${EASE_MOVE} ${f2(t + 0.35)}s both"></i>` : '';
      return `<span class="w ${cls}" style="animation:scword .3s ${EASE_IN} ${f2(Math.max(0, t - 0.03))}s both">${extra}<span>${esc(txt)}</span></span>`;
    }).join(' '),
  }),
  toggle: (e, { esc, at, tn }) => {  // a switch flips on at on_at: knob slides with a little overshoot, the track takes the colour
    const on = num(e.on_at, at + 0.8);
    return { inner: `<span class="tg"><i class="tgb" style="--on:${tn};animation:sctgbg .2s ${EASE_MOVE} ${f2(on)}s both"></i><i class="tgk" style="animation:sctgk .25s ${EASE_POP} ${f2(on)}s both"></i></span>${e.text ? `<span class="tgl">${esc(e.text)}</span>` : ''}` };
  },
  steps: (e, { esc, tn }) => {  // a progress pill "label N / total": the number changes and the bar grows at each step
    const st = e.steps;
    const nums = st.map(([t, n], i) => `<b class="sn" style="animation:scfade .15s ${f2(t)}s both${i + 1 < st.length ? `,scfadeout .12s ${f2(st[i + 1][0])}s forwards` : ''}">${n}</b>`).join('');
    const fills = st.map(([t, n], i) => `<i class="sf" style="background:${tn};--w0:${(((st[i - 1]?.[1]) ?? 0) / e.total * 100).toFixed(1)}%;--w1:${(n / e.total * 100).toFixed(1)}%;animation:scfill .35s ${EASE_IN} ${f2(t)}s both"></i>`).join('');
    return { inner: `<span class="stl">${esc(e.label ?? '')}</span><span class="sbox">${nums}</span><span class="stot">/ ${e.total}</span><span class="str">${fills}</span>` };
  },
  line: (e, { esc, at, tn }) => {
    const [x1, y1] = e.from, [x2, y2] = e.to, len = Math.hypot(x2 - x1, y2 - y1) * 1.3 + 40;
    const c = num(e.curve, 0.35), mx = x1 + (x2 - x1) * c, d = `M${x1} ${y1} C${mx} ${y1},${x2 - (x2 - x1) * c} ${y2},${x2} ${y2}`;
    let dx = (x2 - x1) * c, dy = 0;  // the curve ends level with its last control point; a straight vertical line has no such tangent
    if (Math.abs(dx) < 1) { dx = x2 - x1; dy = y2 - y1; }
    const ang = (Math.atan2(dy, dx) * 180 / Math.PI).toFixed(1), hat = f2(at + num(e.d, 0.7) - 0.05);
    const head = e.arrow === false ? '' : e.head === 'arrow'
      ? `<g transform="translate(${x2} ${y2}) rotate(${ang})"><path d="M4 0 L-30 -17 L-22 0 L-30 17 Z" fill="${tn}" style="transform-box:fill-box;transform-origin:right center;animation:scpop .14s ${EASE_POP} ${hat}s both"/></g>`
      : `<circle cx="${x2}" cy="${y2}" r="9" fill="${tn}" style="animation:scfade .2s ${f2(at + num(e.d, 0.7))}s both"/>`;
    const pk = e.packet_at !== undefined ? `<i class="pk" style="background:${tn};color:${tn};offset-path:path('${d}');animation:scpath ${f2(num(e.packet_d, 0.8))}s ${EASE_MOVE} ${f2(e.packet_at)}s both"></i>` : '';
    return { html: `<svg class="ln"${idAttr(e, esc)} data-bb="${Math.min(x1, x2)} ${Math.min(y1, y2)} ${Math.abs(x2 - x1)} ${Math.abs(y2 - y1)}" viewBox="0 0 ${W} ${H}" style="overflow:visible"><path d="${d}" stroke="${tn}" style="stroke-dasharray:${len.toFixed(0)};stroke-dashoffset:${len.toFixed(0)};animation:scdraw ${f2(num(e.d, 0.7))}s cubic-bezier(.4,0,.2,1) ${f2(at)}s forwards"/>${head}</svg>${pk}` };
  },
};

// the common box of a piece: place and size, then the drawer's inner HTML wrapped in its entrance and later moves
function piece(e, esc, icon) {
  const at = num(e.at, e.k === 'say' ? Math.max(0, Math.min(...e.words.map(w => w[1])) - 0.05) : 0);
  const anim = ANIMS[e.anim ?? DEF_ANIM[e.k] ?? 'up'];
  const tn = tone(e.tone);
  const drawn = PIECES[e.k]?.(e, { esc, icon, at, tn }) ?? { inner: '' };
  if (drawn.html !== undefined) return drawn.html;
  const style = `left:${e.x}px;top:${e.y}px;${e.w ? `width:${e.w}px;` : ''}${e.h ? `height:${e.h}px;` : ''}${drawn.style ?? ''}`;
  let inner = drawn.inner;
  if (e.hl_at !== undefined) inner = `<i class="ghl" style="background:${tn};animation:scgrow .4s ${EASE_IN} ${f2(e.hl_at)}s both"></i><span class="ght">${inner}</span>`;
  if (e.strike_at !== undefined) inner += `<i class="gstrk" style="animation:scgrow .25s ${EASE_MOVE} ${f2(e.strike_at)}s both"></i>`;
  const outs = [`${anim} ${f2(at)}s both`];
  for (const t of [].concat(e.pulse_at ?? [])) outs.push(`scpulse .45s ${EASE_POP} ${f2(t)}s`);  // no fill: the entrance's end state stays
  if (e.strike_at !== undefined) outs.push(`scdimh .25s ease-out ${f2(e.strike_at + 0.1)}s forwards`);
  if (e.out_at !== undefined) outs.push(`scblurout .18s ease-in ${f2(e.out_at)}s forwards`);
  if (e.dim !== undefined) outs.push(`scdim .4s ease-out ${f2(e.dim)}s forwards`);
  if (e.gone !== undefined) outs.push(`scgone .35s ease-in ${f2(e.gone)}s forwards`);
  return `<div class="p ${e.k}"${idAttr(e, esc)} style="${style}"><div class="pi" style="animation:${outs.join(',')}">${inner}</div></div>`;
}

export function scene(sp, esc, icon) {
  const bad = checkScene(sp);
  if (bad.length) throw new Error(`"${sp.id}": scene: ${bad.join('; ')}`);
  const safeIcon = n => { try { return icon(n); } catch { throw new Error(`"${sp.id}": no icon "${n}" in lucide-static`); } };
  const cam = sp.cam === 'none' ? null : sp.cam ?? [{ t: 0, on: '*' }];
  const side = sp.layout === 'side' && sp.canvas !== 'v';
  // beside the speaker the pieces stack in one column in reading order (top to bottom, then left to right), so the
  // camera fits a tall narrow block into the tall narrow board and the text stays big (Kamil 2026-11-05: on a phone held
  // sideways a wide drawing shrunk into the side field cannot be read; "większe i pionowo narysowane")
  const col = side && sp.els.every(e => !TIED.includes(e.k));
  const els = col ? [...sp.els].sort((a, b) => (a.y ?? 0) - (b.y ?? 0) || (a.x ?? 0) - (b.x ?? 0)) : sp.els;
  const world = els.map(e => piece(e, esc, safeIcon)).join('');
  const bg = side ? `<div class="board" style="left:${SIDE.x}px;top:${SIDE.y}px;width:${SIDE.w}px;height:${SIDE.h}px"></div>`
    : sp.bg === 'blobs' ? '<div class="blobs"><i class="b1"></i><i class="b2"></i><i class="b3"></i></div>' : '';
  return `${SCENE_CSS}<div class="scene${side ? ' side' : ''}${col ? ' col' : ''}">${bg}<div class="world"${cam ? ` data-cam="${esc(JSON.stringify(cam)).replace(/"/g, '&quot;')}" data-dur="${sp.dur}"${sp.canvas === 'v' ? ' data-solo="1"' : ''}` : ''}>${world}</div></div>`;
}

// in the page, before the first frame (render.mjs): measures the pieces as laid out (their final place, not mid-animation),
// turns every "on" stop into x, y, z that put those pieces in the middle of the free area, and starts the camera animation.
// Self-contained: its source is evaluated in the page with camKeyframes' source as the second argument.
export function sceneFit(safe, kfSrc, soloSrc) {
  const camKeyframes = new Function(`return ${kfSrc}`)();
  const world = document.querySelector('.scene .world');
  if (!world || !world.dataset.cam) return null;
  const cam = JSON.parse(world.dataset.cam), dur = +world.dataset.dur;
  const pieces = [...world.querySelectorAll(':scope > .p, :scope > svg.ln')].map(el => {
    if (el.dataset.bb) { const [x, y, w, h] = el.dataset.bb.split(' ').map(Number); return { id: el.dataset.id, x, y, w, h }; }
    return { id: el.dataset.id, x: el.offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight };
  });
  const frame = s => {
    const want = s.on === undefined || s.on === '*' ? null : [].concat(s.on);
    const got = pieces.filter(p => !want || want.includes(p.id));
    const x0 = Math.min(...got.map(p => p.x)), y0 = Math.min(...got.map(p => p.y));
    const x1 = Math.max(...got.map(p => p.x + p.w)), y1 = Math.max(...got.map(p => p.y + p.h));
    const pad = s.pad ?? 50, bw = x1 - x0 + 2 * pad, bh = y1 - y0 + 2 * pad;
    const z = Math.min(safe.w / bw, safe.h / bh, s.zmax ?? 1.8);
    return { t: s.t, move: s.move, z, x: (x0 + x1) / 2 - (safe.x + safe.w / 2) / z, y: (y0 + y1) / 2 - (safe.y + safe.h / 2) / z };
  };
  const stops = cam.map(s => (s.on !== undefined || (s.x === undefined && s.y === undefined) ? frame(s) : s));
  const st = document.createElement('style');
  st.textContent = `@keyframes cam_fit{${camKeyframes(stops, dur)}}`;
  document.head.appendChild(st);
  world.style.animation = `cam_fit ${dur}s linear both`;
  if (world.dataset.solo && soloSrc) {  // 9:16: a piece cut by the frame edge hides for that stop (soloKeys)
    const soloKeys = new Function(`return ${soloSrc}`)();
    const els = [...world.querySelectorAll(':scope > .p, :scope > svg.ln')];
    soloKeys(pieces, stops, dur, safe).forEach((keys, i) => {
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
.scene .tb{display:flex;align-items:center;gap:14px;height:80px;padding:0 28px;border-bottom:2px solid #24272c;color:#c9ccd1;font-weight:600;font-size:36px}
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
.scene .ns{margin-top:6px;color:#8b9096;font-weight:600;font-size:30px;white-space:nowrap}
.scene .chat .pi{display:flex;flex-direction:column;gap:18px}
.scene .msg{max-width:78%;padding:24px 32px;border-radius:26px;font-weight:600;font-size:42px;line-height:1.25;color:#eef0f2;background:#1d2025;border:2px solid #2a2d33}
.scene .msg.me{align-self:flex-end;background:#232a35;border-color:#2f3a4a;border-bottom-right-radius:8px}
.scene .msg.ai{align-self:flex-start;border-bottom-left-radius:8px}
.scene .stamp .pi{display:inline-block;width:auto;height:auto;padding:18px 44px;border:7px solid;border-radius:18px;font-weight:900;font-size:84px;letter-spacing:6px;background:rgba(12,13,15,.86)}
.scene .stamp{transform:rotate(var(--r))}
.scene .text .pi{font-weight:800;line-height:1.12;letter-spacing:-1px}
.scene .text b{color:var(--acc)}
.scene .bl{color:#c9ccd1;font-weight:700;font-size:34px;margin-bottom:14px}
.scene .tr{height:30px;border-radius:15px;background:#23262b;overflow:hidden}
.scene .fl{height:100%;border-radius:15px;transform-origin:left}
.scene .stat .pi{display:flex;flex-direction:column;width:auto;height:auto}
.scene .sv{font-weight:900;font-size:140px;line-height:1;letter-spacing:-3px}
.scene .sl{color:#c9ccd1;font-weight:600;font-size:38px;margin-top:10px}
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
