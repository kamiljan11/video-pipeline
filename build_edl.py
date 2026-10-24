#!/usr/bin/env python3
"""build_edl.py plan.json -> edl.json
plan: {"words": "x.cw.json", "sil": "x.sil", "src": "/path.mp4", "keeps": [[w0, w1, {"t0":opt,"t1":opt}], ...],
       "gfx": [{"id":..., "word": idx, "lead": 0.0}], "gfx_dir": "...", "gfx_specs": "...", "face": [x,y], "zooms": [1.0, 1.15]}"""
import json
import re
import sys
from pathlib import Path

import edges
import themes
from gfx_types import PIP, SIDE_BOX

P = json.loads(Path(sys.argv[1]).read_text())
W = [(x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000, x["text"]) for x in json.loads(Path(P["words"]).read_text())["transcription"]]
v = [float(x) for x in re.findall(r"silence_(?:start|end): ([0-9.]+)", Path(P["sil"]).read_text())]
SIL = [(v[i], v[i + 1]) for i in range(0, len(v) - 1, 2)]
PRE, POST, MINGAP, KEEP_L, KEEP_R = 0.10, 0.16, 0.45, 0.15, 0.12
ranges = []
EF = edges.options(P); ENERGY = None; moved = 0  # plan key "edge_fix" (edges.py): dead air / loud cuts at keep edges
if EF is not None and EF["dips"]:
    wav = edges.wav_path(P, EF)
    if wav is None: sys.exit("edge_fix.dips: no 16-bit wav of the recording (set edge_fix.wav)")
    try: ENERGY = edges.Energy(wav)
    except edges.BAD_WAV as e: sys.exit(f"edge_fix.dips: {wav}: {e}")
for k in P["keeps"]:
    a, b = k[0], k[1]; o = k[2] if len(k) > 2 else {}
    t0 = o.get("t0", W[a][0] - PRE); t1 = o.get("t1", W[b][1] + POST)
    if a > 0 and "t0" not in o: t0 = max(t0, W[a - 1][1] + 0.02)
    if b + 1 < len(W) and "t1" not in o: t1 = min(t1, max(W[b + 1][0] - 0.03, W[b][1] + 0.05))
    f0 = EF is None or "t0" not in o; f1 = EF is None or "t1" not in o  # with edge_fix an explicit t0/t1 is final
    # if a real silence sits right at the boundary, snap into it (cleaner cut)
    for ss, se in SIL:
        if f0 and ss - 0.3 < t0 < se and se - t0 < 0.4: t0 = max(t0, se - 0.08)
        if f1 and ss < t1 < se + 0.3 and t1 - ss < 0.4: t1 = min(t1, ss + 0.12)
    # drop leftover blips: keep that starts with <0.35 s of sound then a long pause starts after the pause (and mirror for the end)
    for ss, se in SIL:
        if f0 and se - ss > 0.4 and t0 <= ss < t0 + 0.35 and se < t1 - 0.5: t0 = se - 0.08
        if f1 and se - ss > 0.4 and t1 - 0.35 < se <= t1 and ss > t0 + 0.5: t1 = ss + 0.12
    if EF is not None:
        e0, e1 = t0, t1
        t0, t1 = edges.trim_dead_air(t0, t1, SIL, f0, f1)
        if ENERGY is not None:  # a cut in loud speech -> nearest energy dip, never past the neighbouring words
            if f0: t0 = edges.snap_loud(t0, W[a - 1][1] - 0.06 if a > 0 else 0.0, min(W[a][0] + 0.06, t1 - 0.3), ENERGY, EF)
            if f1: t1 = edges.snap_loud(t1, max(W[b][1] - 0.06, t0 + 0.3), W[b + 1][0] + 0.06 if b + 1 < len(W) else t1 + EF["win"], ENERGY, EF)
        inside = f0 and bool(ranges) and ranges[-1][2] < a and ranges[-1][1] > t0
        if inside: t0 = ranges[-1][1]  # never play the same sound twice
        if t1 - t0 < 0.05:
            why = "it lies inside the previous keep" if inside else "check its t0/t1"
            sys.exit(f"edge_fix: keep {k[:2]} ends before it starts ({t0:.2f}-{t1:.2f} s): {why}")
        moved += (t0, t1) != (e0, e1)
    ranges.append([max(0.0, t0), t1, a])
if EF is not None: print("edge_fix moved", moved, "keep edges")
# tighten long pauses inside kept ranges using measured silence
if "seg_exact" in P and type(P["seg_exact"]) is not bool: sys.exit(f"seg_exact: true or false, got {P['seg_exact']!r}")  # assemble.py reads bool(): "false" would turn it on
MIN_SEG = P.get("min_seg")  # s: no piece shorter than this between two cuts (a 0.7 s flash reads as a double cut)
if MIN_SEG is not None and (type(MIN_SEG) not in (int, float) or not 0 < MIN_SEG <= 3): sys.exit(f"min_seg: seconds 0..3, got {MIN_SEG!r}")
segs = []
for t0, t1, a in ranges:
    cur = t0; rs = []
    for ss, se in SIL:
        if ss > cur + 0.3 and se < t1 - 0.3 and se - ss > MINGAP:
            rs.append([cur, ss + KEEP_L, "pause"]); cur = se - KEEP_R
    rs.append([cur, t1, "end"])
    while MIN_SEG and len(rs) > 1:  # keep the shorter of the two pauses around a too-short piece (merge across it)
        k = next((i for i, r in enumerate(rs) if r[1] - r[0] < MIN_SEG), None)
        if k is None: break
        j = k - 1 if k == len(rs) - 1 or (k > 0 and rs[k][0] - rs[k - 1][1] < rs[k + 1][0] - rs[k][1]) else k
        rs[j:j + 2] = [[rs[j][0], rs[j + 1][1], rs[j + 1][2]]]
    segs += rs
# zoom: toggle only on real jump cuts (removed > 0.8 s of source) -> hides the jump
zs = P.get("zooms", [1.0, 1.15]); zi = 0; out = []; prev_end = None
for s0, s1, kind in segs:
    if prev_end is not None and (s0 - prev_end > 0.8 or P.get("zoom_every_cut")): zi = (zi + 1) % len(zs)
    out.append({"src": "A", "in": round(s0, 3), "out": round(s1, 3), "zoom": zs[zi]}); prev_end = s1
def src2out(t):
    acc = 0.0
    for s in out:
        if t < s["in"]: return acc
        if t <= s["out"]: return acc + t - s["in"]
        acc += s["out"] - s["in"]
    return acc
total = sum(s["out"] - s["in"] for s in out)
specs = {s["id"]: s for s in json.loads(Path(P["gfx_specs"]).read_text())} if P.get("gfx_specs") else {}
ovs = []
def side_box(gid):  # a 16:9 side box covers the face, so no zoom under it; a 9:16 top card (canvas "v") sits above the face
    sp = specs.get(gid, {}); return sp.get("type") in SIDE_BOX and sp.get("canvas") != "v"
if P.get("gfx") and not (P.get("gfx_specs") and P.get("gfx_dir")):
    sys.exit("gfx: the plan places graphics, so it needs \"gfx_specs\" (cards file) and \"gfx_dir\" (their .mov folder)")
for g in P.get("gfx", []):
    if g.get("id") not in specs: sys.exit(f"gfx {g.get('id')!r}: no such card in {P['gfx_specs']}")
    if "find" in g:
        c = [i for i in range(max(0, g["near"] - 25), min(len(W), g["near"] + 25)) if g["find"].lower() in W[i][2].lower()]
        g["word"] = min(c, key=lambda i: abs(i - g["near"]))
    at = total if g["word"] == "END" else src2out(W[g["word"]][0]) + g.get("lead", 0.0)
    ovs.append({"file": f"{P['gfx_dir']}/{g['id']}.mov", "at": round(at, 3), "dur": specs[g["id"]]["dur"], "id": g["id"], "pip": specs[g["id"]].get("type") in PIP})
# no punch-in while a side box is on screen (box would cover the face)
acc = 0.0
for sg in out:
    d = sg["out"] - sg["in"]
    for o in ovs:
        if side_box(o["id"]) and acc < o["at"] + o["dur"] and acc + d > o["at"]:
            sg["zoom"] = 1.0
    acc += d
# ---- animated zooms: slow drift on long shots, quick punch on emphasis words ----
EMPH = P.get("emph", []); BEAT_FX = None
if "beats" in P:  # intent grammar (style/grammar.json): every punch comes from a detected moment, see beatfx.py
    from beatfx import plan_beat_fx
    EMPH, BEAT_FX = plan_beat_fx(P, W, out, ovs, specs, src2out)
boxed = set(); acc = 0.0
for k, sg in enumerate(out):
    d = sg["out"] - sg["in"]
    for o in ovs:
        if side_box(o["id"]) and acc < o["at"] + o["dur"] and acc + d > o["at"]:
            boxed.add(k)
    acc += d
DRIFT = P.get("drift", 0.05); flip = 0
for k, sg in enumerate(out):
    d = sg["out"] - sg["in"]; base = sg["zoom"]
    if k in boxed or d < 3.0 or DRIFT <= 0: continue
    a, b = (base, base + DRIFT) if flip % 2 == 0 else (base + DRIFT, base)
    sg["zoom"] = {"a": round(a, 3), "b": round(b, 3), "t0": 0.0, "t1": round(d, 3)}; flip += 1
PUNCHED = set()
for em in sorted(EMPH, key=lambda e: e.get("word", e.get("near", 0))) if BEAT_FX is not None else EMPH:
    if "word" in em: c = [em["word"]]
    else: c = [i for i in range(max(0, em["near"] - 30), min(len(W), em["near"] + 30)) if em["find"].lower() in W[i][2].lower()]
    if not c: print("emph not found", em); continue
    t_src = W[min(c, key=lambda i: abs(i - em.get("near", c[0])))][0]
    acc_e = 0.0
    for k, sg in enumerate(out):
        if sg["in"] <= t_src <= sg["out"]:
            t_out = acc_e + t_src - sg["in"]; seg_end = acc_e + sg["out"] - sg["in"]
            hit = [o["id"] for o in ovs if side_box(o["id"]) and o["at"] < seg_end and o["at"] + o["dur"] > t_out - 0.2]
            if hit: print("emph skipped (box on screen)", em.get("find", em.get("word")), hit); break
            base = sg["zoom"]["a"] if isinstance(sg["zoom"], dict) else sg["zoom"]
            t0 = max(0.0, t_src - sg["in"] - 0.12, em.get("min_t0", 0.0))  # min_t0: hook never on the first frame (beatfx)
            if BEAT_FX is not None and k in PUNCHED:  # editing grammar: next moment in the same long shot = snap back to the shot's level, punch again
                z = sg["zoom"]; keys = z.get("keys") or [[0.0, z["a"]], [z["t0"], z["a"]], [z["t1"], z["b"]]]
                t0 = max(t0, keys[-1][0] + 0.2)
                keys += [[round(t0 - 0.034, 3), keys[-1][1]], [round(t0, 3), z["a"]], [round(t0 + em.get("speed", 0.3), 3), round(min(z["a"] + em.get("amt", 0.2), 1.38), 3)]]
                z["keys"] = keys; z["b"] = max(v for _, v in keys)
                print("emph", em.get("find", em.get("word")), "seg", k, em.get("beat", "manual"), "(+keys)"); break
            sg["zoom"] = {"a": base, "b": round(min(base + em.get("amt", 0.2), 1.38), 3), "t0": round(t0, 3), "t1": round(t0 + em.get("speed", 0.3), 3)}
            PUNCHED.add(k)
            print("emph", em.get("find", em.get("word")), "seg", k, *([em["beat"]] if "beat" in em else [])); break
        acc_e += sg["out"] - sg["in"]
# manual per-segment zoom from the editing panel: {"<source in, 2 decimals>": zoom}; face_track still clamps to zmax
for sg in out:
    ov = P.get("seg_zoom", {}).get(f"{sg['in']:.2f}")
    if ov is not None: sg["zoom"] = ov
BROLL = None
if "broll" in P:  # stock b-roll (broll.py): full-frame cutaways from their anchor words, never under a graphic
    from broll import place
    BROLL = place(P["broll"], W, out, ovs)
_tail = P.get("tail", 0)  # end screen seconds (long: YouTube end screen; short: end card), goes to ffmpeg tpad/apad
if isinstance(_tail, bool) or not isinstance(_tail, (int, float)) or not 0 <= _tail <= 60:
    sys.exit(f"tail: seconds of end screen 0..60, got {_tail!r}")
edl = {"name": P.get("name", "montaz"), "sources": {"A": P["src"]}, "segments": out, "overlays": ovs, "face": P.get("face", [0.5, 0.45]),
       "tail": P.get("tail", 0), "w": 2560, "h": 1440, "out_name": P.get("out_name", "final.mp4"), "gfx_specs": P.get("gfx_specs"), "progress": P.get("progress", False), "music_seed": P.get("music_seed", 7),
       **{k: P[k] for k in ("music_db", "sfx_db", "audio", "steady_x", "seg_exact", "sfx_style", "music_moods") if k in P}}  # audio: voice filter chain for assemble.py; steady_x: face_track; seg_exact: assemble.py; sfx_style, music_moods: music/make_beds.py
THEME = themes.load()  # work/theme.json (themes.py): accent for captions here, progress bar + PiP frame in assemble.py
if THEME is not None:
    edl["theme"] = THEME
    themes.pip_frame(THEME)  # fail now, not in assemble after the long steps: the theme needs its PiP frame
if BEAT_FX is not None:
    from beatfx import grammar_stamp
    edl["beat_fx"] = BEAT_FX; edl["beat_grammar"] = grammar_stamp()
if BROLL is not None:
    edl["broll"], edl["broll_skipped"] = BROLL
    rej = P.get("broll_rejected")  # ADR-0003 metric (beatfx.py): clips the editor took out; plans arrive via Syncthing
    edl["broll_removed"] = sum(isinstance(r, dict) for r in rej) if isinstance(rej, list) else 0
    for b in BROLL[0]: print("broll", b["id"], b["at"])
    for b in BROLL[1]: print("broll skipped word", b["word"], b["reason"])
if P.get("vertical"):
    # a short has no tail unless its plan asks for one (an end screen card: gfx word "END", e.g. "tail": 3)
    edl.update({"vertical": True, "w": 1080, "h": 1920, "subs": P.get("ass_out"), "tail": P.get("tail", 0)})

txt = []
for k in P["keeps"]: txt.append("".join(W[i][2] for i in range(k[0], k[1] + 1)).strip())
Path(P["edl_out"].replace(".json", ".txt")).write_text("\n".join(txt))
print("segments", len(out), "jumpcuts", sum(1 for i in range(1, len(out)) if out[i]["zoom"] != out[i-1]["zoom"]), "duration", round(total, 1), "s")
for o in ovs: print(o["id"], o["at"])
for w in P.get("probe", []): print("probe", w, round(src2out(W[w][0]), 2))

# ---- captions (SRT for long-form upload, ASS burned-in for vertical) ----
FIX = {"porekscytowany": "podekscytowany", "jaj,": "AI,", "zapewniła": "zapełniła", "podescytowany": "podekscytowany",
       "mnie": "mniej" , "czat": "czat", "techniczne": "technicznie"}
def fixw(w):
    k = w.strip(); lk = k.lower()
    return FIX.get(lk, k) if lk in ("porekscytowany", "jaj,", "zapewniła", "podescytowany") else k
kept = []
for k in P["keeps"]:
    for i in range(k[0], k[1] + 1):
        t = W[i][2].strip()
        if not t: continue
        st = src2out(W[i][0]); en = src2out(W[i][1])
        kept.append([st, max(en, st + 0.12), fixw(t)])
def ts(t, sep=","):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", sep)
if P.get("srt_out"):
    # sentence-ish lines, max ~42 chars
    out_l, cur = [], []
    for w in kept:
        cur.append(w)
        txt = " ".join(x[2] for x in cur)
        if len(txt) > 70 or re.search(r"[.?!]$", w[2]) or (len(txt) > 45 and w[2].endswith(",")):
            out_l.append(cur); cur = []
    if cur: out_l.append(cur)
    def wrap(ws):
        t = " ".join(x[2] for x in ws)
        if len(t) <= 42: return t
        best = None
        for k in range(1, len(ws)):
            a, b2 = " ".join(x[2] for x in ws[:k]), " ".join(x[2] for x in ws[k:])
            sc = max(len(a), len(b2))
            if best is None or sc < best[0]: best = (sc, a + "\n" + b2)
        return best[1] if best else t  # one long word: nothing to split
    with open(P["srt_out"], "w") as f:
        for n, l in enumerate(out_l, 1):
            e = max(l[-1][1] + 0.05, l[0][0] + 0.85)
            if n < len(out_l): e = min(e, out_l[n][0][0] - 0.02)
            f.write(f"{n}\n{ts(l[0][0])} --> {ts(e)}\n{wrap(l)}\n\n")
if P.get("ass_out"):
    hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,130,540,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if type(P.get("caption_box", False)) is not bool: sys.exit(f"caption_box: true/false, got {P['caption_box']!r}")
    if P.get("caption_box"):  # STYL-SHORTOW R2: one line in a box at ~63 % height (under the chin), not bare text at 72 %
        box = themes.ass_color(THEME["ink"], 0) if THEME else "&H00000000"  # BorderStyle 3 box = OutlineColour; opaque: a see-through box doubles where colour runs meet
        hdr = hdr.replace("Style: Cap,Montserrat,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,130,540,1",
                          f"Style: Cap,Montserrat,80,&H00FFFFFF,&H00FFFFFF,{box},&H00000000,-1,0,0,0,100,100,0,0,3,16,0,2,70,70,650,1")
    cv = P.get("caption_v")  # MarginV of the captions (px from the bottom of 1920); lower = further from the face
    if cv is not None:
        if type(cv) is not int or not 300 <= cv <= 900: sys.exit(f"caption_v: whole px 300..900, got {cv!r}")
        hdr = re.sub(r"^(Style: Cap,(?:[^,]*,){20})\d+,", rf"\g<1>{cv},", hdr, flags=re.MULTILINE)
    # captions pause under a card in their own zone (a "pill" hook card, STYL-SHORTOW R3): never two texts on one spot
    for o in ovs:  # the pill css exists only for a 9:16 maxim: anything else would silence captions under nothing
        sp = specs.get(o["id"], {})
        if "pill" in sp and (type(sp["pill"]) is not bool or sp["pill"] and (sp.get("type"), sp.get("canvas")) != ("maxim", "v")):
            sys.exit(f"{o['id']}: pill = true/false, only on a maxim with canvas \"v\", got {sp['pill']!r}")
    quiet = [(o["at"], o["at"] + o["dur"]) for o in ovs if specs.get(o["id"], {}).get("pill") is True]
    PILL_MIN_LEFT = 0.3  # s: a shorter rest of a line after the pill leaves would only flash
    ev = []; i = 0
    CAP_ACC = themes.ass_color(THEME["acc"]) if THEME else "&HC4E22D"  # spoken word in the accent colour
    while i < len(kept):
        grp = [kept[i]]; i += 1
        while i < len(kept) and len(grp) < 3 and len(" ".join(x[2] for x in grp + [kept[i]])) <= 18 and not re.search(r"[.?!,]$", grp[-1][2]):
            grp.append(kept[i]); i += 1
        for j, w in enumerate(grp):  # karaoke-style: current word in accent colour
            end = grp[j + 1][0] if j + 1 < len(grp) else (kept[i][0] if i < len(kept) else w[1])
            txt = " ".join(("{\\c" + CAP_ACC + "&}" + x[2].strip(",.").upper() + "{\\c&HFFFFFF&}") if k == j else x[2].strip(",.").upper() for k, x in enumerate(grp))
            e = min([end, w[1] + 0.6] + [q0 for q0, _ in quiet if q0 > w[0]])
            s = max([w[0]] + [q1 for q0, q1 in quiet if q0 - 0.05 <= w[0] < q1])  # 0.05: card "at" is rounded to ms, the word is not
            if s > w[0] and e - s < PILL_MIN_LEFT: continue  # said under the pill: a line still on when it leaves shows from then, no blank gap
            ev.append(f"Dialogue: 0,{ts(s, '.')[1:-1]},{ts(e, '.')[1:-1]},Cap,,0,0,0,,{txt}")
    if P.get("hook_text"):
        # BorderStyle 3 = opaque box drawn in OutlineColour (libass, like VSFilter); BackColour would only colour a shadow
        box, back = (themes.ass_color(THEME["ink"], 0), "&H00000000") if THEME else ("&H00000000", "&HD8120F0D")  # no theme: as before
        hdr = hdr.replace("[Events]", f"Style: Hook,Montserrat,84,&H00FFFFFF,&H00FFFFFF,{box},{back},-1,0,0,0,100,100,0,0,3,0,0,8,90,130,330,1\n\n[Events]")
        ev.insert(0, f"Dialogue: 1,0:00:00.00,0:00:{P.get('hook_dur', 3.0):05.2f},Hook,,0,0,0,,{{\\fad(0,250)\\bord14}}{P['hook_text']}")
    Path(P["ass_out"]).write_text(hdr + "\n".join(ev) + "\n")

Path(P["edl_out"]).write_text(json.dumps(edl, indent=1, ensure_ascii=False))
