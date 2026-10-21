#!/usr/bin/env python3
# chunked_whisper.py base  (in workdir: base.wav, base.sil) -> base.cw.json (word list with reliable times)
# splits audio at silence midpoints into <=25s chunks so whisper timestamps cannot drift
import json
import os
import re
import subprocess
import sys
from pathlib import Path

b = sys.argv[1]; W = "/home/kamil-jan/video-pipeline"
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", b + ".wav"]))
vals = [float(x) for x in re.findall(r"silence_(?:start|end): ([0-9.]+)", Path(b + ".sil").read_text())]
mids = [(vals[i] + vals[i + 1]) / 2 for i in range(0, len(vals) - 1, 2)]
cuts, last = [0.0], 0.0
for i, m in enumerate(mids):
    nxt = mids[i + 1] if i + 1 < len(mids) else dur
    if nxt - last > 25 and m - last > 3:
        cuts.append(m); last = m
cuts.append(dur)
cd = f"{b}_chunks"; os.makedirs(cd, exist_ok=True)
files = []
for k in range(len(cuts) - 1):
    f = f"{cd}/{k:03d}_{cuts[k]:.3f}.wav"; files.append(f)
    if not os.path.exists(f):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{cuts[k]:.3f}", "-to", f"{cuts[k+1]:.3f}", "-i", b + ".wav", f], check=True)
todo = [f for f in files if not os.path.exists(f[:-4] + ".json")]
if todo:
    subprocess.run([f"{W}/whisper.cpp/build/bin/whisper-cli", "-m", f"{W}/models/ggml-large-v3-q5_0.bin", "-l", "pl", "-t", "30",
                    "-ml", "1", "-sow", "-oj", "--dtw", "large.v3", "-nf", *todo], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
words = []
for f in files:
    off = float(os.path.basename(f)[4:-4])
    for x in json.loads(Path(f + ".json" if os.path.exists(f + ".json") else f[:-4] + ".json").read_text())["transcription"]:
        if x["text"].strip():
            words.append({"s": round(off + x["offsets"]["from"] / 1000, 3), "e": round(off + x["offsets"]["to"] / 1000, 3), "w": x["text"]})
Path(b + ".cw.json").write_text(json.dumps(
    {"transcription": [{"offsets": {"from": int(w["s"] * 1000), "to": int(w["e"] * 1000)}, "text": w["w"]} for w in words]},
    ensure_ascii=False))
print("chunks", len(files), "words", len(words))
