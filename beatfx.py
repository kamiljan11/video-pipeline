"""Beats -> effects (used by build_edl.py when the plan has a "beats" key; see style/grammar.json).

Selection is intentional, not time-based:
  1. forced beats (set by the editor or by critic --fix) always get their punch;
  2. primary beats by priority, unless another punch is closer than rules.min_gap;
  3. secondary beats only inside a stretch with no visual event longer than rules.fill_after;
  4. "pace": a stretch still static for rules.max_static s (critic C1 limit) gets a gentle push on the clause start
     nearest its middle — labelled, so the editor sees it is rhythm, not a moment (and may cut the stretch instead).
Several punches in one long shot become zoom keyframes (build_edl: snap back to the shot's level, punch again). A beat under a side box (kw/list/slide) gets no punch: the box is its effect. Manual emph entries stay as they are;
time-based "auto" emph (old critic --fix) is dropped — every punch must have a reason."""
import hashlib
import itertools
import json
import os
import re

BOX = ("kw", "list", "slide")
SFX = (None, "pop", "whoosh", "ding")  # the sounds music/make_beds.py BEAT_SFX can play
DEFAULT_GRAMMAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style", "grammar.json")
ICONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules", "lucide-static", "icons")  # gfx/render.mjs reads <name>.svg


def load_grammar(path=None):
    """style/grammar.json, checked: a hand edit that drops or breaks a key fails here with its name, not deep in
    build_edl or beats.py (both load the grammar through this function)."""
    path = path or DEFAULT_GRAMMAR
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
    return _validate(g, path)


def _regex(x):
    if not isinstance(x, str):
        return False
    try:
        re.compile(x)
    except re.error:
        return False
    return True


def _num(x, low=None):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and (low is None or x > low)


DETECT_KEYS = {"min_dist": int, "per_sentence": int, "max_sentence": int, "hook_earliest": float, "hook_latest": float,
               "gfx_min_gap": float, "filler": list, "approx": dict, "caption_drop_last": list}


def _validate(g, path):
    if not isinstance(g, dict) or not all(isinstance(g.get(k, {}), dict) for k in ("rules", "effects", "beats", "icons")):
        raise ValueError(f"{path}: rules, effects, beats i icons muszą być obiektami")
    bad = [f"{sec}.{fmt}" for sec in ("rules", "effects") for fmt in ("long", "short")
           if not isinstance(g.get(sec, {}).get(fmt), dict)]
    for fmt in ("long", "short"):
        rules = g.get("rules", {}).get(fmt)
        if isinstance(rules, dict):
            bad += [f"rules.{fmt}.{k}" for k in ("min_gap", "fill_after", "max_static") if not _num(rules.get(k), 0)]
        eff = g.get("effects", {}).get(fmt)
        for kind, e in (eff.items() if isinstance(eff, dict) else ()):
            if kind == "_doc":
                continue
            punch = e.get("punch") if isinstance(e, dict) else None
            if not isinstance(e, dict) or (punch is not None and not (isinstance(punch, dict) and _num(punch.get("amt"), 0)
                                                                      and _num(punch.get("speed", 0.3), 0))):
                bad.append(f"effects.{fmt}.{kind}.punch")  # amt > 0 (zoom in), speed > 0 s
            elif e.get("sfx") not in SFX:
                bad.append(f"effects.{fmt}.{kind}.sfx")
    beats = g.get("beats")
    if not isinstance(beats, dict) or not beats:
        bad.append("beats")
    else:
        for k, b in beats.items():
            if not isinstance(b, dict):
                bad.append(f"beats.{k}")
                continue
            bad += [f"beats.{k}.priority"] * (not _num(b.get("priority")))
            bad += [f"beats.{k}.intent"] * (not isinstance(b.get("intent"), str))
            bad += [f"beats.{k}.cues"] * (not isinstance(b.get("cues", []), list) or not all(map(_regex, b.get("cues", []))))
            bad += [f"effects.{fmt}.{k}" for fmt in ("long", "short")  # every moment type needs its effect in both formats
                    if isinstance(g.get("effects", {}).get(fmt), dict) and k not in g["effects"][fmt]]
            bad += [f"beats.{k}.tier"] * (b.get("tier", "secondary") not in ("primary", "secondary"))
    bad += [f"effects.{fmt}.pace" for fmt in ("long", "short") if isinstance(g.get("effects", {}).get(fmt), dict)
            and "pace" not in g["effects"][fmt]]  # without it static stretches stay static (critic C1)
    for rx, name in g.get("icons", {}).items():  # a missing .svg would stop gfx/render.mjs for every graphic of the project
        if rx != "_doc" and (not _regex(rx) or not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name)
                             or not os.path.exists(os.path.join(ICONS, name + ".svg"))):
            bad.append(f"icons.{rx}")
    detect = g.get("detect")
    if not isinstance(detect, dict):
        bad.append("detect")
    else:  # the only source of detection thresholds (beats.py has no defaults of its own)
        for k, kind in DETECT_KEYS.items():
            v = detect.get(k)
            ok = _num(v, 0) and (kind is not int or isinstance(v, int)) if kind in (int, float) else isinstance(v, kind)
            if ok and isinstance(v, (list, dict)):  # words and their replacement marks: strings only
                ok = all(isinstance(x, str) for x in ([*v, *v.values()] if isinstance(v, dict) else v))
            bad += [f"detect.{k}"] * (not ok)
    bad += _broll_bad(g.get("broll"), g.get("beats"))
    if bad:
        raise ValueError(f"{path}: brak lub zły klucz: {', '.join(bad)}")
    return g


BROLL_KEYS = {"dur": (0.5, 8.0), "lead": (-1.0, 3.0), "min_gap": (0.0, 60.0), "max_share": (0.01, 1.0),
              "not_before": (0.0, 30.0), "per_topic": (1, 20)}


def _broll_bad(br, beats):
    """Optional section "broll" (broll.py): absent = no stock b-roll in any format."""
    if br is None:
        return []
    if not isinstance(br, dict):
        return ["broll"]
    bad = ["broll.provider"] * (not isinstance(br.get("provider"), str))
    topics = br.get("topics")
    if not isinstance(topics, list) or not all(isinstance(t, list) and len(t) == 2 and _regex(t[0]) and isinstance(t[1], str)
                                               and 0 < len(t[1]) <= 100 for t in topics):
        bad.append("broll.topics")  # [[regex on one word, English stock query], ...]
    for fmt in ("long", "short"):
        cfg = br.get(fmt)
        if cfg is None:
            continue
        if not isinstance(cfg, dict):
            bad.append(f"broll.{fmt}")
            continue
        bad += [f"broll.{fmt}.{k}" for k, (lo, hi) in BROLL_KEYS.items()
                if not (_num(cfg.get(k)) and lo <= cfg[k] <= hi and (k != "per_topic" or isinstance(cfg[k], int)))]
        avoid = cfg.get("avoid", [])
        if not isinstance(avoid, list) or not all(isinstance(beats, dict) and isinstance(a, str) and a in beats for a in avoid):
            bad.append(f"broll.{fmt}.avoid")  # moment types from "beats"
    return bad


def grammar_stamp(path=None):
    """Which grammar made this EDL (version + content hash), so a film can be tied to the rules it was cut with. The
    text is kept under style/history/grammar-<sha>.json (content-addressed, written once), so the sha in an EDL always
    resolves to the exact rules, also after grammar.json was edited again."""
    path = path or DEFAULT_GRAMMAR
    with open(path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()[:12]
    keep = os.path.join(os.path.dirname(os.path.abspath(path)), "history", f"grammar-{sha}.json")
    if not os.path.exists(keep):
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        with open(keep + ".tmp", "wb") as f:
            f.write(data)
        os.replace(keep + ".tmp", keep)
    return {"version": json.loads(data).get("version"), "sha": sha}


def _seg_of(t, segs):
    return next((s for s in segs if s["in"] <= t <= s["out"]), None)


def _anchor(w, W, segs, keeps):
    """build_edl places a punch at the word's start time; a cut snapped into the gap before a word can start the
    segment a few ms after it, so fall forward to the next kept word of the same keep."""
    for k in keeps:
        if k[0] <= w <= k[1]:
            for i in range(w, min(k[1], w + 2) + 1):
                if _seg_of(W[i][0], segs):
                    return i
    return None


class _Selection:
    """Effects chosen so far: punch times (min_gap), visual events (static stretches), emph entries and report rows."""

    def __init__(self, P, W, segs, ovs, specs, src2out, G):
        fmt = "short" if P.get("vertical") else "long"
        self.P, self.W, self.segs, self.src2out = P, W, segs, src2out
        self.rules, self.eff, self.kinds = G["rules"][fmt], G["effects"][fmt], G["beats"]
        self.hook_earliest, self.hook_latest = G["detect"]["hook_earliest"], G["detect"]["hook_latest"]
        self.manual = [e for e in P.get("emph", []) if not e.get("auto")]
        self.boxes = [(o["at"], o["at"] + o["dur"]) for o in ovs
                      if specs.get(o["id"], {}).get("type") in BOX and specs.get(o["id"], {}).get("canvas") != "v"]
        # a zoom change on a cut only hides the cut (continuity, RESEARCH.md) and face_track may flatten it: not an event
        self.total = sum(s["out"] - s["in"] for s in segs)
        self.seg_start, acc = {}, 0.0  # output start of each segment (by its source in)
        for sg in segs:
            self.seg_start[sg["in"]] = acc
            acc += sg["out"] - sg["in"]
        self.seg_zoom = P.get("seg_zoom", {})
        # manual punches count for spacing only if build_edl will show them (not under a box / a hand-set shot zoom)
        anchors = [e["word"] if "word" in e else e["near"] for e in self.manual]
        self.punches = [src2out(W[w][0]) for w in anchors if _seg_of(W[w][0], segs) and not self.blocked(w)]
        self.events = [o["at"] for o in ovs] + self.punches
        self.rows, self.chosen = [], []

    def blocked(self, w):
        """Why build_edl would not punch on word w: "manual" (the editor set this shot's zoom in the panel, applied
        after the punches) or "box" (a side box is on screen from 0.2 s before the word to the end of its shot);
        None = the punch will be visible. Same rules as build_edl, so the report never claims a punch it skips."""
        sg = _seg_of(self.W[w][0], self.segs)
        if sg is None:
            return "cut"
        if f"{sg['in']:.2f}" in self.seg_zoom:
            return "manual"
        t = self.seg_start[sg["in"]] + self.W[w][0] - sg["in"]
        end = self.seg_start[sg["in"]] + sg["out"] - sg["in"]
        return "box" if any(a < end and z > t - 0.2 for a, z in self.boxes) else None

    def take(self, kind, w, at, punch, row=None):
        if row is not None:
            row["fx"] = "punch"
        self.punches.append(at)
        self.events.append(at)
        self.chosen.append({"word": w, "amt": punch["amt"], "speed": punch.get("speed", 0.3), "beat": kind,
                            **({"min_t0": self.hook_earliest} if kind == "hook" else {})})

    def gap_around(self, t):
        return (max([x for x in self.events if x <= t], default=0.0),
                min([x for x in self.events if x > t], default=self.total))

    def report(self, b):
        """One report row per beat; returns (row, punch, anchor word) when the beat may still get a punch."""
        P, W, e = self.P, self.W, self.eff.get(b["type"], {})
        w = _anchor(b["word"], W, self.segs, P["keeps"])
        at = self.src2out(W[w if w is not None else b["word"]][0])
        if b["type"] == "hook" and w is not None:
            w = self.hook_word(w)
            at = max(self.src2out(W[w][0]), self.hook_earliest)  # build_edl starts the hook punch at min_t0 at the earliest
        row = {"type": b["type"], "word": b["word"], "at": round(at, 2), "fx": "none", "gfx": e.get("gfx"),
               "sfx": e.get("sfx"), **({"broll": e["broll"]} if e.get("broll") else {})}
        self.rows.append(row)
        if b.get("off"):
            row["fx"] = "off"
        elif b["type"] not in self.kinds:
            row["fx"] = "unknown"  # type renamed/removed in grammar.json: visible, not silently "no effect"
        elif w is None:
            row["fx"] = "cut"
        elif not e.get("punch"):
            row["fx"] = "gfx" if e.get("gfx") else "none"
        elif why := self.blocked(w):
            row["fx"] = why
        else:
            return row, e["punch"], w
        return None

    def primary(self, cands):
        """Strongest first; a punch closer than min_gap to another one makes this beat 'spacing'."""
        tier = {c[0]["type"]: self.kinds.get(c[0]["type"], {}).get("tier", "secondary") for c in cands}
        prim = sorted((c for c in cands if not c[0].get("force") and tier[c[0]["type"]] == "primary"),
                      key=lambda c: (-self.kinds.get(c[0]["type"], {}).get("priority", 0), c[1]["at"]))
        for b, row, punch, w in prim:
            if all(abs(row["at"] - p) >= self.rules["min_gap"] for p in self.punches):
                self.take(b["type"], w, row["at"], punch, row)
            else:
                row["fx"] = "spacing"

    def secondary(self, cands):
        """Only inside a stretch with no visual event for fill_after s, and not right next to its ends."""
        for b, row, punch, w in sorted((c for c in cands if c[1]["fx"] == "none"), key=lambda c: c[1]["at"]):
            before, after = self.gap_around(row["at"])
            if after - before > self.rules["fill_after"] and \
                    min(row["at"] - before, after - row["at"]) >= self.rules["min_gap"] / 2:
                self.take(b["type"], w, row["at"], punch, row)
            else:
                row["fx"] = "quiet"

    def pace(self):
        """Stretches still longer than max_static: a labelled rhythm punch on the clause start nearest the middle."""
        punch = self.eff.get("pace", {}).get("punch")
        if not punch or not self.rules.get("max_static"):
            return
        for i, t in self.pace_points():
            self.take("pace", i, t, punch)
            self.rows.append({"type": "pace", "word": i, "at": round(t, 2), "fx": "punch", "gfx": None, "sfx": None})

    def hook_word(self, w):
        """A hook punch at output 0 s reads as a static start (and critic C3 misses it): move it to the first kept
        word between detect.hook_earliest and hook_latest (0.5-1.5 s) of the finished video."""
        W, src2out, earliest, latest = self.W, self.src2out, self.hook_earliest, self.hook_latest
        if src2out(W[w][0]) >= earliest:
            return w
        for k in self.P["keeps"]:
            for i in range(max(k[0], w), k[1] + 1):
                t = src2out(W[i][0]) if _seg_of(W[i][0], self.segs) else -1
                if t > latest:
                    return w
                if t >= earliest:
                    return i
        return w

    def pace_points(self):
        """Yield (word, t) filling stretches longer than max_static: clause start (word after , . ? !) nearest the
        middle of the longest gap; self.events grows as the caller takes each point."""
        W, rules, starts = self.W, self.rules, []
        for k in self.P["keeps"]:
            for i in range(max(k[0], 1), k[1] + 1):
                if re.search(r"[.?!,]$", W[i - 1][2].strip()) and _seg_of(W[i][0], self.segs):
                    starts.append((self.src2out(W[i][0]), i))
        m = min(rules["min_gap"], rules["max_static"] / 3)  # keep off the gap ends, still fit short gaps
        for _ in range(100):  # each pass fills one gap; bounded
            pts = sorted({0.0, self.total, *self.events})
            gaps = sorted(((b - a, a, b) for a, b in itertools.pairwise(pts) if b - a > rules["max_static"]), reverse=True)
            pick = None
            for _, a, b in gaps:
                ok = [(abs(t - (a + b) / 2), t, i) for t, i in starts if a + m <= t <= b - m and not self.blocked(i)]
                if ok:
                    pick = min(ok)
                    break
            if pick is None:
                return
            yield pick[2], pick[1]


def plan_beat_fx(P, W, segs, ovs, specs, src2out, grammar=None):
    """Return (emph list for build_edl, report rows). segs: build_edl segments before drift/punches.
    Order: forced beats -> primary beats by priority -> secondary beats in long static stretches -> pace."""
    sel = _Selection(P, W, segs, ovs, specs, src2out, grammar or load_grammar())  # never a path from the plan (Syncthing)
    cands = [(b, *c) for b in P["beats"] if (c := sel.report(b))]
    for b, row, punch, w in cands:
        if b.get("force"):
            sel.take(b["type"], w, row["at"], punch, row)
    sel.primary(cands)
    sel.secondary(cands)
    sel.pace()
    sel.rows.sort(key=lambda r: r["at"])
    return sel.manual + sel.chosen, sel.rows


def fit_moves(keys, zmax):
    """face_track (EDL with beat_fx): [[t, zoom], ...] -> same moves under zmax. Each rising piece keeps its size
    (start lowered, floor 1.0, end <= zmax); the holds right before/after a move follow its new start/end, so the shot
    stays still between moves instead of every punch being flattened to one level."""
    old = [v for _, v in keys]
    new = list(old)
    for i in range(len(keys) - 1):
        if old[i + 1] <= old[i] + 1e-6:
            continue
        end = min(old[i + 1], zmax)
        start = max(1.0, min(old[i], end - (old[i + 1] - old[i])))
        new[i], new[i + 1] = start, end
        j = i - 1
        while j >= 0 and old[j] == old[i]:
            new[j] = start
            j -= 1
        j = i + 2
        while j < len(old) and old[j] == old[i + 1]:
            new[j] = end
            j += 1
    return [[t, round(v, 3)] for (t, _), v in zip(keys, new, strict=True)]


def stats(rows):
    """ADR-0002 metric from one EDL's beat_fx: punches by reason and the share of rhythm ("pace") punches."""
    punches = [r for r in rows if r["fx"] == "punch"]
    by = {}
    for r in punches:
        by[r["type"]] = by.get(r["type"], 0) + 1
    return {"punches": len(punches), "by_type": by, "pace_share": round(by.get("pace", 0) / len(punches), 3) if punches else 0.0}


if __name__ == "__main__":  # python3 beatfx.py edl_long.json ... -> metric per film (ADR-0002 review; run_v4.sh logs it)
    import sys
    import time
    for p in sys.argv[1:]:
        with open(p, encoding="utf-8") as f:
            edl = json.load(f)
        row = {**stats(edl["beat_fx"]), "grammar": edl.get("beat_grammar")} if "beat_fx" in edl else {}
        if "broll" in edl:  # ADR-0003 metric: stock b-roll share of the film and clips the editor removed
            body = sum(s["out"] - s["in"] for s in edl["segments"]) or 1.0
            row.update(broll_clips=len(edl["broll"]), broll_share=round(sum(b["dur"] for b in edl["broll"]) / body, 3),
                       broll_removed=edl.get("broll_removed", 0))
        if row:  # films without the grammar or b-roll have nothing to measure
            print(time.strftime("%Y-%m-%d %H:%M"), os.path.abspath(p), json.dumps(row, ensure_ascii=False))
