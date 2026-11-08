#!/usr/bin/env python3
"""hook_check.py: the 6 hook killers on a Polish short hook (Skool CCC C1, C2, So2, So9, Z2, Z3, B4; P1 task 13).

A hook FAILS on any of:
  1. greeting      starts with a hello ("Cześć", "Hej", "Dzień dobry"),
  2. title         a listicle opener with nothing at stake ("5 porad", "3 sposoby"): a title, not a reason to stay
                   ("3 błędy kosztowały mnie 40 tys." has a stake and passes; "bez", "tylko" or the list noun itself is no stake),
  3. filler        throat clearing before the first interesting word ("Dzisiaj", "W tym filmie", "Chciałbym"),
  4. vague         a vague promise ("sekret", "coś", "patent") with no number, acronym, quote or name to anchor it,
                   or hype adjectives piled up (2 or more),
  5. no stake      nothing to gain or lose: no number and no stake word (style/hook_lint.json "stake"),
  6. no text       the hook is not on screen from the first frame (when the caller knows: plan hook_text),
and when it is longer than max_words. Word lists are data: style/hook_lint.json.

film_check.py runs it as short.hook_lint (the plan's hook_text) and out.hooks (clips.json: >= MIN_VARIANTS hooks per short
that is made, each clean, "hook" one of them, "hook_from" a row of style/hook_bank.json). Alone:
  python3 hook_check.py "<hook>" ["<hook>" ...]
"""
from __future__ import annotations

import json
import re
import sys
from collections.abc import Set as AbstractSet
from pathlib import Path

STYLE = Path(__file__).resolve().parent / "style"
MIN_VARIANTS = 3
WORD = re.compile(r"[\wąćęłńóśźż%]+", re.IGNORECASE)


def lists(path: Path = STYLE / "hook_lint.json") -> dict:
    return json.loads(path.read_text())


def _match(e: str, w: str) -> bool:
    """"stem*" = w starts with stem, "word" = w is that word"""
    return w.startswith(e[:-1]) if e.endswith("*") else w == e


def _has(words: list[str], low: str, entries: list[str]) -> list[str]:
    """entries found: a phrase (with a space) anywhere, else a word or "stem*" among the words"""
    return [e for e in entries if (re.search(rf"(?<!\w){re.escape(e)}(?!\w)", low) if " " in e else any(_match(e, w) for w in words))]


def _starts(low: str, entries: list[str]) -> list[str]:
    """entries the hook starts with, as whole words ("elo" is not "Elon", "zaraz" is not "Zarazki")"""
    return [e for e in entries if re.match(rf"{re.escape(e)}(?!\w)", low)]


def _saves_list(words: list[str], low: str, wl: dict) -> bool:
    """a stake word that is neither weak ("5 porad bez nudy") nor the list noun itself ("3 błędy w kodzie"): "3 błędy
    kosztowały mnie 40 tys." passes"""
    return any(e not in wl.get("stake_weak", []) and not _match(e, words[1]) for e in _has(words, low, wl["stake"]))


def anchored(hook: str) -> bool:
    """a number, an acronym (AI, CRM), a quoted word or a capitalised name after the first word"""
    toks = WORD.findall(hook)
    return (any(c.isdigit() for c in hook) or any(len(t) >= 2 and t.isupper() for t in toks)
            or bool(re.search(r"[„\"«].+?[”\"»]", hook)) or any(t[:1].isupper() for t in toks[1:]))


def problems(hook: str, on_screen: bool | None = None, wl: dict | None = None) -> list[str]:
    wl = wl or lists()
    low = " ".join(hook.lower().split())
    words = WORD.findall(low)
    bad = []
    no_text = ["no text: the hook is not on screen from the first frame (plan hook_text)"] if on_screen is False else []
    if not words: return ["empty hook", *no_text]
    if len(words) > wl["max_words"]: bad.append(f"{len(words)} words (max {wl['max_words']})")
    if g := _starts(low, wl["greeting"]): bad.append(f"greeting: starts with {g[0]!r}")
    # a list opener: "5 porad", also "#1 sposób", "nr 1", "numer 1" (round 2 S1: those passed while "1 sposób" was flagged)
    lw = words[1:] if re.match(r"(nr|numer)\b", low) else words
    if re.match(r"(#\s*|nr\.?\s*|numer\s+)?\d+\s", low) and len(lw) > 1 and _has(lw[1:2], lw[1], wl["listicle"]) and not _saves_list(lw, low, wl):
        bad.append(f"title, not a hook: {' '.join(lw[:2])!r} is a list opener")
    if f := _starts(low, wl["filler_start"]): bad.append(f"filler: starts with {f[0]!r}, start at the first interesting word")
    if (v := _has(words, low, wl["vague"])) and not anchored(hook): bad.append(f"vague: {v[0]!r} with no number, acronym, quote or name")
    if len(h := _has(words, low, wl["hype"])) >= 2: bad.append(f"vague: hype adjectives {h}")
    if not any(c.isdigit() for c in hook) and not _has(words, low, wl["stake"]): bad.append("no stake: nothing to gain or lose (a number or a stake word)")
    return bad + no_text


def bank(path: Path = STYLE / "hook_bank.json") -> dict[str, dict]:
    return {r["id"]: r for r in json.loads(path.read_text())["hooks"]}


def clip_problems(item: dict, ids: AbstractSet[str], wl: dict | None = None) -> list[str]:
    """one clips.json item that is made: its hook variants, the chosen one, where it came from"""
    cid, hooks = item.get("id", "?"), item.get("hooks") or []
    bad = [] if len(hooks) >= MIN_VARIANTS else [f"{cid}: {len(hooks)} hook variants (want >= {MIN_VARIANTS} in \"hooks\")"]
    for h in hooks: bad += [f"{cid}: {h!r}: {p}" for p in problems(str(h), wl=wl)]
    if hooks and item.get("hook") not in hooks: bad.append(f"{cid}: \"hook\" is not one of its \"hooks\"")
    if item.get("hook_from") not in ids: bad.append(f"{cid}: \"hook_from\" {item.get('hook_from')!r} is not a row of style/hook_bank.json")
    return bad


def main(argv: list[str]) -> int:
    if not argv: print(__doc__, file=sys.stderr); return 2
    rc = 0
    for h in argv:
        bad = problems(h)
        print(f"{'FAIL' if bad else 'OK  '} {h}" + "".join(f"\n     {b}" for b in bad))
        rc |= bool(bad)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
