// Card writers of the plan2 research items (creator-study/round2/ledger.jsonl), pure functions so tests read their HTML
// without a browser; render.mjs draws them. All are opt-in: a spec without the new fields draws exactly as before.
//   L8  "list" + "upto" / "dim_done": one stacked list whose items come in on their spoken words (build_edl "item_words")
//   L9  "chap" + "chap_style": "roadmap" (the opening roadmap drawing, done / current / next) or "part_tag" (corner tag)
//   L12 "lower" + "define": true (a term and its definition, >= DEFINE.min_dur s)
//   L21 "note" (a caveat or "link w opisie": <= 3 lines / 14 words in the bottom corner away from the face circle)
// Their CSS comes with the card (a <style> before it), not in template.html: the template's bytes are part of every meme
// card's key (render.mjs MEME_CODE), so a new rule there would re-render and un-accept every meme.
// The 16:9 face circle (assemble.py PiP) sits bottom right: a note takes the other bottom corner (ledger wf2 cole-medin:3),
// a part tag the top left (codie-sanchez:2); all four are 16:9 only (Long items; 9:16 has captions and app buttons there).
import { esc, icon } from './html_lib.mjs';

// min_dur = gfx_types.py NOTE / DEFINE (build_edl.py adds the reading time there); here the card alone is checked
export const NOTE = { max_words: 14, max_lines: 3, line_chars: 38, min_dur: 4 };
export const DEFINE = { max_words: 20, max_lines: 3, line_chars: 40, term_words: 4, min_dur: 6 };
export const ROADMAP = { min_parts: 2, max_parts: 10, title_chars: 40, one_column: 5 };  // > one_column parts: two columns (1080 px fits 5 rows)
export const CHAP_STYLES = ['roadmap', 'part_tag'];

export const words = s => String(s ?? '').trim().split(/\s+/).filter(Boolean);
// lines a text takes in a box of `per` characters: its own lines ("\n"), each wrapped at `per` characters (a word never split)
export function lineCount(text, per) {
  return String(text ?? '').split('\n').reduce((n, line) => {
    let lines = 1, len = 0;
    for (const w of words(line)) {
      const l = [...w].length;
      if (len && len + 1 + l > per) { lines++; len = l; } else len += (len ? 1 : 0) + l;
    }
    return n + lines;
  }, 0);
}

const fail = (sp, why) => { throw new Error(`"${sp.id}": ${why}`); };
const isInt = v => Number.isInteger(v);
const isNum = v => typeof v === 'number' && Number.isFinite(v);

// a spec that uses one of these features: its key holds this file's hash too (render.mjs), like "motion": "tokens" cards
export const usesCardsLib = sp => sp.type === 'note' || (sp.type === 'lower' && sp.define !== undefined)
  || (sp.type === 'chap' && sp.chap_style !== undefined) || (sp.type === 'list' && (sp.upto !== undefined || sp.dim_done !== undefined));

// every field of a new-feature card checked before any page opens; a legacy card passes untouched
export function checkCard(sp) {
  if (!usesCardsLib(sp)) return;
  if (sp.canvas === 'v') fail(sp, `this "${sp.type}" card is 16:9 only (a Long feature): no canvas "v"`);
  if (!(isNum(sp.dur) && sp.dur > 0)) fail(sp, `"dur" = seconds > 0, got ${JSON.stringify(sp.dur)}`);
  if (sp.type === 'list') checkList(sp);
  else if (sp.type === 'chap') checkChap(sp);
  else if (sp.type === 'lower') checkDefine(sp);
  else checkNote(sp);
}

// ---- L8 list: "upto" k shows items 1..k (the earlier ones already there, the k-th comes in); "dim_done" greys an item
// once the next one is in (with "upto": the earlier ones, so the newest stands out). "delays" are seconds from the card's
// start per item; with "upto" an earlier item has none (null), so music/make_beds.py pops only for the one coming in.
function checkList(sp) {
  const items = sp.items;
  if (!(Array.isArray(items) && items.length && items.every(x => typeof x === 'string' && x.trim()))) fail(sp, '"items" = a list of texts');
  if (sp.upto !== undefined && !(isInt(sp.upto) && sp.upto >= 1 && sp.upto <= items.length)) fail(sp, `"upto" = a whole number 1..${items.length} (items shown), got ${JSON.stringify(sp.upto)}`);
  if (sp.dim_done !== undefined && typeof sp.dim_done !== 'boolean') fail(sp, `"dim_done" = true or false, got ${JSON.stringify(sp.dim_done)}`);
  const d = sp.delays ?? [], n = sp.upto ?? items.length;
  if (!Array.isArray(d) || d.length > n) fail(sp, `"delays" = at most ${n} values (one per item shown), got ${JSON.stringify(sp.delays)}`);
  const first = sp.upto === undefined ? 0 : n - 1;
  d.forEach((v, i) => {
    if (i < first && v !== null) fail(sp, `"delays"[${i}]: item ${i + 1} is already on the card ("upto" ${n}), so null, got ${JSON.stringify(v)}`);
    if (i >= first && v !== null && !(isNum(v) && v >= 0 && v < sp.dur)) fail(sp, `"delays"[${i}] = seconds 0..dur, got ${JSON.stringify(v)}`);
  });
  // in the order they come in, a missing delay counted as the one listHtml draws (i s), so [0, 5, null] is refused too
  const timed = Array.from({ length: n - first }, (_, j) => d[first + j] ?? listDefault(sp, first + j));
  if (timed.some((v, i) => i && v < timed[i - 1])) fail(sp, `"delays" must not go back in time (a missing one = its index in s): ${JSON.stringify(sp.delays)}`);
  if (timed.some(v => v >= sp.dur)) fail(sp, `an item comes in after the card ends (dur ${sp.dur}): ${JSON.stringify(sp.delays)}`);
}
// when an item without a delay comes in: the old default (i s) in a stack, 0.3 s for the newest of an "upto" card
const listDefault = (sp, i) => (sp.upto === undefined ? i : 0.3);

export function listHtml(sp) {
  // legacy list: the exact markup of before (its .mov keys and stills stay valid)
  if (sp.upto === undefined && sp.dim_done === undefined) return `<div class="list"><div class="h">${esc(sp.text)}</div>${sp.items.map((x,i)=>`<div class="i" style="animation:slide .45s ${(sp.delays||[])[i]??i}s both">${(sp.icons||[])[i]?`<span class="li">${icon(sp.icons[i])}</span>`:`<b>${i+1}</b>`}<span>${esc(x)}</span></div>`).join('')}</div>`;
  checkList(sp);
  const n = sp.upto ?? sp.items.length, stacked = sp.upto === undefined, d = sp.delays ?? [];
  const at = i => d[i] ?? listDefault(sp, i);  // = build_edl.py list_timing
  const rows = sp.items.slice(0, n).map((x, i) => {
    const old = !stacked && i < n - 1, done = sp.dim_done && old;
    // an earlier item of an "upto" card stands still ("animation:none" also beats template.html's nth-child delays)
    const anim = old ? 'none' : [`slide .45s ${at(i)}s both`, ...(sp.dim_done && stacked && i < n - 1 ? [`ldim .3s ${at(i + 1)}s forwards`] : [])].join(',');
    return `<div class="i${done ? ' done' : ''}" style="animation:${anim}">${(sp.icons || [])[i] ? `<span class="li">${icon(sp.icons[i])}</span>` : `<b>${i + 1}</b>`}<span>${esc(x)}</span></div>`;
  }).join('');
  return `<style>.list .i.done{opacity:.42}@keyframes ldim{to{opacity:.42}}</style><div class="list"><div class="h">${esc(sp.text)}</div>${rows}</div>`;
}

// ---- L9 chapter card styles. "parts" = every part title (the same list on each card of the film: one drawing, build_edl
// checks it), "current" = the part that starts here (1..N; 0 on the opening roadmap = nothing done yet)
function checkChap(sp) {
  if (!CHAP_STYLES.includes(sp.chap_style)) fail(sp, `"chap_style" = ${CHAP_STYLES.map(s => `"${s}"`).join(' or ')}, got ${JSON.stringify(sp.chap_style)}`);
  const p = sp.parts, { min_parts: lo, max_parts: hi, title_chars: tc } = ROADMAP;
  if (!(Array.isArray(p) && p.length >= lo && p.length <= hi && p.every(t => typeof t === 'string' && t.trim() && [...t].length <= tc)))
    fail(sp, `"parts" = ${lo}..${hi} part titles of at most ${tc} characters, got ${JSON.stringify(p)}`);
  const min = sp.chap_style === 'roadmap' ? 0 : 1;
  if (!(isInt(sp.current) && sp.current >= min && sp.current <= p.length)) fail(sp, `"current" = the part that starts here, ${min}..${p.length}, got ${JSON.stringify(sp.current)}`);
  if (sp.text !== undefined && !(typeof sp.text === 'string' && [...sp.text].length <= tc)) fail(sp, `"text" = at most ${tc} characters, got ${JSON.stringify(sp.text)}`);
}

const ROADMAP_CSS = '<style>.chap.roadmap .no{margin-bottom:10px}.chap.roadmap .h{font-weight:900;font-size:84px;color:#fff;margin-bottom:46px;animation:fade .4s .1s both}'
  + '.rm{display:flex;flex-direction:column;gap:22px;min-width:1300px}'
  + '.rm .r{display:flex;align-items:center;gap:36px;padding:18px 34px;border-radius:22px;font-weight:700;font-size:62px;color:var(--soft-2)}'
  + '.rm .r b{display:flex;align-items:center;justify-content:center;width:92px;height:92px;border-radius:50%;flex:none;font-weight:900;font-size:50px;border:5px solid var(--acc);color:var(--acc)}'
  + '.rm .r.done{color:var(--mute-2)}.rm .r.done b{background:var(--acc-dim);border-color:var(--acc-dim)}.rm .r.done b svg{width:54px;height:54px;stroke:var(--ink);stroke-width:3}'
  + '.rm .r.next{color:var(--mute)}.rm .r.next b{border-color:var(--line);color:var(--mute)}'
  + '.rm .r.cur{background:rgba(var(--acc-rgb),.16);color:#fff;font-weight:900}.rm .r.cur b{background:var(--acc);color:var(--ink)}'
  + '.rm.two{display:grid;grid-auto-flow:column;grid-template-rows:repeat(var(--rows),auto);column-gap:70px;row-gap:18px;min-width:1720px}'
  + '.rm.two .r{font-size:50px;padding:14px 28px;gap:28px}.rm.two .r b{width:76px;height:76px;font-size:42px}'
  + '@keyframes rmcur{from{background:transparent;transform:scale(1)}60%{transform:scale(1.04)}to{background:rgba(var(--acc-rgb),.16);transform:scale(1)}}</style>';
const TAG_CSS = '<style>.ptag{position:absolute;left:70px;top:60px;display:flex;align-items:center;gap:22px;padding:16px 30px 16px 16px;border-radius:999px;'
  + 'background:rgba(var(--panel-rgb),.84);font-weight:800;font-size:44px;color:#fff;animation:slide .5s cubic-bezier(.16,1,.3,1) both}'
  + '.ptag b{padding:6px 20px;border-radius:999px;background:var(--acc);color:var(--ink);font-weight:900;font-size:38px}</style>';

export function chapHtml(sp) {
  if (sp.chap_style === undefined) return `<div class="chap"><div class="no">${esc(sp.sub)}</div><div class="t">${esc(sp.text)}</div></div>`;  // legacy
  checkChap(sp);
  const n = sp.parts.length, k = sp.current;
  if (sp.chap_style === 'part_tag') return `${TAG_CSS}<div class="ptag"><b>${k}/${n}</b><span>${esc(sp.text ?? sp.parts[k - 1])}</span></div>`;
  // roadmap: every row in place from the first frame (the same drawing on every card); the opening (current 0) brings the
  // rows in one by one, a part card lifts only its current row
  const rows = sp.parts.map((t, i) => {
    const state = i + 1 < k ? 'done' : i + 1 === k ? 'cur' : 'next';
    const anim = k === 0 ? `slide .45s ${(0.25 + 0.2 * i).toFixed(2)}s both` : state === 'cur' ? 'rmcur .5s .3s cubic-bezier(.16,1,.3,1) both' : 'none';
    return `<div class="r ${state}" style="animation:${anim}"><b>${state === 'done' ? icon('check') : i + 1}</b><span>${esc(t)}</span></div>`;
  }).join('');
  const label = sp.sub ?? (k ? `${k}/${n}` : '');
  const two = n > ROADMAP.one_column;  // 6-10 parts: two columns, first half on the left (rows top to bottom)
  const rm = two ? `<div class="rm two" style="--rows:${Math.ceil(n / 2)}">` : '<div class="rm">';
  return `${ROADMAP_CSS}<div class="chap roadmap">${label ? `<div class="no">${esc(label)}</div>` : ''}${sp.text ? `<div class="h">${esc(sp.text)}</div>` : ''}${rm}${rows}</div></div>`;
}

// ---- L12 "define": the lower third with the term (accent) on top and its definition under it
function checkDefine(sp) {
  if (sp.define !== true) fail(sp, `"define" = true (a term and its definition), got ${JSON.stringify(sp.define)}`);
  const term = words(sp.text), def = words(sp.sub);
  if (!term.length || term.length > DEFINE.term_words) fail(sp, `"text" = the term, 1..${DEFINE.term_words} words, got ${JSON.stringify(sp.text)}`);
  if (!def.length || def.length > DEFINE.max_words) fail(sp, `"sub" = the definition, 1..${DEFINE.max_words} words, got ${def.length}`);
  if (lineCount(sp.sub, DEFINE.line_chars) > DEFINE.max_lines) fail(sp, `the definition takes more than ${DEFINE.max_lines} lines (${DEFINE.line_chars} characters a line): shorten it`);
  if (sp.dur < DEFINE.min_dur) fail(sp, `a definition stays >= ${DEFINE.min_dur} s (ledger plan2:L12), got ${sp.dur}`);
}

const DEFINE_CSS = '<style>.lower.define .box{max-width:1100px}.lower.define .n{color:var(--acc)}'
  + '.lower.define .r{font-size:42px;line-height:1.28;margin-top:12px;animation:fade .45s .35s both}</style>';

export function lowerHtml(sp) {
  if (sp.define === undefined) return `<div class="lower"><div class="acc"></div><div class="box"><div class="n">${esc(sp.text)}</div><div class="r">${esc(sp.sub)}</div></div></div>`;  // legacy
  checkDefine(sp);
  return `${DEFINE_CSS}<div class="lower define"><div class="acc"></div><div class="box"><div class="n">${esc(sp.text)}</div><div class="r">${esc(sp.sub)}</div></div></div>`;
}

// ---- L21 "note": a short caveat or pointer, bottom left (the face circle is bottom right), no sound of its own
function checkNote(sp) {
  const n = words(sp.text).length;
  if (!n || n > NOTE.max_words) fail(sp, `a note is 1..${NOTE.max_words} words, got ${n}`);
  if (lineCount(sp.text, NOTE.line_chars) > NOTE.max_lines) fail(sp, `a note takes at most ${NOTE.max_lines} lines (${NOTE.line_chars} characters a line): shorten it`);
  if (sp.dur < NOTE.min_dur) fail(sp, `a note stays >= ${NOTE.min_dur} s (ledger plan2:L21), got ${sp.dur}`);
  if (sp.icon !== undefined && !(typeof sp.icon === 'string' && /^[a-z0-9-]+$/.test(sp.icon))) fail(sp, `"icon" = a lucide name, got ${JSON.stringify(sp.icon)}`);
}

const NOTE_CSS = '<style>.note{position:absolute;left:110px;bottom:120px;max-width:900px;display:flex;gap:24px;align-items:flex-start;padding:24px 36px;'
  + 'border-radius:18px;background:rgba(var(--panel-rgb),.86);border-left:10px solid var(--acc);animation:slide .5s cubic-bezier(.16,1,.3,1) both}'
  + '.note .ni svg{width:46px;height:46px;stroke:var(--acc);stroke-width:2.4;margin-top:4px}'
  + '.note .t{font-weight:600;font-size:36px;line-height:1.3;color:var(--soft-2)}</style>';

export function noteHtml(sp) {
  checkNote(sp);
  const text = String(sp.text).split('\n').map(l => esc(l.trim())).join('<br>');
  return `${NOTE_CSS}<div class="note">${sp.icon ? `<span class="ni">${icon(sp.icon)}</span>` : ''}<div class="t">${text}</div></div>`;
}
