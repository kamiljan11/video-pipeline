#!/usr/bin/env python3
# lines.py words.json -> prints numbered lines "L# [start-end] text" split on sentence punctuation or gaps >0.6s
import json
import re
import sys
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text())
ws = [(x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000, x["text"], k) for k, x in enumerate(d["transcription"]) if x["text"].strip()]
lines, cur = [], []
for i, w in enumerate(ws):
    if cur and (w[0] - cur[-1][1] > 0.6):
        lines.append(cur); cur = []
    cur.append(w)
    if re.search(r"[.?!…]$", w[2].strip()):
        lines.append(cur); cur = []
if cur: lines.append(cur)
for n, l in enumerate(lines):
    print(f"L{n} [{l[0][0]:.2f}-{l[-1][1]:.2f}] w{l[0][3]}-{l[-1][3]} {''.join(x[2] for x in l).strip()}")
