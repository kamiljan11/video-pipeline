"""gfx_events: what happens inside a card, as film times on the card's EDL overlay (build_edl.py), so a checker sees it.

An overlay in the EDL is one card ("at", "dur"), but a scene keeps moving while it is on. These overlay fields (film seconds,
written only when there is something to list) say what:
  "zooms":      L17 the start of each "canvas_zoom" of a scene (gfx/scene_lib.mjs): a punch-in on the drawing, so it counts
                like a punch-in on the face (a punch, an event of the first 60 s)
  "moves":      S14 every change of the picture inside the card: a camera move between "cam" stops, a canvas zoom, a cursor
                setting off, a terminal starting to type, a read-along step; motion inside a panel is a picture change too
  "read_along": L16b each moment a line is lit because it is said (scene term/win/file "read_along", web card "read_along")
  "items":      S11 [in, out] of each list item (a scene piece with "item": n), in list order
Timings mirror gfx/scene_lib.mjs (camera MOVE, the cursor's move, the terminal's typing start): change both together.

Plan check (cue_problems): a gfx entry of the plan may name the spoken word of each cue, "read_along": [word index, ...] and
"items": [word index of each item's numeral, ...]; build_edl.py then refuses a card whose cue is off its word (S11: an item
appears at most 0.3 s after its numeral) and prints the card time to put in the spec.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from itertools import pairwise
from typing import Any

MOVE = 0.9  # s, a camera move before its stop (scene_lib.mjs MOVE)
ZOOM_D = 0.4  # s, a canvas zoom (scene_lib.mjs CANVAS_ZOOM.d)
CUE_EARLY, CUE_LATE = -0.15, 0.3  # s, a cue against its word: a hair early (like gfx_lead) up to 0.3 s late (S11)
CAM_SAME = ("on", "x", "y", "z", "pad", "zmax")  # two stops with these equal frame the same: no move between them


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def piece_at(e: dict) -> float:
    """when a piece comes in (scene_lib.mjs pieceAt): its "at", a kinetic line just before its first word, else 0"""
    at = _num(e.get("at"))
    if at is not None: return at
    ws = [t for w in e.get("words") or [] if isinstance(w, list) and len(w) > 1 and (t := _num(w[1])) is not None]
    return max(0.0, min(ws) - 0.05) if e.get("k") == "say" and ws else 0.0


def _cam_moves(cam: Any) -> list[float]:
    if not isinstance(cam, list): return []
    out: list[float] = []
    for prev, s in pairwise(cam):
        t, t0 = _num(s.get("t")) if isinstance(s, dict) else None, _num(prev.get("t")) if isinstance(prev, dict) else None
        if t is None or t0 is None or all(s.get(k) == prev.get(k) for k in CAM_SAME): continue
        mv = _num(s.get("move"))
        out.append(max(t0, t - (MOVE if mv is None else mv)))
    return out


def scene_times(sp: dict) -> dict[str, list]:
    """card seconds of a scene's inner events: {"zooms", "moves", "read_along", "items"}"""
    dur = _num(sp.get("dur")) or 0.0
    els = [e for e in sp.get("els") or [] if isinstance(e, dict)]
    zooms = [t for z in sp.get("canvas_zoom") or [] if isinstance(z, dict) and (t := _num(z.get("t"))) is not None]
    read = sorted(t for e in els for s in e.get("read_along") or [] if isinstance(s, list) and s and (t := _num(s[0])) is not None)
    cursor, typing = [], []
    for e in els:
        at = piece_at(e)
        if e.get("k") == "cursor":  # scene_lib cursor: arrives at click_at, moving min(0.7, max(0.2, click_at - at - 0.05)) s
            ca = _num(e.get("click_at")); ca = at + 0.75 if ca is None else ca
            cursor.append(ca - min(0.7, max(0.2, ca - at - 0.05)))
        if e.get("k") == "term" and isinstance(e.get("cmd"), str):  # the command starts typing
            ct = _num(e.get("cmd_at")); typing.append(at + 0.5 if ct is None else ct)
    items = []
    for e in els:
        n = e.get("item")
        if not (isinstance(n, int) and not isinstance(n, bool)): continue
        end = min([dur] + [t for k in ("gone", "out_at") if (t := _num(e.get(k))) is not None])
        items.append((n, piece_at(e), end))
    return {"zooms": zooms, "read_along": read, "items": [[a, b] for _, a, b in sorted(items)],
            "moves": sorted(set(_cam_moves(sp.get("cam")) + zooms + cursor + typing + read))}


def card_times(sp: dict) -> dict[str, list]:
    """card seconds of the inner events of any card; a card type without any: empty lists"""
    if sp.get("type") == "scene": return scene_times(sp)
    if sp.get("type") == "web":  # the quote lines marked as said (render.mjs web, webshot_lib markTimes)
        read = [t for v in sp.get("read_along") or [] if (t := _num(v)) is not None]
        return {"zooms": [], "read_along": read, "items": [], "moves": read}
    return {"zooms": [], "read_along": [], "items": [], "moves": []}


def overlay_fields(sp: dict, at: float) -> dict[str, list]:
    """film seconds for the overlay of a card that comes in at `at`; only fields with something in them, events inside the card"""
    dur = _num(sp.get("dur")) or 0.0
    out: dict[str, list] = {}
    for k, ts in card_times(sp).items():
        if k == "items": v = [[round(at + a, 3), round(at + b, 3)] for a, b in ts if 0 <= a <= dur]
        else: v = [round(at + t, 3) for t in ts if 0 <= t <= dur]
        if v: out[k] = v
    return out


def cue_problems(g: dict, sp: dict, at: float, word_film: Callable[[int], float], n_words: int) -> list[str]:
    """a plan gfx entry's "read_along" / "items" word lists against the card's cues; [] = every cue on its word"""
    bad: list[str] = []
    times = card_times(sp)
    for key, cues in (("read_along", times["read_along"]), ("items", [a for a, _ in times["items"]])):
        if key not in g: continue
        ws = g[key]
        if not (isinstance(ws, list) and all(isinstance(w, int) and not isinstance(w, bool) and 0 <= w < n_words for w in ws)):
            bad.append(f"plan {key} = word indexes (0..{n_words - 1}), one per {key} cue of the card, got {ws!r}"); continue
        want = [round(word_film(w) - at, 2) for w in ws]  # card seconds of each word
        if len(ws) != len(cues):
            bad.append(f"plan {key} names {len(ws)} words, the card has {len(cues)} {key} cues; card times of the words: {want}"); continue
        off = [(c, t) for c, t in zip(cues, want, strict=True) if not CUE_EARLY - 1e-6 <= c - t <= CUE_LATE + 1e-6]  # 1e-6: float noise at the ends
        if off:
            bad.append(f"{key} off its words (allowed {CUE_EARLY:+g}..{CUE_LATE:+g} s): card has {[round(c, 2) for c, _ in off]}, "
                       f"the words are said at {[t for _, t in off]} (card s)")
    return bad
