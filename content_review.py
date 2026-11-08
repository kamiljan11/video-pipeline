#!/usr/bin/env python3
"""content_review: read every card of a film for meaning before the render (film_check items long/short.meaning).

    python3 content_review.py <work> <film>
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
from film_check import TEXT_CARDS, Film, card_text_hash, card_texts, says_nothing

QUESTIONS = """For every card: "ok" + why (what it adds for a viewer who has not seen the film) or "cut".
1. does it say something the viewer needs (a number, a name, a step, a contrast), not one filler word?
2. does it make sense alone, without the sentence under it (who / what)?
3. is it the right moment (the sentence under it is about the same thing)?"""


def spoken(words: list[tuple[float, float, str]], t0: float, t1: float) -> str:
    return " ".join(w for s, _, w in words if t0 - 0.3 <= s <= t1).strip()


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
                    f"- said: {spoken(W, o['at'], o['at'] + o['dur'])[:400]}\n")
    md = f"# Content review: {name}\n\n{QUESTIONS}\n\n" + "\n".join(rows)
    return md, hashes


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    work, name = Path(argv[0]), argv[1]
    md, hashes = sheet(work, name)
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
