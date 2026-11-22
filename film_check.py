#!/usr/bin/env python3
"""film_check.py: is everything in the film that has to be there (style/checklist.json)?

  python3 film_check.py <work> <film> [<film> ...]   before the render: plan_<film>.json + its EDL (after build_edl.py)
  python3 film_check.py <work> --out <out>           after the render: the out folder (films, YouTube texts, thumbnails, posts)
  --json                                              the report as JSON on stdout

Exit 0 = every item met or skipped with a reason, 1 = something missing (listed with why), 2 = bad usage or input.
Why: film 2026-11-04 lost half of the pipeline's features (chapters, scenes, text behind, zooms, music, thumbnails) because
nothing checked that they were used. A plan skips an item only by naming why: "skip": {"long.behind": "no wall behind me"}.
Outputs (story.json, clips.json, posts.json) come from the editorial team, team/RUNBOOK.md.
"""
from __future__ import annotations

import datetime
import inspect
import itertools
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import article_check  # the kamiljan.com blog article made from the film
import capabilities  # every feature: used, skipped with a reason, or named as unused
import count_check  # the count he says is the count on the card
import desc_check  # the YouTube descriptions (round 2 Y0-Y5, S2-S3)
import gfx_events  # when a piece comes in inside a scene (prompt_shown_at)
import gfx_types  # next to this script: which card types are a separate screen
import hook_check  # the 6 hook killers
import ig_check  # the Instagram carousels and Reel captions (round 2 IG1-IG6)
import kind as content_kind  # one person or two: which rule set (content_kind.py)
import manifest  # which pipeline commit made each film and material
import post_check  # the LinkedIn post graphic alone (OCR) and the text habits
import research_gate  # research for thumbnails must be in them
import retakes  # the same words said twice: a retake the cut kept (also retake_check.py on the cut itself)
import thumb_check  # the long thumbnails as the feed shows them
import timeline  # film time of a source time: the one place (frame-exact pieces)
import title_check  # the A/B/C titles of the long
import waivers  # Kamil's own words for a rule he set aside (short end_card)

ROOT = Path(__file__).resolve().parent
CHECKLIST = ROOT / "style" / "checklist.json"
BRAND = ROOT / "style" / "brand.json"
LEDGER = ROOT / "render" / "music_ledger.json"
EXPLAINERS = ("scene", "float", "slide", "web")
SKIP_MIN = 10  # a reason shorter than this is not a reason
CHAP_LEAD, CHAP_LAG = 1.0, 3.0  # a chapter card counts for a part when it comes in this close to the part's first word


def bad_input(msg: str) -> NoReturn:
    """a missing or broken input file: named on stderr, exit 2 (not 1, which means items missing)"""
    print(f"film_check: {msg}", file=sys.stderr)
    raise SystemExit(2)


def load(p: Path, what: str):
    try:
        return json.loads(p.read_text())
    except FileNotFoundError:
        bad_input(f"{what} not found: {p}")
    except ValueError as e:
        bad_input(f"{what} is not JSON ({p}): {e}")


TEXT_CARDS = ("kw", "lower", "maxim", "cta")  # words only: a sticker or meme carries a picture (judged in content_review)
# "on", "owner", "extends": piece / film / scene ids (a camera stop "on": ["au"]), not words: a new camera is not a new text (2026-11-08)
TEXT_SKIP_KEYS = {"id", "type", "file", "icon", "bg", "tone", "anim", "k", "src", "url", "photo", "layout", "who", "mark", "head", "font",
                  "on", "owner", "extends", "from", "to"}  # "from"/"to": a line or cursor attached to piece ids (gfx/anchor_lib.mjs)


def says_nothing(title: str, sub: str) -> bool:
    """one word (or none), no sub line, no digit, not a name: "Najwiecej" yes; "GitHub", "kamiljan.com", "92%" no"""
    words = re.findall(r"\w+", title)
    if len(words) > 1 or sub.strip() or re.search(r"\d", title): return False
    is_name = bool(words) and (any(c.isupper() for c in words[0][1:]) or "." in title)  # GitHub, iPhone, kamiljan.com
    return not is_name


def html_words(html: str) -> str:
    """the words a float card's html shows: tags, styles and animation times out (2026-11-15: retime_cards moved the
    delays of 11 floats to the new long cut and every one came back to be read again, words unchanged)"""
    import html as h
    return " ".join(h.unescape(re.sub(r"<[^>]*>", " ", re.sub(r"<(style|script)\b.*?</\1>", " ", html, flags=re.DOTALL))).split())


def card_texts(spec: dict) -> list[str]:
    """every word a card shows: strings anywhere in its spec, not file names, icons, colours or timing"""
    out: list[str] = []
    def walk(v, key=""):
        if isinstance(v, str) and key == "html": out.append(html_words(v))
        elif isinstance(v, str) and key not in TEXT_SKIP_KEYS: out.append(v)
        elif isinstance(v, dict):
            for k, x in sorted(v.items()): walk(x, k)
        elif isinstance(v, list):
            for x in v: walk(x, key)
    walk(spec)
    return out


def card_text_hash(spec: dict) -> str:
    """the key of content_review_<film>.json: a card whose words change must be read again"""
    import hashlib
    return hashlib.sha256("\n".join(card_texts(spec)).encode()).hexdigest()[:16]


def review_problems(f: Path, specs: dict, how: str) -> list[str]:
    """content_review.py verdicts in f for every spec: missing, changed after the review (card_text_hash), not "ok", or
    "ok" without a reason = a problem. how = the content_review.py arguments that make the sheet"""
    if not f.exists(): return [f"no {f.name}: read every text for meaning (python3 content_review.py {how})"]
    rev, bad = load(f, f.name), []
    for i, sp in specs.items():
        r = rev.get(i) if isinstance(rev, dict) else None
        if not isinstance(r, dict): bad.append(f"{i} not reviewed")
        elif r.get("hash") != card_text_hash(sp): bad.append(f"{i} changed after the review")
        elif r.get("verdict") != "ok": bad.append(f"{i} judged {r.get('verdict')!r}: {r.get('why', '')[:60]}")
        elif len(str(r.get("why", "")).strip()) < SKIP_MIN: bad.append(f"{i} ok without a reason")
    return bad


THUMB_TEXT = ("big", "sub", "tag")


def thumb_texts(spec: dict) -> dict:
    """{"long_A": {big, sub, tag}, "cover_s01": {...}}: the words on every thumbnail and Short cover (content_review thumbs)"""
    out = {f"long_{v['id']}": {**{k: v[k] for k in THUMB_TEXT if v.get(k)},
                               **({"panel": w} if (w := thumb_check.thumb_words({"panel": v.get("panel")}).strip()) else {})}
           for v in spec.get("long", [])}
    out.update({f"cover_{v['id']}": {k: v[k] for k in THUMB_TEXT if v.get(k)} for v in spec.get("shorts", [])})
    return out


def word_times(words_file: Path) -> list[float]:
    d = load(words_file, "words")
    return [w["offsets"]["from"] / 1000 for w in d["transcription"]]


NUMBER_WORDS = {"dwa": 2, "dwie": 2, "dwóch": 2, "trzy": 3, "trzech": 3, "cztery": 4, "czterech": 4, "pięć": 5, "pięciu": 5,
                "sześć": 6, "sześciu": 6, "siedem": 7, "siedmiu": 7, "osiem": 8, "ośmiu": 8, **{str(i): i for i in range(2, 11)}}


norm_word = retakes.norm_word  # one normalisation for every word comparison


def in_order(want: list[str], heard: list[str]) -> int:
    """how many of `want` occur in `heard` in the same order (greedy; a word not heard is skipped, the place kept)"""
    pos, n = 0, 0
    for w in want:
        if w in heard[pos:]: pos += heard[pos:].index(w) + 1; n += 1
    return n


def src2out(segments: list[dict], t: float, exact: bool = False) -> float:
    """source time -> film time (timeline.py: whole-frame pieces with seg_exact); a time inside a cut maps to the start
    of the next kept piece"""
    return timeline.src2out(t, segments, exact)


def exact(edl: dict) -> bool:
    return bool(edl.get("seg_exact"))


def body_len(edl: dict) -> float:
    return timeline.total(edl["segments"], exact(edl))


# the film's own look, wanted from start to end; web shots, memes and stickers follow what is said (measured on the
# 2026-11-04 long: web 3/0/2 per third with nothing to show in the middle), so they are not judged
SPREAD_TYPES = ("float", "kw", "scene")
SPREAD_ALL, SPREAD_MIN_S = 4, 180.0
SPREAD_NAMES = ("first", "middle", "last")


def punches(edl: dict) -> list[float]:
    """film times of punch-in zooms: an animated zoom inside a piece (build_edl emph) or an editing-grammar punch"""
    out = []
    for s, acc in zip(edl["segments"], timeline.starts(edl["segments"], exact(edl)), strict=True):
        z = s.get("zoom")
        if isinstance(z, dict) and z.get("keys"):  # keyed moves (beat grammar, podcast word punches): every quick push in
            out += [acc + t0 for (t0, v0), (t1, v1) in itertools.pairwise(z["keys"]) if v1 > v0 + 0.05 and t1 - t0 <= 1.0]
            continue
        # inside the piece, or a fast punch right on its cut (build_edl emph on a word that opens the piece: t0 = 0,
        # 0.3 s; 2026-11-08 s09 counted 1 of its 3 punches); a slow drift over the whole piece is not a punch
        if isinstance(z, dict) and z.get("b", 0) > z.get("a", 0) + 0.1 and (
                z.get("t0", 0) > 0.01 or z.get("t1", 1e9) - z.get("t0", 0) <= 1.0):
            out.append(acc + z.get("t0", 0))
    out += [r["at"] for r in edl.get("beat_fx", []) if r.get("fx") == "punch"]
    out += [t for o in edl.get("overlays", []) for t in o.get("zooms", [])]  # round 2 L17: a canvas zoom inside a scene is a punch
    return sorted(out)


def zoom_steps(edl: dict) -> list[float]:
    """film times where the framing jumps (a jump cut to another zoom level): a picture change too"""
    out, prev = [], None
    for s, acc in zip(edl["segments"], timeline.starts(edl["segments"], exact(edl)), strict=True):
        z = s.get("zoom"); level = z.get("a", 1.0) if isinstance(z, dict) else float(z or 1.0)
        if prev is not None and abs(level - prev) >= 0.08: out.append(acc)
        prev = level if not isinstance(z, dict) else z.get("b", level)
    return out


NOT_READ = {"id", "type", "icon", "tone", "k", "bg", "anim", "file", "owner", "layout", "cam", "img", "src", "sfx", "font", "mark",
            "edl", "words", "behind", "hl", "acc", "theme", "logo", "url", "shot", "meme", "canvas", "side", "on", "from", "to", "icons", "bookend"}  # not read text


def read_words(spec) -> int:
    """words a viewer reads on a card: every string in the spec except the NOT_READ keys; html loses its tags first"""
    if isinstance(spec, str):  # html: no css, inline tags joined (a word drawn letter by letter is one word), others split
        t = re.sub(r"<style.*?</style>", " ", spec, flags=re.DOTALL)
        t = re.sub(r"</?(span|b|i|em|strong)\b[^>]*>", "", t)
        return len(re.sub(r"<[^>]*>|&[a-z]+;", " ", t).split())
    if isinstance(spec, list): return sum(read_words(v) for v in spec)
    if isinstance(spec, dict): return sum(read_words(v) for k, v in spec.items() if k not in NOT_READ)
    return 0


def reading_need(sp: dict, per_word=1.2, head_words=4, per_more=0.35, minimum=2.5, scene_min=6.0) -> float:
    """seconds a card needs on screen: a text card max(minimum, per_word x its first head_words words + per_more x the
    rest: Negacz's 1.5 s a word holds for his 3-word cards, a long line is read at about 3 words a second); a picture card
    (scene drawn piece by piece, web shot, slide: narrated, looked at rather than read) scene_min. Reference: Negacz text
    cards 1.5 s a word (n 92), drawn scenes 23 s median (n 101), style/REF-long-negacz.md L3, L4. The plan builder uses it too"""
    if sp.get("type") in ("scene", "web", "slide") or sp.get("drawn") is True: return scene_min  # "drawn": a card written
    # word by word on the spoken words (film 2 shorts' paper cards, 2026-11-15), looked at like a scene, not read at once
    n = read_words(sp)
    return max(minimum, per_word * min(n, head_words) + per_more * max(n - head_words, 0))

UNTIMED = ("lower", "end", "chap")  # cards held to their own length, not to a reading time (screen_grammar uses the same)


def full_spans(edl: dict, specs: dict) -> list[tuple[float, float]]:
    """time on a separate screen (gfx_types.is_full: the speaker is gone or sits in the corner), overlaps merged"""
    spans: list[list[float]] = []
    for a, b in sorted((o["at"], o["at"] + o["dur"]) for o in edl.get("overlays", [])
                       if gfx_types.is_full(specs.get(o["id"], {}))):
        if spans and a <= spans[-1][1] + 0.05: spans[-1][1] = max(spans[-1][1], b)  # back to back = one screen (frame rounding)
        else: spans.append([a, b])
    return [(a, b) for a, b in spans]


def cover_spans(edl: dict) -> list[tuple[float, float]]:
    """(start, end) of everything the EDL puts over the face: overlays and b-roll"""
    spans = [(o["at"], o["at"] + o["dur"]) for o in edl.get("overlays", [])]
    return spans + [(b["at"], b["at"] + b.get("dur", 0)) for b in edl.get("broll", []) if "at" in b]


PUNCH_ROOM = 1.08  # face_track zmax at or under this: no visible punch fits under the head limit
END_CARD_TAIL = (1.5, 3.5)  # s of an end board after a short's last word when the plan carries Kamil's "end_card" (short.end)
FACE_MIN_S = 10.0  # under this much punchable face a short has nothing to punch into (ADR-0021)


def covered(spans: list[tuple[float, float]], end: float) -> float:
    """seconds of [0, end] under the union of spans"""
    tot, t = 0.0, 0.0
    for a, b in sorted(spans):
        a, b = max(a, t), min(b, end)
        if b > a: tot += b - a
        t = max(t, b)
    return tot


def max_gap(edl: dict, end: float) -> float:
    """longest stretch of the film with no card on screen, no punch-in, no b-roll and no framing jump"""
    moves = [t for o in edl.get("overlays", []) for t in o.get("moves", [])]  # round 2 S14: motion inside a panel (camera, cursor, typing)
    spans = cover_spans(edl) + [(t, t) for t in punches(edl) + zoom_steps(edl) + moves]
    gap, t = 0.0, 0.0
    for a, b in sorted(spans):
        gap = max(gap, a - t); t = max(t, b)
    return round(max(gap, end - t), 1)



def chap_text(spec: dict) -> str:
    """What a chap card shows (gfx/cards_lib.mjs chapHtml): its "text", else the part it starts, parts[current - 1]
    (v5 2026-11-09: part_tag cards carry no "text", and chapters were compared with "None")"""
    if spec.get("text") is not None: return str(spec["text"])
    parts, k = spec.get("parts"), spec.get("current")
    if isinstance(parts, list) and type(k) is int and 1 <= k <= len(parts): return str(parts[k - 1])
    return ""

MEME_CATALOGUE = Path(__file__).resolve().parent / "style" / "memes.json"


def meme_roles_problems(cid: str, sp: dict, roles) -> list[str]:
    """Kamil 2026-11-15 note 44 ("memy źle dobierane, brakuje zrozumienia memów wg kontekstu"): a picture meme's review
    names, box by box, how its text plays the template's role (style/memes.json "roles", the joke's mechanism), so the
    text follows the joke (2026-11-04: Surprised Pikachu got "Gotowe!" / "Nic nie działa", no self-made cause). One entry
    per box, each >= 12 characters; stickers and our own toons are not templates"""
    if sp.get("type") != "meme" or sp.get("toon") is not None: return []
    tpl = json.loads(MEME_CATALOGUE.read_text(encoding="utf-8")).get(str(sp.get("meme")), {})
    want = tpl.get("roles") or []
    if not want: return [f"{cid}: meme {sp.get('meme')!r} has no \"roles\" in style/memes.json"]
    if not (isinstance(roles, list) and len(roles) == len(want) and all(isinstance(x, str) and len(x.strip()) >= 12 for x in roles)):
        return [f'{cid}: "roles" = {len(want)} lines, how each text plays its role: ' + " / ".join(want)]
    return []


class Film:
    def __init__(self, work: Path, name: str):
        self.name = name
        self.plan = load(work / f"plan_{name}.json", f"plan of {name}")
        self.edl = load(work / self.plan.get("edl_out", f"edl_{name}.json"), f"EDL of {name} (run build_edl.py first)")
        self.specs = {s["id"]: s for s in load(work / self.plan["gfx_specs"], "gfx specs")} if self.plan.get("gfx_specs") else {}
        self.vertical = bool(self.plan.get("vertical"))
        self.fmt = "short" if self.vertical else "long"
        self.warns: list[tuple[str, str]] = []  # (item id, advice): printed as WARN, never a failure
        self.work = work
        self.len = body_len(self.edl)
        self.ovs = self.edl.get("overlays", [])

    def typ(self, o: dict) -> str:
        return self.specs.get(o["id"], {}).get("type", "")

    def parts(self) -> list[tuple[str, float, float]]:
        """story.json parts as (title, film start, film end); empty when there is no story"""
        p = self.work / "story.json"
        if not p.exists(): return []
        story = load(p, "story.json"); wt = word_times(self.work / self.plan["words"]); segs = self.edl["segments"]
        if not (isinstance(story, dict) and isinstance(story.get("parts", []), list)):
            bad_input('story.json: {"parts": [{"id", "title", "start_word"}, ...]}')
        for pt in story.get("parts", []):
            sw = pt.get("start_word") if isinstance(pt, dict) else None
            if not (isinstance(sw, int) and not isinstance(sw, bool) and 0 <= sw < len(wt)):
                bad_input(f"story.json part {pt.get('id', '?') if isinstance(pt, dict) else pt!r}: start_word = a word index 0..{len(wt) - 1}, got {sw!r}")
        starts = [(pt.get("title", pt.get("id", "?")), src2out(segs, wt[pt["start_word"]], exact(self.edl))) for pt in story.get("parts", [])]
        return [(t, a, starts[i + 1][1] if i + 1 < len(starts) else self.len) for i, (t, a) in enumerate(starts)]

    def no_chap(self) -> set[str]:
        """parts marked "chap": false (the opening: the hook goes there, not a chapter card)"""
        p = self.work / "story.json"
        if not p.exists(): return set()
        return {pt.get("title", pt.get("id", "?")) for pt in load(p, "story.json").get("parts", []) if pt.get("chap") is False}

    # ---- metrics: name -> value (number, bool or a (bool, detail) pair) ----
    def story_parts(self): return len(self.parts())

    def parts_with_chap_at_start(self):
        chaps = [o["at"] for o in self.ovs if self.typ(o) == "chap"]
        free = self.no_chap()
        miss = [t for t, a, _ in self.parts() if t not in free and not any(a - CHAP_LEAD <= c <= a + CHAP_LAG for c in chaps)]
        return (not miss and bool(self.parts())), f"no chap card at the start of: {', '.join(miss)}" if miss else ""

    def capabilities_missing(self):
        """style/capabilities.json: every "required" feature of the form is in the film or skipped in the plan with a reason
        (`"skip": {"cap.<id>": "why"}`); "report" features not used are WARN (Kamil 2026-11-09: the 2026-11-04 long had no b-roll)"""
        miss, idle = capabilities.coverage(capabilities.load(), self.fmt, capabilities.used(self.plan, self.edl, self.specs, capabilities.default_anims()),
                                           self.plan.get("skip") or {})
        if idle: self.warns.append((f"{self.fmt}.capabilities", f"not used ({len(idle)}): {', '.join(idle)}"))
        bad = capabilities.bad_skips(capabilities.load(), self.plan.get("skip") or {})  # a typo or "ok" waives nothing
        detail = "; ".join(([f"required, not used and not skipped with a reason: {', '.join(miss)}"] if miss else []) + bad)
        return (not miss and not bad), detail

    def parts_with_explainer(self):
        ex = [o["at"] for o in self.ovs if self.typ(o) in EXPLAINERS]
        miss = [t for t, a, b in self.parts() if not any(a <= x < b for x in ex)]
        return (not miss and bool(self.parts())), f"no scene/float/slide/web card in: {', '.join(miss)}" if miss else ""

    def explainers_per_min(self): return round(sum(self.typ(o) in EXPLAINERS for o in self.ovs) / max(self.len / 60, 1e-9), 2)
    def graphics_per_min(self): return round((len(self.ovs) + len(self.edl.get("broll", []))) / max(self.len / 60, 1e-9), 2)
    def max_visual_gap(self): return max_gap(self.edl, self.len)

    def events_first_60s(self):
        ev = [o["at"] for o in self.ovs] + [b.get("at", 1e9) for b in self.edl.get("broll", [])] + punches(self.edl) + zoom_steps(self.edl)
        return sum(0 <= t < 60 for t in ev)

    def punches_per_min(self): return round(len(punches(self.edl)) / max(self.len / 60, 1e-9), 2)

    def punches_per_face_min(self):
        """punches a minute of face on screen with nothing over it: a punch is never made under a card or b-roll
        (build_edl skips emph there), so a short that is 74 % cards (2026-11-08 s09: 34 of 46 s) is judged on the
        12 s it shows the face. Only shots with room for a punch count: face_track's head limit zmax <= PUNCH_ROOM
        means a zoom would cut the head (ADR-0012; 2026-11-08 s17: every shot at zmax 1.0). Under 10 s of such face
        there is nothing to punch into: the card rules judge it."""
        spans = cover_spans(self.edl)
        face = 0.0
        for sg, st in zip(self.edl["segments"], timeline.starts(self.edl["segments"], exact(self.edl)), strict=True):
            if "zmax" in sg and sg["zmax"] <= PUNCH_ROOM:  # no zmax = face_track never limited it: the shot must carry punches
                continue
            end = st + timeline.piece_len(sg, exact(self.edl))
            face += (end - st) - covered([(max(a, st) - st, min(b, end) - st) for a, b in spans if b > st and a < end], end - st)
        if face < FACE_MIN_S: return 99.0, f"{face:.1f} s of face with room for a punch (< {FACE_MIN_S:.0f} s): not judged, the card rules judge this short"
        on_face = [t for t in punches(self.edl) if not any(a <= t < b for a, b in spans)]  # a canvas zoom inside a card is not one
        return round(len(on_face) / (face / 60), 2), ""
    def behind_cards(self): return sum(1 for o in self.ovs if "behind" in self.specs.get(o["id"], {}))

    def effect_spread(self):
        """every kind of effect the film uses is spread over the film, not spent in its first minutes (Kamil 2026-11-10:
        "na poczatku sa jakies efekty potem juz o nich zapominasz"). Kinds: SPREAD_TYPES cards, cards behind the speaker,
        punch-ins. A kind used >= SPREAD_ALL times must be in every third of the film, used 2-3 times in two thirds; a
        kind used once and a film under SPREAD_MIN_S are not judged."""
        if self.len < SPREAD_MIN_S: return True, ""
        kinds: dict[str, list[float]] = {"punch": punches(self.edl)}
        for o in self.ovs:
            if self.typ(o) in SPREAD_TYPES: kinds.setdefault(self.typ(o), []).append(o["at"])
            if "behind" in self.specs.get(o["id"], {}): kinds.setdefault("behind", []).append(o["at"])
        bad = []
        for kind, at in sorted(kinds.items()):
            if len(at) < 2: continue
            hit = {min(int(t / self.len * 3), 2) for t in at}
            need = 3 if len(at) >= SPREAD_ALL else 2
            if len(hit) < need:
                gone = ", ".join(SPREAD_NAMES[i] for i in range(3) if i not in hit)
                bad.append(f"{kind} ({len(at)}x) missing in the {gone} third")
        return not bad, "; ".join(bad)

    def behind_cover_max(self):
        """the worst share of a "behind" text card the speaker hides (behind.py writes <id>.cover.json next to the card);
        "behind": {"drawing": true} (a drawn object, Kamil 2026-11-05 "narysuj szlaban") is not text and is left out;
        a card with no measure counts as fully hidden (phase "behind": run_v4.sh checks it right after behind.py)"""
        gfx = Path(self.plan.get("gfx_dir") or "gfx")
        gfx = gfx if gfx.is_absolute() else self.work / gfx
        got = []
        for o in self.ovs:
            bh = self.specs.get(o["id"], {}).get("behind")
            if not isinstance(bh, dict) or bh.get("drawing"): continue  # a drawing may hide behind him (depth); the limit is for text
            try: c = float(json.loads((gfx / f"{o['id']}.cover.json").read_text())["covered"])
            except (OSError, ValueError, KeyError, TypeError): c = 1.0
            got.append((c, o["id"]))
        got.sort(reverse=True)  # worst first; the limit is the checklist's value, not repeated here
        return (round(got[0][0], 3) if got else 0.0), ("hidden: " + ", ".join(f"{i} {c:.0%}" for c, i in got)) if got else ""
    def meme_cards(self): return sum(self.typ(o) in ("meme", "sticker") for o in self.ovs)

    def meme_review(self, max_age: int = 8, window: float = 6.0, said_share: float = 0.6):
        """Kamil note 19 (2026-11-05, long v2): a meme must fit the sentence and be current. Every meme/sticker card on screen
        has plan "meme_review" {"<card id>": {"sentence", "why", "year", "source"}}: the sentence is said while the card is up
        (said_share of its words from `window` s before to 2 s after), "why" says why it fits, a picture meme names the year it
        started and a source URL, at most max_age years ago (args in style/checklist.json); our own toon needs no year"""
        cards = [o for o in self.ovs if self.typ(o) in ("meme", "sticker")]
        if not cards: return True, "no meme cards"
        rev, bad, now = self.plan.get("meme_review") or {}, [], datetime.datetime.now(datetime.UTC).year
        if not isinstance(rev, dict): return False, f'plan "meme_review" = {{"<card id>": {{...}}}}, got {type(rev).__name__}'
        for o in cards:
            r, sp, cid = rev.get(o["id"]), self.specs.get(o["id"], {}), o["id"]
            if not isinstance(r, dict): bad.append(f'{cid}: no plan meme_review entry {{"sentence", "why", "year", "source"}}'); continue
            words = [w for w in map(norm_word, str(r.get("sentence", "")).split()) if len(w) >= 3]
            heard = [norm_word(w) for t, w in self.film_words() if o["at"] - window <= t <= o["at"] + self.ov_dur(o) + 2]
            got = in_order(words, heard)  # in the order said, not a bag of common words found anywhere (review 2026-11-09)
            if not words: bad.append(f'{cid}: "sentence" = the line the meme illustrates')
            elif got < said_share * len(words): bad.append(f"{cid}: the sentence is not said while the card is up ({got}/{len(words)} words in order)")
            if len(str(r.get("why", "")).strip()) < 15: bad.append(f'{cid}: "why" = why this meme fits that sentence (>= 15 characters)')
            bad += meme_roles_problems(cid, sp, r.get("roles"))
            if sp.get("toon") is not None: continue  # our own drawing: no age, no source
            y = r.get("year")
            if not (isinstance(y, int) and 1990 <= y <= now): bad.append(f'{cid}: "year" = the year the meme started, got {y!r}')
            elif now - y > max_age: bad.append(f"{cid}: the meme is from {y}, more than {max_age} years old (note 19: change it)")
            if not re.match(r"https?://\S+\.\S+", str(r.get("source", ""))): bad.append(f'{cid}: "source" = a URL for the year (e.g. its knowyourmeme page)')
        return not bad, "; ".join(bad[:6]) or f"{len(cards)} memes reviewed"
    # a separate screen too often "rozprasza" (Kamil 2026-11-05, v2 long: 62 full-screen cards, every 21 s, 63 % of the time)
    def full_screen_share(self):
        sp = full_spans(self.edl, self.specs)
        return round(sum(b - a for a, b in sp) / max(self.len, 1e-9), 3), f"{len(sp)} separate screens, {sum(b - a for a, b in sp):.0f} s of {self.len:.0f} s"

    # the bare face: nothing of the EDL on top of it (course author study CCC, n=1: 18-26 % of a lesson is the bare face)
    def face_full(self):
        """share of the long where no overlay (card, float, sticker, scene, lower, chap, end) and no b-roll is on screen"""
        covered, end = 0.0, 0.0
        for a, b in sorted(cover_spans(self.edl)):
            a, b = max(a, end, 0.0), min(b, self.len)  # union, clipped to the film
            if b > a: covered += b - a
            end = max(end, b)
        bare = max(self.len - covered, 0.0)
        return round(bare / max(self.len, 1e-9), 3), (f"{bare:.0f} s of {self.len:.0f} s with nothing on the face; more cards beside the "
                                                      "face (float, kw, sticker) lower it")

    def full_screen_min_gap(self):
        sp = full_spans(self.edl, self.specs)
        gaps = sorted((b2 - a1, a1) for (_, a1), (b2, _) in itertools.pairwise(sp))  # (gap, where it starts)
        if not gaps: return 999.0, ""
        return round(gaps[0][0], 1), "shortest: " + ", ".join(f"{g:.1f} s at {t:.0f} s" for g, t in gaps[:5])

    def cards_shorter_than_reading(self, skip_types=UNTIMED, **rates):
        """cards on screen for less than their reading time (reading_need; Kamil 2026-11-05: "nie zdąży się przeczytać")"""
        short = []
        for o in self.ovs:
            sp = self.specs.get(o["id"], {})
            if sp.get("type") in skip_types: continue
            need = reading_need(sp, **rates)
            if o["dur"] < need - 1e-6: short.append((need - o["dur"], o["id"], o["dur"], need))
        short.sort(reverse=True)
        return len(short), ", ".join(f"{i} {d:.1f} s < {n:.1f} s" for _, i, d, n in short[:6])

    # Negacz (REF-long-negacz.md L1): as much time under scenes as ours (65 %), but 1.3 switches a minute, a scene block
    # 16 s median, the speaker back for 7 s median (3 s p25); ours v2: 2.9 a minute
    def face_windows_head_tracked(self):
        """the PiP windows and corner circles of this film are cut from the recording around the head (assemble.py
        head_track); an EDL without the key keeps the old crop of the zoomed picture for old films"""
        n = sum(1 for o in self.edl.get("overlays", []) if o.get("pip") or o.get("corner"))
        return (self.edl.get("head_track") is True or n == 0), f"{n} face windows, head_track {self.edl.get('head_track', False)}"

    def gfx_lead_early(self):
        """graphics enter before their word (plan "gfx_lead" <= -0.1 s, build_edl.py); a film without graphics passes"""
        lead = self.edl.get("gfx_lead")
        ok = not self.ovs or (isinstance(lead, (int, float)) and not isinstance(lead, bool) and -0.5 <= lead <= -0.1)
        return ok, f"gfx_lead {lead!r} (want -0.5 to -0.1 s), {len(self.ovs)} cards"

    def counts_match(self):
        """the count he says while a card comes in is the count on the card (count_check.py)"""
        # imported here: viewer_pack pulls OpenCV, which the other items do not need
        from viewer_pack import film_words
        words = load(self.work / self.plan["words"], "words json")["transcription"]
        bad = count_check.problems(self.ovs, self.specs, film_words(words, self.edl["segments"]))
        return not bad, "; ".join(bad[:6]) or f"{len(self.ovs)} cards"

    def screen_switches_per_min(self):
        sp = full_spans(self.edl, self.specs)
        return round(len(sp) / max(self.len / 60, 1e-9), 2), f"{len(sp)} separate screens in {self.len / 60:.1f} min"

    def screen_block_median(self):
        d = sorted(b - a for a, b in full_spans(self.edl, self.specs))
        return (round(d[len(d) // 2], 1), f"blocks {d[0]:.1f}-{d[-1]:.1f} s") if d else (999.0, "")


    def lower_matches_brand(self):
        want = load(BRAND, "style/brand.json")["lower_sub"]
        subs = [self.specs[o["id"]].get("sub", "") for o in self.ovs if self.typ(o) == "lower"]
        ok = want in subs
        return ok, "" if ok else f"lower third sub {subs or 'missing'} != {want!r} (style/brand.json)"

    def music_palette_set(self): return isinstance(self.plan.get("music_palette"), dict)

    def music_palette_new(self):
        pal = self.plan.get("music_palette")
        if not isinstance(pal, dict): return False, "no music_palette in the plan: the old bed, the same in every film"
        led = load(LEDGER, "music ledger (render/music_ledger.json, written by make_beds.py)") if LEDGER.exists() else {}
        if not isinstance(led, dict): bad_input(f"music ledger {LEDGER}: an object of entries, got {type(led).__name__}")
        # a fragment test folder is a piece of a film, not the last film (2026-11-14: the fragment of this long refused the long)
        others = [v for v in led.values() if isinstance(v, dict) and v.get("work") != str(self.work.resolve())
                  and not (Path(str(v.get("work") or "/nowhere")) / "FRAGMENT.json").exists()]
        if not others: return True, ""
        last = max(others, key=lambda v: v.get("at", ""))
        same = (last.get("name"), last.get("key", 0)) == (pal.get("name"), pal.get("key", 0))
        return not same, f"same palette and key as the last film ({last.get('work')}, {last.get('film')})" if same else ""

    def music_moods(self): return len(self.plan.get("music_moods") or [])
    def sfx_style_v2(self): return self.plan.get("sfx_style") == "v2"
    def has_end_card(self): return any(self.typ(o) == "end" for o in self.ovs)

    # ---- round 2 long research (creator-study/round2/PLAN2.md L1-L24); each item names its ledger id ----
    def film_word_spans(self) -> list[tuple[float, float]]:
        """(film start, film end) of every kept word, sorted by film time (EDL pieces may play out of source order)"""
        if not hasattr(self, "_fws"):
            raw = load(self.work / self.plan["words"], "words")["transcription"] if self.plan.get("words") else []
            segs, ex = self.edl["segments"], exact(self.edl)
            kept = lambda t: any(sg["in"] <= t <= sg["out"] for sg in segs)
            self._fws = [(src2out(segs, w["offsets"]["from"] / 1000, ex), src2out(segs, w["offsets"]["to"] / 1000, ex)) for w in raw
                         if w.get("text", "").strip() and kept(w["offsets"]["from"] / 1000)]
            self._fws.sort()
        return self._fws

    def film_words(self) -> list[tuple[float, str]]:
        """(film time, word) of every word the cut keeps (its start inside a kept piece)"""
        if not hasattr(self, "_fw"):
            raw = load(self.work / self.plan["words"], "words")["transcription"] if self.plan.get("words") else []
            segs, ex = self.edl["segments"], exact(self.edl)
            kept = lambda t: any(sg["in"] <= t <= sg["out"] for sg in segs)
            self._fw = [(src2out(segs, w["offsets"]["from"] / 1000, ex), w["text"].strip()) for w in raw
                        if w.get("text", "").strip() and kept(w["offsets"]["from"] / 1000)]
        return self._fw

    def scenes_valid(self):
        """the drawn scenes this film shows pass gfx/scene_check.mjs (spec rules, clashes): run_v4.sh stops at that step
        otherwise, after every role signed off (2026-11-09: 8 of 18 short plans had 'canvas_zoom runs into the camera move')"""
        import tempfile
        used = {o["id"] for o in self.ovs}
        scenes = [sp for i, sp in self.specs.items() if i in used and sp.get("type") == "scene"]
        if not scenes: return True, "no drawn scene"
        with tempfile.TemporaryDirectory(prefix="fc-scenes-") as d:
            f = Path(d) / "scenes.json"
            f.write_text(json.dumps(scenes, ensure_ascii=False))
            try:
                r = subprocess.run(["node", str(ROOT / "gfx" / "scene_check.mjs"), str(f)], capture_output=True, text=True,
                                   timeout=900, check=False)
            except (OSError, subprocess.TimeoutExpired) as e:
                return False, f"gfx/scene_check.mjs did not run: {e}"
        lines = (r.stdout + r.stderr).strip().splitlines()
        msg = next((x for x in lines if x.startswith("Error")), None) or next((x for x in lines if "scene_check:" in x), lines[-1] if lines else "")
        return r.returncode == 0, msg or f"gfx/scene_check.mjs exit {r.returncode}, no output"

    def retakes_left(self, n: int = 4, window: float = 20.0):
        """Kamil 2026-11-09 "jak dwa razy coś mówię, bo się pomyliłem, to wytnij i zostaw lepszą wersję": the same n words
        said twice within `window` s of FILM time = a retake the cut kept (retakes.py; retake_check.py hears the cut itself,
        for a take the source transcript lost). A repeat on purpose is named in plan "retakes_ok", one phrase at a time"""
        bad, wrong = retakes.problems(self.film_words(), self.plan, n, window)
        detail = (["retake kept (cut the worse take, or name it in plan retakes_ok): " + "; ".join(bad[:8])] if bad else []) + wrong
        return not bad and not wrong, "; ".join(detail) or "no phrase said twice"

    def story(self) -> dict:
        p = self.work / "story.json"
        return load(p, "story.json") if p.exists() else {}

    def word_at(self, i: int) -> float | None:
        """film time of source word index i (None when cut out or out of range)"""
        raw = load(self.work / self.plan["words"], "words")["transcription"] if self.plan.get("words") else []
        if not (isinstance(i, int) and 0 <= i < len(raw)): return None
        t = raw[i]["offsets"]["from"] / 1000
        return src2out(self.edl["segments"], t, exact(self.edl)) if any(sg["in"] <= t <= sg["out"] for sg in self.edl["segments"]) else None

    def pace_flat(self, block_s: float = 300, drift: float = 0.15, pause_s: float = 1.5):
        """L2: no 5-minute block more than 15 % off the film's median words per minute, no pause over 1.5 s with nothing on
        screen (cards, b-roll, punches). No absolute threshold: Polish creators 114-164 wpm (KS, KO, RS), only a reference"""
        fw = self.film_words()
        if len(fw) < 20: return False, "no words of the film (plan \"words\")"
        blocks = [sum(1 for t, _ in fw if k * block_s <= t < (k + 1) * block_s) / (min(block_s, self.len - k * block_s) / 60)
                  for k in range(int(self.len // block_s) + (self.len % block_s > 60))]
        med = sorted(blocks)[len(blocks) // 2] if blocks else 0
        bad = [f"block {k * block_s / 60:.0f}-{(k + 1) * block_s / 60:.0f} min {b:.0f} wpm vs median {med:.0f}" for k, b in enumerate(blocks)
               if med and abs(b - med) / med > drift]
        spans = cover_spans(self.edl) + [(t, t + 0.6) for t in punches(self.edl)]
        for (_, a), (b, _) in itertools.pairwise(self.film_word_spans()):  # a pause = one word's end to the next one's start
            if b - a > pause_s and not any(x <= a + 0.3 and y >= b - 0.3 for x, y in spans):
                bad.append(f"pause {b - a:.1f} s at {a:.0f} s with nothing on screen")
        return not bad, "; ".join(bad[:6]) or f"{len(blocks)} blocks around {med:.0f} wpm"

    def content_parts(self) -> list[tuple[str, float, float]]:
        free = self.no_chap()
        return [p for p in self.parts() if p[0] not in free]

    def roadmap_in_opening(self, within: float = 50):
        """L3: in the first 50 s the number of parts is said and a list card shows that many items (Hormozi, Graham:
        the viewer knows the road). Parts marked "roadmap": true in story.json = the ones the speaker announces ("trzy pomysły"
        in a 13-chapter film, Kamil 2026-11-09: no skip, the road he names is listed); without marks every content part counts"""
        p = self.work / "story.json"
        marked = {pt.get("title", pt.get("id", "?")) for pt in (load(p, "story.json").get("parts", []) if p.exists() else [])
                  if isinstance(pt, dict) and pt.get("roadmap") is True}
        content = {t for t, _, _ in self.content_parts()}
        if marked - content: return False, f'"roadmap": true on a part without a chapter: {", ".join(sorted(marked - content))}'
        n = len(marked) if marked else len(content)
        if n < 2: return False, f"{n} {'announced' if marked else 'content'} parts in story.json"
        said = {NUMBER_WORDS.get(norm_word(w), -1) for t, w in self.film_words() if t <= within}
        lists = [len(self.specs[o["id"]].get("items", [])) for o in self.ovs if o["at"] <= within and self.typ(o) == "list"]
        bad = ([f"the number {n} is not said in the first {within:.0f} s"] if n not in said else []) + \
              ([f"no list card with {n} items in the first {within:.0f} s (got {lists or 'none'})"] if n not in lists else [])
        return not bad, "; ".join(bad) or f"{n} parts said and listed"

    def first_part_at(self):
        """L4: film time where the first content part starts (the bridge sentence ending the intro = its start_word)"""
        cp = self.content_parts()
        return round(cp[0][1], 1) if cp else self.len

    def end_ok(self):
        """L5: plan "end": "platform" = no full card in the last 20 s, tail <= 1 s, the next film named in the last 30 s and
        plan "next_video"; without the key: an end card, as before (long.end)"""
        if self.plan.get("end") != "platform": return self.has_end_card(), "end card" if self.has_end_card() else "no end card"
        full = [o["id"] for o in self.ovs if o["at"] + o["dur"] > self.len - 20 and gfx_types.is_full(self.specs.get(o["id"], {}))]
        tail = float(self.edl.get("tail", 0) or 0)
        said = " ".join(w.lower() for t, w in self.film_words() if t >= self.len - 30)
        bad = ([f"full cards in the last 20 s: {', '.join(full)}"] if full else []) + ([f"tail {tail:.1f} s > 1"] if tail > 1 else []) + \
              ([] if re.search(r"następn\w* (film|odcin)|kolejn\w* (film|odcin)", said) else ["the next film is not named in the last 30 s"]) + \
              ([] if str(self.plan.get("next_video", "")).strip() else ['no plan "next_video"'])
        return not bad, "; ".join(bad) or "platform end"

    def mid_cta(self, lo: float = 0.15, hi: float = 0.85, max_s: float = 45, chap_gap: float = 3):
        """L6: at most one offer CTA in the middle (15-85 % of the film, <= 45 s, carried by a lower card with a URL, ends
        >= 3 s before the next chap card); story.json "cta_after_part": k asks for one right after part k"""
        mids = [o for o in self.ovs if (self.typ(o) == "cta" or self.specs.get(o["id"], {}).get("cta")) and not self.is_subscribe(o)]
        mids = [o for o in mids if lo * self.len <= o["at"] <= hi * self.len]  # a subscribe card is not an offer (subscribe_mid)
        want = self.story().get("cta_after_part")
        bad = [f"{len(mids)} offer CTAs in the middle (max 1)"] if len(mids) > 1 else []
        chaps = sorted(o["at"] for o in self.ovs if self.typ(o) == "chap")
        for o in mids:
            sp, end = self.specs.get(o["id"], {}), o["at"] + o["dur"]
            if o["dur"] > max_s: bad.append(f"{o['id']} {o['dur']:.0f} s > {max_s:.0f}")
            if not re.search(r"https?://|\w+\.(pl|com|dev|io)\b", json.dumps(sp, ensure_ascii=False)): bad.append(f"{o['id']} has no URL")
            nxt = next((c for c in chaps if c > o["at"]), None)
            if nxt is not None and nxt - end < chap_gap: bad.append(f"{o['id']} ends {nxt - end:.1f} s before a chapter")
        if want is not None:
            cp = self.content_parts()
            if not mids: bad.append(f"story.json cta_after_part {want}: no CTA in the middle")
            elif isinstance(want, int) and 0 <= want < len(cp) and not cp[want][2] - 5 <= mids[0]["at"] <= cp[want][2] + 60:
                bad.append(f"{mids[0]['id']} not right after part {want} ({cp[want][0]})")
        return not bad, "; ".join(bad) or f"{len(mids)} mid CTA"

    def recap(self, max_s: float = 10):
        """L7: a recap before the end: a story part of kind "recap"/"combine", or a card with "recap": true (the opening map
        with every item lit, <= 10 s) in the last fifth"""
        if any(isinstance(p, dict) and p.get("kind") in ("recap", "combine") for p in self.story().get("parts", [])): return True, "recap part"
        rc = [o for o in self.ovs if self.specs.get(o["id"], {}).get("recap") and o["at"] >= 0.8 * self.len]
        if not rc: return False, "no recap part or recap card in the last fifth"
        long_ = [o["id"] for o in rc if o["dur"] > max_s]
        return not long_, f"recap cards over {max_s:.0f} s: {', '.join(long_)}" if long_ else f"recap card {rc[0]['id']}"

    def proof_early(self, within: float = 15):
        """L15: the first proof (a web shot, scene, slide or b-roll from the film's own material) within 15 s"""
        ev = [o["at"] for o in self.ovs if self.typ(o) in ("web", "scene", "slide")] + [b.get("at", 1e9) for b in self.edl.get("broll", [])]
        first = min(ev, default=None)
        return first is not None and first <= within, f"first proof at {first:.1f} s" if first is not None else "no web/scene/slide/b-roll"

    def web_marked(self, min_s: float = 6):
        """L16a: a web card on screen >= 6 s marks what to look at (spec "find": the text the marker underlines)"""
        bad = [o["id"] for o in self.ovs if self.typ(o) == "web" and o["dur"] >= min_s and not self.specs[o["id"]].get("find")]
        return not bad, f"web cards >= {min_s:.0f} s without \"find\": {', '.join(bad[:6])}" if bad else "web cards marked"

    def end_bookend(self, span: float = 30):
        """L18: the end shows again a picture from the first 30 s (same card, or a spec "bookend": <first card id>)"""
        def sig(o: dict) -> str:
            sp = self.specs.get(o["id"], {})
            return sp.get("src") or sp.get("img") or sp.get("shot") or sp.get("url") or o["id"]
        first = {sig(o) for o in self.ovs if o["at"] < span} | {o["id"] for o in self.ovs if o["at"] < span}
        last = [o for o in self.ovs if o["at"] >= self.len - span]
        hit = [o["id"] for o in last if sig(o) in first or self.specs.get(o["id"], {}).get("bookend") in first]
        return bool(hit), f"bookend {hit[0]}" if hit else f"no card of the first {span:.0f} s comes back in the last {span:.0f} s"

    def prompt_shown_at(self) -> list[float]:
        """film times a command / prompt comes on screen: a kw or slide card, or a scene's win / term / chat piece (the
        prompt written out where it is used, gfx_events.piece_at)"""
        out = []
        for o in self.ovs:
            if self.typ(o) in ("kw", "slide"): out.append(o["at"])
            elif self.typ(o) == "scene":
                out += [o["at"] + gfx_events.piece_at(e) for e in self.specs.get(o["id"], {}).get("els", [])
                        if isinstance(e, dict) and e.get("k") in ("win", "term", "chat")]
        return out

    def action_words_shown(self, near: float = 2):
        """L23: a story part's "action_word" (where the command / prompt to try is said) has a kw or slide card within 2 s"""
        bad, n = [], 0
        for p in self.story().get("parts", []):
            if not isinstance(p, dict) or "action_word" not in p: continue
            n += 1; t = self.word_at(p["action_word"])
            if t is None: bad.append(f"{p.get('id')}: action_word {p['action_word']} cut out"); continue
            if not any(abs(a - t) <= near for a in self.prompt_shown_at()): bad.append(f"{p.get('id')}: no kw/slide card or prompt piece at {t:.0f} s")
        return n > 0 and not bad, "; ".join(bad) or (f"{n} action words shown" if n else "no part has an \"action_word\"")

    def framing_changes(self, max_still: float = 45):
        """round 2 L10 ("a second camera from one"): plan zoom_every_s / part_framing used (build_edl edl.framing) and no
        stretch longer than 45 s without a framing change, card or punch (the planned value; face_track may soften it)"""
        used = self.edl.get("options_used", {})
        if not ("zoom_every_s" in used or "part_framing" in used): return False, "plan has neither zoom_every_s nor part_framing"
        fr = self.edl.get("framing", {})
        ms = fr.get("max_still")
        return (ms is None or ms <= max_still), f"{fr.get('changes', '?')} framing changes, longest still {ms} s"

    def said_rows(self, o: dict) -> list[str]:
        """rows of a scene's term / win / file pieces that the speaker says while the card is up (>= 2 of the row's words
        of >= 4 letters, or its only one): those are the lines a read-along lights"""
        said = {norm_word(w) for t, w in self.film_words() if o["at"] <= t <= o["at"] + self.ov_dur(o)}
        out = []
        for e in self.specs.get(o["id"], {}).get("els", []):
            if not (isinstance(e, dict) and e.get("k") in ("term", "win", "file")): continue
            for r in [*(e.get("rows") or []), *(e.get("out") or [])]:
                t = r.get("t") if isinstance(r, dict) else r
                if not isinstance(t, str) or t.startswith("~"): continue
                cw = {norm_word(w) for w in t.split() if len(norm_word(w)) >= 4}
                if cw and len(cw & said) >= min(2, len(cw)): out.append(t)
        return out

    def read_along_used(self):
        """round 2 L16b: a code / window line the speaker reads out is lit when said (overlay "read_along"); lines nobody
        says (placeholders, a window he only points at) need none"""
        need = [o for o in self.ovs if self.typ(o) == "scene" and self.said_rows(o)]
        bad = [f"{o['id']} ({self.said_rows(o)[0][:30]!r})" for o in need if not o.get("read_along")]
        return not bad, f"lines said without read_along: {', '.join(bad[:6])}" if bad else f"{len(need)} scenes with said lines read along"

    def ov_dur(self, o: dict) -> float:
        return float(o.get("dur") or self.specs.get(o["id"], {}).get("dur") or 0)

    def list_said(self, near: float = 90):
        """round 2 L8: a list of >= 3 items brings each item on its word (plan "item_words" -> overlay "items_said", or the
        scene item cues "items"), and two list cards within 90 s are one stacked list ("upto" / "dim_done", EDL variant)"""
        lists = sorted((o for o in self.ovs if self.typ(o) == "list"), key=lambda o: o["at"])
        bad = [f"{o['id']}: {len(self.specs[o['id']].get('items', []))} items not timed to their words (plan item_words)"
               for o in lists if len(self.specs[o["id"]].get("items", [])) >= 3 and not (o.get("items_said") or o.get("items"))]
        bad += [f"{a['id']} + {b['id']} {b['at'] - a['at']:.0f} s apart: one stacked list (upto / dim_done)"
                for a, b in itertools.pairwise(lists) if b["at"] - a["at"] <= near and not (a.get("variant") or b.get("variant"))]
        return not bad, "; ".join(bad[:6]) or f"{len(lists)} list cards"

    def chap_roadmap(self):
        """round 2 L9: every part card is the drawing of the opening map (chap_style "roadmap" / "part_tag", EDL variant)"""
        chaps = [o for o in self.ovs if self.typ(o) == "chap"]
        if not chaps: return False, "no chap cards"
        bad = [o["id"] for o in chaps if o.get("variant") not in ("roadmap", "part_tag")]
        return not bad, f"chap cards without chap_style: {', '.join(bad[:6])}" if bad else f"{len(chaps)} chap cards drawn as the map"

    CUE_DEFINE = re.compile(r"^(czyli|znaczy)$", re.IGNORECASE)
    CUE_NOTE = re.compile(r"^(opisie|opisu|zastrze\w*|link(?:i|u|a|iem|ach|ów)?)$", re.IGNORECASE)  # "link", "linku"...; not "LinkedIn"
    SRC_NOTE = re.compile(r"\bw opisie\b", re.IGNORECASE)  # a web card's source line that carries the pointer ("link w opisie"); review 2026-11-10: not "LinkedIn"

    def define_used(self):
        """round 2 L12: a term the speaker explains ("czyli", "to znaczy") gets a define card (lower + "define": term +
        definition >= 6 s); a film that says none of the cues needs none"""
        cues = [t for t, w in self.film_words() if self.CUE_DEFINE.match(w.strip(".,!?"))]
        n = sum(1 for o in self.ovs if o.get("variant") == "define")
        return n > 0 or not cues, f"{n} define cards, {len(cues)} cue words (czyli / to znaczy)"

    def note_used(self, near: float = 10):
        """round 2 L21: a pointer said aloud ("w opisie", "link", "zastrzeżenie") shows a note card (or the cta) within
        10 s, so a viewer who only reads still gets it; a web card whose source line says it ("... · link w opisie", the
        screen of the repo being pointed to, 2026-11-10 w_repo) shows the pointer too"""
        cues = [t for t, w in self.film_words() if self.CUE_NOTE.match(w.strip(".,!?"))]
        shown = [o["at"] for o in self.ovs if o.get("variant") == "note" or self.typ(o) == "cta"
                 or (self.typ(o) == "web" and self.SRC_NOTE.search(str(self.specs.get(o["id"], {}).get("src", ""))))]
        bad = [t for t in cues if not any(abs(a - t) <= near for a in shown)]
        return not bad, f"said without a note card at {', '.join(f'{t:.0f} s' for t in bad[:6])}" if bad else f"{len(cues)} pointers, all shown"

    def is_subscribe(self, o: dict) -> bool:
        """a cta card that asks to subscribe to the channel (its text), not an offer with a link"""
        return self.typ(o) == "cta" and re.search(r"(?i)subskryb|subscribe", str(self.specs.get(o["id"], {}).get("text", ""))) is not None

    def subscribe_mid(self, lo: float = 0.25, hi: float = 0.7):
        """Kamil 2026-11-15 (note 53): "subskrybowanie kanału gdzieś możesz w jakimś sensownym momencie wrzucić raz": one
        subscribe card (cta whose text asks to subscribe), between lo and hi of the film, after the viewer got something
        (2026-11-04 long: its only one was at 22:02 of 22:24, under the outro)"""
        subs = [o for o in self.ovs if self.is_subscribe(o)]
        mid = [o for o in subs if lo * self.len <= o["at"] <= hi * self.len]
        where = ", ".join(f"{o['id']} at {o['at'] / max(self.len, 1):.0%}" for o in subs) or "none"
        return len(mid) == 1 and len(subs) == 1, f"subscribe cards: {where} (want one, at {lo:.0%}-{hi:.0%} of the film)"

    def scene_specs(self) -> list[tuple[dict, dict]]:
        """(overlay, spec) of every drawn scene on screen"""
        return [(o, self.specs.get(o["id"], {})) for o in self.ovs if self.typ(o) == "scene"]

    def scene_whole(self):
        """Kamil 2026-11-15 (note 50): "zoomowanie elementów jak tłumaczymy… bez sensu, gubimy sporo treści": a drawn scene
        stays whole in the frame, no canvas_zoom and no camera stop on one piece (cam "on" other than "*"); replaces
        round 2 L17 (scene_zoom), which Kamil rejected"""
        bad = []
        for o, sp in self.scene_specs():
            if sp.get("canvas_zoom") or o.get("zooms"): bad.append(f"{o['id']}: canvas_zoom")
            raw = sp.get("cam")
            cams: list = raw if isinstance(raw, list) else []  # "cam": "none" = a still camera, nothing to stop on
            on = [c.get("on") for c in cams if isinstance(c, dict) and c.get("on") not in (None, "*")]
            if on: bad.append(f"{o['id']}: camera on {on[0]!r} (use \"on\": \"*\")")
        return not bad, "; ".join(bad[:6]) or "every scene whole in the frame"

    def scene_hold(self, min_s: float = 3.0):
        """Kamil 2026-11-15 (note 45): "czasami za szybko rzeczy znikają co są rysowane": every drawn piece stays >= min_s
        from its "at" to its "gone" or to the end of the scene on screen (the card's own dur or the EDL's, the shorter)"""
        bad = []
        for o, sp in self.scene_specs():
            end_card = min(float(sp.get("dur") or 0) or self.ov_dur(o), self.ov_dur(o))
            for e in sp.get("els") or []:
                at = float(e.get("at") or 0); end = min(float(e["gone"]), end_card) if e.get("gone") is not None else end_card
                if end - at < min_s: bad.append(f"{o['id']}.{e.get('id', e.get('k'))} {end - at:.1f} s")
        return not bad, f"pieces up < {min_s:g} s: {', '.join(bad[:8])}" if bad else "every piece stays long enough to read"

    def scene_detail(self, s_per_piece: float = 3.0):
        """Kamil 2026-11-15 (note 46): "mało realnie jest rysowane… więcej elementów, strzałek, jakby ktoś realnie to
        tłumaczył": a scene brings a new piece at least every s_per_piece seconds, and two or more boxes (node, chip, file,
        win) are joined by at least one line (arrow)"""
        bad = []
        for o, sp in self.scene_specs():
            els, dur = sp.get("els") or [], self.ov_dur(o)
            if dur / max(len(els), 1) > s_per_piece: bad.append(f"{o['id']}: {len(els)} pieces in {dur:.0f} s")
            if sum(e.get("k") in ("node", "chip", "file", "win") for e in els) >= 2 and not any(e.get("k") == "line" for e in els):
                bad.append(f"{o['id']}: boxes without an arrow")
        return not bad, "; ".join(bad[:8]) or "scenes drawn in detail"

    @staticmethod
    def scene_events(sp: dict) -> list[float]:
        """every moment a drawn scene changes on screen (s from the card start): pieces coming in and leaving, chat messages,
        words, rows marked or lit, values set, code marks, clicks, switches, counts (style/REF-shorts-arjay.md: the panel
        changes on the word, not only when a new piece comes in)"""
        def num(v):
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
        ts: list[float] = []
        for e in sp.get("els") or []:
            if not isinstance(e, dict):
                continue
            for k in ("at", "gone", "dim", "hl_at", "strike_at", "click_at", "on_at", "back_at", "x_at", "out_at", "out_start", "cmd_at", "packet_at", "type_at"):
                if (v := num(e.get(k))) is not None: ts.append(v)
            pulse = e.get("pulse_at")
            ts += [v for v in map(num, pulse if isinstance(pulse, list) else [pulse]) if v is not None]
            ts += [v for m in e.get("msgs") or [] if isinstance(m, dict) and (v := num(m.get("at"))) is not None]
            for key in ("words", "set", "state", "set_cell", "mark", "read_along", "steps", "lit", "fail", "packet", "show", "fill", "pick", "head"):
                ts += [v for x in e.get(key) or [] if isinstance(x, list) and x and (v := num(x[0] if key != "words" else x[1])) is not None]
            for key in ("steps", "items", "fields", "lanes"):  # round 2 pieces: a step / bar / field / segment lands or changes
                for x in e.get(key) or []:
                    if not isinstance(x, dict): continue
                    ts += [v for k in ("at", "b_at") if (v := num(x.get(k))) is not None]  # b_at: the second dot of a bar
                    ts += [v for y in x.get("set") or [] if isinstance(y, list) and y and (v := num(y[0])) is not None]
                    ts += [v for g in x.get("segs") or [] if isinstance(g, dict) and (v := num(g.get("at"))) is not None]
            for key, sub in (("reveal", "at"), ("note", "at"), ("button", "press_at")):
                if isinstance(e.get(key), dict) and (v := num(e[key].get(sub))) is not None: ts.append(v)
            for r in e.get("rows") or []:
                if isinstance(r, dict):
                    ts += [v for k in ("mark_at", "hl_at") if (v := num(r.get(k))) is not None]
            if isinstance(e.get("count"), dict) and (v := num(e["count"].get("at"))) is not None: ts.append(v)
        return sorted(set(ts))

    def scene_beat(self, max_gap: float = 2.5):
        """style/REF-shorts-arjay.md (2026-11-16): the explainer panel never stands still longer than ~2.3 s (measured on 15
        shorts, median of the longest still stretch); a drawn scene on screen changes something (a piece, a row lit, a
        value set, a word, a mark) at least every max_gap s, counting from the card start to its end"""
        bad = []
        for o, sp in self.scene_specs():
            dur = min(float(sp.get("dur") or 0) or self.ov_dur(o), self.ov_dur(o))
            if dur <= 0: bad.append(f"{o['id']} has no length (no \"dur\" on the card or the scene): nothing measured"); continue
            ts = [0.0, *[t for t in self.scene_events(sp) if 0 <= t <= dur], dur]
            gap, at = max(((b - a), a) for a, b in itertools.pairwise(ts))
            if gap > max_gap: bad.append(f"{o['id']} still {gap:.1f} s from {at:.1f} s")
        if not self.scene_specs(): return True, "no drawn scene on screen (nothing to measure)"
        return not bad, f"scenes standing still > {max_gap:g} s: {', '.join(bad[:8])}" if bad else "every scene changes on the word"

    TEXT_KINDS = ("chip", "text", "say", "big", "stat", "steps")  # pieces that only write a thing
    TIED_KINDS = ("line", "tag", "ring", "stamp", "check", "cursor")  # pieces placed on another one: not a picture of their own

    def scene_visual(self, max_share: float = 0.5):
        """style/REF-shorts-arjay.md › Gramatyka obrazu (Kamil 2026-11-16: "on bardziej wizualizuje wiecej rzeczy a my tylko
        napisy"): a scene draws the thought (a flow, tiles, bars, a timeline, a quiz, a card, a table, code, a window) and
        writes it only now and then; at most max_share of its own pieces only write (chip, text, say, big, stat, steps)"""
        bad = []
        for o, sp in self.scene_specs():
            own = [e.get("k") for e in sp.get("els") or [] if isinstance(e, dict) and e.get("k") not in self.TIED_KINDS]
            txt = sum(1 for k in own if k in self.TEXT_KINDS)
            if own and txt / len(own) > max_share: bad.append(f"{o['id']} {txt}/{len(own)} pieces only write")
        if not self.scene_specs(): return True, "no drawn scene on screen (nothing to measure)"
        return not bad, "; ".join(bad[:8]) or "scenes draw the thought, not only write it"

    def scene_concrete(self, max_share: float = 0.34):
        """style/REF-shorts-arjay.md: the panel shows real things (a row "42 Blue mug 5", a named person, a real command),
        not grey placeholder lines; at most max_share of the rows and messages of a scene are "~" placeholders"""
        bad = []
        for o, sp in self.scene_specs():
            rows = []
            for e in sp.get("els") or []:
                if not isinstance(e, dict): continue
                if e.get("k") in ("win", "file"): rows += e.get("rows") or ["~80", "~55", "~70"]
                if e.get("k") == "chat": rows += [m.get("t") for m in e.get("msgs") or [] if isinstance(m, dict)]
            txt = [r.get("t") if isinstance(r, dict) else r for r in rows]
            sk = sum(1 for t in txt if not isinstance(t, str) or re.fullmatch(r"~\d*", t))
            if txt and sk / len(txt) > max_share: bad.append(f"{o['id']} {sk}/{len(txt)} placeholder rows")
        if not self.scene_specs(): return True, "no drawn scene on screen (nothing to measure)"
        return not bad, "; ".join(bad[:8]) or "scenes show real rows, not placeholders"

    def list_items(self, min_on: float = 3):
        """round 2 S11: list item cards in a short stay >= 3 s each (build_edl already holds each to <= 0.3 s after its
        numeral, gfx_events.cue_problems)"""
        cards = [o for o in self.ovs if o.get("items")]
        bad = [f"{o['id']} item {k + 1} {b - a:.1f} s" for o in cards for k, (a, b) in enumerate(o["items"]) if b - a < min_on]
        return not bad, "; ".join(bad[:6]) or f"{len(cards)} item cards"

    def panel_moves(self, every: float = 3, panel: float = 4):
        """round 2 S14: a web / scene panel on screen >= 4 s moves (scroll, cursor, typing, camera on the spoken line)
        at least every 3 s (gfx_events overlay "moves")"""
        bad = []
        for o in self.ovs:
            d = self.ov_dur(o)
            if self.typ(o) not in ("web", "scene") or d < panel: continue
            ts = [o["at"], *sorted(o.get("moves", [])), o["at"] + d]
            if (g := max(b - a for a, b in itertools.pairwise(ts))) > every: bad.append(f"{o['id']} still {g:.1f} s")
        return not bad, "; ".join(bad[:6]) or "every panel moves"

    def words_per_min(self):
        """round 2 P0.6 (info, no threshold): kept words per minute of the cut and of the speech (gaps > 1 s out); the PL
        band is set from our own films first (REF-shorts-top PL 166 [156; 174] wpm, n=5), never copied from EN 180-250"""
        fw = self.film_words()
        if len(fw) < 2: return False, "no words"
        ts = [t for t, _ in fw]
        speech = sum(min(b - a, 1.0) for a, b in itertools.pairwise(ts)) or 1e-9
        return True, f"{len(fw) / max(self.len / 60, 1e-9):.0f} wpm of the cut, {(len(fw) - 1) / (speech / 60):.0f} wpm of the speech"

    def opening_pace(self):
        """L24 (info, no threshold): words in the first 30 s and words per minute of the hook vs the body (PL 65-104 words
        in 30 s, KS, KO)"""
        fw = self.film_words()
        if not fw: return False, "no words"
        w30 = sum(1 for t, _ in fw if t < 30)
        body = sum(1 for t, _ in fw if t >= 30) / max((self.len - 30) / 60, 1e-9)
        return True, f"{w30} words in the first 30 s ({w30 * 2} wpm), body {body:.0f} wpm"

    def filler_cards(self):
        """text cards that say nothing: one word, no sub line, no number, no name (Kamil 2026-11-08 on the card
        "Najwiecej": "bez sensu pisac takie cos w takim okienku ... nic to nie wnosi")"""
        bad = []
        for o in self.ovs:
            sp = self.specs.get(o["id"], {})
            if sp.get("type") not in TEXT_CARDS: continue
            title = str(sp.get("title") or sp.get("text") or "").strip()
            if says_nothing(title, str(sp.get("sub") or "")): bad.append(f"{o['id']} \"{title}\"")
        return not bad, ", ".join(bad) or f"{sum(self.specs.get(o['id'], {}).get('type') in TEXT_CARDS for o in self.ovs)} text cards"

    def meaning_reviewed(self):
        """every card's words were read for meaning before the render: work/content_review_<film>.json
        {id: {"verdict": "ok", "why": "what it adds for a viewer who has not seen the film", "hash": <card_text_hash>}}.
        A card changed after the review (hash), missing, judged "cut" but still in the plan, or "ok" without a reason = FAIL.
        Why: Kamil 2026-11-08: "znajdz sobie wiecej takich bez sensownych nic nie wnoszacych rzeczy", the blog cover
        "18% LECI NA SLEPO" had no meaning without the film"""
        ids = sorted({o["id"] for o in self.ovs if o.get("id") in self.specs})
        if not ids: return True, "no cards"
        bad = review_problems(self.work / f"content_review_{self.name}.json", {i: self.specs[i] for i in ids}, f"{self.work} {self.name}")
        return not bad, (f"{len(bad)} of {len(ids)}: " + "; ".join(bad[:6])) if bad else f"{len(ids)} cards reviewed"

    def stills_accepted(self):
        """every card of the film has a still Kamil accepted (stills.py, ADR-0018): without this item a film that never made
        a stills sheet would render with no look at its cards; render.mjs checks that the accepted version is the one rendered"""
        import stills  # only here: it pulls OpenCV
        acc = stills.gfx_dir(self.work / f"plan_{self.name}.json", self.edl) / "stills" / "accepted.json"
        ids = sorted({o["id"] for o in self.ovs if o.get("id") in self.specs})
        if not ids: return True, "no cards"
        if not acc.exists(): return False, f"no stills sheet yet: python3 stills.py plan_{self.name}.json, Kamil looks, stills.py accept"
        ok = load(acc, "gfx/stills/accepted.json")
        # a still drawn after the acceptance with another key = the card changed since Kamil saw it (the render key itself is
        # JS: a card changed with no new still is stopped by render.mjs, by name)
        newer = lambda i: (k := acc.parent / f"{i}.key").exists() and k.read_text() != ok[i]
        miss = [i for i in ids if i not in ok or newer(i)]
        return not miss, (f"{len(miss)} of {len(ids)} cards without an accepted still of their current version: {', '.join(miss[:6])}" if miss else f"{len(ids)} cards")

    def ends_on_the_last_word(self, tail_max: float):  # tail_max: style/checklist.json short.end args
        """a short stops right after its last word and loops: no end card, no end screen (REF-shorts-top T8: 30/30 top shorts
        end 0.23 s after the last word, none shows an end board)"""
        tail = float(self.edl.get("tail", 0) or 0)
        hold = self.plan.get("end_hold")
        if hold is not None:  # round 2 S5: a 1.0-1.6 s hold only on a scene or maxim in the tail, never a CTA
            last = [self.typ(o) for o in self.ovs if o["at"] + o["dur"] >= self.len + tail - 0.1]
            ok = isinstance(hold, (int, float)) and 1.0 <= hold <= 1.6 and tail <= hold + 0.05 and bool(last) and all(t in ("scene", "maxim") for t in last)
            return ok and not self.has_end_card(), f"end_hold {hold}, tail {tail:.1f} s, cards in the tail {last or 'none'} (want scene/maxim, hold 1.0-1.6 s)"
        said = self.plan.get("end_card")
        if said is not None:  # Kamil 2026-11-15: a short ends on a board pointing to the full film on the channel, in his words
            ends = [o for o in self.ovs if self.typ(o) == "end"]
            ok = (isinstance(said, str) and waivers.SAID.match(said) is not None and len(ends) == 1
                  and END_CARD_TAIL[0] <= tail <= END_CARD_TAIL[1] and ends[0]["at"] >= self.len - 0.05)
            return ok, (f"end_card ({said!r}): {len(ends)} end card(s), tail {tail:.1f} s (want one end card after the last word, "
                        f"tail {END_CARD_TAIL[0]}-{END_CARD_TAIL[1]} s, plan end_card 'Kamil YYYY-MM-DD: his words')")
        return (tail <= tail_max and not self.has_end_card()), f"tail {tail:.1f} s, end card {self.has_end_card()}"
    def hook_text(self):  # the hook line from the plan (ASS) or a card on screen from the first half second
        return bool(str(self.plan.get("hook_text", "")).strip()) or any(o["at"] <= 0.5 for o in self.ovs)
    def hook_lint(self):
        """the hook on screen from the first frame passes the 6 killers (hook_check.py): the plan's hook_text, else the
        text of a card that is up by 0.5 s"""
        text = str(self.plan.get("hook_text", "")).strip()
        if not text:
            first = next((o for o in sorted(self.ovs, key=lambda o: o["at"]) if o["at"] <= 0.5), None)
            spec = self.specs.get(first["id"], {}) if first else {}
            text = " ".join(str(spec.get(k, "")) for k in ("text", "sub")).strip()
        bad = hook_check.problems(text, on_screen=bool(text))
        return not bad, f"{text!r}: " + "; ".join(bad) if bad else text

    def first_sentence(self) -> str:
        out = []
        for _, w in self.film_words():
            out.append(w)
            if re.search(r"[.?!…]$", w): break
        return " ".join(out)

    def last_sentence_at(self) -> float | None:
        fw = self.film_words()
        if not fw: return None
        k = max((i for i in range(len(fw) - 1) if re.search(r"[.?!…]$", fw[i][1])), default=-1)
        return fw[k + 1][0]

    def hook_echo(self, share: float = 0.5):
        """round 2 S4: the hook on screen says something the title and the first sentence do not: under 50 % of its content
        words shared with the short's title (clips.json title_work) or with its first spoken sentence (WARN)"""
        hook = str(self.plan.get("hook_text", "")).strip()
        if not hook: return True, "no hook_text"
        clips = self.work / "clips.json"
        title = next((str(c.get("title_work", "")) for c in (load(clips, "clips.json").get("items", []) if clips.exists() else []) if c.get("id") == self.name), "")
        key = lambda t: {norm_word(w)[:5] for w in t.split() if len(norm_word(w)) >= 4 or any(ch.isdigit() for ch in w)}
        hk = key(hook)
        if not hk: return True, "hook without content words"
        bad = [f"{name} {len(hk & key(t)) / len(hk):.0%}" for name, t in (("title", title), ("first sentence", self.first_sentence())) if t and len(hk & key(t)) / len(hk) >= share]
        return not bad, f"the hook repeats the {', '.join(bad)} of its words" if bad else "the hook adds to the title and first sentence"

    def callback_end(self):
        """round 2 S6 (Sinek 3/3): the last sentence comes back to the hook: a number or content word of the first sentence
        (shorts.callback, which also scores the clip choice) or of the hook text (WARN)"""
        import shorts  # the clip scout's own rule, one definition
        fw = self.film_words(); at = self.last_sentence_at()
        if at is None: return False, "no words"
        last = " ".join(w for t, w in fw if t >= at)
        ok = shorts.callback(self.first_sentence() + " " + str(self.plan.get("hook_text", "")), last)
        return ok, "the end comes back to the hook" if ok else f"the last sentence {last[:60]!r} does not come back to the hook"

    def changes_per_min(self, scene_share: float = 0.5):
        """round 2 S7: picture changes a minute (punch-ins + framing jumps + card starts); a short that is >= 50 % scene
        moves inside the scene and is not counted (refutes "never > 6 s of face")"""
        sc = sum(o["dur"] for o in self.ovs if self.typ(o) == "scene") / max(self.len, 1e-9)
        n = len(punches(self.edl)) + len(zoom_steps(self.edl)) + len(self.ovs)
        v = round(n / max(self.len / 60, 1e-9), 1)
        return (v if sc < scene_share else 99.0), f"{n} changes in {self.len:.0f} s" + (f", scene {sc:.0%} (not counted)" if sc >= scene_share else "")

    def last_line_on_face(self):
        """round 2 S15: the last sentence is said on the face: no full-screen card or split over it (skip: end_hold)"""
        if self.plan.get("end_hold") is not None: return True, "end_hold: the tail holds a card"
        at = self.last_sentence_at()
        if at is None: return False, "no words"
        # the end board of plan end_card comes after the last word and is checked by short.end, not here
        boards = {o["id"] for o in self.ovs if self.typ(o) == "end"} if self.plan.get("end_card") is not None else set()
        over = [o["id"] for o in self.ovs if o["id"] not in boards and o["at"] + o["dur"] > at + 0.2 and (gfx_types.is_full(self.specs.get(o["id"], {})) or
                self.specs.get(o["id"], {}).get("layout") == "split" or o.get("split"))]
        return not over, f"cards over the last sentence ({at:.1f} s): {', '.join(over)}" if over else "the last sentence on the face"

    def short_options(self):
        """round 2 S8 (hook in the middle band + a punch on its end), S9 (one key word a caption line), S16 (the hook's
        nouns shown, or the producer told why not): the short's EDL options_used / plan hook_show_report"""
        used = self.edl.get("options_used", {})
        bad = ([] if used.get("hook_pos") == "mid" else ["hook_pos is not \"mid\" (S8)"]) + \
              ([] if used.get("caption_emph") == "key" else ["caption_emph is not \"key\" (S9)"])
        rep = self.plan.get("hook_show_report")
        if rep and rep.get("missing"): bad.append(f"hook_show: no asset for {', '.join(map(str, rep['missing']))} (rewrite the hook or add hook_assets)")
        return not bad, "; ".join(bad) or "S8, S9 used"

    def first_overlay_at(self): return 0.0 if self.hook_text() else round(min((o["at"] for o in self.ovs), default=self.len), 2)
    def film_len(self): return round(self.len, 1)  # seconds of the finished film (team/roles/producent-shortow.md: a short 30-55 s)
    def caption_pop(self): return self.plan.get("caption_pop") is True

    def layout_cards(self):
        return sum(1 for o in self.ovs if o.get("split") or o.get("corner") or self.typ(o) in ("web", "meme")
                   or self.specs.get(o["id"], {}).get("layout") in ("split", "corner", "full"))


class Out:
    def __init__(self, work: Path, out: Path):
        self.work, self.out = work, out
        self.warns: list[tuple[str, str]] = []  # (item id, advice): the item's "warnings", printed as WARN, never a failure
        self.story = load(work / "story.json", "story.json") if (work / "story.json").exists() else {}
        self.plan = {"skip": self.story.get("skip", {})}

    def made(self, fname: str) -> list[str]:
        p = self.work / fname
        return [c["id"] for c in load(p, fname).get("items", []) if c.get("make")] if p.exists() else []

    def out_long(self):
        films = sorted((self.out / "long").glob("*.mp4"))
        return bool(films), "" if films else "no out/long/*.mp4"

    def out_shorts_vs_clips(self):
        want = self.made("clips.json")
        if not want: return False, "clips.json has no clip with \"make\": true (shorts scout role)"
        miss = [c for c in want if not (self.out / "shorts" / f"{c}.mp4").exists()]
        return not miss, f"not rendered: {', '.join(miss)}" if miss else ""

    def out_youtube_meta(self):
        """long.md has its A/B/C titles; every description passes desc_check.py (chapters inside the long's description,
        a link to the long in every short, hashtag limits, no template leftovers; its WARN lines go to the report)"""
        p = self.out / "youtube" / "long.md"
        if not p.exists(): return False, "no out/youtube/long.md"
        t = p.read_text()
        need = [h for h in ("## Tytuły", "## Opis") if h not in t]
        titles = len(re.findall(r"^\| *[ABC] *\|", t, re.MULTILINE))
        bad = need + ([f"{titles} titles (want A, B, C rows)"] if titles < 3 else [])
        edl = self.work / "edl_long.json"
        try:
            film_s = body_len(load(edl, "edl_long.json")) if edl.exists() else None
            b, w = desc_check.check(self.out, film_s, self.made("clips.json"), post_check.article_said(self.long_words()))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
            return False, f"desc_check failed: {e}"
        self.warns += [("out.youtube", x) for x in w]
        bad += b
        if self.long_words() is None: bad.append('numbers in the descriptions cannot be checked: plan_long.json names no "words" file that exists')  # as out.posts: never a silent skip
        return not bad, "; ".join(bad[:8])

    def out_titles(self):
        """the A/B/C titles (title_check.py): length, the phrase in the first words, a source, the promise said in the first 30 s"""
        p = self.out / "youtube" / "long.md"
        if not p.exists(): return False, "no out/youtube/long.md"
        plan = self.work / "plan_long.json"
        bad = title_check.problems(p.read_text(), title_check.opening_words(plan) if plan.exists() else None)
        self.warns += [("out.titles", w) for w in title_check.warnings(p.read_text())]
        return not bad, "; ".join(bad[:8])

    def out_hooks(self):
        """every short that is made has >= 3 hook variants that pass the 6 killers, the chosen one among them, and the
        hook bank row it started from (hook_check.py, style/hook_bank.json)"""
        p = self.work / "clips.json"
        items = [c for c in load(p, "clips.json").get("items", []) if c.get("make")] if p.exists() else []
        if not items: return False, "clips.json has no clip with \"make\": true"
        try:  # the loop too: a list missing in hook_lint.json is a KeyError only when the first hook is read
            ids, wl = set(hook_check.bank()), hook_check.lists()
            bad = [b for c in items for b in hook_check.clip_problems(c, ids, wl)]
        except (OSError, ValueError, KeyError, TypeError) as e:  # a hand-edited style file with a typo: name it
            return False, f"style/hook_bank.json or style/hook_lint.json cannot be read: {e!r}"
        return not bad, "; ".join(bad[:8]) or f"{len(items)} shorts"

    @staticmethod
    def research_open(form: str) -> list[str]:
        """research_gate.problems for a form; RESEARCH_GATE=off (logged by run_v4) or no ledger on this computer = none"""
        if os.environ.get("RESEARCH_GATE", "on") == "off" or not research_gate.LEDGER.exists(): return []
        return research_gate.problems(research_gate.load(research_gate.LEDGER), form, research_gate.checklist_ids())

    def out_thumbnails(self):
        d = self.out / "thumbnails"
        # research meant for thumbnails must be in them (research_gate.py; Kamil 2026-11-08 "dlaczego nic nie weszlo")
        if rb := self.research_open("thumbs"):
            return False, f"research_gate thumbs: {len(rb)} open: " + "; ".join(rb[:4])
        # one variant = long_<id>.jpg; thumbs.mjs also writes long_<id>_2560.png, which must not count as a second variant
        longs = {f.stem.removeprefix("long_") for f in d.glob("long_*.*") if f.suffix in (".jpg", ".png") and not f.stem.endswith("_2560")}
        miss = [c for c in self.made("clips.json") if not list(d.glob(f"{c}_cover.*"))]
        bad = ([f"{len(longs)} long thumbnail variants (want >= 2 for an A/B test)"] if len(longs) < 2 else []) + [f"no cover for {c}" for c in miss]
        return not bad, "; ".join(bad)

    def out_thumbs_read(self):
        """the long thumbnails at feed size (thumb_check.py): "big" read by OCR at 320 px, one variant without a face, words
        that complete the titles instead of repeating them"""
        spec = self.work / "thumbs.json"
        if not spec.exists(): return False, "no thumbs.json next to the plans (thumbs.mjs input)"
        md = self.out / "youtube" / "long.md"
        text = md.read_text() if md.exists() else ""
        titles = [r["title"] for r in title_check.titles(text)]
        try:
            sp = load(spec, "thumbs.json")
            bad, warns = thumb_check.check(sp, self.out, titles, title_check.phrase(text))
            bad = thumb_check.pick_problems(sp) + review_problems(self.work / "content_review_thumbs.json", thumb_texts(sp), f"{self.work} thumbs") + bad
            self.warns += [("out.thumbs_read", w) for w in warns]
        except (RuntimeError, OSError, ValueError, ImportError, subprocess.SubprocessError) as e:  # ffmpeg, tesseract, OpenCV
            return False, f"thumb_check failed: {e}"
        return not bad, "; ".join(bad[:8])

    def split_full_ab(self):
        """round 2 S19: layout "split_full" tried on 1-2 shorts as an A/B (split_share observed, never a rule)"""
        n = sum(1 for p in sorted(self.work.glob("edl_*.json")) if (load(p, p.name).get("options_used") or {}).get("split_full"))
        return 1 <= n <= 2, f"{n} shorts with split_full (want 1-2 for the A/B)"

    def thumbs_research(self):
        """round 2 TH4/TH6/TH8 in the thumbnails: every face variant placed by `thumb_check.py --place` ("placed") or with
        a hand "fx", tone "lift" on face variants, and the no-face variant built as layout "object" / a panel (a real object
        at >= 40 % of the height), not a crop of a chart"""
        spec = self.work / "thumbs.json"
        if not spec.exists(): return False, "no thumbs.json"
        longs = load(spec, "thumbs.json").get("long", [])
        face = [v for v in longs if not v.get("no_face") and v.get("layout") != "object"]
        bad = [f"long_{v['id']}: not placed (thumb_check.py --place)" for v in face if not (v.get("placed") or "fx" in v)]
        bad += [f"long_{v['id']}: tone is not \"lift\"" for v in face if v.get("tone") != "lift"]
        if not any(v.get("layout") == "object" or v.get("panel") for v in longs): bad.append("no variant with layout \"object\" or a panel (TH8)")
        return not bad, "; ".join(bad[:6]) or f"{len(longs)} variants use TH4/TH6/TH8"

    def out_manifest(self):
        """every film and material folder made by the current pipeline code (manifest.py)"""
        if not self.out.is_dir(): return False, f"no out folder {self.out}"
        bad = manifest.check(self.out)
        return not bad, f"{len(bad)} part(s): " + "; ".join(bad[:6]) if bad else "every part stamped by the current code"

    def short_titles(self, need: int = 2):
        """plan1 5.3: every short that is made has >= 2 title variants (A/B in its `## Tytuły` table, title_check rows), each
        <= 60 characters; WARN when none follows "Claude Code + <business thing> = <result>" (the niche's best pattern)"""
        bad = []
        for c in self.made("clips.json"):
            p = self.out / "youtube" / "shorts" / f"{c}.md"
            rows = title_check.titles(p.read_text(encoding="utf-8")) if p.exists() else []
            if len(rows) < need: bad.append(f"{c}: {len(rows)} title variants (want >= {need} in ## Tytuły)"); continue
            bad += [f"{c} {r['variant']}: {len(r['title'])} characters" for r in rows if len(r["title"]) > title_check.MAX_LEN]
            if not any(re.search(r"\+.+=", r["title"]) for r in rows): self.warns.append(("out.short_titles", f"{c}: no variant \"<tool> + <thing> = <result>\""))
        return not bad, "; ".join(bad[:6]) or "every short has A/B titles"

    def long_film(self) -> Film | None:
        """the long as film_check reads it before the render (plan_long.json + its EDL), None when not there"""
        p = self.work / "plan_long.json"
        if not p.exists(): return None
        try: return Film(self.work, "long")
        except SystemExit: return None

    def long_md(self) -> str:
        p = self.out / "youtube" / "long.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def chapters_match(self, near: float = 3.0, max_len: int = 60):
        """L1 (Huberman, KO, GI): the description's chapters are the film's chap cards: same count (a 0:00 intro row
        allowed), each card's text in a chapter title starting within 3 s of the card. WARN: a title > 60 characters or
        one that starts with a call to action"""
        f, md = self.long_film(), self.long_md()
        if f is None or not md: return False, "no plan_long.json / out/youtube/long.md"
        desc = md[md.find("Rozdziały:"):] if "Rozdziały:" in md else ""
        rows = [(desc_check.seconds(m), md_line.split(None, 1)[1].strip() if len(md_line.split(None, 1)) > 1 else "")
                for md_line in desc.splitlines() if (m := desc_check.CHAPTER.match(md_line))]
        chaps = sorted((o["at"], chap_text(f.specs[o["id"]])) for o in f.ovs if f.typ(o) == "chap")
        if not rows: return False, "no Rozdziały: block"
        body = [r for r in rows if r[0] > 0] if len(rows) == len(chaps) + 1 else rows
        bad = [f"{len(rows)} chapters vs {len(chaps)} chap cards"] if len(body) != len(chaps) else []
        for (at, text), (t, title) in zip(chaps, body, strict=False):
            if abs(at - t) > near: bad.append(f"chapter {title!r} at {t} s, its card at {at:.0f} s")
            if norm_word(text)[:12] not in norm_word(title): bad.append(f"chapter {title!r} is not the card text {text!r}")
        for _, title in rows:
            if len(title) > max_len: self.warns.append(("out.chapters", f"chapter {title!r}: {len(title)} characters > {max_len}"))
            if re.match(r"(?i)(subskrybuj|kliknij|zapisz|sprawdź|zobacz|obserwuj)\b", title): self.warns.append(("out.chapters", f"chapter {title!r} starts with a call to action"))
        return not bad, "; ".join(bad[:6]) or f"{len(chaps)} chapters = chap cards"

    def resources_given(self):
        """L19 (Nate Herk): when the long says "w opisie" / "do opisu", long.md has `## Zasoby` or `## Prompty` with a link or code"""
        f, md = self.long_film(), self.long_md()
        if f is None or not md: return False, "no plan_long.json / out/youtube/long.md"
        said = " ".join(w.lower() for _, w in f.film_words())
        if not re.search(r"\b(w|do) opisu\b|\bw opisie\b", said): return True, "the film promises nothing in the description"
        sec = desc_check.section(md, "Zasoby") or desc_check.section(md, "Prompty") or ""
        ok = bool(re.search(r"https?://|```", sec))
        return ok, "## Zasoby with a link or code" if ok else 'the film says "w opisie": long.md needs ## Zasoby / ## Prompty with a link or code'

    def sources_listed(self):
        """L20: every verified claim of the long (plan_long.json "verified_claims") has a source URL in plan "sources"
        {id: url} and that URL is in long.md `## Źródła`"""
        f, md = self.long_film(), self.long_md()
        if f is None or not md: return False, "no plan_long.json / out/youtube/long.md"
        claims = [c for c in f.plan.get("verified_claims", []) if any(o["id"] == c for o in f.ovs)]
        if not claims: return True, "no verified claims on screen"
        src, sec = f.plan.get("sources") or {}, desc_check.section(md, "Źródła") or ""
        bad = [c for c in claims if not (isinstance(src.get(c), str) and src[c].startswith("http") and src[c] in sec)]
        return not bad, f"claims without a source in ## Źródła: {', '.join(bad[:6])}" if bad else f"{len(claims)} claims sourced"

    def long_words(self) -> Path | None:
        """the long's whisper words file (plan_long.json "words"), None when it is not named or missing"""
        plan = self.work / "plan_long.json"
        words = load(plan, "plan_long.json").get("words") if plan.exists() else None
        return self.work / words if words and (self.work / words).exists() else None

    def out_posts(self):
        want = self.made("posts.json")
        if not want: return False, "posts.json has no post with \"make\": true (social role)"
        wf = self.long_words()  # numbers in a post must be said in the film (PLAN 4.2), blocking: no words file = FAIL, as out.article
        bad = [] if wf else ['numbers in the posts cannot be checked: plan_long.json names no "words" file that exists']
        for pid in want:
            d = self.out / "posts" / pid
            if not (d / "post.md").exists(): bad.append(f"{pid}: no post.md")
            bad += [f"{pid}: {p}" for p in post_check.problems(d, wf)]
            self.warns += [("out.posts", f"{pid}: {w}") for w in post_check.warnings(d)]  # the graphic alone (OCR, contrast) and the text habits
        bad += self.publish_days(want)
        return not bad, "; ".join(bad)

    def publish_days(self, want: list[str]) -> list[str]:
        """round 2 LI6 (PLAN 4.5): one post a day, so each made post has its own "publish_day" (day after the long's
        premiere, 0 = that day) in posts.json; a missing day is a WARN, two posts on one day fail"""
        items = {i.get("id"): i for i in load(self.work / "posts.json", "posts.json").get("items", []) if isinstance(i, dict)}
        days: dict[int, list[str]] = {}
        bad = []
        for pid in want:
            day = items.get(pid, {}).get("publish_day")
            if day is None: self.warns.append(("out.posts", f"{pid}: no publish_day in posts.json (one post a day, the film spread over >= 5 days)"))
            elif isinstance(day, bool) or not isinstance(day, int) or day < 0: bad.append(f"{pid}: publish_day {day!r} is not a whole number of days >= 0")
            else: days.setdefault(day, []).append(pid)
        return bad + [f"publish_day {d}: {', '.join(p)} (one post a day)" for d, p in days.items() if len(p) > 1]

    def out_article(self):
        """the blog article for kamiljan.com (team/roles/artykul.md): out/blog/<slug>/article.json passes article_check, numbers
        checked against the long's words (plan_long.json "words"; without them the item fails)"""
        arts = sorted((self.out / "blog").glob("*/article.json"))
        if not arts: return False, "no out/blog/<slug>/article.json (artykul role)"
        wf = self.long_words()
        if wf is None: return False, 'numbers in the article cannot be checked: plan_long.json names no "words" file that exists'
        bad = [f"{a.parent.name}: {p}" for a in arts for p in article_check.problems(a.parent, wf)]
        # a YouTube thumbnail sells a click in the feed; on the blog its words mean nothing (Kamil 2026-11-08, cover
        # "18% LECI NA SLEPO": "bardzo bez sensu i zdjecie i tekst na bloga"): the cover is made for the article
        thumbs = {f.read_bytes() for f in (self.out / "thumbnails").glob("*") if f.is_file()} if (self.out / "thumbnails").is_dir() else set()
        for a in arts:
            cov = a.parent / str((load(a, a.name).get("cover") or {}).get("src", ""))
            if cov.is_file() and cov.read_bytes() in thumbs: bad.append(f"{a.parent.name}: the cover is a copy of a YouTube thumbnail (make one for the article)")
        self.warns += [("out.article", f"{a.parent.name}: {w}") for a in arts for w in article_check.warnings(a.parent)]
        return not bad, "; ".join(bad[:8])


    def out_instagram(self):
        """the Instagram form (team/roles/social.md): out/instagram/<post>/ carousels + reels/<short>.json pass ig_check,
        numbers checked against the long's words (without them the item fails, as out.posts)"""
        wf = self.long_words()
        if wf is None: return False, 'numbers in the Instagram captions cannot be checked: plan_long.json names no "words" file that exists'
        bad, warn = ig_check.check(self.out / "instagram", wf)
        self.warns += [("out.instagram", w) for w in warn]
        return not bad, "; ".join(bad[:8])

FRAGMENT_TAG = "fragment test, whole-film item:"


def fragment_of(work: Path) -> dict | None:
    """the FRAGMENT.json fragment.py wrote in this work folder ({src_work, from_word, to_word, ...}); None for a film"""
    p = work / "FRAGMENT.json"
    if not p.is_file(): return None
    try: rec = json.loads(p.read_text())
    except ValueError: return None
    ok = isinstance(rec, dict) and isinstance(rec.get("src_work"), str) and all(
        isinstance(rec.get(k), int) and not isinstance(rec.get(k), bool) for k in ("from_word", "to_word"))
    return rec if ok else None


def talk(obj) -> bool:
    """two people (kind.is_talk: the plan's "podcast" key, else content_kind.json in the work folder)"""
    work = getattr(obj, "work", None)
    return content_kind.is_talk(obj.plan, work) if work is not None else bool(content_kind.from_plan(obj.plan))


def judge(obj, item: dict) -> tuple[str, str]:
    skip = (obj.plan.get("skip") or {}).get(item["id"])
    # "no_skip": an item that is itself a list of reasons (the capability map) has no off switch: one sentence on
    # long.capabilities waived every required feature at once (pg-review 2026-11-09 code-1); its "no_skip" says what to do
    if item.get("no_skip") and skip is not None: return "FAIL", f'"skip": {{"{item["id"]}": ...}} is not allowed: {item["no_skip"]}'
    if isinstance(skip, str) and len(skip.strip()) >= SKIP_MIN: return "SKIP", skip.strip()
    # "podcast": a conversation of two people (plan "podcast", ADR-0031) is not a solo explainer: {"off": why} = not
    # asked there, {"value": x, "why": ...} = its own threshold (Kamil 2026-11-22: minimal graphics, no drawings)
    pod = item.get("podcast") if talk(obj) else None
    if isinstance(pod, dict) and isinstance(pod.get("off"), str): return "SKIP", f"podcast: {pod['off']}"
    if isinstance(pod, dict) and "value" in pod: item = {**item, "value": pod["value"]}
    fn = getattr(obj, item["metric"], None)
    if fn is None: raise SystemExit(f"film_check: style/checklist.json {item['id']}: unknown metric {item['metric']!r}")
    args = item.get("args", {})  # "args": the metric's own parameters, data like the value
    if not isinstance(args, dict): raise SystemExit(f"film_check: style/checklist.json {item['id']}: \"args\" = an object, got {args!r}")
    try: inspect.signature(fn).bind(**args)  # only the binding: a TypeError inside the metric stays a real traceback
    except TypeError as e: raise SystemExit(f"film_check: style/checklist.json {item['id']}: \"args\" {args!r} do not fit {item['metric']}: {e}") from e
    v = fn(**args)
    detail = ""
    if isinstance(v, tuple): v, detail = v
    op, want = item["op"], item.get("value")
    if op == "true" or want == "all": ok = bool(v)
    elif op == ">=": ok = v >= want
    elif op == "<=": ok = v <= want
    elif op == "==": ok = v == want
    else: raise SystemExit(f"film_check: {item['id']}: op {op!r}")
    shown = detail or (f"{v} {op} {want}" if op not in ("true",) and want != "all" else "")
    # a fragment test (fragment.py, long-lite phase 7) is a few minutes of a long: a count or a place over the whole film
    # (memes >= 3, the name card, the mid CTA, the recap at the end) cannot hold there; it is shown with FRAGMENT_TAG (the
    # report row says "fragment": true, research_gate --report reads that), every other item still fails (Kamil 2026-11-14
    # "chce normalnie dla paru minut tak zeby byl caly proces"). accept.py never accepts a fragment as the long
    if not ok and item.get("whole_film") and fragment_of(obj.work): return "WARN", f"{FRAGMENT_TAG} {shown or f'{v} {op} {want}'}"
    if not ok and item.get("level") == "warn": return "WARN", f"{v} {op} {want}: {shown}"  # observe: advice until the evidence holds
    return ("OK" if ok else "FAIL"), shown


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--json"]; as_json = "--json" in argv
    if len(args) < 2: print(__doc__, file=sys.stderr); return 2
    phase = None
    if "--phase" in args:  # items with a "phase" run only when asked (run_v4.sh: "behind" right after behind.py)
        i = args.index("--phase")
        if i + 1 >= len(args): print("film_check: --phase needs a name", file=sys.stderr); return 2
        phase = args[i + 1]; del args[i:i + 2]
    work = Path(args[0])
    every = load(CHECKLIST, "style/checklist.json")["items"]
    items = [x for x in every if x.get("phase") == phase]
    if phase is not None and not items:  # a typo must not pass a gate with nothing checked
        known = sorted({x["phase"] for x in every if x.get("phase")})
        print(f"film_check: no items with phase {phase!r} in style/checklist.json (known: {', '.join(known) or 'none'})", file=sys.stderr)
        return 2
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args): print("film_check: --out needs a folder", file=sys.stderr); return 2
        targets = [("out", Out(work, Path(args[i + 1])))]
    else:
        targets = [(f, Film(work, f)) for f in args[1:]]
    report, failed = [], 0
    for name, obj in targets:
        fmt = obj.fmt if isinstance(obj, Film) else "out"
        for it in (x for x in items if x["fmt"] == fmt):
            seen = len(getattr(obj, "warns", []))
            st, detail = judge(obj, it)
            failed += st == "FAIL"
            report.append({"film": name, "id": it["id"], "status": st, "detail": detail, "why": it["why"],
                           "fragment": st == "WARN" and detail.startswith(FRAGMENT_TAG),
                           "warnings": [w for _, w in getattr(obj, "warns", [])[seen:]]})  # the checker's own advice for this item
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for r in report:
            print(f"{r['status']:4} {r['film']:<22} {r['id']:<22} {r['detail']}" + (f"\n       why: {r['why']}" if r["status"] == "FAIL" else ""))
            for w in r["warnings"]: print(f"WARN {r['film']:<22} {r['id']:<22} {w}")
        print(f"film_check: {failed} missing" if failed else "film_check: all items met or skipped with a reason")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
