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
export const sceneSafe = sp => (sp.pip === false ? { x: 120, y: 100, w: W - 240, h: H - 200 } : { x: 110, y: 100, w: PIP_ZONE.x - 140, h: H - 200 });
export const TONES = { acc: 'var(--acc)', ok: '#3ecf8e', bad: '#ff5f57', warn: '#f5b84a', blue: '#6ea8fe', orange: '#ff8a3d', mute: '#8b9096' };
export const KINDS = ['win', 'file', 'term', 'chip', 'node', 'chat', 'you', 'line', 'stamp', 'text', 'bar', 'stat'];
const ANIMS = { pop: 'scpop .5s cubic-bezier(.2,1.4,.4,1)', up: 'scup .55s cubic-bezier(.2,.9,.2,1)', fade: 'scfade .45s ease-out',
  left: 'scleft .55s cubic-bezier(.2,.9,.2,1)', right: 'scright .55s cubic-bezier(.2,.9,.2,1)', drop: 'scdrop .6s cubic-bezier(.2,1.3,.4,1)' };
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
    if (e.k === 'line') {
      const pt = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
      if (!pt(e.from) || !pt(e.to)) bad.push(`${n}: "from" and "to" = [x, y]`);
    } else if (!Number.isFinite(e.x) || !Number.isFinite(e.y)) bad.push(`${n}: "x" and "y" are required`);
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
  if (sp.cam === 'none' && sp.pip !== false) {
    // no camera: the frame is the canvas, so a piece reaching into the PiP corner would sit under the face
    (sp.els || []).forEach((e, i) => {
      if (!e || e.k === 'line' || e.k === 'text' || !Number.isFinite(e.x)) return;
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

function piece(e, esc, icon, dur) {
  const at = num(e.at, 0), anim = ANIMS[e.anim ?? (e.k === 'stamp' ? 'drop' : e.k === 'line' ? 'fade' : 'up')];
  const tn = tone(e.tone);
  let inner = '', cls = e.k, style = `left:${e.x}px;top:${e.y}px;${e.w ? `width:${e.w}px;` : ''}${e.h ? `height:${e.h}px;` : ''}`;
  if (e.k === 'win' || e.k === 'file') {
    const head = e.k === 'win'
      ? `<div class="tb"><i></i><i></i><i></i><span class="ti">${e.icon ? icon(e.icon) : ''}${esc(e.title ?? '')}</span></div>`
      : `<div class="tb fb">${icon(e.icon ?? 'file-text')}<span class="ti">${esc(e.name ?? e.title ?? '')}</span>${e.badge ? `<span class="bdg" style="color:${tone(e.badge.tone)};border-color:${tone(e.badge.tone)};animation:scpop .4s cubic-bezier(.2,1.6,.4,1) ${f2(num(e.badge.at, at + 0.5))}s both">${esc(e.badge.text)}</span>` : ''}</div>`;
    const rows = (e.rows ?? ['~80', '~55', '~70']).map((r, i) => row(r, esc, icon, at + 0.15 + i * num(e.step, 0.12))).join('');
    inner = `${head}<div class="bd">${rows}</div>`;
  } else if (e.k === 'term') {
    const cmdAt = num(e.cmd_at, at + 0.5), typed = e.cmd.length / TYPE_CPS, outAt = num(e.out_at, cmdAt + typed + 0.35);
    const lines = (e.out ?? []).map((l, i) => `<div class="ol${(e.hl ?? []).includes(i) ? ' hot' : ''}" style="animation:scfade .15s ${f2(outAt + i * LINE_STEP)}s both">`
      + `${(e.hl ?? []).includes(i) ? `<span class="rhl" style="background:${tn};animation:scgrow .45s ease-out ${f2(num(e.hl_at, outAt + (e.out.length) * LINE_STEP + 0.4))}s both"></span>` : ''}<span>${esc(l)}</span></div>`).join('');
    inner = `<div class="tb"><i></i><i></i><i></i><span class="ti">${esc(e.title ?? 'terminal')}</span></div>`
      + `<div class="bd"><div class="cl"><span class="ps">${esc(e.prompt ?? '$')}</span> <span class="cmd" style="--n:${e.cmd.length};animation:sctype ${f2(Math.max(typed, 0.1))}s steps(${Math.max(e.cmd.length, 1)}) ${f2(cmdAt)}s both">${esc(e.cmd)}</span></div>${lines}</div>`;
  } else if (e.k === 'chip') {
    inner = `<span class="ci" style="background:${tn}">${icon(e.icon ?? 'zap')}</span><span>${esc(e.text ?? '')}</span>`;
  } else if (e.k === 'node') {
    const s = num(e.size, 200);
    inner = `<div class="nt" style="width:${s}px;height:${s}px;color:${tn};border-color:${tn}">${icon(e.icon ?? 'box')}</div>${e.text ? `<div class="nl">${esc(e.text)}</div>` : ''}${e.sub ? `<div class="ns">${esc(e.sub)}</div>` : ''}`;
  } else if (e.k === 'you') {
    inner = `<div class="nt you">${icon('user')}</div><div class="nl">${esc(e.text ?? 'Ty')}</div>`;
  } else if (e.k === 'chat') {
    inner = (e.msgs ?? []).map((m, i) => {
      const t = num(m.at, at + i * num(e.step, 0.5)), sk = typeof m.t !== 'string' || /^~\d*$/.test(m.t);
      return `<div class="msg ${m.who === 'me' ? 'me' : 'ai'}" style="animation:scup .4s cubic-bezier(.2,.9,.2,1) ${f2(t)}s both">${sk ? `<div class="sk" style="width:${((m.t ?? '~').length > 1 ? +(m.t ?? '~').slice(1) : 70) * 6}px"></div>` : esc(m.t)}</div>`;
    }).join('');
  } else if (e.k === 'stamp') {
    style += `color:${tn};border-color:${tn};--r:${num(e.rot, -6)}deg;`;
    inner = esc(e.text ?? '');
  } else if (e.k === 'text') {
    style += `font-size:${num(e.size, 64)}px;color:${e.tone ? tn : '#f1f2f4'};${e.w ? '' : 'white-space:nowrap;'}`;
    inner = esc(e.t ?? '').replace(/\*([^*]+)\*/g, '<b>$1</b>');
  } else if (e.k === 'bar') {
    const v = Math.min(Math.max(num(e.v, 1), 0), 1);
    inner = `${e.label ? `<div class="bl">${esc(e.label)}</div>` : ''}<div class="tr"><div class="fl" style="width:${(v * 100).toFixed(1)}%;background:${tn};animation:scgrow ${f2(num(e.d, 1))}s cubic-bezier(.2,.8,.2,1) ${f2(at + 0.3)}s both"></div></div>`;
  } else if (e.k === 'stat') {
    inner = `<div class="sv" style="color:${tn}">${esc(e.value ?? '')}</div><div class="sl">${esc(e.label ?? '')}</div>`;
  } else if (e.k === 'line') {
    const [x1, y1] = e.from, [x2, y2] = e.to, len = Math.hypot(x2 - x1, y2 - y1) * 1.3 + 40;
    const c = num(e.curve, 0.35), mx = x1 + (x2 - x1) * c, d = `M${x1} ${y1} C${mx} ${y1},${x2 - (x2 - x1) * c} ${y2},${x2} ${y2}`;
    const head = e.arrow === false ? '' : `<circle cx="${x2}" cy="${y2}" r="9" fill="${tn}" style="animation:scfade .2s ${f2(at + num(e.d, 0.7))}s both"/>`;
    return `<svg class="ln"${e.id ? ` data-id="${esc(e.id)}"` : ''} data-bb="${Math.min(x1, x2)} ${Math.min(y1, y2)} ${Math.abs(x2 - x1)} ${Math.abs(y2 - y1)}" viewBox="0 0 ${W} ${H}" style="overflow:visible"><path d="${d}" stroke="${tn}" style="stroke-dasharray:${len.toFixed(0)};stroke-dashoffset:${len.toFixed(0)};animation:scdraw ${f2(num(e.d, 0.7))}s cubic-bezier(.4,0,.2,1) ${f2(at)}s forwards"/>${head}</svg>`;
  }
  const outs = [`${anim} ${f2(at)}s both`];
  if (e.dim !== undefined) outs.push(`scdim .4s ease-out ${f2(e.dim)}s forwards`);
  if (e.gone !== undefined) outs.push(`scgone .35s ease-in ${f2(e.gone)}s forwards`);
  return `<div class="p ${cls}"${e.id ? ` data-id="${esc(e.id)}"` : ''} style="${style}"><div class="pi" style="animation:${outs.join(',')}">${inner}</div></div>`;
}

export function scene(sp, esc, icon) {
  const bad = checkScene(sp);
  if (bad.length) throw new Error(`"${sp.id}": scene: ${bad.join('; ')}`);
  const safeIcon = n => { try { return icon(n); } catch { throw new Error(`"${sp.id}": no icon "${n}" in lucide-static`); } };
  const cam = sp.cam === 'none' ? null : sp.cam ?? [{ t: 0, on: '*' }];
  const world = sp.els.map(e => piece(e, esc, safeIcon, sp.dur)).join('');
  return `${SCENE_CSS}<div class="scene"><div class="world"${cam ? ` data-cam="${esc(JSON.stringify(cam)).replace(/"/g, '&quot;')}" data-dur="${sp.dur}"` : ''}>${world}</div></div>`;
}

// in the page, before the first frame (render.mjs): measures the pieces as laid out (their final place, not mid-animation),
// turns every "on" stop into x, y, z that put those pieces in the middle of the free area, and starts the camera animation.
// Self-contained: its source is evaluated in the page with camKeyframes' source as the second argument.
export function sceneFit(safe, kfSrc) {
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
  return stops;
}

// the look: near-black canvas with a faint dot grid, flat dark cards with thin borders, skeleton lines for text that does
// not need reading, colour only where the eye should go (accent, ok, bad); Montserrat for UI, a monospace for the terminal
const SCENE_CSS = `<style>
.scene{position:absolute;inset:0;overflow:hidden;background:#0c0d0f;background-image:radial-gradient(rgba(255,255,255,.055) 2px,transparent 2.5px);background-size:56px 56px;animation:scfade .35s both}
.scene .world{position:absolute;left:0;top:0;width:${W}px;height:${H}px;transform-origin:0 0}
.scene .p{position:absolute}
.scene .pi{width:100%;height:100%}
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
</style>`;
