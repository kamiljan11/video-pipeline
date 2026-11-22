# Repo survey: what open-source AI video editors do better than our pipeline

Date: 2026-11-22. Method: `gh api repos/...` (stars, licence, pushed_at read 2026-11-22), README/SKILL/source files read via `gh api .../contents/...`. Nothing installed or cloned. "Last commit" = GitHub `pushed_at`. A claim without a URL was not verified and is marked [UNVERIFIED].

Our weak spots (from style/NOTES_LOG.md rows 58-64): drawn scenes with hand-placed x/y (row 64: "tragiczny chaos w rysowaniu"), too many cards / graphics that serve no purpose (row 63: solo-talk packaging on a 2-person podcast), purposeless zooms (rows 61-62), inconsistent colours, two-person podcasts edited like solo talks.

---

## 1. Complete systems (adopt wholesale or rebuild on?)

None of these is a drop-in replacement for our pipeline. Two are close in shape (openshorts for shorts + podcast layout, video-use / OpenMontage for the agent loop). None ships a good "explainer drawing" engine for a talking-head long.

### 1.1 mutonby/openshorts - verdict: BORROW PARTS (podcast layout logic), do not adopt
- URL: https://github.com/mutonby/openshorts | 9707 stars | MIT | last commit 2026-11-22
- Covers: YouTube link/upload -> moment picking -> 9:16 reframe -> captions -> hook line -> per-platform titles -> in-browser transcript editor -> posting (README). Long-form output with graphics: NO (shorts only).
- Quality evidence: README embeds a real before/after GIF (`screenshots/split-before-after.gif`, "Real OpenShorts output, not a mock-up", CC BY source podcast). I could not view the GIF; I read the claim only. Marketing README, so treat quality as [UNVERIFIED] until someone watches the demo.
- Podcast handling (the thing we lack): two people are stacked 9:16 instead of shrinking the wide shot, captions sit on the seam, it cuts back to a face-tracked crop for one-person shots (README). Active speaker from mouth movement plus audio energy: https://github.com/mutonby/openshorts/blob/main/active_speaker.py
- Local on Linux CPU: README says Docker, 8 GB+ RAM, "5 to 8 min per 8-min video on CPU". Needs Gemini key (paid API) for picking/layout; with local LLM some features degrade (hook grounding "Gemini-only", docs/architecture/layouts-and-reframing.md). Paid API conflicts with the owner's subscription-only rule, so the LLM part must be re-pointed.
- Verdict: do not rebuild on it (web app, Docker, Gemini-coupled, shorts only). Take the ideas in section 3 (changes 2, 5).

### 1.2 browser-use/video-use - verdict: BORROW PARTS (agent loop and self-eval), possibly adopt as the cutting core for talking heads
- URL: https://github.com/browser-use/video-use | 31447 stars | MIT | last commit 2026-10-08
- Covers: Claude Code skill; transcribe (ElevenLabs Scribe, word timestamps + diarization + audio events) -> packed phrase transcript -> LLM writes EDL -> per-segment render with 30 ms fades -> subtitles last -> overlays from HyperFrames/Remotion/Manim/PIL in parallel sub-agents -> self-eval on the rendered output at every cut (README, SKILL.md).
- Quality evidence: README links a 15 s demo on TikTok (not viewed). [UNVERIFIED]
- Local: ffmpeg + Python + Node; needs ElevenLabs API key (paid) for transcription; we use whisper.cpp, so swap is needed. Light on CPU (it is an ffmpeg wrapper).
- Weak for us: its animation section says "get the palette ... from the conversation", i.e. no enforced design system; no podcast multicam logic. https://github.com/browser-use/video-use/blob/main/SKILL.md
- Verdict: we already have EDL + word-boundary cutting (build_edl.py). Borrow: render self-eval at each cut, hard-rules list, `timeline_view` (filmstrip + waveform + word labels PNG) as a cheap visual check for our film_check.

### 1.3 OpenMontageInc/OpenMontage - verdict: BORROW IDEAS ONLY (AGPL: do not copy code)
- URL: https://github.com/OpenMontageInc/OpenMontage | 82386 stars | AGPL-3.0 | last commit 2026-11-16
- Covers end to end: pipelines `talking-head`, `podcast-repurpose`, `clip-factory`, `animated-explainer` (pipeline_defs/*.yaml), each a chain of director skills (idea -> script -> scene -> assets -> edit -> compose -> publish) with a reviewer gate per stage and human checkpoints (pipeline_defs/podcast-repurpose.yaml, skills/meta/reviewer.md).
- Quality evidence: README embeds showcase videos (SIGNAL FROM TOMORROW, THE LAST BANANA ...) - these are generative-AI films, not talking-head/podcast; I did not watch them. No showcase of a podcast edit seen. [UNVERIFIED for our use case]
- Local: Python + Node/Remotion, free stock + Piper TTS path exists; most showcases use paid generators (Kling, Veo). Remotion needs a company licence if we grow past its free tier (see risks).
- Verdict: AGPL-3.0 means copying code into our MIT repo is not allowed. Its useful parts are documents, and ideas can be reimplemented: see changes 1 and 6.

### 1.4 heygen-com/hyperframes (+ Studio app) - verdict: BORROW PARTS (layout audit, motion doctrine); consider as a renderer later
- URL: https://github.com/heygen-com/hyperframes | 88225 stars | Apache-2.0 | last commit 2026-11-22
- Covers: HTML/CSS/GSAP -> deterministic MP4, agent skills, lint and checks, Studio GUI (README). Edits user footage too ("script-based editing", "edit your own footage" tiles in README). Not an auto-editor for podcasts.
- Quality evidence: showcase page https://hyperframes.heygen.com/examples (not viewed). Our own renderer is already HTML->Chrome->.mov, so the concepts transfer directly.
- Local: Node >= 22, headless Chrome; CPU OK. Free CLI under Apache-2.0 (Studio Pro is paid, not needed).
- Verdict: do not migrate renderers. Do take `layoutAudit` (change 3) and `motion-doctrine` (change 7). Apache-2.0 allows reuse of code with notice.

### 1.5 nexu-io/openmotion and FireRedTeam/FireRed-OpenStoryline - verdict: SKIP (for our case)
- openmotion: https://github.com/nexu-io/openmotion | 15254 | Apache-2.0 | 2026-11-22. Recreates a reference video with your brand kit, "Motion.md" shot format. Aimed at promo/brand videos, not talking-head. 
- OpenStoryline: https://github.com/FireRedTeam/FireRed-OpenStoryline | 3731 | Apache-2.0 | 2026-07-31. Stock-footage + narration agent with "Style Skills". Not talking-head.

### 1.6 Clip-picker apps: Anil-matcha/AI-Youtube-Shorts-Generator, fralapo/clippyme, AgriciDaniel/claude-shorts - verdict: SKIP / borrow rubric
- https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator | 6470 | MIT | 2026-11-21. LLM highlight + Whisper + auto crop. We already have scout-shortow.
- https://github.com/fralapo/clippyme | 74 | MIT | 2026-10-14. Active-speaker tracking, "camera that stays still within each shot" (README).
- https://github.com/AgriciDaniel/claude-shorts | 475 | MIT | 2026-07-11. 5-dimension segment rubric (hook, coherence, emotion, value density, payoff); content-type classifier (talking-head / screen / podcast) at step 3 (README).

---

## 2. Whether a visual is needed at all (content earns the graphic)

| Repo | Mechanism | Evidence |
|---|---|---|
| OpenMontage talking-head scene-director | Visual only when the transcript contains a trigger: technical term -> definition card; number/percent -> stat card; A vs B -> comparison; list -> checklist; data/ranking -> chart; process -> progress; topic change -> title. Reads full transcript first ("most important step"), lists "where do they use numbers / compare / list / introduce jargon". Hard cap "3-6 overlays per minute ... more is distracting", 3-5 s each, timed to the spoken words, at natural pauses, "vary the types". Every overlay row in the plan carries a "Why" column; user approves the plan before render. | https://github.com/OpenMontageInc/OpenMontage/blob/main/skills/pipelines/talking-head/scene-director.md |
| OpenMontage slideshow_risk | Scores a plan 0-5 on 6 dimensions incl. `decorative_visuals` ("scenes decorate instead of communicate"), `weak_motion` ("motion exists but has no narrative purpose"), `weak_shot_intent`, `typography_overreliance`, `repetition`; average >= 4.0 = fail, do not compose. Heuristic code, not a VLM. (AGPL: reimplement, do not copy.) | https://github.com/OpenMontageInc/OpenMontage/blob/main/lib/slideshow_risk.py |
| HyperFrames visualization registry | Routing table "show, don't tell": strongest class first (recreate the real UI > honest UI analogue > terminal > checklist as last resort); "Never invent UI that implies a screen that doesn't exist". | https://github.com/heygen-com/hyperframes/blob/main/.claude/skills/changelog-video/references/visualization-registry.md |
| openshorts layout_picker | One closed-choice decision per source ("none / screencast / split"), never a measurement; `apply()` only adds, never removes a user choice; default is plain crop = do nothing unless evidence. | https://github.com/mutonby/openshorts/blob/main/docs/architecture/layouts-and-reframing.md |
| openshorts hook_grounding | Hook text is rewritten only if >= 25 % of the clip is on-screen content (frames sent to a VLM). Same pattern: act only when a measured condition holds. | same doc |
| video-use | Animations only "when requested"; palette must be agreed first. No purpose test. | SKILL.md |

Pattern to copy: a trigger table (number, A-vs-B, list, process, term, topic change) plus a per-minute cap plus a mandatory "why" field per graphic, enforced by a checker. None of these repos has a "draw an explainer scene" engine, so for process explanations nobody shows a better solution than ours; the gain is in gating and layout.

---

## 3. Repo table (23 repos)

| Repo | URL | Stars | Licence | Last commit | Category | What to take |
|---|---|---|---|---|---|---|
| browser-use/video-use | https://github.com/browser-use/video-use | 31447 | MIT | 2026-10-08 | LLM edit agent | render self-eval per cut, `timeline_view`, 12 hard rules, project.md memory |
| OpenMontageInc/OpenMontage | https://github.com/OpenMontageInc/OpenMontage | 82386 | AGPL-3.0 | 2026-11-16 | LLM edit agent / pipelines | trigger->overlay table, per-minute cap, reviewer gate with proposed_fix, slideshow-risk scoring (ideas only) |
| heygen-com/hyperframes | https://github.com/heygen-com/hyperframes | 88225 | Apache-2.0 | 2026-11-22 | HTML motion graphics | layoutAudit (overlap, text over face, safe zone, caption collision, connector detached), motionAudit, lint codes, motion-doctrine, `frame.md` brand spec |
| mutonby/openshorts | https://github.com/mutonby/openshorts | 9707 | MIT | 2026-11-22 | AI shorts, podcast reframe | split layout for 2 people, active_speaker from mouth + audio, caption seam, hook placement avoiding faces, closed-choice layout picker with 12 stills |
| nexu-io/openmotion | https://github.com/nexu-io/openmotion | 15254 | Apache-2.0 | 2026-11-22 | motion graphics agent | brand kit idea; Motion.md shot file (skip) |
| FireRedTeam/FireRed-OpenStoryline | https://github.com/FireRedTeam/FireRed-OpenStoryline | 3731 | Apache-2.0 | 2026-07-31 | LLM edit agent | reusable "Style Skills" idea (skip) |
| fralapo/clippyme | https://github.com/fralapo/clippyme | 74 | MIT | 2026-10-14 | shorts, active speaker | camera still within a shot, switch to letterbox |
| AgriciDaniel/claude-shorts | https://github.com/AgriciDaniel/claude-shorts | 475 | MIT | 2026-07-11 | shorts, captions | 5-dim segment rubric, cursor-follow crop, boundary snap |
| Anil-matcha/AI-Youtube-Shorts-Generator | https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator | 6470 | MIT | 2026-11-21 | shorts | nothing new for us |
| harry0703/MoneyPrinterTurbo | https://github.com/harry0703/MoneyPrinterTurbo | 145084 | MIT | 2026-11-22 | topic -> stock-footage shorts | skip (different product) |
| FujiwaraChoki/MoneyPrinterV2 | https://github.com/FujiwaraChoki/MoneyPrinterV2 | 32498 | AGPL-3.0 | 2026-09-15 | automation | skip, AGPL |
| remotion-dev/remotion | https://github.com/remotion-dev/remotion | 74947 | custom (free for individuals / small orgs, company licence above a size; LICENSE.md) | 2026-11-22 | React motion graphics | only if we ever leave HTML cards; licence check needed |
| remotion-dev/template-tiktok | https://github.com/remotion-dev/template-tiktok | 308 | none stated | 2026-11-09 | caption template | whisper.cpp -> TikTok captions reference |
| motion-canvas/motion-canvas | https://github.com/motion-canvas/motion-canvas | 20144 | MIT | 2026-07-02 | programmatic animation | generator-based timeline + auto layout (flex-like) for explainer scenes; evidence: repo description "Visualize Your Ideas With Code"; layout claim [UNVERIFIED, not read] |
| midrender/revideo | https://github.com/midrender/revideo | 4225 | MIT | 2026-07-15 | programmatic video | Motion Canvas fork for headless rendering; same [UNVERIFIED] note |
| ManimCommunity/manim | https://github.com/ManimCommunity/manim | 42808 | MIT | 2026-11-22 | explainer animation | `arrange`/`next_to` relative placement instead of absolute coords [UNVERIFIED, not read] |
| 3b1b/manim | https://github.com/3b1b/manim | 96818 | MIT | 2026-09-09 | explainer animation | reference only |
| kieler/elkjs | https://github.com/kieler/elkjs | 2908 | EPL-2.0 | 2026-11-09 | graph auto layout | layered (Sugiyama) layout with ports computes node/edge positions; "a graph layout engine only", we render |
| eclipse-elk/elk | https://github.com/eclipse-elk/elk | 382 | EPL-2.0 | 2026-11-18 | graph auto layout | source of the algorithms |
| dagrejs/dagre | https://github.com/dagrejs/dagre | 5863 | MIT | 2026-10-24 | graph auto layout | lighter DAG layout, MIT, easiest to bundle |
| terrastruct/d2 | https://github.com/terrastruct/d2 | 25891 | MPL-2.0 | 2026-11-22 | diagram language | text -> diagram, selectable layout engine (`layout-engine: elk` in its README), themes by id |
| excalidraw/excalidraw | https://github.com/excalidraw/excalidraw | 136127 | MIT | 2026-11-21 | hand-drawn style | rough style reference; we already have rough_lib.mjs |
| mermaid-js/mermaid | https://github.com/mermaid-js/mermaid | 91194 | MIT | 2026-11-22 | diagram language | layout via dagre/ELK; text DSL an LLM writes reliably |
| m-bain/whisperX | https://github.com/m-bain/whisperX | 25596 | BSD-2-Clause | 2026-11-21 | ASR + diarization | wav2vec2 forced alignment word times + pyannote speaker labels (README) |
| pyannote/pyannote-audio | https://github.com/pyannote/pyannote-audio | 10832 | MIT | 2026-11-19 | diarization | who speaks when, for podcast cuts |
| Breakthrough/PySceneDetect | https://github.com/Breakthrough/PySceneDetect | 5617 | BSD-3-Clause | 2026-11-22 | shot detection | cut detection on multi-cam sources |
| Junhua-Liao/Light-ASD | https://github.com/Junhua-Liao/Light-ASD | 197 | MIT | 2025-03-23 | active speaker detection (CVPR 2023) | stale; audio-visual ASD model, heavier than openshorts' mouth-motion heuristic |
| jianfch/stable-ts | https://github.com/jianfch/stable-ts | 2290 | MIT | 2026-05-30 (archived) | timestamps | skip, archived |
| mifi/lossless-cut | https://github.com/mifi/lossless-cut | 46326 | GPL-2.0 | 2026-11-22 | manual cutting | skip, GPL |

Not found / removed from my list: several guessed repo names returned 404 (e.g. TalkNet-ASD under that owner, mediapipe/mediapipe, Anil-matcha/Opus-Clip-Alternative); they are not in the table.

---

## 4. Top 8 changes, ranked by expected quality gain / effort

1. **Gate every graphic by content trigger + per-minute cap + "why" field, enforced by a checker.** Shows: OpenMontage scene-director (3-6 overlays/min, trigger table, Why column) and slideshow_risk (`decorative_visuals`, `weak_motion`). Changes: team/roles/motion-designer.md and the scout role (add trigger table: number, A-vs-B, list, process, term, topic change), style/checklist.json (`long.explainer_count`, `long.graphics`: cap per minute, every card/scene needs `why` and `trigger` keys), film_check.py (fail when a card has no trigger or density exceeds cap, replacing the density-quota logic). Effort: low. Gain: highest, directly answers "scenes serve no purpose".
2. **Podcast = its own edit grammar: stacked two-person layout, speaker-driven cuts, captions on the seam.** Shows: openshorts (README split layout; active_speaker.py: mouth motion + audio energy, per-speaker normalised, windows of 0.4 s, "unclear" windows do not vote). Changes: podcast.py (decide per scene: two-shot stack vs single-speaker crop based on both people actually taking turns), face_track.py (mouth-region activity), build_edl.py (cuts follow speaker, not zoom quota). Effort: medium. Gain: high. Reimplement, MIT so code reuse also allowed with notice.
3. **Automatic layout audit on rendered stills, replacing eyeballing.** Shows: HyperFrames `layoutAudit.ts` issue codes: `content_overlap`, `text_box_overflow`, `text_over_face`, `caption_zone_collision`, `outside_safe_zone`, `connector_detached`, `connector_orphan`, `canvas_content_at_edge`. Changes: gfx/scene_check.mjs (add the same checks on DOM boxes per frame: overlap between pieces, stamp-on-arrow, arrows crossing, text over face rectangle), film_check.py. Effort: medium. Gain: high (rows 63-64 describe exactly overlap and crossing arrows). Apache-2.0 allows borrowing with notice.
4. **Auto layout of scenes by a graph engine instead of hand-placed x/y.** Shows: elkjs layered layout with ports (README), dagre (MIT), D2 with `layout-engine: elk`, Mermaid. Changes: gfx/scene_lib.mjs (`flow`, `grid`, `timeline`, `table` get positions from dagre/ELK; the scene spec lists nodes and edges only, no coordinates; reading order = layout rank). Effort: medium-high. Gain: high for flow-type scenes. Licence: elkjs EPL-2.0 is weak copyleft per file; dagre MIT is the safe default.
5. **Closed-choice decisions made from a few stills, not free-form generation.** Shows: openshorts layout_picker (12 frames at 1024 px, "decision between closed options, not a measurement", 92-96 % on 48 hand-labelled clips, only adds options) and hook_grounding (act only if >= 25 % of clip is on-screen content). Changes: where an LLM/VLM picks layout, zoom or graphic type, restrict output to an enum and log it; applies to podcast.py layout choice and scout role. Effort: low. Gain: medium.
6. **Reviewer gate that critiques with a concrete fix, per stage.** Shows: OpenMontage skills/meta/reviewer.md (every critical finding must carry `proposed_fix`, otherwise downgraded to investigation; findings must cite a field or frame), video-use self-eval on the rendered output at every cut. Changes: film_check.py output format (finding + evidence frame + proposed fix), team roles. Effort: low-medium. Gain: medium. Idea only for OpenMontage (AGPL).
7. **Motion doctrine: motion must have a cause and direction continuity; ban idle wobble; stillness before climax.** Shows: HyperFrames `motion-doctrine` ("ban on idle wobble - motion must PERFORM, not breathe") and `motionAudit.ts` codes `motion_frozen`, `motion_appears_late`, `motion_out_of_order`. Changes: gfx/motion_tokens.mjs, podcast.py `single_drift`/`word_punches` (rows 61-62: a drift or punch is allowed only when a trigger word/emphasis exists), film_check `long.punch`. Effort: low-medium. Gain: medium; answers "purposeless zooms".
8. **One brand/design spec file with locked palette and a single accent, validated before render.** Shows: HyperFrames docs/prompting/design-systems.mdx (`frame.md` frontmatter with exact hex and fonts; "Strict - brand colors, fonts ... scaled up for the medium - type sizes, border weight"; web 1px borders vanish after H.264); video-use example palette "<= 2 accent colors, ~40 % empty space"; OpenMontage `visual-style.md` spec with extractors (from site/video/PDF). Changes: style/ theme (gfx/theme_lib.mjs), a validator in film_check that rejects any hex not in the palette. Effort: low. Gain: medium (colour consistency).

Also worth doing, smaller: `timeline_view`-style filmstrip+waveform PNG at each cut for visual QA (video-use); whisperX for aligned words + diarization labels when two voices share one mic (https://github.com/m-bain/whisperX).

---

## 5. Risks

- **Licences.** OpenMontage and MoneyPrinterV2 are AGPL-3.0; lossless-cut is GPL-2.0. Do not copy code from them into our MIT repo; ideas and documented rules only (rewrite from scratch, do not paraphrase code line by line). Apache-2.0 (hyperframes, openmotion, OpenStoryline) and MIT code may be reused with the notice kept. elkjs/ELK are EPL-2.0 (file-level copyleft; fine as an npm dependency, modifications to ELK files must be shared). D2 is MPL-2.0 (same file-level logic). Remotion has a custom licence: free for individuals / small for-profit orgs, company licence above a size (LICENSE.md in the repo) - do not adopt without reading it for the owner's situation.
- **Paid APIs.** openshorts needs Gemini, video-use needs ElevenLabs, OpenMontage showcases use Kling/Veo. Owner rules: no paid AI video, subscription-only infrastructure. Any adoption must replace those calls with whisper.cpp and Claude in-session.
- **Unverified quality.** I saw READMEs and source, not rendered videos. "Looks polished" claims for every complete system are marketing until someone watches a demo; I recommend the owner watch the openshorts split GIF and the HyperFrames examples page before any adoption decision.
- **Not read in depth:** Motion Canvas, Revideo, Manim layout APIs (rows marked [UNVERIFIED]); Light-ASD last commit is 2025-03-23 (stale).
- **No complete system does what the owner wants end to end** (podcast long + shorts + purposeful graphics). Rebuilding on one of them would lose our face tracking, EDL, theme, and checklist work; patching with changes 1-3 is cheaper.
