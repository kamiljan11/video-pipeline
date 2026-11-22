# Pipeline map: single-speaker assumptions (2026-11-22)

Source: read-only sweep of this worktree (base origin/main 40ffa83) and the main checkout
(`~/Dane/video-pipeline`, branch feat/scene-explainer 1f87588, 278 commits ahead of origin/main).
[vp] = this worktree, [main] = main checkout. Line numbers in [main] may shift (uncommitted edits there).

## Base problem
- origin/main is from 2026-10-31. The working code lives on feat/scene-explainer / PR #11
  (backup/main-local-2026-11-17). framing.py, cutout.py, frame_pick.py, lip_check.py, retakes.py,
  screen_grammar.py, cuts.py, word_times.py, film_check.py exist only there.
- Scripts hardcode `/home/kamil-jan/video-pipeline` (symlink to the main checkout): run_v4.sh:5,
  face_track.py:19, head_check.py:25, gfx/render.mjs:2, assemble.py:183, critic.py:145.

## Stage order
1. dejudder.py (optional) -> wav/.sil (manual/panel)
2. chunked_whisper.py:13-50 (whisper.cpp large-v3, pl, word-level) -> .cw.json; fallback transcribe.py
3. beats.py + beatfx.py (style/grammar.json)
4. build_edl.py (+ edges.py)
5. face_track.py; critic.py --fix x3 (run_v4.sh:124-131 [main])
6. edl_guard, film_check, research_gate, dry_run [main]
7. music/make_beds.py; gfx/render.mjs -> ProRes4444; behind.py
8. assemble.py (per-segment cut :97-117, concat + overlays :126-226)
9. av/sync/lip/words/music checks, critic --video, to_otio, manifest
Shorts = plan_short*.json ("vertical": true) through run_v4.sh; shorts.py only ranks sentence runs.

## Single-speaker assumptions
- No diarization anywhere; word = (from, to, text) (build_edl.py:16).
- Mono audio: assemble.py:116 `-ac 1`, stage 2 reads [0:a] only.
- One source "A": build_edl.py:89, :188; face_track.py:16.
- Fixed size 2560x1440 (build_edl.py:189), src_w/src_h never written -> 4K crop risk (unverified).
- face_track.py: YuNet at 640x360 (:19,:27), largest face only (:29), one face/head per segment
  (:113-124), cache keyed by time only (:17,:22), one x-path for vertical (:33-59).
- head_check.py:34 largest face; [main] frame_pick.py:139 num_faces=1, lip_check.py:40 top 60% centre strip,
  thumb_check.py:111, stills.py:70, film_check.py:451.
- assemble.py vf_for :42-72 one crop around one face; 9:16 crop :57-63; PiP bottom-right :164-188;
  split face box gfx_types.py:12. behind.py:67-84 imports vf_for by AST (keep names/globals).
- retakes.py:17-30 speaker-blind (two people echoing = false positive, inference).

## Graphics vs faces
No safe-zone data; positions hardcoded for one centred head: template.html .kw/.list right:70 / left:110,
.lower/.cta bottom-left, .maxim full-width bottom + scrim, PiP bottom-right; [main] STICKER_BOX,
scene SIDE x1640-2460. 9:16 captions MarginV 540, caption_v 300-900, split caption_y 1150. No speaker
colour/label in captions or SRT. All of these can cover the second person.

## Theme system
themes.py:17-31 + gfx/theme_lib.mjs:12-24; 24 css tokens; new theme = style/themes/<name>.json +
`node gfx/pip_assets.mjs 600 <acc> <name>`; select with work/theme.json. No speaker tokens.
Hardcoded colours: build_edl.py:271-328 (ASS), pip_assets.mjs:6, themes.py:45, template.html several.

## Gates
`.venv/bin/python -m unittest discover -s tests -v`, `npm test` (node --test gfx/test), `ruff check .`,
pyright (pre-commit), CI quality.yml + gitleaks.

## Modules to touch (R reuse / N new)
a) diarization: N diarize.py -> "spk" in .cw.json; readers build_edl, beats, shorts, critic, broll, retakes, cuts.
b) 2 faces + active speaker: rework face_track (all faces, left/right identity, per-speaker boxes,
   source in cache key, higher detection res); head_check, frame_pick, lip_check, render_audit, edl_guard.
c) long-form layouts wide/single/split: N per-segment "layout"; extend vf_for; stop hardcoding "A"; src_w/src_h.
d) shorts: vertical crop follows active speaker; optional stacked layout; speaker-aware shorts score.
e) safe zones: N data from face boxes; cards/PiP/captions respect all faces; critic C2 vs all faces.

## Unverified
RVM matte with two people; YuNet small faces at 640x360 from 4K; 4K crop error; panel/ src_w; tests not run.
