#!/usr/bin/env python3
# verify_cut.py edl.txt output.mp4 -> transcribes output and lists words expected but missing (possible clipped speech)
import difflib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from cpu_budget import heavy_threads, low_priority

exp_txt, video = sys.argv[1], sys.argv[2]
W = "/home/kamil-jan/video-pipeline"
tmp = tempfile.mkdtemp()
wav = os.path.join(tmp, "a.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ac", "1", "-ar", "16000", wav], check=True)
subprocess.run([f"{W}/whisper.cpp/build/bin/whisper-cli", "-m", f"{W}/models/ggml-large-v3-q5_0.bin", "-l", "pl", "-t", str(heavy_threads()),
                "-otxt", "-of", os.path.join(tmp, "a"), wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, preexec_fn=low_priority)
norm = lambda t: re.findall(r"[a-ząćęłńóśźż0-9%]+", t.lower())
e = norm(Path(exp_txt).read_text()); g = norm(Path(os.path.join(tmp, "a.txt")).read_text())
sm = difflib.SequenceMatcher(None, e, g, autojunk=False)
print(f"expected {len(e)} words, heard {len(g)}, match ratio {sm.ratio():.3f}")
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op in ("delete", "replace") and a2 - a1 >= 2:
        print(f"MISSING? {' '.join(e[max(0,a1-3):a1])} [[{' '.join(e[a1:a2])}]] {' '.join(e[a2:a2+3])}  | heard: {' '.join(g[b1:b2])}")
