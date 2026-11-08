"""count_check.py: the count he says matches what the card shows (Skool CCC A4/E9/G4, P1 task 4).

"trzy kroki" over a card with six tiles, or a card showing 7 while he says "sześć", tells the viewer one of them is
wrong. A card is checked when he says a count (2-12, digits or Polish words in any case) from LEAD s before it comes
in to SPAN s after: its countable group (list items, the largest set of one kind of scene element) and every small
number it shows must be among the counts he says there. Saying nothing countable is not a claim, so nothing is checked.
film_check.py runs it as long.counts / short.counts.
"""
from __future__ import annotations

import re
from collections import Counter

LEAD, SPAN = 3.0, 4.0
LO, HI = 2, 12
# Polish cardinals in the cases speech uses ("trzy kroki", "trzech rzeczy", "z czterema", "dwoje dzieci")
WORDS = {2: ("dwa", "dwie", "dwóch", "dwoma", "dwu", "dwoje", "dwojga"), 3: ("trzy", "trzech", "trzema", "troje"),
         4: ("cztery", "czterech", "czterema", "czworo"), 5: ("pięć", "pięciu", "pięcioma"), 6: ("sześć", "sześciu", "sześcioma"),
         7: ("siedem", "siedmiu", "siedmioma"), 8: ("osiem", "ośmiu", "ośmioma"), 9: ("dziewięć", "dziewięciu"),
         10: ("dziesięć", "dziesięciu"), 11: ("jedenaście", "jedenastu"), 12: ("dwanaście", "dwunastu")}
WORD_N = {w: n for n, ws in WORDS.items() for w in ws}
COUNTABLE = ("chip", "node", "file", "win", "bar", "check", "stat")  # scene_lib kinds a viewer counts; lines, stamps, text are decoration


def said_count(word: str) -> int | None:
    w = re.sub(r"[^\w]", "", word.lower())
    if w.isdigit() and LO <= int(w) <= HI: return int(w)
    return WORD_N.get(w)


def card_count(spec: dict) -> int | None:
    if spec.get("type") == "list": return len(spec.get("items", [])) or None
    # a roadmap chapter card (plan2:L9) shows every part: "trzy części" over it counts its parts
    if spec.get("type") == "chap" and spec.get("chap_style") == "roadmap": return len(spec.get("parts") or []) or None
    kinds = Counter(e.get("k") for e in spec.get("els", []) if e.get("k") in COUNTABLE)
    n = max(kinds.values(), default=0)
    return n if n >= LO else None


def shown_numbers(spec: dict) -> set[int]:
    """small whole numbers the card puts on screen as a value (kw/count text, a scene "stat" value, a "steps" total)"""
    texts = [str(spec.get(k, "")) for k in ("text", "sub")] if spec.get("type") in ("kw", "count") else []
    texts += [str(e.get("value", e.get("text", ""))) for e in spec.get("els", []) if e.get("k") == "stat"]
    texts += [str(e.get("total", "")) for e in spec.get("els", []) if e.get("k") == "steps"]
    return {int(n) for t in texts for n in re.findall(r"(?<![\d.,])\d+(?![\d.,%])", t) if LO <= int(n) <= HI}


def early_items(o: dict) -> list[str]:
    """plan2:L8, a list placed with "item_words" (build_edl.py writes delays, items_said, item_lead into its overlay): no
    item on screen before he says it, so the items visible never outnumber the items said (an item counts as said from its
    word's start + the card's lead, the same few tenths a card comes in before its word)"""
    d, said, lead = o.get("delays"), o.get("items_said"), o.get("item_lead", 0.0)
    if not (isinstance(d, list) and isinstance(said, list)): return []
    return [f"{o['id']}: item {i + 1} on screen at {o['at'] + (v or 0.0):.2f} s, said at {t:.2f} s"
            for i, (v, t) in enumerate(zip(d, said, strict=False)) if o["at"] + (v or 0.0) < t + lead - 0.05]


def problems(overlays: list[dict], specs: dict[str, dict], said: list[tuple[float, str]]) -> list[str]:
    """said = (time in the finished film, word), viewer_pack.film_words"""
    out = []
    for o in overlays:
        sp = specs.get(o.get("id", ""))
        if not sp: continue
        out += early_items(o)
        counts = {n for t, w in said if o["at"] - LEAD <= t <= o["at"] + min(o["dur"], SPAN) and (n := said_count(w))}
        if not counts: continue
        n = card_count(sp)
        # an "upto" list (plan2:L8) shows items 1..k of the list: the count he says may be either
        shown = sp.get("upto") if sp.get("type") == "list" and isinstance(sp.get("upto"), int) else None
        if n and n not in counts and shown not in counts: out.append(f"{o['id']}: {n} on the card, says {sorted(counts)}")
        out += [f"{o['id']}: shows {v}, says {sorted(counts)}" for v in sorted(shown_numbers(sp) - counts)]
    return out
