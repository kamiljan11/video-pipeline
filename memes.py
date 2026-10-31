#!/usr/bin/env python3
"""memes.py add <slug>: fetch the picture of a style/memes.json template from imgflip into render/memes/<slug>.<ext> plus
<slug>.json (name, size, text boxes, source URL) for the 9:16 "meme" card (gfx/render.mjs). The pictures are third-party, so
they stay out of the public repo (render/ is ignored). Only https://i.imgflip.com pictures, JPEG or PNG, at most MAX_BYTES.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
CATALOGUE = os.path.join(ROOT, "style", "memes.json")
OUT = os.environ.get("VP_MEMES", os.path.join(ROOT, "render", "memes"))
API = "https://api.imgflip.com/get_memes"
MAX_BYTES = 5_000_000


def kind(data: bytes) -> str:
    """file extension from the picture's first bytes; anything but JPEG/PNG is refused (named)"""
    if data.startswith(b"\xff\xd8\xff"): return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return "png"
    raise ValueError("not a JPEG or PNG picture")


def entry(slug: str, tpl: dict, cat: dict, ext: str, today: str) -> dict:
    """the <slug>.json render.mjs reads: imgflip's name, size and URL, our own text boxes"""
    if not str(tpl.get("url", "")).startswith("https://i.imgflip.com/"):
        raise ValueError(f"picture URL outside i.imgflip.com: {tpl.get('url')!r}")
    return {"name": tpl["name"], "img": f"{slug}.{ext}", "width": int(tpl["width"]), "height": int(tpl["height"]),
            "boxes": cat["boxes"], "source": tpl["url"], "fetched": today}


def get(url: str, limit: int) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "video-pipeline memes.py"}), timeout=30) as r:
        data = r.read(limit + 1)
    if len(data) > limit: raise ValueError(f"{url}: over {limit} bytes")
    return data


def add(slug: str) -> str:
    with open(CATALOGUE, encoding="utf-8") as f: cat = json.load(f)
    if slug.startswith("_") or slug not in cat: raise ValueError(f"no template {slug!r} in {CATALOGUE}")
    tpl = next((m for m in json.loads(get(API, MAX_BYTES))["data"]["memes"] if m["id"] == cat[slug]["imgflip"]), None)
    if tpl is None: raise ValueError(f"imgflip id {cat[slug]['imgflip']} not in its current list ({API})")
    if not tpl["url"].startswith("https://i.imgflip.com/"): raise ValueError(f"picture URL outside i.imgflip.com: {tpl['url']!r}")
    data = get(tpl["url"], MAX_BYTES)
    e = entry(slug, tpl, cat[slug], kind(data), datetime.datetime.now(datetime.UTC).date().isoformat())
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, e["img"]), "wb") as f: f.write(data)
    with open(os.path.join(OUT, f"{slug}.json"), "w", encoding="utf-8") as f: json.dump(e, f, ensure_ascii=False, indent=1)
    return os.path.join(OUT, e["img"])


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "add": sys.exit("usage: memes.py add <slug>  (slugs: style/memes.json)")
    try: print(add(sys.argv[2]))
    except (ValueError, OSError, KeyError) as ex: sys.exit(f"FAILED memes {sys.argv[2]}: {ex}")
