#!/bin/bash
# renders shorts then long into ~/video-pipeline/render (not synced), moves finals to Videos/Montaz/.../out
WORK=/home/kamil-jan/Videos/Montaz/2026-10-20/work
OUT=/home/kamil-jan/Videos/Montaz/2026-10-20/out
R=/home/kamil-jan/video-pipeline/render
cd "$WORK"
for n in short1_95procent short2_cichy_bol short3_jedno_zlecenie short4_drugi_tydzien long; do
  f=$(python3 -c "import json;print(json.load(open('edl_$n.json'))['out_name'])")
  [ -f "$OUT/$f" ] && continue
  nice -n 15 python3 /home/kamil-jan/video-pipeline/assemble.py edl_$n.json "$R/$n" >> "$R/render.log" 2>&1 \
    && mv "$R/$n/$f" "$OUT/$f.part" && mv "$OUT/$f.part" "$OUT/$f" && echo "DONE $n" >> "$R/render.log"
done
echo ALL_DONE >> "$R/render.log"
