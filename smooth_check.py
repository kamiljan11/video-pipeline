"""smooth_check: does the finished film play smoothly, frame after frame?

    python3 smooth_check.py <film.mp4> [--pulse-max 1.8] [--dup-max 1.0]

Kamil 2026-11-22 (U12): "naprawic problem klatkowania co pare sekund video". Measured on the dry3 preview: every x264
keyframe (keyint 250 = 8.33 s) changed the picture 2.3x more than the frames around it (preview crf 30) and the frames
before it froze; the recording itself is clean apart from 48 single frames the phone dropped (0-300 s at 60 fps, then
30 fps). Problems (exit 1):
  - timestamps not constant (a frame shown longer or shorter than 1/fps by more than 1 ms): a stutter in any player
  - keyframe pulse: the median over keyframes that are not cuts of (change into the keyframe / median change of the 12
    frames around it) above --pulse-max (crf 30 preview 2.31, crf 22 preview 1.42, final medium crf 18 1.36)
  - doubled frames: a frame equal to the one before while the picture around it moves, more than --dup-max per minute
The picture is compared at 40x22 grey (motion of the whole frame, not codec noise); a change above CUT is a cut.
"""
import argparse
import json
import subprocess
import sys
from itertools import pairwise

import numpy as np

W, H = 40, 22
CUT = 4.0          # mean grey change per pixel: a cut, not motion
STILL = 0.02       # below this two frames are the same picture
MOVING = 0.3       # the median change around a frame above this = the picture moves
TS_TOL = 0.001     # seconds


def changes(frames: np.ndarray) -> np.ndarray:
    """[n, H, W] grey frames -> n-1 mean absolute changes between neighbours"""
    return np.abs(np.diff(frames.astype(np.float32), axis=0)).mean(axis=(1, 2))


def around(d: np.ndarray, i: int, k: int = 6) -> np.ndarray:
    return np.r_[d[max(0, i - k):i], d[i + 1:i + 1 + k]]


def pulse(d: np.ndarray, keys: list[int]) -> "tuple[float, list[int]]":
    """d = changes, keys = keyframe indices (frame k is reached by change k-1) -> (median ratio, keyframes used)"""
    used, ratios = [], []
    for k in keys:
        i = k - 1
        if i < 6 or i > len(d) - 7 or d[i] >= CUT: continue  # edges and cuts (a cut is a keyframe too) say nothing
        base = float(np.median(around(d, i)))
        if base <= 0.05: continue  # a still picture: any change is a big ratio of nothing
        used.append(k); ratios.append(float(d[i]) / base)
    return (float(np.median(ratios)) if ratios else 0.0), used


def doubled(d: np.ndarray) -> list[int]:
    """frames equal to the one before while the frames around them move"""
    return [i + 1 for i in range(len(d)) if d[i] < STILL and np.median(around(d, i)) > MOVING]


def uneven(ts: list[float], fps: float) -> list[float]:
    """frame times shown longer or shorter than 1/fps"""
    step = 1.0 / fps
    return [round(a, 3) for a, b in pairwise(ts) if abs((b - a) - step) > TS_TOL]


def probe(path: str) -> tuple[float, list[float], list[int]]:
    """-> (fps, frame times, keyframe indices) of the first video stream"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-show_entries", "frame=pts_time,key_frame", "-of", "json", path],
                       capture_output=True, text=True, check=True, timeout=1800)
    j = json.loads(r.stdout); num, den = (int(x) for x in j["streams"][0]["r_frame_rate"].split("/"))
    fr = j["frames"]
    return num / den, [float(f["pts_time"]) for f in fr], [i for i, f in enumerate(fr) if f.get("key_frame") == 1]


def grey(path: str) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-an", "-vf", f"scale={W}:{H}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True, timeout=3600)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="smooth_check: does the finished film play smoothly, frame after frame?")
    ap.add_argument("film"); ap.add_argument("--pulse-max", type=float, default=1.8); ap.add_argument("--dup-max", type=float, default=1.0)
    a = ap.parse_args(argv)
    fps, ts, keys = probe(a.film)
    d = changes(grey(a.film)); mins = max(len(d) / fps / 60, 1e-6)
    bad = []
    if odd := uneven(ts, fps): bad.append(f"{len(odd)} frame(s) not 1/{fps:g} s apart, first at {odd[:5]} s")
    p, used = pulse(d, keys)
    if p > a.pulse_max: bad.append(f"keyframe pulse {p:.2f}x over {len(used)} keyframes > {a.pulse_max}: raise the encode quality (assemble.py SEG_ENC/OUT_ENC)")
    dup = doubled(d)
    if len(dup) / mins > a.dup_max: bad.append(f"{len(dup)} doubled frames ({len(dup) / mins:.1f}/min > {a.dup_max}), first at {[round(i / fps, 2) for i in dup[:5]]} s")
    print(f"smooth_check {a.film}: {fps:g} fps, {len(d) + 1} frames, pulse {p:.2f}x ({len(used)} keyframes), doubled {len(dup)}")
    for b in bad: print(f"FAIL smooth: {b}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
