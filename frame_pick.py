#!/usr/bin/env python3
"""frame_pick: the best still of the speaker in a time window, for thumbnails, Short covers and post pictures.

    python3 frame_pick.py <video> <t0> <t1> [--crop W:H:X:Y] [--top 6] [--sheet sheet.jpg] [--out best.png] [--json]

Kamil 2026-11-08: "na thumbaile i screeny wybierasz bardzo nie korzystne zdjecia ... brzydkie czasami rozmazane",
"glupie miny wybierasz". build_pack_v2.py took ONE frame (a word start + 0.15 s): long A had the mouth round mid-word,
long B half-shut eyes and a blurred hand, cover s01 squinting eyes. Here every 0.1 s of the window is scored on the face
YuNet finds (5 landmarks: eyes, nose tip, mouth corners):
  sharp   Laplacian variance of the face box (blur from motion or focus)
  still   1 - the frame's difference to the sample before (a hand or the head in motion)
  eyes    contrast inside both eye boxes (an open eye has iris + white; a shut or squinting one is flat skin)
  mouth   closed or smiling: the dark share between the mouth corners (an open, talking mouth is dark) and the mouth
          width against the eye distance (a round "o" is narrow, a smile wide)
  front   the nose tip between the eyes and level eyes (a turned or tilted head reads badly at feed size)
Each measure is scaled to the window (its BEST_PCT percentile = 1, capped), a sample below EYES_MIN or SHARP_MIN of the window's best is
dropped, the rest ranked by WEIGHTS. --sheet writes the top N side by side with their scores: look at it before use.
"""
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

FACE_MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
FPS = 10           # samples per second in the window
WIDTH = 1280       # samples are scaled to this width (2560 recordings: half)
WEIGHTS = {"sharp": 0.25, "eyes": 0.3, "mouth": 0.2, "still": 0.15, "front": 0.1}
EYES_MIN, SHARP_MIN = 0.7, 0.6  # of the window's best: below = not a candidate (shut eyes, blur)
BEST_PCT = 90      # percentile of the window that counts as its best (scores above it are capped at 1)
MIN_GAP = 0.5      # s between two candidates of the top list (not 6 copies of one moment)


@dataclass
class Cand:
    t: float
    score: float
    sharp: float
    eyes: float
    mouth: float
    still: float
    front: float
    raw: dict


def frames(video: str, t0: float, t1: float, crop: str | None):
    """(t, BGR frame) every 1/FPS s from t0 to t1, scaled to WIDTH"""
    vf = ([f"crop={crop}"] if crop else []) + [f"fps={FPS}", f"scale={WIDTH}:-2"]
    probe = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", "0.05", "-i", video, "-vf", ",".join(vf),
                            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True, timeout=120)
    first = cv2.imdecode(np.frombuffer(probe.stdout, np.uint8), cv2.IMREAD_COLOR)
    if first is None: raise RuntimeError(f"{video}: no frame at {t0:.2f} s")
    h, w = first.shape[:2]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", video, "-vf", ",".join(vf),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    assert p.stdout is not None
    n, size = 0, w * h * 3
    try:
        while (buf := p.stdout.read(size)) and len(buf) == size:
            yield t0 + n / FPS, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
            n += 1
    finally:
        p.stdout.close(); p.wait(timeout=60)


def detector(w: int, h: int):
    if not FACE_MODEL.is_file(): raise FileNotFoundError(f"face model missing: {FACE_MODEL}")
    return cv2.FaceDetectorYN.create(str(FACE_MODEL), "", (w, h), 0.7)


def box(gray: np.ndarray, cx: float, cy: float, half_w: float, half_h: float) -> np.ndarray:
    h, w = gray.shape
    x0, x1 = int(max(cx - half_w, 0)), int(min(cx + half_w, w))
    y0, y1 = int(max(cy - half_h, 0)), int(min(cy + half_h, h))
    return gray[y0:y1, x0:x1]


def measure(img: np.ndarray, prev: np.ndarray | None, det) -> dict | None:
    """raw measures of one frame; None without a face"""
    _, faces = det.detect(img)
    if faces is None or not len(faces): return None
    f = max(faces, key=lambda r: r[2] * r[3])  # the biggest face: the speaker
    x, y, fw, fh = f[:4]
    (rex, rey), (lex, ley), (nx, ny), (mrx, mry), (mlx, mly) = f[4:14].reshape(5, 2)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    face = box(gray, x + fw / 2, y + fh / 2, fw / 2, fh / 2)
    eye_d = float(np.hypot(lex - rex, ley - rey)) or 1.0
    eyes = [box(gray, ex, ey, eye_d * 0.22, eye_d * 0.13) for ex, ey in ((rex, rey), (lex, ley))]
    eye_c = min(float(np.percentile(e, 95) - np.percentile(e, 5)) if e.size else 0.0 for e in eyes)
    mw = float(np.hypot(mlx - mrx, mly - mry))
    mouth = box(gray, (mrx + mlx) / 2, (mry + mly) / 2, mw * 0.35, mw * 0.18)
    cheek = box(gray, nx, (ny + (mry + mly) / 2) / 2, mw * 0.3, mw * 0.08)  # skin between the nose and the lips
    skin = float(np.median(cheek)) if cheek.size else float(np.median(face))
    dark = float((mouth < 0.55 * skin).mean()) if mouth.size else 1.0
    still = 1.0 if prev is None else 1.0 - min(float(np.abs(gray - prev).mean()) / 12.0, 1.0)
    off = abs(nx - (rex + lex) / 2) / eye_d + abs(ley - rey) / eye_d
    return {"sharp": float(cv2.Laplacian(face, cv2.CV_32F).var()) if face.size else 0.0, "eyes": eye_c,
            "dark": dark, "smile": mw / eye_d, "still": still, "off": float(off), "face_h": float(fh / img.shape[0]), "gray": gray}


def pick(video: str, t0: float, t1: float, crop: str | None = None) -> list[Cand]:
    """every sample with a face, ranked; samples under EYES_MIN / SHARP_MIN of the window's best are left out"""
    raw, prev, det = [], None, None
    for t, img in frames(video, t0, t1, crop):
        if det is None: det = detector(img.shape[1], img.shape[0])
        m = measure(img, prev, det)
        prev = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if m: m.pop("gray"); raw.append((t, m))
    if not raw: return []
    # the window's "best" = its 90th percentile, not its maximum: one blurred frame with a high eye-box contrast (a hand or
    # the head in motion) would set the bar so that no sharp frame reached EYES_MIN (s03 cover, 2026-11-08: 152 faces, 0 kept)
    best = {k: float(np.percentile([m[k] for _, m in raw], BEST_PCT)) or 1.0 for k in ("sharp", "eyes", "smile")}
    out = []
    for t, m in raw:
        s = {"sharp": min(m["sharp"] / best["sharp"], 1.0), "eyes": min(m["eyes"] / best["eyes"], 1.0), "still": m["still"],
             "mouth": 0.6 * (1.0 - min(m["dark"] / 0.25, 1.0)) + 0.4 * min(m["smile"] / best["smile"], 1.0),
             "front": max(0.0, 1.0 - m["off"] / 0.35)}
        if s["eyes"] < EYES_MIN or s["sharp"] < SHARP_MIN: continue
        r3 = {k: round(v, 3) for k, v in s.items()}
        out.append(Cand(round(t, 2), round(sum(WEIGHTS[k] * s[k] for k in WEIGHTS), 3), r3["sharp"], r3["eyes"], r3["mouth"],
                        r3["still"], r3["front"], {k: round(v, 3) for k, v in m.items()}))
    return sorted(out, key=lambda c: -c.score)


def top(cands: list[Cand], n: int) -> list[Cand]:
    """the n best, at least MIN_GAP apart"""
    got: list[Cand] = []
    for c in cands:
        if all(abs(c.t - g.t) >= MIN_GAP for g in got): got.append(c)
        if len(got) == n: break
    return got


def grab(video: str, t: float, out: str, crop: str | None = None, scale: str | None = None) -> None:
    vf = ",".join(([f"crop={crop}"] if crop else []) + ([f"scale={scale}:flags=lanczos"] if scale else []))
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", *(["-vf", vf] if vf else []), "-y", out],
                   check=True, timeout=120)


def sheet(video: str, cands: list[Cand], out: str, crop: str | None = None) -> None:
    """the candidates side by side, each with its time and scores, for a look before use"""
    tiles = []
    for c in cands:
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{c.t:.3f}", "-i", video, "-frames:v", "1", "-vf",
                            ",".join(([f"crop={crop}"] if crop else []) + ["scale=-2:360"]), "-f", "image2pipe", "-vcodec", "png", "-"],
                           capture_output=True, check=True, timeout=120).stdout
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
        if im is None: continue
        for i, line in enumerate((f"{c.t:.1f}s  {c.score:.2f}", f"e{c.eyes:.2f} s{c.sharp:.2f} m{c.mouth:.2f} st{c.still:.2f}")):
            cv2.putText(im, line, (8, 24 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
            cv2.putText(im, line, (8, 24 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        tiles.append(im)
    if tiles: cv2.imwrite(out, np.hstack(tiles))


def main(argv: list[str]) -> int:
    def opt(name: str, default: str | None = None) -> str | None:
        return argv[argv.index(name) + 1] if name in argv else default
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    if len(pos) != 3: print(__doc__, file=sys.stderr); return 2
    video, t0, t1 = pos[0], float(pos[1]), float(pos[2])
    crop, n = opt("--crop"), int(opt("--top", "6") or 6)
    best = top(pick(video, t0, t1, crop), n)
    if not best: print(f"frame_pick: no sharp frame with open eyes in {t0}-{t1} s", file=sys.stderr); return 1
    if s := opt("--sheet"): sheet(video, best, s, crop)
    if o := opt("--out"): grab(video, best[0].t, o, crop)
    if "--json" in argv: print(json.dumps([asdict(c) for c in best], ensure_ascii=False))
    else:
        for c in best: print(f"{c.t:8.2f} s  score {c.score:.3f}  eyes {c.eyes:.2f} sharp {c.sharp:.2f} mouth {c.mouth:.2f} still {c.still:.2f} front {c.front:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
