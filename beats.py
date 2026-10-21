#!/usr/bin/env python3
"""beats.py plan.json [--llm] [--write] [--gfx] [--grammar path] [--json proposal.json]  — find intent moments ("beats") in the kept text.

A beat = a moment type from style/grammar.json (stat, contrast, list, maxim, ...) anchored to one word index.
Detection reads the spoken text: kept words -> sentences -> cue regexes (up to 3 moments per sentence, stronger first,
first sentence = hook). --llm asks the local model (http://127.0.0.1:8081, optional; never an external API) to
classify sentences no cue matched. build_edl.py/beatfx.py turn beats into effects via the same grammar; critic.py checks.
--write stores plan["beats"] (manual beats and beats switched off by hand are kept). --gfx also proposes the graphics
the grammar automates (auto_gfx; shorts: 9:16 number cards quoting the spoken number); with --write they go to
gfx_specs + plan["gfx"]. --json out = the whole proposal (beats, gfx, specs); nothing else is written.
Thresholds and word lists: grammar["detect"]. The grammar path is never read from the plan (plans arrive via Syncthing)."""
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GRAMMAR = os.path.join(HERE, "style", "grammar.json")
LLM_URL = os.environ.get("BEATS_LLM_URL", "http://127.0.0.1:8081/v1/chat/completions")
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def load_grammar(path=None):
    """beatfx.load_grammar (one validator: a broken key is named, not a bare KeyError; detect thresholds required) + compiled cues."""
    from beatfx import load_grammar as checked
    g = checked(path or DEFAULT_GRAMMAR)
    for b in g["beats"].values():
        b["_re"] = [re.compile(c, re.IGNORECASE) for c in b.get("cues", [])]
    return g


def load_words(plan, base="."):
    with open(os.path.join(base, plan["words"]), encoding="utf-8") as f:
        return [(x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000, x["text"]) for x in json.load(f)["transcription"]]


def sentences(plan, W, max_sentence=30):
    """Kept word indices grouped into sentences: split on . ? ! (and at a comma after max_sentence words)."""
    out, cur = [], []
    for k in plan["keeps"]:
        for i in range(k[0], k[1] + 1):
            t = W[i][2].strip()
            if not t:
                continue
            cur.append(i)
            if re.search(r"[.?!…]$", t) or (len(cur) >= max_sentence and t.endswith(",")):
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    return out


def _text_map(idx, W):
    """Sentence text plus the word index owning each character (for mapping a regex match to its word)."""
    parts, owner = [], []
    for i in idx:
        t = W[i][2].strip()
        if parts:
            parts.append(" ")
            owner.append(i)
        parts.append(t)
        owner.extend([i] * len(t))
    return "".join(parts), owner


def classify(idx, W, grammar, min_dist=6, per_sentence=3):
    """All cue hits in one sentence as [(type, anchor word)], highest priority first; hits closer than min_dist words
    to a stronger one are dropped (one moment per phrase, several per long sentence)."""
    text, owner = _text_map(idx, W)
    hits = []
    for name, b in grammar["beats"].items():
        for rx in b["_re"]:
            for m in rx.finditer(text):
                pos = m.start(m.lastindex) if m.lastindex else m.start()  # first group = context (", ale"): anchor at the cue
                while pos < len(text) - 1 and text[pos] in " ,;:–-":
                    pos += 1
                hits.append((b["priority"], name, owner[min(pos, len(owner) - 1)]))
    hits.sort(key=lambda h: (-h[0], h[2]))
    pos_of = {i: n for n, i in enumerate(idx)}
    out = []
    for _, name, w in hits:
        if len(out) < per_sentence and all(abs(pos_of[w] - pos_of[o[1]]) >= min_dist for o in out):
            out.append((name, w))
    return out


def hook_anchor(idx, W, earliest=0.5, latest=1.5):
    """Hook punch lands on an early content word, not at t=0 (a ramp starting at 0 reads as a static start) and
    within `latest` s of the first word (shorts: visual change inside 1.5 s)."""
    t_first = W[idx[0]][0]
    for i in idx[1:]:
        if W[i][0] - t_first > latest:
            break
        if W[i][0] - t_first >= earliest and len(re.sub(r"\W", "", W[i][2])) >= 4:
            return i
    return next((i for i in idx if W[i][0] - t_first >= earliest), idx[-1])


def detect(plan, W, grammar):
    beats, d = [], grammar["detect"]
    for n, idx in enumerate(sentences(plan, W, d["max_sentence"])):
        text = " ".join(W[i][2].strip() for i in idx)
        hits = classify(idx, W, grammar, d["min_dist"], d["per_sentence"])
        if n == 0:
            h = hook_anchor(idx, W, d["hook_earliest"], d["hook_latest"])
            beats.append({"type": "hook", "word": h, "src": "rule", "text": text[:120]})
            hits = [x for x in hits if abs(idx.index(x[1]) - idx.index(h)) >= d["min_dist"]]
        for name, w in hits:
            beats.append({"type": name, "word": w, "src": "rule", "text": text[:120]})
        if not hits and n:
            beats.append({"type": None, "word": idx[0], "src": "rule", "text": text[:120], "_idx": idx})
    return beats


def llm_refine(beats, W, grammar, url=LLM_URL, timeout=180):
    """Ask the local model to label sentences that matched no cue. Unreachable model or a reply of an unexpected
    shape (no choices, content null, truncated body) = rule-only result."""
    todo = [b for b in beats if b["type"] is None]
    if not todo:
        return 0
    if urllib.parse.urlsplit(url).hostname not in LOCAL_HOSTS:  # the transcript never leaves the laptop
        print(f"llm: {url} nie jest lokalny (BEATS_LLM_URL); tylko reguły", file=sys.stderr)
        return 0
    types = {k: v["intent"] for k, v in grammar["beats"].items() if k != "hook"}
    lines = [f"{n}: {b['text']}" for n, b in enumerate(todo)]
    prompt = ("Klasyfikujesz zdania z nagrania wideo (mówiony polski) według intencji mówcy. Typy:\n"
              + "\n".join(f"- {k}: {v}" for k, v in types.items())
              + "\n- none: zwykłe zdanie bez wyraźnej intencji\nZwróć TYLKO JSON: {\"labels\": [{\"n\": numer, \"type\": typ, \"word\": słowo-kotwica z tego zdania}]}.\n"
              + "Zdania:\n" + "\n".join(lines))
    body = json.dumps({"model": "chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    try:
        req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
        direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never via http_proxy: text stays local
        with direct.open(req, timeout=timeout) as r:
            content = json.load(r)["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError(f"content: {type(content).__name__}")
    except (urllib.error.URLError, OSError, http.client.HTTPException, KeyError, IndexError, TypeError, ValueError) as e:
        print(f"llm: niedostępny ({e!r}); tylko reguły", file=sys.stderr)
        return 0
    m = re.search(r"\{.*\}", content, re.DOTALL)
    try:
        labels = json.loads(m.group(0))["labels"] if m else []
    except (ValueError, KeyError, TypeError):
        labels = []
    if not isinstance(labels, list):
        labels = []
    got = 0
    for lab in labels:
        if not isinstance(lab, dict) or not isinstance(lab.get("n"), int) or not 0 <= lab["n"] < len(todo):
            continue
        if not isinstance(lab.get("type"), str) or lab["type"] not in types:  # a list/object type = bad shape, skip
            continue
        b = todo[lab["n"]]
        anchor = next((i for i in b["_idx"] if str(lab.get("word", "")).lower().strip(",.?!") and
                       W[i][2].strip().lower().strip(",.?!") == str(lab["word"]).lower().strip(",.?!")), b["_idx"][0])
        b.update(type=lab["type"], word=anchor, src="llm")
        got += 1
    return got


def merge(old, new):
    """Keep what the editor decided by hand: manual beats, and type/off overrides on the same anchor word."""
    by_word = {b["word"]: b for b in old if b.get("src") == "manual" or b.get("off") or b.get("force")}
    out = []
    for b in new:
        o = by_word.pop(b["word"], None)
        out.append(o if o else b)
    out.extend(by_word.values())
    return sorted(out, key=lambda b: b["word"])


def kept_order(plan):
    return [i for k in plan["keeps"] for i in range(k[0], k[1] + 1)]


def stat_card(word, W, order, detect):
    """(text, sub) of a number card from the spoken words: '40' + 'repozytoriów', '3 na 4', '~60' + 'ekranów'.
    The caption is at most 2 words and never ends on a preposition ('20 minut w tygodniu' -> 'minut'). detect =
    grammar["detect"] (word lists)."""
    approx, filler, drop = detect["approx"], set(detect["filler"]), set(detect["caption_drop_last"])
    clean = [W[i][2].strip().strip(",.?!:;„”\"") for i in order]
    p = order.index(word)
    text, j = clean[p], p + 1
    if re.fullmatch(r"\d{1,3}", text):  # '1 200 zł' said as two tokens = one number (thousands groups)
        while j < len(clean) and re.fullmatch(r"\d{3}", clean[j]) and not re.search(r"[.?!,]$", W[order[j - 1]][2].strip()):
            text, j = f"{text}\u00a0{clean[j]}", j + 1
    if j + 1 < len(clean) and clean[j].lower() == "na" and re.fullmatch(r"\d+%?", clean[j + 1]):
        text, j = f"{text} na {clean[j + 1]}", j + 2
    prev = clean[p - 1].lower() if p else ""
    if prev in approx:
        text = text + "+" if approx[prev] == "+" else "~" + text
    sub = []
    if re.search(r"[.?!]$", W[order[j - 1]][2].strip()):  # the number ends its sentence: the next words are another thought
        return text, ""
    for i in range(j, min(j + 4, len(clean))):
        w = clean[i]
        if w.lower() in filler and not sub:
            continue
        sub.append(w)
        if re.search(r"[.?!,]$", W[order[i]][2].strip()) or len(sub) == 2:
            break
    while sub and sub[-1].lower() in drop:
        sub.pop()
    return text, " ".join(sub)


def pick_icon(text, grammar):
    for rx, name in grammar.get("icons", {}).items():
        if rx != "_doc" and re.search(rx, text, re.IGNORECASE):
            return name
    return "hash"


def make_gfx(plan, beats, W, grammar, specs):
    """Graphics for moments listed in grammar auto_gfx[format] (shorts: number cards, 9:16). Idempotent: id per moment;
    a moment with another graphic closer than gfx_min_gap s is left alone (one card read at a time). Returns new specs
    (plan["gfx"] updated in place). Graphic ids use only [A-Za-z0-9_-] (the panel and gfx/render.mjs file names)."""
    fmt = "short" if plan.get("vertical") else "long"
    d = grammar["detect"]
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(plan.get("name") or "film")).strip("_") or "film"
    kinds = grammar.get("auto_gfx", {}).get(fmt, [])
    order = kept_order(plan)
    have = {s["id"] for s in specs}
    near = [g["word"] for g in plan.get("gfx", []) if isinstance(g.get("word"), int)]
    # shorts: the hook title sits in the same top band for hook_dur s; source time >= output time, so +1 s margin
    hook_end = W[order[0]][0] + plan.get("hook_dur", 3.0) + 1.0 if plan.get("hook_text") and order else -1.0
    new = []
    for b in beats:
        if b["type"] not in kinds or b.get("off") or b["word"] not in order:
            continue
        gid = f"b_{name}_{b['word']}"
        if gid in have or any(abs(W[w][0] - W[b["word"]][0]) < d["gfx_min_gap"] for w in near) or W[b["word"]][0] < hook_end:
            continue
        text, sub = stat_card(b["word"], W, order, d)
        spec = {"id": gid, "type": "kw", "text": text, "sub": sub, "icon": pick_icon(b.get("text", ""), grammar),
                "dur": grammar["auto_gfx"].get("dur", 2.5), "quote": True, "beat": b["type"]}
        if fmt == "short":
            spec["canvas"] = "v"
        new.append(spec)
        plan.setdefault("gfx", []).append({"id": gid, "word": b["word"], "lead": 0.0})
        near.append(b["word"])
    return new


def _atomic_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def main(argv):
    plan_p = argv[0]
    gpath = argv[argv.index("--grammar") + 1] if "--grammar" in argv else None
    with open(plan_p, encoding="utf-8") as f:
        plan = json.load(f)
    grammar = load_grammar(gpath)
    W = load_words(plan, os.path.dirname(os.path.abspath(plan_p)))
    beats = detect(plan, W, grammar)
    if "--llm" in argv:
        print("llm: oznaczone", llm_refine(beats, W, grammar))
    beats = [{k: v for k, v in b.items() if not k.startswith("_")} for b in beats if b["type"]]
    beats = merge(plan.get("beats", []), beats)
    fmt = "short" if plan.get("vertical") else "long"
    for b in beats:
        eff = grammar["effects"][fmt].get(b["type"], {})
        print(f"{W[b['word']][0]:8.2f}s  {b['type']:<10} @{b['word']:<5} {W[b['word']][2].strip():<14} gfx={eff.get('gfx')}  | {b.get('text', '')[:70]}")
    work = os.path.dirname(os.path.abspath(plan_p))
    new, gfx_before = [], list(plan.get("gfx", []))
    if "--gfx" in argv:
        sp_path = os.path.join(work, plan.get("gfx_specs", "gfx_specs.json"))
        specs = []
        if os.path.exists(sp_path):
            with open(sp_path, encoding="utf-8") as f:
                specs = json.load(f)
        new = make_gfx(plan, beats, W, grammar, specs)
        for sp in new:
            print(f"grafika {sp['id']}: {sp['text']} / {sp['sub']} ({sp['icon']})")
        if new:  # shorts have no specs file / gfx dir until their first graphic: point the plan at them only now
            plan.setdefault("gfx_specs", "gfx_specs.json")
            plan.setdefault("gfx_dir", os.path.join(work, "gfx"))
        if new and "--write" in argv:  # specs first: a crash in between leaves an unused spec, never a plan
            _atomic_json(sp_path, specs + new)  # pointing at a card that does not exist
    if "--json" in argv:  # proposal for the editing panel, which applies it through its undo history
        _atomic_json(argv[argv.index("--json") + 1], {"beats": beats, "gfx": plan.get("gfx", [])[len(gfx_before):],
                                                       "specs": new})
    if "--write" in argv:
        plan["beats"] = beats
        _atomic_json(plan_p, plan)
        print("zapisano", len(beats), "momentów ->", plan_p)

if __name__ == "__main__":
    main(sys.argv[1:])
