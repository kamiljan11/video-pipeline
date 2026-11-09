#!/usr/bin/env python3
"""design_ledger: every work item a design names reaches the research ledger, so research_gate blocks a render while it is open.

    python3 design_ledger.py check   exit 1: a work item of docs/designs/*.md without its ledger row
    python3 design_ledger.py sync    append the missing rows as "todo" (then set done/deferred with ledger.py set)

Kamil 2026-11-09 "a da sie system enforcowac zeby nie pominal rzeczy": the visual upgrade plan of 2026-11-05 (drawn lines,
pieces pinned to ids, motion palette, sketch scenes) never became ledger rows, so no gate knew it was missing from the film.

A design with a `## Order of work` heading carries a line `<!-- ledger-forms: long, shorts -->` (forms of research_gate.FORMS
its items change; `none` = work outside films); the section holds numbered items `N. **title**`. Row id: `design:<file stem>:<N>:<form>`; status starts "todo".
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import research_gate

ROOT = Path(__file__).resolve().parent
DESIGNS = ROOT / "docs" / "designs"
FORMS_RX = re.compile(r"<!--\s*ledger-forms:\s*([\w ,]+?)\s*-->")
SECTION_RX = re.compile(r"^## Order of work\b.*$", re.MULTILINE)
ITEM_RX = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*", re.MULTILINE)


def items(doc: Path) -> list[dict]:
    """the ledger rows a design asks for (empty: the design has no ledger-forms line)"""
    text = doc.read_text(encoding="utf-8")
    m = FORMS_RX.search(text)
    if not m:
        if SECTION_RX.search(text):  # a plan of work no gate would know about: exactly how 2026-11-05 got lost
            raise ValueError(f"{doc.name}: '## Order of work' without '<!-- ledger-forms: long, shorts -->' (or 'none' for work outside films)")
        return []
    forms = [f.strip() for f in m.group(1).split(",") if f.strip() and f.strip() != "none"]
    if not forms: return []
    unknown = [f for f in forms if f not in research_gate.FORMS]
    if unknown: raise ValueError(f"{doc.name}: ledger-forms {unknown} not in research_gate.FORMS {sorted(research_gate.FORMS)}")
    sec_m = SECTION_RX.search(text)
    if not sec_m: raise ValueError(f"{doc.name}: ledger-forms but no '## Order of work' section")
    sec = text[sec_m.end():].split("\n## ", 1)[0]
    work = ITEM_RX.findall(sec)
    if not work: raise ValueError(f"{doc.name}: '## Order of work' has no numbered '**title**' items")
    return [{"id": f"design:{doc.stem}:{n}:{f}", "src": f"docs/designs/{doc.name}", "form": f, "rule": t.strip(),
             "target": f"docs/designs/{doc.name} item {n}", "status": "todo", "ref": ""} for n, t in work for f in forms]


def missing(designs: Path, ledger: list[dict]) -> list[dict]:
    have = {r["id"] for r in ledger}
    return [i for d in sorted(designs.glob("*.md")) for i in items(d) if i["id"] not in have]


def main(argv: list[str]) -> int:
    if argv[:1] not in (["check"], ["sync"]): print(__doc__, file=sys.stderr); return 2
    path = research_gate.LEDGER
    ledger = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    try: gone = missing(DESIGNS, ledger)
    except ValueError as e: print(f"FAIL {e}"); return 1
    if argv[0] == "sync" and gone:
        with path.open("a", encoding="utf-8") as f:
            for i in gone: f.write(json.dumps(i, ensure_ascii=False) + "\n")
        print(f"design_ledger: {len(gone)} row(s) added as todo to {path}")
        return 0
    for i in gone: print(f"FAIL {i['id']}: {i['rule']} (no ledger row; python3 design_ledger.py sync)")
    print(f"design_ledger: {len(gone)} design item(s) without a ledger row {'OK' if not gone else 'FAIL'}")
    return 1 if gone else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
