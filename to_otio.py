#!/usr/bin/env python3
# to_otio.py edl.json out.otio  -> OpenTimelineIO timeline (V1 cuts from source, V2 graphics, A1 audio) for Kdenlive import
import json
import sys
from pathlib import Path

import opentimelineio as otio

edl = json.loads(Path(sys.argv[1]).read_text()); R = 30
rt = lambda s: otio.opentime.RationalTime(round(s * R), R)
tr = lambda a, d: otio.opentime.TimeRange(rt(a), rt(d))
tl = otio.schema.Timeline(name=edl.get("name", "montaz"))
v1 = otio.schema.Track(name="V1 kamera", kind=otio.schema.TrackKind.Video)
a1 = otio.schema.Track(name="A1 dzwiek", kind=otio.schema.TrackKind.Audio)
v2 = otio.schema.Track(name="V2 grafiki", kind=otio.schema.TrackKind.Video)
refs = {k: otio.schema.ExternalReference(target_url="file://" + p) for k, p in edl["sources"].items()}
t = 0.0
for i, s in enumerate(edl["segments"]):
    d = s["out"] - s["in"]
    for trk in (v1, a1):
        c = otio.schema.Clip(name=f"{s['src']}_{i:03d}" + (f" zoom{s.get('zoom',1)}" if s.get("zoom", 1) != 1 else ""),
                             media_reference=otio.schema.ExternalReference(target_url=refs[s["src"]].target_url), source_range=tr(s["in"], d))
        trk.append(c)
    t += d
pos = 0.0
for o in sorted(edl.get("overlays", []), key=lambda o: o["at"]):
    if o["at"] > pos: v2.append(otio.schema.Gap(source_range=tr(0, o["at"] - pos)))
    v2.append(otio.schema.Clip(name=o["file"].split("/")[-1], media_reference=otio.schema.ExternalReference(target_url="file://" + o["file"]),
                               source_range=tr(0, o["dur"])))
    pos = max(pos, o["at"]) + o["dur"]
tl.tracks.extend([v1, v2, a1])
otio.adapters.write_to_file(tl, sys.argv[2])
print("OTIO", sys.argv[2], "len", round(t, 1))
