"""kind.py: which rule set a film follows, one answer for every step (build_edl, film_check; face_track gets it from the EDL).

is_talk(plan, work): the plan's own "podcast" key wins (true / an object = two people, false = one person); without it the
answer content_kind.py measured on the recording (<work>/content_kind.json, "talk" or "solo"). No key and no measurement
= one person, the rules every film had before 2026-11-22 (said in the log line, so a missing measurement is seen).
"""
import json
import sys
from pathlib import Path


def is_talk(plan: dict, work: Path) -> bool:
    if "podcast" in plan: return plan["podcast"] is not False
    f = Path(work) / "content_kind.json"
    if not f.is_file():
        print("kind: solo (no content_kind.json: run content_kind.py <work> <plan> to measure)", file=sys.stderr)
        return False
    return json.loads(f.read_text()).get("kind") == "talk"
