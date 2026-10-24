#!/usr/bin/env python3
"""make_beds.py edl.json outdir -> outdir/music.wav (own generated bed), outdir/sfx.wav (synth SFX timed to graphics/zooms)
Adds edl["music"], edl["sfx"] in place."""
import json
import os
import subprocess
import sys
import wave
from itertools import pairwise
from pathlib import Path

import numpy as np

SR = 44100
edl_p, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
edl = json.loads(Path(edl_p).read_text())
segs = edl["segments"]; body = sum(s["out"] - s["in"] for s in segs); total = body + edl.get("tail", 0)
specs = {s["id"]: s for s in json.loads(Path(edl["gfx_specs"]).read_text())} if edl.get("gfx_specs") else {}
rng = np.random.default_rng(3)
MOODS = ("tension", "story", "upbeat", "resolve", "drop")  # = music/gen_music.py
v2 = edl.get("sfx_style") == "v2"  # sounds by motion type (typing ticks, list clicks, riser + impact...); absent or "v1" = the classic set
if edl.get("sfx_style") not in (None, "v1", "v2"): sys.exit(f'sfx_style: "v1" or "v2", got {edl["sfx_style"]!r}')
moods = edl.get("music_moods") or None  # [[t_out_seconds, mood], ...]: the bed follows the mood of each moment
if moods is not None:
    ok = isinstance(moods, list) and all(isinstance(e, list) and len(e) == 2 and type(e[0]) in (int, float) and np.isfinite(e[0]) and e[0] >= 0
                                         and e[1] in MOODS for e in moods)
    if not ok: sys.exit(f"music_moods: [[seconds >= 0, one of {'/'.join(MOODS)}], ...], got {edl['music_moods']!r}")
    if any(b[0] <= a[0] for a, b in pairwise(moods)): sys.exit("music_moods: the times must increase")

def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x))
def bp(x, lo, hi):
    return lp(x, hi) - lp(x, lo)

def whoosh(d=0.7, up=True):
    n = int(d * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # sweep: blend of bands, crossfaded over time
    a = bp(noise, 300, 1200); b = bp(noise, 1500, 6000)
    k = t / d if up else 1 - t / d
    sig = a * (1 - k) + b * k
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return sig * env * 0.5
def pop(k=1.0):
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = (520 + 600 * np.exp(-t * 40)) * k
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32) * 0.55
    click = rng.standard_normal(n) * np.exp(-t * 900) * 0.15
    return s + click
def pen(d=0.45):
    """a marker scribbling on paper/whiteboard: scratchy band noise with stroke-rate flutter"""
    n = int(d * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 1800, 7000) * (0.55 + 0.45 * np.sin(2 * np.pi * 11 * t) ** 2)
    return s * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6 * 0.35
def ding():
    n = int(1.2 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1318.5, .5), (1975.5, .25), (2637, .12))) * np.exp(-t * 4) * 0.4
    return s

# --- sfx_style v2: one sound per motion (all peak-normalised here, the level is set where they are placed) ---
def pk(x, peak):
    return x * (peak / max(1e-9, np.abs(x).max()))
def keytick(k=1.0):
    """a soft key press: a short dull click on top of a low thock"""
    n = int(0.06 * SR); t = np.arange(n) / SR
    return pk(bp(rng.standard_normal(n), 1800, 6500) * np.exp(-t * 330) * 0.5 + np.sin(2 * np.pi * 190 * k * t) * np.exp(-t * 90) * 0.6, 0.5)
def click(k=1.0):
    """a UI click: higher and glassier than a key (no thock)"""
    n = int(0.04 * SR); t = np.arange(n) / SR
    return pk(np.sin(2 * np.pi * 2400 * k * t) * np.exp(-t * 220) * 0.6 + bp(rng.standard_normal(n), 3000, 9000) * np.exp(-t * 700) * 0.4, 0.5)
def typing(d=0.6):
    """a burst of key presses: uneven rhythm, every key a bit different"""
    out = np.zeros(int(d * SR) + int(0.06 * SR)); t = 0.0
    while t < d:
        s = int(t * SR); tk = keytick(2 ** (rng.uniform(-2, 2) / 12)) * rng.uniform(0.6, 1.0); out[s:s + len(tk)] += tk
        t += rng.uniform(0.035, 0.065)
    return pk(out, 0.6)
def swoosh(d=0.35):
    """a soft slide: smoother and lower than whoosh, quick in and gentle out"""
    n = int(d * SR); t = np.arange(n) / SR; x = np.clip(t / d, 0, 1); noise = rng.standard_normal(n)
    return pk((bp(noise, 400, 1800) * (1 - x) + bp(noise, 900, 4000) * x) * np.sin(np.pi * x ** 0.7) ** 2, 0.55)
def riser(d=0.9):
    """filtered noise and a tone climbing together, swelling to the end, then cut for the impact"""
    n = int(d * SR); t = np.arange(n) / SR; x = t / d; noise = rng.standard_normal(n)
    tone = np.sin(2 * np.pi * np.cumsum(250 * 4 ** x) / SR) * 0.35
    return pk((bp(noise, 400, 1500) * (1 - x) + bp(noise, 2500, 9000) * x + tone) * x ** 2 * np.clip((d - t) / 0.01, 0, 1), 0.7)
def impact():
    """a soft impact: low sine falling in pitch, a puff of low noise"""
    n = int(0.9 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(45 + 65 * np.exp(-t * 7)) / SR) * np.exp(-t * 5)
    return pk((body + lp(rng.standard_normal(n), 300) * np.exp(-t * 12) * 3) * np.clip(t / 0.004, 0, 1), 0.8)
def thud():
    n = int(0.4 * SR); t = np.arange(n) / SR
    return pk(np.sin(2 * np.pi * np.cumsum(38 + 45 * np.exp(-t * 30)) / SR) * np.exp(-t * 14) + lp(rng.standard_normal(n), 800) * np.exp(-t * 90) * 0.5, 0.9)
def paper():
    """paper rustle: noisy crackle in sparse little bursts"""
    n = int(0.5 * SR); t = np.arange(n) / SR; env = np.zeros(n)
    for c in rng.uniform(0, 0.45, 26):
        i = int(c * SR); m = min(n - i, int(0.03 * SR)); env[i:i + m] += rng.uniform(0.3, 1.0) * np.exp(-np.arange(m) / SR * 110)
    return pk(bp(rng.standard_normal(n), 2000, 9000) * np.minimum(env, 1.2) * np.sin(np.pi * t / 0.5) ** 0.5, 0.6)
def pencil(d=0.55):
    """a pencil writing on paper: uneven strokes (no steady flutter: a fixed rate sounds like a rattle), graphite grain
    as dense tiny ticks on soft friction noise, up-strokes a little brighter than down-strokes"""
    n = int(d * SR); out = np.zeros(n); i, up = int(rng.uniform(0, 0.02) * SR), False
    while i < n:
        m = min(n - i, int(rng.uniform(0.06, 0.15) * SR)); t = np.arange(m) / SR
        grain = (rng.random(m) < rng.uniform(0.04, 0.09)) * rng.uniform(0.3, 1.0, m)  # graphite catching on the fibres
        lo, hi = (2200, 7000) if up else (1200, 4500)
        body = bp(grain + 0.35 * rng.standard_normal(m), lo, hi)
        env = np.minimum(1, t / 0.006) * np.minimum(1, (m / SR - t) / 0.02) * (0.7 + 0.3 * rng.uniform() * np.sin(np.pi * t / max(t[-1], 1e-3)))
        out[i:i + m] += body * env * rng.uniform(0.6, 1.0)
        i += m + int(rng.uniform(0.012, 0.05) * SR); up = not up
    return pk(out, 0.5)
def scatter():
    """things falling apart: little clatter hits, dense at first, then fewer and quieter"""
    n = int(0.9 * SR); out = np.zeros(n)
    for i, c in enumerate(np.sort(rng.uniform(0, 1, 16)) ** 1.6 * 0.6):
        m = int(0.15 * SR); t = np.arange(m) / SR; f = rng.uniform(700, 3800)
        hit = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t * rng.uniform(50, 200)) + rng.standard_normal(m) * np.exp(-t * 500) * 0.5
        s = int(c * SR); out[s:s + m] += hit * rng.uniform(0.4, 1.0) * (1 - 0.6 * i / 16)
    return pk(out, 0.7)
def roar(d=1.2):
    """a cartoon dinosaur roar: a rising, falling growl (saw, 30 Hz amplitude wobble) shaped by an open-to-closed mouth"""
    n = int(d * SR); t = np.arange(n) / SR; x = t / d
    f0 = np.interp(x, [0, 0.08, 0.3, 0.7, 1], [70, 120, 170, 110, 55]) * (1 + 0.04 * np.sin(2 * np.pi * 5.5 * t)) * (1 + 0.05 * lp(rng.standard_normal(n), 25) / 0.3)
    src = 2 * (np.cumsum(f0) / SR % 1.0) - 1 + rng.standard_normal(n) * 0.12
    mouth = bp(src, 200, 600) * (0.5 + 0.5 * x) + bp(src, 600, 1400) * (1.2 * (1 - x) + 0.2) + bp(src, 1400, 3200) * 0.5 * (1 - x)
    env = np.clip(t / 0.05, 0, 1) * np.exp(-np.maximum(t - 0.35, 0) * 2.2) * np.clip((d - t) / 0.15, 0, 1)
    return pk(np.tanh(2.5 * pk(mouth, 1.0) * (0.65 + 0.35 * np.sin(2 * np.pi * 30 * t)) * env), 0.8)

sfx = np.zeros(int(total * SR) + SR * 2)
def put(t, sig, g=1.0):
    s = max(0, int(t * SR)); e = min(len(sfx), s + len(sig)); sfx[s:e] += sig[:e - s] * g

def put2(t, sig, g=1.0):  # put() that keeps the sound's own start when it begins before 0
    s = round(t * SR); a = max(0, -s); e = min(len(sfx), s + len(sig))
    if e > s + a: sfx[s + a:e] += sig[a:e - s] * g
vr = np.random.default_rng(11)  # v2 variation (pitch, level), apart from rng so the classic draws stay as they were
def maxim_ticks(sp, dur):
    """per letter of a "maxim" card: when it is typed (= gfx/maxim_lib.mjs wordTimes + charTimes; stars removed as maximWords does)"""
    words = [w.replace("*", "") for w in ("" if sp.get("text") is None else str(sp["text"])).split() if set(w) != {"*"}]
    at, latest = sp.get("at"), max(0.0, dur - 0.3)  # LAST_SHOWN
    if isinstance(at, list) and len(at) == len(words) and all(type(x) in (int, float) and np.isfinite(x) for x in at):
        times, prev = [], 0.0
        for x in at: prev = max(prev, min(max(0.0, x), latest)); times.append(prev)
    else:
        lens = [len(w) + 1 for w in words]; total_l = sum(lens) or 1; span = max(0.0, min(dur * 0.6 - 0.25, total_l * 0.05))  # TYPE_START, CHAR_EVEN
        times, cum = [], 0
        for ln in lens: times.append(0.25 + span * cum / total_l); cum += ln
    out = []
    for i, w in enumerate(words):
        step = min(0.045, max(0.0, (times[i + 1] if i + 1 < len(times) else dur) - times[i]) / max(1, len(w)))  # CHAR_MAX
        out += [times[i] + j * step for j in range(len(w))]
    return out
def card_v2(o, sp, ty):
    at = o["at"]; dur = sp.get("dur", o["dur"]) if type(sp.get("dur", o["dur"])) in (int, float) else o["dur"]
    if ty in ("kw", "count", "lower"): put2(at + 0.03, pop(2 ** (vr.uniform(-1.2, 1.2) / 12)), 0.8 * vr.uniform(0.88, 1.0))
    if ty == "count":  # ticks rise while the digits count (gfx/count_lib.mjs countSeconds, starting COUNT_DELAY after the card)
        cs = max(0.0, min(1.6, dur * 0.4, dur - 0.8)); k = min(32, int(cs / 0.05))
        for i in range(k): put2(at + 0.35 + cs * i / k, click(1 + i / max(1, k)), 0.12 + 0.2 * i / max(1, k))
    if ty == "list":
        put2(at, swoosh(0.45), 0.4)
        for dl in sp.get("delays", []):
            if type(dl) in (int, float) and np.isfinite(dl):
                put2(at + dl - 0.05, swoosh(0.16), 0.2); put2(at + dl, click(2 ** (vr.uniform(-1, 1) / 12)), 0.5)
    if ty == "chap": put2(at - 0.9, riser(0.9), 0.55); put2(at, impact(), 0.7)
    if ty in ("slide", "web"): put2(at - 0.3, whoosh(0.8), 0.9)
    if ty == "end": put2(at - 0.3, whoosh(0.9, False), 0.8)
    if ty == "cta": put2(at + 0.1, ding(), 0.6)
    if ty == "maxim":  # a soft key press per letter, under the voice; no whoosh. ("float": only its own "sfx" moments)
        for t in maxim_ticks(sp, dur): put2(at + t, keytick(2 ** (vr.uniform(-2, 2) / 12)), 0.2 * vr.uniform(0.6, 1.0))

for o in edl.get("overlays", []):
    sp = specs.get(o["id"], {}); ty = sp.get("type")
    if v2:
        card_v2(o, sp, ty)
        continue
    if ty in ("kw", "count", "lower"): put(o["at"] + 0.03, pop(), 0.8)
    if ty == "list":
        put(o["at"], whoosh(0.5), 0.5)
        for dl in sp.get("delays", []): put(o["at"] + dl + 0.05, pop(), 0.7)
    if ty in ("chap", "slide", "web"): put(o["at"] - 0.3, whoosh(0.8), 0.9)  # = gfx_types.CARD_WHOOSH
    if ty == "end": put(o["at"] - 0.3, whoosh(0.9, False), 0.8)
    if ty == "cta": put(o["at"] + 0.1, ding(), 0.6)
    if ty == "maxim": put(o["at"] - 0.1, whoosh(0.45), 0.45)  # the sentence comes in softly; its own moments via "sfx"
acc = 0.0
for s in segs:
    z = s.get("zoom")
    # emphasis punch-in; with an editing grammar (beat_fx) punches are silent unless their moment asks for a sound
    if "beat_fx" not in edl and isinstance(z, dict) and z["t0"] > 0.01 and z["b"] > z["a"] + 0.1:
        put(acc + z["t0"] - 0.05, whoosh(0.35), 0.35)
    acc += s["out"] - s["in"]
BEAT_SFX = {"pop": lambda: (pop(), 0.7, 0.0), "whoosh": lambda: (whoosh(0.35), 0.35, -0.05), "ding": lambda: (ding(), 0.5, 0.0)}
for r in edl.get("beat_fx", []):
    if r.get("fx") == "punch" and r.get("sfx") in BEAT_SFX:
        sig, g, dt = BEAT_SFX[r["sfx"]]()
        put(r["at"] + dt, sig, g)
# a card's own moments (spec "sfx": [[t, name], ...], t from the card's start): items popping in, pen strokes, the key fact
def pen_sfx():  # a card sound only, not an editing-grammar moment sound (those are BEAT_SFX)
    return pen(), 0.6, 0.0
def sfx_of(fn, g, dt=0.0):  # a card sound for CARD_SFX
    return lambda: (fn(), g, dt)
CARD_SFX = {**BEAT_SFX, "pen": pen_sfx, "pencil": sfx_of(pencil, 0.5), "tick": sfx_of(keytick, 0.4), "type": sfx_of(typing, 0.4), "click": sfx_of(click, 0.5), "riser": sfx_of(riser, 0.55), "impact": sfx_of(impact, 0.7), "paper": sfx_of(paper, 0.6), "scatter": sfx_of(scatter, 0.6), "roar": sfx_of(roar, 0.8), "swoosh": sfx_of(swoosh, 0.45), "drop": sfx_of(thud, 0.8)}
for o in edl.get("overlays", []):
    for e in specs.get(o["id"], {}).get("sfx") or []:  # a malformed entry is skipped: a sound never stops the render
        if isinstance(e, list) and len(e) == 2 and isinstance(e[0], (int, float)) and np.isfinite(e[0]) and isinstance(e[1], str) and e[1] in CARD_SFX:
            sig, g, dt = CARD_SFX[e[1]]()
            put(o["at"] + e[0] + dt, sig, g)

sfx /= max(1e-9, np.abs(sfx).max()) / 0.8
d16 = (np.stack([sfx, sfx], 1) * 32767).astype(np.int16)
with wave.open(os.path.join(od, "sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d16.tobytes())
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "gen_music.py"), os.path.join(od, "music.wav"), f"{total + 1:.2f}",
                str(edl.get("music_seed", 7)), *([json.dumps(moods)] if moods else [])], check=True)
edl["music"] = os.path.join(od, "music.wav"); edl["sfx"] = os.path.join(od, "sfx.wav")
Path(edl_p).write_text(json.dumps(edl, indent=1, ensure_ascii=False))
print("beds ok", round(total, 1))
