#!/bin/bash
# run_v4.sh WORKDIR OUTDIR name1 name2 ...  — full pipeline with critic gate
# per video: build_edl -> face_track -> critic --fix (auto-fixes) -> rebuild -> face_track -> critic -> beds -> render -> critic --video
WORK=$1; OUT=$2; shift 2
VP=/home/kamil-jan/video-pipeline; R=$VP/render; PY=$VP/.venv/bin/python

# words_check: no word lost by the cut (plan text vs rough) or by the sound (rough vs film). Kamil 2026-11-08 "0:04 uciales
# moje gadanie ... juz ktorys raz". WORDS_CHECK=off skips it, logged (a quick preview render)
words_ok() {
  if [ "${WORDS_CHECK:-on}" = off ]; then echo "WORDS_CHECK=off: words_check skipped for $1" >> "$R/render.log"; return 0; fi
  python3 $VP/words_check.py cut "edl_$1.txt" "$R/$1/rough.mkv" >> "$R/render.log" 2>&1 || { echo "FAILED words_check cut $1" >> "$R/render.log"; return 1; }
  python3 $VP/words_check.py sound "$R/$1/rough.mkv" "$2" >> "$R/render.log" 2>&1 || { echo "FAILED words_check sound $1" >> "$R/render.log"; return 1; }
}
cd "$WORK" || { echo "run_v4: no work folder $WORK" >&2; exit 2; }
# the films are moved to OUT at the very end: a relative OUT counts from WORK (after the cd), so check it before 20 min of
# render (2026-11-05: a finished long failed on mv because OUT was relative to the caller's folder)
{ [ -d "$OUT" ] && [ -w "$OUT" ]; } || { echo "FAILED out: no writable folder $OUT seen from $WORK (a relative OUT counts from the work folder)" | tee -a "$R/render.log" >&2
  echo ALL_DONE >> "$R/render.log"; echo "FAILED_FILMS $*" >> "$R/render.log"; exit 2; }
# fail-fast for every film (ADR-0002): a failed step never renders a stale or unclamped EDL, the film gets no DONE
# scenes laid out in Chrome first: two pieces covering each other on screen (labels run together) stop the run, named.
# timeout: a hung Chrome must not hold the run without a log line. SCENE_CHECK=off (logged) only for a clash judged false
if [ -f gfx_specs.json ] && grep -q '"type": *"scene"' gfx_specs.json; then
  if [ "${SCENE_CHECK:-on}" = off ]; then echo "WARN scene_check off" >> "$R/render.log"
  else
    timeout "${SCENE_CHECK_TIMEOUT:-600}" node $VP/gfx/scene_check.mjs gfx_specs.json >> gfx.log 2>&1; rc=$?
    if [ $rc -ne 0 ]; then
      why="gfx.log: CLASH lines"; [ $rc -eq 124 ] && why="timeout ${SCENE_CHECK_TIMEOUT:-600} s, Chrome hung"
      echo "FAILED scene_check rc=$rc ($why)" >> "$R/render.log"; echo ALL_DONE >> "$R/render.log"; echo "FAILED_FILMS $*" >> "$R/render.log"; exit 1
    fi
  fi
fi
if [ -f gfx_specs.json ] && ! node $VP/gfx/render.mjs gfx_specs.json gfx >> gfx.log 2>&1; then
  # graphics are shared by every film of the project: none renders with missing or stale cards
  echo "FAILED gfx (gfx.log)" >> "$R/render.log"; echo ALL_DONE >> "$R/render.log"; echo "FAILED_FILMS $*" >> "$R/render.log"; exit 1
fi
failed=""  # films with a FAILED step: the .otio below must not come from a stale long EDL; exit 1 at the end
for n in "$@"; do
  L="$R/critic_$n.log"; : > "$L"
  # research_gate: research meant for this form must be in the film (done = a film_check item measures it) before a render.
  # Kamil 2026-11-08 "dlaczego nic nie weszlo!?" (0 of 24 Long items in the 2026-11-04 long). RESEARCH_GATE=off = logged
  form=$(python3 -c "import json,sys; print('shorts' if json.load(open(sys.argv[1])).get('vertical') else 'long')" "plan_$n.json" 2>/dev/null || echo long)
  if [ "${RESEARCH_GATE:-on}" = off ]; then echo "RESEARCH_GATE=off: research_gate skipped for $n ($form)" >> "$R/render.log"
  else python3 $VP/research_gate.py "$form" >> "$R/render.log" 2>&1 || { echo "FAILED research_gate $form $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  fi
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
  # the checklist (style/checklist.json): every feature used or skipped in the plan with a reason; FILM_CHECK=off only for old
  # projects made before the checklist (logged), never to get a film out faster
  if [ "${FILM_CHECK:-on}" = off ]; then echo "WARN film_check off $n" >> "$R/render.log"
  else python3 $VP/film_check.py . "$n" >> "$L" 2>&1 || { echo "FAILED film_check $n ($L)" >> "$R/render.log"; failed="$failed $n"; continue; }
    # soft items (checklist "level": "warn") pass, but they must be seen where the render is watched, not only in the critic log
    grep "^WARN" "$L" | sed "s/^/[$n] /" >> "$R/render.log" || true
  fi
  $PY $VP/music/make_beds.py edl_$n.json "$R/beds_$n" >> "$R/render.log" 2>&1 || { echo "FAILED make_beds $n" >> "$R/render.log"; failed="$failed $n"; continue; }
  # "behind" cards of THIS film (behind.py --edl): the speaker cut out on its final EDL (the gfx render above ran before the
  # critic's fixes); a card whose window did not change is skipped
  if [ -f gfx_specs.json ] && grep -q '"behind"' gfx_specs.json; then
    timeout 3600 $VP/matte/.venv/bin/python $VP/behind.py gfx_specs.json gfx --edl "edl_$n.json" >> "$R/render.log" 2>&1 || { echo "FAILED behind $n" >> "$R/render.log"; failed="$failed $n"; continue; }
    # what the cut-out hides (behind.py <id>.cover.json): text or a drawing behind the head must stay readable
    if [ "${FILM_CHECK:-on}" != off ]; then
      python3 $VP/film_check.py . "$n" --phase behind >> "$L" 2>&1 || { echo "FAILED film_check behind $n ($L)" >> "$R/render.log"; failed="$failed $n"; continue; }
    fi
  fi
  f=$(python3 -c "import json;print(json.load(open('edl_$n.json'))['out_name'])")
  # out_name comes from the plan (Syncthing): a bare file name only, never a path out of OUTDIR
  case "$f" in ""|*/*|.*) echo "FAILED out_name $n" >> "$R/render.log"; failed="$failed $n"; continue;; esac
  rm -f "$R/$n/rough.mkv"
  # av_check: no voice dropped, sound in step with the cut before graphics (film 2026-11-04: 0.65 s lost in long + 4 shorts)
  # sync_check: every piece of the cut where build_edl timed its cards and subtitles (timeline.py; 2026-11-04: up to 287 ms off)
  if nice -n 15 python3 $VP/assemble.py edl_$n.json "$R/$n" >> "$R/render.log" 2>&1 \
    && { python3 $VP/av_check.py "$R/$n/$f" --ref "$R/$n/rough.mkv" >> "$R/render.log" 2>&1 || { echo "FAILED av_check $n" >> "$R/render.log"; false; }; } \
    && { python3 $VP/sync_check.py edl_$n.json "$R/$n/rough.mkv" >> "$R/render.log" 2>&1 || { echo "FAILED sync_check $n" >> "$R/render.log"; false; }; } \
    && words_ok "$n" "$R/$n/$f" \
    && mv "$R/$n/$f" "$OUT/$f.part" && mv "$OUT/$f.part" "$OUT/$f"; then
    echo "DONE $n" >> "$R/render.log"
    # manifest: the film names the pipeline commit that made it (film_check --out: out.manifest; Kamil 2026-11-08
    # "inne materialy tez nowe logiki robiles czy wszystko po starych poszlo??")
    python3 $VP/manifest.py stamp "$OUT" "$f" >> "$R/render.log" 2>&1 || { echo "FAILED manifest $n" >> "$R/render.log"; failed="$failed $n"; }
    # editing-grammar metric per render (ADR-0002); EDLs get overwritten
    python3 $VP/beatfx.py edl_$n.json >> "$R/beat_stats.log" 2>> "$R/render.log" || echo "WARN beat_stats $n" >> "$R/render.log"
  else
    echo "FAILED assemble $n" >> "$R/render.log"; failed="$failed $n"; continue
  fi
  echo "--- po renderze ---" >> "$L"; nice python3 $VP/critic.py plan_$n.json --video "$OUT/$f" >> "$L" 2>&1
done
# the Kdenlive project only from the long rendered in THIS run (never from a stale edl_long.json)
if [[ " $* " == *" long "* && " $failed " != *" long "* ]] && [ -f edl_long.json ]; then
  lf=$(python3 -c "import json;print(json.load(open('edl_long.json'))['out_name'])")
  $PY $VP/to_otio.py edl_long.json "$OUT/${lf%.mp4}_do_kdenlive.otio" >> "$R/render.log" 2>&1 \
    || { echo "FAILED to_otio long" >> "$R/render.log"; failed="$failed long"; }
fi
echo ALL_DONE >> "$R/render.log"
# any failed film -> exit 1, so a render started from a terminal or a task sees it too (the panel also checks "DONE <film>")
[ -z "$failed" ] || { echo "FAILED_FILMS$failed" >> "$R/render.log"; exit 1; }
