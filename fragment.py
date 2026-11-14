#!/usr/bin/env python3
"""fragment.py SRC_WORK DST_WORK --from-word A --to-word B — a FRAGMENT of a long's edit as its own work folder.

Phase 7 of docs/designs/2026-11-10-long-lite-steps.md (Kamil 2026-11-14 "mial byc render kawalka zeby widziec realnie czy
dzialaja logiki zeby pelny zrobic?"): the long pipeline (build_edl -> gfx -> behind -> dry run -> final) is tried on ~3 min
of a real long before the whole long is rendered. The fragment is cut out of the long's plan, not re-edited: the same
recording, transcript and card designs, only the time window is smaller, so a failure is the system's, not a new edit's.

Window = the long's keeps in PLAY order from the keep holding word A to the keep holding word B, clipped to A..B (a clipped
edge loses its measured t0/t1: that time belongs to the word that is no longer the edge). Everything tied to a word (gfx,
emph, beats, list item_words, story parts) stays only when its word is kept; the end card ("word": "END") stays.
music_moods are film seconds: shifted by the long's film time of the window start (from the long's EDL), the mood playing
there starts the fragment. The recording's files (words, silences, wav, video) are linked, never copied or changed.
Writes DST_WORK/FRAGMENT.json {src_work, from_word, to_word, plan_sha256, keeps, gfx} so the fragment says where it came from.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import timeline

# recording inputs next to the words file (word_times.py, edges.py, words_check.py read them by stem): linked when present
STEM_FILES = (".cw.json", ".dtw.cw.json", ".lines.txt", ".sil", ".wav", ".crop.mp4")
# the edit's notes the checks read (film_check: story.json parts, content_review_<film>.json, claims for research)
COPY_FILES = ("claims.json", "content_review_long.json")


def word_in(keeps: list, w) -> bool:
    return isinstance(w, int) and not isinstance(w, bool) and any(k[0] <= w <= k[1] for k in keeps)


def cut_keeps(keeps: list, a: int, b: int) -> list:
    """the keeps from the one holding word a to the one holding word b (play order), clipped to a..b"""
    pos = [i for i, k in enumerate(keeps) if k[0] <= a <= k[1]], [i for i, k in enumerate(keeps) if k[0] <= b <= k[1]]
    if not pos[0]: sys.exit(f"fragment: word {a} is in no keep of the plan")
    if not pos[1]: sys.exit(f"fragment: word {b} is in no keep of the plan")
    i, j = pos[0][0], pos[1][0]
    if j < i: sys.exit(f"fragment: word {b} plays before word {a}")
    out = []
    for k in keeps[i:j + 1]:
        o = dict(k[2]) if len(k) > 2 else {}
        lo, hi = k[0], k[1]
        if k is keeps[i] and a > lo: lo = a; o.pop("t0", None)
        if k is keeps[j] and b < hi: hi = b; o.pop("t1", None)
        out.append([lo, hi, o] if o else [lo, hi])
    return out


def shift_moods(moods: list, t0: float, t1: float) -> list:
    """[[film s, mood], ...] of the long -> the fragment's: the mood playing at t0 at 0, the changes up to t1 shifted"""
    if not moods: return moods
    cur = [m for m in moods if m[0] <= t0]
    out = [[0, (cur[-1] if cur else moods[0])[1]]]
    out += [[round(m[0] - t0, 2), m[1]] for m in moods if t0 < m[0] < t1]
    return out


def with_extends(specs: dict, ids: set) -> set:
    """a scene that "extends" another needs that one's spec too"""
    need, todo = set(ids), list(ids)
    while todo:
        e = specs.get(todo.pop(), {}).get("extends")
        if isinstance(e, str) and e in specs and e not in need: need.add(e); todo.append(e)
    return need


def cut_plan(plan: dict, specs: list, story: dict | None, edl: dict, words: list, a: int, b: int):
    """-> (plan, specs, story) of the fragment; words = [(from s, to s), ...] of the recording"""
    keeps = cut_keeps(plan["keeps"], a, b)
    p = dict(plan)
    p["keeps"] = keeps
    p["gfx"] = [g for g in plan.get("gfx", []) if (g.get("word") == "END" or word_in(keeps, g.get("word")))
                and all(word_in(keeps, w) for w in g.get("item_words", []))]
    for key in ("emph", "beats"):
        if key in plan: p[key] = [e for e in plan[key] if word_in(keeps, e.get("word"))]
    ids = {g["id"] for g in p["gfx"]}
    if isinstance(plan.get("meme_review"), dict): p["meme_review"] = {k: v for k, v in plan["meme_review"].items() if k in ids}
    if isinstance(plan.get("verified_claims"), list): p["verified_claims"] = [c for c in plan["verified_claims"] if c in ids]
    if isinstance(plan.get("sources"), dict): p["sources"] = {k: v for k, v in plan["sources"].items() if k in ids}
    if plan.get("music_moods"):
        ex = bool(edl.get("seg_exact"))
        t0 = timeline.src2out(words[keeps[0][0]][0], edl["segments"], ex)
        t1 = timeline.src2out(words[keeps[-1][1]][1], edl["segments"], ex)
        p["music_moods"] = shift_moods(plan["music_moods"], t0, t1)
    p.setdefault("notes", [])
    p["notes"] = list(p["notes"]) + [f"fragment.py: words {a}-{b} of the long, {len(keeps)} keeps, {len(p['gfx'])} cards"]
    by_id = {s["id"]: s for s in specs}
    keep_ids = with_extends(by_id, ids)
    sp = [s for s in specs if s["id"] in keep_ids]
    st = None
    if isinstance(story, dict):
        st = dict(story)
        st["parts"] = [pt for pt in story.get("parts", []) if word_in(keeps, pt.get("start_word"))]
        if "beats" in story: st["beats"] = [e for e in story["beats"] if word_in(keeps, e.get("word"))]
    return p, sp, st


def link(src: Path, dst: Path):
    if dst.exists() or dst.is_symlink(): return
    dst.symlink_to(src.resolve())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="a fragment of a long's edit as its own work folder")
    ap.add_argument("src_work"); ap.add_argument("dst_work")
    ap.add_argument("--from-word", type=int, required=True); ap.add_argument("--to-word", type=int, required=True)
    ap.add_argument("--film", default="long")
    x = ap.parse_args(argv)
    src, dst = Path(x.src_work), Path(x.dst_work)
    if x.to_word < x.from_word: sys.exit("fragment: --to-word before --from-word")
    plan_p = src / f"plan_{x.film}.json"
    plan = json.loads(plan_p.read_text())
    edl = json.loads((src / plan.get("edl_out", f"edl_{x.film}.json")).read_text())
    specs = json.loads((src / plan["gfx_specs"]).read_text()) if plan.get("gfx_specs") else []
    story = json.loads((src / "story.json").read_text()) if (src / "story.json").exists() else None
    words = [(w["offsets"]["from"] / 1000, w["offsets"]["to"] / 1000) for w in json.loads((src / plan["words"]).read_text())["transcription"]]
    p, sp, st = cut_plan(plan, specs, story, edl, words, x.from_word, x.to_word)
    if dst.exists() and any(dst.iterdir()): sys.exit(f"fragment: {dst} is not empty (a fragment starts from zero)")
    dst.mkdir(parents=True, exist_ok=True)
    stem = str(plan["words"]).removesuffix(".cw.json")
    for suf in STEM_FILES:
        if (src / (stem + suf)).exists(): link(src / (stem + suf), dst / (stem + suf))
    for f in COPY_FILES:
        if (src / f).exists(): (dst / f).write_bytes((src / f).read_bytes())
    if (src / "sources").is_dir(): link(src / "sources", dst / "sources")
    (dst / plan_p.name).write_text(json.dumps(p, ensure_ascii=False, indent=1))
    if plan.get("gfx_specs"): (dst / plan["gfx_specs"]).write_text(json.dumps(sp, ensure_ascii=False, indent=1))
    if st is not None: (dst / "story.json").write_text(json.dumps(st, ensure_ascii=False, indent=1))
    rec = {"src_work": str(src.resolve()), "from_word": x.from_word, "to_word": x.to_word,
           "plan_sha256": hashlib.sha256(plan_p.read_bytes()).hexdigest(), "keeps": len(p["keeps"]), "gfx": [g["id"] for g in p["gfx"]]}
    (dst / "FRAGMENT.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"fragment: {dst} words {x.from_word}-{x.to_word}: {len(p['keeps'])} keeps, {len(p['gfx'])} cards, {len(sp)} specs, "
          f"{len(p.get('music_moods') or [])} moods, {len((st or {}).get('parts', []))} story parts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
