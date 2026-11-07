#!/usr/bin/env python3
"""thumb_check.py: the rendered long thumbnails as the feed shows them (Skool CCC So5, So6, C4, Z6; P1 task 15).

thumbs.mjs checks what the browser measures (fit, the timestamp corner, the cover's safe zones, the smallest font at
320 px). This checks the pictures it wrote, against thumbs.json and the titles in out/youtube/long.md:
  - shrunk to SMALL px wide (a phone feed tile), tesseract reads at least OCR_MIN of the letters of each "big" (words of
    one letter left out: tesseract drops "z" between big digits that the eye reads, film 2 "3 z 4"),
  - at least one variant without a face (YuNet): Test & Compare learns something only when the variants differ,
  - the words of a thumbnail (big + sub + tag) share less than SHARE_MAX with every title: they complete the title, they
    do not repeat it (any title can show next to any thumbnail in the test).

film_check.py runs it as out.thumbs_read (Out.out_thumbs_read); alone:
  python3 thumb_check.py <thumbs.json> <out dir>   (out dir = the one with thumbnails/ and youtube/long.md)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

import title_check

SMALL = 320        # px wide: a thumbnail in the phone feed
OCR_MIN = 0.8      # share of the letters of "big" read at that size
SHARE_MAX = 0.5    # share of the thumbnail's words that may be in a title
FACE_MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"
TIMEOUT = 120
PASSES = ("format=gray", "format=gray,lutyuv=y='if(gt(val,110),0,255)'")  # grey; black letters on white (light text on dark)


def letters(text: str, min_word: int = 1) -> str:
    return "".join(w for w in re.findall(r"[\w%]+", text.lower()) if len(w) >= min_word or w.isdigit())


def read_small(img: Path) -> list[str]:
    """what tesseract reads in each of PASSES after the picture is shrunk to SMALL px (then blown up 4x so tesseract has
    pixels to work on: the detail lost in the shrink stays lost)"""
    out = []
    with tempfile.TemporaryDirectory() as t:
        small = Path(t) / "s.png"
        for f in PASSES:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(img), "-vf", f"scale={SMALL}:-1:flags=area,scale={SMALL * 4}:-1:flags=bicubic,{f}",
                            str(small)], check=True, timeout=TIMEOUT)
            out.append(subprocess.run(["tesseract", str(small), "-", "-l", "pol", "--psm", "11"], capture_output=True, text=True, check=True,
                                      timeout=TIMEOUT).stdout)
    return out


def read_share(big: str, seen: str) -> float:
    """share of the letters of big (words of 2+ letters, numbers) found in order in what was read (OCR splits and merges
    words: "3 z 4" -> "324")"""
    want, got = letters(big, 2), letters(seen)
    if not want: return 1.0
    return sum(b.size for b in SequenceMatcher(None, want, got, autojunk=False).get_matching_blocks()) / len(want)


def has_face(img: Path) -> bool:
    import cv2  # only here: OpenCV is needed for this one check
    if not FACE_MODEL.is_file(): raise RuntimeError(f"no face model {FACE_MODEL}")
    im = cv2.imread(str(img))
    if im is None: raise RuntimeError(f"cannot read {img}")
    size = (640, 360) if im.shape[1] >= im.shape[0] else (360, 640)
    _, faces = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", size, 0.7).detect(cv2.resize(im, size))
    return faces is not None and len(faces) > 0


def title_share(thumb: str, title: str) -> float:
    mine, theirs = list(dict.fromkeys(title_check.content(thumb))), title_check.content(title)
    if not mine: return 0.0
    return sum(any(title_check.same(w, t) for t in theirs) for w in mine) / len(mine)


def problems(spec: dict, out: Path, titles: list[str]) -> list[str]:
    if not shutil.which("tesseract"): return ["no tesseract: sudo apt install tesseract-ocr tesseract-ocr-pol (README, setup)"]
    bad, faces = [], []
    for v in spec.get("long", []):
        img = out / "thumbnails" / f"long_{v['id']}.jpg"
        if not img.is_file(): bad.append(f"long_{v['id']}: no {img.name}"); continue
        share = max(read_share(v.get("big", ""), seen) for seen in read_small(img))
        if share < OCR_MIN: bad.append(f"long_{v['id']}: at {SMALL} px only {share:.0%} of {v.get('big')!r} is read (want >= {OCR_MIN:.0%}): bigger or fewer letters")
        if FACE_MODEL.is_file(): faces.append(has_face(img))
        words = " ".join(str(v.get(k, "")) for k in ("big", "sub", "tag"))
        for t in titles:
            if title_share(words, t) >= SHARE_MAX: bad.append(f"long_{v['id']}: {title_share(words, t):.0%} of its words are in the title {t!r} (want < {SHARE_MAX:.0%})")
    if not FACE_MODEL.is_file(): bad.append(f"no face model {FACE_MODEL}: the variant without a face cannot be checked (README, setup)")
    if faces and all(faces): bad.append(f"all {len(faces)} long variants show a face: make one without (a chart, the number, the screen)")
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    out, md = Path(argv[1]), Path(argv[1]) / "youtube" / "long.md"
    titles = [r["title"] for r in title_check.titles(md.read_text())] if md.is_file() else []
    try:
        bad = problems(json.loads(Path(argv[0]).read_text()), out, titles)
    except (RuntimeError, OSError, ValueError, ImportError, subprocess.SubprocessError) as e:
        print(f"FAILED thumb_check: {e}", file=sys.stderr); return 1
    print("\n".join(bad) or "OK thumb_check")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
