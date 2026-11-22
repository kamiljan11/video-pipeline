#!/usr/bin/env python3
"""waivers: a gate switched off in run_v4.sh renders nothing unless the plan carries Kamil's own words for it.

    python3 waivers.py <plan.json> <gate> [<gate> ...]     exit 1: a gate is off and the plan has no waiver for it

Kamil 2026-11-10: "czyli to że ty wybiorczosc wprowadzasz w trakcie pracy bedzie rozwiazane? i nie beda pomijane bramki".
The 2026-11-04 v5 render had LIP_CHECK=off on 5 shorts with only a log line. Plan: "waivers": {"lip_check": "Kamil
2026-11-10: <his sentence>"}. No code writes this key (tests/test_waivers.py); it is typed into the plan after Kamil said it.
"""
import json
import re
import sys
from pathlib import Path

GATES = ("lip_check", "words_check", "film_check", "scene_check", "research_gate")
SAID = re.compile(r"^Kamil \d{4}-\d{2}-\d{2}: \S.{9,}$")  # who, when, what he said (at least a few words)


def missing(plan: dict, off: list[str]) -> list[str]:
    """one line per gate that is off without a usable waiver"""
    w = plan.get("waivers", {})
    if not isinstance(w, dict): return [f"waivers: an object {{gate: 'Kamil YYYY-MM-DD: his words'}}, got {w!r}"]
    bad = [f"waivers.{g}: no such gate (gates: {', '.join(GATES)})" for g in w if g not in GATES]
    for g in off:
        if g not in GATES: bad.append(f"{g}: no such gate (gates: {', '.join(GATES)})")
        elif g not in w: bad.append(f"{g} is off and the plan has no waivers.{g}")
        elif not isinstance(w[g], str) or not SAID.match(w[g]): bad.append(f"waivers.{g}: 'Kamil YYYY-MM-DD: his words', got {w[g]!r}")
    return bad


def main(argv: list[str]) -> int:
    if len(argv) < 2: print(__doc__); return 2
    p = Path(argv[0])
    try: plan = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e: print(f"waivers: FAIL cannot read {p}: {e}"); return 1
    bad = missing(plan, argv[1:])
    for b in bad: print(f"waivers: FAIL {p.name}: {b}")
    if not bad: print(f"waivers: {p.name} off with Kamil's waiver: {', '.join(argv[1:])}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
