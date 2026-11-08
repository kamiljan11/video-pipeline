#!/usr/bin/env python3
"""sync_check: is every piece of the finished film where the EDL put its graphics, subtitles and cards?

    python3 sync_check.py <edl.json> <final.mp4> [--max-ms 80] [--json out.json]

build_edl.py times every card, scene beat and subtitle with src2out() (EDL piece lengths). assemble.py then cuts the
pieces; with seg_exact it rounds each one to whole frames. Any difference between the two moves everything on screen
against the voice (film 2026-11-04: +287 ms by the end, Kamil 2026-11-08 "do 1:27 sporo spoznien w roznym miejscu").
This check does not trust either side: for every piece it finds the piece's own sound (from the recording) in the
film's sound by envelope cross-correlation near the planned time, and reports planned vs found.

Problems (exit 1): a piece found more than --max-ms (default 80, about 2.5 frames) away from its planned time,
or too few pieces measurable (under half). Pieces too short or too quiet to measure are counted, never guessed.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 1000  # envelope rate: 1 ms
SEARCH = 0.6  # s each side of the planned time
MIN_LEN = 0.8  # s of sound needed to measure a piece


def planned_starts(edl: dict) -> list[float]:
    """where build_edl.src2out() puts each piece: the sum of the EDL lengths before it (what cards and subs use)"""
    acc, out = 0.0, []
    for s in edl["segments"]:
        out.append(acc)
        acc += s["out"] - s["in"]
    return out


def envelope(path: str, ss: float | None = None, t: float | None = None) -> np.ndarray:
    """mono |x| averaged per ms, from 16 kHz audio"""
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None: cmd += ["-ss", f"{max(ss, 0):.3f}"]
    cmd += ["-i", path]
    if t is not None: cmd += ["-t", f"{t:.3f}"]
    # the voice band only and in dB: the film's music, ducking and compression change the level, not the shape
    cmd += ["-vn", "-ac", "1", "-af", "highpass=f=300,lowpass=f=3400", "-ar", "16000", "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True, timeout=1800).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) ** 2
    k = 16000 // SR
    return 10 * np.log10(a[: len(a) // k * k].reshape(-1, k).mean(1) + 1.0)


def find(piece: np.ndarray, film: np.ndarray, at: float, search: float | None = None) -> tuple[float | None, float]:
    """(found start in s or None, normalized correlation) of piece inside film around `at`"""
    sr = SEARCH if search is None else search
    lo = int(max(at - sr, 0) * SR); hi = int((at + sr) * SR) + len(piece)
    win = film[lo:hi]
    if len(win) < len(piece) + 2: return None, 0.0
    p = piece - piece.mean(); ps = np.sqrt((p ** 2).sum())
    if ps == 0: return None, 0.0
    best, bi = -2.0, 0
    for i in range(0, len(win) - len(p) + 1, 2):  # 2 ms steps, refined below
        w = win[i:i + len(p)]; w = w - w.mean(); ws = np.sqrt((w ** 2).sum())
        if ws == 0: continue
        c = float((p * w).sum() / (ps * ws))
        if c > best: best, bi = c, i
    for i in (bi - 1, bi + 1):
        if 0 <= i <= len(win) - len(p):
            w = win[i:i + len(p)]; w = w - w.mean(); ws = np.sqrt((w ** 2).sum())
            if ws and (c := float((p * w).sum() / (ps * ws))) > best: best, bi = c, i
    if bi <= 2 or bi >= len(win) - len(p) - 2: return None, best  # on the edge of the search: no real match inside
    return (lo + bi) / SR, best


def check(edl: dict, film_path: str, max_ms: float = 80.0, src_env: dict | None = None, film_env: np.ndarray | None = None) -> dict:
    film = envelope(film_path) if film_env is None else film_env
    starts = planned_starts(edl)
    rows, skipped = [], 0
    cache = src_env if src_env is not None else {}
    for i, (s, at) in enumerate(zip(edl["segments"], starts)):
        d = s["out"] - s["in"]
        if d < MIN_LEN: skipped += 1; continue
        if s["src"] not in cache: cache[s["src"]] = envelope(edl["sources"][s["src"]])
        src = cache[s["src"]]
        a, b = int((s["in"] + 0.05) * SR), int((s["out"] - 0.05) * SR)  # skip the 12 ms fades
        piece = src[a:b]
        if len(piece) < MIN_LEN * SR / 2 or piece.max() - np.median(piece) < 15: skipped += 1; continue
        got, r = find(piece, film, at + 0.05)
        if got is None or r < 0.6: skipped += 1; continue
        rows.append({"seg": i, "planned": round(at, 3), "found": round(got - 0.05, 3), "ms": round((got - 0.05 - at) * 1000), "r": round(r, 3)})
    measured = len(rows)
    bad = [x for x in rows if abs(x["ms"]) > max_ms]
    problems = [f"piece {x['seg']} at {x['planned']:.2f} s plays {x['ms']:+d} ms off its planned time (cards, scene beats and subtitles move with it)" for x in bad[:12]]
    if len(bad) > 12: problems.append(f"... {len(bad) - 12} more pieces over {max_ms:g} ms")
    total = len(edl["segments"])
    if measured < (total - sum(1 for s in edl["segments"] if s["out"] - s["in"] < MIN_LEN)) / 2:
        problems.append(f"only {measured} of {total} pieces measurable: sync not proven")
    ms = [x["ms"] for x in rows]
    return {"problems": problems, "measured": measured, "skipped": skipped, "total": total,
            "max_ms": max((abs(m) for m in ms), default=0), "median_ms": float(np.median(ms)) if ms else None, "rows": rows}


def main(argv: list[str]) -> int:
    max_ms, out = 80.0, None
    if "--max-ms" in argv: i = argv.index("--max-ms"); max_ms = float(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if "--json" in argv: i = argv.index("--json"); out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if len(argv) != 2: print("usage: sync_check.py <edl.json> <final.mp4> [--max-ms 80] [--json out.json]", file=sys.stderr); return 2
    edl = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    rep = check(edl, argv[1], max_ms)
    if out: Path(out).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for p in rep["problems"]: print(p)
    print(f"sync: {rep['measured']}/{rep['total']} pieces measured, max {rep['max_ms']} ms, median {rep['median_ms']} ms"
          + ("" if rep["problems"] else " OK"))
    return 1 if rep["problems"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
