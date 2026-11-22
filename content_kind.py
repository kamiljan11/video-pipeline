"""content_kind.py <work> <plan.json>: is the recording one person talking to the camera ("solo") or two people in one
shot ("talk")? Kamil 2026-11-22: "nasz system ... powinien sam rozpoznawac czy to bedziemy stosowac logiki ... jednej
osoby ... czy ... 2 osob bo wtedy inne logiki powinny wejsc". The answer picks the rule set: build_edl, face_track
(podcast.py framing, ADR-0031) and film_check read it through kind.is_talk().

How: SAMPLES frames spread over the kept part of the recording, OpenCV YuNet (the model face_track.py uses) at 960x540;
a face counts when it is at least MIN_FACE of the frame height (a poster or a screen in the back is smaller). "talk" when
two faces show in >= SHARE of the frames, "solo" when one does; anything else stops with the counts (a person who walks
out, a dark room): set "podcast": true / false in the plan by hand then. The result is cached in <work>/content_kind.json
with the recording's size and mtime, so a second run reads it.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 960, 540
MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
SAMPLES, MIN_FACE, SHARE = 24, 0.08, 0.6
VERSION = 1


def classify(counts: list[int], share: float = SHARE) -> str:
    """faces per sampled frame -> "talk" | "solo"; SystemExit with the histogram when neither holds"""
    if not counts: raise SystemExit("content_kind: no frame was read")
    two, one = sum(c >= 2 for c in counts) / len(counts), sum(c == 1 for c in counts) / len(counts)
    if two >= share: return "talk"
    if one >= share: return "solo"
    hist = {k: counts.count(k) for k in sorted(set(counts))}
    raise SystemExit(f"content_kind: not clear (faces per frame {hist} over {len(counts)} frames, need {share:.0%} with 1 or 2): "
                     "set \"podcast\": true (two people) or false (one) in the plan")


def big_faces(dets, min_face: float = MIN_FACE) -> int:
    """YuNet detections [[x, y, w, h, ...]] in pixels of W x H -> how many are big enough to be a person in the shot"""
    return 0 if dets is None else sum(1 for d in dets if float(d[3]) / H >= min_face)


def times(plan: dict, words: list, n: int = SAMPLES) -> list[float]:
    """n recording times spread over the plan's keeps (word index ranges into words: [(t0, t1, text)]), else over all words"""
    spans = [(words[a][0], words[min(b, len(words) - 1)][1]) for a, b in plan.get("keeps", [])] or [(words[0][0], words[-1][1])]
    total = sum(b - a for a, b in spans)
    out, acc, k = [], 0.0, 0
    for a, b in spans:
        while k < n and (k + 0.5) * total / n <= acc + (b - a):
            out.append(round(a + (k + 0.5) * total / n - acc, 3)); k += 1
        acc += b - a
    return out


def frame(src: Path, t: float):
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-an",
                        "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=False)
    if r.returncode != 0 or len(r.stdout) < W * H * 3:
        raise SystemExit(f"content_kind: ffmpeg gave no frame of {src} at {t:.1f}s: {r.stderr.decode(errors='replace')[-200:]}")
    return np.frombuffer(r.stdout[:W * H * 3], np.uint8).reshape(H, W, 3)


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    work, plan_file = Path(argv[0]), Path(argv[0]) / argv[1]
    plan = json.loads(plan_file.read_text())
    if "podcast" in plan:  # set by hand: kind.is_talk reads the plan first, nothing to measure (and an unclear recording must not stop it)
        print(f"content_kind: skipped, the plan says \"podcast\": {json.dumps(plan['podcast'])[:40]}"); return 0
    src = work / plan["src"]; out = work / "content_kind.json"
    st = src.stat(); key = {"src": plan["src"], "size": st.st_size, "mtime": int(st.st_mtime), "version": VERSION}
    if out.is_file():
        old = json.loads(out.read_text())
        if old.get("key") == key: print(f"content_kind: {old['kind']} (cached, {out.name})"); return 0
    words = [(x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000, x["text"]) for x in json.loads((work / plan["words"]).read_text())["transcription"]]
    import cv2
    yn = cv2.FaceDetectorYN.create(str(MODEL), "", (W, H), 0.6)
    ts = times(plan, words)
    counts = [big_faces(yn.detect(frame(src, t))[1]) for t in ts]
    kind = classify(counts)
    out.write_text(json.dumps({"kind": kind, "faces": counts, "times": ts, "key": key}, indent=1) + "\n")
    print(f"content_kind: {kind} (faces per frame {counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
