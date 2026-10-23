// "maxim" card: a key sentence typed on screen letter by letter while it is said; words in *stars* get the accent and a
// marker stroke once they are typed. Timing is per word: spec "at" = start of each word in seconds from the card's start
// (from the transcript); without it the words come at an even pace per letter.
export const TYPE_START = 0.25, CHAR_MAX = 0.045, CHAR_EVEN = 0.05, MARK_DUR = 0.3, CARET_HOLD = 0.7, LAST_SHOWN = 0.3;

// "Pierwszy projekt ma *zbudować zaufanie*" -> [{w: "Pierwszy", hl: false}, ..., {w: "zbudować", hl: true}, {w: "zaufanie", hl: true}]
// a star on its own ("a * b *") switches the highlight too, so a stray space never highlights the rest of the sentence
export function maximWords(text) {
  const out = []; let hl = false;
  for (const tok of String(text ?? '').split(/\s+/).filter(Boolean)) {
    if (/^\*+$/.test(tok)) { hl = !hl; continue; }
    const open = tok.startsWith('*'), close = tok.endsWith('*');
    if (open) hl = true;
    out.push({ w: tok.replace(/\*/g, ''), hl });
    if (close) hl = false;
  }
  return out;
}

// start time of every word: the spec's own (never going back in time, the last one shown at least LAST_SHOWN s) or an
// even pace per letter that leaves the reader at least 40 % of the card to read the finished sentence
export function wordTimes(words, dur, at) {
  const n = words.length, latest = Math.max(0, dur - LAST_SHOWN);
  if (Array.isArray(at) && at.length === n && at.every(x => typeof x === 'number' && isFinite(x))) {
    let prev = 0;
    return at.map(x => (prev = Math.max(prev, Math.min(Math.max(0, x), latest))));
  }
  const lens = words.map(({ w }) => w.length + 1), total = lens.reduce((a, b) => a + b, 0) || 1;
  const span = Math.max(0, Math.min(dur * 0.6 - TYPE_START, total * CHAR_EVEN));
  let cum = 0;
  return lens.map(l => { const t = TYPE_START + span * cum / total; cum += l; return t; });
}

// per character: when it appears; each word types out over at most CHAR_MAX s per letter and never past the next word's start
export function charTimes(words, times, dur) {
  return words.map(({ w }, i) => {
    const next = i + 1 < times.length ? times[i + 1] : dur;
    const step = Math.min(CHAR_MAX, Math.max(0, next - times[i]) / Math.max(1, w.length));
    return [...w].map((_, j) => times[i] + j * step);
  });
}

// runs inside the card page (render.mjs sends its source): shows the letters, the caret and the marker strokes for time t.
// Self-contained on purpose (no imports, no outer names).
export function maximSeek(hold, mark) {
  let letters = null, marks = null, caret = null;
  return t => {
    if (!letters) {
      letters = [...document.querySelectorAll('.maxim i')].map(el => ({ el, t: +el.dataset.t }));
      marks = [...document.querySelectorAll('.maxim .mk')].map(el => ({ el, t: +el.dataset.t }));
      caret = document.querySelector('.maxim .caret');
    }
    let last = null, lastT = 0;
    for (const l of letters) {
      const on = t >= l.t; l.el.style.visibility = on ? 'visible' : 'hidden';
      if (on && l.t >= lastT) { last = l.el; lastT = l.t; }
    }
    for (const m of marks) {
      const p = Math.min(1, Math.max(0, (t - m.t) / mark)); m.el.style.transform = `scaleX(${1 - (1 - p) ** 3})`;
    }
    if (last) last.after(caret);
    caret.style.opacity = !last || t > lastT + hold ? 0 : t - lastT < 0.15 || Math.floor(t * 3) % 2 === 0 ? 1 : 0;
  };
}
