#!/usr/bin/env python3
"""stills.py: every graphic card as a still on a real frame of the film, with the sentence said under it, before any .mov
is rendered (Skool CCC A6, G5, Z4; P1 task 9). Kamil looks at the 2 key cards first, then the sheet of all, and accepts.

  python3 stills.py <plan.json> [--only id,id]   -> <gfx>/stills/<id>_still.jpg + sheet.jpg (film order) + sheet.md
  python3 stills.py accept <plan.json> <id> ... | --all

A still = gfx/render.mjs --stills (the same page as the .mov, at the moment everything is up: spec "still" or stillTime)
laid over the source frame at that moment of the film (EDL overlay "at" + still time, mapped through the segments; the
source frame as shot, without the EDL zoom), the words heard while the card is up underneath. Shorts (canvas "v") get the
source centre-cropped to 9:16 around the EDL face x.
accept copies each card's render key into <gfx>/stills/accepted.json; from the first sheet on, render.mjs renders only cards
whose key there matches (a card changed after acceptance needs a new still and a new accept). STILLS=off overrides.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

import viewer_pack

ROOT = Path(__file__).resolve().parent
CELL = (960, 540)        # still size on the sheet (16:9); a 9:16 still is 304x540 centred in the cell
CAPTION = 110            # px under each still for the id and the sentence
COLS = 2
TIMEOUT = 600
FONT = cv2.FONT_HERSHEY_SIMPLEX


def gfx_dir(plan_path: Path, edl: dict) -> Path:
    files = [Path(o["file"]) for o in edl.get("overlays", []) if o.get("file")]
    return files[0].parent if files else plan_path.parent / "gfx"


def source_at(edl: dict, t: float) -> tuple[str, float] | None:
    """(source file, seconds in it) shown at film time t, or None past the end"""
    acc = 0.0
    for s in edl["segments"]:
        length = s["out"] - s["in"]
        if t < acc + length: return edl["sources"][s["src"]], s["in"] + (t - acc)
        acc += length
    return None


def said(words: list[tuple[float, str]], a: float, b: float) -> str:
    return " ".join(w for t, w in words if a <= t < b)


def frame(src: str, t: float, size: tuple[int, int], face_x: float) -> np.ndarray:
    """the source frame at t, scaled to cover size (w, h) and cropped around face_x (0..1) when the aspect differs"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True, timeout=TIMEOUT).stdout
    im = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if im is None: raise RuntimeError(f"no frame at {t:.2f} s in {src}")
    w, h = size
    k = max(w / im.shape[1], h / im.shape[0])
    im = cv2.resize(im, (round(im.shape[1] * k), round(im.shape[0] * k)), interpolation=cv2.INTER_AREA)
    x0 = int(min(max(face_x * im.shape[1] - w / 2, 0), im.shape[1] - w))
    y0 = (im.shape[0] - h) // 2
    return im[y0:y0 + h, x0:x0 + w]


def over(base: np.ndarray, png: Path) -> np.ndarray:
    """the card (RGBA, its own size) scaled onto base by its alpha"""
    card = cv2.imread(str(png), cv2.IMREAD_UNCHANGED)
    if card is None or card.ndim != 3: raise RuntimeError(f"cannot read the still {png}")
    card = cv2.resize(card, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_AREA)
    if card.shape[2] == 3: return card  # nothing see-through (a full-screen scene): the PNG is written without alpha
    a = card[:, :, 3:4].astype(np.float32) / 255
    return (card[:, :, :3] * a + base * (1 - a)).astype(np.uint8)


def wrap(text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > width: lines.append(cur); cur = w
        else: cur = f"{cur} {w}".strip()
    return [*lines, cur] if cur else lines


def cell(img: np.ndarray, cid: str, sentence: str) -> np.ndarray:
    """one sheet cell: the still in a CELL box, the id and up to 2 lines of what is said (ASCII: cv2 fonts have no ą ę)"""
    c = np.full((CELL[1] + CAPTION, CELL[0], 3), 24, np.uint8)
    x = (CELL[0] - img.shape[1]) // 2
    c[:img.shape[0], x:x + img.shape[1]] = img
    cv2.putText(c, cid, (12, CELL[1] + 32), FONT, 0.8, (120, 200, 255), 2, cv2.LINE_AA)
    flat = sentence.translate(str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ„”", "acelnoszzACELNOSZZ\"\""))
    for i, line in enumerate(wrap(flat or "(nothing said)", 78)[:2]):
        cv2.putText(c, line, (12, CELL[1] + 64 + i * 28), FONT, 0.62, (230, 230, 230), 1, cv2.LINE_AA)
    return c


def sheet(cells: list[np.ndarray]) -> np.ndarray:
    rows = [np.hstack(cells[i:i + COLS] + [np.zeros_like(cells[0])] * (COLS - len(cells[i:i + COLS]))) for i in range(0, len(cells), COLS)]
    return np.vstack(rows)


def make(plan_path: Path, only: list[str] | None = None) -> dict:
    t0 = time.monotonic()
    plan, edl, words, specs = viewer_pack.load(plan_path)
    gfx = gfx_dir(plan_path, edl)
    shown = [o for o in edl.get("overlays", []) if o.get("id") in specs and (not only or o["id"] in only)]
    if not shown: raise ValueError(f"no graphic cards of {plan_path.name} in its EDL" + (f" among {only}" if only else ""))
    ids = list(dict.fromkeys(o["id"] for o in shown))
    subprocess.run(["node", str(ROOT / "gfx" / "render.mjs"), str(plan_path.parent / plan["gfx_specs"]), str(gfx), "--stills", *ids],
                   check=True, timeout=TIMEOUT, cwd=plan_path.parent)
    sd = gfx / "stills"
    heard = viewer_pack.film_words(words, edl["segments"])
    face_x = (edl.get("face") or [0.5])[0]

    def one(o: dict) -> tuple[str, np.ndarray, str]:
        sp, t = specs[o["id"]], float((sd / f"{o['id']}.t").read_text())
        size = (round(CELL[1] * 9 / 16), CELL[1]) if sp.get("canvas") == "v" else CELL
        at = source_at(edl, o["at"] + t)
        base = frame(*at, size, face_x) if at else np.zeros((size[1], size[0], 3), np.uint8)
        img, sentence = over(base, sd / f"{o['id']}.png"), said(heard, o["at"], o["at"] + o.get("dur", sp.get("dur", 0)))
        cv2.imwrite(str(sd / f"{o['id']}_still.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        return o["id"], cell(img, f"{o['id']}  {viewer_pack.stamp(o['at'])}", sentence), sentence

    with ThreadPoolExecutor(6) as ex: done = list(ex.map(one, shown))
    cv2.imwrite(str(sd / "sheet.jpg"), sheet([c for _, c, _ in done]), [cv2.IMWRITE_JPEG_QUALITY, 82])
    (sd / "sheet.md").write_text("".join(f"- `{cid}` {s or '(nothing said)'}\n" for cid, _, s in done))
    acc = sd / "accepted.json"
    if not acc.exists(): acc.write_text("{}\n")  # from now on render.mjs asks for an accepted still per card
    return {"cards": len(done), "sheet": str(sd / "sheet.jpg"), "seconds": round(time.monotonic() - t0, 1)}


def accept(plan_path: Path, ids: list[str]) -> list[str]:
    _, edl, _, _ = viewer_pack.load(plan_path)
    sd = gfx_dir(plan_path, edl) / "stills"
    keys = {k.stem: k.read_text() for k in sd.glob("*.key")}
    want = sorted(keys) if ids == ["--all"] else ids
    miss = [i for i in want if i not in keys]
    if miss: raise ValueError(f"no still for {miss}: run python3 stills.py {plan_path} --only {','.join(miss)} first")
    acc = sd / "accepted.json"
    done = json.loads(acc.read_text()) if acc.exists() else {}
    done.update({i: keys[i] for i in want})
    acc.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n")
    return want


def main(argv: list[str]) -> int:
    try:
        if argv[:1] == ["accept"] and len(argv) >= 3:
            print(f"accepted {len(accept(Path(argv[1]), argv[2:]))} cards")
            return 0
        if len(argv) in (1, 3) and (len(argv) == 1 or argv[1] == "--only"):
            r = make(Path(argv[0]), argv[2].split(",") if len(argv) == 3 else None)
            print(f"{r['cards']} stills in {r['seconds']} s: {r['sheet']}")
            return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as e:
        print(f"FAILED stills: {e}", file=sys.stderr); return 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
