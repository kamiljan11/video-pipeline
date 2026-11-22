# VISUAL-LONG: how real video podcasts are edited (16:9, WATCHED, not read)

Date: 2026-11-22. Host: laptop. Complements `RESEARCH-LONGFORM.md` (text sources only); this file is from looking at frames.

## 0. Method and honest limits (read first)

- 9 channels, 10 episodes. Per episode, 360p video only, two 3-min windows: **A = 00:00-03:00** (cold open / intro) and **B = a 3-min window around the episode middle**. Files: `~/Dane/creator-study/podcast-visual/long/<channel>/` (<= 14 MB per episode). No audio, nothing uploaded.
- Measured with ffmpeg/OpenCV (scripts in `.../podcast-visual/tools/`, raw numbers `cuts.json`, `pushin.json`, `framing2.json`):
  - **cuts** = `tools/cuts.py`: frame-difference spikes at 8 fps on 96x54 grey (ffmpeg `scene>0.3` undercounts cuts between similar dark/same-palette shots, e.g. DOAC window B gives 11 vs 18 with the custom detector; I use the custom one; `scene>0.3` counts are in `*.scenes.txt`).
  - **push-in** = `tools/pushin.py`: ORB features, first vs last frame of every cut-free window >= 6 s (<= 12 s), centre 70% crop, similarity transform scale. Locked-off shot = 1.000. Caveat: split-screen/framed layouts (20VC, MFM) bias toward 1.000; a missed cut or a person leaning gives false positives (I eyeballed the outliers in `pushin/_checks.jpg`).
  - **framing** = `tools/framing.py` with the repo's YuNet model: share of sampled frames (every 2 s) with 2+ faces, and face-width/frame-width. Rough; eyeballed sheets override it.
  - **graphics** = counted by LOOKING at 5-s contact sheets (`*.sheet.jpg`, 6x6 = 36 frames per 3 min; spec said 6x4, I used 6x6 so one sheet = one window). Resolution is 5 s: anything shorter than ~5 s can be missed; durations are +-5 s.
- **Sample is thin**: 6 min per episode, 1 episode per channel. Anything that happens only at chapter boundaries or in the last minutes is NOT covered. "Not seen" = not seen in these windows, not "never".
- **Two of the requested channels did not give two people on camera**:
  - `@Dylematy` (Dworak): all 243 videos listed are solo vlogs/travel/diet (checked titles; no guest episode found). Sampled one (DV #58). It is a solo-presenter reference only.
  - `Dwie Lewe Ręce`: both episodes sampled (Giełzak, Dymek) show ONE person on camera for the whole 12 min (guest not shown). `Kryzys Wieku Średniego` ep. 35: solo host. Titles of other KWS episodes (25 listed) did not suggest guests either.
  - So **two-person visuals = 6 channels** (Imponderabilia, DOAC, 20VC, Lenny's, MFM [3 people], Modern Wisdom). I added Modern Wisdom as the 9th channel to compensate. Counts below are "n/9 (n/6 two-person)".
- **No show in the sample uses ONE wide camera for 2 people.** Imponderabilia and Modern Wisdom are in-room multicam; DOAC is multicam; 20VC/Lenny's/MFM are remote (Zoom-like) recordings. Our single-wide-4K-with-virtual-crops case has no direct visual precedent here; the nearest is the in-room multicam grammar (VL3-VL6).
- Not checked: whether YouTube chapters exist, audio, speaker-switch logic (cut-to-speaker latency), 4K quality, any episode of Dworak with a guest.

## 1. Per-channel table

Cuts/min and shot lengths = custom detector. "2+ faces" = % of sampled frames (YuNet). Sheets = `~/Dane/creator-study/podcast-visual/long/<dir>/<file>.sheet.jpg`.

| Channel (episode, id) | On camera | cuts/min A / B | median shot s A / B (mean B) | 2+faces % A / B | Push-in (B, scale per window) | Graphics seen (A, then B) | Sheets A / B |
|---|---|---|---|---|---|---|---|
| Imponderabilia (Marta ... guest, `qHLJr7ojYA8`, 100 min) | 2, in-room multicam (wide 2-shot, med/close singles of both) | 15.0 / 5.7 | 2.4 / 9.7 (10.0) | 9 / 24 | max 1.021 (14 windows), median 0.000 | A: burned word captions ~70 s, corner tag "W DZISIEJSZYM ODCINKU" ~70 s, sponsor fragment ~75 s (full-frame phone/mascot b-roll, tag "fragment sponsorowany" top-left, brand lower-third + QR + code bottom ~10 s). B: none | `imponderabilia/qHLJr7ojYA8_0.sheet.jpg` / `..._2918.sheet.jpg` |
| The Diary of a CEO (Mark Cuban, `6VTSAs4Rsck`, 92 min) | 2, multicam, medium + close singles, host reaction cutaways | 20.3 / 6.0 | 1.8 / 6.6 (9.5) | 3 / 0 | **max 1.144, min 0.915; 6 of 8 windows deviate > 3%** | A: keyword kinetic text on ~9 of 36 frames, b-roll/illustration/collage ~7 of 36, small bottom subtitles, phone inset (3 frames). B: none | `doac/6VTSAs4Rsck_0.sheet.jpg` / `..._2657.sheet.jpg` |
| 20VC (Mistral CEO, `KotQbLX8pOw`, 50 min) | 2, remote; layout switches 2-up split / full-frame guest | 9.3 / 3.7 | 2.4 / 17.4 (15.0) | 47 / 43 | max 1.001 (framed layout, not informative) | A: kinetic teaser text + glitch ~50 s, logo/subscribe card ~5 s, then permanent branded frame (sponsor top-left, 20VC logo top-right, sponsor bottom), name+title lower-third bottom-left ~15 s. B: only the permanent frame | `20vc/KotQbLX8pOw_0.sheet.jpg` / `..._1418.sheet.jpg` |
| Lenny's Podcast (Tulsee Doshi, `qGf2Yvan4Wg`, 58 min) | 2, remote; mostly full-frame active speaker, some 2-up | 10.3 / 3.7 | 2.9 / 8.2 (15.0) | 14 / 3 | max 1.118 (checked: guest leaning, not a digital zoom), median 0.000 | A: burned word-by-word captions ~65 s, 3 full-frame clips/slides, tiny logo + sponsor tag corners from ~70 s. B: sponsor spot = 5 full-screen slides ~25 s | `lennys/qGf2Yvan4Wg_0.sheet.jpg` / `..._1666.sheet.jpg` |
| My First Million (Ex-Amazon VP, `0_hpTKQqKOQ`, 73 min) | 3, remote; 3-up grid + full-frame singles | 10.3 / 7.3 | 5.2 / 6.6 (7.8) | 37 / 41 | max 1.086 (one window), median 0.01 | A: show logo top-right on singles, name tag bottom-left on EVERY single, black&white name card ~5 s, 1 headline screenshot card ~5 s. B: name tag + logo only | `mfm/0_hpTKQqKOQ_0.sheet.jpg` / `..._2110.sheet.jpg` |
| Modern Wisdom (Alex O'Connor, `OLwQ5A3sRyI`, 116 min) | 2, in-room multicam, cinematic, wide establishing + med/close singles | 6.0 / 6.3 | 3.4 / 6.0 (9.0) | 2 / 7 | max 1.026, median 0.02 | A: title "A Modern Wisdom Cinema production" ~10 s, logo bug bottom-left. B: bug + sponsor strap (URL, bottom ~12% of frame, full width) ~45 s | `modern-wisdom/OLwQ5A3sRyI_0.sheet.jpg` / `..._3400.sheet.jpg` |
| Dwie Lewe Ręce (Giełzak, `a-a3lHmOEUY`, 57 min; Dymek `tHrJeoYbNG4`, 44 min) | **1 on camera**, locked single | 0.7 / 0.0 (both eps) | no cuts after ~5 s intro card | 0 | scale 0.999-1.005 | A: logo card ~5 s, bug bottom-right whole time, URL pill ~5 s at ~10 s. B: bug only | `dwie-lewe-rece/a-a3lHmOEUY_0.sheet.jpg` / `..._1631.sheet.jpg`; `dwie-lewe-rece-b/tHrJeoYbNG4_0.sheet.jpg` / `..._1229.sheet.jpg` |
| Kryzys Wieku Średniego (#35, `9UkpOx0_-xM`, 18 min) | 1 (solo host), locked | 0.0 / 0.3 | 180 / 92.7 | 9 / 0 (sofa pillows false) | 1.000 | A+B: burned phrase captions 100% of time; A: 6 floating cards (news clip, episode card) in ~40 s at left/right edge, none after. B: none | `kryzys-wieku-sredniego/9UkpOx0_-xM_0.sheet.jpg` / `..._449.sheet.jpg` |
| Dylematy (DV #58, `CemCZnW21pw`, 14 min) | 1 (solo vlog), phone-like locked | 1.0 / 0.0 | 9.8 / 183 | 0 / 0 | 1.110 in one 12-s window (slow digital zoom, eyeballed in `_checks.jpg`) | A: candle cold open + sticker b-roll ~15 s. No captions/name/bug. B: none | `dylematy/CemCZnW21pw_0.sheet.jpg` / `..._336.sheet.jpg` |

Push-in montage and outlier checks: `~/Dane/creator-study/podcast-visual/pushin/_checks.jpg` (DOAC 55.3 s and 160.5 s of window B, Dylematy 25.5 s, Lenny's 90.9 s; first/last frame of the window). Longest-shot first/last frame pairs per file: `.../pushin/<channel>_<id>_<start>.jpg`.

## 2. Findings

Denominator: n/9 sampled channels (n/6 two-person). CONSENSUS = n >= 4/9 (adjusted from "4/8" because I sampled 9). Evidence = channel, window, sheet.

### CONSENSUS (>= 4/9)

- **VL1. The body of the episode is graphic-free except persistent corner marks and sponsor reads. n=9/9 (6/6).** In window B (middle) no editorial overlay (keyword text, caption, b-roll card, quote, meme, screenshot) was seen at 5-s resolution in any channel. What is on screen in B: Imponderabilia none; DOAC none; 20VC permanent frame; Lenny's sponsor slides; MFM name tag + logo; MW logo + sponsor strap; DLR bug; KWS captions (solo, VL9); Dylematy none. Editorial graphics per minute in B = 0 for 9/9.
- **VL2. The cold open (first 60-75 s) is edited 2-3x denser than the body. n=5/9 (5/6; MW is the exception: 6.0 vs 6.3; the 3 solo channels have no cuts).** Cuts/min A vs B: DOAC 20.3 vs 6.0; Imponderabilia 15.0 vs 5.7; Lenny's 10.3 vs 3.7; 20VC 9.3 vs 3.7; MFM 10.3 vs 7.3. Median shot in A is 1.8-2.9 s (DOAC, Imponderabilia, 20VC, Lenny's) vs 6.6-17.4 s in B. Sheets: `doac/..._0`, `imponderabilia/..._0`.
- **VL3. Body rhythm: 3.7-7.3 cuts/min, median shot 6-10 s, mean 8-15 s, and cuts follow the speaker (with host reaction shots). n=6/6 two-person (6/9).** B cuts/min: 3.7 (20VC, Lenny's), 5.7 (Imponderabilia), 6.0 (DOAC), 6.3 (MW), 7.3 (MFM). Median shot B: DOAC 6.6, MFM 6.6, MW 6.0, Lenny's 8.2, Imponderabilia 9.7, 20VC 17.4 (split layout keeps both visible, so fewer cuts). Longest shot in B: 46 s (DOAC), 52.8 s (MW), 71.5 s (Lenny's; speaker monologue). Speaker-following and reaction shots of the listener seen in DOAC B (host close-up at ~5 s of sheet frames 5 and 32), Imponderabilia B (host medium between guest singles), MW A/B, MFM, Lenny's. I did not time the cut latency.
- **VL4. Most singles are locked-off: no digital push-in/zoom. n=8/9.** Median scale change per cut-free window is 0.000-0.02 %/s in all channels; max window change: Imponderabilia 1.021, MW 1.026, MFM 1.086 (person moved), Lenny's 1.118 (person leaned, `_checks.jpg` row 4). Exception: **DOAC** (VL13).
- **VL5. Persistent corner logo/bug after the intro, small, never on faces. n=5/9.** DLR bottom-right (~14% of width, whole windows A+B), MFM top-right (~4% width) on singles, 20VC top-right + sponsor top-left in a branded frame, MW bottom-left (~8% width), Lenny's tiny top-left/top-right (low contrast, from ~70 s). Not seen: DOAC, Imponderabilia (apart from sponsor tag), KWS, Dylematy.
- **VL6. B-roll / screenshot / card cutaways exist only in the first minutes, not in the body. n=6/9.** DOAC A: ~7 of 36 sampled frames (~19% of the cold open) are illustrations, collages, hands/props; Lenny's A: 3 clips/slides in the first 60 s (film clip, "Welcome to the Gemini era" slide, app-icons diagram); KWS A: 6 floating cards (news clip, episode card) inside ~40 s; MFM A: 1 headline screenshot ~5 s; Imponderabilia A: sponsor phone/mascot b-roll; Dylematy A: sticker overlay + photos. In B none (except Lenny's sponsor slides, VL8). Full-frame cutaways replace the face (never half-cover it); KWS cards are edge-anchored.
- **VL7. Teaser/cold-open first, then logo card, then body. n=4/9 clearly (DOAC, Imponderabilia, 20VC, Lenny's), plus a short intro card in MFM (name card), DLR (logo card ~5 s), MW (title ~10 s) = 7/9 have some opening card.** 20VC: kinetic teaser ~50 s then a 5-s logo/subscribe card (`20vc/KotQbLX8pOw_0.sheet.jpg` frame 11), then the branded frame; Imponderabilia: guest teaser with captions and a corner tag for ~70 s, then wide 2-shot; DOAC: teaser with kinetic text and b-roll for ~85 s (sheet frames 1-17), then a dark intro and the interview. Logo cards last about 5 s.
- **VL8. Sponsor reads are graphic-heavy and are the only mid-episode overlays. n=4/9.** Imponderabilia A: ~75 s sponsored fragment with tag "fragment sponsorowany" (small, top-left), full-frame product inserts and a bottom brand lower-third with QR + promo code ~10 s (bottom ~25% of frame, faces free). Lenny's B: 5 full-screen slides ~25 s. MW B: bottom strap with URL ~45 s (bottom ~12%, over chest/mic, not the face; in a close-up it sits right under the chin). 20VC: "presented by" + sponsor logos in the permanent frame. Not seen: DOAC, MFM (in these windows).

### SINGLE / weak (< 4/9)

- **VL9. Burned-in captions: only in the cold open for 3/9 (Imponderabilia ~70 s, Lenny's ~65 s, DOAC small subtitles), through the whole video for 1/9 (KWS solo). 0/6 two-person shows have captions in B.** Position: bottom centre, ~5-8% height, white with shadow, over the chest/mic area, not on faces. Word-level bursts in Imponderabilia/Lenny's, phrase-level in KWS.
- **VL10. Keyword/kinetic text: 2/9 (DOAC A: ~9 of 36 frames, i.e. ~3 per minute in the cold open; 20VC A: 1).** Placement: big text on the EMPTY side of the frame opposite the face, or lower-left/right (DOAC A frames 1, 3, 4, 6, 8, 11); never over the face in the frames I saw. 0 in any B window.
- **VL11. Speaker name tag: 2/9.** MFM: small bold white caps bottom-left on every single, always. 20VC: name + title ("... Co-Founder & CEO ...") bottom-left of the guest tile once for ~15 s at ~65 s. Not seen: DOAC, Imponderabilia, MW, Lenny's in these windows (a first-appearance tag may be outside windows).
- **VL12. Wide 2-shot as punctuation: 2/9 (Imponderabilia, MW).** Imponderabilia B: 2+ faces in 24% of sampled frames (wide table shot) + 10% extra wide singles; wide shots last ~5-10 s and return every ~20-40 s. MW: wide establishing ~7% in B, used at the intro (`modern-wisdom/..._0.sheet.jpg` frames 1, 4) and mid-episode transitions (frame 15 of `..._3400.sheet.jpg`). DOAC: no wide 2-shot in either window, only singles of both people.
- **VL13. Slow push-in on close singles: 1/9 (DOAC).** B windows with scale 1.10, 1.09, 1.14 (push-in) and 0.97, 0.96, 0.92 (pull-out), 8-12 s per window = about 1.0-1.4% per second of frame scale, ~10-14% total per shot, in both directions (`_checks.jpg` rows 1-2, DOAC at 55.3 s and 160.5 s of window B). Dylematy (solo): one 12-s window at 1.11 (~0.9%/s).
- **VL14. Two sizes of the same single alternate: 3/9 (Imponderabilia, DOAC, MW = all in-room multicam).** Face width / frame width (YuNet): Imponderabilia 0.04 (wide) - 0.235 (close), DOAC 0.11 - 0.215, MW 0.10 - 0.20, i.e. close crop is ~1.8-2x the medium crop. Remote shows keep one size (Lenny's 0.15-0.20, 20VC 0.18-0.20, MFM 0.17-0.20).
- **VL15. Split/grid layouts only in remote-recorded shows: 3/9 (20VC 43-47% of frames, MFM 37-41%, Lenny's 3-14%).** 0/3 in-room shows use split screen; they use the wide 2-shot instead.
- **VL16. A show can run with ZERO cuts if it has one person and rhythm comes from overlays: 3/9 (DLR 0.0-0.7, KWS 0.0-0.3, Dylematy 0.0-1.0 cuts/min).** KWS compensates with captions the whole time and 6 edge cards in the first ~40 s.
- **VL17. Over-the-shoulder shots: not seen (0/9). Meme/quote cards: not seen (0/9). Subscribe animation: 1/9 (20VC, ~5 s card).** Chapter title cards: **not seen (0/9) in the sampled windows** (only opening cards, VL7; episode-number card in KWS A at ~55 s, a corner tag "W DZISIEJSZYM ODCINKU" in Imponderabilia A). Chapter-card evidence is therefore UNVERIFIED, not negative; my windows are not chosen at chapter boundaries.

## 3. Rules for our pipeline (long, 16:9, one wide 4K camera, crops L / R / wide)

Each rule is tagged with its evidence; "(thin)" = n < 4 or not seen.

### Camera
1. **Body shot length: aim median 6-10 s, 4-7 cuts/min** (VL3, 6/6). Never go below ~3.5 cuts/min on average in a talking section with real speaker changes; long holds up to ~45-70 s on one monologuing speaker are normal (VL3).
2. **Cold open (first 60-75 s, highlight teaser): 10-20 cuts/min, median shot 2-3 s** (VL2, 5/6). Then drop to body rhythm at the title card.
3. **Wide vs single**: singles are the default. Wide 2-shot only as punctuation: ~10-25% of the time, 5-10 s each, mostly at episode start, after long single runs, at laughs/overlaps and at topic changes (VL12, 2/9, thin; Imponderabilia is the quantified case). Do NOT build a split-screen mode (VL15: only remote shows; our table is in one room).
4. **Single = two sizes of the same virtual camera**: medium crop and a close crop of ~1.8-2x face scale, alternate them within a speaker's turn to get a cut without changing who is shown (VL14, 3/3 in-room multicam shows). With a 4K source this is ~2x crop; check that the close crop stays sharp at 1080p output (4K -> 2x crop of 1080 is native, no upscale).
5. **Cut to the listener (reaction single) only on a real reaction or after a long (>20 s) monologue** (VL3; DOAC and Imponderabilia do it; frequency not measured by me).
6. **Push-in: default NONE (VL4, 8/9 locked-off).** If we add motion, copy the only observed case (DOAC, VL13): on close singles only, slow, 1.0-1.4% scale per second, total <= ~14% per shot of 8-12 s, either direction, never combined with a cut-in on the same shot. No ramps/punch zooms on words in long form: none of 9 channels shows them (not seen).

### Graphics: types and max density per minute
| Zone | Allowed | Max density | Evidence |
|---|---|---|---|
| Body (after the title card) | persistent corner logo/bug; speaker name tag; sponsor read only when there is a real sponsor | **editorial graphics (keyword text, b-roll, quote, meme, screenshot): 0 per minute** | VL1 9/9 |
| Cold open (first 60-75 s) | burned captions (word-level bursts), keyword text, b-roll/illustration, one corner tag | keyword text <= ~3/min, b-roll/cutaway <= ~20% of the time | VL6, VL9, VL10 (DOAC numbers, thin) |
| Opening card | logo/title card ~5 s; optional title line ~10 s | 1 | VL7 |
| Sponsor read | tag top-left small, bottom-third brand strap incl. URL/code, full-frame product inserts | strap <= ~45 s, inserts <= ~25 s per read | VL8 |
| Name tag | first appearance of each person, ~15 s, bottom-left (MFM shows it permanently on every single) | 1 per person per episode (our choice; MFM/20VC evidence only, thin) | VL11 |
| Persistent bug | one logo, corner, <= ~10% of frame width | always on after the title card | VL5 (5/9) |

### What never covers a face
- All captions, strips and straps sit in the bottom ~25% of the frame (below chin, over chest/mic/table) (VL8, VL9, VL11, MW, MFM, 20VC, Imponderabilia).
- Keyword text goes on the empty side opposite the face, not over it (DOAC, VL10).
- Corner cards (KWS) sit on the outer 20% of the frame, over the shelf/background; they may collide with captions (KWS A, ~55 s: episode card over caption) so cards and captions need a joint layout check.
- Full-frame cutaways REPLACE the speaker (never half-cover a face), 5-10 s (VL6; 5-s sampling).
- Sponsor strap in close-ups touches the chin area (MW B, `modern-wisdom/..._3400.sheet.jpg` frames 25-34): our close crop must leave >= ~15% of frame height below the chin or the strap must move to the wide/medium crop.

### Chapter card form
- **No chapter card was observed in 9 channels (VL17), so there is no evidence-based form.** Closest observed elements: small corner tag with a short phrase persistent through a section (Imponderabilia "W DZISIEJSZYM ODCINKU", top-left, ~70 s, small); an episode-number card (KWS, left/top-right, ~5-10 s, edge-anchored); a 5-s full-frame logo card (20VC, DLR). Provisional rule until verified: chapter entrance = a short (<= ~5 s) edge-anchored or bottom-third card or a corner tag; no full-frame black card inside the body; verify by pulling windows around chapter timestamps of 2-3 of these episodes (not done).

### Open items (UNVERIFIED)
- Chapter boundaries, name-tag-at-first-appearance, and mid-episode b-roll could not be assessed from the 3+3-min windows.
- A single wide camera with 2 people: no precedent in the sample. A cheap next study would be 1-2 channels filmed on one wide camera (not done).
- Speaker-switch latency and J/L cut offsets: need audio (not downloaded).

## 4. Files

- Downloads, sheets, scene lists: `~/Dane/creator-study/podcast-visual/long/<channel>/` (`dl.log` per episode; `*.sheet.jpg`, `*.scenes.txt` = ffmpeg scene>0.3, `*.scenes08.txt` = scene>0.08, noisy).
- Raw measurements: `.../podcast-visual/cuts.json`, `pushin.json`, `framing2.json` (`framing.json` is the first, cruder face-size pass); scripts `.../podcast-visual/tools/{analyze.sh,cuts.py,pushin.py,framing.py}`, downloader `.../podcast-visual/dl.sh`.
- Push-in evidence: `.../podcast-visual/pushin/`.
