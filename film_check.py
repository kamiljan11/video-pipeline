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

import json
import re
import sys
from pathlib import Path
from typing import NoReturn

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


def max_gap(edl: dict, end: float) -> float:
    """longest stretch of the film with no card on screen, no punch-in, no b-roll and no framing jump"""
    spans = [(o["at"], o["at"] + o["dur"]) for o in edl.get("overlays", [])]
    spans += [(b["at"], b["at"] + b.get("dur", 0)) for b in edl.get("broll", []) if "at" in b]
    spans += [(t, t) for t in punches(edl) + zoom_steps(edl)]
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
    def hook_text(self):  # the hook line from the plan (ASS) or a card on screen from the first half second
        return bool(str(self.plan.get("hook_text", "")).strip()) or any(o["at"] <= 0.5 for o in self.ovs)
    def first_overlay_at(self): return 0.0 if self.hook_text() else round(min((o["at"] for o in self.ovs), default=self.len), 2)
    def caption_pop(self): return self.plan.get("caption_pop") is True

    def layout_cards(self):
        return sum(1 for o in self.ovs if o.get("split") or o.get("corner") or self.typ(o) in ("web", "meme")
                   or self.specs.get(o["id"], {}).get("layout") in ("split", "corner", "full"))


class Out:
    def __init__(self, work: Path, out: Path):
        self.work, self.out = work, out
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
        p = self.out / "youtube" / "long.md"
        if not p.exists(): return False, "no out/youtube/long.md"
        t = p.read_text()
        need = [h for h in ("## Tytuły", "## Opis", "## Rozdziały", "## Tagi") if h not in t]
        titles = len(re.findall(r"^\| *[ABC] *\|", t, re.MULTILINE))
        chap = re.findall(r"^(\d+:\d\d) ", t, re.MULTILINE)
        bad = need + ([f"{titles} titles (want A, B, C rows)"] if titles < 3 else []) \
            + (["chapters must start at 0:00 and have at least 3 rows"] if len(chap) < 3 or chap[0] != "0:00" else [])
        miss = [c for c in self.made("clips.json") if not (self.out / "youtube" / "shorts" / f"{c}.md").exists()]
        bad += [f"no out/youtube/shorts/{c}.md" for c in miss]
        return not bad, "; ".join(bad)

    def out_thumbnails(self):
        d = self.out / "thumbnails"
        # one variant = long_<id>.jpg; thumbs.mjs also writes long_<id>_2560.png, which must not count as a second variant
        longs = {f.stem.removeprefix("long_") for f in d.glob("long_*.*") if f.suffix in (".jpg", ".png") and not f.stem.endswith("_2560")}
        miss = [c for c in self.made("clips.json") if not list(d.glob(f"{c}_cover.*"))]
        bad = ([f"{len(longs)} long thumbnail variants (want >= 2 for an A/B test)"] if len(longs) < 2 else []) + [f"no cover for {c}" for c in miss]
        return not bad, "; ".join(bad)

    def out_posts(self):
        want = self.made("posts.json")
        if not want: return False, "posts.json has no post with \"make\": true (social role)"
        bad = []
        for pid in want:
            d = self.out / "posts" / pid
            if not (d / "post.md").exists(): bad.append(f"{pid}: no post.md")
            if not [f for f in d.glob("*") if f.suffix in (".png", ".jpg", ".pdf")]: bad.append(f"{pid}: no graphic (png/jpg/pdf)")
        return not bad, "; ".join(bad)


def judge(obj, item: dict) -> tuple[str, str]:
    skip = (obj.plan.get("skip") or {}).get(item["id"])
    if isinstance(skip, str) and len(skip.strip()) >= SKIP_MIN: return "SKIP", skip.strip()
    fn = getattr(obj, item["metric"], None)
    if fn is None: raise SystemExit(f"film_check: style/checklist.json {item['id']}: unknown metric {item['metric']!r}")
    v = fn(); detail = ""
    if isinstance(v, tuple): v, detail = v
    op, want = item["op"], item.get("value")
    if op == "true" or want == "all": ok = bool(v)
    elif op == ">=": ok = v >= want
    elif op == "<=": ok = v <= want
    elif op == "==": ok = v == want
    else: raise SystemExit(f"film_check: {item['id']}: op {op!r}")
    shown = detail or (f"{v} {op} {want}" if op not in ("true",) and want != "all" else "")
    return ("OK" if ok else "FAIL"), shown


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--json"]; as_json = "--json" in argv
    if len(args) < 2: print(__doc__, file=sys.stderr); return 2
    work = Path(args[0])
    items = load(CHECKLIST, "style/checklist.json")["items"]
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
            st, detail = judge(obj, it)
            failed += st == "FAIL"
            report.append({"film": name, "id": it["id"], "status": st, "detail": detail, "why": it["why"]})
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for r in report:
            print(f"{r['status']:4} {r['film']:<22} {r['id']:<22} {r['detail']}" + (f"\n       why: {r['why']}" if r["status"] == "FAIL" else ""))
        print(f"film_check: {failed} missing" if failed else "film_check: all items met or skipped with a reason")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
