# Visual upgrade plan (look, drawing, motion) — 2026-11-05

Why: Kamil 5.11 after out_v2 of film 2: "widzę pełno starych rzeczy", side boards unreadable on a phone, stamps in empty
space, words instead of motion ("ODMOWA"), messy scenes, old memes. The research changed timing and layout rules
(film_check), not the look. This file pulls the visual findings out of the REF files into one order of work.
Rule: take mechanics only, never another creator's graphics or branding.

## What the research found (sources)

| idea | source | what we have | gap |
|---|---|---|---|
| hand-drawn scene: flat background, thin lines drawn in time, handwritten labels, speaker in a circle | REF-long-negacz.md L3 (101 blocks, 8 of 10 films, median 19 s) | `scene_lib.mjs` UI pieces (chip, stamp, node), straight lines | new scene type `sketch` (P2 #5, cost L) |
| lines drawn on screen (stroke reveal) | GSAP DrawSVGPlugin, already in `node_modules/gsap` (Standard licence, no charge: REF-oss-survey.md:40) | CSS line grow only | use DrawSVG for every line, arrow, circle |
| hand annotations (circle, underline, box, highlight with wobble, fixed seed) | rough-notation `render.ts:68-264` (MIT), REF-oss-survey.md:156, :395 | `ring`, `hl` straight and placed by coordinates (missed its target in s13) | annotation attached to a piece id, rough stroke |
| handwritten text written stroke by stroke | tegaki `textToSvg()` (MIT), REF-oss-survey.md:154, :392 | none | needs a font with Polish letters (ą ę ł ń ś ź ż), 8-12 h |
| motion palette per role (word scale-in ~370 ms, scene punch-in, quote rise+blur, rolling number, spring) | Remocn mechanics (MIT), REF-oss-survey.md top 10 #10 | one curve `.2,1.6,.4,1` for everything | 3-5 h |
| meme/GIF stickers cut out of the background | rembg + pymatting + sticker-forge mechanics, REF-oss-survey.md top 10 #9 | `sticker` card exists, no cutting, no GIF | ~10 h; weights licence to check |
| morph one shape into another (toggle springs back, icon turns into a verdict) | GSAP MorphSVGPlugin (in node_modules) | none | use for "action instead of a word" (Kamil: ODMOWA -> toggle flashes red and springs back) |
| card audit: text >= 28 px, contrast >= 4.5, two texts overlapping > 3 %, same word twice | eian-riso-broll `riso.js:357-389` (idea only, NC licence) | scene_check: overlap only | phone-readability gate |
| soft 0.5 s entry into scenes, hard cut back to the speaker | REF-long-negacz.md L7 | hard cuts everywhere | P2 #6, S-M |

<!-- ledger-forms: long, shorts -->
## Order of work (each = one commit + tests + a preview Kamil watches)

1. **Phone-readability gate** in scene_check: text height after the camera scale >= 40 px on the 1440 frame, stamp
   must overlap its target piece, annotation/line must touch its target box. Catches Kamil notes 15, 16, 18. S.
2. **Pieces attach to ids**: `line {from: "e1", to: "e2"}`, `ring {on: "md.row0"}`, `stamp {on: "term"}` measured in
   the DOM, no hand coordinates. S-M.
3. **DrawSVG lines + rough annotations** (circle, underline, box) with a fixed seed. S-M.
4. **Motion palette** (Remocn mechanics) + MorphSVG actions: toggle springs back and flashes red, check turns into X. M.
5. **`sketch` scene type**: flat background, drawn lines, handwritten labels (tegaki + Polish font), speaker circle,
   one big idea per scene. L. Prototype on 2 scenes of film 2 first; Kamil decides before it becomes the default.
6. **Meme stickers and GIFs**: cut-out pipeline + a meme review per film (the sentence it illustrates, why it fits,
   year of the meme; old ones out). Kamil note 19, cat typing gif.

Open decisions for Kamil: own handwriting font and chalk line (REF-long-negacz.md:258)? Background colour of sketch
scenes (our brand, not Negacz `#363465`)?
