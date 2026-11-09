#!/usr/bin/env python3
"""cutout.py <slug> [--method person|flat|alpha] — a meme's character without its background, for the 16:9 "sticker"
card with "cut": true (docs/designs/2026-11-05-visual-upgrade.md item 6): the character floats beside the speaker with a
white sticker edge instead of sitting in a rectangle of the meme photo.

Writes render/memes/<slug>.cut.png (the whole picture, RGBA) and "cut": {"file", "method", "src_sha256", "cover"} into
render/memes/<slug>.json; render.mjs refuses a cut whose src_sha256 is not the picture's (a re-fetch makes it stale).
Methods, no download and no install (Kamil 2026-11-07: no paid tools; a general segmentation model would be a new install):
  person  the people in the picture, Robust Video Matting (matte/models, sha-pinned, behind.py's Matter) on the still frame
          fed WARM times so its recurrent state settles; run with matte/.venv/bin/python
  flat    a plain background: pixels joined to the crop's border whose colour is within TOL of the border's median
  alpha   the picture already has transparency (PNG): kept as it is
Every sticker crop of style/memes.json must keep COVER_MIN..COVER_MAX of its area, else the cut fails by name (the model
found nobody, or the background is not plain): the sticker then stays a rectangle, or the meme is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MEMES = Path(os.environ.get("VP_MEMES", ROOT / "render" / "memes"))
CATALOGUE = ROOT / "style" / "memes.json"
WARM = 6  # times the still is fed to the matting model; its recurrent state needs a few frames to settle on a person
TOL = 24.0  # flat: colour distance (RGB, 0..441) from the border median that still counts as background
BORDER_STD_MAX = 18.0  # flat: a border whose colours spread more than this is no plain background
LOW = 0.2  # person: matte values under this are noise (faint lines along panel borders of a multi-panel meme, preview 2026-11-09)
EDGE = 3  # px cleared each side of a crop edge inside the picture
COVER_MIN, COVER_MAX = 0.08, 0.92  # share of a crop the character keeps; outside = the cut found nothing / everything


class CutError(Exception):
    pass


def read_rgba(pic: Path) -> np.ndarray:
    """the picture as HxWx4 uint8 (ffmpeg decodes, as behind.py does: no PIL in matte/.venv)"""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(pic)], capture_output=True, text=True, check=False)
    if probe.returncode: raise CutError(f"{pic.name}: ffprobe cannot read it ({probe.stderr.strip()[:120]})")
    w, h = map(int, probe.stdout.strip().split(",")[:2])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(pic), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                         capture_output=True, check=False)
    if raw.returncode or len(raw.stdout) != w * h * 4: raise CutError(f"{pic.name}: ffmpeg cannot decode it")
    return np.frombuffer(raw.stdout, np.uint8).reshape(h, w, 4).copy()


def write_png(rgba: np.ndarray, out: Path) -> None:
    h, w = rgba.shape[:2]
    tmp = out.with_suffix(".part.png")
    p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-i", "-",
                        "-frames:v", "1", str(tmp)], input=rgba.tobytes(), capture_output=True, check=False)
    if p.returncode: raise CutError(f"ffmpeg cannot write {out.name}: {p.stderr.decode()[:160]}")
    tmp.replace(out)


def crop_box(c: list[float], w: int, h: int) -> tuple[int, int, int, int]:
    x, y, cw, ch = c
    return round(x * w), round(y * h), max(1, round(cw * w)), max(1, round(ch * h))


def flat_alpha(rgb: np.ndarray) -> np.ndarray:
    """1 = keep: everything except the plain background joined to the border (grown 4-neighbour from the border)"""
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.float32)
    if float(border.std(axis=0).max()) > BORDER_STD_MAX:
        raise CutError(f"the border is not one plain colour (spread {float(border.std(axis=0).max()):.0f} > {BORDER_STD_MAX:.0f})")
    close = np.linalg.norm(rgb.astype(np.float32) - np.median(border, axis=0), axis=2) <= TOL
    bg = np.zeros_like(close)
    bg[0], bg[-1], bg[:, 0], bg[:, -1] = close[0], close[-1], close[:, 0], close[:, -1]
    while True:
        grown = bg.copy()
        grown[1:] |= bg[:-1]; grown[:-1] |= bg[1:]; grown[:, 1:] |= bg[:, :-1]; grown[:, :-1] |= bg[:, 1:]
        grown &= close
        if (grown == bg).all(): break
        bg = grown
    return (~bg).astype(np.float32)


def person_alpha(rgb: np.ndarray) -> np.ndarray:
    import behind  # matte/.venv: onnxruntime + the sha-pinned RVM file
    try:
        m = behind.Matter(ratio=min(1.0, 512 / max(rgb.shape[:2])))
    except behind.BehindError as e:
        raise CutError(str(e)) from e
    except ImportError as e:
        raise CutError(f"method person needs onnxruntime: run with matte/.venv/bin/python ({e})") from e
    a = None
    for _ in range(WARM): a = m(rgb)
    a = np.clip(np.asarray(a, np.float32), 0, 1)
    a[a < LOW] = 0
    return a


def cut(slug: str, method: str, memes: Path = MEMES, catalogue: Path = CATALOGUE) -> dict:
    meta_f = memes / f"{slug}.json"
    if not meta_f.exists(): raise CutError(f"{meta_f} missing: python3 memes.py add {slug}")
    meta = json.loads(meta_f.read_text(encoding="utf-8"))
    # the crops render.mjs uses: style/memes.json wins, else the picture's own json (a picture placed by hand)
    crops = json.loads(catalogue.read_text(encoding="utf-8")).get(slug, {}).get("sticker") or meta.get("sticker")
    if not crops: raise CutError(f'"{slug}" has no "sticker" crops (style/memes.json or {meta_f.name}): nothing to cut out')
    pic = memes / meta["img"]
    rgba = read_rgba(pic)
    h, w = rgba.shape[:2]
    if method == "alpha":
        alpha = rgba[..., 3].astype(np.float32) / 255
        if float((alpha < 0.5).mean()) < 0.05: raise CutError(f"{pic.name} has no transparency (method alpha needs a cut-out PNG)")
    elif method == "person":
        alpha = person_alpha(rgba[..., :3])
    else:
        alpha = np.zeros((h, w), np.float32)
        for i, c in enumerate(crops):
            x, y, cw, ch = crop_box(c, w, h)
            try: alpha[y:y + ch, x:x + cw] = flat_alpha(rgba[y:y + ch, x:x + cw, :3])
            except CutError as e: raise CutError(f"crop {i}: {e}") from e
    # a crop edge inside the picture (a panel border): clear EDGE px each side, else a person reaching the next panel's edge
    # shows as a sliver at the top of this crop once scaled, and the white sticker edge outlines it (preview 2026-11-09)
    for c in crops:
        x, y, cw, ch = crop_box(c, w, h)
        for e in (y, y + ch):
            if 0 < e < h: alpha[max(0, e - EDGE):e + EDGE, x:x + cw] = 0
        for e in (x, x + cw):
            if 0 < e < w: alpha[y:y + ch, max(0, e - EDGE):e + EDGE] = 0
    cover = []
    for i, c in enumerate(crops):
        x, y, cw, ch = crop_box(c, w, h)
        k = round(float((alpha[y:y + ch, x:x + cw] >= 0.5).mean()), 3)
        if not COVER_MIN <= k <= COVER_MAX:
            raise CutError(f"crop {i}: the cut keeps {k:.0%} of it (want {COVER_MIN:.0%}..{COVER_MAX:.0%}): "
                           f"{'nobody found' if k < COVER_MIN else 'the background stayed'} with method {method}")
        cover.append(k)
    out = rgba.copy()
    out[..., 3] = np.round(alpha * 255).astype(np.uint8)
    write_png(out, memes / f"{slug}.cut.png")
    meta["cut"] = {"file": f"{slug}.cut.png", "method": method, "src_sha256": hashlib.sha256(pic.read_bytes()).hexdigest(), "cover": cover}
    tmp = meta_f.with_suffix(".json.part")
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"); tmp.replace(meta_f)
    return meta["cut"]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="a meme's character without its background, for the sticker card (cut: true)")
    ap.add_argument("slug"); ap.add_argument("--method", choices=("person", "flat", "alpha"), default="person")
    a = ap.parse_args(argv)
    try:
        c = cut(a.slug, a.method)
    except (CutError, OSError, ValueError, KeyError) as e:
        print(f"FAILED cutout {a.slug}: {e}"); return 1
    print(f"cutout {a.slug}: {c['file']} ({c['method']}), crops keep {', '.join(f'{k:.0%}' for k in c['cover'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
