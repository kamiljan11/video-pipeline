#!/usr/bin/env python3
"""spot_check.py edl.json words.json video "fraza1" "fraza2" ...  — resolve C8 alarms: find each phrase in the kept
transcript, cut ±3 s around it from the FINAL video and transcribe that piece alone (whisper.cpp)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from cpu_budget import heavy_threads, low_priority

edl = json.loads(Path(sys.argv[1]).read_text()); W = json.loads(Path(sys.argv[2]).read_text())["transcription"]; video = sys.argv[3]
norm = lambda t: re.sub(r"[^a-ząćęłńóśźż0-9 ]", "", t.lower()).split()
def src2out(t):
    acc = 0.0
    for s in edl["segments"]:
        if s["in"] <= t <= s["out"]: return acc + t - s["in"]
        acc += s["out"] - s["in"]
    return None
words = [(i, norm(w["text"])) for i, w in enumerate(W)]
tmp = tempfile.mkdtemp()
for ph in sys.argv[4:]:
    p = norm(ph); hit = None
    for i in range(len(W) - len(p)):
        if [x[0] if x else "" for _, x in words[i:i + len(p)]] == p:
            t = src2out(W[i]["offsets"]["from"] / 1000)
            if t is not None: hit = t; break
    if hit is None: print(f"[{ph}] nie ma w zachowanym materiale"); continue
    wav = os.path.join(tmp, "x.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, hit - 3):.2f}", "-t", "7", "-i", video, "-ac", "1", "-ar", "16000", wav], check=True)
    r = subprocess.run(["/home/kamil-jan/video-pipeline/whisper.cpp/build/bin/whisper-cli", "-m", "/home/kamil-jan/video-pipeline/models/ggml-large-v3-q5_0.bin",
                        "-l", "pl", "-t", str(heavy_threads()), "-nt", wav], check=False, preexec_fn=low_priority, capture_output=True, text=True).stdout.strip().replace("\n", " ")
    ok = all(w in norm(r) for w in p)
    print(f"[{ph}] @ {hit:.1f}s -> {'OK' if ok else 'BRAK?'} | słychać: {r}")
