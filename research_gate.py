#!/usr/bin/env python3
"""research_gate: no film render while research meant for that form is still open or "done" without proof in the film.

    python3 research_gate.py <long|shorts|thumbs> [--ledger path]   exit 1 + the open items
    python3 research_gate.py <form> --report fc.json                after film_check --json: every done item's check is OK
                                                                    in this film (WARN or FAIL = exit 1; SKIP = INFO + reason)

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
--report (Kamil 2026-11-08 "czy realnie wprowadziles nowe logiki??? sprawdzales to"): most research checks are level
"warn" in film_check, so a film could miss them and still pass. Here a done item whose check is in the report must be OK
there, with a row for every film of its format in the report (a missing row = not measured = not met); an id of another
format (e.g. out.* for a film) is checked in that format's report. An empty or malformed report = exit 2.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = Path(os.environ.get("RESEARCH_LEDGER", str(Path.home() / "Dane" / "creator-study" / "round2" / "ledger.jsonl")))
LEDGER_SET = "RESEARCH_LEDGER" in os.environ  # a ledger someone named must exist; the default one may be absent
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


REPORT_KEYS = ("film", "id", "status", "detail")


def check_report(report: object) -> list[dict]:
    """a film_check --json report: a non-empty list of {film, id, status, detail} rows; ValueError otherwise"""
    if not isinstance(report, list) or not report: raise ValueError("empty report: film_check measured nothing")
    bad = [r for r in report if not isinstance(r, dict) or any(k not in r for k in REPORT_KEYS)]
    if bad: raise ValueError(f"{len(bad)} row(s) without {'/'.join(REPORT_KEYS)}, e.g. {str(bad[0])[:120]}")
    return report


def report_problems(items: list[dict], form: str, report: object) -> tuple[list[str], list[str]]:
    """(problems, info) of the done items of a form against a film_check --json report. A check of a format the report
    holds (its id prefix, e.g. "long.") must have a row for every film of that format in the report: a missing row is
    not met (a renamed check or a check film_check never ran). A check of another format (out.* in a film report) is
    measured in that format's report."""
    rows: dict[tuple[str, str], list[dict]] = {}
    films: dict[str, set[str]] = {}  # id prefix -> the films the report measured it in
    for r in check_report(report):
        rows.setdefault((r["id"], r["film"]), []).append(r)
        films.setdefault(r["id"].split(".")[0], set()).add(r["film"])
    bad, info = [], []
    for i in items:
        if not (of_form(i, form) and i["status"] == "done"): continue
        for cid in re.findall(r"check:([\w.]+)", str(i.get("ref", ""))):
            for film in sorted(films.get(cid.split(".")[0], ())):
                got = rows.get((cid, film))
                if not got: bad.append(f"{i['id']} done, but {cid} has no row for {film} in the report (not measured)")
                for r in got or []:
                    if r["status"] == "SKIP": info.append(f"INFO {i['id']} {cid} skipped in {film}: {r['detail']}")
                    # a whole-film check in a fragment test folder (film_check FRAGMENT_TAG, fragment.py): not measurable there
                    elif r.get("fragment") is True and r["status"] == "WARN": info.append(f"INFO {i['id']} {cid} whole-film, fragment test {film}: {str(r['detail'])[:120]}")
                    elif r["status"] != "OK": bad.append(f"{i['id']} done, but {cid} is {r['status']} in {film}: {str(r['detail'])[:160]}")
    return bad, info


def meta_items(items: list[dict], form: str) -> list[str]:
    return [f"INFO {i['id']} done as plan work ({i['ref']})" for i in items
            if of_form(i, form) and i["status"] == "done" and str(i.get("ref", "")).startswith("meta:")]


def ledger_items(path: Path, named: bool) -> list[dict] | None:
    """The ledger's items. The default ledger absent (a computer without the author's research, README Quick start) = no
    items, said on stderr; a ledger named by --ledger or RESEARCH_LEDGER absent = None: the caller stops (exit 2)."""
    if path.exists(): return load(path)
    if named: print(f"research_gate: no ledger at {path}", file=sys.stderr); return None
    print(f"research_gate: no research ledger on this computer ({path}; RESEARCH_LEDGER names one): 0 items", file=sys.stderr)
    return []


def main(argv: list[str]) -> int:
    ledger, named = LEDGER, LEDGER_SET or "--ledger" in argv
    if "--ledger" in argv: i = argv.index("--ledger"); ledger = Path(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    report = None
    if "--report" in argv: i = argv.index("--report"); report = Path(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1 or argv[0] not in FORMS:
        print("usage: research_gate.py <long|shorts|thumbs> [--ledger path] [--report film_check.json]", file=sys.stderr); return 2
    items = ledger_items(ledger, named)
    if items is None: return 2
    if report is not None:
        try: bad, info = report_problems(items, argv[0], json.loads(report.read_text(encoding="utf-8")))
        except (OSError, ValueError) as e: print(f"research_gate: bad report {report}: {e}", file=sys.stderr); return 2
        for b in bad: print(b)
        for x in info: print(x)
        print(f"research {argv[0]} in {report.name}: {len(bad)} done item(s) not met in the film" + ("" if bad else " OK"))
        return 1 if bad else 0
    bad = problems(items, argv[0], checklist_ids())
    n = sum(of_form(i, argv[0]) for i in items)
    for b in bad: print(b)
    for m in meta_items(items, argv[0]): print(m)
    print(f"research {argv[0]}: {n} items, {len(bad)} open or without proof" + ("" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
