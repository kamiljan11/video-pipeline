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

import inspect
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import article_check  # the kamiljan.com blog article made from the film
import count_check  # the count he says is the count on the card
import desc_check  # the YouTube descriptions (round 2 Y0-Y5, S2-S3)
import gfx_types  # next to this script: which card types are a separate screen
import hook_check  # the 6 hook killers
import ig_check  # the Instagram carousels and Reel captions (round 2 IG1-IG6)
import post_check  # the LinkedIn post graphic alone (OCR) and the text habits
import thumb_check  # the long thumbnails as the feed shows them
import title_check  # the A/B/C titles of the long

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
TEXT_SKIP_KEYS = {"id", "type", "file", "icon", "bg", "tone", "anim", "k", "src", "url", "photo", "layout", "who", "mark", "head", "font"}


def says_nothing(title: str, sub: str) -> bool:
    """one word (or none), no sub line, no digit, not a name: "Najwiecej" yes; "GitHub", "kamiljan.com", "92%" no"""
    words = re.findall(r"\w+", title)
    if len(words) > 1 or sub.strip() or re.search(r"\d", title): return False
    is_name = bool(words) and (any(c.isupper() for c in words[0][1:]) or "." in title)  # GitHub, iPhone, kamiljan.com
    return not is_name


def card_texts(spec: dict) -> list[str]:
    """every word a card shows: strings anywhere in its spec, not file names, icons, colours or timing"""
    out: list[str] = []
    def walk(v, key=""):
        if isinstance(v, str) and key not in TEXT_SKIP_KEYS: out.append(v)
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


def word_times(words_file: Path) -> list[float]:
    d = load(words_file, "words")
    return [w["offsets"]["from"] / 1000 for w in d["transcription"]]


def src2out(segments: list[dict], t: float) -> float:
    """source time -> film time; a time inside a cut maps to the start of the next kept piece"""
    acc = 0.0
    for s in segments:
        if t < s["in"]: return acc
        if t <= s["out"]: return acc + t - s["in"]
        acc += s["out"] - s["in"]
    return acc


def body_len(edl: dict) -> float:
    return sum(s["out"] - s["in"] for s in edl["segments"])


def punches(edl: dict) -> list[float]:
    """film times of punch-in zooms: an animated zoom inside a piece (build_edl emph) or an editing-grammar punch"""
    out, acc = [], 0.0
    for s in edl["segments"]:
        z = s.get("zoom")
        if isinstance(z, dict) and z.get("t0", 0) > 0.01 and z.get("b", 0) > z.get("a", 0) + 0.1:
            out.append(acc + z["t0"])
        acc += s["out"] - s["in"]
    out += [r["at"] for r in edl.get("beat_fx", []) if r.get("fx") == "punch"]
    return sorted(out)


def zoom_steps(edl: dict) -> list[float]:
    """film times where the framing jumps (a jump cut to another zoom level): a picture change too"""
    out, acc, prev = [], 0.0, None
    for s in edl["segments"]:
        z = s.get("zoom"); level = z.get("a", 1.0) if isinstance(z, dict) else float(z or 1.0)
        if prev is not None and abs(level - prev) >= 0.08: out.append(acc)
        prev = level if not isinstance(z, dict) else z.get("b", level)
        acc += s["out"] - s["in"]
    return out


NOT_READ = {"id", "type", "icon", "tone", "k", "bg", "anim", "file", "owner", "layout", "cam", "img", "src", "sfx", "font", "mark",
            "edl", "words", "behind", "hl", "acc", "theme", "logo", "url", "shot", "meme", "canvas", "side"}  # not read text


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
    if sp.get("type") in ("scene", "web", "slide"): return scene_min
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


def max_gap(edl: dict, end: float) -> float:
    """longest stretch of the film with no card on screen, no punch-in, no b-roll and no framing jump"""
    spans = cover_spans(edl) + [(t, t) for t in punches(edl) + zoom_steps(edl)]
    gap, t = 0.0, 0.0
    for a, b in sorted(spans):
        gap = max(gap, a - t); t = max(t, b)
    return round(max(gap, end - t), 1)


class Film:
    def __init__(self, work: Path, name: str):
        self.name = name
        self.plan = load(work / f"plan_{name}.json", f"plan of {name}")
        self.edl = load(work / self.plan.get("edl_out", f"edl_{name}.json"), f"EDL of {name} (run build_edl.py first)")
        self.specs = {s["id"]: s for s in load(work / self.plan["gfx_specs"], "gfx specs")} if self.plan.get("gfx_specs") else {}
        self.vertical = bool(self.plan.get("vertical"))
        self.fmt = "short" if self.vertical else "long"
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
        starts = [(pt.get("title", pt.get("id", "?")), src2out(segs, wt[pt["start_word"]])) for pt in story.get("parts", [])]
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
    def behind_cards(self): return sum(1 for o in self.ovs if "behind" in self.specs.get(o["id"], {}))

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
        others = [v for v in led.values() if isinstance(v, dict) and v.get("work") != str(self.work.resolve())]
        if not others: return True, ""
        last = max(others, key=lambda v: v.get("at", ""))
        same = (last.get("name"), last.get("key", 0)) == (pal.get("name"), pal.get("key", 0))
        return not same, f"same palette and key as the last film ({last.get('work')}, {last.get('film')})" if same else ""

    def music_moods(self): return len(self.plan.get("music_moods") or [])
    def sfx_style_v2(self): return self.plan.get("sfx_style") == "v2"
    def has_end_card(self): return any(self.typ(o) == "end" for o in self.ovs)

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
        f = self.work / f"content_review_{self.name}.json"
        ids = sorted({o["id"] for o in self.ovs if o.get("id") in self.specs})
        if not ids: return True, "no cards"
        if not f.exists(): return False, f"no {f.name}: read every card for meaning (python3 content_review.py {self.work} {self.name})"
        rev = load(f, f.name)
        bad = []
        for i in ids:
            r = rev.get(i) if isinstance(rev, dict) else None
            if not isinstance(r, dict): bad.append(f"{i} not reviewed")
            elif r.get("hash") != card_text_hash(self.specs[i]): bad.append(f"{i} changed after the review")
            elif r.get("verdict") != "ok": bad.append(f"{i} judged {r.get('verdict')!r}: {r.get('why', '')[:60]}")
            elif len(str(r.get("why", "")).strip()) < SKIP_MIN: bad.append(f"{i} ok without a reason")
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

    def first_overlay_at(self): return 0.0 if self.hook_text() else round(min((o["at"] for o in self.ovs), default=self.len), 2)
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

    def out_thumbnails(self):
        d = self.out / "thumbnails"
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
            bad, warns = thumb_check.check(load(spec, "thumbs.json"), self.out, titles, title_check.phrase(text))
            self.warns += [("out.thumbs_read", w) for w in warns]
        except (RuntimeError, OSError, ValueError, ImportError, subprocess.SubprocessError) as e:  # ffmpeg, tesseract, OpenCV
            return False, f"thumb_check failed: {e}"
        return not bad, "; ".join(bad[:8])

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

def judge(obj, item: dict) -> tuple[str, str]:
    skip = (obj.plan.get("skip") or {}).get(item["id"])
    if isinstance(skip, str) and len(skip.strip()) >= SKIP_MIN: return "SKIP", skip.strip()
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
