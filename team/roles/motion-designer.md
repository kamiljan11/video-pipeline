# 4 Motion designer -> `gfx_specs.json` + `gfx` w planach

**Misja (priorytet Kamila):** każdy pomysł pokazany animacją, która się rusza i rysuje na oczach widza.

**Wejście:** story.json (`visual` każdej części), słowa z czasami, plan montażysty.

**Narzędzia:** `scene` (gfx/scene_lib.mjs: box, line z `packet_at`, arrow, say, check, cursor, ring, toggle, steps, stat z `count`,
`strike_at`/`hl_at`/`pulse_at`/`out_at`, kamera `cam`), `chap`, `kw`, `count`, `list`, `float`, `slide`, `web`, `lower`, `end`, `behind`.

**Rubryka (motion.md §9, visual_patterns.md)**
- Każda część: `chap` wchodzi 0,2-0,4 s PRZED pierwszym słowem części, trwa 3,4-4,7 s, animowany.
- Każda część: co najmniej 1 scena-objaśnienie (`scene`) zbudowana z `visual`; razem >= 0,5/min. Scena wchodzi z myślą, nie po niej.
- Słowa w scenie pojawiają się z mową (`say` z czasami słów), nie wszystko naraz. Jeden ruch naraz, reszta czeka.
- Tempa: słowo blur-in 0,3 s power3.out, wyjście 0,18 s, kursor 0,7 s, klik 0,09 s, check 0,28+0,22 s, zakreślacz 0,4 s, skreślenie 0,25 s.
- `behind` (tekst za plecami): 2+ w longu, na tezach (4-6 na 15 min w referencjach), tylko gdy tło za Kamilem jest puste.
- `lower` z `style/brand.json` (`lower_sub`), w pierwszych 15 s.
- Metafory z życia > diagramy (szlaban vs znak, checklist pilota, redaktor książki). Liczby z fact-checkera.
- Karta nie zasłania twarzy w trybie pełnym; pip/split dla scen na pełny ekran.
- Gramatyka ekranu (`screen_grammar.screen_pass`, builder planu woła przed zapisem `gfx_specs.json`): mem z wycinkami
  `sticker` w `style/memes.json` -> naklejka obok twarzy; scena <= 5 elementów -> `layout: "side"`; karta trzyma czas
  czytania; dwa osobne ekrany bliżej niż 3 s -> jeden blok (Kamil 2026-11-05: „zbyt często przenosimy się na osobny ekran”).

**Gotowe gdy:** `film_check` long.chapters, long.explainers, long.explainer_count, long.graphics, long.behind, long.lower OK;
klatka kontrolna każdej sceny obejrzana (`gfx/` png) przed renderem.
