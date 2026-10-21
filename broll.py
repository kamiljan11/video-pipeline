#!/usr/bin/env python3
"""broll.py plan.json [--json proposal.json] [--credits]  — stock b-roll where the speaker names a concrete thing.

A kept word matching a topic of style/grammar.json broll.topics (regex on that one lowercased word -> English stock
query) gets broll.<format>.dur s of matching footage starting on that word, unless the place is taken: before
not_before s (hook title), inside a sentence holding a moment of an avoid type (hook, confession, cta, number card...:
the face carries it), on a word whose clip the editor removed (plan["broll_rejected"]), under a graphic, closer than min_gap s to another b-roll, over max_share of the film, or the
query was used per_topic times. Clips come from stock.py (free provider, key from Infisical) and are cached in
render/broll/ (shared by every project). Output times come from the film's current EDL (plan["edl_out"]: recompute
the film first); build_edl.py places the clips again from the anchor word (place()) and drops any that collide with a
graphic, sit on a cut word or point outside render/broll/.
--json out: proposal {"broll": [...merged with the plan's...], "new", "skipped", "credits"}; the plan is not written
(the editing panel applies it through its history). No --json: prints the proposal. --credits: the plan's credits."""
import json
import os
import re
import sys
from pathlib import Path

import stock
from beatfx import load_grammar
from beats import kept_order, load_words, sentences

HERE = os.path.dirname(os.path.realpath(__file__))  # = the panel's BROLL_DIR (resolved path)
CACHE = os.environ.get("VP_BROLL_DIR") or os.path.join(HERE, "render", "broll")  # env: tests only (plans cannot set it)
FRAME = {"short": ("portrait", 1080, 1920), "long": ("landscape", 1920, 1080)}


def src2out(segments, t):
    """Output time of source time t (same rule as build_edl.py: a cut moment maps to the next kept frame)."""
    acc = 0.0
    for s in segments:
        if t < s["in"]:
            return acc
        if t <= s["out"]:
            return acc + t - s["in"]
        acc += s["out"] - s["in"]
    return acc


def topic_of(word, topics):
    w = re.sub(r"[^\w-]", "", word.lower())
    return next((q for rx, q in topics if w and re.search(rx, w)), None)


def blocked(plan, W, edl, cfg, grammar):
    """Output intervals where no b-roll may start or run: graphics, sentences of avoided moments, the hook band."""
    segs = edl["segments"]
    out = [(0.0, cfg["not_before"])]
    out += [(o["at"] - 0.3, o["at"] + o["dur"] + 0.3) for o in edl.get("overlays", [])]
    avoid = {b["word"] for b in plan.get("beats", []) if b.get("type") in cfg.get("avoid", []) and not b.get("off")}
    for sent in sentences(plan, W, grammar["detect"]["max_sentence"]):
        if avoid & set(sent):
            out.append((src2out(segs, W[sent[0]][0]), src2out(segs, W[sent[-1]][1])))
    return out


def clash(a, b, spans):
    return any(a < y and b > x for x, y in spans)


def propose(plan, W, edl, grammar, find=stock.search, fetch=stock.fetch, cache=CACHE):
    fmt = "short" if plan.get("vertical") else "long"
    br = grammar.get("broll") or {}
    cfg = br.get(fmt)
    got = plan.get("broll")  # plans arrive via Syncthing: an item without an int word cannot be placed (place() skips it)
    old = [b for b in got if isinstance(b, dict) and type(b.get("word")) is int and 0 <= b["word"] < len(W)] if isinstance(got, list) else []
    if not cfg:
        return {"broll": old, "new": 0, "skipped": [], "credits": credits(old), "format": fmt, "error": None}
    segs = edl["segments"]
    total = sum(s["out"] - s["in"] for s in segs)
    spans = blocked(plan, W, edl, cfg, grammar)
    placed = [src2out(segs, W[b["word"]][0]) + (b["lead"] if _num(b.get("lead"), -5, 5) else 0.0) for b in old]
    got = plan.get("broll_rejected")
    rejected = [r for r in got if isinstance(r, dict)] if isinstance(got, list) else []  # removed by the editor: never again
    used_ids = {(b.get("provider"), b.get("id")) for b in old + rejected}
    no_words = {r.get("word") for r in rejected}
    per_q, dead_q = {}, set()  # dead_q: no clip or a failed search/download this run; never asked again (limit 200/h)
    for b in old:
        per_q[b.get("query")] = per_q.get(b.get("query"), 0) + 1
    share = sum(b.get("dur", 0) for b in old)
    orientation, mw, mh = FRAME[fmt]
    new, skipped = [], []
    for i in kept_order(plan):
        q = topic_of(W[i][2], br["topics"])
        if not q or i in no_words or q in dead_q:
            continue
        t = src2out(segs, W[i][0]) + cfg["lead"]
        a, b = t, t + cfg["dur"]
        said = W[i][2].strip()
        if b > total or clash(a, b, spans) or any(abs(a - p) < cfg["min_gap"] + cfg["dur"] for p in placed):
            continue  # place taken: quietly, most matches are
        if per_q.get(q, 0) >= cfg["per_topic"]:
            continue
        if share + cfg["dur"] > cfg["max_share"] * total:
            skipped.append({"word": i, "said": said, "reason": "limit udziału b-rollu w filmie"})
            break
        try:
            clips = [c for c in find(br["provider"], q, orientation, mw, mh, cfg["dur"] + 0.5) if (c.provider, c.id) not in used_ids]
            if not clips:
                skipped.append({"word": i, "said": said, "reason": f"brak klipu dla „{q}”"})
                dead_q.add(q)
                continue
            c = clips[0]
            path = fetch(c, cache)
        except stock.ProviderDown as e:
            skipped.append({"word": i, "said": said, "reason": str(e), "down": True})
            break  # no network / bad key / limit: the next words would only repeat it
        except stock.StockError as e:
            skipped.append({"word": i, "said": said, "reason": str(e)})
            dead_q.add(q)
            continue
        item = {"word": i, "dur": cfg["dur"], "lead": cfg["lead"], "query": q, "said": said, "file": path,
                "clip_dur": c.duration, "provider": c.provider, "id": c.id, "author": c.author, "url": c.page}
        new.append(item)
        placed.append(a)
        used_ids.add((c.provider, c.id))
        per_q[q] = per_q.get(q, 0) + 1
        share += cfg["dur"]
    merged = sorted(old + new, key=lambda b: b["word"])
    down = next((s["reason"] for s in skipped if s.get("down")), None)
    return {"broll": merged, "new": len(new), "skipped": skipped, "credits": credits(merged), "format": fmt, "error": down}


def _num(x, lo, hi):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and lo <= x <= hi


def _slot(b, W, segments, total, spans, end, root):
    """(at, dur, real file) of one plan item in output time, or the reason it cannot be placed (Polish, for the UI)."""
    file, dur, lead = b.get("file"), b.get("dur", 2.5), b.get("lead", 0.0)
    real = os.path.realpath(file) if isinstance(file, str) else ""
    if not _num(dur, 0.5, 8.0) or not _num(lead, -1.0, 3.0):
        return "zły czas b-rollu"
    if os.path.dirname(real) != root or not real.endswith(".mp4") or not os.path.isfile(real):
        return "brak pliku b-rollu w render/broll"
    t = W[b["word"]][0]
    if not any(s["in"] <= t <= s["out"] for s in segments):
        return "słowo wycięte"
    at = max(0.0, src2out(segments, t) + lead)
    d = min(at + dur, total) - at
    if d < 0.5:
        return "za blisko końca filmu"
    if clash(at, at + d, spans):
        return "pod grafiką"
    if at < end:
        return "nachodzi na poprzedni b-roll"
    return at, d, real


def place(items, W, segments, overlays, cache=CACHE):
    """EDL entries for the plan's b-roll (build_edl.py, key "broll"): [{file, at, dur, ss, word, query, id}], skipped.
    A clip starts on its anchor word (+lead) in output time, is cut at the film's end, skips its first second when the
    clip is long enough (stock clips often fade in) and is dropped when the word was cut, it would overlap a graphic
    (+-0.3 s) or the previous clip, or its file is not a cached clip (plans arrive through Syncthing: no other paths)."""
    root = os.path.realpath(cache)
    total = sum(s["out"] - s["in"] for s in segments)
    spans = [(o["at"] - 0.3, o["at"] + o["dur"] + 0.3) for o in overlays]
    out, skipped, end = [], [], -1.0
    good = [b for b in items if isinstance(b, dict) and isinstance(b.get("word"), int) and not isinstance(b["word"], bool)
            and 0 <= b["word"] < len(W)]
    skipped += [{"word": b.get("word") if isinstance(b, dict) else None, "reason": "zły wpis b-rollu"} for b in items if b not in good]
    for b in sorted(good, key=lambda b: b["word"]):
        got = _slot(b, W, segments, total, spans, end, root)
        if isinstance(got, str):
            skipped.append({"word": b["word"], "said": W[b["word"]][2].strip()[:60], "reason": got})
            continue
        at, d, real = got
        clip = b.get("clip_dur")
        ss = 1.0 if isinstance(clip, (int, float)) and clip >= d + 1.5 else 0.0
        out.append({"file": real, "at": round(at, 3), "dur": round(d, 3), "ss": ss, "word": b["word"],
                    "query": str(b.get("query", ""))[:100], "id": f"broll_{b['word']}"})
        end = at + d
    return out, skipped


def credits(items):
    """Lines for the video description (the licence does not require them; the provider asks for them)."""
    seen, out = set(), []
    for b in items:
        key = (b.get("provider"), b.get("id"))
        if key in seen:
            continue
        seen.add(key)
        out.append(f"B-roll: {str(b.get('provider', '')).capitalize()} — {b.get('author') or 'autor nieznany'} ({b.get('url', '')})")
    return out


def main(argv):
    if not argv or argv[0].startswith("-"):
        sys.exit(__doc__)
    plan = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    if "--credits" in argv:
        print("\n".join(credits(plan.get("broll", []))) or "(brak b-rollu w planie)")
        return
    edl_p = plan.get("edl_out")
    if not edl_p or not os.path.exists(edl_p):
        sys.exit("brak EDL filmu: najpierw przelicz film (build_edl.py)")
    edl = json.loads(Path(edl_p).read_text(encoding="utf-8"))
    prop = propose(plan, load_words(plan), edl, load_grammar())
    for b in prop["broll"]:
        print(f"broll word {b['word']} „{b.get('said', '')}” -> {b.get('query')} ({b.get('provider')} {b.get('id')})")
    for s in prop["skipped"]:
        print(f"skipped word {s['word']} „{s['said']}”: {s['reason']}")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(prop, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
