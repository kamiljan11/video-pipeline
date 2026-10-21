#!/usr/bin/env python3
"""head_check.py video.mp4 [edl.json] [step_s]  — C10: is the head fully inside the frame in the FINAL render?
Samples a frame every step seconds, detects the face (YuNet), grows the box for hair/chin and flags frames where the
head touches the frame edge (<1.5% margin). Skips times covered by full-screen cards (chap/slide/end) and stock b-roll
when edl given."""
import json
import sys
from pathlib import Path

import cv2

v = sys.argv[1]; edl = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else None
step = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
skip = []
if edl:
    specs = {}
    try: specs = {s["id"]: s for s in json.loads(Path(edl["gfx_specs"]).read_text())}
    except (OSError, ValueError, KeyError, TypeError): pass  # no specs file (or gfx_specs null): no graphics to skip
    skip = [(o["at"], o["at"] + o["dur"]) for o in edl.get("overlays", []) if specs.get(o["id"], {}).get("type") in ("chap", "slide", "end")]
    skip += [(b["at"], b["at"] + b["dur"]) for b in edl.get("broll", [])]  # stock b-roll: full frame, no speaker
cap = cv2.VideoCapture(v); W = cap.get(3); H = cap.get(4); n = cap.get(7); fps = cap.get(5) or 30; dur = n / fps
sw, sh = (360, 640) if H > W else (640, 360)
det = cv2.FaceDetectorYN.create("/home/kamil-jan/video-pipeline/models/face_detection_yunet_2023mar.onnx", "", (sw, sh), 0.6)
bad, none, checked = [], [], 0; t = 0.5
while t < dur - 0.5:
    if not any(a - 0.3 <= t <= b + 0.3 for a, b in skip):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
        if ok:
            checked += 1; _, f = det.detect(cv2.resize(fr, (sw, sh)))
            if f is None or not len(f): none.append(round(t, 1))
            else:
                x, y, w, h = max(f, key=lambda q: q[2] * q[3])[:4] / [sw, sh, sw, sh]
                hx0, hy0, hx1, hy1 = x - 0.15 * w, y - 0.45 * h, x + w * 1.15, y + h * 1.25
                if min(hx0, hy0, 1 - hx1) < 0.015: bad.append((round(t, 1), round(hx0, 3), round(hy0, 3), round(1 - hx1, 3)))
    t += step
print(f"C10 {v.split('/')[-1]}: sprawdzono {checked} klatek, głowa przy krawędzi: {len(bad)}, brak twarzy: {len(none)}")
for b in bad[:15]: print("  krawędź t={:.1f}s (lewo {:.3f}, góra {:.3f}, prawo {:.3f})".format(*b))
if none: print("  brak twarzy t=", none[:20])
