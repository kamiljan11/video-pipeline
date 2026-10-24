#!/usr/bin/env python3
"""shorts.py plan_long.json [--n 5] [--min 25] [--max 60] [--json out.json] [--grammar path]  — where the shorts are in a long.

Candidates for 9:16 shorts from the long's kept text, ranked, so the choice is repeatable instead of a guess:
  sentences of the long (beats.sentences) -> every run of whole sentences lasting min..max s -> score -> the best runs
  that do not overlap. Score (reasons are printed next to it):
  + opener: the first sentence carries a moment that works as a hook (stat, question, contrast, confession, maxim)
  - opener: it leans on what came before ("Czyli…", "A teraz obiecane…", "Jak mówiłem…"): a short has no before
  + closer: the last sentence lands (maxim, advice, contrast, stat); - it ends open (a question, a comma)
  + body: concrete moments inside (stat, example, story, list), capped; - a length far from the sweet spot (~42 s)
  - a CTA of the long inside (subscribe, link below): it belongs to the long
Moments come from the same cues as beats.py (style/grammar.json), so the editing grammar and the picking agree.
Length = speech time (sum of sentence spans; pauses between sentences are not counted, build_edl tightens them),
so the printed start–end in the long can be longer. No metric yet: the ranking was checked once by hand on the long of
2026-10-22 (4 of the 5 hand-picked shorts overlap a top-6 candidate); weights are a first guess, tune them on new longs.
Output: table + (--json) candidates with "keeps" (word ranges) ready for a plan_short*.json; a person (or a Claude
session) picks and writes the hook text. Reads only; writes only the --json file.
"""
import json
import os
import re
import sys

from beats import classify, load_grammar, load_words, sentences

HOOKS = {"stat": 3.0, "question": 2.5, "contrast": 2.0, "confession": 2.0, "maxim": 2.0, "list": 1.5}
LANDS = {"maxim": 3.0, "advice": 2.0, "contrast": 1.5, "stat": 1.0}
BODY = {"stat": 0.6, "example": 0.5, "story": 0.5, "list": 0.5, "confession": 0.4}
BODY_CAP = 3.0
SWEET, SPREAD = 42.0, 12.0  # s; -1 point per SPREAD seconds away from SWEET
LEANS_BACK = re.compile(r"^\W*(czyli|więc|ale|dlatego|\d+\.(\s|$)|a\b|i\b|no\b|bo\b|także|też|oraz|natomiast|zatem|to\b|tak\b|tyle|jak (mówiłem|wspomniałem)|"
                        r"a teraz|wracając|o tym|tego|ten|ta\b|te\b|tamt|weźmy|na przykład|"
                        r"(po )?(pierwsz|drugi|drugie|trzeci|czwart|piąt|kolejn|następn)\w*\b)", re.IGNORECASE)  # mid-list: no list before it
POINTS_ON = re.compile(r"\b(zaczniemy|zacznijmy|przejdźmy|przejdziemy|za chwilę|zaraz (powiem|pokażę)|w następn\w*|o tym (za|później))\b",
                       re.IGNORECASE)  # the closer announces what comes next in the long
LONG_ONLY = {"cta", "section"}


def span(idx, W):
    return W[idx[-1]][1] - W[idx[0]][0]


def text(idx, W):
    return " ".join(W[i][2].strip() for i in idx)


def runs(idx):
    """Word indices -> [[first, last], ...] contiguous ranges (plan "keeps")."""
    out = []
    for i in idx:
        if out and i == out[-1][1] + 1: out[-1][1] = i
        else: out.append([i, i])
    return out


def score(sents, moments, W):
    """(points, reasons) of one run of sentences."""
    pts, why = 0.0, []
    first, last = sents[0], sents[-1]
    opener = {t for t, _ in moments[0]}
    best = max((HOOKS[t] for t in opener if t in HOOKS), default=0.0)
    if best: pts += best; why.append("hak: " + "/".join(sorted(opener & HOOKS.keys())))
    if LEANS_BACK.match(text(first, W)): pts -= 4; why.append(f"start nawiązuje do wcześniej: „{W[first[0]][2].strip()}…”")
    elif W[first[0]][2].strip()[:1].islower(): pts -= 4; why.append("start w pół zdania")  # whisper split after "20..."
    closer = {t for t, _ in moments[-1]}
    land = max((LANDS[t] for t in closer if t in LANDS), default=0.0)
    if land: pts += land; why.append("puenta: " + "/".join(sorted(closer & LANDS.keys())))
    end = W[last[-1]][2].strip()
    if end.endswith("?"): pts -= 2; why.append("kończy pytaniem")
    elif not re.search(r"[.!…]$", end): pts -= 2; why.append("kończy w pół zdania")
    if POINTS_ON.search(text(last, W)): pts -= 3; why.append("koniec zapowiada dalszą część longa")
    body = min(BODY_CAP, sum(BODY.get(t, 0) for m in moments for t, _ in m))
    if body: pts += body; why.append(f"konkret +{body:.1f}")
    if any(t in LONG_ONLY for m in moments for t, _ in m): pts -= 3; why.append("CTA/przejście longa w środku")
    dur = sum(span(s, W) for s in sents)
    pts -= abs(dur - SWEET) / SPREAD
    return round(pts, 2), why


def candidates(plan, W, grammar, lo=25.0, hi=60.0):
    d = grammar["detect"]
    sents = sentences(plan, W, d["max_sentence"])
    moments = [classify(s, W, grammar, d["min_dist"], d["per_sentence"]) for s in sents]
    out = []
    for a in range(len(sents)):
        dur = 0.0
        for b in range(a, len(sents)):
            dur += span(sents[b], W)
            if dur > hi: break
            if dur >= lo:
                pts, why = score(sents[a:b + 1], moments[a:b + 1], W)
                idx = [i for s in sents[a:b + 1] for i in s]
                out.append({"score": pts, "why": why, "dur": round(dur, 1), "sent": [a, b], "keeps": runs(idx),
                            "start": round(W[idx[0]][0], 2), "end": round(W[idx[-1]][1], 2),
                            "opens": text(sents[a], W)[:90], "closes": text(sents[b], W)[-90:]})
    return out


def pick(cands, n):
    """Best first, never two that share a sentence."""
    taken, out = set(), []
    for c in sorted(cands, key=lambda c: -c["score"]):
        s = set(range(c["sent"][0], c["sent"][1] + 1))
        if not s & taken:
            out.append(c); taken |= s
        if len(out) == n: break
    return sorted(out, key=lambda c: c["start"])


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def opt(argv, k, v):
    """Value after flag k as the type of the default v; a missing or wrong value stops with a named error."""
    if k not in argv: return v
    i = argv.index(k) + 1
    if i >= len(argv) or argv[i].startswith("--"): sys.exit(f"{k}: brak wartości")
    try:
        return type(v)(argv[i])
    except ValueError:
        sys.exit(f"{k}: oczekiwano {type(v).__name__}, jest {argv[i]!r}")


def main(argv):
    if not argv or argv[0].startswith("-"): sys.exit(__doc__)
    with open(argv[0], encoding="utf-8") as f:
        plan = json.load(f)
    W = load_words(plan, os.path.dirname(os.path.abspath(argv[0])))
    lo, hi, n = opt(argv, "--min", 25.0), opt(argv, "--max", 60.0), opt(argv, "--n", 5)
    if not 5 <= lo < hi <= 180: sys.exit(f"--min/--max: 5 <= min < max <= 180 s, got {lo} {hi}")
    if n < 1: sys.exit(f"--n: co najmniej 1, jest {n}")
    out = opt(argv, "--json", "")
    if out and (os.path.basename(out).startswith(("plan_", "edl_", "gfx_specs")) or os.path.exists(out) and not out.endswith(".shorts.json")):
        sys.exit(f"--json {out}: to nie może być plan ani istniejący plik (wynik = nowy plik, np. kandydaci.shorts.json)")
    best = pick(candidates(plan, W, load_grammar(opt(argv, "--grammar", "") or None), lo, hi), n)
    if not best: sys.exit(f"brak kandydatów {lo:.0f}–{hi:.0f} s (za krótki long albo za wąskie okno)")
    for k, c in enumerate(best, 1):
        print(f"#{k}  {mmss(c['start'])}–{mmss(c['end'])}  {c['dur']:.0f} s mowy  wynik {c['score']:+.1f}  ({'; '.join(c['why'])})")
        print(f"    start: {c['opens']}\n    koniec: …{c['closes']}")
    if out:
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(best, f, ensure_ascii=False, indent=1)
        os.replace(tmp, out)


if __name__ == "__main__":
    main(sys.argv[1:])
