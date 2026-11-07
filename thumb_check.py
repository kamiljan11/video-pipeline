#!/usr/bin/env python3
"""thumb_check.py: the rendered long thumbnails as the feed shows them (Skool CCC So5, So6, C4, Z6; P1 task 15).

thumbs.mjs checks what the browser measures (fit, the timestamp corner, the cover's safe zones, the smallest font at
320 px). This checks the pictures it wrote, against thumbs.json and the titles in out/youtube/long.md:
  - shrunk to SMALL px wide (a phone feed tile), tesseract reads at least OCR_MIN of the letters of each "big" (words of
    one letter left out: tesseract drops "z" between big digits that the eye reads, film 2 "3 z 4"),
  - at least one variant without a face (YuNet): Test & Compare learns something only when the variants differ,
  - the words of a thumbnail (big + sub + tag) share less than SHARE_MAX with every title: they complete the title, they
    do not repeat it (any title can show next to any thumbnail in the test),
  - at most WORDS_FAIL content words in big + sub + tag (WARN above WORDS_WARN; creator study W1, 9 of 9: 2-5 words),
  - WARN: a face under FACE_MIN of the frame height (creator study W5: big or none, a small one loses),
  - WARN: a "big" that is a bare topic label (no digit, "?", arrow, "vs", verb-like word): "Kod z AI", "Blizna", "Szlaban"
    (long variants and short covers).
WARN lines do not fail the check: problems() returns only the failures, check() returns (failures, warnings).

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
WORDS_WARN = 4     # content words of big + sub + tag: more than this is a WARN
WORDS_FAIL = 5     # ... more than this fails
FACE_MIN = 0.30    # a face shorter than this share of the frame height is a WARN
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


def face_height(img: Path) -> float:
    """height of the tallest YuNet face box as a share of the frame height (0.0 = no face)"""
    import cv2  # only here: OpenCV is needed for this one check
    if not FACE_MODEL.is_file(): raise RuntimeError(f"no face model {FACE_MODEL}")
    im = cv2.imread(str(img))
    if im is None: raise RuntimeError(f"cannot read {img}")
    size = (640, 360) if im.shape[1] >= im.shape[0] else (360, 640)
    try:
        _, faces = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", size, 0.7).detect(cv2.resize(im, size))
    except cv2.error as e:  # not a RuntimeError: a broken model file (an LFS pointer) would be a traceback in film_check
        raise RuntimeError(f"face detector on {img.name}: {e}") from e
    if faces is None or len(faces) == 0: return 0.0
    return max(float(f[3]) for f in faces) / size[1]  # row = x, y, w, h, landmarks, score; the picture was resized to size


def has_face(img: Path) -> bool:
    return face_height(img) > 0


def title_share(thumb: str, title: str) -> float:
    mine, theirs = list(dict.fromkeys(title_check.content(thumb))), title_check.content(title)
    if not mine: return 0.0
    return sum(any(title_check.same(w, t) for t in theirs) for w in mine) / len(mine)


def content_words(text: str) -> list[str]:
    """the words counted against the limit: runs of letters/digits ("%" stays with its number); a word of one letter ("z",
    "w", "i") is dropped unless it is a digit; arrows and punctuation are not words ("92% -> 18%" = 2). No stop-word list:
    "bez", "mój" count, the viewer reads them too."""
    return [w for w in re.findall(r"[\w%]+", text.lower()) if len(w) >= 2 or w.isdigit()]


VERBISH_END = re.compile(r"(ć|ę|ją|uj|aj|ij)$")  # infinitive, 1st person ("psuję"), 3rd person plural, imperative
VERBISH = {"stop", "jak", "kiedy", "czy", "dlaczego", "kto", "co", "nie", "zrób"}  # a question / command word: not a label
SIGNS = ("?", "!", "->", "→", "←", "⇒", "vs", "versus")


def is_topic_label(big: str) -> bool:
    """a "big" that only names a topic: no digit, no "?"/"!", no arrow, no "vs", no verb-like word (an ending of
    VERBISH_END, or a word of VERBISH). Rough on purpose: Polish verbs are too many for a list, so a miss is a WARN
    nobody needs, never a false FAIL."""
    low = big.lower().strip()
    if not content_words(low) or any(c.isdigit() for c in low): return False
    if any(sg in low.split() if sg.isalpha() else sg in low for sg in SIGNS): return False
    return not any(w in VERBISH or VERBISH_END.search(w) for w in content_words(low))


def check(spec: dict, out: Path, titles: list[str]) -> tuple[list[str], list[str]]:
    """(failures, warnings) of the thumbnails in spec"""
    if not shutil.which("tesseract"): return ["no tesseract: sudo apt install tesseract-ocr tesseract-ocr-pol (README, setup)"], []
    bad, warn, faces = [], [], []
    for v in spec.get("shorts", []):
        if is_topic_label(str(v.get("big", ""))): warn.append(f"{v.get('id')}: big {v.get('big')!r} is a topic label (add a number, a question, a verb or a result)")
    for v in spec.get("long", []):
        img = out / "thumbnails" / f"long_{v['id']}.jpg"
        if not img.is_file(): bad.append(f"long_{v['id']}: no {img.name}"); continue
        share = max(read_share(v.get("big", ""), seen) for seen in read_small(img))
        if share < OCR_MIN: bad.append(f"long_{v['id']}: at {SMALL} px only {share:.0%} of {v.get('big')!r} is read (want >= {OCR_MIN:.0%}): bigger or fewer letters")
        if FACE_MODEL.is_file():
            h = face_height(img); faces.append(h > 0)
            if 0 < h < FACE_MIN: warn.append(f"long_{v['id']}: the face is {h:.0%} of the frame height (want >= {FACE_MIN:.0%}): bigger, or no face")
        words = " ".join(str(v.get(k, "")) for k in ("big", "sub", "tag"))
        n = len(content_words(words))
        if n > WORDS_FAIL: bad.append(f"long_{v['id']}: {n} words of text (big + sub + tag), want <= {WORDS_FAIL}: shorten sub, drop tag")
        elif n > WORDS_WARN: warn.append(f"long_{v['id']}: {n} words of text (big + sub + tag), better <= {WORDS_WARN}")
        if is_topic_label(str(v.get("big", ""))): warn.append(f"long_{v['id']}: big {v.get('big')!r} is a topic label (add a number, a question, a verb or a result)")
        for t in titles:
            if title_share(words, t) >= SHARE_MAX: bad.append(f"long_{v['id']}: {title_share(words, t):.0%} of its words are in the title {t!r} (want < {SHARE_MAX:.0%})")
    if not FACE_MODEL.is_file(): bad.append(f"no face model {FACE_MODEL}: the variant without a face cannot be checked (README, setup)")
    if faces and all(faces): bad.append(f"all {len(faces)} long variants show a face: make one without (a chart, the number, the screen)")
    return bad, warn


def problems(spec: dict, out: Path, titles: list[str]) -> list[str]:
    """the failures only (film_check out.thumbs_read); the warnings are in check()"""
    return check(spec, out, titles)[0]


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    out, md = Path(argv[1]), Path(argv[1]) / "youtube" / "long.md"
    titles = [r["title"] for r in title_check.titles(md.read_text())] if md.is_file() else []
    try:
        bad, warn = check(json.loads(Path(argv[0]).read_text()), out, titles)
    except (RuntimeError, OSError, ValueError, ImportError, subprocess.SubprocessError) as e:
        print(f"FAILED thumb_check: {e}", file=sys.stderr); return 1
    print("\n".join(bad + [f"WARN {w}" for w in warn]) or "OK thumb_check")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
