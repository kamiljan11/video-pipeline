#!/usr/bin/env python3
"""content_review: read every card of a film for meaning before the render (film_check items long/short.meaning).

    python3 content_review.py <work> <film>
    python3 content_review.py <work> thumbs     the words on every long thumbnail and Short cover (thumbs.json) ->
                                                work/content_review_thumbs.{md,json} (film_check out.thumbs_read)
        writes work/content_review_<film>.md (each card: its words + the sentence said under it) and adds a
        {"verdict": "todo"} entry to work/content_review_<film>.json for every card that is new or changed since its
        review (card_text_hash). Reviewed cards keep their verdict.

Then the editor reads the sheet and sets, per card, "verdict": "ok" with "why" = what the card adds for a viewer who
has not seen the film, or "cut" (and takes the card out of the plan). The question for every card:
  1. does it say something the viewer needs (a number, a name, a step, a contrast), not one filler word?
  2. does it make sense alone, without the sentence under it (who / what)?
  3. is it the right moment (the sentence under it is about the same thing)?
"""
import json
import sys
from pathlib import Path

import timeline
from film_check import (
    TEXT_CARDS,
    Film,
    card_text_hash,
    card_texts,
    load,
    says_nothing,
    thumb_texts,
)

QUESTIONS = """For every card: "ok" + why (what it adds for a viewer who has not seen the film) or "cut".
1. does it say something the viewer needs (a number, a name, a step, a contrast), not one filler word?
2. does it make sense alone, without the sentence under it (who / what)?
3. is it the right moment (the sentence under it is about the same thing)?"""

THUMB_QUESTIONS = """For every thumbnail / cover: "ok" + why, or "cut" (and change the words in thumbs.json).
The stranger test: someone scrolling who never heard of the film sees only this picture and these words.
1. what do they understand, in one sentence of their own? (if "nothing" or "a number without a subject": cut)
2. does it make them want the answer the film gives (a result, a question, a contrast), not just name a topic?
3. is the promise in the film (the long / the short says it)? Kamil 2026-11-08: "18% LECI NA SLEPO ... bez sensu"."""


def thumbs_sheet(work: Path) -> tuple[str, dict]:
    spec = load(work / "thumbs.json", "thumbs.json")
    texts = thumb_texts(spec)
    frames = {f"long_{v['id']}": v for v in spec.get("long", [])} | {f"cover_{v['id']}": v for v in spec.get("shorts", [])}
    rows = [f"### {i}\n- words: {' | '.join(t.values()) or '(no words)'}\n- frame: {frames[i].get('frame', '-')}"
            f" (pick {frames[i].get('pick', {}).get('t', '-') if isinstance(frames[i].get('pick'), dict) else '-'})\n" for i, t in texts.items()]
    return f"# Content review: thumbnails and covers\n\n{THUMB_QUESTIONS}\n\n" + "\n".join(rows), {i: card_text_hash(t) for i, t in texts.items()}


def spoken(words: list[tuple[float, float, str]], t0: float, t1: float) -> str:
    return " ".join(w for s, _, w in words if t0 - 0.3 <= s <= t1).strip()


MEMES = Path(__file__).resolve().parent / "style" / "memes.json"


def meme_lines(sp: dict) -> str:
    """a meme card shows its template's joke, the role of each box beside the text put there, and the wrong use (note 44)"""
    if sp.get("type") != "meme": return ""
    t = json.loads(MEMES.read_text(encoding="utf-8")).get(str(sp.get("meme")), {})
    raw = sp.get("text")
    texts: list = raw if isinstance(raw, list) else [raw]
    roles = "".join(f"  - box {i + 1}: {r} <- {texts[i] if i < len(texts) else '(empty)'!r}\n" for i, r in enumerate(t.get("roles") or []))
    return f"- meme joke: {t.get('joke', '(not in style/memes.json)')}\n{roles}- wrong use: {t.get('misfit', '?')}\n"


def scene_lines(sp: dict) -> str:
    """a drawn scene lists its pieces in order (note 48 "coś bez sensu trochę rysujesz"): each piece must show something
    the sentence at its second says, else it is cut"""
    if sp.get("type") != "scene": return ""
    rows = []
    for e in sorted(sp.get("els") or [], key=lambda e: float(e.get("at") or 0)):
        words = " ".join(str(e.get(k)) for k in ("text", "name", "title", "cmd") if e.get(k)) or ", ".join(
            str(r.get("t") if isinstance(r, dict) else r) for r in e.get("rows") or []) or e.get("on", "")
        rows.append(f"  - {float(e.get('at') or 0):5.1f} s {e.get('k')}: {str(words)[:80]}\n")
    return "- pieces (each must show what is said at its second):\n" + "".join(rows)


def sheet(work: Path, name: str) -> tuple[str, dict]:
    f = Film(work, name)
    plan = f.plan
    words_file = work / plan["words"]
    raw = json.loads(words_file.read_text(encoding="utf-8"))["transcription"]
    exact = bool(f.edl.get("seg_exact"))
    W = [(timeline.src2out(x["offsets"]["from"] / 1000, f.edl["segments"], exact), 0.0, x["text"].strip()) for x in raw]
    W = [w for w in W if w[2]]
    rows, hashes = [], {}
    for o in sorted(f.ovs, key=lambda o: o["at"]):
        sp = f.specs.get(o["id"])
        if not sp: continue
        h = card_text_hash(sp); hashes[o["id"]] = h
        texts = card_texts(sp)
        flag = " **FILLER?**" if sp.get("type") in TEXT_CARDS and says_nothing(str(sp.get("title") or sp.get("text") or ""), str(sp.get("sub") or "")) else ""
        m, s = divmod(o["at"], 60)
        rows.append(f"### {o['id']} ({sp.get('type')}, {int(m)}:{s:04.1f}, {o['dur']:.1f} s){flag}\n"
                    f"- on screen: {' | '.join(t for t in texts if t.strip())[:400] or '(no words)'}\n"
                    f"- said: {spoken(W, o['at'], o['at'] + o['dur'])[:400]}\n" + meme_lines(sp) + scene_lines(sp))
    md = f"# Content review: {name}\n\n{QUESTIONS}\n\n" + "\n".join(rows)
    return md, hashes


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    work, name = Path(argv[0]), argv[1]
    md, hashes = thumbs_sheet(work) if name == "thumbs" else sheet(work, name)
    (work / f"content_review_{name}.md").write_text(md, encoding="utf-8")
    jf = work / f"content_review_{name}.json"
    rev = json.loads(jf.read_text(encoding="utf-8")) if jf.exists() else {}
    todo = 0
    for i, h in hashes.items():
        if not isinstance(rev.get(i), dict) or rev[i].get("hash") != h:
            rev[i] = {"verdict": "todo", "why": "", "hash": h}; todo += 1
    for i in [k for k in rev if k not in hashes]: del rev[i]  # cards gone from the plan
    jf.write_text(json.dumps(rev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{name}: {len(hashes)} cards, {todo} to read -> {jf.name} (sheet {work / f'content_review_{name}.md'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
