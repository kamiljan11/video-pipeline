#!/bin/bash
# run_v4.sh WORKDIR OUTDIR name1 name2 ...  — full pipeline with critic gate
# per video: build_edl -> face_track -> critic --fix (auto-fixes) -> rebuild -> face_track -> critic -> beds -> render -> critic --video
WORK=$1; OUT=$2; shift 2
VP=/home/kamil-jan/video-pipeline; R=$VP/render; PY=$VP/.venv/bin/python
cd "$WORK"
node $VP/gfx/render.mjs gfx_specs.json gfx >> gfx.log 2>&1
failed=""  # films with a FAILED step: the .otio below must not come from a stale long EDL
for n in "$@"; do
  L="$R/critic_$n.log"; : > "$L"
  # a failed build_edl (e.g. a typo in style/grammar.json) or face_track must not render a stale/unclamped edl_$n.json: no DONE for this film
  python3 $VP/build_edl.py plan_$n.json >> "$R/render.log" 2>&1 || { echo "FAILED build_edl $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  $PY $VP/face_track.py edl_$n.json >> "$L" 2>&1 || { echo "FAILED face_track $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  for it in 1 2 3; do
    python3 $VP/critic.py plan_$n.json --fix > "$R/crit_tmp.log" 2>&1; cat "$R/crit_tmp.log" >> "$L"
    grep -q " FIX:" "$R/crit_tmp.log" || break
    echo "--- iteracja $it: przebudowa po poprawkach ---" >> "$L"
    python3 $VP/build_edl.py plan_$n.json >> "$R/render.log" 2>&1 || { echo "FAILED build_edl $n" >> "$R/render.log"; failed="$failed $n"; continue 2; }
    $PY $VP/face_track.py edl_$n.json >> "$L" 2>&1 || { echo "FAILED face_track $n" >> "$R/render.log"; failed="$failed $n"; continue 2; }
  done
  $PY $VP/music/make_beds.py edl_$n.json "$R/beds_$n" >> "$R/render.log" 2>&1 || { echo "FAILED make_beds $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  f=$(python3 -c "import json;print(json.load(open('edl_$n.json'))['out_name'])")
  rm -f "$R/$n/rough.mkv"
  nice -n 15 python3 $VP/assemble.py edl_$n.json "$R/$n" >> "$R/render.log" 2>&1 \
    && mv "$R/$n/$f" "$OUT/$f.part" && mv "$OUT/$f.part" "$OUT/$f" && echo "DONE $n" >> "$R/render.log" \
    && { python3 $VP/beatfx.py edl_$n.json >> "$R/beat_stats.log" 2>> "$R/render.log" || echo "WARN beat_stats $n" >> "$R/render.log"; }  # editing-grammar metric per render (ADR-0002); EDLs get overwritten
  echo "--- po renderze ---" >> "$L"; nice python3 $VP/critic.py plan_$n.json --video "$OUT/$f" >> "$L" 2>&1
done
[ -f edl_long.json ] && [[ " $failed " != *" long "* ]] && $PY $VP/to_otio.py edl_long.json "$OUT/95procent_long_do_kdenlive.otio" >> "$R/render.log" 2>&1
echo ALL_DONE >> "$R/render.log"
