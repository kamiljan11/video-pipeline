#!/usr/bin/env python3
"""kden_import: the cut edges Kamil moved in Kdenlive -> the plan's "cut_fix" (cut_fix.py; build_edl.py applies them).

    python3 kden_import.py <project>.kdenlive <work>/plan_<film>.json [--check]

Reads the project (as exported by kden_export.py or as saved by Kdenlive) and <project>.kdenlive.base.json (the cut as
exported). The recording's pieces on the timeline are compared one by one, in order, with the exported ones; an edge on
another frame becomes [old, new] in the plan. Pieces removed or added on the timeline are not imported: the count must
match, else nothing is written and the difference is named (cut or restore whole pieces in the plan's "keeps").
--check prints what would change and writes nothing. The plan before the first import stays as <plan>.before_kden.
"""
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cut_fix


class KdenImportError(ValueError):
    pass


def to_frames(v: str, fps: int) -> int:
    """an MLT time: frames ("123") or a clock ("00:01:02.500")"""
    if ":" not in v: return int(v)
    h, m, s = v.split(":")
    return round((int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))) * fps)


def timeline_pieces(xml_text: str, sources: set[str], fps: int) -> list[tuple[int, int]]:
    """(first frame, frame after the last) of every piece of the recording, from the track that holds the most of them"""
    root = ET.fromstring(xml_text)
    names = {os.path.basename(s) for s in sources}
    res = {}
    for el in root.iter():
        if el.tag in ("producer", "chain"):
            r = next((p.text or "" for p in el.findall("property") if p.get("name") == "resource"), "")
            if os.path.basename(r) in names: res[el.get("id")] = r
    best: list[tuple[int, int]] = []
    for pl in root.iter("playlist"):
        if pl.get("id") == "main_bin": continue
        ents = [(to_frames(e.get("in", "0"), fps), to_frames(e.get("out", "0"), fps) + 1) for e in pl.findall("entry") if e.get("producer") in res]
        if len(ents) > len(best): best = ents
    return best


def moved(base: dict, now: list[tuple[int, int]]) -> list[list[float]]:
    """[old seconds, new seconds] for every edge on another frame than exported"""
    fps, pieces = base["fps"], base["pieces"]
    if len(now) != len(pieces):
        raise KdenImportError(f"the timeline has {len(now)} pieces of the recording, the export had {len(pieces)}: pieces were removed, added "
                           "or split. Only moved edges are imported; undo that on the timeline, or change the plan's keeps and export again")
    out = []
    for k, ((_, b_in, b_out), (n_in, n_out)) in enumerate(zip(pieces, now)):
        if n_in != round(b_in * fps): out.append([b_in, round(n_in / fps, 3)])
        if n_out != round(b_out * fps): out.append([b_out, round(n_out / fps, 3)])
        # two pieces that meet in the recording are one piece split at a chapter start (framing.py), not a cut: build_edl
        # has no edge there to move (pg-review 2026-11-10 data-3)
        if k and pieces[k - 1][0] == pieces[k][0] and abs(pieces[k - 1][2] - b_in) < 1e-6 and (n_in != round(b_in * fps) or now[k - 1][1] != round(b_in * fps)):
            raise KdenImportError(f"the edge at {b_in:.3f} s is a chapter start inside one piece, not a cut: put it back and move the nearest real cut")
    return out


def merged(old_fixes: list[list[float]], new_fixes: list[list[float]]) -> list[list[float]]:
    """the plan's fixes with the new ones: an edge moved before and moved again keeps its first `old` (what build_edl computes)"""
    out = [list(f) for f in old_fixes]
    for old, new in new_fixes:
        prev = next((f for f in out if abs(f[1] - old) <= cut_fix.TOL), None)
        if prev: prev[1] = new
        else: out.append([old, new])
    return [f for f in out if abs(f[0] - f[1]) > 1e-9]


def main(argv: list[str]) -> int:
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if len(args) != 2: print(__doc__); return 2
    proj, plan_p = Path(args[0]), Path(args[1])
    try:
        base = json.loads(Path(str(proj) + ".base.json").read_text(encoding="utf-8"))
        plan = json.loads(plan_p.read_text(encoding="utf-8"))
        now = timeline_pieces(proj.read_text(encoding="utf-8"), {p[0] for p in base["pieces"]}, base["fps"])
        new = moved(base, now)
        fixes = merged(plan.get("cut_fix", []), new)
        cut_fix.check(fixes)
    except (OSError, ValueError, ET.ParseError) as e:
        print(f"kden_import: FAIL {e}"); return 1
    gain = sum((o - n) if any(abs(o - p[1]) < 1e-9 for p in base["pieces"]) else (n - o) for o, n in new)
    print(f"kden_import: {len(new)} cut edge(s) moved, film {gain:+.2f} s; plan cut_fix: {len(fixes)} edge(s)")
    for o, n in new: print(f"  {o:.3f} -> {n:.3f} s")
    if check or not new: return 0
    before, last = Path(str(plan_p) + ".before_kden"), Path(str(plan_p) + ".last_kden")
    if not before.exists(): shutil.copy2(plan_p, before)  # the plan before any import
    shutil.copy2(plan_p, last)                            # the plan before this import
    plan["cut_fix"] = fixes
    tmp = Path(str(plan_p) + ".tmp")  # written whole, then swapped in: a kill mid-write never leaves half a plan
    tmp.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, plan_p)
    print(f"kden_import: wrote {plan_p} (before any import: {before.name}, before this one: {last.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
