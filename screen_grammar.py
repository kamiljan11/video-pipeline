"""Screen grammar of a 16:9 long: how often the film leaves the speaker for a separate screen and how long a card stays.

A plan builder (render/montaz/<film>/work/build_plan_*.py) calls screen_pass() on its cards before it writes gfx_specs.json.
The rules come from Kamil's corrections of film 2 (2026-11-05: "zbyt często przenosimy się na osobny ekran", "nie zdąży się
przeczytać", "memy wycinać i wklejać dookoła mnie", "rzeczy latające dookoła mnie") and from the Negacz teardown
(style/REF-long-negacz.md L1, L3, L4). film_check.py measures the result: long.screen_switches, long.screen_block,
long.speaker_back, long.screen_share, long.reading.

  python3 -m unittest tests.test_screen_grammar
"""
from __future__ import annotations

import copy
import itertools
import json
import os
from functools import cache
from pathlib import Path

from film_check import UNTIMED, reading_need
from gfx_types import beside, is_full

HERE = Path(__file__).resolve().parent


def _style() -> tuple[int, float, str, float]:
    """thresholds are data (README: style = data, not code): style/screen_grammar.json + the gate's long.speaker_back"""
    st = json.loads((HERE / "style" / "screen_grammar.json").read_text())
    side, shift, recap = st.get("side_max_els"), st.get("shift_max"), st.get("recap_prefix")
    if not (isinstance(side, int) and side > 0 and isinstance(shift, (int, float)) and shift >= 0 and isinstance(recap, str) and recap):
        raise SystemExit('style/screen_grammar.json: "side_max_els" a whole number > 0, "shift_max" seconds >= 0, "recap_prefix" an id prefix')
    back = [i.get("value") for i in json.loads((HERE / "style" / "checklist.json").read_text())["items"] if i.get("id") == "long.speaker_back"]
    if len(back) != 1 or not isinstance(back[0], (int, float)): raise SystemExit("style/checklist.json: one long.speaker_back with a number value")
    return side, float(shift), recap, float(back[0])


# SIDE_MAX_ELS: a scene of this many pieces or fewer is drawn beside him (layout "side"); SHIFT_MAX: a card with no room after
# it may start this much earlier; SPEAKER_BACK: between two separate screens he is back this long, or the two become one block
SIDE_MAX_ELS, SHIFT_MAX, RECAP, SPEAKER_BACK = _style()
# a piece of words stays on screen long enough to be read: 0.6 s + 0.25 s a word, at least 1.2 s (the same rule as
# gfx/scene_check.mjs readProblems READ_MIN_S; 2026-11-08 the s08 punch line "TYLKO NA PAPIERZE" came in 0.8 s before its card ended)
PIECE_READ_MIN, PIECE_READ_BASE, PIECE_READ_WORD = 1.2, 0.6, 0.25
_TEXT_KEYS = {"text", "words", "t", "rows", "label", "title", "name", "sub", "head", "suf", "out", "cmd", "value", "pre", "lines", "msgs", "items"}
_NOT_TEXT = {"k", "id", "tone", "icon", "anim", "mark", "who", "on", "owner", "extends", "from", "to"}


def piece_words(e) -> int:
    """the words a viewer reads in one scene piece (its text, rows, lines, chat messages ...; not its id, tone or icon)"""
    def strings(x, inside):
        if isinstance(x, str): return [x] if inside else []
        if isinstance(x, dict): return [w for k, v in x.items() if k not in _NOT_TEXT for w in strings(v, inside or k in _TEXT_KEYS)]
        if isinstance(x, (list, tuple)): return [w for v in x for w in strings(v, inside)]
        return []
    return sum(len(s.split()) for s in strings(e, False))


def piece_need(e) -> float:
    """seconds a scene piece must stay on screen to be read"""
    return max(PIECE_READ_MIN, PIECE_READ_BASE + PIECE_READ_WORD * piece_words(e))


def piece_start(e: dict) -> float:
    """seconds into a resolved card when a piece comes in (scene_check.mjs window_: its at, first word, message or item)"""
    ts = [e.get("at"), *(w[1] for w in e.get("words") or [] if isinstance(w, (list, tuple)) and len(w) > 1),
          *(m.get("at") for m in e.get("msgs") or [] if isinstance(m, dict)), *(m.get("at") for m in e.get("items") or [] if isinstance(m, dict))]
    ts = [t for t in ts if isinstance(t, (int, float))]
    return min(ts) if ts else 0.0


def read_floor(sp: dict) -> float:
    """seconds into a resolved card (times in seconds) when its last piece of words has been read; a piece that leaves
    ("gone") is not held by the card's length. 0 for a card without pieces"""
    return max([0.0] + [piece_start(e) + piece_need(e) for e in sp.get("els") or [] if not isinstance(e.get("gone"), (int, float))])


TIED = ("line", "cursor", "ring", "stamp", "check")  # scene_lib.mjs TIED: pieces placed on another piece, not stackable in a column
SHIFTABLE = ("kw", "count", "sticker", "float")  # cards whose inner timing is only a top-level "at" list (or none)
# RECAP: id prefix of a recap map (plan builders name them m1_mapa, m2_…), dropped when it has no room to be read


@cache
def has_sticker(slug: str) -> bool:
    """the template has "sticker" crops (style/memes.json, or the picture's own json in the meme library, as gfx/render.mjs
    memeLib reads them): without them a "sticker" card stops the render (review 2026-11-05: 5 of 19 templates have none)"""
    lib = Path(os.environ.get("VP_MEMES", HERE / "render" / "memes"))
    for f in (HERE / "style" / "memes.json", lib / f"{slug}.json"):
        try: d = json.loads(f.read_text())
        except (OSError, ValueError): continue
        crops = (d.get(slug) if f.name == "memes.json" else d) or {}
        if isinstance(crops, dict) and crops.get("sticker"): return True
    return False


def goes_beside(sp: dict) -> bool:
    """screen_pass puts it in the free field right of the head (gfx_types.beside): a 16:9 meme with sticker crops or a
    simple scene"""
    if sp.get("canvas") == "v": return False
    if sp["type"] == "meme": return has_sticker(str(sp.get("meme")))  # no crops: the meme stays a whole picture
    return (sp["type"] == "scene" and len(sp.get("els") or []) <= SIDE_MAX_ELS and sp.get("pip") is not False
            and sp.get("cam") != "none"  # scene_lib.checkScene refuses layout "side" with cam "none"
            and not any(e.get("k") in TIED for e in sp.get("els") or []))  # stacked into a column beside him (scene_lib col)


def screen_pass(cards: list[tuple[float, dict]], drop: dict[str, str] | None = None, log=print):
    """cards = [(film start s, spec)], the plan's cards one at a time. Returns (specs, shift) with copies of the specs:
    - memes with sticker crops (has_sticker) become stickers and simple scenes go beside him (layout "side"): he stays full frame;
    - every card is held to its reading time (film_check.reading_need): longer where the next card leaves room; else a
      SHIFTABLE card starts up to SHIFT_MAX s earlier, taking the time from the card before when that one has more
      than its own reading time; shift = {id: seconds earlier (negative)} for the plan's "lead";
    - a recap map (id "m…", a scene) that still cannot get its reading time is dropped, and so is every id in drop;
    - two separate screens closer than SPEAKER_BACK with nothing between them join into one block."""
    t0 = {sp["id"]: t for t, sp in cards}
    drop = drop or {}
    for i, why in drop.items(): log(f"screen_pass: {i} left out ({why})")
    out = [copy.deepcopy(sp) for _, sp in sorted(cards, key=lambda c: c[0]) if sp["id"] not in drop]
    for sp in out:
        if goes_beside(sp) and sp["type"] == "meme": sp["type"] = "sticker"
        elif goes_beside(sp): sp["layout"] = "side"; sp.pop("bg", None)
    shift: dict[str, float] = {}

    def blocks(sp, other):  # a lower third sits bottom left: it does not stop a card beside him (right) from running on
        return not (other["type"] == "lower" and beside(sp))

    def room_after(k):
        nxt = [t0[q["id"]] for q in out[k + 1:] if blocks(out[k], q)]
        return (min(nxt) - t0[out[k]["id"]] - 0.05) if nxt else 99.0

    keep: list[dict] = []

    def room_before(sp):
        prev = [t0[q["id"]] + q["dur"] for q in keep if blocks(sp, q)]
        return t0[sp["id"]] - (max(prev) + 0.05) if prev else t0[sp["id"]]

    for k, sp in enumerate(out):
        need = reading_need(sp)
        if sp["dur"] < need and sp["type"] not in UNTIMED:
            sp["dur"] = round(min(need, max(sp["dur"], room_after(k))), 2)
            d = min(need - sp["dur"], SHIFT_MAX)
            if sp["type"] in SHIFTABLE and d > room_before(sp) and keep and blocks(sp, keep[-1]):
                prev = keep[-1]  # take it from the card before when that one has more than its own reading time
                cut = min(d - max(room_before(sp), 0.0), prev["dur"] - max(reading_need(prev), read_floor(prev)))  # nor its last piece (s39 2026-11-08)
                if cut > 0: prev["dur"] = round(prev["dur"] - cut, 2)
            d = min(d, room_before(sp))
            if d > 0.05 and sp["type"] in SHIFTABLE:
                t0[sp["id"]] -= d; sp["dur"] = round(sp["dur"] + d, 2); shift[sp["id"]] = round(-d, 3)
                if isinstance(sp.get("at"), list): sp["at"] = [round(x + d, 2) for x in sp["at"]]  # words stay on their speech
        if sp["id"].startswith(RECAP) and sp["type"] == "scene" and sp["dur"] < need - 1e-6:
            log(f"screen_pass: {sp['id']} dropped (recap map, {sp['dur']:.1f} s of room < {need:.1f} s to read)"); continue
        keep.append(sp)
    full = [sp for sp in keep if is_full(sp)]
    for p, q in itertools.pairwise(full):
        gap = t0[q["id"]] - t0[p["id"]] - p["dur"]
        between = [sp for sp in keep if t0[p["id"]] < t0[sp["id"]] < t0[q["id"]]]
        if 0 < gap < SPEAKER_BACK and not between: p["dur"] = round(t0[q["id"]] - t0[p["id"]], 2)
    return keep, shift
