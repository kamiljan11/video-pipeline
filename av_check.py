"""av_check: did the finished film keep every bit of the voice, with the sound in step with the picture?

    python3 av_check.py <final.mp4> [--ref rough.mkv] [--max-ms 60]

Film 2026-11-04 (Kamil 2026-11-08 "0:04 uciales moje gadanie" + "mowa nie jest zespolona z ekranem"): ffmpeg dropped
0.65 s of the voice inside the long's stage-2 run. The AAC track then had one 0.676 s packet at 3.09 s: players that
follow timestamps played a hole, players that play samples in a row ran the voice 0.65 s ahead of the lips for the
rest of the film. Problems (exit 1):
  - an audio packet longer than 2 normal packets (a hole in the sound), except the very last one
  - the decoded sound shorter or longer than the audio track says by more than --max-ms
  - with --ref (the cut before graphics, render/long/rough.mkv): the film's sound, decoded in a row, more than
    --max-ms away from the reference at any of 12 points (a dropped or doubled piece of voice)
"""
import json
import subprocess
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

import sync_check


def packets(path: str) -> list[tuple[float, float]]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "packet=pts_time,duration_time",
                          "-of", "json", path], capture_output=True, text=True, check=True, timeout=600).stdout
    rows = []
    for p in json.loads(out).get("packets", []):
        try: rows.append((float(p["pts_time"]), float(p["duration_time"])))
        except (KeyError, ValueError): continue
    return rows


def holes(pk: list[tuple[float, float]]) -> list[str]:
    if len(pk) < 3: return ["no audio track or under 3 packets"]
    normal = float(np.median([d for _, d in pk]))
    bad = [f"a {d * 1000:.0f} ms audio packet at {t:.2f} s (normal {normal * 1000:.0f} ms): {(d - normal) * 1000:.0f} ms of sound missing there"
           for t, d in pk[:-1] if d > 2 * normal]
    bad += [f"audio jumps {(b[0] - a[0] - a[1]) * 1000:+.0f} ms at {a[0]:.2f} s" for a, b in pairwise(pk)
            if abs(b[0] - a[0] - a[1]) > normal]
    return bad


def decoded_s(path: str) -> float:
    return len(sync_check.envelope(path)) / sync_check.SR


def track_s(pk: list[tuple[float, float]]) -> float:
    return pk[-1][0] + pk[-1][1] - pk[0][0] if pk else 0.0


def against_ref(film: np.ndarray, ref: np.ndarray, max_ms: float, points: int = 12) -> list[str]:
    """the film's sound decoded in a row vs the reference: 4 s windows of the reference found in the film near the same time"""
    n = min(len(film), len(ref)) / sync_check.SR
    bad = []
    for t in np.unique(np.linspace(1.0, max(n - 5.0, 1.0), points).round(1)):  # distinct points, a short film gets fewer
        piece = ref[int(t * sync_check.SR):int((t + 4) * sync_check.SR)]
        got, r = sync_check.find(piece, film, float(t), search=2.0)
        if got is None or r < 0.6: continue  # music-only or silent stretch: not measurable, not a fault
        if abs(got - t) * 1000 > max_ms: bad.append(f"at {t:.1f} s the voice is {(got - t) * 1000:+.0f} ms off the cut before graphics (dropped or doubled sound)")
    return bad


def check(path: str, ref: str | None = None, max_ms: float = 60.0) -> list[str]:
    pk = packets(path)
    bad = holes(pk)
    if pk and abs(decoded_s(path) - track_s(pk)) * 1000 > max_ms:
        bad.append(f"decoded sound {decoded_s(path):.3f} s vs audio track {track_s(pk):.3f} s: samples missing or extra")
    if ref: bad += against_ref(sync_check.envelope(path), sync_check.envelope(ref), max_ms)
    return bad


def main(argv: list[str]) -> int:
    ref, max_ms = None, 60.0
    if "--ref" in argv: i = argv.index("--ref"); ref = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if "--max-ms" in argv: i = argv.index("--max-ms"); max_ms = float(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1 or not Path(argv[0]).exists():
        print("usage: av_check.py <final.mp4> [--ref rough.mkv] [--max-ms 60]", file=sys.stderr); return 2
    bad = check(argv[0], ref, max_ms)
    for b in bad: print(b)
    if not bad: print("av OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
