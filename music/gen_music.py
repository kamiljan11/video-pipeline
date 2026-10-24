#!/usr/bin/env python3
"""gen_music.py out.wav seconds [seed]
Original, self-generated background bed (our own synthesis = nothing for Content ID to match).
Calm, slightly uplifting: 92 BPM, Am-F-C-G, soft pads, pluck arpeggio, sub bass, light kick + shaker.
Optional 4th arg: JSON [[t, mood], ...] (tension/story/upbeat/resolve/drop) = the same grid, sections crossfaded by mood."""
import json
import sys
import wave

import numpy as np

SR = 44100
out, secs = sys.argv[1], float(sys.argv[2]); rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 7)
BPM = 92; beat = 60 / BPM; bar = 4 * beat
N = int(secs * SR) + SR * 6
L = np.zeros(N); R = np.zeros(N)
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
prog = [(57, [0, 3, 7, 10]), (53, [0, 4, 7, 11]), (48, [0, 4, 7, 14]), (55, [0, 4, 7, 9])]

def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x))

def saw(freq, n, phase=0.0):
    t = (np.arange(n) / SR * freq + phase) % 1.0
    return 2 * t - 1

def add(buf, start, sig):
    s = int(start * SR); e = min(len(buf), s + len(sig))
    if s < len(buf): buf[s:e] += sig[:e - s]

ir_n = int(2.2 * SR); ti = np.arange(ir_n) / SR
def verb(x, seed):
    ir = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-ti * 3.2)
    ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    m = len(x) + ir_n; nf = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:len(x)]

# --- moods (4th arg: JSON [[t, mood], ...]): same 92 BPM grid and chord blocks, one render per section, crossfaded ---
MOODS = ("tension", "story", "upbeat", "resolve", "drop")
XF, XF_OUT, XF_IN = 1.5, 0.3, 0.6  # crossfade; into a "drop" (fast) and back out of it
MOOD_GAIN = {"tension": 1.14, "story": 2.25, "upbeat": 1.15, "resolve": 1.2}  # measured: every mood renders at RMS ~0.085 (the plain bed: 0.09)
PROG_T = [(57, [0, 3, 7, 10]), (57, [0, 3, 6, 10]), (53, [0, 3, 7, 10]), (56, [0, 3, 7, 10])]  # minor, dark, over an A pedal
PROG_R = [(48, [0, 4, 7, 14]), (55, [0, 4, 7, 11]), (53, [0, 4, 7, 14]), (48, [0, 4, 7, 11])]  # C G F C: the lift

def m_pad(root, iv, r, fc, gain, dur, att):
    n = int((dur + 1.5) * SR); tt = np.arange(n) / SR
    env = np.clip(tt / att, 0, 1) * np.clip((dur + 1.5 - tt) / 1.5, 0, 1)
    pad = np.zeros(n)
    for i in iv:
        for d in (-0.07, 0.0, 0.07): pad += saw(mtof(root + i) * 2 ** (d / 12), n, r.random())
    return lp(pad, fc) * env * gain
def m_tone(f, dur, decay, gain, parts=((1, 1.0),), att=0.004):
    t = np.arange(int(dur * SR)) / SR
    return sum(np.sin(2 * np.pi * f * k * t) * a * np.exp(-t * decay * (1 + 0.5 * i)) for i, (k, a) in enumerate(parts)) * np.clip(t / att, 0, 1) * gain
def m_kick(gain, depth=30):
    t = np.arange(int(0.35 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-t * depth)) / SR) * np.exp(-t * 9) * gain
def m_noise(r, d, lo, hi, decay, gain):
    t = np.arange(int(d * SR)) / SR
    x = r.standard_normal(len(t)); x = lp(x, hi) - lp(x, lo)
    return x * np.exp(-t * decay) * gain

def mood_window(mood, w0, w1, seed):
    """one mood for the window [w0, w1] s (absolute time, so the grid is shared) -> (L, R); pad/verb are not cut at the edges: the caller fades"""
    n = max(1, round((w1 - w0) * SR)); L = np.zeros(n); R = np.zeros(n); mi = MOODS.index(mood)
    def put(t, sig, pan=0.5, g=1.0):
        s = round((t - w0) * SR); a = max(0, -s); e = min(len(sig), n - s)
        if e > a: L[s + a:s + e] += sig[a:e] * g * 2 * (1 - pan); R[s + a:s + e] += sig[a:e] * g * 2 * pan
    for b in range(max(0, int(w0 // bar) - 4), int(w1 // bar) + 2):
        r = np.random.default_rng([seed, mi, b]); tb = b * bar
        ch = (b // 2) % 4
        if b % 2 == 0:  # chord block = 2 bars
            if mood == "tension": root, iv = PROG_T[ch]; put(tb, m_pad(root - 12, iv, r, 600, 0.030, 2 * bar, 1.4))
            elif mood == "story": root, iv = prog[ch]; put(tb, m_pad(root + 12, iv, r, 1000, 0.017, 2 * bar, 1.8))
            elif mood == "upbeat": root, iv = prog[ch]; put(tb, m_pad(root + 12, iv, r, 2400, 0.014, 2 * bar, 0.6))
            else:
                root, iv = PROG_R[ch]; put(tb, m_pad(root + 12, iv, r, 1500, 0.020, 2 * bar, 1.0)); put(tb, m_pad(root, iv[:3], r, 700, 0.020, 2 * bar, 1.0))
        root, iv = {"tension": PROG_T, "resolve": PROG_R}.get(mood, prog)[ch]
        if mood == "tension":
            for e in range(8):  # pulsing low pedal on A
                put(tb + e * beat / 2, m_tone(mtof(36), 0.3, 9, 0.11 * (1.0 if e % 2 == 0 else 0.55), ((1, 1.0), (2, 0.3))), 0.5)
            put(tb, m_kick(0.14, 25), 0.5)  # sparse: a heartbeat, one tom, one rim click
            if b % 2: put(tb + 2.5 * beat, m_kick(0.08, 25), 0.5)
            if b % 4 == 3: put(tb + 2 * beat, m_tone(95, 0.35, 9, 0.10, ((1, 1.0), (1.5, 0.2))), 0.4)
            if b % 2 == 0: put(tb + 3.5 * beat, m_noise(r, 0.05, 2500, 8000, 80, 0.03), 0.6)
            if r.random() < 0.5:  # a lone high ping, a minor ninth off the chord
                put(tb + r.integers(0, 8) * beat / 2, m_tone(mtof(root + 24 + iv[int(r.integers(0, len(iv)))]), 1.8, 2.5, 0.03, ((1, 1.0), (2.76, 0.2))), r.random())
        elif mood == "story":
            for q in range(4):  # soft piano-ish notes, about half of the beats
                if r.random() < 0.5:
                    f = mtof(root + (12 if q % 2 else 24) + iv[int(r.integers(0, len(iv)))])
                    put(tb + q * beat + 0.02 * r.random(), m_tone(f, 2.0, 2.4, 0.055 + 0.02 * r.random(), ((1, 1.0), (2, 0.4), (3, 0.12))), 0.3 + 0.4 * r.random())
            if b % 2 == 0: put(tb, m_tone(mtof(root + 12), 2.4, 1.6, 0.05, ((1, 1.0), (2, 0.3))), 0.5)
        elif mood == "upbeat":
            for e in range(8):
                put(tb + e * beat / 2, m_tone(mtof(root - 12 + (12 if e % 4 == 3 else 0)), 0.3, 7, 0.12, ((1, 1.0), (2, 0.25))), 0.5)
                f = mtof(root + 24 + iv[[0, 2, 1, 3, 2, 1, 3, 2][e] % len(iv)])
                if r.random() > 0.05: put(tb + e * beat / 2, m_tone(f, 0.6, 7, 0.05, ((1, 1.0), (2, 0.45))), 0.5 + 0.35 * np.sin(e * 0.9))
            for q in range(4):
                if q in (0, 2): put(tb + q * beat, m_kick(0.19), 0.5)
                else: put(tb + q * beat, m_noise(r, 0.16, 1500, 7000, 24, 0.10) + m_tone(190, 0.16, 30, 0.07), 0.5)
                for h in (0, 0.5): put(tb + (q + h) * beat, m_noise(r, 0.05, 6000, 14000, 70, 0.022 if h == 0 else 0.034), 0.45 + 0.1 * h)
        else:  # resolve: bells climbing the chord, long warm bass, a soft kick
            put(tb, m_tone(mtof(root - 12), 2.4, 1.4, 0.10, ((1, 1.0), (2, 0.3))), 0.5)
            for q in range(4):
                put(tb + q * beat, m_tone(mtof(root + 12 + iv[q % len(iv)] + (12 if q > 1 else 0)), 1.6, 3, 0.05, ((1, 1.0), (2.76, 0.18), (5.4, 0.06))), 0.3 + 0.13 * q)
            for q in (0, 2): put(tb + q * beat, m_kick(0.085, 20), 0.5)
    ir = lambda x, k: x + 0.35 * verb(x, k)
    return ir(L, 1), ir(R, 2)

def parse_moods(raw):
    try: mm = json.loads(raw)
    except ValueError: sys.exit(f"music_moods: not JSON: {raw[:60]!r}")
    if not isinstance(mm, list) or not mm: sys.exit("music_moods: [[seconds, mood], ...], at least one pair")
    prev = -1.0
    for e in mm:
        if not (isinstance(e, list) and len(e) == 2 and type(e[0]) in (int, float) and np.isfinite(e[0]) and e[0] >= 0 and e[1] in MOODS):
            sys.exit(f"music_moods: each entry [seconds >= 0, one of {'/'.join(MOODS)}], got {e!r}")
        if e[0] <= prev: sys.exit(f"music_moods: times must increase, got {e[0]} after {prev}")
        prev = e[0]
    return [(0.0 if i == 0 else float(t), m) for i, (t, m) in enumerate(mm)]

def moods_track(mm, secs, seed):
    n = int(secs * SR); L = np.zeros(n); R = np.zeros(n); t = np.arange(n) / SR
    def width(a, b): return XF_OUT if b == "drop" else XF_IN if a == "drop" else XF  # boundary between sections a -> b
    for k, (s, mood) in enumerate(mm):
        if mood == "drop": continue
        e = mm[k + 1][0] if k + 1 < len(mm) else secs + 10
        wi = width(mm[k - 1][1], mood) if k else 0.0; wo = width(mood, mm[k + 1][1]) if k + 1 < len(mm) else 0.0
        g = np.ones(n)
        if wi: g *= np.sin(np.clip((t - (s - wi / 2)) / wi, 0, 1) * np.pi / 2)  # equal-power
        if wo: g *= np.cos(np.clip((t - (e - wo / 2)) / wo, 0, 1) * np.pi / 2)
        lo = int(max(0.0, s - wi / 2 - 2 * bar) * SR); z = min(secs, e + wo / 2)
        if z <= lo / SR: continue
        wl, wr = mood_window(mood, lo / SR, z, seed)
        m = min(len(wl), n - lo)
        L[lo:lo + m] += wl[:m] * g[lo:lo + m] * MOOD_GAIN[mood]; R[lo:lo + m] += wr[:m] * g[lo:lo + m] * MOOD_GAIN[mood]
    return L, R

if len(sys.argv) > 4:  # moods: a separate render path; without the 4th argument the bed below is unchanged
    mm = parse_moods(sys.argv[4])
    L, R = moods_track(mm, secs, int(sys.argv[3]) if len(sys.argv) > 3 else 7)
    fi, fo = min(int(1.5 * SR), len(L) // 2), min(3 * SR, len(L) // 2)  # a hook starts with the music, not 3 s later
    for ch in (L, R):
        ch[:fi] *= np.linspace(0, 1, fi); ch[-fo:] *= np.linspace(1, 0, fo)
    peak = max(np.abs(L).max(), np.abs(R).max())
    if peak > 0.9: L, R = L / peak * 0.9, R / peak * 0.9
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
    print("music", out, round(secs, 1), "s,", len(mm), "mood sections")
    sys.exit(0)

total_bars = int(secs / bar) + 2
for b in range(0, total_bars, 2):
    root, iv = prog[(b // 2) % 4]
    t0 = b * bar; dur = 2 * bar
    n = int((dur + 1.5) * SR); tt = np.arange(n) / SR
    env = np.clip(tt / 1.2, 0, 1) * np.clip((dur + 1.5 - tt) / 1.5, 0, 1)
    pad = np.zeros(n)
    for i in iv:
        f = mtof(root + 12 + i)
        for d in (-0.07, 0.0, 0.07):
            pad += saw(f * 2 ** (d / 12), n, rng.random())
    pad = lp(pad, 900) * env * 0.022
    add(L, t0, pad * 0.9); add(R, t0, pad * 1.1)
    for q in range(0, 8, 2):
        nb = int(beat * 1.8 * SR); tb = np.arange(nb) / SR
        bs = np.sin(2 * np.pi * mtof(root - 12) * tb) * np.exp(-tb * 2.2) * np.clip(tb / 0.01, 0, 1) * 0.10
        add(L, t0 + q * beat, bs); add(R, t0 + q * beat, bs)
    pat = [0, 2, 1, 3, 2, 1, 3, 2]
    for e8 in range(16):
        if rng.random() < 0.18: continue
        i = iv[pat[e8 % 8] % len(iv)]; f = mtof(root + 24 + i)
        npl = int(0.7 * SR); tp = np.arange(npl) / SR
        pl = (np.sin(2 * np.pi * f * tp) + 0.25 * np.sin(4 * np.pi * f * tp)) * np.exp(-tp * 6) * np.clip(tp / 0.004, 0, 1) * 0.045
        pan = 0.5 + 0.35 * np.sin(e8 * 0.9)
        add(L, t0 + e8 * beat / 2, pl * (1 - pan) * 2); add(R, t0 + e8 * beat / 2, pl * pan * 2)

for b in range(4, total_bars):
    if b % 16 in (14, 15): continue
    for q in range(4):
        tq = b * bar + q * beat
        if q in (0, 2):
            nk = int(0.35 * SR); tk = np.arange(nk) / SR
            fk = 45 + 70 * np.exp(-tk * 30)
            kick = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk * 9) * 0.16
            add(L, tq, kick); add(R, tq, kick)
        for h in (0, 0.5):
            nh = int(0.06 * SR); noise = rng.standard_normal(nh)
            noise = noise - lp(noise, 6000)
            sh = noise * np.exp(-np.arange(nh) / SR * 60) * (0.018 if h == 0 else 0.028)
            add(L, tq + h * beat, sh * 0.8); add(R, tq + h * beat, sh * 1.2)

L = L + 0.35 * verb(L, 1); R = R + 0.35 * verb(R, 2)
n = int(secs * SR); L, R = L[:n], R[:n]
fade = int(3 * SR); ramp = np.linspace(0, 1, fade)
for ch in (L, R):
    ch[:fade] *= ramp; ch[-fade:] *= ramp[::-1]
peak = max(np.abs(L).max(), np.abs(R).max()); L, R = L / peak * 0.7, R / peak * 0.7
data = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print("music", out, round(secs, 1), "s")
