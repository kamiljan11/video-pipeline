"""podcast_faces.py: the two faces of a podcast wide shot and who is talking, from the picture alone (CPU, no new model).

- Both faces: OpenCV YuNet (the same model as face_track.py) on frames scaled to 960x540, the two largest faces sorted by
  x = "L" (left of the frame) and "R". A frame with one face gives it to the side whose last box is nearer.
- Who talks: mouth motion. Per frame, the mean absolute difference of the lower part of each face box against the frame
  before; each side is divided by its own median (a beard, a bigger face or a closer seat must not win by itself). A word
  goes to the side whose mouth moved more over the word by at least mouth_ratio (style/podcast.json), else "?".
This is a lip-motion heuristic, not a trained active-speaker model (research/podcast: TalkNet / Light-ASD are MIT but have
no measured CPU speed): podcast_fix.json in the work folder overrides any stretch by hand, and the report counts the "?".
"""
import json
import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np

W, H = 960, 540  # analysis frame: two faces of a 4K wide shot are still ~60-100 px wide here (640x360 is too small)
MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
WINDOW_S = 10.0  # one face box per side per window of the recording
STALL_S = 120.0  # seconds without a frame before ffmpeg counts as hung (a 4K seek can be slow)


def two_faces(faces, last=None):
    """detections [[x, y, w, h, ...], ...] in pixels of W x H -> {"L": box, "R": box} normalised (x, y, w, h); a missing
    side is absent. One face: the side whose last known box centre is nearer (no history: by which half it is in)."""
    fs = sorted((list(map(float, f[:4])) for f in (faces if faces is not None else [])), key=lambda b: -b[2] * b[3])[:2]
    fs = [[b[0] / W, b[1] / H, b[2] / W, b[3] / H] for b in fs]
    if len(fs) == 2:
        a, b = sorted(fs, key=lambda b: b[0] + b[2] / 2)
        return {"L": a, "R": b}
    if len(fs) == 1:
        c = fs[0][0] + fs[0][2] / 2
        if last and "L" in last and "R" in last:
            dl = abs(c - (last["L"][0] + last["L"][2] / 2)); dr = abs(c - (last["R"][0] + last["R"][2] / 2))
            return {"L" if dl <= dr else "R": fs[0]}
        return {"L" if c < 0.5 else "R": fs[0]}
    return {}


def mouth_box(box):
    """the mouth part of a face box (normalised x, y, w, h): the lower 45 % and the middle 60 % of its width, a little
    under the chin line (an open mouth goes below the detector's box)"""
    x, y, w, h = box
    return (x + 0.2 * w, y + 0.6 * h, 0.6 * w, 0.5 * h)


def roi(gray, box):
    x, y, w, h = mouth_box(box)
    x0, y0 = max(0, int(x * W)), max(0, int(y * H)); x1, y1 = min(W, int((x + w) * W)), min(H, int((y + h) * H))
    return gray[y0:y1, x0:x1] if x1 - x0 >= 4 and y1 - y0 >= 4 else None


def motion(prev, cur, box):
    a, b = roi(prev, box), roi(cur, box)
    if a is None or b is None or a.shape != b.shape: return None
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))))


def frames(src, t0, dur, fps):
    """BGR frames W x H of the recording from t0 for dur seconds at fps (one ffmpeg, no seeking per frame). A failed
    ffmpeg or a stretch that gives far fewer frames than asked stops with a named error: half-measured samples would be
    cached as if they were whole (podcast.py)."""
    with tempfile.TemporaryFile() as err:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{t0:.3f}", "-i", str(src), "-t", f"{dur:.3f}", "-an",
                              "-vf", f"fps={fps},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                             stdout=subprocess.PIPE, stderr=err)
        n = W * H * 3; k = 0
        out = p.stdout
        if out is None: raise SystemExit("podcast_faces: ffmpeg started without a stdout pipe")
        stalled = threading.Event()

        def stall():  # a hung read never returns on its own: killing ffmpeg closes the pipe
            stalled.set(); p.kill()

        watch = None
        try:
            while True:
                watch = threading.Timer(STALL_S, stall); watch.start()  # armed only while waiting on ffmpeg, not on the caller
                buf = out.read(n)
                watch.cancel()
                if len(buf) < n: break
                yield t0 + k / fps, np.frombuffer(buf, np.uint8).reshape(H, W, 3); k += 1
            rc = p.wait(timeout=STALL_S)
        except subprocess.TimeoutExpired:
            stalled.set(); rc = None
        finally:
            if watch is not None: watch.cancel()
            if p.poll() is None: p.kill(); p.wait()
        err.seek(0); msg = err.read().decode(errors="replace").strip()[-300:]
        if stalled.is_set(): raise SystemExit(f"podcast_faces: ffmpeg gave no frame for {STALL_S:.0f}s on {src} at {t0:.1f}s: {msg}")
        if rc != 0: raise SystemExit(f"podcast_faces: ffmpeg failed on {src} at {t0:.1f}s (exit {rc}): {msg}")
        if k < 0.9 * dur * fps - 2: raise SystemExit(f"podcast_faces: {src} at {t0:.1f}s gave {k} frames, expected ~{dur * fps:.0f}: {msg}")


def analyse(src, ranges, cfg, detector=None):
    """ranges [[t0, t1], ...] (recording seconds) -> samples [[t, mL|None, mR|None], ...] and boxes {"t0-t1": {"L", "R"}}
    (median box per side over the range). detector(frame) -> detections; default YuNet."""
    import cv2
    if detector is None:
        yn = cv2.FaceDetectorYN.create(str(MODEL), "", (W, H), 0.6)
        detector = lambda fr: yn.detect(fr)[1]
    samples, boxes = [], {}
    fps, every = cfg["detect_fps"], max(1, round(cfg["face_every_s"] * cfg["detect_fps"]))
    for t0, t1 in ranges:
        cur, seen, prev = {}, {}, None
        for k, (t, fr) in enumerate(frames(src, t0, t1 - t0, fps)):
            if k % every == 0:
                got = two_faces(detector(fr), cur or None)
                cur.update(got)
                w = int((t - t0) // WINDOW_S)  # boxes per window: a person who leans or moves is framed where they are now
                for s, b in got.items(): seen.setdefault(w, {"L": [], "R": []})[s].append(b)
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            if prev is not None:
                samples.append([round(t, 3)] + [motion(prev, g, cur[s]) if s in cur else None for s in ("L", "R")])
            prev = g
        for w, sides in seen.items():
            a, b = t0 + w * WINDOW_S, min(t1, t0 + (w + 1) * WINDOW_S)
            boxes[f"{a:.3f}-{b:.3f}"] = {s: [round(float(v), 4) for v in np.median(np.array(bs), axis=0)] for s, bs in sides.items() if bs}
    return samples, boxes


def word_speakers(words, samples, ratio):
    """one "L" / "R" / "?" per word from the mouth-motion samples (each side divided by its own median)"""
    arr = np.array([[t, np.nan if a is None else a, np.nan if b is None else b] for t, a, b in samples], dtype=float).reshape(-1, 3)
    if not len(arr): return ["?"] * len(words)
    med = [_scale(arr[:, i]) for i in (1, 2)]
    out = []
    for a, b, _ in words:
        m = arr[(arr[:, 0] >= a) & (arr[:, 0] <= b + 1e-6)]
        if not len(m): out.append("?"); continue
        lv, rv = (np.nanmean(m[:, i]) / med[i - 1] if not np.isnan(med[i - 1]) and np.any(~np.isnan(m[:, i])) else np.nan for i in (1, 2))
        out.append(_pick(lv, rv, ratio))
    return out


def _scale(col):
    """a side's typical mouth motion (median; mean when the mouth is still most of the time, else 1): never 0, so a side
    that was seen is never taken for unseen"""
    seen = col[~np.isnan(col)]
    if not len(seen): return np.nan
    m = float(np.median(seen))
    return m if m > 0 else (float(np.mean(seen)) or 1.0)


def _pick(lv, rv, ratio):
    """the side whose (normalised) mouth moved ratio times more; one side unseen = the seen side; else a question mark"""
    if np.isnan(lv) and np.isnan(rv): return "?"
    if np.isnan(rv): return "L"
    if np.isnan(lv): return "R"
    return "L" if lv >= ratio * rv else "R" if rv >= ratio * lv else "?"


def apply_fix(words, spk, fix):
    """podcast_fix.json [[t0, t1, "L"|"R"], ...]: every word whose middle is inside a stretch gets that speaker"""
    spk = list(spk)
    for row, (t0, t1, s) in enumerate(fix, 1):
        if s not in ("L", "R"): raise SystemExit(f"podcast_fix.json row {row}: speaker must be \"L\" or \"R\", got {s!r}")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (t0, t1)) or not t0 < t1:
            raise SystemExit(f"podcast_fix.json row {row}: t0 < t1 in recording seconds, got {t0!r}, {t1!r}")
        for i, (a, b, _) in enumerate(words):
            if t0 <= (a + b) / 2 < t1: spk[i] = s
    return spk


def load_fix(work):
    f = Path(work) / "podcast_fix.json"
    if not f.is_file(): return []
    v = json.loads(f.read_text())
    if not (isinstance(v, list) and all(isinstance(x, list) and len(x) == 3 for x in v)):
        raise SystemExit(f"{f}: expected [[t0, t1, \"L\"|\"R\"], ...]")
    return v
