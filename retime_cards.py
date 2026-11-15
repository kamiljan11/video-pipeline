#!/usr/bin/env python3
"""retime_cards: the pieces of every scene and float card follow the cut when the cut changes.

    python3 retime_cards.py <old edl.json> <new edl.json> <gfx_specs.json>     rewrites the specs (a copy .bak next to it)

A scene or float card times its pieces in card seconds, typed for the words said under it in one cut. Any other cut (a
sentence put back, a pause kept longer) moves those words. 2026-11-15: Kamil asked for the cut sentences back and for air
between sentences (\"za ostro pociachane\"); by hand that was 7 cards shifted one by one, and longer pauses move every piece
of every card a little. Each timing is mapped through the recording: card second t of the old cut -> the source second shown
there -> the film second of that source second in the new cut -> minus the card's new start. A source second the new cut
leaves out maps to the next piece the new cut keeps. Cards on screen in only one of the two cuts are left alone.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

TIMING = {"at", "t", "gone", "dur", "out_at", "mark_at", "on_at", "hl_at", "x_at", "cmd_at", "click_at", "back_at",
          "packet_at", "pulse_at"}  # card seconds in a scene spec (gfx/scene_lib.mjs); "t" is text when it is not a number
LEAD = 0.7  # s: a card starting this close before a cut belongs to the piece after it
EASE = re.compile(r"\([^)]*\)")


def film_to_source(segs: list[dict], t: float) -> float:
    """the source second shown at film second t (segments in film order; past the end the last frame holds)"""
    for s in segs:
        d = s["out"] - s["in"]
        if t < d: return s["in"] + max(t, 0.0)
        t -= d
    return segs[-1]["out"] if segs else 0.0


def source_to_film(segs: list[dict], src: float) -> float:
    """the film second that shows source second src; one the cut leaves out -> the start of the next piece after it in
    the source (pieces may be out of source order: the nearest later start wins)"""
    t, later = 0.0, None
    for s in segs:
        if s["in"] <= src < s["out"]: return t + (src - s["in"])
        if s["in"] >= src and (later is None or s["in"] < later[0]): later = (s["in"], t)
        t += s["out"] - s["in"]
    return later[1] if later else t


def start_source(segs: list[dict], a: float) -> float:
    """the recording second a card starting at film second a belongs to: a card that starts under the last LEAD s of a
    piece (gfx_lead puts it a little before its word) belongs to the next piece (2026-11-15 f_nie_wierzy: started 0.6 s
    before the cut to w187, mapped to w69 and came out 51 s long)"""
    t = 0.0
    for i, s in enumerate(segs):
        d = s["out"] - s["in"]
        if a < t + d:
            if t + d - a < LEAD and i + 1 < len(segs): return segs[i + 1]["in"]
            return s["in"] + max(a - t, 0.0)
        t += d
    return segs[-1]["out"] if segs else 0.0


def mapper(old: dict, new: dict, card: str):
    """card second in the old cut -> card second in the new cut, or None when the card is not in the old cut or the new
    cut leaves out the second it started on. A new cut built without cards (no overlays) starts the card where the
    recording second of its old start lands; the plan anchors cards to words, so that is where it will start."""
    a = next((o["at"] for o in old.get("overlays", []) if o.get("id") == card), None)
    if a is None: return None
    if new.get("overlays"): b = next((o["at"] for o in new["overlays"] if o.get("id") == card), None)
    else:
        src = start_source(old["segments"], a)
        b = source_to_film(new["segments"], src) if any(s["in"] <= src < s["out"] for s in new["segments"]) else None
    if b is None: return None
    return lambda t: round(source_to_film(new["segments"], film_to_source(old["segments"], a + t)) - b, 2)


def retime_json(o, f) -> int:
    """every TIMING number in a scene spec through f, in place; the count changed"""
    n = 0
    if isinstance(o, dict):
        for k, v in o.items():
            if k in TIMING and isinstance(v, (int, float)) and not isinstance(v, bool):
                w = f(v)
                if w != v: o[k] = w; n += 1
            else: n += retime_json(v, f)
    elif isinstance(o, list):
        for v in o: n += retime_json(v, f)
    return n


def retime_html(html: str, f) -> tuple[str, int]:
    """the delay of every animation in a float card's html through f (shorthand "name time easing delay fill"; an
    infinite loop keeps its delay: it runs while the piece is up)"""
    n = 0

    def one(m: re.Match) -> str:
        nonlocal n
        parts = re.split(r",(?![^()]*\))", m.group(1))
        for i, a in enumerate(parts):
            flat = EASE.sub(lambda z: "(" + "_" * (len(z.group(0)) - 2) + ")", a)  # times inside cubic-bezier() are not times
            ts = list(re.finditer(r"(?<![\d.])(\d+(?:\.\d+)?)s\b", flat))
            if len(ts) < 2 or "infinite" in a: continue
            d = ts[1]; w = f(float(d.group(1)))
            if abs(w - float(d.group(1))) > 1e-9:
                parts[i] = a[:d.start()] + f"{max(w, 0.0):.2f}s" + a[d.end():]; n += 1
        return "animation:" + ",".join(parts)
    return re.sub(r"animation:([^;\"]+)", one, html), n


def forward(segs: list[dict], a: float, b: float) -> bool:
    """film seconds a..b of a cut show the recording in its order (a cut that moved a piece back maps card seconds
    backwards: 2026-11-15 f_nie_wierzy over the moved w187-232 came out 51 s long instead of 3.65 s)"""
    t, last = 0.0, None
    for s in segs:
        d = s["out"] - s["in"]
        if t + d > a and t < b:
            if last is not None and s["in"] < last: return False
            last = s["out"]
        t += d
    return True


def retime(old: dict, new: dict, specs: list[dict]) -> list[str]:
    """every scene and float card of both cuts retimed in place; one line per card that changed or was left alone
    because the old cut plays its words out of order"""
    out = []
    for sp in specs:
        if sp.get("type") not in ("scene", "float"): continue
        cid = sp.get("id")
        if not isinstance(cid, str): continue
        f = mapper(old, new, cid)
        if f is None: continue
        dur = sp.get("dur")
        at = next(o["at"] for o in old.get("overlays", []) if o.get("id") == cid)
        if not forward(old["segments"], at, at + (dur if isinstance(dur, (int, float)) else 0.0)):
            out.append(f"{cid}: LEFT ALONE, the old cut plays its words out of recording order: time it by hand"); continue
        if sp["type"] == "scene": n = retime_json({k: v for k, v in sp.items() if k in ("els", "cam", "canvas_zoom")}, f)
        else: sp["html"], n = retime_html(sp.get("html", ""), f)
        if isinstance(dur, (int, float)): sp["dur"] = max(f(dur), 0.5)
        if n or sp.get("dur") != dur: out.append(f"{sp['id']}: {n} timings, dur {dur} -> {sp.get('dur')}")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3: print(__doc__, file=sys.stderr); return 2
    old, new = (json.loads(Path(a).read_text(encoding="utf-8")) for a in argv[:2])
    sp = Path(argv[2]); specs = json.loads(sp.read_text(encoding="utf-8"))
    lines = retime(old, new, specs)
    shutil.copyfile(sp, sp.with_suffix(".json.bak"))
    sp.write_text(json.dumps(specs, ensure_ascii=False), encoding="utf-8")
    for line in lines: print(f"retime_cards: {line}")
    print(f"retime_cards: {len(lines)} cards retimed ({sp.with_suffix('.json.bak')} keeps the old specs)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
