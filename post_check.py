"""post_check.py: a LinkedIn post that keeps the measured habits of the top creators (style/REF-posts-top.md).

- The graphic stands alone (Kamil 2026-11-05: "grafika sama musi nieść przekaz"). gfx/post_gfx.mjs writes grafika.png and
  grafika.txt (the words it drew); OCR has to find at least RECALL of those words in the picture: a word cut at an edge,
  hidden under another element is missing. Tesseract binarises adaptively and reads even navy on navy, so contrast is
  measured on its own: WCAG AA inside every word box. Word count WORDS (REF P1: class A graphics).
- The text completes the graphic: at most MAX_TAGS hashtags (WARN above 0: median 0 in 94 posts, round 2 6/6), at most
  MAX_URLS link (round 2 LI2), the last line is a question for the comments ("P.S. ...?" counts) and the resource (film,
  repo) sits in the line before it, at least MIN_TEXT words (WARN outside WORDS_TEXT: Kamil's rule, not the sample),
  WARN without "cta_variant" (question / ps, round 2 LI4), "5 rzeczy" in the hook = 5 list lines in the text (LI5). The closing question is Kamil's call (2026-11-07, Skool CCC C07/C10/C17) against our sample (4/68
  top posts end on a question); the weekly review shows whether comments grow.
- Line 1 is the hook (SYNTH-linkedin W1, PLAN 4.1): no greeting, filler or list-title opener (hook_check killers 1-4 with
  style/hook_lint.json), at most HOOK_CHARS characters (LinkedIn cuts the feed at "see more"), no "?" (the question closes the post).
- Numbers are honest (PLAN 4.2): every number in the text and on the graphic has to be said in the film (article_check.said_numbers
  on the film's whisper words json), blocking. Without a words file the check is skipped (a note, not a failure).
- A count in the hook ("5 rzeczy", "Trzy rzeczy") equals the list items in grafika.json (PLAN 4.3, only for a "list" graphic).
film_check.py out.posts calls problems() for every post folder.

  python3 post_check.py [--words <film words json>] <post dir>...   prints the problems, rc 1 when there are any
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import count_check
import hook_check  # killers 1-4 and the list nouns, one source with the shorts (style/hook_lint.json)
import utm  # KamilJan.com links say where the click came from (round 2 X1)

RECALL = 0.85  # [PROP] share of the drawn words OCR must find; measured 1.00 on all 9 film 2 graphics (2026-11-05); dark-on-dark text falls far below (tests)
CONTRAST = (4.5, 3.0)  # WCAG AA: normal text, large text (a word box at least LARGE px high on the 1080 px graphic)
LARGE = 40
WORDS = (15, 230)  # same range as gfx/post_gfx.mjs WORDS
LIMITS_FILE = Path(__file__).resolve().parent / "style" / "platform_limits.json"
try:  # a broken data file is named in problems(), never a traceback at import (film_check imports this module)
    LIMITS, LIMITS_ERROR = json.loads(LIMITS_FILE.read_text())["hashtags"]["linkedin"], ""
    LIMITS = {"warn": int(LIMITS["warn"]), "fail": int(LIMITS["fail"])}
except (OSError, ValueError, KeyError, TypeError) as e:
    LIMITS, LIMITS_ERROR = {"warn": 0, "fail": 3}, f"style/platform_limits.json cannot be read ({e!r}): hashtag limits fell back to 0/3"
MAX_TAGS = LIMITS["fail"]  # style/platform_limits.json (round 2 X2): warn above LIMITS["warn"] (0), fail above this
MIN_TEXT = 20  # fewer words = a caption, not a post (round 2 LI3: the 60-130 range is a WARN, this stays a problem)
MAX_URLS = 1   # round 2 LI2 (6/6): one link in the text, the rest in the first comment
CTA_VARIANTS = ("question", "ps")  # round 2 LI4: logged per post for the ADR-0015 review
LIST_LINE = re.compile(r"^\s*(?:[-•*–]|\d+[.)])\s+\S")
URL = utm.URL
VOICE = Path(__file__).resolve().parent / "style" / "voice.md"  # "## Zakazane": phrases Kamil never writes (one per bullet)
WORDS_TEXT = (60, 130)  # [PROP] REF-posts-top P2 point 6: about 60-120, from Kamil's rule, not from the sample
WORD = re.compile(r"[\w%]+")
HOOK_CHARS = 140  # REF-posts-top: the feed shows about this much before "see more"
HOOK_KILLERS = ("greeting", "title", "filler", "vague")  # hook_check.problems messages 1-4; "no stake" and the word cap are the short's rules
NUM = re.compile(r"\d+(?:[.,]\d+)?")
COUNT_WORDS = {**count_check.WORD_N, "jeden": 1, "jedna": 1, "jedno": 1}  # every case ("trzech rzeczy"), one map with count_check


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


def hook_problems(text: str) -> list[str]:
    """PLAN 4.1: line 1 of the post (the hook): killers 1-4, at most HOOK_CHARS characters, no question mark"""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines: return []
    first = lines[0]
    out = [f"line 1: {p}" for p in hook_check.problems(first) if p.startswith(HOOK_KILLERS)]
    if len(first) > HOOK_CHARS: out.append(f"line 1: {len(first)} characters, at most {HOOK_CHARS} (the feed cuts it at 'see more')")
    if "?" in first: out.append("line 1: a question mark (the hook states the result; the question closes the post)")
    return out


def hook_count(text: str, listicle: list[str] | None = None) -> int | None:
    """the number of things line 1 promises ("5 rzeczy", "Trzy drobne rzeczy"): a count word or digits with a list noun (hook_lint
    "listicle") in the next 3 words; None when the hook promises no list"""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    nouns = hook_check.lists()["listicle"] if listicle is None else listicle
    toks = WORD.findall(lines[0].lower()) if lines else []
    for i, t in enumerate(toks):
        n = int(t) if t.isdigit() else COUNT_WORDS.get(t)
        if n is not None and any(hook_check._match(e, w) for w in toks[i + 1:i + 4] for e in nouns): return n
    return None


def spoken_numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in NUM.findall(text)}


def number_problems(text: str, drawn: str, said: set[str] | None) -> list[str]:
    """PLAN 4.2: numbers of the text and of the graphic that the film never says (said None = no words file: skipped)"""
    if said is None: return []
    out = []
    for where, src in (("text", text), ("graphic", drawn)):
        gone = sorted(spoken_numbers(src) - said, key=float)
        if gone: out.append(f"numbers in the {where} that the film does not say: {', '.join(gone)} (say them in the film or drop them)")
    return out


def count_problems(text: str, spec: object) -> list[str]:
    """PLAN 4.3: "5 rzeczy" in the hook = 5 items of a "list" graphic (other graphic types carry no list to count)"""
    n = hook_count(text)
    if n is None or not isinstance(spec, dict) or spec.get("type") != "list" or not isinstance(spec.get("items"), list): return []
    k = len(spec["items"])
    return [] if k == n else [f"the hook promises {n} things, grafika.json lists {k}"]


def text_count_problems(text: str, spec: object) -> list[str]:
    """round 2 LI5: "5 rzeczy:" in the hook = 5 list lines in the TEXT, when the graphic is not a "list" (that one is
    count_problems)"""
    n = hook_count(text)
    if n is None or (isinstance(spec, dict) and spec.get("type") == "list"): return []
    k = sum(1 for ln in text.splitlines()[1:] if LIST_LINE.match(ln))
    return [] if k in (0, n) else [f"the hook promises {n} things, the text lists {k}"]


def text_problems(text: str, hashtags: list[str], banned: list[str] | None = None) -> list[str]:
    out = []
    low = text.lower()
    hits = [b for b in (banned_phrases() if banned is None else banned) if b and b in low]
    if hits: out.append(f"phrases Kamil never writes (style/voice.md): {', '.join(repr(h) for h in hits)}")
    if len(hashtags) > MAX_TAGS: out.append(f"{len(hashtags)} hashtags, at most {MAX_TAGS}")
    urls = URL.findall(text)
    if len(urls) > MAX_URLS: out.append(f"{len(urls)} links in the text, at most {MAX_URLS} (the rest go in the first comment, team/roles/social.md)")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines: return [*out, 'no "text" in linkedin.json']
    last = lines[-1]
    if not last.endswith("?"): out.append(f"the post must end on a question for the comments, got {last!r} (resource goes in the line before)")
    n = len(text.split())
    if n < MIN_TEXT: out.append(f"{n} words of text, at least {MIN_TEXT} (the text completes the graphic)")
    return out


def text_warnings(text: str, hashtags: list[str], cta_variant: object = None) -> list[str]:
    """round 2 LI1, LI3, LI4, LI5: observe until our own posts show an effect"""
    out = []
    if LIMITS["warn"] < len(hashtags) <= MAX_TAGS: out.append(f"{len(hashtags)} hashtags (median 0 in the study, want {LIMITS['warn']})")
    n = len(text.split())
    if n >= MIN_TEXT and not WORDS_TEXT[0] <= n <= WORDS_TEXT[1]: out.append(f"{n} words of text, better {WORDS_TEXT[0]}-{WORDS_TEXT[1]} (the graphic carries the idea)")
    if cta_variant not in CTA_VARIANTS: out.append(f"no cta_variant ({' / '.join(CTA_VARIANTS)}) in linkedin.json: the ADR-0015 review will compare comments per variant")
    for u in utm.untagged(text): out.append(f"{u} has no utm_ (utm.py tag ... linkedin post <film>)")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines and lines[0].endswith(":") and not any(LIST_LINE.match(ln) for ln in lines[1:]): out.append("line 1 ends on ':' but no list follows")
    return out


def drawn_text(d: Path) -> str:
    """the words on the graphic: grafika.txt, else every string of grafika.json"""
    txt, spec = d / "grafika.txt", d / "grafika.json"
    if txt.exists(): return txt.read_text()
    if not spec.exists(): return ""

    def strings(v: object) -> list[str]:
        if isinstance(v, str): return [v]
        if isinstance(v, list): return [x for e in v for x in strings(e)]
        if isinstance(v, dict): return [x for e in v.values() for x in strings(e)]
        return [str(v)] if isinstance(v, (int, float)) and not isinstance(v, bool) else []
    try: return " ".join(strings(json.loads(spec.read_text())))
    except ValueError: return ""


def article_said(words_file: Path | None) -> set[str] | None:
    """numbers the film says, digits and spelled out (article_check.said_numbers: one rule for posts and the article)"""
    import article_check  # late: article_check imports banned_phrases from here
    return article_check.said_numbers(words_file)


def warnings(d: Path) -> list[str]:
    """PLAN 4.1 line-1 rules as warnings: the study's text rules are observe until our own posts confirm them (review
    2026-11-07, SYNTH-linkedin.md); the numbers stay blocking"""
    try: s = json.loads((d / "linkedin.json").read_text())
    except (OSError, ValueError): return []
    if not isinstance(s, dict) or not isinstance(s.get("text"), str): return []
    raw = s.get("hashtags")
    tags: list[str] = [str(t) for t in raw] if isinstance(raw, list) else []
    return hook_problems(s["text"]) + text_warnings(s["text"], tags, s.get("cta_variant"))


def problems(d: Path, words_file: Path | None = None) -> list[str]:
    """everything wrong with one post folder (grafika.png, grafika.txt, linkedin.json); words_file = the film's whisper words
    json (plan "words"), without it the numbers are not checked against the film"""
    out = ([LIMITS_ERROR] if LIMITS_ERROR else []) + graphic_problems(d)
    spec = d / "linkedin.json"
    if not spec.exists(): return [*out, "no linkedin.json"]
    try: s = json.loads(spec.read_text())
    except ValueError as e: return [*out, f"linkedin.json is not JSON ({e})"]
    text, tags = (s.get("text"), s.get("hashtags", [])) if isinstance(s, dict) else (None, None)
    if not isinstance(text, str) or not isinstance(tags, list): return [*out, 'linkedin.json needs {"text": "...", "hashtags": [...]}']
    out += text_problems(text, tags)
    gj = d / "grafika.json"
    try: g = json.loads(gj.read_text()) if gj.exists() else None
    except ValueError: g = None  # graphic_problems / post_gfx name a broken spec
    out += count_problems(text, g) + text_count_problems(text, g)
    try: said = article_said(words_file)
    except ValueError as e: return [*out, str(e)]
    return out + number_problems(text, drawn_text(d), said)


def main(argv: list[str]) -> int:
    words = None
    if "--words" in argv:
        i = argv.index("--words")
        if i + 1 >= len(argv): print("--words needs a file", file=sys.stderr); return 2
        words, argv = Path(argv[i + 1]), argv[:i] + argv[i + 2:]
    else: print("note: no --words <film words json>: numbers are not checked against the film", file=sys.stderr)
    bad = 0
    for a in argv:
        for p in problems(Path(a), words):
            print(f"{a}: {p}"); bad += 1
        for w in warnings(Path(a)): print(f"{a}: WARN {w}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
