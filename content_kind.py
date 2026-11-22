"""content_kind.py <work> <plan.json>: is the recording one person talking to the camera ("solo") or two people in one
shot ("talk")? Kamil 2026-11-22: "nasz system ... powinien sam rozpoznawac czy to bedziemy stosowac logiki ... jednej
osoby ... czy ... 2 osob bo wtedy inne logiki powinny wejsc". The answer picks the rule set: build_edl, face_track
(podcast.py framing, ADR-0031) and film_check read it through kind.is_talk(). ADR-0032.

How: "samples" frames spread over the whole recording (style/content_kind.json), OpenCV YuNet (the model face_track.py
uses) at 960x540; a face counts when it is at least "min_face" of the frame height (a poster or a screen in the back is
smaller). "talk" when two faces show in >= "share" of the frames, "solo" when one does. Anything else (a person who
walks out, a screen recording, a dark room) = solo rules, the ones every film had before, with a WARN line and
"clear": false in the file: set "podcast": true / false in the plan by hand then. A plan with "podcast" is not
measured. The answer is kept in <work>/content_kind.json "sources"[src] with the recording's size and mtime
(kind.key), so a second run, and the shorts of the same recording, read it.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

import kind

W, H = 960, 540
ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "face_detection_yunet_2023mar.onnx"
CFG = ROOT / "style" / "content_kind.json"
FFMPEG_S = 60  # one frame grab; a hung ffmpeg on a broken file must not stall a night run


def load_cfg(path: Path = CFG) -> dict:
    c = {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}
    if not (isinstance(c.get("samples"), int) and c["samples"] > 0 and 0 < c.get("min_face", 0) < 1 and 0.5 <= c.get("share", 0) <= 1):
        raise SystemExit(f"content_kind: {path} needs samples > 0, 0 < min_face < 1, 0.5 <= share <= 1, got {c}")
    return c


def classify(counts: list[int], share: float) -> tuple[str, bool]:
    """faces per sampled frame -> (kind, clear); not clear = ("solo", False)"""
    if not counts: raise SystemExit("content_kind: no frame was read")
    two, one = sum(c >= 2 for c in counts) / len(counts), sum(c == 1 for c in counts) / len(counts)
    if two >= share: return "talk", True
    if one >= share: return "solo", True
    return "solo", False


def big_faces(dets, min_face: float) -> int:
    """YuNet detections [[x, y, w, h, ...]] in pixels of W x H -> how many are big enough to be a person in the shot"""
    return 0 if dets is None else sum(1 for d in dets if float(d[3]) / H >= min_face)


def times(dur: float, n: int) -> list[float]:
    """n times spread evenly over a recording of dur seconds (the middle of n equal parts)"""
    return [round((k + 0.5) * dur / n, 3) for k in range(n)]


def duration(src: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                       capture_output=True, text=True, check=False, timeout=FFMPEG_S)
    try: return float(r.stdout.strip())
    except ValueError: raise SystemExit(f"content_kind: ffprobe gave no duration for {src}: {r.stderr[-200:]}") from None


def frame(src: Path, t: float):
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-an",
                            "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           capture_output=True, check=False, timeout=FFMPEG_S)
    except subprocess.TimeoutExpired: raise SystemExit(f"content_kind: ffmpeg hung over {FFMPEG_S} s on {src} at {t:.1f}s") from None
    if r.returncode != 0 or len(r.stdout) < W * H * 3:
        raise SystemExit(f"content_kind: ffmpeg gave no frame of {src} at {t:.1f}s: {r.stderr.decode(errors='replace')[-200:]}")
    return np.frombuffer(r.stdout[:W * H * 3], np.uint8).reshape(H, W, 3)


def write(out: Path, src: str, entry: dict) -> None:
    """add the recording's entry to content_kind.json, atomically (a cut-off file must never be read half)"""
    m = json.loads(out.read_text()) if out.is_file() else {}
    if not isinstance(m.get("sources"), dict): m = {"sources": {}}
    m["sources"][src] = entry
    tmp = out.with_suffix(".json.tmp"); tmp.write_text(json.dumps(m, indent=1) + "\n"); os.replace(tmp, out)


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    work = Path(argv[0]); plan = json.loads((work / argv[1]).read_text())
    if kind.from_plan(plan) is not None:  # set by hand: kind.is_talk reads the plan first, nothing to measure
        print(f"content_kind: skipped, the plan says \"podcast\": {json.dumps(plan['podcast'])[:40]}"); return 0
    key, out = kind.key(work, plan), work / "content_kind.json"
    try: old = kind.measured(work, plan)
    except SystemExit: old = None  # stale or broken: measure again and overwrite
    if old is not None: print(f"content_kind: {old['kind']} (cached, {out.name})"); return 0
    cfg, src = load_cfg(), work / plan["src"]
    import cv2
    yn = cv2.FaceDetectorYN.create(str(MODEL), "", (W, H), 0.6)
    ts = times(duration(src), cfg["samples"])
    counts = [big_faces(yn.detect(frame(src, t))[1], cfg["min_face"]) for t in ts]
    k, clear = classify(counts, cfg["share"])
    write(out, plan["src"], {"kind": k, "clear": clear, "faces": counts, "times": ts, "key": key})
    if not clear:
        hist = {c: counts.count(c) for c in sorted(set(counts))}
        print(f"WARN content_kind: not clear (faces per frame {hist} over {len(counts)} frames, need {cfg['share']:.0%} "
              "with 1 or 2) -> solo rules; set \"podcast\": true (two people) or false (one) in the plan to decide")
    print(f"content_kind: {k} (faces per frame {counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
