#!/usr/bin/env python3
"""out_gate: the last gate before Kamil watches an out folder: every material made by the current code and every done
research item met in it.

    python3 out_gate.py <work> <out>     exit 0 = film_check --out passes (FAIL items) and research_gate --report is OK
                                         for long, shorts and thumbs on that report; writes <work>/fc_out.json

Kamil 2026-11-08: "inne materialy tez nowe logiki robiles czy wszystko po starych poszlo??" and "czy realnie wprowadziles
nowe logiki???". run_v4.sh holds each film to its research (research_used); the materials (descriptions, thumbnails,
posts, blog) are made after it, so this runs once they are all in the out folder (out.manifest is one of the items).
"""
import json
import subprocess
import sys
from pathlib import Path

import research_gate

ROOT = Path(__file__).resolve().parent
TIMEOUT_S = 3600


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    work, out = Path(argv[0]), Path(argv[1])
    try: r = subprocess.run([sys.executable, str(ROOT / "film_check.py"), str(work), "--out", str(out), "--json"],
                            capture_output=True, text=True, check=False, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired: print(f"out_gate: film_check --out ran over {TIMEOUT_S} s", file=sys.stderr); return 2
    try: report = research_gate.check_report(json.loads(r.stdout))
    except ValueError as e:  # JSONDecodeError is a ValueError
        print(f"out_gate: film_check --out gave no report (exit {r.returncode}): {e}; {r.stderr.strip()[-400:]}", file=sys.stderr); return 2
    (work / "fc_out.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fails = [f"{x['id']}: {str(x['detail'])[:160]}" for x in report if x["status"] == "FAIL"]
    items = research_gate.ledger_items(research_gate.LEDGER, research_gate.LEDGER_SET)
    if items is None: return 2
    missed, info = [], []
    for form in research_gate.FORMS:
        b, i = research_gate.report_problems(items, form, report); missed += b; info += i
    for x in fails: print(f"FAIL {x}")
    for x in missed: print(x)
    for x in info: print(x)
    print(f"out_gate: {len(fails)} film_check FAIL, {len(missed)} research item(s) not met" + ("" if fails or missed else " OK"))
    return 1 if fails or missed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
