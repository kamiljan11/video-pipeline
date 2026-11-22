# RESEARCH: editing long-form 2-person video podcasts (1 wide camera + multicam)
Date: 2026-11-22. Method: WebSearch + WebFetch only (host: laptop). reddit.com is blocked for the crawler (API 400) -> NO Reddit sources.

## 0. Evidence quality (read first)
- ~58 distinct URLs consulted (fetched or search-snippet). Mostly vendor blogs, docs, forum threads, 2 academic papers, 3 GitHub READMEs. NO controlled study of shot length / retention for podcasts.
- **Named shows (Diary of a CEO, Huberman, Lex Fridman, Flagrant, Rogan, Imponderabilia, Dwie Lewe Ręce, Rozmowy w Karecie, Kryzys Wieku Średniego, Wojewódzki&Kędzierski, Magdalena Bilska): NO source found describing their editing grammar.** Only: DOAC trailer editing (outside scope), Fridman clip-captions advice from a clip vendor, Imponderabilia = Google blog w/o production detail. Anything about them = UNVERIFIED; must be observed by watching episodes (frame-by-frame sampling) — not from the web.
- No Polish-language editor sources on this topic were found (several PL queries returned generic listicles).
- Saturation: new queries 1-12 (~25 sources) gave the core rules; from ~source 25 onward every new source repeated: "favor active speaker + wide for shared moments", "don't switch on every acknowledgement", "J/L cuts", "4K punch-in ~200%", "keep some crosstalk", "separate tracks". Genuinely NEW info after that came only from tool docs (Descript, AutoCut, opensource-clipping, pyannote, Light-ASD, TalkNet, WhisperX) and caption/YouTube specifics. Numeric shot-length rules: never appeared in any source (explicitly "no golden rule").

## 1. CONSENSUS rules (>=3 independent sources)
Numbering: R# ; (n) = number of sources; URLs below each. [INF] = my inference/derivation, not a source claim.

**R1 (6). Don't hold one static shot for the entire episode; make at least 2 distinct framings (wide + per-person).** With one camera this means punch-ins.
- Descript don'ts https://www.descript.com/blog/article/adding-video-to-your-podcast-avoid-these-common-mistakes
- B&H https://www.bhphotovideo.com/explora/node/124651
- Spotify https://creators.spotify.com/resources/video-podcast-editing
- Adobe community (Zoom-call podcast) https://community.adobe.com/t5/premiere-pro/editing-a-zoom-call-for-a-video-podcast/m-p/11766130
- Rizzle/LinkedIn teardown (holding same 2-host layout 45 min = monotony) https://bd.linkedin.com/in/nabilhassan47
- Podpage https://www.podpage.com/blog/podcast-video-production

**R2 (5). Default = the active speaker (medium/close); wide (2-shot) = shared exchanges, opening, and "safety/cover" shot.**
- OBSBOT workflow https://www.obsbot.com/blog/podcast/multi-camera-podcast-production-workflow
- B&H https://www.bhphotovideo.com/explora/node/124651
- StudioBinder (open on master/wide; close-ups for emotional peaks) https://www.studiobinder.com/blog/how-to-edit-a-dialogue-scene/
- Leake et al. SIGGRAPH 2017 idioms "start wide", "speaker visible", "intensify emotion" (close-ups only for strong emotion) https://graphics.stanford.edu/papers/roughcut
- mediacollege (wide helps when you'd rather not rush a cut) https://mediacollege.com/video/interviews/editing.html
- Descript Automatic Multicam ("Automatic" style shows multiple speakers during dialogue) https://help.descript.com/visuals/automatic-multicam

**R3 (5). Do NOT cut on every short acknowledgement / interjection ("mhm", "yeah"); hold the angle.** Auto-switchers need review exactly here.
- OBSBOT https://www.obsbot.com/blog/podcast/multi-camera-podcast-production-workflow
- Finchley ("robotic cut": switching at the instant the other voice rises = rigid) https://www.finchley.co.uk/finchley-learning/video-engineering-in-a-professional-podcast-post-production-cutting-working-practices  (page text partly garbled in my fetch -> treat as snippet-level)
- FireCut (holds shot through short pause) https://firecut.ai/blog/the-ultimate-2-person-podcast-camera-setup-and-how-to-edit-it-in-minutes/
- invideo (overlap/interjections may yield camera choices you'd override) https://invideo.io/blog/edit-multi-camera-footage-with-ai-for-podcasts/
- PodcastVideos ("avoid rapid cuts unless it enhances energy") https://www.podcastvideos.com/articles/edit-multi-camera-podcast-footage-2025
- AutoCut angles: min shot duration setting exists (no default published); same camera never twice in a row https://www.autocut.com/en/autocutangles/

**R4 (4). Cut audio and picture at different times (J-cut / L-cut); don't cut exactly at the question/answer boundary.** Let the answer start while still on the asker/reaction (L-cut) or show the answerer a few frames before they speak (J-cut).
- mediacollege ("cut slightly before or after; exact cuts look stilted") https://mediacollege.com/video/interviews/editing.html
- StudioBinder https://www.studiobinder.com/blog/how-to-edit-a-dialogue-scene/
- Finchley split edits https://www.finchley.co.uk/finchley-learning/video-engineering-in-a-professional-podcast-post-production-cutting-the-final-cut-additional-editing-topics-you-are-bound-to-encounter
- B&H / Finchley "when to cut" snippet (reaction shots, J/L) via search results
[INF] cut-offset magnitude (e.g. 0.2-0.5 s) is NOT given by any source; tune by eye.

**R5 (4). Reaction shots (listener) are a standard tool: add energy, cover jump cuts / removed material.**
- mediacollege (noddies "will save your edit"; must match the content emotionally) https://mediacollege.com/video/interviews/editing.html
- B&H https://www.bhphotovideo.com/explora/node/124651
- Finchley https://www.finchley.co.uk/finchley-learning/video-engineering-in-a-professional-podcast-post-production-cutting-when-to-cut-and-why (404 on direct fetch; snippet only)
- Descript crosstalk-in-video (cover overlap with reaction/other visuals) https://www.descript.com/blog/article/how-to-edit-crosstalk-in-video
- Adobe (cut away during audio edit to avoid visible jump cut) https://www.adobe.com/creativecloud/video/discover/temp/podcast-videos.html

**R6 (5). One-camera "virtual multicam": use a high-res (4K) wide, duplicate it onto N tracks with different crop/scale (wide + one per person), nest -> multicam, switch with number keys; apply zoom to the clips INSIDE the multicam, not the multicam wrapper.**
- Tuts+ (1080p sequence, 4K clip, wide ~50% scale, close ~85-90%+; keys 1/2) https://photography.tutsplus.com/articles/how-to-create-multiple-camera-shots-from-a-single-camera-using-premiere-pro--cms-41932
- AutoCut single-cam (V2/V3 = zoom on each speaker) https://autocut.com/help-center/autocut-podcast/single-camera
- Adobe community "zoom one clip in multicam" https://community.adobe.com/t5/premiere-pro-discussions/how-to-zoom-one-clip-in-multi-camera-sequence/m-p/9888383
- Adobe community Zoom-call podcast (adjustment-layer "camera moves") https://community.adobe.com/t5/premiere-pro/editing-a-zoom-call-for-a-video-podcast/m-p/11766130
- Descript feature thread (multicam from 1 video not natively; Center active speaker is the 1-camera path) https://feedback.descript.com/feature-requests/p/multicam-from-single-video
- invideo/AutoCut guides (4K crop "sensor cropping" = extra angles) https://invideo.io/blog/ai-video-editor-vs-premiere-pro-plugins-multicam-podcasts/

**R7 (4). Punch-in factor from 4K: lossless up to ~200% in a 1080p timeline (pixel math); practical softness beyond; quick test export.** Forum voices differ on "safe" (110-120% conservative if timeline is 4K and export soft) -> see D2.
- Adobe forum (200% = 1:1 pixels) https://community.adobe.com/t5/premiere-pro-discussions/question-about-4k-sequences-scaling-and-output-and-computer-performance/m-p/13118366/highlight/true
- Creative COW ("110% safe, 120% if clean, eyes go soft") https://creativecow.net/?p=409049
- Adobe forum (punched-in 2160p timeline exports blurry to 1080p; fix: 1080p sequence, scale 50-100%) https://community.adobe.com/t5/premiere-pro-discussions/punched-in-footage-on-2160p-timeline-exports-blurry-to-1080p/m-p/14072784/highlight/true
- Tuts+ (see R6)
[INF] 3840 px wide / 1920 = exactly 2.0x. A single-camera wide of 2 people side by side framed ~full width: a "single" crop of one person at ~1/2 width (~2x) ~ 1920x1080 native pixels, but 16:9 crop of half the width includes a lot of the neighbour; tighter crops (>2x) need upscaling if export is 1080p. If you export 4K, 2x crop = 1080p-native (soft on 4K output).

**R8 (4). Do not remove ALL crosstalk/laughter; remove noise (coughs, bumps), repetitive flat backchannels, and overlaps too loud/muddy to follow. Keep enthusiastic overlap and laughter (lower the less-important track instead of deleting).**
- Descript crosstalk (audio) https://www.descript.com/blog/article/how-to-edit-out-crosstalk-in-your-podcast-and-when-to-leave-it-alone
- Descript crosstalk (video) https://www.descript.com/blog/article/how-to-edit-crosstalk-in-video
- The Podcast Host (laugh: let it stand briefly then lower; enthusiastic "right right" = keep; flat = silence; 60-min 2-track interview ~20 min of crosstalk work) https://www.thepodcasthost.com/editing-production/crosstalk-edits/
- Riverside crosstalk https://riverside.com/university-videos/fix-crosstalk-in-your-podcast-edit
- Podcast Host "how much editing" https://www.thepodcasthost.com/editing-production/much-editing-should-i-do-in-my-podcast/
**Prereq (3 sources agree):** separate track per speaker is required to repair overlap; with one shared track you can only keep or cut whole segment. Same in Descript audio article, OBSBOT, Zencastr https://zencastr.com/blog/podcast-editing-your-guide-to-getting-the-job-done.
**Video during crosstalk (Descript video article):** (a) cut audio keep video, (b) cover with visuals/reaction, (c) switch layout to the speaker full screen then back.

**R9 (4). Silence/filler removal: conservative, judgment-based, review by ear. Automated filler removal often harsh. Shorten pauses rather than delete.**
- Mubert docs (informal: flag >=0.5 s, shorten to ~0.3 s "beat"; full removal sounds jammed) https://mubert.com/tools/cast/features/remove-silence
- Descript filler-word art / feedback (harsh cuts) https://www.descript.com/blog/article/the-art-of-filler-word-removal ; https://feedback.descript.com/feature-requests/p/filler-words-dont-ignoreremove-unless-they-can-be-cleanly-removed
- Podcast Host https://www.thepodcasthost.com/editing-production/much-editing-should-i-do-in-my-podcast/
- Pro Tools Expert https://www.pro-tools-expert.com/production-expert-1/2020/7/29/editing-audio-interviews-what-choices-do-we-make-and-why
- SoundGirls (avoid over-editing) https://soundgirls.org/?p=47521
UNVERIFIED numbers: 0.3/0.5 s are one vendor's defaults; a writer's "<150-200 ms strips micro-pauses" is a single non-authoritative claim. Source-based conclusion: conversation = more conservative than solo [INF; sources say "judgment", none states a conversation-vs-solo delta]. Practical: cut dead air at topic changes (Spotify) and long (>~1 s [INF]) pauses; keep reaction pauses/"thinking" pauses of guest (a producer quote in Descript article).
Cuts in the middle of a speaker's turn on a single wide shot show up as jump cuts -> hide with a punch-in change (see R12) [INF, consistent with R5/Adobe "cutaway during audio edit"].

**R10 (4). Separate mic per person, each on its own track; normalize levels across speakers; -16 LUFS integrated, true peak ~-1 dBTP for YouTube-oriented mixes.**
- Descript mixing/levels https://www.descript.com/blog/article/how-to-mix-podcast-audio-thats-studio-quality ; https://www.descript.com/blog/article/basics-to-get-the-right-podcast-audio-level
- OBSBOT (each mic on own track; camera audio = sync ref only; 48 kHz) https://www.obsbot.com/blog/podcast/multi-camera-podcast-production-workflow
- PodcastVideos (normalize speaker levels) https://www.podcastvideos.com/articles/edit-multi-camera-podcast-footage-2025
- B&H mixing https://www.bhphotovideo.com/explora/node/121956
Differing numbers: Adobe -20..-16, Zencastr default -19 LUFS (see D5). One shared phone mic: voices on one track -> no crosstalk repair, no per-speaker diarization-free switching; two mics, even close, bleed (Adobe forum, sonix, Audacity forum): https://sonix.ai/articles/how-to-mic-a-two-person-interview ; https://community.adobe.com/questions-729/best-way-to-deal-with-mic-bleed-two-lav-mics-interview-1387464 . Fix bleed: de-bleed / sidechain plugins (forum, anecdotal). Dynamic mics reject room/other voice better than condensers (Podcast Host/forums).

**R11 (3). Music: intro/outro only; duck under speech; not long musical interludes on video.**
- Descript don'ts (drop slow musical interludes that clash with video pacing; no long intros) https://www.descript.com/blog/article/adding-video-to-your-podcast-avoid-these-common-mistakes
- Adobe Premiere auto-duck (Essential Sound) via forum https://community.adobe.com/t5/premiere-pro-discussions/help-with-audio-settings-for-voice-over-and-music/m-p/12040586/highlight/true
- Mubert (15-20 dB below speech under voice; single vendor, UNVERIFIED as norm) https://mubert.com/tools/cast/features/auto-duck-podcast
- invideo (no universal dB; listen) https://invideo.io/blog/automatically-lower-background-music-under-dialogue-with-ai/

**R12 (4). Visual overlays (photos, clips, posts, screen) when the talk references them: they add interest and hide edits; but don't overdo (not wall-to-wall).**
- Descript don'ts https://www.descript.com/blog/article/adding-video-to-your-podcast-avoid-these-common-mistakes
- Spotify (picture-in-picture; title cards at segment changes) https://creators.spotify.com/resources/video-podcast-editing
- CapCut B-roll pacing (don't change captions+overlays+B-roll all at once; ask what it helps viewer understand) https://www.capcut.com/create/b-roll-pacing-educational-videos
- Descript B-roll https://descript.com/blog/article/using-b-roll-a-beginners-guide
- LinkedIn teardown (overlay when hosts cite numbers/refs) https://bd.linkedin.com/in/nabilhassan47
No source gives a frequency; "Learn screen" full-screen at key learning moments (Sweetfish) https://sweetfishmedia.com/blog/the-6-screens-every-video-podcast-needs. [INF] For side-by-side 2-person shot: place overlays in the empty gap between the two heads or full-screen cutaway only during that speaker's turn; never over a face.

**R13 (4). Hook/cold open: short teaser from the best moment before the standard intro; keep intro short on video platforms.**
- Sweetfish (cold open 5-10 s max) https://sweetfishmedia.com/blog/the-6-screens-every-video-podcast-needs
- vidIQ (intro <=10 s; first 30 s decisive) https://vidiq.com/blog/post/youtube-video-intros/
- Zencastr (15-30 s teaser) https://zencastr.com/blog/how-to-create-a-podcast-intro ; Trappe (20-40 s cold open) https://christophtrappe.com/podcast-cold-open
- Descript don'ts (no long intros) ; Callum McDonnell Substack on DOAC trailers (guest-in-chair first, A/B on Facebook, single agency account) https://callummcdonnell.substack.com/p/meet-the-viral-editor-behind-steven
Length disagreement -> D4.

**R14 (3). Chapters: YouTube official rules (VERIFIED on source): first timestamp 00:00, >=3 timestamps ascending, >=10 s per chapter, listed in description (overrides auto-chapters).**
- https://support.google.com/youtube/answer/9884579?hl=en (fetched, exact)
- Dickinson https://blogs.dickinson.edu/mediacenter/2026/01/12/youtube-adding-video-chapters/ ; vidIQ https://vidiq.com/youtube-chapter-generator/
Mark strong soundbites/beats with timeline markers during edit (PodcastVideos) -> reuse for chapters + shorts.

**R15 (4). Sync first, then cut; check sync at start/middle/end (drift); single frame rate; clap/transient.**
- OBSBOT; Spotify (sync check throughout, drift) https://creators.spotify.com/resources/video-podcast-editing ; Descript Zoom/remote tips; mediacollege (countdown).

**R16 (3). Lower thirds: name+role, simple, template reused every episode; shown when speaker first appears; ~3-5 s (one source).**
- fiveable (3-5 s, consistent) https://fiveable.me/tv-studio-production/unit-7/thirds-titles/study-guide/kQd4R1XeWNW530P9
- Masterclass (name card; intro/outro animation, avoid mid-motion distraction) https://masterclass.com/articles/how-to-use-lower-third-graphics-in-film-and-tv
- Frame.io (move it if it conflicts with face/tight close-up) https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/
- Sweetfish; Riverside lower thirds https://riverside.com/blog/lower-thirds
"Within first minute" = [INF] (no source).

## 2. Captions for 2 people (mixed / thinner evidence)
**C1 (3).** Position: bottom area (bottom ~25% of frame, central ~80% width, >=60 px from edges) is the compatible default; keep other on-screen text in the top two-thirds so it never collides; lower-third name then goes above caption zone or corner. OPUS https://www.opus.pro/blog/video-caption-design-placement ; 3Play https://www.3playmedia.com/blog/closed-caption-styling-formatting-best-practices-you-need-to-know/ ; Colorado.edu https://www.colorado.edu/digital-accessibility/node/617 ; CapCut (keep away from edges where platform UI sits).
**C2 (3).** Format: <=42 chars/line, max 2 lines; caption display 1-6 s; contrast >=4.5:1 (7:1 optimal); 18-24 pt min mobile (OPUS; units pt/px mixed in source -> UNVERIFIED conversion). 3Play; Leeds https://digitalaccessibility.leeds.ac.uk/guidance/digital-audio-and-video/captions/ ; Veed https://www.veed.io/video-accessibility/best-practices-for-captioning
**C3 (3).** Speaker identification: colour alone is insufficient (viewers not used to it) -> pair colour with a name label or different lines; accessible palette example: white #FFFFFF, yellow #FFFF00, cyan #00FFFF, green #00FF00 (BBC-style). Adobe community colour-coding thread https://community.adobe.com/t5/premiere-pro-discussions/how-to-color-code-subtitles-captions-multiple-speakers/m-p/13367231 ; Kapwing https://www.kapwing.com/resources/how-to-add-colored-captions-to-any-video/ ; Colorado.
**C4 (1-2).** Speaker-following caption placement is "moving out of favor" for streaming compatibility (3Play-derived snippet) but is possible when burned-in; AI tools avoid faces automatically (OPUS). For a side-by-side single wide shot [INF]: captions bottom-center are over torsos/table, not faces -> fine; colour per speaker + persistent small name tag in the active speaker's half is a design option; unproven.
**C5 (1).** Fridman/Huberman-style clip captions = minimal white w/ shadow, no emoji (clip vendor opinion, not the shows) https://autoclip.dev/blog/how-to-clip-lex-fridman-podcast-for-shorts -> UNVERIFIED as show style. Bold/animated captions for shorts (Descript: burned-in subs are standard on short clips).

## 3. DISPUTED / no numeric consensus
**D1. Shot length / cut frequency.** No source gives a number. Spotify: "no golden rule". PremiumBeat: ~4 s shots in a long interview = distracting (single example). Descript Automatic Multicam: cutaway "Occasional" = 1 per 30 s in monologue; "Frequent" = 1 per 10 s (these are tool presets, not editorial evidence). opensource-clipping `--switch-hold-duration` default 2.0 s (hold before switching; tool default). => For implementation: parameterize (min hold ~2 s as tool default [INF-tuning], max hold untested; start e.g. 8-12 s then check by eye). All numbers = tunables, not rules.
**D2. Punch-in "safe" factor.** 200% (pixel math, 4K->1080p) vs 110-120% (Creative COW, for features going soft) vs "blurry on export" reports in 4K timelines. Resolve by exporting a test frame; if output is 1080p use a 1080p sequence.
**D3. Wide vs single balance in single-cam.** Split-screen/2-shot as baseline (Rizzle) vs switch to full-screen solo during long monologues (teardown) vs "close-ups only for emotional peaks" (StudioBinder/Leake). No ratio given.
**D4. Intro length:** 5-10 s (Sweetfish), <=10 s (vidIQ), 15-30 s (Zencastr), 20-40 s cold open (Trappe), 30-60 s (Goldcast) https://www.goldcast.io/blog-post/podcast-intro-examples . "7 of top 20 podcasts have intros >30 s" appears in one snippet (UNVERIFIED).
**D5. Loudness:** -16 LUFS (common) vs -19 (Zencastr default) vs -20..-16 (Adobe). Check YouTube normalization yourself (not confirmed from YouTube docs here).
**D6. Auto vs manual switching.** Vendors (AutoCut, FireCut, Descript, DaVinci SmartSwitch, Riverside) claim near-automatic; forum users (Adobe) say "usually a good deal of manual switching", AutoPod needs manual cleanup. Treat auto output as a first draft.
**D7. Remove ums.** Auto-removal vs manual: Descript user complaints "harsh/abrupt"; producer prefers manual. Consensus = review; none quantify.

## 4. Tools / open-source tech (data; accuracy numbers are from READMEs/papers, not my runs)
| Tool | Task | Numbers / notes | Source |
|---|---|---|---|
| pyannote speaker-diarization-3.1 | who spoke when (audio) | DER (no collar, overlap counted): VoxConverse 11.3, AMI headset 18.8, DIHARD3 21.7, AISHELL-4 12.2, REPERE 7.8, MSDWild 25.3, AVA-AVD 50.0. Mono 16 kHz. HF token + accept terms. No RTF given on card. CPU: indirect: 8-vCPU AWS 45 min video took 36.5 min (GH issue); 3.1.1 reported much slower than 3.1.0 on CPU embedding (GH issues). Expect ~20-50+ min CPU per audio hour [INF from those] | https://huggingface.co/pyannote/speaker-diarization-3.1 ; https://www.github.com/pyannote/pyannote-audio/issues/1621 ; /1626 ; /1687 |
| pyannote community-1 / Precision-3 | newer | benchmark page lists them (charts only, numbers not extractable) | https://www.pyannote.ai/benchmark |
| WhisperX | ASR + word align + diarization (pyannote) | "70x realtime large-v2" (GPU, batched); CPU: `--compute_type int8 --device cpu`; set `--min_speakers 2 --max_speakers 2`; README: "overlapping speech is not handled particularly well", "diarization far from perfect"; BSD-2; needs HF token. Third-party non-peer-reviewed benchmark: WhisperX diarization DER 26.31% on 26 mixed call files (UNVERIFIED quality) | https://github.com/m-bain/whisperX ; https://scribie.com/blog/speech-to-text-accuracy-benchmark-assemblyai-deepgram-whisperx |
| TalkNet-ASD | audio-visual ASD | AVA val mAP 92.3 (test 90.8); Columbia avg F1 96.3 (TalkSet-trained); AVA-trained transfers poorly outside AVA; CUDA by default, CPU needs code edits; Python 3.7.9; MIT; 15.7M params | https://github.com/TaoRuijie/TalkNet-ASD |
| Light-ASD | lightweight ASD | AVA val mAP 94.06; 1.0M params; Columbia F1 avg 81.1 (AVA weights) / 95.5 (TalkSet fine-tuned); MIT; README gives no CPU/speed. Paper claims 0.1-4.5 ms single-frame; robotics paper: Light-ASD still too slow for real time inside a full pipeline, 1 s clip @30 fps ~1.3 s unoptimized | https://github.com/Junhua-Liao/Light-ASD ; https://openaccess.thecvf.com/content/CVPR2023/papers/Liao_A_Light_Weight_Model_for_Active_Speaker_Detection_CVPR_2023_paper.pdf ; https://arxiv.org/pdf/2407.11915 |
| LoCoNet | ASD | AVA 95.2 mAP, 34.3M params (heavy) | https://arxiv.org/html/2301.08237v2 |
| LR-ASD | lighter successor | 0.84M params, 94.5 mAP (snippet) | search snippet via https://duanhaihan.github.io/publications/2025/IJCV2025.pdf |
| opensource-clipping | full open pipeline (BlazeFace/YOLO + pyannote 3.1 + Whisper) | camera-switch hold default 2.0 s, blend 0.0 s (0.2 smooth); track-step 0.25 s, deadzone 0.15, smooth 0.30, jitter 5 px, snap 0.25; only 9:16 output; CPU fallback int8; UNVERIFIED on real footage | https://github.com/NaufalRizqullah/opensource-clipping |
| WhoSpoke | diarization+transcript+mouth-open cue fusion | page failed to load in fetch -> unverified | https://pypi.org/project/whospoke/ |
| Google AutoFlip | generic reframe (MediaPipe) | not podcast-specific | https://research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/ |
| Descript Center active speaker (beta) | 1 wide cam -> crop to active speaker | crops are FIXED per scene, don't track movement; consumes AI credits; footage w/ existing cuts -> late/incorrect framing; no max speakers/size documented | https://help.descript.com/hc/en-us/articles/36838169552269 |
| Descript Automatic Multicam | multi-track | needs one audio track per camera; cutaway freq none/30 s/10 s; overwrites scenes | https://help.descript.com/visuals/automatic-multicam |
| DaVinci Resolve 20 SmartSwitch | multicam auto speaker switching | secondary sources only; internals/min-shot unknown | https://cined.com/davinci-resolve-20-released-with-handful-of-ai-assisted-features |
| OpusClip | split layout (2 speakers) needs both in the same original frame; active speaker detect; first speaker pinned top via brand template | https://www.opus.pro/blog/best-ai-podcast-and-webinar-clip-makers |
| OpenClip | face+diarization tracking; no hold time documented; fails on hidden faces, backlight, small faces | https://openclip.app/guides/speaker-tracking-guide |
| AutoCut Podcast / AutoPod / FireCut | Premiere plug-ins | need one mic track per speaker | https://autocut.com/help-center/autocut-podcast/single-camera |

**Feasible pipeline for 1 wide cam, 2 people side by side, CPU-only [INF, built from the above]:**
1. Diarize audio (pyannote 3.1 or WhisperX w/ min=max=2 speakers). If 1 mic -> overlap segments are the weak spot (WhisperX README).
2. Map speaker -> left/right ONCE (2-person static seating): run an ASD (Light-ASD/TalkNet) or mouth-motion cue on a few sampled segments, vote; or just ask the user. No need to run ASD on the whole video = big CPU saving.
3. Build segment list (speaker, t0, t1) -> apply hold rules (min hold, ignore backchannel < ~1 s, L-cut offset) -> crop keyframes from the 4K wide (fixed crop per speaker, optional slow drift). Descript's own tool uses fixed crops per scene, supporting this design.
4. Render with ffmpeg crop/scale; overlays/captions in the empty zones.
Not verified: end-to-end accuracy on side-by-side phone footage, and CPU timings for ASD (no CPU fps found for Light-ASD/TalkNet anywhere; S3FD face-detect cost not found).

## 5. Per-topic quick answers to the brief
- Wide vs single vs split: wide to open + shared exchanges + safety; single (punch-in) for the speaker; split-screen is the baseline layout for 2-person in vertical/short-form tools, and is criticised as monotone over long runs (R1, D3).
- Whom to cut to: active speaker; reactions for energy; don't chase every interjection (R2,R3,R5). "Cut on the question vs answer": sources say don't cut exactly on the boundary (R4); none specifies "show asker during question" for podcasts. NPR/PBS note edits must preserve meaning: https://www.npr.org/sections/npr-training/2025/05/29/g-s1-65686/how-to-decide-what-to-cut-or-not-in-an-interview .
- Min/max shot length: NO sourced numbers (D1).
- Punch-in factor: see R6/R7/D2.
- Crosstalk: R8. Laughter: keep, lower the other track.
- Captions/lower thirds/graphics: R12, R16, section 2.
- Pacing: R9. Audio: R10-R11. Hook/chapters: R13-R14.
- Tools: section 4.

## 6. Unchecked / blocked
reddit.com blocked; mixinglight (paywalled), B&H partly 403, nono.ma (connection refused), Canon (403), cutback.video (redirect not followed), gotranscript 404 pages. Named-show editing grammar not found. Finchley pages returned garbled/404 content in fetch -> cited only as snippet-level.
