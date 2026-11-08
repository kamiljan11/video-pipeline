"""framing.py: "second camera from one" (research ledger L10) for build_edl.py; the ONE place that decides the zoom level
of every EDL piece when a plan asks for "zoom_every_s" or "part_framing".

Without either key build_edl.py keeps its old rule (the level toggles only on a real jump cut) and never calls assign().
With them the level alternates between a wide framing (plan "zooms"[0], 1.0) and a tight one ("zooms"[1], 1.15):
  - zoom_every_s N: no framing lasts longer than N s of film; an existing cut is used when one falls in the second half of
    the run, else the piece is split at a word gap in the window, a sentence end first, then a comma, then the latest gap
    (a cut inside a word would be heard). The split pieces are contiguous: same sound, a new framing.
  - part_framing: the first word of every story part (story.json "parts"[].start_word, or a list of word indices) opens
    a new framing, A (wide) on even parts and B (PART_B, ledger L10: 1.2-1.25) on odd ones.
  - never more than 2 tight framings in a row (L10), a third becomes wide.
face_track.py clamps every level to what keeps the head in frame afterwards (ADR-0012): the head-safe rule wins.
Every piece that starts a framing made here carries "framing" ("every_s" or "part", plus "part": its number)."""
from __future__ import annotations

import json
import re
from collections import deque
from itertools import pairwise
from pathlib import Path

import timeline

PART_B = 1.2  # L10: the tight base framing of an odd story part (1.2-1.25 in the study)
JUMP = 0.8  # s of removed source that counts as a jump cut (build_edl.py's old rule)
MIN_PIECE = 2.0  # s: a framing split never leaves a piece shorter than this (a flash reads as a double cut)
PART_EDGE = 0.5  # s: a part start this close to a piece edge moves the framing to that edge instead of a split
SENTENCE = re.compile(r"[.?!…]$")
CLAUSE = re.compile(r"[,;:–-]$")


class FramingError(ValueError):
    pass


def options(plan: dict, plan_dir: Path, n_words: int) -> dict | None:
    """{"every": seconds or None, "parts": [word index, ...] or None} from the plan; None = neither key (old rule)"""
    every = plan.get("zoom_every_s")
    if every is not None and (isinstance(every, bool) or not isinstance(every, (int, float)) or not 5 <= every <= 120):
        raise FramingError(f"zoom_every_s: seconds 5..120 (L10: a framing change at least this often), got {every!r}")
    pf = plan.get("part_framing", False)
    parts = None
    if pf is True:
        p = plan_dir / "story.json"
        if not p.exists():
            raise FramingError(f"part_framing: true reads the story parts from {p}, which does not exist (or give a list of word indices)")
        try:
            story = json.loads(p.read_text())
        except ValueError as e:
            raise FramingError(f"part_framing: {p}: {e}") from e
        raw = story.get("parts") if isinstance(story, dict) else None
        if not isinstance(raw, list):
            raise FramingError(f'part_framing: {p}: {{"parts": [{{"start_word": i}}, ...]}}')
        parts = [pt.get("start_word") if isinstance(pt, dict) else None for pt in raw]
    elif isinstance(pf, list):
        parts = pf
    elif pf is not False:
        raise FramingError(f"part_framing: true (story.json beside the plan), false or a list of word indices, got {pf!r}")
    if parts is not None:
        valid = [w for w in parts if isinstance(w, int) and not isinstance(w, bool) and 0 <= w < n_words]
        if not parts or len(valid) != len(parts):
            raise FramingError(f"part_framing: every part start is a word index 0..{n_words - 1}, got {parts!r}")
        parts = sorted(set(valid))
    if every is None and parts is None:
        return None
    return {"every": None if every is None else float(every), "parts": parts}


def part_pieces(segs: list, W: list, starts: list[int] | None) -> list[list]:
    """segs ([s0, s1, kind]) as pieces [s0, s1, part number or None, split?]: a piece is split in the word gap before each
    part's first word (or the part is pinned to the piece edge it sits next to)"""
    pieces = [[s0, s1, None, False] for s0, s1, _ in segs]
    for n, w in enumerate(starts or []):
        tw = W[w][0]
        c = (W[w - 1][1] + tw) / 2 if w > 0 else tw
        k = next((i for i, p in enumerate(pieces) if p[1] > tw), None)
        if k is None:  # the part starts after the last kept word: nothing of it is in the film
            continue
        s0, s1 = pieces[k][0], pieces[k][1]
        if c - s0 < PART_EDGE:
            pieces[k][2] = n
        elif s1 - c < PART_EDGE:
            if k + 1 < len(pieces): pieces[k + 1][2] = n
        else:
            c = round(c, 3)
            pieces[k:k + 1] = [[s0, c, pieces[k][2], pieces[k][3]], [c, s1, n, True]]
    return pieces


def cut_point(W: list, s0: float, s1: float, lo: float, hi: float) -> float | None:
    """source time of the best word gap inside the piece with lo <= gap <= hi: a sentence end, then a clause end, then the
    latest gap (closest to when the change is due); None = no gap there"""
    best = None
    for i in range(len(W) - 1):
        a, b = W[i][1], W[i + 1][0]
        if a < s0 or b > s1:
            continue
        m = max(a, min((a + b) / 2, b))
        if not lo <= m <= hi:
            continue
        t = W[i][2].strip()
        score = (2 if SENTENCE.search(t) else 1 if CLAUSE.search(t) else 0, m)
        if best is None or score > best:
            best = score
    return None if best is None else round(best[1], 3)


def assign(pieces: list[list], W: list, zooms: list, opts: dict, exact: bool, every_cut: bool = False) -> tuple[list[dict], dict]:
    """EDL segments with their zoom level, and a report {"every_s", "parts", "changes", "max_still"} for the EDL"""
    wide = zooms[0]
    tight = zooms[1] if len(zooms) > 1 and zooms[1] > wide + 0.01 else round(wide + 0.15, 3)
    part_b = max(PART_B, tight)
    every = opts["every"]

    def is_tight(z: float) -> bool:
        return z > wide + 0.01

    q: deque[tuple[float, float, int | None, bool, str | None]] = deque((p[0], p[1], p[2], p[3], None) for p in pieces)
    out: list[dict] = []
    level = None; changed_at = 0.0; acc = 0.0; prev_end = None; tight_run = 0; changes = 0; longest = 0.0
    while q:
        s0, s1, part, split, why = q.popleft()
        d = timeline.piece_len({"in": round(s0, 3), "out": round(s1, 3)}, exact)
        mark = None
        if part is not None:
            new, mark = (wide if part % 2 == 0 else part_b), "part"
        elif level is None:
            new = wide
        elif why == "every_s":
            new, mark = (wide if is_tight(level) else tight), "every_s"
        elif prev_end is not None and (s0 - prev_end > JUMP or every_cut):
            new = wide if is_tight(level) else tight
        elif every and not split and prev_end is not None and s0 > prev_end + 1e-6 and acc + d - changed_at > every \
                and acc - changed_at >= every / 2:
            new, mark = (wide if is_tight(level) else tight), "every_s"  # an existing (pause) cut, before splitting a word gap
        else:
            new = level
        if level is not None and new != level and is_tight(new) and is_tight(level) and tight_run >= 2:
            new = wide  # L10: at most 2 tight framings in a row
        carry: dict = {}
        if level is not None and new == level and split and out:
            # a part split that changes nothing (part A after a wide piece): no cut, the previous piece goes on
            prev = out.pop()
            carry = {k: prev[k] for k in ("framing", "part") if k in prev}
            s0, acc = prev["in"], timeline.total(out, exact)
            d = timeline.piece_len({"in": round(s0, 3), "out": round(s1, 3)}, exact)
            mark = None
        elif level is None or new != level:
            if level is not None:
                changes += 1
                longest = max(longest, acc - changed_at)
            tight_run = (tight_run + 1 if level is not None and is_tight(level) else 1) if is_tight(new) else 0
            changed_at = acc
        else:
            mark = None
        level = new
        if every and acc + d - changed_at > every:
            target = changed_at + every - acc  # offset into this piece where the change is due
            hi = min(s1 - MIN_PIECE, s0 + max(target, MIN_PIECE))
            lo = min(hi, s0 + max(MIN_PIECE, target - every / 2))
            c = cut_point(W, s0, s1, lo, hi) if hi >= s0 + MIN_PIECE else None
            if c is not None:
                q.appendleft((c, s1, None, True, "every_s"))
                s1 = c
        seg = {"src": "A", "in": round(s0, 3), "out": round(s1, 3), "zoom": new, **carry}
        if mark:
            seg["framing"] = mark
            if mark == "part": seg["part"] = part
        out.append(seg)
        acc = timeline.total(out, exact)
        prev_end = s1
    longest = max(longest, acc - changed_at)
    return out, {"every_s": every, "parts": len(opts["parts"] or []), "changes": changes, "max_still": round(longest, 2)}


def _level(z) -> float:
    return z.get("b", z.get("a", 1.0)) if isinstance(z, dict) else float(z)


def _rises(z: dict) -> list[float]:
    """piece times where a quick punch-in starts (a rise of > 0.1 in under 1 s), keyframed or a single move"""
    keys = z.get("keys") or [[0.0, z["a"]], [z["t0"], z["a"]], [z["t1"], z["b"]]]
    return [ta for (ta, va), (tb, vb) in pairwise(keys) if vb > va + 0.1 and tb - ta < 1.0]


def hook_punch(out: list[dict], boxed: set, at: float, exact: bool, window: float = 0.25, amt: float = 0.2,
               speed: float = 0.3) -> dict:
    """plan "hook_pos": "mid" (ledger S8): a picture change when the hook title leaves, at `at` (hook_dur) +-window s of
    film time. A zoom step or punch already there is kept; else a punch-in (amt, speed as an emphasis in build_edl.py) is
    put into the piece on screen then, never under a card that covers the face (boxed). Returns {"at", "seg", "how"} or
    {"at": None, "why"}; the piece it went into gets "hook_punch": true. face_track.py may still clamp it (head first)."""
    starts = timeline.starts(out, exact)
    for k, sg in enumerate(out):
        z = sg["zoom"]
        if k and abs(starts[k] - at) <= window and abs(_level(out[k - 1]["zoom"]) - (z["a"] if isinstance(z, dict) else z)) >= 0.08:
            return {"at": round(starts[k], 3), "seg": k, "how": "zoom_step"}
        hits = [t for t in _rises(z) if abs(starts[k] + t - at) <= window] if isinstance(z, dict) else []
        if hits:
            return {"at": round(starts[k] + hits[0], 3), "seg": k, "how": "punch"}
    k = next((i for i, s in enumerate(starts) if s <= at < s + timeline.piece_len(out[i], exact)), None)
    if k is None:
        return {"at": None, "why": f"the film ends before {at:g} s"}
    why = "a card covers the face then"
    for kk in (k, k + 1, k - 1):
        if not 0 <= kk < len(out) or kk in boxed:
            continue
        sg, d = out[kk], timeline.piece_len(out[kk], exact)
        rel = min(max(at - starts[kk], 0.05), d - speed - 0.05)
        if rel < 0.05 or abs(starts[kk] + rel - at) > window:
            why = "no piece long enough for a punch then"
            continue
        z = sg["zoom"]
        if not isinstance(z, dict):
            sg["zoom"] = {"a": z, "b": round(min(z + amt, 1.38), 3), "t0": round(rel, 3), "t1": round(rel + speed, 3)}
        elif z.get("keys") or z["t1"] - z["t0"] < 1.0:  # a punch already in the piece: snap back to its level, punch again
            keys = z.get("keys") or [[0.0, z["a"]], [z["t0"], z["a"]], [z["t1"], z["b"]]]
            if rel < keys[-1][0] + 0.2:
                why = "another move runs then"
                continue
            keys += [[round(rel - 0.034, 3), keys[-1][1]], [round(rel, 3), z["a"]], [round(rel + speed, 3), round(min(z["a"] + amt, 1.38), 3)]]
            z["keys"] = keys; z["b"] = max(v for _, v in keys)
        else:  # the slow drift of a long shot: the punch takes its place (as an emphasis does)
            sg["zoom"] = {"a": z["a"], "b": round(min(z["a"] + amt, 1.38), 3), "t0": round(rel, 3), "t1": round(rel + speed, 3)}
        sg["hook_punch"] = True
        return {"at": round(starts[kk] + rel, 3), "seg": kk, "how": "punch"}
    return {"at": None, "why": why}
