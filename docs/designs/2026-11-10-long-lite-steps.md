# Long-lite — micro-steps (start Sunday 2026-11-15, after the weekly limit reset)

Plan: `docs/designs/2026-11-10-long-lite.md`. Order (Kamil 2026-11-10): **system rebuild -> test on a FRAGMENT of a long -> only once the fragment passes, the whole long.** Longs only; the rest only after the long is accepted and Kamil writes "jedz dalej".

Every step = commit (Conventional Commits) + `pytest` with `set -o pipefail` rc=0 + ruff. No `--no-verify`, no lint suppression. Branch `feat/long-lite` from `feat/film-v2-motion` (a6bb0c4 + docs). No merge to main without Kamil's phrase. Junk -> `~/Dane/_to_delete/<date>-video-pipeline` + LISTA.txt, `df -h` in the report.

## Status 2026-11-14 (scheduled run video-long-lite-start, laptop)

| phase | status | commit / reason |
|---|---|---|
| 1 no selectivity | done (waivers in the plan, `SKIPPED_GATES` line) | bbae4e8 |
| 2 dry run + freeze | done; fixed twice on the real long: the record names the commit the dry run STARTED on (9d98663), the edl hash leaves out what make_beds writes after the check point (see below) | bbae4e8, 9d98663, + edl-digest fix |
| 3 timeline + watcher | done; watcher `--stall` 1800 s too short for words_check under load (whisper says nothing for 30-60 min) | 8005df4 |
| 4.1-4.3 Kdenlive round trip | done (kden_export / kden_import / cut_fix) | 94876e2 |
| 4.4 snap_tail + entry_check | deferred: edge_fix already moves keep edges, Kamil's Kdenlive cut_fix too; a third mechanism on the same edge without a measurement = conflict (NOTES_LOG 41) | — |
| 4.5 duck default 0.004 | deferred: the long has 0.004 in its plan; the default is film code, every film stale (NOTES_LOG 38, 42) | — |
| 5 effect rules | done (`long.effect_spread`) | c4c6e3b |
| 6 ACCEPTED | gate only in run_v4.sh for now; build_posts / ig_carousel / article / publish_post do not check it yet (NOTES_LOG 43) | c4c6e3b |
| — lip_check | the long had cards over 1073 of 1086 s: 0 pieces measured, OK, for every long since v5; now measured under the cards (dry run 3: 15/24 pieces, median -14.5 ms) | 9fd8bbf |
| 7 fragment test | BLOCKED 2026-11-14 before the dry run, decision for Kamil: `fragment.py` cuts words 875-1593 of the 2026-11-04 long (p4 "blizna" -> p6, 235 s, 11 keeps, 21 cards incl. 3 chap + 2 behind, 9 moods) into `render/montaz/lite-test-2026-11-14/work`; build_edl OK, `long.effect_spread` PASS, but film_check FAILs 8 whole-film items the cut breaks (screen_switches 8 in 3.9 min, screen_share 132/235 s, memes 1<3, lower = define not the name card, music_palette = same film in the ledger, stills not accepted for this film, cta_place, capabilities sources/claims/note/find/bookend). Options: fragment profile in film_check (whole-film items WARN when FRAGMENT.json) / Kamil's waivers / skip to the whole long | 864f888 |

Runs on the whole long (timeline.log, minutes): dry run 3 on 9fd8bbf = DRY_OK, 92.4 total (plan 0.3, beds 0.9, assemble 23.7, checks 67.0; machine load ~40 from another transcription); full render refused after 0.8 min: `edl_long.json changed after the dry run` — make_beds rewrites the edl after the full render's check point, so no full render could ever pass. Fixed in dry_run.digest (6af5035). Dry run 4 of the whole long on 6af5035 started 14:09 and was stopped at 14:10 (plan stage): order change from Kamil 14.11 ("mial byc render kawalka zeby widziec realnie czy dzialaja logiki zeby pelny zrobic?") -> Phase 7 fragment first, the whole long only after Kamil accepts the fragment. Phase 7 not started: there is no tool that cuts a fragment plan (keeps, gfx, chapter, behind, music of a time window) out of plan_long.json, and this run had ~2 % of its 10 % budget left.

## Phase 0 — start (session S0, ~0.5 %)
- 0.1 `get_usage` -> `timeline.log` line `S0 start usage=<pct>`; phase budget: whole rebuild <= 15 % of the weekly limit, stop + report on overrun.
- 0.2 `git status` clean, `git worktree list`, check that no render is running (`systemctl --user list-units 'vp-*'`).
- 0.3 Branch `feat/long-lite`. Read the plan + this file. One line to Kamil: "starting phase 1".
- 0.4 ADR `docs/adr/0025-long-lite-process-boundaries.md`: 5 boundaries (system != film, freeze, render entry = dry run, limit of new gates, film budget) + ACCEPTED + "jedz dalej".

## Phase 1 — no selectivity (~1.5 %)
- 1.1 `run_v4.sh`: list of switches (`LIP_CHECK`, `WORDS_CHECK`, `FILM_CHECK`, `SCENE_CHECK`, `RESEARCH_GATE`) -> each `=off` writes `SKIPPED <gate> <film>` to `render.log` AND to `<out>/<film>.skipped`.
- 1.2 `film_check.py`: an existing `.skipped` without `plan.waivers.<gate>` = FAIL `waiver missing`. A waiver = a quote from Kamil + date (format validated).
- 1.3 Test: a waiver cannot be created by run_v4 / film_check (no code path writes `waivers`); test that `=off` without a waiver -> rc!=0.
- 1.4 Report: the first line of `RAPORT.md`/stdout = list of skipped gates or `skipped: none`.

## Phase 2 — dry run + freeze (~2 %)
- 2.1 `run_v4.sh DRY=1`: `assemble.py --proxy` + all post checks (av, sync, lip, words cut/sound, film_check) -> `<work>/dry.json` {commit, plan_sha256, edl_sha256, verdicts, t_start, t_end}.
- 2.2 Final render (DRY unset): refuses (rc 3, message "no green dry run for commit X / plan Y") when `dry.json` is missing, red, or has a different commit/plan sha.
- 2.3 Freeze: `manifest.py freeze <work>` writes the commit at the film's start; run_v4 refuses to start when HEAD != freeze (outside NOT_FILM/docs/tests) -> message "code changed during the film: <files>".
- 2.4 Tests: stub assemble (like test_run_v4 STUB) — the dry run passes -> final OK; a plan change -> final refuses; a commit -> refuses.
- 2.5 Measure: dry-run time on a 3 min fragment -> `timeline.log`.

## Phase 3 — watchdog + timeline + tokens (~1 %)
- 3.1 `timeline.log` in work/: `<ISO> <stage> start|end rc=<n>` from run_v4 and gfx render (stages: transcribe, build_edl, gfx, behind, scene_check, dry, final, package).
- 3.2 Watchdog: a script (user systemd unit) that watches the log; STALL = no new line for N min (per stage, from the measurements) -> one line to the session; DONE/FAILED the same. The session doesn't poll.
- 3.3 Gates: each prints one line `GATE <name> PASS|FAIL <reason>`; the session reads the long log only on FAIL.
- 3.4 Stills: `scene_check` writes `flagged.json`; the session looks only at flagged cards; Kamil gets the contact sheet.

## Phase 4 — cuts (~2 %)
- 4.1 `edl2mlt.py` -> repo `tools/kden/edl2mlt.py`, entry in NOT_FILM; tests: the XML has main_bin version 1.04, kdenlive:id per producer, V1 = cuts with sound, mix transitions.
- 4.2 `kden_import.py <project.kdenlive> <plan_long.json>`: V1 (in/out per clip) -> keeps with t0/t1; dropped clip = keep removed; a new piece from outside the old keeps = allowed (that's "recovering a cut part"); report: N edges moved, +/- seconds.
- 4.3 Round-trip test: edl2mlt -> import with no changes = identical keeps; an edge moved by 0.5 s -> keep t1 +0.5.
- 4.4 `snap_tail` + `entry_check` (REF-oss-survey item 5, claude-youtube-editor `cutlib.py:77-90`, `analyze_cut.py:39-51`, MIT -> attribution in the code): in build_edl, instead of fixed POST 0.16 (`build_edl.py:31`); entry_check blocking in the dry run.
- 4.5 Default `music_duck.threshold` 0.015 -> 0.004 in `assemble.py:406` (measured 2026-11-10, NOTES_LOG row 38) + test.

## Phase 5 — effect rules (~1 %)
- 5.1 `long.effect_spread` in checklist + film_check: every kind (behind, emph, float, kw, web, meme, chap) in every third; <=3 uses -> 2 of 3. Start: report, blocking after the first real hit (Kamil reported the problem -> blocking right away if this long has a gap).
- 5.2 Measure on the 2026-11-04 long: per kind per third + the 34 s gap at ~13:10 (what fills it?) -> NOTES_LOG.
- 5.3 capabilities: `required` only for effect kinds; parameters (`opt.*`, `pfx.*`) -> `report`. Test test_capabilities green.

## Phase 6 — ACCEPTED + order of forms (~1 %)
- 6.1 `accept.py <out>`: writes `out/long/ACCEPTED` {commit, mp4 sha256, date, quote}; the quote is a required argument (Kamil's sentence from the chat).
- 6.2 Stage B (run_v4 for clips, build_posts, ig_carousel, article, publish_post) refuses without ACCEPTED or when the sha differs.
- 6.3 RUNBOOK: new order diagram A -> ACCEPTED -> "jedz dalej" -> B; shorts from the accepted long.

## Phase 7 — FRAGMENT test (~2-3 %)
- 7.1 Fragment: 3 min of the 2026-11-04 recording (a piece with cards, a behind card, a chapter, music) -> new work dir `render/montaz/lite-test-<date>/` (fresh edit from zero).
- 7.2 Full path: transcription -> build_edl -> plan -> gfx -> Kdenlive project -> (Kamil moves 1-2 edges, optional) -> import -> dry -> final -> package.
- 7.3 Success criteria (all of them): 1 dry + 1 final, zero code changes during the test, zero skipped gates, effect_spread green, timeline.log complete, usage measured.
- 7.4 Report to Kamil: times per stage, % of the limit, what broke. Kamil decides: whole long or fix.
- 7.5 Failure -> fixes in the SYSTEM (not in the test film), new commit, the fragment test from zero.

## Phase 8 — whole long (only after 7 is green + Kamil's "ok")
- 8.1 Which long: Kamil's decision (the 2026-11-04 long with his Kdenlive cuts or a new recording).
- 8.2 Freeze -> plan -> gfx -> Kdenlive for Kamil -> import -> dry -> final -> package -> Kamil watches -> ACCEPTED.
- 8.3 After the film: NOTES_LOG (hours, renders, % of the limit vs target 4-6 h / 5-10 %).

## Later (after the reset or after the long)
- Browser screen recordings by the system (Playwright `recordVideo`), desktop with consent in the portal.
- All layers in Kdenlive (zooms, circle, subtitles) — open choice for Kamil (option 2 from 2026-11-10).
- Shorts/posts/carousels/blog on the same rules (only after "jedz dalej").
- Rename the repo to content-pipeline; clean up `render/long/chunks` (810 MB, old hashes) -> _to_delete.
- Delete modules that caught nothing over 2 films.

## Not in scope (deliberately)
- Lip sync at the start of the long: Kamil 2026-11-10 "jakies opoznienia sprzetowe", measured 0 -> -41 ms; lip_check stays.
- Paid APIs, AI video: no (Kamil 2026-11-07).
