"""retakes: the same n words said twice close together = a retake the cut kept (Kamil 2026-11-09 "jak dwa razy cos mowie,
bo sie pomylilem, to wytnij i zostaw lepsza wersje"). Shared by film_check long/short.retakes (the plan's words) and
retake_check.py (what whisper hears in the cut itself, 2026-11-14: the source transcript had lost one of the two takes).
A repeat on purpose is named in plan "retakes_ok": {"<the n+ words>": "why (>= 10 chars)"}, one phrase at a time.
"""
from __future__ import annotations

import re

SKIP_MIN = 10  # a reason shorter than this says nothing (the same bar as film_check "skip")


def norm_word(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())


def runs(words: list[tuple[float, str]], n: int = 4, window: float = 20.0) -> list[tuple[float, float, list[str]]]:
    """(time of the first take, time of the repeat, the repeated words) for each run of n+ words said again within
    `window` s; one retake repeats several overlapping n-word groups, they make one run. words = [(time, word)] in order"""
    fw = [(t, w) for t, w in ((t, norm_word(x)) for t, x in words) if w]
    seen: dict[str, float] = {}
    out: list[list] = []
    prev = False
    for i in range(len(fw) - n + 1):
        t, key = fw[i][0], " ".join(w for _, w in fw[i:i + n])
        again = key in seen and t - seen[key] <= window
        if again and prev: out[-1][2].append(fw[i + n - 1][1])
        elif again: out.append([seen[key], t, key.split()])
        prev = again
        seen[key] = t
    return [(a, b, w) for a, b, w in out]


def allowed(plan: dict, n: int = 4) -> tuple[list[list[str]], list[str]]:
    """(named phrases as word lists, what is wrong with the plan's retakes_ok): a named phrase waives nothing unless it
    has n+ words and a reason"""
    ok: list[list[str]] = []
    wrong: list[str] = []
    for k, v in (plan.get("retakes_ok") or {}).items():
        words = [x for x in map(norm_word, str(k).split()) if x]
        if len(words) < n: wrong.append(f"retakes_ok {k!r}: name the {n}+ words said twice")
        elif not (isinstance(v, str) and len(v.strip()) >= SKIP_MIN): wrong.append(f"retakes_ok {k!r}: the reason must say why (>= {SKIP_MIN} characters)")
        else: ok.append(words)
    return ok, wrong


def named(run: list[str], ok: list[list[str]]) -> bool:
    """the key covers the WHOLE repeated run (whole words, in a row): 4 named words do not waive a 20-word retake"""
    return any(k[i:i + len(run)] == run for k in ok for i in range(len(k) - len(run) + 1))


def problems(words: list[tuple[float, str]], plan: dict, n: int = 4, window: float = 20.0) -> tuple[list[str], list[str]]:
    """(retakes not named in the plan as "'words' at A s and B s", wrong retakes_ok entries)"""
    ok, wrong = allowed(plan, n)
    return [f"'{' '.join(w)}' at {a:.0f} s and {b:.0f} s" for a, b, w in runs(words, n, window) if not named(w, ok)], wrong
