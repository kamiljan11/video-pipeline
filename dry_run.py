#!/usr/bin/env python3
"""dry_run: the full render starts only after a small one passed every check on the same code and the same film.

    python3 dry_run.py pass <work> <film>    after run_v4.sh DRY=1 passed every check: writes <work>/dry_<film>.json
    python3 dry_run.py need <work> <film>    before the full render: exit 1 unless that file is from this code and this film

Kamil 2026-11-10: the 2026-11-04 long took 5 full renders (30-50 min each) because the checks ran after the render and the
code changed between runs (NOTES_LOG rows 31, 34, 37, 38). The small render (assemble.py --dry: 640 px picture, the full
sound) runs the same checks in a fraction of the time. The record names the commit and the sha256 of edl_<film>.json and
gfx_specs.json: a code change (manifest.code_changed, the film's code) or another cut or card set asks for a new dry run.
This is also the code freeze of a film: nothing but the film's data changes between the dry run and the render.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

import manifest

INPUTS = ("edl_{film}.json", "gfx_specs.json")  # what the render is made of; gfx_specs.json may be absent (a film with no cards)


def inputs(work: Path, film: str) -> dict:
    out = {}
    for name in (n.format(film=film) for n in INPUTS):
        p = work / name
        if p.exists(): out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def record(work: Path, film: str) -> Path:
    return work / f"dry_{film}.json"


def passed(work: Path, film: str) -> str:
    """writes the record and returns ""; a reason instead when the code is not committed (the record could not be traced to a commit)"""
    if manifest.dirty(): return "uncommitted code: commit it, then run the dry run again"
    rec = {"commit": manifest.head(), "inputs": inputs(work, film), "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    if f"edl_{film}.json" not in rec["inputs"]: return f"no edl_{film}.json in {work}"
    record(work, film).write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return ""


def needed(work: Path, film: str) -> str:
    """"" when a dry run of this film passed on this code and these inputs; else what to do"""
    p = record(work, film)
    if not p.exists(): return f"no dry run of {film}: run_v4.sh with DRY=1 first"
    try: rec = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e: return f"{p.name} is not JSON ({e}): run the dry run again"
    if manifest.dirty(): return "uncommitted code: commit it, then run the dry run again"
    why = manifest.code_changed(rec.get("commit", ""), film=True)
    if why: return f"{why}: the code changed after the dry run, run it again"
    now = inputs(work, film)
    diff = sorted(n for n in set(now) | set(rec.get("inputs", {})) if now.get(n) != rec.get("inputs", {}).get(n))
    if diff: return f"{', '.join(diff)} changed after the dry run: run it again"
    return ""


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in ("pass", "need"): print(__doc__); return 2
    work, film = Path(argv[1]), argv[2]
    why = passed(work, film) if argv[0] == "pass" else needed(work, film)
    print(f"dry_run {argv[0]} {film}: {'FAIL ' + why if why else 'OK'}")
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
