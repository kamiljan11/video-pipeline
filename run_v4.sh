#!/bin/bash
# run_v4.sh WORKDIR OUTDIR name1 name2 ...  — full pipeline with critic gate
# per video: build_edl -> face_track -> critic --fix (auto-fixes) -> rebuild -> face_track -> critic -> beds -> render -> critic --video
WORK=$1; OUT=$2; shift 2
VP=/home/kamil-jan/video-pipeline; R=$VP/render; PY=$VP/.venv/bin/python
cd "$WORK"
# fail-fast for every film (ADR-0002): a failed step never renders a stale or unclamped EDL, the film gets no DONE
if [ -f gfx_specs.json ] && ! node $VP/gfx/render.mjs gfx_specs.json gfx >> gfx.log 2>&1; then
  # graphics are shared by every film of the project: none renders with missing or stale cards
  echo "FAILED gfx (gfx.log)" >> "$R/render.log"; echo ALL_DONE >> "$R/render.log"; echo "FAILED_FILMS $*" >> "$R/render.log"; exit 1
fi
failed=""  # films with a FAILED step: the .otio below must not come from a stale long EDL; exit 1 at the end
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
  # the final EDL against edl_guard.py (ADR-0006) before the heavy steps: a refused value fails now, named, not after behind.py
  python3 $VP/edl_guard.py edl_$n.json >> "$R/render.log" 2>&1 || { echo "FAILED edl_guard $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  $PY $VP/music/make_beds.py edl_$n.json "$R/beds_$n" >> "$R/render.log" 2>&1 || { echo "FAILED make_beds $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  # "behind" cards of THIS film (behind.py --edl): the speaker cut out on its final EDL (the gfx render above ran before the
  # critic's fixes); a card whose window did not change is skipped
  if [ -f gfx_specs.json ] && grep -q '"behind"' gfx_specs.json; then
    timeout 3600 $VP/matte/.venv/bin/python $VP/behind.py gfx_specs.json gfx --edl "edl_$n.json" >> "$R/render.log" 2>&1 || { echo "FAILED behind $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  fi
  f=$(python3 -c "import json;print(json.load(open('edl_$n.json'))['out_name'])")
  # out_name comes from the plan (Syncthing): a bare file name only, never a path out of OUTDIR
  case "$f" in ""|*/*|.*) echo "FAILED out_name $n" >> "$R/render.log"; failed="$failed $n"; continue;; esac
  rm -f "$R/$n/rough.mkv"
  if nice -n 15 python3 $VP/assemble.py edl_$n.json "$R/$n" >> "$R/render.log" 2>&1 \
    && mv "$R/$n/$f" "$OUT/$f.part" && mv "$OUT/$f.part" "$OUT/$f"; then
    echo "DONE $n" >> "$R/render.log"
    # editing-grammar metric per render (ADR-0002); EDLs get overwritten
    python3 $VP/beatfx.py edl_$n.json >> "$R/beat_stats.log" 2>> "$R/render.log" || echo "WARN beat_stats $n" >> "$R/render.log"
  else
    echo "FAILED assemble $n" >> "$R/render.log"; failed="$failed $n"; continue
  fi
  echo "--- po renderze ---" >> "$L"; nice python3 $VP/critic.py plan_$n.json --video "$OUT/$f" >> "$L" 2>&1
done
# the Kdenlive project only from the long rendered in THIS run (never from a stale edl_long.json)
if [[ " $* " == *" long "* && " $failed " != *" long "* ]] && [ -f edl_long.json ]; then
  $PY $VP/to_otio.py edl_long.json "$OUT/95procent_long_do_kdenlive.otio" >> "$R/render.log" 2>&1 \
    || { echo "FAILED to_otio long" >> "$R/render.log"; failed="$failed long"; }
fi
echo ALL_DONE >> "$R/render.log"
# any failed film -> exit 1, so a render started from a terminal or a task sees it too (the panel also checks "DONE <film>")
[ -z "$failed" ] || { echo "FAILED_FILMS$failed" >> "$R/render.log"; exit 1; }
