// Motion tokens (Skool CCC M13, P1 task 10; visual-upgrade plan step 4): one place for how long a move takes, which curve
// it rides and how far apart pieces of a group come in. Durations are frames at 30 fps, so a move lands on a frame.
// Numbers: the mograph motion-system reference (mechanics only), see Knowledge/Skool CCC "Skills - grafika, efekty, dzwiek" M13.
// Rules: no single move longer than F.slow; an exit takes half its entrance; entrances ride land or pop, never a curve
// that eases both ways (ease-in-out = the piece hesitates before it arrives); a stagger step is at most STAGGER_MAX frames.
// scene_lib.mjs uses these for a card with "motion": "tokens"; motionProblems() is the lint (scene_check.mjs runs it).

export const FPS = 30;
export const F = { tick: 2, micro: 4, fast: 6, base: 12, slow: 24, hold: 12, beat: 30 };
export const EASE = {
  land: 'cubic-bezier(.16,1,.3,1)',    // arrive and settle (entrances, draws)
  pop: 'cubic-bezier(.34,1.56,.64,1)', // arrive with about 8 % overshoot (marks, stamps, badges)
  shift: 'cubic-bezier(.83,0,.17,1)',  // reflow of things already on screen only, never an entrance
  leave: 'cubic-bezier(.7,0,.84,0)',   // exits
};
export const STAGGER = { glyph: 1, word: 3, grid: 2, step: 5, object: 8 };
export const STAGGER_MAX = 12;
export const sec = f => +(f / FPS).toFixed(3);

// keyframes that bring a piece (or a part of it) on screen; the rest (pulse, dim, gone, camera, cursor path) are not entrances
export const ENTRANCES = new Set(['scpop', 'scup', 'scfade', 'scleft', 'scright', 'scdrop', 'scblur', 'scboard', 'scgrow', 'scdraw',
  'scword', 'sctgk', 'sctgbg', 'scfill', 'scpart', 'scburst', 'scrip']);

// a timing function that eases in and out: the CSS keyword or a cubic-bezier symmetric about its middle (x1 = 1 - x2, y1 = 1 - y2)
export function easesBothWays(tf) {
  if (/^ease-in-out$/.test(tf)) return true;
  const m = /^cubic-bezier\(([^)]+)\)$/.exec(tf);
  if (!m) return false;
  const [x1, y1, x2, y2] = m[1].split(',').map(Number);
  return x1 > 0.2 && Math.abs(x1 + x2 - 1) < 0.06 && Math.abs(y1 + y2 - 1) < 0.06;
}

// html: a drawn card. Every entrance in an inline "animation:" list that eases both ways is named once per curve.
export function motionProblems(html) {
  const bad = new Map();
  for (const [, list] of html.matchAll(/animation:([^";]+)/g)) {
    for (const one of list.split(/,(?![^(]*\))/)) {
      const [name, ...rest] = one.trim().split(/\s+(?![^(]*\))/);
      const tf = rest.find(t => /^(ease|linear|cubic-bezier|steps)/.test(t));
      if (ENTRANCES.has(name) && tf && easesBothWays(tf)) bad.set(`${name} ${tf}`, (bad.get(`${name} ${tf}`) ?? 0) + 1);
    }
  }
  return [...bad].map(([k, n]) => `entrance eases both ways: ${k} (${n}x); use land or pop`);
}

// stagger steps of a scene card in frames, from the keys that space a group out ("step" of win/file rows and chat messages)
export function staggerProblems(sp) {
  return (sp.els ?? []).filter(e => typeof e?.step === 'number' && Math.round(e.step * FPS) > STAGGER_MAX)
    .map(e => `${sp.id}: ${e.id ?? e.k} "step" ${e.step}s = ${Math.round(e.step * FPS)} frames (stagger max ${STAGGER_MAX}); give the items their own "at" when they follow speech`);
}
