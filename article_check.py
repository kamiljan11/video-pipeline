"""article_check.py: a blog article for kamiljan.com made from one film (team/roles/artykul.md), checked before it is
published (publish_post.py) so the site's own tests (comfy-container src/data/posts.test.ts) cannot fail on it.

The article lives in out/blog/<slug>/article.json, next to its pictures:
  {"slug", "date": "YYYY-MM-DD", "youtube": "https://www.youtube.com/watch?v=..." | null,
   "cover": {"src": "cover.png", "width", "height", "alt": {"pl", "en"}},
   "sources": [{"label", "url"}],            # what the article adds beyond the film (Kamil 2026-11-07: "dodatkowe rzeczy")
   "body": {"pl" | "en": {"title", "description", "lead", "blocks": [{"t": "p"|"h2"|"list"|"code"|"img", ...}]}}}
Blocks are the site's (posts.ts Block); an "img" src is a file in the article folder, the publisher moves it to /blog/<slug>/.

Rules: the site's (both languages complete, description 50-300 chars, > 5 blocks, unique heading ids, alt > 20 chars,
pictures on disk, no em/en dash, no hype words) plus ours: detailed (MIN_WORDS Polish words, MIN_H2 sections, English at
least EN_RATIO of the Polish length), the film linked in both languages once it has a URL, at least one outside source
linked in the body, every number in the Polish text said in the film or sitting in a block with a source link, and no
phrase from style/voice.md "## Zakazane". Structure (PLAN 3.1-3.8, creator-study 2026-11-07): the film linked in the lead or
before the first h2, a lead of at most MAX_LEAD words with a digit, at least MIN_H2 sections ("Krok N" sections equal the N
the lead promises), the ending = a recap list + the film link + a last paragraph ending with "?", a number in the Polish title
said in the film. Soft rule (printed as WARN, never a failure, see warnings()): at least one picture per two sections.

  python3 article_check.py out/blog/<slug> [--words <film words json>]   prints the problems, rc 1 when there are any
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# style/voice.md "## Zakazane": one reader for posts and articles
from post_check import banned_phrases

MIN_WORDS = 1500    # Kamil 2026-11-07: "raczej szczegółowy"; a 20 min film says ~2500 words, the article goes deeper per part (how-to: 1500)
MIN_H2 = 5          # one section per step of a how-to
MAX_LEAD = 80       # lead = promise + number of parts + one measured credibility line
IMG_PER_H2 = 0.5    # warn below one picture per two sections
EN_RATIO = 0.6      # the English body may be tighter, not a summary
DESC = (50, 300)    # posts.test.ts
MIN_BLOCKS = 6      # posts.test.ts: more than 5
MIN_ALT = 21        # posts.test.ts: more than 20
HYPE = re.compile(r"\b(revolutionary|game-chang|seamless|unlock|rewolucyjn|przełomow)", re.IGNORECASE)  # posts.test.ts
DASH = re.compile(r"[–—]")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK = re.compile(r"\[[^\]]+\]\((https://[^)\s]+)\)")
YT = re.compile(r"^https://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_-]{11}(?:[&?][A-Za-z0-9_=&.-]*)?$")
NUM = re.compile(r"\d+(?:[.,]\d+)?")
STEPS = re.compile(r"\b(\d+)\s+(?:krok(?:i|ach|ów|ami|iem)?|steps?)\b", re.IGNORECASE)  # "w 4 krokach", "4 kroki", "in 4 steps"
STEP_H2 = re.compile(r"^\s*(?:krok|step)\s+\d+\b", re.IGNORECASE)
KINDS = {"p": ("text",), "h2": ("id", "text"), "list": ("items",), "code": ("code",), "img": ("src", "alt", "caption", "width", "height")}


def block_text(b: dict) -> str:
    return " ".join(b.get("items", [])) if b.get("t") == "list" else str(b.get("text", b.get("code", b.get("caption", ""))))


def said_numbers(words_file: Path | None) -> set[str] | None:
    """digits the film says (whisper writes most numbers as digits); None = no transcript given, the check is skipped"""
    if not words_file: return None
    try:  # whisper.cpp json, as film_check.word_times reads it
        text = " ".join(str(w.get("text", "")) for w in json.loads(words_file.read_text(encoding="utf-8"))["transcription"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        raise ValueError(f"{words_file}: not a whisper.cpp words json with \"transcription\" ({e!r})") from e
    return {n.replace(",", ".") for n in NUM.findall(text)}


def inside(folder: Path, src: object) -> bool:
    """a picture is a file IN the article folder: no absolute path, no ../ (publish_post hands it to ffmpeg)"""
    f = (folder / str(src)).resolve()
    return f.is_file() and f.is_relative_to(folder.resolve())


def meta_problems(a: dict, folder: Path) -> list[str]:
    out: list[str] = []
    slug = a.get("slug", "")
    if not (isinstance(slug, str) and SLUG.match(slug) and len(slug) <= 80): out.append(f"slug {slug!r}: lowercase words joined by '-', at most 80 chars")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(a.get("date", ""))): out.append(f"date {a.get('date')!r}: YYYY-MM-DD")
    yt = a.get("youtube")
    if yt is not None and not (isinstance(yt, str) and YT.match(yt)): out.append(f"youtube {yt!r}: a youtube.com/watch?v= or youtu.be link, or null before the film is up")
    cov = a.get("cover") or {}
    if not inside(folder, cov.get("src", "")): out.append(f"cover {cov.get('src')!r}: no such file in {folder}")
    for lang in ("pl", "en"):
        if len(str((cov.get("alt") or {}).get(lang, ""))) < MIN_ALT: out.append(f"cover alt ({lang}): describe the picture, more than {MIN_ALT - 1} chars")
    return out


def block_problems(blocks: list, folder: Path, tag: str) -> list[str]:
    out: list[str] = []
    if len(blocks) < MIN_BLOCKS: out.append(f"blocks {tag}: at least {MIN_BLOCKS}, got {len(blocks)}")
    ids = [x.get("id") for x in blocks if x.get("t") == "h2"]
    if len(ids) < MIN_H2: out.append(f"sections {tag}: at least {MIN_H2} h2, got {len(ids)}")
    if len(set(ids)) != len(ids): out.append(f"heading ids {tag}: not unique {ids}")
    for i, x in enumerate(blocks):
        need = KINDS.get(x.get("t"))
        if need is None: out.append(f"block {i} {tag}: type {x.get('t')!r}, want one of {sorted(KINDS)}"); continue
        if any(k not in x for k in need): out.append(f"block {i} {tag} ({x['t']}): needs {', '.join(need)}")
        if x["t"] != "img": continue
        if not inside(folder, x.get("src", "")): out.append(f"block {i} {tag}: picture {x.get('src')!r} not in {folder}")
        if len(str(x.get("alt", ""))) < MIN_ALT: out.append(f"block {i} {tag}: alt more than {MIN_ALT - 1} chars")
    return out


def loose_numbers(blocks: list, said: set[str], srcs: list[str]) -> list[str]:
    """numbers neither said in the film nor next to a link from "sources" (the film's own link backs nothing new)"""
    out: list[str] = []
    for x in blocks:
        t = block_text(x)
        if x.get("t") in ("code", "img") or any(u in srcs for u in LINK.findall(t)): continue
        loose = sorted({n for n in NUM.findall(t) if n.replace(",", ".") not in said and len(n) > 1})
        if loose: out.append(f"(pl) numbers not said in the film and without a source link: {', '.join(loose)} in {t[:60]!r}")
    return out


def structure_problems(b: dict, tag: str, yt: str | None) -> list[str]:
    """PLAN 3.1 film link up front, 3.2 lead, 3.3 promised steps, 3.5 ending"""
    out: list[str] = []
    blocks = b.get("blocks", [])
    lead = str(b.get("lead", ""))
    h2s = [i for i, x in enumerate(blocks) if x.get("t") == "h2"]
    head = lead + " " + " ".join(block_text(x) for x in blocks[: h2s[0] if h2s else len(blocks)])
    if yt and not any(same_film(u, yt) for u in LINK.findall(head)): out.append(f"{tag}: the film {yt} is not linked in the lead or before the first h2 (the reader meets it at once)")
    n_lead = len(lead.split())
    if n_lead > MAX_LEAD: out.append(f"lead {tag}: {n_lead} words, at most {MAX_LEAD} (promise, number of parts, one measured line)")
    if not re.search(r"\d", lead): out.append(f"lead {tag}: no digit (the promise carries a number: parts, minutes or a measured result)")
    promised = STEPS.search(lead)
    if promised:
        want, got = int(promised.group(1)), sum(1 for x in blocks if x.get("t") == "h2" and STEP_H2.match(str(x.get("text", ""))))
        if got != want: out.append(f"steps {tag}: the lead promises {want} steps, the text has {got} \"Krok N\" sections")
    tail = blocks[h2s[-1] + 1:] if h2s else blocks
    last = blocks[-1] if blocks else {}
    if last.get("t") != "p" or not block_text(last).rstrip().endswith("?"): out.append(f"ending {tag}: the last block must be a paragraph ending with '?' (the one question to the reader)")
    if not any(x.get("t") == "list" for x in tail[:-1]): out.append(f"ending {tag}: no recap list before the closing question (after the last h2)")
    if yt and not any(same_film(u, yt) for x in tail for u in LINK.findall(block_text(x))): out.append(f"ending {tag}: the film {yt} is not linked in the ending")
    return out


def same_film(url: str, yt: str) -> bool:
    return url.split("&")[0] == yt.split("&")[0]


def image_density(blocks: list, tag: str) -> list[str]:
    h2 = sum(1 for x in blocks if x.get("t") == "h2")
    img = sum(1 for x in blocks if x.get("t") == "img")
    return [f"pictures {tag}: {img} for {h2} sections, want at least one per two (stills, post graphics)"] if img < IMG_PER_H2 * h2 else []


def body_problems(b: dict, lang: str, folder: Path, yt: str | None, srcs: list[str]) -> tuple[list[str], str]:
    tag = f"({lang})"
    out: list[str] = []
    if len(str(b.get("title", ""))) <= 10: out.append(f"title {tag}: more than 10 chars")
    if not DESC[0] <= len(str(b.get("description", ""))) <= DESC[1]: out.append(f"description {tag}: {DESC[0]}-{DESC[1]} chars, got {len(str(b.get('description', '')))}")
    blocks = b.get("blocks", [])
    out += block_problems(blocks, folder, tag)
    whole = json.dumps(b, ensure_ascii=False)
    if DASH.search(whole): out.append(f"{tag}: an em or en dash (the site's test fails on it)")
    hype = HYPE.search(whole)
    if hype: out.append(f"{tag}: hype word {hype.group(0)!r} (the site's test fails on it)")
    text = " ".join(block_text(x) for x in blocks) + " " + str(b.get("lead", ""))
    links = LINK.findall(text)
    if yt and not any(same_film(u, yt) for u in links): out.append(f"{tag}: the film {yt} is not linked in the text")
    out += structure_problems(b, tag, yt)
    if not any(u in srcs for u in links): out.append(f"{tag}: no source from \"sources\" is linked in the text")
    return out, text


def problems(folder: Path, words_file: Path | None = None) -> list[str]:
    f = folder / "article.json"
    try:
        a = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"{f}: {e}"]
    out = meta_problems(a, folder)
    srcs = [str(s.get("url", "")) for s in a.get("sources", []) if isinstance(s, dict)]
    if not srcs or not all(u.startswith("https://") for u in srcs): out.append('"sources": at least one https source the article adds beyond the film')
    try:
        said = said_numbers(words_file)
    except ValueError as e:
        return [*out, str(e)]
    words = {}
    for lang in ("pl", "en"):
        b = (a.get("body") or {}).get(lang)
        if not isinstance(b, dict): out.append(f"body.{lang}: missing"); continue
        bad, text = body_problems(b, lang, folder, a.get("youtube"), srcs)
        out += bad
        words[lang] = len(text.split())
        if lang != "pl": continue
        seen = f"{b.get('title', '')} {b.get('description', '')} {text}".lower()  # title and description go to the page head too
        hits = [p for p in banned_phrases() if p and p in seen]
        if hits: out.append(f"(pl): phrases Kamil never writes (style/voice.md): {', '.join(map(repr, hits))}")
        if said is not None:
            out += loose_numbers(b.get("blocks", []), said, srcs)
            title_loose = sorted({n for n in NUM.findall(str(b.get("title", ""))) if n.replace(",", ".") not in said})
            if title_loose: out.append(f"title (pl): numbers not said in the film: {', '.join(title_loose)} in {str(b.get('title', ''))!r}")
    if words.get("pl", 0) < MIN_WORDS: out.append(f"(pl) {words.get('pl', 0)} words, want at least {MIN_WORDS} (detailed: each part of the film deeper)")
    if "en" in words and words["en"] < EN_RATIO * words.get("pl", 0): out.append(f"(en) {words['en']} words, want at least {EN_RATIO:.0%} of the Polish {words.get('pl', 0)}")
    return out


def warnings(folder: Path) -> list[str]:
    """soft rules: never fail the article (publish_post and film_check read problems() only)"""
    try:
        body = json.loads((folder / "article.json").read_text(encoding="utf-8")).get("body") or {}
    except (OSError, json.JSONDecodeError):
        return []
    return [w for lang in ("pl", "en") if isinstance(body.get(lang), dict) for w in image_density(body[lang].get("blocks", []), f"({lang})")]


def main(argv: list[str]) -> int:
    words = Path(argv[argv.index("--words") + 1]) if "--words" in argv else None
    dirs = [Path(x) for i, x in enumerate(argv) if not x.startswith("--") and (i == 0 or argv[i - 1] != "--words")]
    if not dirs: print(__doc__); return 2
    bad = 0
    for d in dirs:
        for p in problems(d, words): print(f"{d.name}: {p}"); bad += 1
        for w in warnings(d): print(f"{d.name}: WARN {w}")
    if not bad: print("article OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
