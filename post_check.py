"""post_check.py: a LinkedIn post that keeps the measured habits of the top creators (style/REF-posts-top.md).

- The graphic stands alone (Kamil 2026-11-05: "grafika sama musi nieść przekaz"). gfx/post_gfx.mjs writes grafika.png and
  grafika.txt (the words it drew); OCR has to find at least RECALL of those words in the picture: a word cut at an edge,
  hidden under another element is missing. Tesseract binarises adaptively and reads even navy on navy, so contrast is
  measured on its own: WCAG AA inside every word box. Word count WORDS (REF P1: class A graphics).
- The text completes the graphic: at most MAX_TAGS hashtags (median 0 in 94 posts), the last line is a question for the
  comments and the resource (film, repo) sits in the line before it, WORDS_TEXT words (Kamil's rule: the graphic carries,
  the text completes). The closing question is Kamil's call (2026-11-07, Skool CCC C07/C10/C17) against our sample (4/68
  top posts end on a question); the weekly review shows whether comments grow.
film_check.py out.posts calls problems() for every post folder.

  python3 post_check.py <post dir>...       prints the problems, rc 1 when there are any
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RECALL = 0.85  # [PROP] share of the drawn words OCR must find; measured 1.00 on all 9 film 2 graphics (2026-11-05); dark-on-dark text falls far below (tests)
CONTRAST = (4.5, 3.0)  # WCAG AA: normal text, large text (a word box at least LARGE px high on the 1080 px graphic)
LARGE = 40
WORDS = (15, 230)  # same range as gfx/post_gfx.mjs WORDS
MAX_TAGS = 3
VOICE = Path(__file__).resolve().parent / "style" / "voice.md"  # "## Zakazane": phrases Kamil never writes (one per bullet)
WORDS_TEXT = (60, 130)  # [PROP] REF-posts-top P2 point 6: about 60-120, from Kamil's rule, not from the sample
WORD = re.compile(r"[\w%]+")


def words(text: str) -> list[str]:
    """lower-case words of 3+ characters (short ones like "z", "na" OCR drops or merges too often to count)"""
    return [w for w in WORD.findall(text.lower()) if len(w) >= 3 or any(c.isdigit() for c in w)]


def luminance(png: Path):
    """WCAG relative luminance per pixel (pixels read by ffmpeg, as everywhere in the pipeline)"""
    import numpy as np
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(png)],
                        capture_output=True, text=True, check=True, timeout=60).stdout.strip().split(",")
    w, h = int(wh[0]), int(wh[1])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True, timeout=60).stdout
    c = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


def ocr(png: Path) -> dict[str, float]:
    """{word: contrast} for the words tesseract reads in the picture; psm 3 (page) and 11 (sparse) together: page mode
    misses big numbers on a coloured bar, sparse mode misses words in table cells. Contrast = WCAG ratio of the light
    and the dark end (95th / 5th percentile) inside the word's box, the best reading of a word that shows up twice."""
    import numpy as np
    lum, got = luminance(png), {}
    for psm in ("3", "11"):
        r = subprocess.run(["tesseract", str(png), "-", "-l", "pol", "--psm", psm, "tsv"], capture_output=True, text=True, check=True, timeout=120)
        for row in r.stdout.splitlines()[1:]:
            f = row.split("\t")
            if len(f) < 12 or not f[11].strip() or float(f[10]) < 0: continue
            x, y, w, h = map(int, f[6:10])
            box = lum[y:y + h, x:x + w]
            lo, hi = np.percentile(box, [5, 95]) if box.size else (0.0, 0.0)
            ratio = (hi + 0.05) / (lo + 0.05)
            need = CONTRAST[1] if h >= LARGE else CONTRAST[0]
            for wd in words(f[11]): got[wd] = max(got.get(wd, 0.0), ratio / need)
    return got


def graphic_problems(d: Path) -> list[str]:
    png, txt, spec = d / "grafika.png", d / "grafika.txt", d / "grafika.json"
    if not png.exists() or not txt.exists(): return ["no grafika.png + grafika.txt (gfx/post_gfx.mjs)"]
    if spec.exists() and spec.stat().st_mtime > min(png.stat().st_mtime, txt.stat().st_mtime):
        return ["grafika.json is newer than grafika.png: run node gfx/post_gfx.mjs on this folder again"]
    if not shutil.which("tesseract"): return ["no tesseract: sudo apt install tesseract-ocr tesseract-ocr-pol (README, setup)"]
    drawn = txt.read_text()
    n = len(drawn.split())
    out = [] if WORDS[0] <= n <= WORDS[1] else [f"{n} words on the graphic, want {WORDS[0]}-{WORDS[1]}"]
    want = words(drawn)
    try: seen = ocr(png)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:  # no "pol" data, a broken png: a named problem, not a traceback
        return [*out, f"OCR failed ({' '.join(str(getattr(e, 'stderr', '') or e).split())[:160]}): is tesseract-ocr-pol installed?"]
    missing = [w for w in want if w not in seen]
    if want and 1 - len(missing) / len(want) < RECALL:
        out.append(f"OCR finds {len(want) - len(missing)}/{len(want)} of the drawn words (< {RECALL:.0%}): "
                   f"not readable alone, missing {' '.join(missing[:8])}")
    faint = sorted({w for w in want if 0 < seen.get(w, 1.0) < 1.0})
    if faint: out.append(f"low contrast (WCAG < {CONTRAST[0]}:1, large text < {CONTRAST[1]}:1): {' '.join(faint[:8])}")
    return out


def banned_phrases(voice: Path = VOICE) -> list[str]:
    """the bullets under "## Zakazane" in style/voice.md, lowercase; "długi myślnik" stands for the character itself"""
    # a renamed heading must not switch the gate off quietly: no file or no list = an error, not "nothing banned"
    text = voice.read_text(encoding="utf-8").replace("\r\n", "\n")
    sect = re.search(r"^## Zakazane\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    items = [m.strip().lower() for m in re.findall(r"^- (.+)$", sect.group(1), re.MULTILINE)] if sect else []
    if not items: raise ValueError(f'{voice}: no "## Zakazane" list of bullets, the banned-phrase check needs it')
    return ["\u2014" if i == "długi myślnik" else i for i in items]


def text_problems(text: str, hashtags: list[str], banned: list[str] | None = None) -> list[str]:
    out = []
    low = text.lower()
    hits = [b for b in (banned_phrases() if banned is None else banned) if b and b in low]
    if hits: out.append(f"phrases Kamil never writes (style/voice.md): {', '.join(repr(h) for h in hits)}")
    if len(hashtags) > MAX_TAGS: out.append(f"{len(hashtags)} hashtags, at most {MAX_TAGS}")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines: return [*out, 'no "text" in linkedin.json']
    last = lines[-1]
    if not last.endswith("?"): out.append(f"the post must end on a question for the comments, got {last!r} (resource goes in the line before)")
    n = len(text.split())
    if not WORDS_TEXT[0] <= n <= WORDS_TEXT[1]: out.append(f"{n} words of text, want {WORDS_TEXT[0]}-{WORDS_TEXT[1]} (the graphic carries the idea)")
    return out


def problems(d: Path) -> list[str]:
    """everything wrong with one post folder (grafika.png, grafika.txt, linkedin.json)"""
    out = graphic_problems(d)
    spec = d / "linkedin.json"
    if not spec.exists(): return [*out, "no linkedin.json"]
    try: s = json.loads(spec.read_text())
    except ValueError as e: return [*out, f"linkedin.json is not JSON ({e})"]
    text, tags = (s.get("text"), s.get("hashtags", [])) if isinstance(s, dict) else (None, None)
    if not isinstance(text, str) or not isinstance(tags, list): return [*out, 'linkedin.json needs {"text": "...", "hashtags": [...]}']
    return out + text_problems(text, tags)


def main(argv: list[str]) -> int:
    bad = 0
    for a in argv:
        for p in problems(Path(a)):
            print(f"{a}: {p}"); bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
