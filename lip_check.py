#!/usr/bin/env python3
"""lip_check: are the lips and the voice of the finished film together, as they were in the recording?

    python3 lip_check.py <edl.json> <final.mp4> [--max-ms 45] [--median-ms 20]

Kamil 2026-11-09 "dalej long ma opoznienie i to jeszcze wieksze": every gate was green (sync_check compares the cut's
SOUND with the plan, av_check the voice packets), none compared the PICTURE with the sound. Measured on film 2026-11-04:
the voice 40 ms late (afftdn 25 ms + three 5 ms limiter look-aheads) and the picture 0-33 ms early on half the pieces
(cut at `-ss in` while the recording's frames sit at 0.033 + k/30) = up to 73 ms, two frames.

For every piece with no card over it (>= MIN_LEN s; with fewer than MIN_PIECES of those, every piece, cards or not): the recording's picture motion (mean frame difference, 96x54 gray)
is found in the film's picture near the planned time, and the recording's voice envelope in the film's sound. desync =
sound lag - picture lag (> 0: the voice after the lips). Only pieces where both match well (r >= R_MIN) count; a zoom
or a crop that changes the motion lowers r and the piece is left out, said, never guessed.

Problems (exit 1): median desync over --median-ms, any counted piece over --max-ms, or pieces there but none counted (fewer
than MIN_PIECES counted = WARN; no piece of MIN_LEN s at all = WARN). run_v4.sh: LIP_CHECK=off skips it, logged.
"""
import json
import subprocess
import sys

import numpy as np

import timeline
from av_latency import video_start
from sync_check import envelope

FPS = timeline.FPS
MIN_LEN = 2.0  # s of a piece with nothing over it
R_MIN = 0.8
MIN_PIECES = 3  # fewer counted = WARN only: a short has 1-3 pieces without cards, and the fault measured (filters, cut grid)
#                 is the pipeline's, the same in every piece (film 2026-11-04: +40 ms sound in all 16 pieces of the long)
SEARCH = 0.5  # s each side of the planned time
PIECES_MAX = 24  # spread over the film: enough for a median, a long is checked in minutes


def motion(path: str, ss: float, t: float) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(ss, 0):.3f}", "-i", path, "-t", f"{t:.3f}", "-an",
                          "-vf", f"fps={FPS},scale=96:54,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True, timeout=600).stdout
    f = np.frombuffer(raw, np.uint8)[: len(raw) // (54 * 96) * 54 * 96].reshape(-1, 54, 96).astype(np.float32)
    return np.abs(np.diff(f, axis=0)).mean(axis=(1, 2)) if len(f) > 1 else np.zeros(0)


def lag(a: np.ndarray, b: np.ndarray, max_lag: int, rate: float) -> tuple[float, float]:
    """(ms, r): where a sits in b, b starting max_lag samples early; parabolic refinement between samples"""
    if len(a) < 3 or a.std() == 0 or len(b) < len(a): return 0.0, 0.0
    a = (a - a.mean()) / a.std()
    cs = []
    for k in range(2 * max_lag + 1):
        seg = b[k:k + len(a)]
        if len(seg) < len(a): break
        cs.append(float((a * (seg - seg.mean()) / (seg.std() + 1e-9)).mean()))
    c = np.array(cs); k = float(c.argmax()); i = int(k)
    if 0 < i < len(c) - 1 and (d := c[i - 1] - 2 * c[i] + c[i + 1]):
        k = i + 0.5 * (c[i - 1] - c[i + 1]) / d
    return (k - max_lag) / rate * 1000, float(c.max())


def pieces(edl: dict) -> list[tuple[int, float]]:
    """(segment index, film start) of the pieces with nothing over them, spread over the film; with fewer than MIN_PIECES
    of those, every piece of MIN_LEN s, cards or not, and the match (r >= R_MIN) decides which count.
    2026-11-14: the 2026-11-04 long has cards over 1073 of its 1086 s, so it had 0 pieces and lip_check said OK for every
    long since v5 without measuring; with the cards, 16 of 24 pieces of that long matched (median -18 ms)"""
    segs = edl["segments"]; ex = bool(edl.get("seg_exact")); st = timeline.starts(segs, ex)
    cov = [(o["at"], o["at"] + o["dur"]) for o in edl.get("overlays", [])]
    long_enough = [i for i, s in enumerate(segs) if timeline.piece_len(s, ex) >= MIN_LEN]
    ok = [i for i in long_enough if not any(a < st[i] + timeline.piece_len(segs[i], ex) and b > st[i] for a, b in cov)]
    if len(ok) < MIN_PIECES: ok = long_enough
    pick = sorted({ok[int(j)] for j in np.linspace(0, len(ok) - 1, min(PIECES_MAX, len(ok)))}) if ok else []
    return [(i, st[i]) for i in pick]


def measure(edl: dict, film: str) -> list[dict]:
    """picture_ms / sound_ms: where the recording's moment in + 0.2 s shows up in the film vs the plan (t0 + 0.2 s)"""
    out = []; fv0 = video_start(film)
    for i, t0 in pieces(edl):
        s = edl["segments"][i]; src = edl["sources"][s["src"]]
        L = timeline.piece_len(s, bool(edl.get("seg_exact"))) - 0.4
        ref, want = s["in"] + 0.2, t0 + 0.2 - SEARCH  # want < 0 on the film's first piece: the window starts at 0
        # frame differences cannot see where inside a frame a window starts: both windows start ON a frame and the
        # offsets of those frames from the asked times are added back (film 2026-11-04: frames at 0.033 + k/30)
        rs, fs = timeline.snap_in(ref, video_start(src)), timeline.snap_in(max(want, 0.0), fv0)
        pl, pr = lag(motion(src, rs, L), motion(film, fs, L + 2 * SEARCH), int(SEARCH * FPS), FPS)
        pl += ((fs - want) - (rs - ref)) * 1000
        ws = max(want, 0.0)
        sl, sr = lag(envelope(src, ref, L), envelope(film, ws, L + 2 * SEARCH), int(SEARCH * 1000), 1000)
        sl += (ws - want) * 1000
        out.append({"t": round(t0, 2), "picture_ms": round(float(pl), 1), "r_picture": round(pr, 2), "sound_ms": round(float(sl), 1),
                    "r_sound": round(sr, 2), "desync_ms": round(float(sl - pl), 1)})
    return out


def judge(rows: list[dict], max_ms: float, median_ms: float) -> list[str]:
    good = [r for r in rows if r["r_picture"] >= R_MIN and r["r_sound"] >= R_MIN]
    if not rows:  # no piece of MIN_LEN s at all: nothing to compare, said in main, no FAIL
        return []
    if not good:  # pieces there, none matched: a zoom or crop changed the motion, or picture and sound are off
        return [f"lips not measurable: 0 of {len(rows)} pieces matched (r >= {R_MIN}); rows above, LIP_CHECK=off with a reason to skip"]
    bad = []
    med = float(np.median([r["desync_ms"] for r in good]))
    if abs(med) > median_ms: bad.append(f"voice {'after' if med > 0 else 'before'} the lips by {abs(med):.0f} ms (median of {len(good)} pieces)")
    bad += [f"{r['t']:.2f} s: voice {'after' if r['desync_ms'] > 0 else 'before'} the lips by {abs(r['desync_ms']):.0f} ms"
            for r in good if abs(r["desync_ms"]) > max_ms]
    return bad


def _opt(args: list[str], name: str, default: float) -> float:
    """--name value: taken out of args"""
    if name not in args: return default
    i = args.index(name); v = float(args[i + 1]); del args[i:i + 2]
    return v


def main(argv: list[str]) -> int:
    args = list(argv)
    max_ms, median_ms = _opt(args, "--max-ms", 45.0), _opt(args, "--median-ms", 20.0)
    if len(args) != 2: print(__doc__, file=sys.stderr); return 2
    with open(args[0], encoding="utf-8") as f: edl = json.load(f)
    rows = measure(edl, args[1])
    for r in rows:
        mark = "" if r["r_picture"] >= R_MIN and r["r_sound"] >= R_MIN else "  (not counted: weak match)"
        print(f"  {r['t']:8.2f} s  picture {r['picture_ms']:+6.1f} ms  sound {r['sound_ms']:+6.1f} ms  desync {r['desync_ms']:+6.1f} ms{mark}")
    bad = judge(rows, max_ms, median_ms)
    good = [r["desync_ms"] for r in rows if r["r_picture"] >= R_MIN and r["r_sound"] >= R_MIN]
    print(f"lips: {len(good)}/{len(rows)} pieces counted, median {np.median(good) if good else float('nan'):+.1f} ms, "
          f"{len(bad)} problems {'OK' if not bad else 'FAIL'}")
    if not rows: print(f"  WARN lips: no piece of {MIN_LEN:.0f} s, not measured (the long measures the same code)")
    if 0 < len(good) < MIN_PIECES: print(f"  WARN lips: only {len(good)} piece(s) counted (a median wants {MIN_PIECES})")
    for b in bad: print(f"  problem: {b}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
