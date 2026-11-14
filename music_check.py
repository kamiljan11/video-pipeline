#!/usr/bin/env python3
"""music_check.py <assemble.audio.args.json> — the music is heard: under the voice, not under the floor.

Kamil 2026-11-14 on the fragment test: "muzyka tech chyba w tle nie gra". Measured on the fragment's own audio graph
(words_check.stems: the voice and the bed rendered apart): with music_duck threshold 0.004 / ratio 8 the bed sat at
-64 dBFS under speech, 48 dB under the voice (median); only the pauses (5 % of the film) had it at -32 dBFS. Nothing
judged that: words_check only asks the voice to stay >= 10 dB over the bed.

Gate: the median of voice minus bed over the 0.3 s windows with speech lies in [MIN_DB, MAX_DB]. Below MIN_DB the music
fights the words; above MAX_DB it is not heard. Same fragment, threshold 0.04 / ratio 2.5 / music_db -9: 22.7 dB, 5th
percentile 11.5 dB, 3.7 % of speech windows under 10 dB. Exit 1 = out of the range (named), 2 = could not measure.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import words_check

MIN_DB, MAX_DB = 14.0, 28.0  # voice over the bed while he speaks (median); dialogue mixes keep the bed roughly 15-25 dB under
SPEECH_DB = -35.0            # a 0.3 s voice window louder than this holds speech (words_check.voice_over_bed uses the same)


def measure(voice: np.ndarray, bed: np.ndarray, sr: int) -> dict:
    """median voice-minus-bed under speech, the bed's median level under speech and in pauses (dBFS)"""
    w = int(0.3 * sr)
    vd = np.array([words_check._db(voice[s:s + w]) for s in range(0, len(voice) - w, w)])
    bd = np.array([words_check._db(bed[s:s + w]) for s in range(0, len(voice) - w, w)])
    sp, pa = vd > SPEECH_DB, vd < -50
    if not sp.any(): return {}
    out = {"over": float(np.median(vd[sp] - bd[sp])), "bed_speech": float(np.median(bd[sp])), "speech_windows": int(sp.sum())}
    if pa.any(): out["bed_pause"] = float(np.median(bd[pa]))
    return out


def judge(m: dict) -> str:
    """"" when the music sits in the range, else why"""
    if not m: return "no speech measured"
    if m["over"] > MAX_DB: return f"music not heard: the voice is {m['over']:.1f} dB over it (max {MAX_DB:g}); raise music_db or ease music_duck"
    if m["over"] < MIN_DB: return f"music too loud: the voice is only {m['over']:.1f} dB over it (min {MIN_DB:g}); lower music_db or duck deeper"
    return ""


def main(argv: list[str]) -> int:
    if len(argv) != 1: print(__doc__, file=sys.stderr); return 2
    st = words_check.stems(Path(argv[0]))
    if st is None: print(f"music_check: FAILED to measure (no stems from {argv[0]})"); return 2
    m = measure(*st, words_check.SR)
    why = judge(m)
    shown = ", ".join(f"{k} {v:.1f}" if isinstance(v, float) else f"{k} {v}" for k, v in m.items())
    print(f"music_check: {shown}: {'FAIL ' + why if why else 'OK'}")
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
