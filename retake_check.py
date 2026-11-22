#!/usr/bin/env python3
"""retake_check.py <media> <plan.json> — a retake the CUT kept, heard in the cut itself, utterance by utterance.

Kamil 2026-11-14 on the fragment test (out/long.mp4 at 1:00): "jest dwa razy powtorzenie bo sie pomylilem i zle obciete".
The source transcript (whisper over the whole recording) had only one of the two takes, so the cut (built on its words)
and film_check long.retakes (reading the same words) could not see the other; whisper over the whole cut (words_check)
dropped it too, also with --max-context 0. Measured: whisper over each pause-separated utterance hears both takes
("z jednej aplikacji po usunieciu profilu" 59.4 s, "no i przyklad w jednej aplikacji po usunieciu profilu" 63.1 s).

So: silences of the cut (ffmpeg silencedetect) -> utterances (pieces of speech, short ones joined up to MERGE_S) -> one
whisper-cli run over all of them -> (utterance start, word) -> retakes.problems (the same n words within WINDOW s; a
repeat on purpose is named in plan "retakes_ok"). Exit 1 = a retake, named with its film times; 2 = could not measure.
run_v4.sh runs it on the dry run's rough cut (the final render has the same cut: dry_run.py digests plan + EDL).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import retakes
from cpu_budget import heavy_threads, low_priority

W = str(Path(__file__).resolve().parent)
NOISE_DB, PAUSE_S = -35, 0.25   # a pause between utterances: quieter than NOISE_DB for PAUSE_S (measured on the fragment)
MERGE_S, MIN_S = 3.0, 0.15      # utterances shorter than MERGE_S join the previous one; blips under MIN_S are not speech
WINDOW = 20.0                   # film seconds between two takes (film_check long.retakes uses the same)


def utterances(silences: list[tuple[str, float]], length: float) -> list[tuple[float, float]]:
    """speech spans between the silences ("start"/"end" events in order), short ones joined to the previous one"""
    spans, start = [], 0.0
    for kind, t in silences:
        if kind == "start": spans.append((start, t))
        else: start = t
    spans.append((start, length))
    out: list[tuple[float, float]] = []
    for a, b in spans:
        if b - a < MIN_S: continue
        if out and b - out[-1][0] < MERGE_S: out[-1] = (out[-1][0], b)
        else: out.append((a, b))
    return out


def timed_words(spans: list[tuple[float, float]], texts: list[str]) -> list[tuple[float, str]]:
    """(time, word): each word at its utterance start plus its share of the utterance (whisper's text has no times)"""
    out = []
    for (a, b), text in zip(spans, texts):
        ws = text.split()
        out += [(a + (b - a) * i / max(len(ws), 1), w) for i, w in enumerate(ws)]
    return out


def silences(wav: str) -> list[tuple[str, float]]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", wav, "-af", f"silencedetect=noise={NOISE_DB}dB:d={PAUSE_S}", "-f", "null", "-"],
                       capture_output=True, text=True, check=True, timeout=600)
    return [(m.group(1), float(m.group(2))) for m in re.finditer(r"silence_(start|end): ([0-9.]+)", r.stderr)]


def hear(media: str) -> list[tuple[float, str]]:
    with tempfile.TemporaryDirectory(prefix="retake-") as d:
        wav = f"{d}/a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", wav], check=True, timeout=1800)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                                   capture_output=True, text=True, check=True, timeout=60).stdout)
        spans = utterances(silences(wav), dur)
        files = []
        for i, (a, b) in enumerate(spans):
            f = f"{d}/{i:04d}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, a - 0.1):.3f}", "-to", f"{b + 0.15:.3f}", "-i", wav, f],
                           check=True, timeout=120)
            files += ["-f", f]
        subprocess.run([f"{W}/whisper.cpp/build/bin/whisper-cli", "-m", f"{W}/models/ggml-large-v3-q5_0.bin", "-l", "pl",
                        "-t", str(heavy_threads()), "-nt", "-otxt", *files], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=True, preexec_fn=low_priority, timeout=7200)
        texts = [Path(f"{d}/{i:04d}.wav.txt").read_text(encoding="utf-8").replace("\n", " ") for i in range(len(spans))]
    return timed_words(spans, texts)


def main(argv: list[str]) -> int:
    if len(argv) != 2: print(__doc__, file=sys.stderr); return 2
    media, plan_p = argv
    try:
        plan = json.loads(Path(plan_p).read_text())
        words = hear(media)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        print(f"retake_check: FAILED to measure {media}: {e}"); return 2
    bad, wrong = retakes.problems(words, plan, window=WINDOW)
    for b in bad: print(f"retake_check: retake kept in the cut: {b} (cut the worse take, or name it in plan retakes_ok)")
    for w in wrong: print(f"retake_check: {w}")
    print(f"retake_check: {len(words)} words heard, {len(bad)} retake(s) {'FAIL' if bad or wrong else 'OK'}")
    return 1 if bad or wrong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
