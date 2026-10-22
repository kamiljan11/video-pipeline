#!/usr/bin/env python3
"""Pack a finished film for the viewer review: per time window one sheet of frames (with timestamps), what is said
and what is on screen. A reviewer agent reads pack.md and the sheets like a viewer would and reports where it drags.

  .venv/bin/python viewer_pack.py <plan.json> <film.mp4> <outdir> [--every S] [--window S]

Defaults: long film a frame every 2.5 s in 30 s windows, vertical short every 1.5 s in 15 s windows.
Relative paths in the plan are read from the plan's folder (the work dir, where the pipeline runs them from).
The outdir is the pack: earlier sheets and pack files in it are replaced.
How the review is run and what it reports: review/viewer.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

SHEET_COLS = {False: 4, True: 6}  # horizontal / vertical film
FRAME_H = {False: 225, True: 400}


def film_words(words: list[dict], segments: list[dict]) -> list[tuple[float, str]]:
    """(time in the finished film, word) for every word heard in the film, in film order. A cut lands a few ms
    after a word starts (or before the next one), so a word counts when more than half of it is inside a segment,
    once (the first such segment)."""
    out = []
    used: set[int] = set()
    acc = 0.0
    for s in segments:
        for i, w in enumerate(words):
            a, b = w["offsets"]["from"] / 1000, w["offsets"]["to"] / 1000
            inside = min(b, s["out"]) - max(a, s["in"])
            if i not in used and inside > max(b - a, 0.02) / 2:
                out.append((acc + max(a, s["in"]) - s["in"], w["text"].strip()))
                used.add(i)
        acc += s["out"] - s["in"]
    return out


def windows(total: float, size: float) -> list[tuple[float, float]]:
    n = max(1, int(np.ceil(total / size - 1e-9)))
    return [(i * size, min(total, (i + 1) * size)) for i in range(n)]


def card_text(spec: dict) -> str:
    parts = [spec.get("text", ""), spec.get("sub", ""), *spec.get("items", [])]
    return " / ".join(p for p in parts if p)


def on_screen(overlays: list[dict], specs: dict[str, dict], a: float, b: float) -> list[str]:
    """Graphics and b-roll visible in [a, b): 'id (type) 12.0-18.5 s: text'."""
    seen = []
    for o in overlays:
        end = o["at"] + o["dur"]
        if o["at"] < b and end > a:
            sp = specs.get(o["id"])
            kind = sp.get("type", "?") if sp else o.get("kind", "BRAK SPECA")  # never guess what is on screen
            text = card_text(sp) if sp else ""
            seen.append(f"{o['id']} ({kind}) {o['at']:.1f}-{end:.1f} s" + (f": {text}" if text else ""))
    return seen


def stamp(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def duration(film: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", film],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def grab_frames(film: str, every: float, height: int, tmp: Path) -> list[Path]:
    """One decode pass: frame k shows the film at k * every seconds."""
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", film, "-vf", f"fps=1/{every},scale=-2:{height}",
                    "-q:v", "4", str(tmp / "f%05d.jpg")], check=True)
    return sorted(tmp.glob("f*.jpg"))


def sheet(frames: list[tuple[float, Path]], cols: int, path: Path) -> None:
    tiles = []
    for t, f in frames:
        img = cv2.imread(str(f))
        if img is None:
            raise RuntimeError(f"unreadable frame {f}")
        cv2.rectangle(img, (0, 0), (92, 26), (0, 0, 0), -1)
        cv2.putText(img, stamp(t), (4, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(img)
    blank = np.zeros_like(tiles[0])
    tiles += [blank] * (-len(tiles) % cols)
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(str(path), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])


def pack(plan_path: Path, film: str, outdir: Path, every: float | None = None, size: float | None = None) -> dict:
    plan = json.loads(plan_path.read_text())
    base = plan_path.parent
    edl = json.loads((base / plan["edl_out"]).read_text())
    words = json.loads((base / plan["words"]).read_text())["transcription"]
    specs = {s["id"]: s for s in json.loads((base / plan["gfx_specs"]).read_text())} if plan.get("gfx_specs") else {}
    vertical = bool(edl.get("vertical"))
    every = every or (1.5 if vertical else 2.5)
    size = size or (15.0 if vertical else 30.0)
    total = duration(film)
    said = film_words(words, edl["segments"])
    shown = edl.get("overlays", []) + [dict(b, kind="broll") for b in edl.get("broll", [])]
    outdir.mkdir(parents=True, exist_ok=True)
    for old in [*outdir.glob("w[0-9][0-9][0-9].jpg"), outdir / "pack.json", outdir / "pack.md"]:
        old.unlink(missing_ok=True)  # a pack of an earlier render must not mix in
    result = {"film": film, "plan": str(plan_path), "vertical": vertical, "every": every, "total": round(total, 2),
              "windows": []}
    with tempfile.TemporaryDirectory(dir=outdir) as tmp:
        frames = [(k * every, f) for k, f in enumerate(grab_frames(film, every, FRAME_H[vertical], Path(tmp)))]
        for i, (a, b) in enumerate(windows(total, size)):
            mine = [(t, f) for t, f in frames if a <= t < b]
            if not mine:
                result.setdefault("missing", []).append(i)
                print(f"warning: no frames for window {i} ({stamp(a)}-{stamp(b)}): the film is shorter than it claims",
                      file=sys.stderr)
                continue
            name = f"w{i:03d}.jpg"
            sheet(mine, SHEET_COLS[vertical], outdir / name)
            result["windows"].append({"i": i, "start": a, "end": b, "sheet": name,
                                      "said": " ".join(w for t, w in said if a <= t < b),
                                      "on_screen": on_screen(shown, specs, a, b)})
    (outdir / "pack.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    lines = [f"# {Path(film).name}: {stamp(total)}, {'pionowy' if vertical else 'poziomy'}, klatka co {every} s", ""]
    if result.get("missing"):
        lines += [f"UWAGA: okna bez klatek (nieobejrzane): {result['missing']}", ""]
    for w in result["windows"]:
        lines += [f"## Okno {w['i']}: {stamp(w['start'])}-{stamp(w['end'])}  (arkusz {w['sheet']})",
                  f"Mówi: {w['said'] or '(cisza)'}",
                  "Na ekranie: " + ("; ".join(w["on_screen"]) or "tylko kamera"), ""]
    (outdir / "pack.md").write_text("\n".join(lines))
    return result


def main(argv: list[str]) -> int:
    opts: dict[str, float | None] = {"--every": None, "--window": None}
    rest = []
    it = iter(argv)
    for a in it:
        if a in opts:
            try:
                opts[a] = float(next(it, "nan"))
            except ValueError:
                opts[a] = float("nan")
        else:
            rest.append(a)
    if len(rest) != 3 or any(v is not None and not v > 0 for v in opts.values()):
        print(__doc__, file=sys.stderr)
        return 2
    plan, film, outdir = Path(rest[0]), rest[1], Path(rest[2])
    for p in (plan, Path(film)):
        if not p.is_file():
            print(f"FAILED viewer_pack: no such file {p}", file=sys.stderr)
            return 1
    try:
        r = pack(plan, film, outdir, opts["--every"], opts["--window"])
    except (KeyError, ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as e:  # JSONDecodeError is a ValueError
        print(f"FAILED viewer_pack {film}: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(f"{len(r['windows'])} windows -> {outdir / 'pack.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
