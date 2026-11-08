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
  - words of the long's `## Fraza kluczowa` are left out of that share: the tool name may sit on both (round 2 TH1:
    "Claude Code: 18%" over a title with "Claude Code" was a false FAIL),
  - WARN: a face under FACE_MIN of the frame height (creator study W5, round 2 TH2 6/6: big or none, a small one loses),
    a face centred (cx in FACE_MID: the text loses its side), two faces or more,
  - WARN: flat tone (grey std < TONE_STD or mean < TONE_MEAN) and colour count 0 or >= COLOURS_MAX hue bins (TH3),
  - WARN: a big that starts with a small letter, a sum of money in the text (TH10, weak: n=1-2),
  - WARN: a "big" that is a bare topic label (no digit, "?", arrow, "vs", verb-like word): "Kod z AI", "Blizna", "Szlaban"
    (long variants and short covers); a big made only of tool names ("Claude Code", "MCP", style/title_lint.json
    "tools") is not a label.
WARN lines do not fail the check: problems() returns only the failures, check() returns (failures, warnings).

film_check.py runs it as out.thumbs_read (Out.out_thumbs_read); alone:
  python3 thumb_check.py <thumbs.json> <out dir>   (out dir = the one with thumbnails/ and youtube/long.md)
Before thumbs.mjs (TH4), once per film:
  python3 thumb_check.py --place <thumbs.json>   writes fx/fy (+ "placed": {cx, cy}) into the long variants without "fx",
  so the face YuNet finds in the frame lands at x PLACE_CX (0.72 text left / 0.28 text right); other fields stay as they are
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
FACE_MIN = 0.40    # a face shorter than this share of the frame height is a WARN (round 2 TH2: 0.30 -> 0.40)
FACE_MID = (0.35, 0.65)  # face centre x in this band = centred, the text has no side of its own (WARN)
TONE_STD, TONE_MEAN = 0.25, 0.15  # grey std / mean (0..1) under these = flat or dark in the feed (WARN)
COLOURS_MAX = 4    # hue bins (of 12) holding >= COLOUR_SHARE of the saturated pixels: 0 = grey, >= 4 = noisy (WARN)
COLOUR_SHARE = 0.05
MONEY = re.compile(r"\d\s*(zł|pln|\$|€|tys|mln|k\b)|[$€]\s*\d", re.IGNORECASE)
try:  # named in check(), never a traceback at import (film_check imports this module)
    TOOLS, TOOLS_ERROR = set(json.loads((Path(__file__).resolve().parent / "style" / "title_lint.json").read_text()).get("tools", [])), ""
except (OSError, ValueError, AttributeError) as e:
    TOOLS, TOOLS_ERROR = set(), f"style/title_lint.json cannot be read ({e!r}): tool names count as topic labels"
TIMEOUT = 120
# TH4 --place (wf2:thumbs-a:1, c:1): the face centre in the outer third, away from the text column: x 0.72 when the text
# is on the left, 0.28 when it is on the right; y a bit above the middle so the chin stays clear of the bottom edge
PLACE_CX = {"left": 0.72, "right": 0.28}
PLACE_CY = 0.42
THUMB_W, THUMB_H, FW = 1280, 720, 1600  # the long thumbnail and thumbs.mjs's default "fw" (longHtml)
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
    return face_info(img)[0]


def face_box(img: Path) -> tuple[float, float, float, int, int, int]:
    """(centre x, centre y, height) as shares of the picture for the tallest YuNet face, the number of faces, and the
    picture's own width and height in px; no face = (0.0, 0.0, 0.0, 0, w, h)"""
    import cv2  # only here: OpenCV is needed for this one check
    if not FACE_MODEL.is_file(): raise RuntimeError(f"no face model {FACE_MODEL}")
    im = cv2.imread(str(img))
    if im is None: raise RuntimeError(f"cannot read {img}")
    size = (640, 360) if im.shape[1] >= im.shape[0] else (360, 640)
    try:
        _, faces = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", size, 0.7).detect(cv2.resize(im, size))
    except cv2.error as e:  # not a RuntimeError: a broken model file (an LFS pointer) would be a traceback in film_check
        raise RuntimeError(f"face detector on {img.name}: {e}") from e
    if faces is None or len(faces) == 0: return 0.0, 0.0, 0.0, 0, im.shape[1], im.shape[0]
    top = max(faces, key=lambda f: float(f[3]))  # row = x, y, w, h, landmarks, score; the picture was resized to size
    return ((float(top[0]) + float(top[2]) / 2) / size[0], (float(top[1]) + float(top[3]) / 2) / size[1], float(top[3]) / size[1],
            len(faces), im.shape[1], im.shape[0])


def face_info(img: Path) -> tuple[float, float, int]:
    """(height share, centre x share, number of faces) of the tallest YuNet face; (0.0, 0.0, 0) = no face"""
    cx, _, h, n, _, _ = face_box(img)
    return h, cx, n


def tone(img: Path) -> tuple[float, float, int]:
    """(grey std, grey mean, colour bins) of the picture, 0..1 / count of COLOUR_SHARE hue bins"""
    import cv2
    import numpy as np
    im = cv2.imread(str(img))
    if im is None: raise RuntimeError(f"cannot read {img}")
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    hue = hsv[..., 0][(hsv[..., 1] > 80) & (hsv[..., 2] > 60)]  # saturated, not dark: the pixels that read as colour
    bins = np.bincount((hue.astype(int) * 12 // 180).clip(0, 11), minlength=12) if hue.size else np.zeros(12)
    return float(g.std()), float(g.mean()), int((bins >= COLOUR_SHARE * max(hue.size, 1)).sum()) if hue.size > 0.02 * g.size else 0


def has_face(img: Path) -> bool:
    return face_height(img) > 0


def title_share(thumb: str, title: str, phrase: str = "") -> float:
    """share of the thumbnail's content words that are in the title; words of the search phrase are left out (TH1)"""
    key = title_check.content(phrase)
    mine = [w for w in dict.fromkeys(title_check.content(thumb)) if not any(title_check.same(w, k) for k in key)]
    theirs = title_check.content(title)
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
    if all(w in TOOLS for w in content_words(low)): return False  # "Claude Code", "MCP": the tool is the promise (TH1)
    if any(sg in low.split() if sg.isalpha() else sg in low for sg in SIGNS): return False
    return not any(w in VERBISH or VERBISH_END.search(w) for w in content_words(low))


def text_warns(name: str, v: dict) -> list[str]:
    big, words = str(v.get("big", "")), " ".join(str(v.get(k, "")) for k in ("big", "sub", "tag"))
    w = [f"{name}: big {big!r} is a topic label (add a number, a question, a verb or a result)"] if is_topic_label(big) else []
    first = next((c for c in big if c.isalnum()), "")  # "3 z 4", "1 zdanie": a big that starts with a digit is fine
    if first.isalpha() and first.islower(): w.append(f"{name}: big {big!r} starts with a small letter")
    if MONEY.search(words): w.append(f"{name}: a sum of money in the text ({words.strip()!r}): weak in the study, a result or % reads better")
    return w


def thumb_words(v: dict) -> str:
    """the words on a long thumbnail: big + sub + tag, and the labels of a TH8 panel (wf2:thumbs-c:7: the viewer reads them,
    so they count toward WORDS_FAIL and the title share)"""
    panel = v.get("panel")
    items = panel.get("items", []) if isinstance(panel, dict) and isinstance(panel.get("items"), list) else []
    labels = [str(it.get("label", "")) if isinstance(it, dict) else str(it) for it in items]
    return " ".join([str(v.get(k, "")) for k in ("big", "sub", "tag")] + labels)


def pick_problems(spec: dict) -> list[str]:
    """every frame with the speaker came from frame_pick.py ("pick": {"t", "score"}); a frame without him says
    "no_face": true. Kamil 2026-11-08 "glupie miny wybierasz", "rozmazane": one frame at a word start had a mid-word
    mouth, half-shut eyes, a blurred hand. A TH8 layout "object" variant has no frame at all, so nothing to pick."""
    bad = []
    for kind, name in (("long", "long_{}"), ("shorts", "{}_cover")):
        for v in spec.get(kind, []):
            if v.get("no_face") or (kind == "long" and v.get("layout") == "object"): continue
            pk = v.get("pick")
            if not (isinstance(pk, dict) and isinstance(pk.get("t"), (int, float)) and isinstance(pk.get("score"), (int, float))):
                bad.append(f"{name.format(v.get('id'))}: frame not chosen by frame_pick.py (want \"pick\": {{t, score}}, or \"no_face\": true)")
    return bad


def check(spec: dict, out: Path, titles: list[str], phrase: str = "") -> tuple[list[str], list[str]]:
    """(failures, warnings) of the thumbnails in spec; phrase = the long's `## Fraza kluczowa`"""
    if not shutil.which("tesseract"): return ["no tesseract: sudo apt install tesseract-ocr tesseract-ocr-pol (README, setup)"], []
    bad, warn, faces = [], ([TOOLS_ERROR] if TOOLS_ERROR else []), []
    for v in spec.get("shorts", []):
        warn += text_warns(str(v.get("id")), v)
    for v in spec.get("long", []):
        img = out / "thumbnails" / f"long_{v['id']}.jpg"
        if not img.is_file(): bad.append(f"long_{v['id']}: no {img.name}"); continue
        share = max(read_share(v.get("big", ""), seen) for seen in read_small(img))
        if share < OCR_MIN: bad.append(f"long_{v['id']}: at {SMALL} px only {share:.0%} of {v.get('big')!r} is read (want >= {OCR_MIN:.0%}): bigger or fewer letters")
        if FACE_MODEL.is_file():
            h, cx, nf = face_info(img); faces.append(h > 0)
            if 0 < h < FACE_MIN: warn.append(f"long_{v['id']}: the face is {h:.0%} of the frame height (want >= {FACE_MIN:.0%}): bigger, or no face")
            if h > 0 and FACE_MID[0] <= cx <= FACE_MID[1]: warn.append(f"long_{v['id']}: the face is centred (x {cx:.2f}): put it on one side, the text on the other")
            if nf >= 2: warn.append(f"long_{v['id']}: {nf} faces: one face reads at feed size")
        sd, mean, cols = tone(img)
        if sd < TONE_STD or mean < TONE_MEAN: warn.append(f"long_{v['id']}: flat tone (grey std {sd:.2f}, mean {mean:.2f}; want std >= {TONE_STD}, mean >= {TONE_MEAN})")
        if cols == 0 or cols >= COLOURS_MAX: warn.append(f"long_{v['id']}: {cols} colour groups (want 1-{COLOURS_MAX - 1})")
        words = thumb_words(v)
        n = len(content_words(words))
        if n > WORDS_FAIL: bad.append(f"long_{v['id']}: {n} words of text (big + sub + tag), want <= {WORDS_FAIL}: shorten sub, drop tag")
        elif n > WORDS_WARN: warn.append(f"long_{v['id']}: {n} words of text (big + sub + tag), better <= {WORDS_WARN}")
        warn += text_warns(f"long_{v['id']}", v)
        for t in titles:
            sh = title_share(words, t, phrase)
            if sh >= SHARE_MAX: bad.append(f"long_{v['id']}: {sh:.0%} of its words are in the title {t!r} (want < {SHARE_MAX:.0%}; phrase words not counted)")
    if not FACE_MODEL.is_file(): bad.append(f"no face model {FACE_MODEL}: the variant without a face cannot be checked (README, setup)")
    if faces and all(faces): bad.append(f"all {len(faces)} long variants show a face: make one without (a chart, the number, the screen)")
    return bad, warn


def problems(spec: dict, out: Path, titles: list[str], phrase: str = "") -> list[str]:
    """the failures only; the warnings are in check()"""
    return check(spec, out, titles, phrase)[0]


def placement(cx: float, cy: float, img_w: int, img_h: int, side: str, fw: float = FW, fy: float | None = None) -> tuple[int, int, float, float]:
    """thumbs.mjs background-position (fx, fy) that puts a face centred at (cx, cy) of the frame at PLACE_CX[side],
    PLACE_CY of the thumbnail, for a frame drawn fw px wide. Then clamped so the frame still reaches the edge on the face
    side and covers the full height (the text side is under the dark band, an uncovered strip there does not show).
    A given fy is kept. -> (fx, fy, cx, cy reached in the thumbnail)"""
    fh = fw * img_h / img_w
    x = PLACE_CX[side] * THUMB_W - cx * fw
    x = max(x, THUMB_W - fw) if side == "left" else min(x, 0.0)
    y = PLACE_CY * THUMB_H - cy * fh if fy is None else fy
    if fy is None: y = min(0.0, max(y, THUMB_H - fh))
    fx, fy_ = round(x), round(y)
    return fx, fy_, (fx + cx * fw) / THUMB_W, (fy_ + cy * fh) / THUMB_H


def place(spec: dict, base: Path, detect=None) -> list[str]:
    """TH4: fx/fy for every long variant without "fx", from the face YuNet finds in its frame (detect(path) -> face_box()
    tuple); writes "placed": {cx, cy} next to them so a checker can tell a placed variant from a hand-set one. A variant
    with "fx", "no_face", layout "object" or no face found is left as it is. -> one line per variant"""
    detect = detect or face_box
    out = []
    for v in spec.get("long", []):
        name = f"long_{v.get('id')}"
        if "fx" in v: out.append(f"{name}: has fx {v['fx']}, left as it is"); continue
        if v.get("no_face") or v.get("layout") == "object": out.append(f"{name}: no face (no_face / layout object), left as it is"); continue
        side = v.get("side", "left")
        if side not in PLACE_CX or not isinstance(v.get("frame"), str): out.append(f"{name}: needs \"frame\" and side left/right, left as it is"); continue
        cx, cy, h, _, iw, ih = detect(base / v["frame"])
        if h <= 0: out.append(f"{name}: YuNet finds no face in {v['frame']}, left as it is"); continue
        fx, fy, gx, gy = placement(cx, cy, iw, ih, side, float(v.get("fw", FW)), v.get("fy"))
        v["fx"], v["fy"], v["placed"] = fx, fy, {"cx": round(gx, 3), "cy": round(gy, 3)}
        far = "" if abs(gx - PLACE_CX[side]) < 0.02 else f" (want {PLACE_CX[side]}: the frame edge stops it; a bigger \"fw\" helps)"
        out.append(f"{name}: fx {fx}, fy {fy}: face centre at x {gx:.2f}, y {gy:.2f}{far}")
    return out


def main(argv: list[str]) -> int:
    if argv[:1] == ["--place"]:
        if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
        f = Path(argv[1])
        try:
            spec = json.loads(f.read_text())
            lines = place(spec, f.resolve().parent)
        except (RuntimeError, OSError, ValueError, ImportError) as e:
            print(f"FAILED thumb_check --place: {e}", file=sys.stderr); return 1
        f.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
        print("\n".join(lines) or "no long variants")
        return 0
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    out, md = Path(argv[1]), Path(argv[1]) / "youtube" / "long.md"
    text = md.read_text() if md.is_file() else ""
    titles = [r["title"] for r in title_check.titles(text)]
    try:
        bad, warn = check(json.loads(Path(argv[0]).read_text()), out, titles, title_check.phrase(text))
    except (RuntimeError, OSError, ValueError, ImportError, subprocess.SubprocessError) as e:
        print(f"FAILED thumb_check: {e}", file=sys.stderr); return 1
    print("\n".join(bad + [f"WARN {w}" for w in warn]) or "OK thumb_check")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
