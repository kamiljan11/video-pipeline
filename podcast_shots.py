"""podcast_shots.py: who is on screen when, in a two-person podcast shot with one wide camera (pure logic, no video).

Input: the words [(from, to, text)] of the recording and one speaker per word: "L" (person on the left of the frame),
"R" (right) or "?" (not sure: podcast_faces.py could not tell, or nobody's lips moved).
- turns(): who has the floor, [[t0, t1, spk]]. A short run of the other person inside one speaker's talk (shorter than
  backchannel_s: "mhm", "yeah", a laugh) does not take the floor: research/podcast R3, never cut on every acknowledgement.
- long_shots(): 16:9 shots [[t0, t1, shot]], shot "wide" | "L" | "R". Open on the wide two-shot, then the active speaker;
  a turn shorter than hold_s keeps the shot it found (no switch for a one-liner); a single shot longer than single_max_s
  gets a wide cutaway of cutaway_s in the middle (one static angle for minutes looks dead, research R1).
- short_shots(): 9:16 shots, shot "L" | "R" | "stack" (speaker A over speaker B). Stack only where the floor changes
  at least stack_switches times within stack_window_s (fast back and forth); a long monologue is never stacked.
Times are recording (source) seconds, the same clock as the words. The numbers live in style/podcast.json.
"""
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

CFG = Path(__file__).resolve().parent / "style" / "podcast.json"
SIDES = ("L", "R")


def load_cfg(over=None, path: Path = CFG) -> dict:
    """style/podcast.json, then the plan's "podcast" object on top (only keys the file has, positive numbers)"""
    cfg = {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}
    for k, v in (over or {}).items():
        if k in ("speakers",): continue  # names of the two people: not a rule
        if k not in cfg: sys.exit(f"podcast: unknown key {k!r} (known: {sorted(cfg)})")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0: sys.exit(f"podcast: {k} must be a number > 0, got {v!r}")
        cfg[k] = v
    return cfg


def fill_unknown(spk: list) -> "list | None":
    """"?" words take the speaker of the word before (else the next known one): a word nobody can place stays with the
    person who was talking. All "?" = None (no speaker found at all)."""
    if not any(s in SIDES for s in spk): return None
    out, last = [], None
    for s in spk:
        last = s if s in SIDES else last
        out.append(last)
    first = next(s for s in out if s)
    return [s or first for s in out]


def _runs(words, spk):
    runs = []
    for (a, b, _), s in zip(words, spk):
        if runs and runs[-1][2] == s: runs[-1][1] = b
        else: runs.append([a, b, s])
    return runs


def turns(words, spk, cfg) -> list:
    """[[t0, t1, spk]], contiguous (a turn ends where the next begins), backchannels folded into the talk around them"""
    if len(words) != len(spk): sys.exit(f"podcast: {len(words)} words but {len(spk)} speaker labels")
    spk = fill_unknown(list(spk))
    if not words or spk is None: return []
    runs = _runs(words, spk)
    changed = True
    while changed:
        changed = False
        for i in range(1, len(runs) - 1):
            a, b, s = runs[i]
            if b - a < cfg["backchannel_s"] and runs[i - 1][2] == runs[i + 1][2] != s:
                runs[i - 1][1] = runs[i + 1][1]; del runs[i:i + 2]; changed = True; break
    for i in range(len(runs) - 1): runs[i][1] = runs[i + 1][0]
    return [[round(a, 3), round(b, 3), s] for a, b, s in runs]


def merge(shots) -> list:
    out = []
    for a, b, s in shots:
        if b <= a: continue
        if out and out[-1][2] == s and abs(out[-1][1] - a) < 1e-6: out[-1][1] = b
        else: out.append([a, b, s])
    return out


def absorb(shots, min_s) -> list:
    """a piece shorter than min_s joins the shot before it (the first one: the shot after it)"""
    shots = merge(shots)
    i = 0
    while len(shots) > 1 and i < len(shots):
        a, b, _ = shots[i]
        if b - a < min_s:
            if i == 0: shots[1][0] = a
            else: shots[i - 1][1] = b
            del shots[i]; shots = merge(shots); i = 0; continue
        i += 1
    return shots


def _held(tn, cfg):
    """the active speaker per turn, but a turn shorter than hold_s keeps the shot before it"""
    out = []
    for a, b, s in tn:
        out.append([a, b, out[-1][2] if out and b - a < cfg["hold_s"] else s])
    return merge(out)


def long_shots(tn, cfg) -> list:
    if not tn: return []
    shots = _held(tn, cfg)
    t0 = tn[0][0]; w_end = t0 + cfg["open_wide_s"]
    opened = [[t0, min(w_end, tn[-1][1]), "wide"]]
    for a, b, s in shots:
        if b > w_end: opened.append([max(a, w_end), b, s])
    out = []
    for a, b, s in merge(opened):
        n = math.ceil((b - a) / cfg["single_max_s"]) if s in SIDES else 1
        if n <= 1: out.append([a, b, s]); continue
        cut, c = a, cfg["cutaway_s"]
        for k in range(1, n):
            m = a + k * (b - a) / n
            out += [[cut, m - c / 2, s], [m - c / 2, m + c / 2, "wide"]]; cut = m + c / 2
        out.append([cut, b, s])
    return [[round(a, 3), round(b, 3), s] for a, b, s in absorb(out, cfg["min_piece_s"])]


def short_shots(tn, cfg) -> list:
    if not tn: return []
    switches = [tn[i][0] for i in range(1, len(tn)) if tn[i][2] != tn[i - 1][2]]
    k, win = int(cfg["stack_switches"]), cfg["stack_window_s"]
    stacks = []
    for j in range(len(switches) - k + 1):
        if switches[j + k - 1] - switches[j] <= win:
            last = switches[j + k - 1]
            end_turn = next(b for a, b, _ in tn if a <= last < b + 1e-9)
            a, b = switches[j], min(end_turn, last + cfg["hold_s"])
            if stacks and a <= stacks[-1][1]: stacks[-1][1] = max(stacks[-1][1], b)
            else: stacks.append([a, b])
    base = [[a, b, s] for a, b, s in tn]  # no hold rule on 9:16: the face that talks is the only face on screen
    out = []
    for a, b, s in base:
        cuts = [a, b] + [x for st in stacks for x in st if a < x < b]
        for x0, x1 in pairwise(sorted(cuts)):
            mid = (x0 + x1) / 2
            out.append([x0, x1, "stack" if any(p <= mid < q for p, q in stacks) else s])
    return [[round(a, 3), round(b, 3), s] for a, b, s in absorb(out, cfg["min_piece_s"])]


def shot_at(shots, t):
    for a, b, s in shots:
        if a <= t < b: return s
    return shots[-1][2] if shots and t >= shots[-1][1] else (shots[0][2] if shots else None)
