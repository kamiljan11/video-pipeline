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

- Objaśnienie jak u arjay (`style/REF-shorts-arjay.md`): prawdziwe rzeczy (`table` z wierszami, imiona, prawdziwa komenda w `code`),
  nie szare kreski; stan zmienia się w tym samym elemencie na słowo (`set`, `state`, `set_cell`, `mark`), coś rusza się co <= 2,5 s;
  `"cam": "grow"` (+ `"look": "paper"` w shortach), żeby pierwszy element wypełniał kadr. Short = własny pionowy układ, 1–3 elementy
  naraz, stare z `gone`; nie ten sam rysunek co w longu.
- Gramatyka obrazu (runda 2, Kamil 2026-11-16: „on bardziej wizualizuje więcej rzeczy, a my tylko napisy”): każde zdanie sceny
  dostaje rysunek wg rodzaju myśli: proces -> `flow`, ilość -> `grid`, porównanie -> `bars`, czas -> `timeline`, wybór -> `quiz`,
  rzecz/stan -> `form` / `table` / `win`, czego nie ma -> `strike_at`. Napis (`chip`, `text`, `big`) to dodatek do rysunku, nie
  rysunek. Short: każda myśl = nowa pełna kompozycja (`gone` + `cam: grow`), nie dokładanie do jednej.

**Gotowe gdy:** `film_check` long.chapters, long.explainers, long.explainer_count, long.graphics, long.behind, long.lower OK, scene_beat, scene_concrete i scene_visual bez ostrzeżeń;
klatka kontrolna każdej sceny obejrzana (`gfx/` png) przed renderem.
