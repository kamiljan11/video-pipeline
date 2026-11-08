#!/usr/bin/env python3
"""ig_check: the Instagram form of a film (round 2 IG1, IG2, IG4, IG6; SYNTH2-instagram R1-R6, R11, R12).

    python3 ig_check.py [--words <film words json>] <out>/instagram

Folder (one carousel per post, Reels = the shorts):
  <id>/caption.json     {"text": "...", "hashtags": [...], "alt": ["slide 1 ...", ...]}
  <id>/slide_01.png ... the carousel slides, 1080x1350 (4:5), in order; the last one carries the call to action
  <id>/slide_NN.txt     optional: the words drawn on that slide (OCR source for the numbers rule)
  reels/<short>.json    {"text": "...", "hashtags": [...]}: the caption of the short posted as a Reel

Problems (exit 1) = platform limits and honest numbers only: more than limits.hashtags.fail tags, a caption over
caption_max characters, more than slides_max slides, alt[] not one per slide, a number the film never says (with
--words), "5 rzeczy" in line 1 with another number of content slides, a Reel caption with no line 1.
Everything else is a WARN (observe, SYNTH2-instagram section 0: thresholds change after our own Insights, IG7):
line 1 over line1_max, hook killers 1-4, a "?" in line 1, tags above warn, 3-4 or 11-20 slides, a clickable-looking
link in a caption (Instagram does not link it: "link w bio" or the first comment), the last slide's text without
exactly one call (zapisz / wyślij / skomentuj / udostępnij / obserwuj).
Limits: style/platform_limits.json "instagram" (one table per form, X2)."""
import json
import re
import sys
from pathlib import Path

import post_check

LIMITS_FILE = Path(__file__).resolve().parent / "style" / "platform_limits.json"
try:
    _ALL = json.loads(LIMITS_FILE.read_text(encoding="utf-8"))
    LIMITS = _ALL["instagram"]
    TAGS = {k: {"warn": int(v["warn"]), "fail": int(v["fail"])} for k, v in _ALL["hashtags"].items() if k.startswith("instagram")}
    NEED = {"caption_max", "line1_max", "slides_ok", "slides_max", "alt_max"}
    LIMITS_ERROR = ("" if {"instagram", "instagram_reel"} <= set(TAGS) and NEED <= set(LIMITS)
                    else f"{LIMITS_FILE}: needs hashtags instagram + instagram_reel and instagram {sorted(NEED)}")
except (OSError, ValueError, KeyError, TypeError) as e:  # a broken table is named in problems(), never a silent default
    LIMITS, TAGS, LIMITS_ERROR = {}, {}, f"{LIMITS_FILE}: cannot read the instagram limits ({e})"

CTA = re.compile(r"\b(zapisz|wyślij|wyslij|skomentuj|udostępnij|udostepnij|obserwuj|napisz)\b", re.IGNORECASE)
SLIDE = re.compile(r"^slide_(\d\d)\.png$")


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def tag_notes(tags: list, kind: str) -> tuple[list[str], list[str]]:
    lim = TAGS.get(kind)
    if not lim: return [], []
    if len(tags) > lim["fail"]: return [f"{len(tags)} hashtags, Instagram allows {lim['fail']}"], []
    return [], ([f"{len(tags)} hashtags, want at most {lim['warn']}"] if len(tags) > lim["warn"] else [])


def caption_notes(text: str, tags: list, kind: str) -> tuple[list[str], list[str]]:
    """the caption rules of a carousel and of a Reel: (problems, warnings)"""
    bad, warn = tag_notes(tags, kind)
    lines = _lines(text)
    if not lines: return [*bad, "the caption has no line 1"], warn
    if len(text) > LIMITS["caption_max"]: bad.append(f"caption: {len(text)} characters, Instagram allows {LIMITS['caption_max']}")
    first, lim = lines[0], LIMITS["line1_max"]
    if len(first) > lim: warn.append(f"line 1: {len(first)} characters, about {lim} show before 'więcej'")
    warn += [p for p in post_check.hook_problems(text) if "characters" not in p]  # killers 1-4 and "?", the length is the line above
    if post_check.URL.search(text): warn.append("a link in the caption: Instagram does not make it clickable (write 'link w bio' or put it in the first comment)")
    return bad, warn


def slides(d: Path) -> list[Path]:
    return sorted(p for p in d.iterdir() if SLIDE.match(p.name))


def carousel_notes(d: Path, said: set[str] | None) -> tuple[list[str], list[str]]:
    """one carousel folder: caption.json + slide_NN.png"""
    try: c = json.loads((d / "caption.json").read_text(encoding="utf-8"))
    except OSError: return ["no caption.json"], []
    except ValueError as e: return [f"caption.json is not JSON ({e})"], []
    text, tags, alt = (c.get("text"), c.get("hashtags", []), c.get("alt")) if isinstance(c, dict) else (None, None, None)
    if not isinstance(text, str) or not isinstance(tags, list): return ['caption.json needs {"text": "...", "hashtags": [...], "alt": [...]}'], []
    bad, warn = caption_notes(text, tags, "instagram")
    sl = slides(d)
    lo, hi, top = [*LIMITS["slides_ok"], LIMITS["slides_max"]]
    if not sl: bad.append("no slide_01.png")
    elif len(sl) > top: bad.append(f"{len(sl)} slides, Instagram allows {top}")
    elif not lo <= len(sl) <= hi: warn.append(f"{len(sl)} slides, want {lo}-{hi}")
    nums = [int(p.name[6:8]) for p in sl]  # SLIDE matched every name in slides()
    if nums != list(range(1, len(sl) + 1)): bad.append(f"slides are not numbered 01..{len(sl):02d} without gaps: {nums}")
    if not isinstance(alt, list) or len(alt) != len(sl) or not all(isinstance(a, str) and a.strip() for a in alt):
        bad.append(f"alt: want one non-empty text per slide ({len(sl)}), got {len(alt) if isinstance(alt, list) else 'none'}")
    elif any(len(a) > LIMITS["alt_max"] for a in alt): warn.append(f"an alt text over {LIMITS['alt_max']} characters")
    drawn = "\n".join(p.with_suffix(".txt").read_text(encoding="utf-8", errors="replace") for p in sl if p.with_suffix(".txt").exists())
    n = post_check.hook_count(text)
    if n is not None and sl and n != len(sl) - 2: bad.append(f"line 1 promises {n} things, the carousel has {len(sl) - 2} content slides (cover and call slide not counted)")
    if sl:
        last = sl[-1].with_suffix(".txt")
        calls = CTA.findall(last.read_text(encoding="utf-8", errors="replace")) if last.exists() else None
        if calls is None: warn.append(f"no {last.name}: the call on the last slide cannot be checked")
        elif len(calls) != 1: warn.append(f"the last slide has {len(calls)} calls ({', '.join(calls) or 'none'}), want exactly 1")
    return bad + post_check.number_problems(text, drawn, said), warn


def reel_notes(p: Path) -> tuple[list[str], list[str]]:
    try: r = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e: return [f"not JSON ({e})"], []
    if not isinstance(r, dict) or not isinstance(r.get("text"), str) or not isinstance(r.get("hashtags", []), list):
        return ['want {"text": "...", "hashtags": [...]}'], []
    return caption_notes(r["text"], r.get("hashtags", []), "instagram_reel")


def check(ig: Path, words_file: Path | None = None) -> tuple[list[str], list[str]]:
    """every carousel and Reel under <out>/instagram: (problems, warnings), each line led by its folder or file"""
    if LIMITS_ERROR: return [LIMITS_ERROR], []
    bad, warn = [], []
    if not ig.is_dir(): return [*bad, f"no {ig}"], []
    try: said = post_check.article_said(words_file)
    except ValueError as e: return [*bad, str(e)], []
    posts = sorted(d for d in ig.iterdir() if d.is_dir() and d.name != "reels")
    reels = sorted((ig / "reels").glob("*.json")) if (ig / "reels").is_dir() else []
    if not posts and not reels: bad.append(f"{ig}: no carousel folder and no reels/*.json")
    for d in posts:
        b, w = carousel_notes(d, said)
        bad += [f"{d.name}: {x}" for x in b]; warn += [f"{d.name}: {x}" for x in w]
    for p in reels:
        b, w = reel_notes(p)
        bad += [f"reels/{p.name}: {x}" for x in b]; warn += [f"reels/{p.name}: {x}" for x in w]
    return bad, warn


def main(argv: list[str]) -> int:
    words = None
    if "--words" in argv:
        i = argv.index("--words")
        if i + 1 >= len(argv): print("--words needs a file", file=sys.stderr); return 2
        words, argv = Path(argv[i + 1]), argv[:i] + argv[i + 2:]
    if len(argv) != 1: print("usage: ig_check.py [--words <film words json>] <out>/instagram", file=sys.stderr); return 2
    bad, warn = check(Path(argv[0]), words)
    for b in bad: print(b)
    for w in warn: print(f"WARN {w}")
    if not bad: print(f"instagram OK ({len(warn)} warnings)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
