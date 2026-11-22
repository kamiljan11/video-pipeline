# RESEARCH-SHORTS: cutting 9:16 shorts from 2-person video podcasts (one wide camera)

Date: 2026-11-22. Method: ~20 WebSearch queries + ~45 pages fetched. Language of rules: English.
Status legend: CONSENSUS = >=3 independent sources agree; DISPUTED = sources differ; SINGLE = one source; VENDOR = only vendor marketing, no independent test; DERIVED = my own arithmetic (not from a source); UNVERIFIED = not confirmed on the page.
IMPORTANT caveat: almost ALL evidence is vendor blogs (OpusClip, Vizard, Klap, cut.pro, conbersa, quso...). No independent A/B study of split vs crop was found. No Reddit thread was retrievable (WebSearch returned none; reddit not reachable) -> r/NewTubers / r/podcasting / r/VideoEditing coverage = ZERO. No analysis of DOAC/Flagrant/Rogan/Polish clip channels' actual layouts found (only DOAC marketing/hook articles). Nothing on speaker-name tags, progress bars (zero sources).

## 0. Source index (S#)
S1 https://cut.pro/en/blog/vertical-framing-multi-person-podcast-2026
S2 https://www.opus.pro/blog/how-to-edit-podcast-shorts-like-a-pro-using-opus-clip-pc-mac (+ OpusClip help: Split layout only when both speakers in same frame; "Pin first speaker" brand-template switch; via search summary of opus.pro/blog/best-ai-podcast-and-webinar-clip-makers)
S3 https://www.opus.pro/blog/the-reframe-benchmark (vendor-run, 301 tests)
S4 https://www.conbersa.ai/learn/podcast-multi-camera-clip-strategy
S5 https://www.conbersa.ai/learn/podcast-clip-vertical-video-format
S6 https://www.conbersa.ai/learn/podcast-clip-captioning-best-practices
S7 https://agent.vizard.ai/how-to/stack-two-interview-speakers-in-one-vertical-frame.html
S8 https://agent.vizard.ai/how-to/switch-the-camera-to-whoever-is-talking-in-a-recorded-panel.html
S9 https://quso.ai/help/new-cut-magic
S10 https://quso.ai/blog/how-to-edit-podcast-shorts-like-a-pro.html
S11 https://lautus.ai/blog/horizontal-video-to-vertical/
S12 https://clipspeed.ai/blog/vertical-video-editing-guide.html
S13 https://joyspace.ai/speaker-highlight-method-automated-framing
S14 https://cut.pro/en/blog/auto-reframe-vertical-clips-2026
S15 https://frameos.studio/blog/how-to-make-shorts-from-podcasts
S16 https://www.overdigital.ai/article/how-we-built-podsplit (engineering write-up, LR-ASD+YuNet+pyannote 4+WhisperX)
S17 https://reap.video/blog/short-form-video-safe-zones
S18 https://www.opus.pro/blog/youtube-shorts-caption-subtitle-best-practices
S19 https://captions.ai/help/guides/creators/hook-repurposed-clip
S20 https://callummcdonnell.substack.com/p/meet-the-viral-editor-behind-steven (DOAC editor interview/summary)
S21 https://www.opus.pro/blog/ideal-youtube-shorts-length-format-retention (author = Head of Growth at OpusClip; no sample details)
S22 safe-zone guides: https://adaptlypost.com/blog/social-media-safe-zones-2026-complete-guide ; https://www.revid.ai/instagram-reels-safe-zone ; https://rightblogger.com/blog/tiktok-safe-zone-template ; https://brand-qa2.canadiantire.ca/en/ctr/design-system/omni-channel/motion/margins-and-safe-space.html (seen only via search snippets)
S23 Adobe/Resolve reframe: https://community.adobe.com/t5/premiere-pro-ideas/auto-frame-for-a-2-shot/idi-p/13652134 ; https://elements.tv/blog/comparing-the-auto-reframe-in-davinci-resolve-and-premiere-pro/ ; https://photography.tutsplus.com/articles/how-to-use-use-auto-reframe-to-crop-your-video-in-premiere-pro--cms-41934 (snippet) ; https://learn.adobe.com/premiere-pro/using/auto-reframe.html (snippet)
S24 https://riverside.com/university-videos/understanding-the-ai-speaker-view-in-the-magic-editor
S25 https://www.autocut.com/en/autocutpodcast/
S26 https://klap.app/blog/create-shorts-from-podcast
S27 https://descript.canny.io/feature-requests/p/one-click-podcast-to-reel-vertical-layout-split-screen-active-speaker
S28 https://www.choppity.com/features/automated-tracking ; https://www.kapwing.com/ai/auto-speaker-focus (no detail)
S29 https://discuss.pytorch.org/t/active-speaker-driven-video-cropping-what-the-inference-actually-cost/225447
S30 https://arxiv.org/abs/2002.03977v3 (MS virtual cinematography; 4K wide cam crop/zoom)
S31 https://hackernoon.com/talknet-asd-the-whos-talking-model-for-any-video
S32 https://github.com/Xaymar/obs-StreamFX/wiki/Filter-Auto-Framing ; https://habr.com/en/articles/1022298/ (403 on fetch; only search snippet: damped-oscillator virtual camera, Kalman "overkill")
S33 https://playpodcasts.com / https://www.opus.pro/blog/ideal... (404 / skipped) ; Vizard blog https://vizard.ai/blog/vizard-now-automatically-centers-the-active-speaker (snippet only)
OSS repos (read): O1 https://github.com/NaufalRizqullah/opensource-clipping ; O2 https://github.com/ClipsAI/clipsai ; O3 https://github.com/nmbrthirteen/podcli ; O4 https://github.com/FujiwaraChoki/supoclip ; O5 https://research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/ ; O6 https://github.com/TaoRuijie/TalkNet-ASD ; O7 https://github.com/Junhua-Liao/Light-ASD ; O8 https://github.com/Junhua-Liao/LR-ASD ; O9 https://github.com/SJTUwxz/LoCoNet_ASD ; O10 https://github.com/pyannote/pyannote-audio ; O11 https://huggingface.co/pyannote/speaker-diarization-3.1 ; O12 https://github.com/m-bain/whisperX ; O13 https://github.com/ShiqiYu/libfacedetection ; O14 https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet ; O15 https://github.com/deepinsight/insightface ; O16 https://github.com/google-ai-edge/mediapipe ; O17 https://huggingface.co/papers/2303.04439 (Light-ASD paper abstract) ; O18 https://arxiv.org/abs/2407.11915 (snippet)

## 1. Saturation report
- Total distinct sources actually read/fetched: ~45 pages (+ ~20 search-result summaries). Distinct *independent* voices on layout/caption rules are fewer (~12): most "blog" sources restate each other.
- Layout rules (single default, split for back-and-forth, hard-cut on turn, no cut on backchannel): first stated in S1 (source #1), repeated by S4, S5, S7, S8, S10, S11, S12, S13, S14, S15 -> saturation reached by ~source #8 (S8). Everything after only repeated it.
- Caption placement rules (seam for split, below chin / mid-frame for single): S1, S5, S6, S7, S9, S15, S17, S18 -> saturated by source ~#9.
- Safe-zone numbers: disagree each time (S5, S6, S12, S17, S18, S22, S1) -> NOT saturating, genuinely disputed; new sources keep giving new numbers.
- Hook/clip selection: S15, S19, S20, S26, S10 + search snippets -> saturated ~#6.
- OSS: new data kept arriving until O1/O3/S16/S29 were read; after ~12 repos/pages new items were re-listings.
- NOT saturated / gaps: Reddit (0), real clip channels (0), name tags/progress bars (0), independent retention experiments (0), pyannote/TalkNet CPU real-time factor (0 measured numbers).

## 2. RULES (numbered)

### A. Layouts and switching

R1. Default = full-height single-speaker crop following the person who has the floor. CONSENSUS (S1, S4, S5, S10, S11, S13, S15 + Adobe/Resolve users S23 ask for exactly this). 
R2. Stacked split (A top / B bottom, each ~1080x960) = ONLY for fast back-and-forth, joke+comeback, or when the question matters as much as the answer; avoid for long single-speaker stretches (silent half = dead space, speaker half the size). CONSENSUS (S1, S4, S11, S12, S13, S10, S27, O1, O3). Counter-view: one source (via search, playpodcasts/other, UNVERIFIED) argues static split is monotonous - supports "mix, don't leave it static".
R3. Blurred-background full frame (original 16:9 as middle band, blurred copy fills rest) = only 2-3 s moments (group laugh, someone enters, object shown); never default (picture shrinks to 1080x608 = 1/3 of screen height). SINGLE strong (S1) + S11 (numbers) + AutoFlip letterbox fallback (O5) + O1 fallback blurred pillarbox. Treat as a fallback for overlapping speech / lost faces.
R4. Reaction cutaway (listener's face) 1-2 s, only when the face actually reacts. S1 (SINGLE), S12 says reaction shots "more viral" (VENDOR claim). With ONE wide camera it is just a tight crop on the listener - implementable.
R5. Good clip uses 2-3 layouts in sequence, not one. SINGLE (S1); consistent with S4/S12.
R6. Switch ON the new speaker's first word/sentence start, not mid-word, not early. SINGLE (S1); S11: cut when the other starts answering. Implementable via WhisperX word timestamps + diarization turn start.
R7. Backchannel rule: laughs, "mm-hm", "yeah", "right", coughs do NOT trigger a switch. S1, S8 ("very short turns should not cut"). CONSENSUS-ish (2 sources + O3 logic).
R8. Minimum hold: sources disagree on numbers. Values: O1 default switch-hold 2.0 s (implemented default, MIT code); S1 "two switches within 1 s look like an error -> use split instead"; S4 (multi-cam) 3-7 s cadence, <3 s only for rapid back-and-forth, never >7 s on one angle (retention-loss number 10-25% UNSOURCED); S21 one cut per 2-4 s (OpusClip employee, no data). DISPUTED. Proposal for our engine (my synthesis, not sourced): min hold ~2 s (O1 default), if >=2 switches inside ~4-5 s -> flip to split for that stretch; speaker-turn < ~1 s = ignore.
R9. Overlapping speech: hold the current layout / go to the wide or split; do not pick a winner. S8, O1 (blurred pillarbox fallback). CONSENSUS (2 + O1).
R10. Hard cut vs glide: a speaker change = hard cut (instant, or <=0.2 s blend: O1 `--switch-blend-duration` default 0.0); NEVER slow pan between two people ("a slow pan reads as a mistake" S11; S16: lateral jump >15% frame width in <0.6 s = cut, smoothing never crosses a cut). Within one speaker's segment: slow glide to follow movement. CONSENSUS (S11, S16, S12 says "easing so pans look smooth" = conflicting; resolved by cut-between/glide-within).
R11. Do not leave the frame on the listener while the other talks (S11 check). Keep question+answer in same clip so the short stands alone (S11, S15: host for question, guest for answer; O3: "questions stay on the split, guest goes full frame on long answers").
R12. Opening frame: if a clip opens on a split with tiny faces, consider opening full-screen and splitting later. SINGLE (S1).
R13. Three+ people: base = full screen on speaker; 3-band split "almost never works on phone"; split only for 2 active. S1, S12 (60% active speaker grid), S26. N/A for our 2-person case.
R14. Pin the host in the TOP slot of the split (OpusClip "Pin first speaker") for a consistent mental map. SINGLE (S2) - ours: keep each person in a fixed slot for the whole clip (top=left person, or host top).
R15. Failure modes to guard: speakers sitting very close, constant movement, heavy graphics cut through middle (S7); crop between two faces shows neither (S11, S12); face-only tracking in multi-face scenes jitters between faces (S14); no face -> fallback center crop (S12) or largest face (S16). CONSENSUS.

### B. Captions, text, graphics

R16. Single-speaker: captions below chin, mid-lower frame, above bottom UI zone. S1 ("eyes upper third, captions just below chin, above bottom 35%"), S5/S6 (block top at 35-45% height, bottom at 60-70%), S15 (15-25% from bottom), S18 (centre third; keep out of top 20% and bottom 25%). CONSENSUS on "middle/lower-middle, not bottom"; numbers DISPUTED (see R27).
R17. Stacked split: captions in the SEAM between the two faces (centre of frame), word-timed; captions under the lower face collide with account name/description UI. CONSENSUS (S1, S7 "at the join", S9 auto-position avoiding faces, S27 wants layout-aware placement). 4 sources.
R18. Blurred-band layout: captions directly under the band (S1 SINGLE).
R19. Word-by-word highlight synced to speech, 2-5 words on screen, 1-2 lines max (S6; S18 says 5-7 words/line & 2 lines - DISPUTED words count; O1 default 5 words-per-sub, HORMOZI style). Effect size claims (+18-23%, +15-25%, +34%) are all unverified vendor numbers (dev.to/clamper, fluxnote, S21) -> treat as no evidence; only qualitative consensus.
R20. Speaker colour coding: distinct caption colour per person (S1; S18: white primary, yellow secondary); or small speaker label above line (S16 amber label; S12/S26 "speaker labels"). 3-4 sources, no effect data.
R21. Caption type: bold sans-serif (Montserrat/Inter/Poppins/Arial Black), white + outline or semi-opaque plate 60-80% (S6, S18, S10, S5). Contrast >=4.5:1 (S18, WCAG). Active word accent colour yellow/neon green (dev.to snippet, weak).
R22. Caption lead 0.1-0.3 s before audio, block duration ~0.3 s/word + 0.5 s (S18 SINGLE).
R23. Remove ums/false starts, fix proper nouns (S6, S15, S10, S20 "best producers retype every line" - DOAC marketing blog, UNVERIFIED).
R24. Do not stack burned-in + native captions on Reels (S17).
R25. On-screen hook text: <7 words, upper third, above UI, ADD context rather than repeat audio (search snippets: playbooks.com skill page - weak) vs S19: strongest hooks say the same idea in speech AND text at same moment. DISPUTED (repeat vs add). Both agree: large text in first frame, works muted.
R26. Name tags / lower thirds / progress bar: NO SOURCE found. S3 says OpusClip removes source lower thirds and renders its own. Treat as design decision: small name label once at first appearance of each speaker (2-3 s), top of split panels or via caption speaker label (S16 label approach). UNVERIFIED.

### C. Safe zones (1080x1920) - DISPUTED, no official pixel values
R27. Numbers by source:
- S1 (citing Meta, UNVERIFIED): keep free top 14%, bottom 35%, sides 6% each.
- S17: top ~15%, left/right 10-15%, bottom 25-35% ("working margins, not official").
- S5/S6: top 15%, bottom 20%, right 8-12% (captions).
- S12: content y>150, y<1650, x<930, x>60.
- S18: captions in centre third; out of top 20%, bottom 25%.
- S22: Reels top 210-270 px, bottom 310-670 px; Shorts bottom 288-300 px, right 96-192 px; universal 900x1400 centred (adaptlypost); TikTok clear area 895x1194 (rightblogger); Canadian Tire guide: 48 px sides, text from y=260.
- S17 explicitly: Meta/Google/TikTok publish safe zones mainly for ads; no permanent pixel box exists.
=> Conservative implementable rule: keep captions/faces inside x 60..930 (right rail), y ~290..1500 (top 15% / bottom ~22%); split seam caption centred near y~960 sits inside every variant. Verify visually in each app (preview draft). Right 10% keep faces out (S5, S17).

### D. Clip selection

R28. Self-contained: a new viewer understands without prior context; setup ~3-15 s max then payoff; cut off on cliffhanger/open question or payoff (S15, S10, S26, S19 + search snippets). CONSENSUS.
R29. Prefer: strong claims, surprising answer to a question, real disagreement host/guest, punchline, emotional peak, quotable line, story arc (S15, S26 "find where they disagree", S10, S20). Avoid mid-exchange tangents/context-dependent clips (S15). CONSENSUS (4). NO source ranks which type performs best.
R30. Always include the question with the answer (S11, S15, O3). 
R31. Length: S2 "30-90 s best" (vendor), S5 TikTok 21-34 s / Reels 30-60 s / Shorts 45-60 s (UNVERIFIED), S21 15-30 s highest retention, >45 s sharp drop (OpusClip head of growth, no data), S15 30-55 s, S1-search "20-45 s", S7 30-60 s, S20 (DOAC) ~90 s target, S10 table (TikTok 15-60, Reels 15-90, Shorts <=60), vivideo/soundstripe 30-60 s. DISPUTED; median claim ~30-60 s; <15 s underperform (S5), >90 s drops (S5). Our goal 20-60 s fits the middle.
R32. Yield: 60-min episode -> 8-12 clips; 30-min -> 4-6 (S15); Klap: 90-min -> 10-20+ (S26).
R33. Hook in first 1-2 s (TikTok/Reels) / 2-3 s (Shorts): start mid-thought, no intro/logo/pause; open with strongest line, or jump-cut past setup, or text overlay posing the question; tease best point early for longer clips; hook must match the payoff (S15, S19, S10, S20, S21 "50-60% of drop-off in first 3 s" UNVERIFIED). CONSENSUS (5).
R34. DOAC-style (VENDOR/secondary, UNVERIFIED): ~90 s, hook + lesson + emotional shift + cliffhanger; test opening with guest-in-chair vs B-roll (S20). A/B test and measure avg view duration; hold 70%+ to end = strong (S15, S20).
R35. Fill muted viewing: "70-85% watch muted" appears in many vendor posts without source -> UNVERIFIED; captions mandatory regardless.

### E. Crop math (DERIVED from sources + arithmetic)

R36. 9:16 from 16:9 at full height keeps 31.6% of width: 608 px of 1920 (S1, S11, S16 31.6%); from 4K (3840x2160) crop = 1215x2160, exact 1080x1920 output w/o upscaling (S11, DERIVED check: 2160*9/16=1215). Fixed centre crop (56% claim in S12 is wrong for 9:16 at same height - it's 31.6%; S12 "178% scale / 56% width" refers to fitting differently -> inconsistent, ignore).
R37. Two faces in one 9:16 window only works if both within 1215 px of 3840 (4K) i.e. heads close; with two people side by side at normal podcast spacing (~1/3 of frame width apart) -> impossible without tiny faces (S1, S11, S7). Hence single-follow or split.
R38. Split (DERIVED): output panel 1080x960 (9:8). Crop per panel from 4K source: width W, height 0.889*W. Using the full half of the frame W=1920 -> 1920x1707 (downscale 1.78x, no zoom), or tighter W=1215 -> 1215x1080 (still >=1:1 for 1080 out). Minimum sharp crop width = 1080 src px (1:1). Practical: W between 1080 and 1920. S12: 50/50 stack gives each face 540 px of the 1080 px width? (it says 540 px height - actually wrong unit; it is 960 px at 1080x1920) -> ignore number.
R39. Headroom/eye line: S12 head in top 30-40% of the frame with shoulders/torso visible; S11 eyes ~1/3 down; S5/S17 faces near vertical middle with headroom, out of far-right 10%; leave room for gestures (S12). For split panels apply the same per panel (eyes ~35-40% down the 960 px panel) - DERIVED.
R40. Lean-in / movement: smooth crop within segment (R10), extra horizontal margin when gestures; AutoFlip uses "core" vs "all" face box; in narrow crops only core box fits (O5). Re-measure per scene if people move (S7). Keep face-lost fallback: hold last position, then largest face (S16) or centre between.
R41. Source quality: record 1080p min, ideally 4K; 720p zoomed 300% blurry (S12); RØDE: 4K enables crop reframing (search snippet). Output 1080x1920, H.264 MP4, 30 fps, 8-12 Mbps (S5, S10 snippet).

### F. Automation, smoothing, virtual camera

R42. Pipeline pattern used by working open implementations (S16, O1, S29): proxy 720p -> face detect ~1-5 fps + IoU tracker -> diarization (pyannote) + word timestamps (WhisperX) -> ASD (LR-ASD/TalkNet) or audio-only diarization+face-position mapping -> schedule of (speaker, crop) -> median filter -> hard cuts snapped to turn starts -> Catmull-Rom + Gaussian smoothing within segments (sigma ~0.75 s, S16) -> ffmpeg crop with per-frame expressions (sendcmd) -> libass captions. 
R43. Smoothing parameters (O1 defaults, tested code): detect interval 0.25 s, deadzone 0.15, catch-up smooth 0.30, jitter threshold 5 px, snap (hard-cut) threshold 0.25, layout smooth window 12 frames (~0.5 s), scene-cut reset threshold 18, conf 0.55. S16: sample 5/s, 5-wide median, 15% / 0.6 s cut test, snap to scene change within 0.5 s. AutoFlip: low-degree polynomial path fit, three modes stationary/pan/track (O5). StreamFX uses smoothing + stability + prediction (no Kalman numbers, S32). Habr (snippet only, UNVERIFIED): damped oscillator, Kalman overkill for few faces. => Kalman not required; deadzone + median + per-segment Gaussian is enough (S16, O1, S32 snippet).
R44. Cost lesson (S29): pipeline feeding cost dominates, not the model: ASD forward pass for 2 people 1.2 s per 60 s clip on RTX 3060; re-detecting with YOLO at 25 fps = +452% time; reuse tracker boxes (+15%); use ffmpeg to sample frames (20x faster than OpenCV decode loop). S16: face sampling at 1 fps = ~5x speed-up without drift.
R45. Fallbacks (S16, O1, S12): no ASD signal -> largest face; no face -> centre/last known; overlap -> wide/blurred.
R46. Auto-reframe in editors: Premiere Auto Reframe has Slower/Default/Faster motion; picks subject itself, no reference point; two-person talk-show shots not handled -> manual keyframes; workaround = duplicate wide shot on 2 tracks, frame A on one, B on other, switch tracks (S23, Adobe community). Resolve Smart Reframe (Studio only) one focal point/ reference point; moves a lot, adds motion to static shots, slower (~39 fps) (S23 elements.tv, search snippets). Manual keyframing 5-10 speaker changes/60 s clip = 10-15 min (S12). => Commercial NLE auto-reframe does NOT solve our two-person case; confirmed by 3 sources.
R47. Commercial tools: OpusClip Split/Three/Four layouts only if all speakers in the same source frame; active speaker detection; "pin first speaker"; segments frame into panels, clamps face crops to panel (S2, S3 - vendor-run benchmark OpusClip 2.40-2.59/3 vs others, caveat: self-published). Vizard: stack two speakers from ONE wide recording, measured pixel crops, captions at join, fails on close-seated speakers / >2 / constant movement (S7). Riverside Smart Layouts: style + switching frequency (low for long-form, high for short-form) + cutaway (S24). AutoCut Podcast: user-set min/max time per camera, needs separate mics (S25). Klap, quso CutMagic (Two Speakers layout, auto subtitle position, S9), Choppity (S28).

## 3. Open-source landscape and licences (we sell software -> permissive only)

| Component | What | Licence (as seen) | CPU feasibility / notes |
|---|---|---|---|
| opensource-clipping (O1) | Full pipeline: Faster-Whisper, LLM highlights, face-track crop, split-screen, dynamic-split, camera-switch (hold 2 s, pyannote 3.1), HORMOZI karaoke subs | MIT (sidebar) | CPU supported for Whisper (int8); needs HF_TOKEN for diarization modes; Gemini default LLM. Best OSS reference for params. |
| ClipsAI (O2) | clip finding (WhisperX) + resize "reframes on current speaker" via pyannote | MIT | Needs HF token; face-detection details not on page (UNVERIFIED) |
| podcli (O3) | MCP/CLI clipper, face tracking, split/multicam | AGPL-3.0 (commercial licence available) | PROBLEM for us; read only |
| SupoClip (O4) | clipper, 9:16 face-centred | "SupoClip Noncommercial Source License 1.1" (companies/paid hosting need permission); secondary sources said AGPL (conflict) | NOT usable |
| AutoFlip / MediaPipe (O5, O16) | shot detect + saliency + camera path fit | MediaPipe repo Apache-2.0 (sidebar); AutoFlip needs OpenCV 3 + Bazel | Runs on CPU (TFLite); old, not speaker-aware |
| TalkNet-ASD (O6) | AVA ASD, mAP 92.3 val | MIT | Python 3.7; CPU possible by editing cuda->cpu (no speed given) |
| Light-ASD (O7, O17) | ~1.0M params, 0.6 GFLOPs, 94.06-94.1 mAP | MIT | Light; per-frame 0.1-4.5 ms per paper (hardware unnamed -> UNVERIFIED for CPU); robot study: still not real-time on their setup (O18) |
| LR-ASD (O8) | 0.84M params, 0.51 GFLOPs, 94.5 mAP (IJCV 2025) | MIT | Used in S16 production pipeline, <1M params |
| LoCoNet (O9) | ASD | NO licence stated on page | skip |
| pyannote.audio (O10) | diarization | code MIT; models gated (accept conditions + HF token); community-1 CC-BY-4.0 (per WhisperX README); precision-2 paid API | 3.1 pipeline "runs on CPU by default" (O11); no CPU RTF figure found (UNVERIFIED); H100 community-1 ~31 s/h audio |
| speaker-diarization-3.1 (O11) | pure PyTorch, 16 kHz mono | MIT but gated | |
| WhisperX (O12) | word-level timestamps via wav2vec2 | BSD-2-Clause | CPU int8 ok; overlapping speech weak; needs per-language align model (Polish available? UNVERIFIED) |
| YuNet / OpenCV zoo (O14), libfacedetection (O13) | CPU face detector | YuNet files MIT (zoo); libfacedetection licence text not shown (UNVERIFIED; commonly BSD-3) | libfacedetection 640x480 ~20 FPS single thread i7, ~153 FPS 16 threads (O13) |
| MediaPipe BlazeFace (O1 default) | face detector | Apache-2.0 | CPU fast |
| InsightFace (O15) | code MIT, but pretrained models NON-COMMERCIAL (some need licence) | avoid for product | |
| Ultralytics YOLOv8 (used in O1, S29) | licence NOT checked - Ultralytics is AGPL-3.0 as far as I know (UNVERIFIED here) | avoid | |

Notes: "auto-podcast-clipper" as a named GitHub repo was NOT found. TalkNet weights/training data (AVA) licence not checked.
CPU verdict: SINGLE-wide-camera 2-person case needs only 2 faces: YuNet/BlazeFace at 1-5 fps + diarization turns mapped to left/right face by 1st-appearance order, with LR-ASD only as an optional verifier on ambiguous segments. (my synthesis). Evidence: S16 (1 fps face sampling, <1M param ASD), S29 (ASD pass 1.2 s/60 s clip on GPU; feed cost dominates). CPU real-time numbers for ASD/pyannote: none found -> must benchmark ourselves.

## 4. Consensus vs disputed (summary)
CONSENSUS: single-speaker default; split for rapid exchange; hard cut on turn; ignore backchannels; captions in seam for split / mid-lower for single; word-highlight; hook in 1-3 s; self-contained clips with question+answer; commercial auto-reframe fails on 2-person wide shots.
DISPUTED: min hold (1 s / 2 s / 3-7 s / 2-4 s); safe-zone numbers; clip length (15-30 vs 30-60 vs 90); caption words/line (2-5 vs 5-7); hook text repeat-vs-add; static split vs dynamic.
UNVERIFIED everywhere: all retention/engagement percentages (+15-34% captions, 50-60% drop in 3 s, 10-25% from long holds, 70-85% muted).

## 5. Suggested defaults for our engine (synthesis, not sourced as a whole)
- Layout state machine: SINGLE(follow speaker) <-> SPLIT (when >=2 speaker changes in <=4 s or overlap > ~1 s) ; BLUR-WIDE fallback <=3 s; optional reaction cut 1-2 s.
- Switch on speaker-turn start (WhisperX word time), min turn 1 s to count, min hold 2 s, hard cut (0-0.2 s blend), snap to nearest frame; within segment: median(5) + deadzone 0.15 + Gaussian ~0.75 s, never across cuts.
- Split panels 1080x960, eyes ~35-40% down panel, fixed slots (host top), caption seam at y~960, speaker colours.
- Single: head top 30-40%, captions just below chin, inside x 60..930, y ~290..1500.
- Clip picker: Q+A pair, claim/disagreement/punchline, 20-60 s, hook text <=7 words in first frame (speech+text), end on payoff/cliffhanger; check standalone.
- Dev stack with permissive licences only: faster-whisper/WhisperX (BSD/MIT), pyannote 3.1/community-1 (MIT/CC-BY; gated), YuNet or BlazeFace, LR-ASD/Light-ASD/TalkNet (MIT), ffmpeg (check build is LGPL not GPL if bundled - not researched).
