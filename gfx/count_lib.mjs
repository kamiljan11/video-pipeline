// "count" card (ADR-0005 pilot): every number in the card text counts up from 0 to its value, the rest of the text stays.
// "95%" -> 0% .. 95%; "2,5 dnia" -> 0,0 .. 2,5; "12 000 zł" keeps its thousands space; "50–70%" counts both numbers.
// a number only when it stands alone: not inside a word or code ("B2B", "Q3", "v2.0"), a time ("15:30"), a dotted number
// ("10.5"); a thousands group needs exactly 3 digits after the space ("Q3 2025" is not "3 202")
const NUM = /(?<![\p{L}\d.:,])(?:\d{1,3}(?:[ \u00a0]\d{3})+(?!\d)|\d+)(?:,\d+)?(?![\d.:]|,\d)/gu;

// text -> ["prefix", {value, dec, group, final}, "rest", ...]; strings and numbers alternate as they stand in the text
export function countParts(text) {
  const s = String(text ?? ''), out = []; let last = 0;
  for (const m of s.matchAll(NUM)) {
    const raw = m[0], [int, frac = ''] = raw.split(',');
    if (/^0\d/.test(int)) continue;  // "007", "00": a code, not an amount -> stays as written (part of the next text piece)
    if (m.index > last) out.push(s.slice(last, m.index));
    out.push({ value: Number(int.replace(/[ \u00a0]/g, '') + (frac ? `.${frac}` : '')), dec: frac.length, group: /[ \u00a0]/.test(int), final: raw });
    last = m.index + raw.length;
  }
  if (last < s.length) out.push(s.slice(last));
  return out;
}

// Polish number as the card shows it (sent into the card page as source by render.mjs: keep it self-contained): decimal comma, the thousands group only when the text had one (non-breaking space)
export function fmtNum(v, dec, group) {
  const [int, frac] = Math.max(0, v).toFixed(dec).split('.');
  const g = group ? int.replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0') : int;
  return frac ? `${g},${frac}` : g;
}

// width the number keeps while it counts (tabular digits = 1ch each, a comma or space is narrower): no box jump, no gap
export const numWidth = final => {
  const d = (final.match(/\d/g) || []).length;
  return +(d + (final.length - d) * 0.35).toFixed(2);
};

// the count starts once the box is in and ends before the fade-out (render.mjs: last 0.35 s); a card too short to count
// (COUNT_DUR 0) shows its numbers at once
export const COUNT_DELAY = 0.35;
export const COUNT_DUR = dur => Math.max(0, Math.min(1.6, dur * 0.4, dur - COUNT_DELAY - 0.45));

export const hasNumber = text => countParts(text).some(p => typeof p !== 'string');
