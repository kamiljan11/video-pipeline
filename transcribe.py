import json
import os
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

from cpu_budget import heavy_threads, low_priority

# usage: transcribe.py out_dir wav1 wav2 ...
out_dir = sys.argv[1]
low_priority()
model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=heavy_threads())
for wav in sys.argv[2:]:
    name = os.path.splitext(os.path.basename(wav))[0]
    dst = os.path.join(out_dir, name + ".json")
    if os.path.exists(dst):
        continue
    t = time.time()
    segs, info = model.transcribe(wav, language="pl", word_timestamps=True, vad_filter=False,
        beam_size=5, condition_on_previous_text=False,
        initial_prompt="Yyy, eee, no więc, tak jakby... Nagranie na YouTube, mówię swobodnie.")
    out = []
    for s in segs:
        out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                    "words": [{"w": w.word, "s": w.start, "e": w.end, "p": round(w.probability, 3)} for w in (s.words or [])]})
    Path(dst).write_text(json.dumps({"file": name, "duration": info.duration, "segments": out}, ensure_ascii=False, indent=1))
    print(name, round(info.duration, 1), "s audio in", round(time.time() - t, 1), "s", flush=True)
