#!/usr/bin/env python3
# chunked_whisper.py base  (in workdir: base.wav, base.sil) -> base.cw.json (word list with reliable times)
# splits audio at silence midpoints into <=25s chunks so whisper timestamps cannot drift
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import word_times
from cpu_budget import heavy_threads, low_priority

b = sys.argv[1]; W = str(Path(__file__).resolve().parent)  # whisper.cpp/ and models/ live in the checkout
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", b + ".wav"]))
vals = [float(x) for x in re.findall(r"silence_(?:start|end): ([0-9.]+)", Path(b + ".sil").read_text())]
mids = [(vals[i] + vals[i + 1]) / 2 for i in range(0, len(vals) - 1, 2)]
cuts, last = [0.0], 0.0
for i, m in enumerate(mids):
    nxt = mids[i + 1] if i + 1 < len(mids) else dur
    if nxt - last > 25 and m - last > 3:
        cuts.append(m); last = m
cuts.append(dur)
cd = f"{b}_chunks_dtw"; os.makedirs(cd, exist_ok=True)  # _dtw: the old chunks have no DTW times and would be skipped as done
files = []
for k in range(len(cuts) - 1):
    f = f"{cd}/{k:03d}_{cuts[k]:.3f}.wav"; files.append(f)
    if not os.path.exists(f):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{cuts[k]:.3f}", "-to", f"{cuts[k+1]:.3f}", "-i", b + ".wav", f], check=True)
todo = [f for f in files if word_times.chunk_json(f) is None]  # resume: a chunk with output is not sent to whisper again
if todo:
    subprocess.run([f"{W}/whisper.cpp/build/bin/whisper-cli", "-m", f"{W}/models/ggml-large-v3-q5_0.bin", "-l", "pl", "-t", str(heavy_threads()),
                    "-ml", "1", "-sow", "-ojf", "-nfa", "--dtw", "large.v3", "-nf", *todo], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=low_priority)
words = []; dtw_n = 0
for f in files:
    off = float(os.path.basename(f)[4:-4]); j = word_times.chunk_json(f)
    if j is None: sys.exit(f"chunked_whisper: whisper-cli wrote no output for {f} (expected {f}.json)")
    for x in json.loads(j.read_text())["transcription"]:
        if x["text"].strip():
            # the DTW start of the word (flash attention off, -nfa: with it whisper drops DTW without a word); else whisper's guess
            d = word_times.dtw_start_ms(x)
            s0 = d / 1000 if d is not None else x["offsets"]["from"] / 1000
            words.append({"s": round(off + s0, 3), "e": round(off + max(x["offsets"]["to"] / 1000, s0 + 0.04), 3), "w": x["text"]})
            dtw_n += d is not None
if words:  # the start after a pause onto the voice onset (word_times.snap)
    cw = [{"offsets": {"from": int(w["s"] * 1000), "to": int(w["e"] * 1000)}, "text": w["w"]} for w in words]
    snapped = word_times.snap(cw, word_times.onsets(b + ".wav"))
else: cw, snapped = [], 0
Path(b + ".cw.json").write_text(json.dumps({"transcription": cw}, ensure_ascii=False))
print("chunks", len(files), "words", len(words), "dtw", dtw_n, "snapped", snapped)
if words and dtw_n < len(words) * 0.9: sys.exit(f"chunked_whisper: only {dtw_n} of {len(words)} words have DTW times (whisper-cli dropped DTW?)")
