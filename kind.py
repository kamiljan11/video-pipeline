"""kind.py: which rule set a film follows, one answer for every step (build_edl, film_check; face_track gets it from the EDL).

is_talk(plan, work): the plan's own "podcast" key wins (true / an object = two people, false or null = one person);
without it the answer content_kind.py measured on the plan's recording (<work>/content_kind.json "sources"[src], "talk" or "solo"),
checked against that recording (key()). No key and no measurement = one person, the
rules every film had before 2026-11-22 (said once on stderr, so a missing measurement is seen). ADR-0032.
"""
import functools
import json
import sys
from pathlib import Path

VERSION = 2  # of the measurement: a new version measures again


def from_plan(plan: dict) -> "bool | None":
    """the plan's "podcast" key -> True (two people) / False (one) / None (no key: measure)"""
    if "podcast" not in plan: return None
    v = plan["podcast"]
    if v is True or isinstance(v, dict): return True
    if v is False or v is None: return False
    raise SystemExit(f"podcast: the plan key must be true, false or an object, got {v!r}")


def key(work: Path, plan: dict) -> dict:
    """what the measurement depends on: the recording only (frames spread over all of it, not over a plan's keeps, so
    the long and its shorts in one folder share one answer)"""
    st = (Path(work) / plan["src"]).stat()
    return {"src": plan["src"], "size": st.st_size, "mtime": int(st.st_mtime), "version": VERSION}


@functools.cache
def _note_once(msg: str) -> None:
    print(msg, file=sys.stderr)


def measured(work: Path, plan: dict) -> "dict | None":
    """the entry content_kind.py wrote for the plan's recording, None when not measured; stops on a broken or stale file"""
    f = Path(work) / "content_kind.json"
    if not plan.get("src") or not f.is_file(): return None
    try: m = json.loads(f.read_text())
    except json.JSONDecodeError as e: raise SystemExit(f"kind: {f} is not valid JSON ({e}): run content_kind.py again") from e
    e = (m.get("sources") or {}).get(plan["src"])
    if e is None: return None
    if e.get("key") != key(work, plan):
        raise SystemExit(f"kind: {f} was measured on another version of {plan['src']}: run content_kind.py <work> <plan> again")
    return e


def is_talk(plan: dict, work: Path) -> bool:
    said = from_plan(plan)
    if said is not None: return said
    e = measured(work, plan)
    if e is None:
        _note_once(f"kind: solo ({plan.get('src')} not measured in content_kind.json: run content_kind.py <work> <plan>)")
        return False
    return e.get("kind") == "talk"
