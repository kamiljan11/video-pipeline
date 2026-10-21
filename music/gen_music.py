#!/usr/bin/env python3
"""gen_music.py out.wav seconds [seed]
Original, self-generated background bed (our own synthesis = nothing for Content ID to match).
Calm, slightly uplifting: 92 BPM, Am-F-C-G, soft pads, pluck arpeggio, sub bass, light kick + shaker."""
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

ir_n = int(2.2 * SR); ti = np.arange(ir_n) / SR
def verb(x, seed):
    ir = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-ti * 3.2)
    ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    m = len(x) + ir_n; nf = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:len(x)]
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
