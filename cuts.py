"""cuts: a long keeps everything Kamil said except his mistakes, each cut named, and air between sentences.

Kamil 2026-11-15, on the 2026-11-04 long cut from 26 to 18 minutes: "my nagrywamy i tak filmy z telepromterem wiec nie
trzeba az tak usuwac tresci jak bys wycia powtorzenia faile jak cos mowie ale tez nie ostro tak zeby zostawic przestrzen
na oddech ... nie plynie video juz tak fajnie tylko jest za ostro pociachane". The editor's card said "cut bridge sentences
without content" and the 2026-11-09 edit took out 23 spans of digressions and bridges with the retakes.

A long's plan names every run of words left out of its keeps in "cuts": {"w<from>-<to>": "<kind>: why"}, kind one of KINDS
(a run inside a named range is covered; "Kamil YYYY-MM-DD: his words" for a cut he asked for). The pause between sentences stays up to BREATH s (plan "pads" mingap at least that).
Shorts are cut for length and are not held to this.

Every film (long and short) plays the recording in its order: Kamil 2026-11-15 "nie chcemy reorganizowac kolejnosci
klipow w nagraniu ... po kolei jest narracja nadana bo to jest z teleproptera" (the 2026-11-04 long had w187-232 moved
before w69-166). order() names a keep that starts before the one in front of it ends.
"""
from __future__ import annotations

import re
from itertools import pairwise

KINDS = ("retake", "false start", "slip", "mic", "off take", "Kamil")  # off take: talk before/after the take  # what may go: his mistakes, or what he named himself
BREATH = 0.6  # s: a pause up to this stays whole (pads mingap); build_edl LONG_PADS keeps 0.5 s of a longer one
LONG_PADS = {"pre": 0.18, "post": 0.28, "keep_l": 0.28, "keep_r": 0.22, "mingap": 0.7}
KEY = re.compile(r"^w(\d+)(?:-(\d+))?$")  # "w<from>-<to>" or one word "w<n>"


def dropped(keeps: list, n_words: int) -> list[tuple[int, int]]:
    """runs [from, to] of word indexes of the whole recording that no keep holds: talk before the first keep and after
    the last counts too (pg-review 2026-11-15: a long could lose its opening sentence with nothing named)"""
    kept = {i for k in keeps for i in range(int(k[0]), int(k[1]) + 1)}
    if not kept: return []
    runs: list[list[int]] = []
    for i in range(n_words):
        if i in kept: continue
        if runs and runs[-1][1] == i - 1: runs[-1][1] = i
        else: runs.append([i, i])
    return [(a, b) for a, b in runs]


def order(keeps: list) -> list[str]:
    """keeps that go back in the recording: the teleprompter's narrative runs forward"""
    return [f"keep w{int(b[0])}-{int(b[1])} comes after w{int(a[0])}-{int(a[1])}: a film plays the recording in its order "
            f"(teleprompter narrative), put the keeps in word order" for a, b in pairwise(keeps) if int(b[0]) <= int(a[1])]


def problems(plan: dict, n_words: int) -> list[str]:
    """what a long's plan cuts without a named reason, a named cut with no usable reason, a pause cut too short"""
    named, bad = [], []
    for k, v in (plan.get("cuts") or {}).items():
        m = KEY.match(k)
        if not m: bad.append(f"cuts {k!r}: name a run as \"w<from>-<to>\" or \"w<n>\""); continue
        kind = v.split(":", 1)[0].strip() if isinstance(v, str) and ":" in v else ""
        if not (any(kind == k or (k == "Kamil" and kind.startswith("Kamil ")) for k in KINDS) and len(v.split(":", 1)[1].strip()) >= 5):
            bad.append(f"cuts {k!r}: \"<kind>: why\" with kind one of {', '.join(KINDS)}, got {v!r}"); continue
        named.append((int(m.group(1)), int(m.group(2) or m.group(1))))
    covered = {i for x, y in named for i in range(x, y + 1)}  # neighbouring named ranges cover one run together
    for a, b in dropped(plan.get("keeps") or [], n_words):
        if not all(i in covered for i in range(a, b + 1)):
            bad.append(f"w{a}-{b} is cut and plan \"cuts\" does not name it: a long keeps what was said (put it back) or names "
                       f"a mistake ({', '.join(KINDS)})")
    gap = (plan.get("pads") or {}).get("mingap", LONG_PADS["mingap"] if plan.get("pads") is None else 0.45)
    if gap < BREATH: bad.append(f"pads.mingap {gap:g}: a long keeps pauses up to at least {BREATH:g} s whole (air between sentences)")
    return bad
