# Plan 2026-11-09: enforce "nothing skipped", then film 2026-11-04 from zero

Kamil 2026-11-09: "enforcowanie 3-4 razy ze sprawdzeniem i dopiero mapowanie, produkowanie od zera calosci i render calosci".
Start only on Kamil's "gotowe". State at the start: pipeline `aa4957a`, lip sync fixed (s01 +8.9 ms, old long +46 ms),
new work dir `render/montaz/2026-11-04-v5/work` (step-0 files hardlinked: crop, wav, sil, dtw.cw.json, lines.txt).

## Why
The last film missed features the system already had or had planned: the visual upgrade plan 2026-11-05 (steps 2-5:
pieces pinned to ids, drawn lines/circles, motion palette, `sketch` scene) never reached the research ledger, so no gate
knew it was missing; role agents use only what their card and the checklist name.

## Phase 1 — enforcement (4 locks), each a gate in code
| # | lock | blocks | done when |
|---|---|---|---|
| 1 | `style/capabilities.json`: every feature (card types, scene kinds, plan keys, sound/picture effects) -> owner role + checklist id or `"not_for": {form: why}` | — (data) | file covers every feature found by lock 2 |
| 2 | test: scan code (card types in `gfx/*.mjs`, plan keys passed by `build_edl.py`, scene kinds) -> each in capabilities.json with owner + check | a feature with no owner/check = red test, no commit | `tests/test_capabilities.py` green, and red when a fake feature is added |
| 3 | test: every item of `## Order of work` in `docs/designs/*.md` has a ledger row (`research_gate` then blocks a render while `todo`) | a planned item that silently never happens | test red on the 2026-11-05 visual plan until its rows exist |
| 4 | `film_check`: coverage per film — every capability for the form is used or skipped with a reason in the plan | an agent that did not know a feature | FAIL on a plan that ignores a required capability |
| + | role briefs get the capability list generated from the file | work from memory | brief generator in `team/` |

Verification 3-4 rounds (Kamil): each round = full tests + a deliberate break (fake feature, design item without a ledger row,
plan without a capability) that the gate must catch + a fresh-context reviewer looking for a feature the map misses.
Stop only when a round finds nothing new.

## Phase 2 — mapping
Generated report: capability -> role -> gate -> used in the last film? Holes go into the ledger (`todo`) or get a reason.
Visual upgrade 2026-11-05 steps 2-4 enter as ledger rows and are built (one commit + test + preview each); step 5 `sketch`
needs Kamil: handwriting font (own or ready Polish font) and background colour.

## Phase 3 — film from zero (team/RUNBOOK.md, roles 1-12, new artifacts only; role agents never read the old work dir)
story -> fact-check -> cuts/opening -> cards/scenes -> zooms -> sound -> shorts scout + plans -> stills (Kamil looks at 2 key
cards) -> film_check + critic + research_gate green.

## Phase 4 — render everything
`run_v4.sh` long + shorts -> gates incl. lip_check -> manifest stamp -> out_gate -> `out/RAPORT.md`; local only, Kamil watches.
Measured costs: long assemble 17 min with cache (more from zero), words_check cut 3.5 h throttled (decision: unthrottled at night?).

## Open for Kamil
- clap test: ~15 s, 5 claps in front of the camera with the normal recorder (camera v4l2 vs mic pulse = 2 clocks; lip_check
  cannot see a recorder offset because it compares against the recording)
- `sketch` font + background; whisper without the thread cap at night
- map holes without a gate (ADR-0023, pg-review 2026-11-09 product-3): b-roll author credits in the description, variety of post
  graphic types (`post_gfx`), EDL-only knobs (pip_size, sub_style, music_offset), `--acc-thumb` colour for thumbs accent "thumb",
  thumbs `arrow` without a gate; meme max_age 8 years (assumed); rembg/isnet for non-human memes (= a new model download)
