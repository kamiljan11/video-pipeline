#!/usr/bin/env python3
"""ig_carousel: the Instagram carousels of a film's posts (Kamil 2026-11-10 "karuzele dopisz"): 5-10 slides each, not 2.

    python3 ig_carousel.py --posts <work>/posts.json --posts-dir <out>/posts --out <out>/instagram [--tags "#a,#b"]
                           [--only id,id] [--regen] [--no-render]

Per post with "make": true in posts.json (text: <posts-dir>/<id>/linkedin.json, the same words as the LinkedIn post):
  <out>/<id>/carousel.json   what each slide says: hook, 3-8 ideas, call (gfx/carousel_gfx.mjs documents the fields). Derived from the
                             post text ONCE; an existing file is kept, so a hand edit wins (--regen derives it again)
  <out>/<id>/caption.json    {"text", "hashtags", "alt": [one per slide]}: the post with "link w bio" for the link
  <out>/<id>/slide_NN.png/.txt   rendered by `node gfx/carousel_gfx.mjs` (skipped with --no-render)
Deriving never writes a word of its own except the fixed call line and the swipe hint (CALL, SWIPE below): the hook slide is
the post's first paragraph, an idea slide is one to three sentences of the body, the call slide is the post's closing
question. So every number on a slide is a number of the post, and ig_check.py --words holds it against the film.
Hashtags: posts.json item "hashtags_ig", else --tags, else style/brand.json "instagram_hashtags"."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import ig_check
import post_check

ROOT = Path(__file__).resolve().parent
BRAND = ROOT / "style" / "brand.json"
IDEAS = (3, 8)         # idea slides: a hook + 3..8 ideas + a call = 5..10 slides
IDEA_MAX = 260         # characters of one idea (gfx/carousel_gfx.mjs IDEA_MAX)
SHORT = 50             # a sentence shorter than this joins its neighbour: one idea needs more than a few words
CALL = "Napisz w komentarzu"   # the ONE call of the last slide (ig_check CTA); the question above it is what to answer
SWIPE = "Przesuń dalej →"
BIO = "Cały system opisany krok po kroku: link w bio"
ABBR = {"np", "tzw", "tj", "m.in", "itd", "itp", "ok", "ul", "dr", "prof", "nr", "godz", "ang", "pl"}
URL = re.compile(r"https?://\S+")
END = re.compile(r"[.!?…]+[”\"»)]*\s+")
UPPER = re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ„\"«(]")


def sentences(par: str) -> list[str]:
    """one paragraph -> sentences: split after . ! ? (and a closing quote) when a capital follows and the word is not an abbreviation"""
    out, start = [], 0
    for m in END.finditer(par):
        word = re.findall(r"[\w.]+", par[start:m.start() + 1])[-1:] or [""]
        if m.end() < len(par) and UPPER.match(par[m.end()]) and word[0].rstrip(".").lower() not in ABBR:
            out.append(par[start:m.end()].strip()); start = m.end()
    out.append(par[start:].strip())
    return [s for s in out if s]


def clause_split(s: str) -> tuple[str, str] | None:
    """cut one long sentence at the clause boundary (colon, semicolon, comma) nearest its middle; None = nowhere sensible"""
    cuts = [m.end() for m in re.finditer(r"[:;,]\s+", s) if 25 <= m.end() <= len(s) - 25]
    if not cuts: return None
    k = min(cuts, key=lambda c: abs(c - len(s) / 2))
    a, b = s[:k].rstrip(" ,;:"), s[k:].strip()
    a += "."  # the first idea ends with a full stop (it was cut at a colon, semicolon or comma)
    return a, b[0].upper() + b[1:]


def group(units: list[str], lo: int, hi: int) -> list[str]:
    """merge short neighbours, then pull the count into lo..hi: merge the shortest adjacent pair when too many, cut the longest
    sentence at a clause when too few; ValueError when the post cannot reach it"""
    us = list(units)
    i = 0
    while i < len(us) and len(us) > 1:  # a short sentence joins a neighbour that is still one sentence (two per slide at most)
        if len(us[i]) < SHORT:
            ok = [j for j in (i - 1, i + 1) if 0 <= j < len(us) and len(sentences(us[j])) == 1 and len(sentences(us[i])) == 1]
            if ok:
                j = ok[0]; a, b = sorted((i, j))
                us[a:b + 1] = [f"{us[a]} {us[b]}"]; i = a
                continue
        i += 1
    while len(us) > hi:
        k = min(range(len(us) - 1), key=lambda n: len(us[n]) + len(us[n + 1]))
        us[k:k + 2] = [f"{us[k]} {us[k + 1]}"]
    while len(us) < lo:
        order = sorted(range(len(us)), key=lambda n: -len(us[n]))
        for n in order:
            cut = clause_split(us[n])
            if cut: us[n:n + 1] = list(cut); break
        else: raise ValueError(f"only {len(us)} ideas in the post, want {lo}")
    for n, u in enumerate(us):  # one idea at most IDEA_MAX characters
        if len(u) > IDEA_MAX:
            cut = clause_split(u)
            if not cut or len(us) >= hi: raise ValueError(f"an idea of {len(u)} characters: {u[:50]}...")
            us[n:n + 1] = list(cut)
            return group(us, lo, hi)
    return us


def derive(text: str, author: str, theme: str = "cetus") -> dict:
    """the post text -> the carousel spec; ValueError names what the post lacks"""
    pars = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(pars) < 3: raise ValueError("the post has fewer than 3 paragraphs")
    hook, rest = pars[0], [p for p in pars[1:] if not URL.search(p)]
    close = None
    if rest and rest[-1].rstrip().endswith("?"):
        close = re.sub(r"^P\.?S\.?\s*", "", rest.pop(), flags=re.IGNORECASE).strip()
    n = post_check.hook_count(text)  # "5 rzeczy" in line 1 = exactly 5 idea slides (ig_check)
    lo, hi = (n, n) if n is not None else IDEAS
    if not IDEAS[0] <= lo <= hi <= IDEAS[1]: raise ValueError(f"line 1 promises {n} things, a carousel has {IDEAS[0]}-{IDEAS[1]} idea slides")
    ideas = group([s for p in rest for s in sentences(p)], lo, hi)
    brand = author.split("·")[-1].strip() if "·" in author else ""
    call = {"type": "call", "title": close or "", "call": CALL, "bio": BIO}
    if not close: del call["title"]
    spec = {"theme": theme, "author": author,
            "slides": [{"type": "hook", **({"kicker": brand} if brand else {}), "title": hook, "sub": SWIPE},
                       *({"type": "idea", "text": t} for t in ideas), call]}
    for s in spec["slides"]:
        if s["type"] == "idea" and has_call(s["text"]): raise ValueError(f"an idea slide holds a call ({s['text'][:40]}...): the call belongs on the last slide only")
    last = " ".join(v for k, v in spec["slides"][-1].items() if k != "type")
    if len(ig_check.CTA.findall(last)) != 1: raise ValueError(f"the last slide must hold exactly one call, has: {ig_check.CTA.findall(last)}")
    return spec


def has_call(t: str) -> bool:
    return bool(ig_check.CTA.search(t))


def caption_text(text: str) -> str:
    """the post for Instagram: a link is not clickable there, so the link line says 'link w bio'"""
    return "\n\n".join(re.sub(r"\s*:?\s*https?://\S+", ": link w bio", p) if URL.search(p) else p for p in re.split(r"\n\s*\n", text.strip()))


def alt_texts(spec: dict) -> list[str]:
    n = len(spec["slides"])
    kind = {"hook": "okładka", "idea": "myśl", "call": "wezwanie"}
    return [f"Slajd {i} z {n}, {kind[s['type']]}: " + " ".join(str(s[k]) for k in ("kicker", "head", "title", "text", "call", "bio") if s.get(k))
            for i, s in enumerate(spec["slides"], 1)]


def build(post_id: str, text: str, out: Path, author: str, tags: list[str], regen: bool = False) -> dict:
    """write carousel.json (kept when it exists) and caption.json of one post; -> the spec"""
    d = out / post_id
    d.mkdir(parents=True, exist_ok=True)
    f = d / "carousel.json"
    if f.exists() and not regen: spec = json.loads(f.read_text(encoding="utf-8"))
    else:
        spec = derive(text, author)
        f.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "caption.json").write_text(json.dumps({"text": caption_text(text), "hashtags": tags, "alt": alt_texts(spec)}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return spec


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--posts", required=True, type=Path, help="work/posts.json")
    ap.add_argument("--posts-dir", required=True, type=Path, help="out/posts")
    ap.add_argument("--out", required=True, type=Path, help="out/instagram (any folder)")
    ap.add_argument("--tags", default="", help="default hashtags, comma separated")
    ap.add_argument("--only", default="", help="post ids, comma separated")
    ap.add_argument("--regen", action="store_true", help="derive carousel.json again, dropping hand edits")
    ap.add_argument("--no-render", action="store_true", help="write the JSON only")
    a = ap.parse_args(argv)
    try: posts = json.loads(a.posts.read_text(encoding="utf-8"))["items"]
    except (OSError, ValueError, KeyError) as e: print(f"ig_carousel: {a.posts}: {e}", file=sys.stderr); return 2
    brand = json.loads(BRAND.read_text(encoding="utf-8")) if BRAND.exists() else {}
    default_tags = [t.strip() for t in a.tags.split(",") if t.strip()] or list(brand.get("instagram_hashtags", []))
    only = {x for x in a.only.split(",") if x}
    dirs, failed = [], 0
    for p in posts:
        if not p.get("make") or (only and p["id"] not in only): continue
        try:
            post = json.loads((a.posts_dir / p["id"] / "linkedin.json").read_text(encoding="utf-8"))
            spec_g = json.loads((a.posts_dir / p["id"] / "grafika.json").read_text(encoding="utf-8")) if (a.posts_dir / p["id"] / "grafika.json").exists() else {}
            build(p["id"], post["text"], a.out, spec_g.get("author", "Kamil Jan · Higher Minds"), p.get("hashtags_ig", default_tags), a.regen)
            dirs.append(str(a.out / p["id"]))
        except (OSError, ValueError, KeyError) as e:
            print(f"ig_carousel: {p['id']}: {e}", file=sys.stderr); failed += 1
    if dirs: print(f"ig_carousel: {len(dirs)} carousels written to {a.out}")
    if dirs and not a.no_render:
        r = subprocess.run(["node", str(ROOT / "gfx" / "carousel_gfx.mjs"), *dirs], cwd=ROOT, check=False)
        if r.returncode: return r.returncode
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
