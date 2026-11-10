#!/usr/bin/env python3
"""accept: the long is watched and accepted by Kamil before anything else is made from the recording.

    python3 accept.py write <work> <long.mp4> "Kamil YYYY-MM-DD: <his sentence>"    after he said the long is good
    python3 accept.py check <work>            exit 1 unless <work>/ACCEPTED_long.json names a film that is still that file

Kamil 2026-11-10: "najpierw powinnismy dosjc do momentu ze wychodzi koncowy render juz zakceptowany gotowy do wrzucenia
long a dopiero potem reszta rusza nie automatycznie tylko za napisaniem jedz dalej". run_v4.sh refuses every film other
than the long without it (2026-11-04 v5: 18 shorts rendered and re-rendered next to a long that still changed, NOTES_LOG
row 34). The record holds the film's sha256: a long rendered again after the acceptance needs a new one.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

import manifest
import waivers

NAME = "ACCEPTED_long.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()


def write(work: Path, film: Path, said: str) -> str:
    """"" and the record on disk, or why not"""
    if not waivers.SAID.match(said): return f"whose words and when: 'Kamil YYYY-MM-DD: his sentence', got {said!r}"
    if not film.is_file(): return f"no film {film}"
    rec = {"film": str(film.resolve()), "sha256": sha256(film), "commit": manifest.head(), "said": said,
           "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    (work / NAME).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ""


def check(work: Path) -> str:
    """"" when the accepted long is still the file Kamil watched; else what is missing"""
    p = work / NAME
    if not p.exists(): return f"the long is not accepted yet (no {NAME} in {work}): Kamil watches it first, then accept.py write"
    try: rec = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e: return f"{NAME} is not JSON ({e})"
    film = Path(rec.get("film", ""))
    if not film.is_file(): return f"the accepted long is gone: {film}"
    if sha256(film) != rec.get("sha256"): return f"{film.name} changed after Kamil accepted it: he watches the new one, then accept.py write"
    return ""


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[0] == "write": why = write(Path(argv[1]), Path(argv[2]), argv[3])
    elif len(argv) == 2 and argv[0] == "check": why = check(Path(argv[1]))
    else: print(__doc__); return 2
    print(f"accept {argv[0]}: {'FAIL ' + why if why else 'OK'}")
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
