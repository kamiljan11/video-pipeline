#!/usr/bin/env python3
"""kden_export: edl_<film>.json -> a Kdenlive project where Kamil drags the cut edges to get back what was cut too much.

    python3 kden_export.py <work>/edl_long.json <out>.kdenlive [--music music.wav] [--sfx sfx.wav]

Tracks, bottom to top: sfx, music (both at the plan's music_db, to hear the cut in context), V1 = the recording in the
film's pieces, picture and voice in one clip (the Ripple tool moves the rest of the timeline with a dragged edge), then
the cards (a card that overlaps another goes one track up; they are there to see what a moved cut does to them).
Not in it: zooms, the face circle, subtitles — drawn by the render. <out>.kdenlive.base.json keeps the cut as exported:
kden_import.py compares the saved project with it and writes the moved edges to the plan ("cut_fix", cut_fix.py).
Kdenlive 26.08 opens it only with main_bin "kdenlive:docproperties.version" and a kdenlive:id on every clip (2026-11-10).
"""
import json
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

FPS = 30


def frames(seconds: float) -> int:
    return round(seconds * FPS)


def lanes(overlays: list[dict]) -> list[list[tuple[int, int, int]]]:
    """cards onto as few tracks as they fit: per track (card number, start frame, frames), no two overlapping"""
    out: list[list[tuple[int, int, int]]] = []
    for n, o in enumerate(sorted(overlays, key=lambda o: o["at"])):
        a, d = frames(o["at"]), max(1, frames(o["dur"]))
        lane = next((ln for ln in out if ln[-1][1] + ln[-1][2] <= a), None)
        if lane is None: lane = []; out.append(lane)
        lane.append((n, a, d))
    return out


def project(edl: dict, base: str, music: str | None = None, sfx: str | None = None) -> str:
    prod, binl, pls, tracks, nid = [], [], [], [], 2  # tracks: (playlist id, hide attribute or None)

    def clip(pid: str, path: str, out: int | None = None, chain: bool = False, level: float | None = None) -> None:
        nonlocal nid
        tag = "chain" if chain else "producer"
        flt = f'<filter><property name="mlt_service">volume</property><property name="level">{level}</property></filter>' if level is not None else ""
        length = "" if out is None else f' out="{out}"'
        prod.append(f'<{tag} id="{pid}"{length}><property name="resource">{escape(path)}</property>'
                    f'<property name="kdenlive:id">{nid}</property>{flt}</{tag}>')
        binl.append(f'<entry producer="{pid}"/>'); nid += 1

    for k, p in edl["sources"].items(): clip(f"src_{k}", os.path.abspath(p), chain=True)
    for name, path in (("sfx", sfx), ("music", music)):
        if path and os.path.exists(path):
            clip(name, os.path.abspath(path), level=edl.get("music_db", -12))
            pls.append(f'<playlist id="a_{name}"><property name="kdenlive:audio_track">1</property><entry producer="{name}"/></playlist>')
            tracks.append((f"a_{name}", "video"))
    cuts = "".join(f'<entry producer="src_{s["src"]}" in="{frames(s["in"])}" out="{frames(s["out"]) - 1}"/>' for s in edl["segments"])
    pls.append(f'<playlist id="v_cam">{cuts}</playlist>'); tracks.append(("v_cam", None)); cam = len(tracks) - 1
    cards = sorted(edl.get("overlays", []), key=lambda o: o["at"])
    for i, lane in enumerate(lanes(cards)):
        ents, end = [], 0
        for n, a, d in lane:
            clip(f"g{n}", os.path.join(base, cards[n]["file"]), out=d - 1)
            if a > end: ents.append(f'<blank length="{a - end}"/>')
            ents.append(f'<entry producer="g{n}" in="0" out="{d - 1}"/>'); end = a + d
        pls.append(f'<playlist id="v_cards{i + 1}">{"".join(ents)}</playlist>'); tracks.append((f"v_cards{i + 1}", "audio"))

    def transition(i: int, a: int, b: int, service: str, extra: str = "") -> str:
        return (f'<transition id="t{i}"><property name="a_track">{a}</property><property name="b_track">{b}</property>'
                f'<property name="mlt_service">{service}</property><property name="always_active">1</property>'
                f'<property name="internal_added">237</property>{extra}</transition>')

    x = ['<?xml version="1.0" encoding="utf-8"?>', f'<mlt LC_NUMERIC="C" version="7.43.0" title={quoteattr(edl.get("name", "film"))} producer="main_bin">',
         (f'<profile description="{edl.get("w", 2560)}x{edl.get("h", 1440)} {FPS} fps" width="{edl.get("w", 2560)}" height="{edl.get("h", 1440)}" progressive="1" '
          f'sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="16" display_aspect_den="9" frame_rate_num="{FPS}" frame_rate_den="1" colorspace="709"/>'),
         *prod,
         '<playlist id="main_bin"><property name="kdenlive:docproperties.version">1.04</property><property name="xml_retain">1</property>' + "".join(binl) + "</playlist>",
         *pls, '<tractor id="tractor0">' + "".join(f'<track producer="{p}"/>' if hide is None else f'<track producer="{p}" hide="{hide}"/>' for p, hide in tracks)]
    x += [transition(i, 0, i, "mix", '<property name="sum">1</property>') for i in range(1, len(tracks))]
    x += [transition(100 + i, cam, i, "qtblend") for i in range(cam + 1, len(tracks))]
    return "\n".join([*x, "</tractor></mlt>"]) + "\n"


def base_record(edl: dict) -> dict:
    """the cut as exported, for kden_import.py: every piece's recording file and its start/end in seconds"""
    return {"fps": FPS, "pieces": [[os.path.abspath(edl["sources"][s["src"]]), s["in"], s["out"]] for s in edl["segments"]]}


def main(argv: list[str]) -> int:
    opt = {k: argv[argv.index(k) + 1] for k in ("--music", "--sfx") if k in argv and argv.index(k) + 1 < len(argv)}
    args = [a for a in argv if a not in opt and a not in opt.values()]
    if len(args) != 2: print(__doc__); return 2
    edl_p, out_p = Path(args[0]), Path(args[1])
    edl = json.loads(edl_p.read_text(encoding="utf-8"))
    out_p.write_text(project(edl, str(edl_p.resolve().parent), opt.get("--music"), opt.get("--sfx")), encoding="utf-8")
    Path(str(out_p) + ".base.json").write_text(json.dumps(base_record(edl)) + "\n", encoding="utf-8")
    print(f"{out_p}: {len(edl['segments'])} pieces, {len(edl.get('overlays', []))} cards on {len(lanes(edl.get('overlays', [])))} track(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
