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
Funkcja, której skaner nie widzi (opcje wewnątrz specu karty: `behind`, `define`, `chap_style`, `layout`, kamera sceny),
dalej zależy od checklisty — runda 3 (krytyk kompletności, 24 pozycje) dodaje je do skanu. Rejestr badań leży poza repo
(`~/Dane/creator-study`), więc test blokady 3 na prawdziwych designach działa tylko na laptopie; na renderze blokuje `run_v4.sh`.
**Koszt:** skan ~0,1 s; 0 zł. **Metryka:** funkcje `required` nieużyte bez powodu w filmie (cel 0), skipy na film.
