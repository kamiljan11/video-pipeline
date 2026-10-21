#!/bin/bash
# v3: animated zooms + icons + CTA + progress bar + own music + SFX. Shorts first, then long.
WORK=/home/kamil-jan/Videos/Montaz/2026-10-20/work
OUT=/home/kamil-jan/Videos/Montaz/2026-10-20/out
R=/home/kamil-jan/video-pipeline/render
PY=/home/kamil-jan/video-pipeline/.venv/bin/python
cd "$WORK"
node /home/kamil-jan/video-pipeline/gfx/render.mjs gfx_specs.json gfx >> gfx.log 2>&1
for n in short1_95procent short2_cichy_bol short3_jedno_zlecenie short4_drugi_tydzien long; do
  python3 /home/kamil-jan/video-pipeline/build_edl.py plan_$n.json >> "$R/render.log" 2>&1
  $PY /home/kamil-jan/video-pipeline/music/make_beds.py edl_$n.json "$R/beds_$n" >> "$R/render.log" 2>&1
  f=$(python3 -c "import json;print(json.load(open('edl_$n.json'))['out_name'])")
  rm -f "$R/$n/rough.mkv"
  nice -n 15 python3 /home/kamil-jan/video-pipeline/assemble.py edl_$n.json "$R/$n" >> "$R/render.log" 2>&1 \
    && mv "$R/$n/$f" "$OUT/$f.part" && mv "$OUT/$f.part" "$OUT/$f" && echo "DONE $n" >> "$R/render.log"
done
/home/kamil-jan/video-pipeline/.venv/bin/python /home/kamil-jan/video-pipeline/to_otio.py edl_long.json "$OUT/95procent_long_do_kdenlive.otio" >> "$R/render.log" 2>&1
echo ALL_DONE >> "$R/render.log"
