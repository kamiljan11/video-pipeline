#!/usr/bin/env python3
"""word_times: word start times that sit on the voice, not where whisper guessed.

Every card, scene beat, subtitle, punch-in and cut point is timed from the word list (x.cw.json). whisper.cpp's own
segment times missed the voice onset by more than 150 ms on 29 % of the words after a pause on film 2026-11-04
(worst 1.07 s); its DTW token times (flash attention OFF, or whisper silently disables DTW) had no miss over 210 ms.
Kamil 2026-11-08: "do 1:27 sporo spoznien w roznym miejscu".

    python3 word_times.py refine <words.cw.json> <dtw.cw.json> <audio.wav> [--out new.cw.json]
        keep the text of <words> (hand fixes stay), take each word's start from <dtw> where the same word matches in
        order, then snap starts after a pause to the voice onset; prints how far the starts moved
    python3 word_times.py error <words.cw.json> <audio.wav>
        how far word starts sit from the voice onsets (p10 / median / p90, share over 150 ms)
"""
import difflib
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np

HOP = 0.01  # s per energy frame
QUIET = 0.15  # s of quiet before an onset
SNAP_EARLY, SNAP_LATE = 0.25, 0.10  # an onset this far before / after a word start pulls the start onto it


def load(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["transcription"]


def save(words: list[dict], path: str) -> None:
    Path(path).write_text(json.dumps({"transcription": words}, ensure_ascii=False), encoding="utf-8")


def dtw_start_ms(item: dict, chunk_off_ms: int = 0) -> int | None:
    """start of one whisper word (-ml 1 -sow -ojf) from its first real token's DTW time, in ms; None without DTW"""
    for t in item.get("tokens", []):
        if t.get("text", "").startswith("[_") or not t.get("text", "").strip(): continue
        if t.get("t_dtw", -1) >= 0: return chunk_off_ms + int(t["t_dtw"]) * 10
        return None
    return None


def onsets(wav: str) -> np.ndarray:
    """voice onsets in s: a voiced 10 ms frame after QUIET s of unvoiced ones (noise floor + 18 dB)"""
    with wave.open(wav) as wf:
        sr, ch = wf.getframerate(), wf.getnchannels()
        if wf.getsampwidth() != 2: raise ValueError(f"{wav}: want 16-bit PCM")
        a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32)
    a = a.reshape(-1, ch).mean(1); hop = int(sr * HOP); n = len(a) // hop
    if n < 20: return np.array([])
    db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    voiced = db > np.percentile(db, 20) + 18
    q = int(QUIET / HOP)
    idx = [i for i in range(q, n) if voiced[i] and not voiced[i - q:i].any()]
    return np.array(idx, dtype=float) * HOP


def norm(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())


def transfer(words: list[dict], dtw: list[dict]) -> int:
    """starts of `dtw` onto the same words of `words` (matched in order by normalized text); returns how many moved.
    A word keeps its old start when no match, or when the match is over 1.5 s away (a different occurrence)."""
    a, b = [norm(w["text"]) for w in words], [norm(w["text"]) for w in dtw]
    moved = 0
    for tag, i1, i2, j1, _ in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal": continue
        for k in range(i2 - i1):
            w, d = words[i1 + k], dtw[j1 + k]
            s = d["offsets"]["from"]
            if abs(s - w["offsets"]["from"]) > 1500 or not a[i1 + k]: continue
            if s != w["offsets"]["from"]: moved += 1
            w["offsets"]["from"] = s
            w["offsets"]["to"] = max(w["offsets"]["to"], s + 40)
    return moved


def snap(words: list[dict], on: np.ndarray) -> int:
    """a word start after a pause goes onto the voice onset near it; never before the previous word's end"""
    if not on.size: return 0
    snapped = 0
    for i, w in enumerate(words):
        s = w["offsets"]["from"] / 1000
        prev_end = words[i - 1]["offsets"]["to"] / 1000 if i else 0.0
        if s - prev_end < QUIET: continue  # inside a phrase: energy says nothing about this word
        j = int(np.abs(on - s).argmin()); o = float(on[j])
        if -SNAP_EARLY <= o - s <= SNAP_LATE and o > prev_end:
            w["offsets"]["from"] = round(o * 1000); w["offsets"]["to"] = max(w["offsets"]["to"], w["offsets"]["from"] + 40)
            snapped += 1
    return snapped


def error(words: list[dict], on: np.ndarray) -> dict:
    """for each voice onset: the nearest word start minus the onset (s), within 1.5 s"""
    st = np.array([w["offsets"]["from"] / 1000 for w in words if w["text"].strip()])
    if not st.size or not on.size: return {"n": 0}
    e = np.array([st[np.abs(st - o).argmin()] - o for o in on]); e = e[np.abs(e) < 1.5]
    return {"n": len(e), "p10_ms": round(float(np.percentile(e, 10)) * 1000), "median_ms": round(float(np.median(e)) * 1000),
            "p90_ms": round(float(np.percentile(e, 90)) * 1000), "over_150ms_pct": round(float((np.abs(e) > 0.15).mean()) * 100, 1)}


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "error":
        print(json.dumps(error(load(argv[1]), onsets(argv[2])))); return 0
    if len(argv) >= 4 and argv[0] == "refine":
        out = argv[argv.index("--out") + 1] if "--out" in argv else argv[1]
        words, on = load(argv[1]), onsets(argv[3])
        before = error(words, on)
        moved = transfer(words, load(argv[2])); snapped = snap(words, on)
        save(words, out)
        print(json.dumps({"words": len(words), "dtw_moved": moved, "snapped": snapped, "before": before, "after": error(words, on), "out": out}))
        return 0
    print(__doc__, file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
