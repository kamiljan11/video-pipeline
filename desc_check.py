#!/usr/bin/env python3
"""desc_check.py: the YouTube descriptions in out/youtube/ (round 2 Y0-Y5, S2, S3, S10, M1, M2; SYNTH2-yt-description).

One module for the description rules (limits in style/platform_limits.json, footer in style/brand.json). film_check.py
runs it as out.youtube (Out.out_youtube_meta); problems fail, warnings print.

Long (out/youtube/long.md, `## Opis`):
  FAIL  no "Rozdziały:" block inside the description, starting at 0:00, >= 3 rows (YouTube reads chapters only from
        the description, 11/14 creators with chapters put them there as one block)
  FAIL  `## Tagi` longer than tags_max_chars (YouTube refuses the upload); tags themselves are optional (13/16 set them)
  FAIL  more hashtags than the long's "fail" limit
  WARN  line 1 longer than line1_max (the fold shows about 2 lines), the first URL below line first_url_line_max
        (15/16 creators put a link in line 1-2), a KamilJan.com link without utm_ (utm.py), a hashtag in line 1-2,
        more hashtags than the long's warn limit (3: Polish creators 3-7, global 0), the footer of brand.json "description_footer" missing,
        the second chapter later than first_chapter_max_s (14/16: part 1 starts ~60-70 s), more than
        chapters_per_min_max chapters per minute (needs the film's length)
  WARN  no `## End screen` (which video or playlist the end screen points to, M1), an empty `## Przypięty komentarz`,
        a pinned comment with more than 1 URL or with neither a question nor a link (M2, n=0 in the data: WARN only)
Short (out/youtube/shorts/<id>.md, `## Opis`):
  FAIL  template leftovers ("goes here", "TODO", "00:00 Intro", "po jego publikacji"), no link to the long
        (a youtube.com / youtu.be URL, or {{LONG_URL}} that the publisher fills when the long is out)
  WARN  more than lines_max lines or words_max words before the long's link (32 shorts: 1-3 lines), a description
        that repeats the title (title_copy_max), {{LONG_URL}} not filled yet, more hashtags than the short's warn
        limit, #shorts (0/10 creators), chapters,
        no `## Powiązany film` (S10), the same line in two or more shorts (every short reads as its own)

  python3 desc_check.py <out dir> [<film seconds>]
  python3 desc_check.py --fill-long <youtube url of the long> <out dir>   (after the long is published, before the shorts)
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from pathlib import Path

import utm

ROOT = Path(__file__).resolve().parent
LIMITS = ROOT / "style" / "platform_limits.json"
BRAND = ROOT / "style" / "brand.json"
LONG_LINK = re.compile(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+|\{\{LONG_URL\}\}")
LEFTOVER = re.compile(r"goes here|\bTODO\b|^00:00 Intro$|po jego publikacji", re.IGNORECASE | re.MULTILINE)
HASHTAG = re.compile(r"(?<![\w&])#[^\W\d_][\w]*")
CHAPTER = re.compile(r"^(\d{1,2}):(\d\d)(?::(\d\d))?\s+\S", re.MULTILINE)


def section(md: str, name: str) -> str | None:
    """text under `## name` up to the next `## `, None when there is no such heading"""
    m = re.search(rf"^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip("\n") if m else None


def limits() -> dict:
    return json.loads(LIMITS.read_text())


def footer() -> str:
    return str(json.loads(BRAND.read_text()).get("description_footer", "")).strip()


def seconds(m: re.Match) -> int:
    a, b, c = m.group(1), m.group(2), m.group(3)
    return int(a) * 3600 + int(b) * 60 + int(c) if c else int(a) * 60 + int(b)


def chapters(desc: str) -> list[int]:
    """chapter starts (s) of the "Rozdziały:" block of a description: the timestamp lines after that label"""
    i = desc.find("Rozdziały:")
    if i < 0: return []
    return [seconds(m) for m in CHAPTER.finditer(desc[i:])]


def hashtags(text: str) -> list[str]:
    return HASHTAG.findall(text)


def lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip()]


def thesis(desc: str) -> list[str]:
    """the description lines before the long's link, any link, the footer or the hashtag line: what the viewer reads as the point"""
    out = []
    for ln in lines(desc):
        if LONG_LINK.search(ln) or utm.URL.search(ln) or (footer() and footer() in ln) or (hashtags(ln) and len(hashtags(ln)) == len(ln.split())): break
        out.append(ln)
    return out


def title_words(text: str) -> list[str]:
    return [w for w in re.findall(r"\w+", text.lower()) if len(w) > 3]


def fill_long(out: Path, url: str) -> list[Path]:
    """put the published long's URL in place of {{LONG_URL}} in every short description; the files changed"""
    if not LONG_LINK.fullmatch(url) or "{{" in url: raise ValueError(f"not a YouTube URL: {url!r}")
    done = []
    for f in sorted((out / "youtube" / "shorts").glob("*.md")):
        t = f.read_text()
        if "{{LONG_URL}}" in t: f.write_text(t.replace("{{LONG_URL}}", url)); done.append(f)
    return done


def long_check(md: str, film_s: float | None = None, lim: dict | None = None) -> tuple[list[str], list[str]]:
    lim = lim or limits()
    L, H = lim["long_desc"], lim["hashtags"]["long"]
    bad, warn = [], []
    desc = section(md, "Opis")
    if desc is None: return ["long.md: no `## Opis`"], []
    ch = chapters(desc)
    if len(ch) < 3 or ch[0] != 0: bad.append(f"long: the description has no 'Rozdziały:' block from 0:00 with >= 3 rows (found {len(ch)}): YouTube reads chapters only there")
    if any(b <= a for a, b in itertools.pairwise(ch)): bad.append("long: chapter times do not grow")
    tags = section(md, "Tagi")
    if tags and len(tags.strip()) > L["tags_max_chars"]: bad.append(f"long: tags are {len(tags.strip())} characters (YouTube takes <= {L['tags_max_chars']})")
    tg = hashtags(desc)
    if len(tg) > H["fail"]: bad.append(f"long: {len(tg)} hashtags (max {H['fail']})")
    elif len(tg) > H["warn"]: warn.append(f"long: {len(tg)} hashtags (want {H['warn']}; at most {H['fail']}, at the end)")
    ls = lines(desc)
    if ls and len(ls[0]) > L["line1_max"]: warn.append(f"long: description line 1 is {len(ls[0])} characters (want <= {L['line1_max']}: the fold shows ~2 lines)")
    first_url = next((i + 1 for i, ln in enumerate(ls) if utm.URL.search(ln)), None)
    if first_url is None or first_url > L["first_url_line_max"]:
        warn.append(f"long: the first link is in line {first_url or 'none'} (want line <= {L['first_url_line_max']}: the article or the offer, above the fold)")
    if any(hashtags(ln) for ln in ls[:2]): warn.append("long: a hashtag in line 1-2 (YouTube shows them above the title; keep the promise there)")
    for u in utm.untagged(desc): warn.append(f"long: {u} has no utm_ (utm.py tag)")
    if footer() and footer() not in re.sub(r"\?utm_[^\s]*", "", desc): warn.append("long: the footer of style/brand.json 'description_footer' is not in the description")
    if len(ch) >= 2 and ch[1] > L["first_chapter_max_s"]: warn.append(f"long: the first part starts at {ch[1] // 60}:{ch[1] % 60:02d} (want <= {L['first_chapter_max_s']} s)")
    if film_s and ch and len(ch) / (film_s / 60) > L["chapters_per_min_max"]:
        warn.append(f"long: {len(ch)} chapters in {film_s / 60:.1f} min = {len(ch) / (film_s / 60):.2f}/min (want <= {L['chapters_per_min_max']})")
    end = section(md, "End screen")
    if end is None: warn.append("long: no `## End screen` (which video or playlist the end screen points to)")
    elif not (utm.URL.search(end) or re.search(r"playlist|playlista|film|wideo|video", end, re.IGNORECASE)):
        warn.append("long: `## End screen` names no video or playlist (a URL, or 'playlista …' / 'film …')")
    pin = section(md, "Przypięty komentarz") or ""
    if not pin.strip(): warn.append("long: `## Przypięty komentarz` is missing or empty")
    else:
        urls = utm.URL.findall(pin)
        if len(urls) > 1: warn.append(f"long: the pinned comment has {len(urls)} links (want <= 1)")
        if "?" not in pin and not urls: warn.append("long: the pinned comment has neither a question nor a link")
    return bad, warn


def short_check(name: str, md: str, lim: dict | None = None) -> tuple[list[str], list[str]]:
    lim = lim or limits()
    S, H = lim["short_desc"], lim["hashtags"]["short"]
    bad, warn = [], []
    desc = section(md, "Opis")
    if desc is None: return [f"{name}: no `## Opis`"], []
    for m in LEFTOVER.finditer(desc): bad.append(f"{name}: template leftover {m.group(0)!r} in the description")
    if not LONG_LINK.search(desc): bad.append(f"{name}: no link to the long (a YouTube URL or {{{{LONG_URL}}}})")
    body = thesis(desc)
    if len(body) > S["lines_max"]: warn.append(f"{name}: {len(body)} description lines before the long's link (want <= {S['lines_max']})")
    nw = len(" ".join(body).split())
    if nw > S["words_max"]: warn.append(f"{name}: {nw} words before the long's link (want <= {S['words_max']})")
    title = section(md, "Tytuł") or ""
    tw = title_words(title)
    if tw and body and sum(w in title_words(" ".join(body)) for w in tw) / len(tw) >= S["title_copy_max"]:
        warn.append(f"{name}: the description repeats the title: say the short's point in other words")
    if "{{LONG_URL}}" in desc: warn.append(f"{name}: {{{{LONG_URL}}}} still in the description: run desc_check.py --fill-long <url> <out> once the long is out")
    tg = hashtags(desc)
    if len(tg) > H["fail"]: bad.append(f"{name}: {len(tg)} hashtags (max {H['fail']})")
    elif len(tg) > H["warn"]: warn.append(f"{name}: {len(tg)} hashtags (want <= {H['warn']})")
    if any(t.lower() == "#shorts" for t in tg): warn.append(f"{name}: #shorts (0/10 creators use it; YouTube knows a short by its shape)")
    if CHAPTER.search(desc): warn.append(f"{name}: chapters in a short")
    for u in utm.untagged(desc): warn.append(f"{name}: {u} has no utm_ (utm.py tag)")
    if section(md, "Powiązany film") is None: warn.append(f"{name}: no `## Powiązany film` (the long, set as the related video in Studio)")
    return bad, warn


def check(out: Path, film_s: float | None = None, shorts: list[str] | None = None) -> tuple[list[str], list[str]]:
    """(failures, warnings) of out/youtube; shorts = the ids to check (default: every shorts/*.md)"""
    lim = limits()
    yt = out / "youtube"
    bad, warn = (long_check((yt / "long.md").read_text(), film_s, lim) if (yt / "long.md").is_file() else (["no out/youtube/long.md"], []))
    files = [yt / "shorts" / f"{s}.md" for s in shorts] if shorts is not None else sorted((yt / "shorts").glob("*.md"))
    seen: dict[str, list[str]] = {}
    for f in files:
        if not f.is_file(): bad.append(f"no {f.relative_to(out)}"); continue
        md = f.read_text()
        b, w = short_check(f.stem, md, lim); bad += b; warn += w
        for ln in lines(section(md, "Opis") or ""):
            if not utm.URL.search(ln) and not LONG_LINK.search(ln) and len(ln) > 20: seen.setdefault(ln.strip(), []).append(f.stem)
    for ln, who in seen.items():
        if len(who) >= 2: warn.append(f"{', '.join(who)}: the same description line {ln[:60]!r}")
    return bad, warn


def main(argv: list[str]) -> int:
    if argv[:1] == ["--fill-long"]:
        if len(argv) != 3: print(__doc__, file=sys.stderr); return 2
        try: done = fill_long(Path(argv[2]), argv[1])
        except (OSError, ValueError) as e: print(f"FAILED desc_check --fill-long: {e}", file=sys.stderr); return 1
        print(f"filled {len(done)} short descriptions"); return 0
    if not 1 <= len(argv) <= 2: print(__doc__, file=sys.stderr); return 2
    try:
        bad, warn = check(Path(argv[0]), float(argv[1]) if len(argv) == 2 else None)
    except (OSError, ValueError, KeyError) as e:
        print(f"FAILED desc_check: {e}", file=sys.stderr); return 1
    print("\n".join(bad + [f"WARN {w}" for w in warn]) or "OK desc_check")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
