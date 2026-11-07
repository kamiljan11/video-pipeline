#!/usr/bin/env python3
"""title_check.py: the long's A/B/C titles in out/youtube/long.md (Skool CCC So3, So4, C5, C10; P1 task 14).

Every title row:
  - at most MAX_LEN characters (the real length, not the "znaki" column: the search page cuts the rest),
  - a word of `## Fraza kluczowa` in its first FIRST_WORDS words (search reads the start),
  - a filled "źródło" column: the niche title it started from (a title that already works, then our own angle),
  - its promise said in the long's first OPENING seconds: at least PROMISE_MIN of its content words (or all, when it has
    fewer) are heard there, else the viewer clicked for something the opening does not give and leaves.
Words match on a shared start of STEM letters (Polish endings: "wstydziłem" / "wstydziłam", "działa" / "działać").

Soft WARN lines (style/title_lint.json, creator-study PLAN 2.7, 2.9; never in the exit code, never in problems()):
  - shorter than min_len characters,
  - a long title with no promise marker (digit + result, delivery word, audience, pain),
  - "Mój/Moje/Moja" without a result (a digit with a result word or %),
  - a number next to a news word (news titles lose to evergreen ones),
  - a series prefix ("Tutorial:") or a brand tag after "|".

film_check.py runs it as out.titles (Out.out_titles); alone:
  python3 title_check.py <long.md> [<plan_long.json>]   (with the plan the opening is read from its words and EDL)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MAX_LEN = 60
FIRST_WORDS = 3
OPENING = 30.0     # s of the finished long
PROMISE_MIN = 2
STEM = 5
STOP = {"mój", "moja", "moje", "mnie", "nie", "nic", "się", "jak", "czy", "ale", "albo", "oraz", "dla", "bez", "pod", "nad",
        "przez", "jest", "są", "to", "ten", "ta", "tak", "już", "dziś", "teraz", "mam", "masz", "mu", "go", "jej", "ich",
        "na", "do", "od", "po", "za", "ze", "że", "co", "kto", "gdy", "który", "która", "które", "a", "i", "w", "z", "o", "u"}


LINT_FILE = Path(__file__).resolve().parent / "style" / "title_lint.json"


def words(text: str) -> list[str]:
    return re.findall(r"[\wąćęłńóśźż%]+", text.lower())


def content(text: str) -> list[str]:
    """the words that carry the promise: no stop words, a digit or 3+ letters (AI counts, "na" does not)"""
    return [w for w in words(text) if w not in STOP and (len(w) >= 3 or any(c.isdigit() for c in w) or w == "ai")]


def same(a: str, b: str) -> bool:
    n = min(STEM, len(a), len(b))
    return a == b if n < 3 else a[:n] == b[:n]


def section(md: str, head: str) -> str:
    m = re.search(rf"^## {re.escape(head)}\s*$(.*?)(?=^## |\Z)", md, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def titles(md: str) -> list[dict]:
    """rows of the `## Tytuły` table by its header (wariant, tytuł, źródło); a table without a header = the 2nd cell is the title"""
    rows = [[c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))] for ln in section(md, "Tytuły").splitlines() if ln.strip().startswith("|")]
    rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
    head = [c.lower() for c in rows[0]] if rows and rows[0][0].lower() == "wariant" else []
    col = lambda name, d: head.index(name) if name in head else d
    ti, si = col("tytuł", 1), col("źródło", -1)
    out = []
    for r in rows[1:] if head else rows:
        if not re.fullmatch(r"[A-Z]", r[0]): continue
        out.append({"variant": r[0], "title": r[ti] if ti < len(r) else "",
                    "source": r[si] if 0 <= si < len(r) else None})
    return out


def phrase(md: str) -> str:
    return " ".join(ln.strip() for ln in section(md, "Fraza kluczowa").splitlines() if ln.strip())


def problems(md: str, opening: list[str] | None) -> list[str]:
    """None = no words of the long: the promise check cannot run and says so (it never passes quietly)"""
    rows, key = titles(md), content(phrase(md))
    bad = [] if key else ["no `## Fraza kluczowa` (one line: what the viewer types into search)"]
    heard = [w for t in opening or [] for w in words(t)]
    for r in rows:
        v, t = r["variant"], r["title"]
        if len(t) > MAX_LEN: bad.append(f"{v}: {len(t)} characters (max {MAX_LEN})")
        if key and not any(same(w, k) for w in words(t)[:FIRST_WORDS] for k in key):
            bad.append(f"{v}: no word of the phrase {phrase(md)!r} in its first {FIRST_WORDS} words")
        if not r["source"]: bad.append(f"{v}: empty źródło (the niche title it started from)")
        if opening is None: continue
        promise = list(dict.fromkeys(content(t)))
        got = [w for w in promise if any(same(w, h) for h in heard)]
        if len(got) < min(PROMISE_MIN, len(promise)):
            bad.append(f"{v}: the first {OPENING:.0f} s say {got or 'none'} of {promise}")
    if opening is None: bad.append("the opening cannot be checked: no words and EDL of the long")
    return bad


def lint_lists(path: Path = LINT_FILE) -> dict:
    return json.loads(path.read_text())


def hit(text: str, entries: list[str]) -> bool:
    """an entry matches as a whole word, a "stem*" prefix of a word, or (with a space or a symbol) a phrase anywhere"""
    low, ws = text.lower(), words(text)
    for e in entries:
        if e.endswith("*"):
            if any(w.startswith(e[:-1]) for w in ws): return True
        elif " " in e or not e.replace("%", "").isalnum():
            if re.search(rf"(?<!\w){re.escape(e)}(?!\w)" if e[0].isalnum() and e[-1].isalnum() else re.escape(e), low): return True
        elif e in ws: return True
    return False


def warnings(md: str, lint: dict | None = None) -> list[str]:
    """soft title advice (PLAN 2.7, 2.9): promise marker, "Mój" without a result, number + news, min length, series/brand tag"""
    try:  # a hand-edited lint file with a typo or a missing list: name it, never a traceback (warnings keep the exit code)
        return _warnings(md, lint or lint_lists())
    except (OSError, ValueError, KeyError, TypeError) as e:
        return [f"style/title_lint.json cannot be read, title warnings skipped: {e!r}"]


def _warnings(md: str, lint: dict) -> list[str]:
    out: list[str] = []
    for r in titles(md):
        v, t = r["variant"], r["title"]
        if not t: continue
        number = any(c.isdigit() for c in t)
        result = number and hit(t, lint["result"])
        if len(t) < lint["min_len"]: out.append(f"{v}: {len(t)} characters (soft min {lint['min_len']}: short abstract titles lose)")
        marker = result or hit(t, lint["delivery"]) or hit(t, lint["audience"]) or hit(t, lint["pain"]) \
            or any(re.search(x, t.lower()) for x in lint["delivery_regex"])
        if len(t) >= lint["marker_min_len"] and not marker:
            out.append(f"{v}: no promise marker (digit + result, delivery word like 'jak' / 'od zera' / 'w N minut', audience, or pain)")
        if hit(t, lint["mine"]) and not result:
            out.append(f"{v}: 'Mój/Moje/Moja' without a result (a digit with its result): the viewer has no reason to care yet")
        if number and hit(t, lint["news"]):
            out.append(f"{v}: a number next to a news word (news titles lose to evergreen ones)")
        head = t.split(":", 1)[0].strip().lower() if ":" in t else ""
        if (head and head in lint["series_prefix"]) or any(re.search(x, t.lower()) for x in lint["series_prefix_regex"]):
            out.append(f"{v}: series prefix {t.split(':', 1)[0].strip()!r} (spend those characters on the promise)")
        if any(sep in t for sep in lint["brand_separators"]):
            out.append(f"{v}: brand tag after '|' (the channel name is already under the title)")
    return out


def opening_words(plan_path: Path) -> list[str] | None:
    """what is heard in the long's first OPENING s: plan "words" through the EDL ("edl_out") segments"""
    work, plan = plan_path.parent, json.loads(plan_path.read_text())
    wf, ef = work / str(plan.get("words", "")), work / str(plan.get("edl_out", "edl_long.json"))
    if not plan.get("words") or not wf.is_file() or not ef.is_file(): return None
    from viewer_pack import film_words  # OpenCV: only when the opening is read
    heard = film_words(json.loads(wf.read_text())["transcription"], json.loads(ef.read_text())["segments"])
    return [w for t, w in heard if t < OPENING]


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2: print(__doc__, file=sys.stderr); return 2
    opening = opening_words(Path(argv[1])) if len(argv) == 2 else None
    bad = problems(Path(argv[0]).read_text(), opening)
    print("\n".join(bad) or "OK title_check")
    for w in warnings(Path(argv[0]).read_text()): print(f"WARN {w}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
