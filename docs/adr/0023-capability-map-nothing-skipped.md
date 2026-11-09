# ADR-0023 — Mapa funkcji: nic, co pipeline umie, nie wypada z filmu niezauważone

Data: 2026-11-09 | Status: przyjęte (Kamil: „a da sie system enforcowac zeby nie pominal rzeczy”) | Drzwi: dwukierunkowe |
Przegląd: 2026-11-16 (po filmie v5 z nagrania 04.11) — ile skipów z powodem napisały role i czy któryś był wymówką

**Kontekst:** wszystkie bramki były zielone, a long 2026-11-04 nie miał b-rolla, korekcji koloru (`grade`) ani `sfx_duck`,
nie użył kart count/list/meme/slide, a plan wizualny 2026-11-05 (rysowane linie, elementy przypięte do id, paleta ruchu,
sceny `sketch`) nie trafił do żadnego filmu: nie był w rejestrze badań, więc `research_gate` o nim nie wiedział. Role
używają tego, co nazywa ich karta i lista kontrolna.

**Decyzje (4 blokady):**
| # | co | gdzie |
|---|---|---|
| 1 | każda funkcja: właściciel (karta roli), bramka (punkt checklisty albo `gate:<plik>`), `use` per forma | `style/capabilities.json` |
| 2 | funkcje czytane z KODU (`gfx/render.mjs` typy kart, `gfx/scene_lib.mjs` KINDS/BGS/ANIMS, klucze planu w `build_edl.py` i `plan.get(...)` innych etapów); brak wpisu / wpis bez kodu / zły właściciel albo bramka = test czerwony i `FAILED capabilities map` przed renderem | `capabilities.py check`, `tests/test_capabilities.py`, `run_v4.sh` |
| 3 | design z `## Order of work` musi mieć `ledger-forms`; każdy punkt = wiersz rejestru (`todo`), `research_gate` blokuje render, dopóki nie `done`/`deferred` z powodem | `design_ledger.py`, `run_v4.sh` |
| 4 | film: każda funkcja `required` użyta (na ekranie wg EDL, klucz w planie, także wartość 0) albo `skip cap.<id>` z powodem — jeden powód na funkcję: skip punktu listy NIE zwalnia jego funkcji (long.graphics sprawdza kw, maxim, gfx i broll; jedno zdanie nie może przepuścić b-rolla); `report` nieużyte = WARN z listą; `capabilities.py map` liczy skipy na film | `film_check` long/short.capabilities |
| + | rola zaczyna od `capabilities.py brief <rola>` | `team/RUNBOOK.md` |

**`use` z dowodów, nie z głowy:** klucz planu, który long 2026-11-04 ustawiał, a który zmienia film = `required`; klucze
techniczne (ścieżki, cisza, nazwy) = `infra`; klucze tylko shortów (napisy, hak) = `never` w longu z `why`; typy kart longa =
`required`, shortów: `kw`, `meme` (reszta `report`), elementy scen, tła i wejścia = `report`. `required` musi mieć dowód
w kodzie mapy (`capabilities.py problems`): własne `why` albo `why` punktu listy TEJ formy (punkt longa nie jest dowodem dla
shorta; `check` może być `{long: id, short: id}`). Bez dowodu dla shorta -> `report` (b-roll, `sfx_style`); `card.end` w
shorcie = `report`, bo `short.end` mówi: top shorty kończą bez planszy (30/30).

**Sprawdzenie na planach 2026-11-04 (stary montaż, 2026-11-09):** `capabilities.py map` -> long: 9 `required` brak
(count, list, meme, slide, broll, end, grade, next_video, sfx_duck) — dokładnie luki z Kontekstu; short s01: 2 (kw,
sfx_duck). Blokada widzi to, czego bramki nie widziały.

**Odrzucone:** lista ręczna bez skanu kodu (starzeje się jak plan 2026-11-05); wymaganie każdej funkcji w każdym filmie bez
skipu (45-sekundowy short nie zmieści 15 typów kart; skip z powodem = świadoma decyzja, którą widać w planie).
**Recenzja T2 (2026-11-09, `~/.cache/pg-review-20261109-160123-caps`):** 0 jako „nieustawione”, `RESEARCH_GATE=off`
wyłączał też obie blokady (teraz bez wyłącznika), `required` bez dowodu, skip punktu zwalniał wiele funkcji, skan bez
znacznika = goły traceback (teraz `FAIL` z nazwą pliku; 0 znalezionych = błąd mapy), brak rejestru = `FAIL`, nie traceback.
**Ryzyko:** skip jako wymówka („nie pasuje”). Kontrola: skipy są w planie, QA-widz i Kamil je widzą; przegląd po filmie v5.
**Runda 3 (krytyk kompletności, 24 pozycje):** skan czyta też opcje specu (`sp.<klucz>` w `gfx/*.mjs`, `sp.get(...)` w etapach
Pythona -> `opt.*`, 53; `long` required z dowodem z listy: behind, chap_style, define, find, read_along, canvas_zoom), menu
(`menu.*`: memy, toony, palety, moody, dźwięki kart, style kart części, zestawy ruchu — wartości z kodu w `brief`, bez
rozliczania filmu), `P.get` we wszystkich etapach (`critic_accept`), domyślne wejście elementu sceny (DEF_ANIM, inaczej `up`).
**Runda 4 (krytyk rundy 3):** opcje czytane inaczej (`specs.get(id).get("k")`: bookend, cta; `"k" in sp`; `BOX_KEYS`:
caption_y, face_anchor, face_zoom; zagnieżdżone `behind.clean/ratio`; `sp?.x`, destrukturyzacja, `sp.type === 'x' ?`; `"k" in P`;
wejścia zestawu tokens), pola elementów sceny `pfx.*` (efekty: hl_at, strike_at, pulse_at, packet_at, gone… = report), menu
layout/theme/beat/tone; `use` poprawione: progress, edge_fix, seg_exact, min_seg -> report (domyślnie wyłączone), `beats` ->
required (bez niego żaden punch/dźwięk gramatyki), `card.end` -> check per forma, w shorcie never; grupy „jedno z”
(`explainer`: float/scene/slide/web, `meme`: meme/sticker — jak liczą long.explainers i long.memes); skip `cap.<id>` >= 10 znaków
i istniejące id (literówka = FAIL). Stary long 2026-11-04 po rundzie 4: 9 braków, w tym `beats`.
**Runda 5 (krytyk rundy 4, każda pozycja sprawdzona w kodzie):** skan specu czyta każdy etap (`*.py`, `music/*.py`; `quote` z
`critic.py` był poza stałą listą plików); pola obiektów w elemencie sceny: `rows.*` (ptaszek `mark`, `hl`), `msgs.*` (`who`),
`count.*`, `badge.*`; pola `_on/_from/_to` z `anchor_lib` poza skanem (pisze je kod, nie rola); menu `layout` bez `long` (to brak
układu w 16:9). `use` poprawione: `card.end` + `plan.end` = grupa `end` (long.end przechodzi z planszą ALBO `end: "platform"`),
`next_video` -> report; `part_framing` + `zoom_every_s` = grupa `framing` (long.framing chce jednego z nich); `punch_headroom`,
`caption_box`, `caption_v` -> report (domyślne); `caption_emph` -> check short.options (S9); `verified_claims` w shorcie ->
report (C9 w critic.py łapie liczby bez źródła); note, sticker, toon, define, upto, dim_done w shorcie -> never (render odrzuca
canvas "v"); compact, pill, face_box, face_corner w longu -> never (działają tylko w 9:16). Stary long 2026-11-04: 7 braków
(count, list, beats, broll, grade, sfx_duck, read_along).
**Runda 6 (krytyk rundy 5, bez regresji, 8 drobnych):** `"want"` = liczą się tylko te wartości (`caption_emph: "key"`,
`hook_pos: "mid"`, `end: "platform"`): ustawienie wartości domyślnej nie jest już „użyciem”; `read_along` wymagany na
elementach sceny (`pfx.read_along`), bo tam patrzy long.read_along (opcja karty web -> report); pola list specu
(`opt.cam.*`, `opt.canvas_zoom.*`); skan kart łapie `a || b` i `switch`, skan Pythona `spec.get`, `specs[o["id"]].get`,
`spec["a"]["b"]` (bez `long`/`shorts` z thumbs.json); `hook_dur` -> report (domyślne 3 s), logo* w shorcie -> never.
Stary long 2026-11-04: 6 braków (count, list, beats, broll, grade, sfx_duck); short s01: 3 (kw, beats, sfx_duck).
Punkty listy na poziomie warn (long.define, long.note, long.read_along…) stają się blokadą przez `required` — świadomie: funkcja
ma być użyta albo pominięta z powodem.
Poza mapą świadomie: pod-pola kluczy planu (np. pola `emph[]`, `broll[]`), pola `story.json`/`clips.json`/`thumbs.json`
i wyjścia `out.*` (posty, miniatury, artykuł) — pilnuje ich checklista `film_check --out`, uruchamiana na każdym filmie.
Dziury poza mapą bez bramki (krytyk r3, do decyzji): podpisy autorów b-rolla w opisie (`broll.py` je robi, nic nie sprawdza),
różnorodność typów grafik postów (`post_gfx` list/quote/bars/split/table), pokrętła tylko w EDL (pip_size, sub_style, music_offset); miniatury: `accent: "thumb"` (TH8) nic nie zmienia, dopóki
motyw nie ma tokenu `--acc-thumb` (kolor wybiera Kamil), a `arrow` jest opcją bez bramki (krytyk r4). Rejestr badań leży poza repo
(`~/Dane/creator-study`), więc test blokady 3 na prawdziwych designach działa tylko na laptopie; na renderze blokuje `run_v4.sh`.
**Koszt:** skan ~0,1 s; 0 zł. **Metryka:** funkcje `required` nieużyte bez powodu w filmie (cel 0), skipy na film.
