#!/usr/bin/env python3
"""research_gate: no film render while research meant for that form is still open or "done" without proof in the film.

    python3 research_gate.py <long|shorts|thumbs> [--ledger path]   exit 1 + the open items

Kamil 2026-11-08, after the 2026-11-04 night render had 0 of 24 Long research items in it: "dlaczego nic nie weszlo!?
przeciez pisalem ci 5 krotnie ze po to robisz reserache zeby ulepszyc video pipeline i dopiero zregenerowac cale video".
For every ledger item of the form (creator-study/round2/ledger.jsonl):
  todo                      -> open: blocks the render
  merged (ref = carrier id) -> open while the carrier is open
  done                      -> must name the film_check item that measures it in the film: ref contains
                               "check:<id>" and <id> is in style/checklist.json (code alone is not "used")
  deferred                  -> must say who or what it waits for: ref starts with "Kamil:" (his decision) or
                               "data:" (results that do not exist yet)
  rejected                  -> a reason of >= 10 characters
  done "meta: ..."          -> work on the plan itself, no film rule (e.g. a revision of the list); always printed as INFO
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = Path(os.environ.get("RESEARCH_LEDGER", "/home/kamil-jan/Dane/creator-study/round2/ledger.jsonl"))
FORMS = {  # ledger "form" text -> the film form it changes
    "long": (r"^Long\b", r"^P1 — long", r"^long$"),
    "shorts": (r"^Shorts\b", r"^P2 — shorty", r"^shorts$"),
    "thumbs": (r"^Thumbs\b", r"^P1 — miniatury", r"^thumbs$"),
}


def checklist_ids() -> set[str]:
    return {i["id"] for i in json.loads((ROOT / "style" / "checklist.json").read_text(encoding="utf-8"))["items"]}


def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def of_form(item: dict, form: str) -> bool:
    return any(re.search(rx, item.get("form", "")) for rx in FORMS[form])


def problems(items: list[dict], form: str, ids: set[str]) -> list[str]:
    by_id = {i["id"]: i for i in items}

    def open_(i: dict, seen: tuple = ()) -> bool:
        if i["status"] == "todo": return True
        if i["status"] == "merged":
            c = by_id.get(i.get("ref", ""))
            return c is None or i["id"] in seen or open_(c, (*seen, i["id"]))
        return False

    bad: list[str] = []
    carried: dict[str, int] = {}  # open carrier id -> how many merged items of this form wait for it
    for i in items:
        if not of_form(i, form): continue
        ref, st, rule = str(i.get("ref", "")), i["status"], i.get("rule", "")[:70]
        if open_(i):
            if st == "merged" and ref in by_id: carried[ref] = carried.get(ref, 0) + 1; continue  # reported with its carrier
            bad.append(f"{i['id']} open ({st}{' -> ' + ref + ' (unknown id)' if st == 'merged' else ''}): {rule}")
        elif st == "done":
            got = re.findall(r"check:([\w.]+)", ref)
            if not got and re.match(r"^meta:\s*\S{3,}", ref): continue  # plan work, not a film rule (listed by meta_items)
            if not got: bad.append(f"{i['id']} done without a film_check item (ref \"check:<id>\"): {rule}")
            elif missing := [g for g in got if g not in ids]: bad.append(f"{i['id']} names unknown film_check items {missing}: {rule}")
        elif st == "deferred" and not re.match(r"^(Kamil|data):\s*\S{3,}", ref):
            bad.append(f"{i['id']} deferred without \"Kamil: ...\" or \"data: ...\": {rule}")
        elif st == "rejected" and len(ref.strip()) < 10:
            bad.append(f"{i['id']} rejected without a reason: {rule}")
    for cid, n in carried.items():
        c = by_id[cid]
        if not (of_form(c, form) and c["status"] == "todo"):  # carrier outside the form, or itself merged further
            bad.append(f"{cid} open ({c['status']}, carries {n} item(s) of this form): {c.get('rule', '')[:70]}")
        else:
            bad = [b + f" [+{n} merged]" if b.startswith(cid + " open") else b for b in bad]
    return bad


def meta_items(items: list[dict], form: str) -> list[str]:
    return [f"INFO {i['id']} done as plan work ({i['ref']})" for i in items
            if of_form(i, form) and i["status"] == "done" and str(i.get("ref", "")).startswith("meta:")]


def main(argv: list[str]) -> int:
    ledger = LEDGER
    if "--ledger" in argv: i = argv.index("--ledger"); ledger = Path(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1 or argv[0] not in FORMS:
        print("usage: research_gate.py <long|shorts|thumbs> [--ledger path]", file=sys.stderr); return 2
    if not ledger.exists(): print(f"research_gate: no ledger at {ledger}", file=sys.stderr); return 2
    items = load(ledger)
    bad = problems(items, argv[0], checklist_ids())
    n = sum(of_form(i, argv[0]) for i in items)
    for b in bad: print(b)
    for m in meta_items(items, argv[0]): print(m)
    print(f"research {argv[0]}: {n} items, {len(bad)} open or without proof" + ("" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
