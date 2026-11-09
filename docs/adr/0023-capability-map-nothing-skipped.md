# ADR-0023 — Mapa funkcji: nic, co pipeline umie, nie wypada z filmu niezauważone

Data: 2026-11-09 | Status: przyjęte (Kamil: „a da sie system enforcowac zeby nie pominal rzeczy”) | Drzwi: dwukierunkowe |
Przegląd: po filmie 2026-11-04 v5 — ile skipów z powodem napisały role i czy któryś był wymówką

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
| 4 | film: każda funkcja `required` użyta (na ekranie wg EDL, klucz w planie) albo `skip cap.<id>` / skip jej punktu listy z powodem; `report` nieużyte = WARN z listą | `film_check` long/short.capabilities |
| + | rola zaczyna od `capabilities.py brief <rola>` | `team/RUNBOOK.md` |

**`use` z dowodów, nie z głowy:** klucz planu, który long 2026-11-04 ustawiał, a który zmienia film = `required`; klucze
techniczne (ścieżki, cisza, nazwy) = `infra`; klucze tylko shortów (napisy, hak) = `never` w longu z `why`; typy kart longa =
`required`, shortów: `kw`, `meme`, `end` (reszta `report`), elementy scen, tła i wejścia = `report`.

**Odrzucone:** lista ręczna bez skanu kodu (starzeje się jak plan 2026-11-05); wymaganie każdej funkcji w każdym filmie bez
skipu (45-sekundowy short nie zmieści 15 typów kart; skip z powodem = świadoma decyzja, którą widać w planie).
**Ryzyko:** skip jako wymówka („nie pasuje”). Kontrola: skipy są w planie, QA-widz i Kamil je widzą; przegląd po filmie v5.
Funkcja, której skaner nie widzi (np. opcja wewnątrz specu karty: `behind`, `define`, `chap_style`), dalej zależy od checklisty.
**Koszt:** skan ~0,1 s; 0 zł. **Metryka:** funkcje `required` nieużyte bez powodu w filmie (cel 0), skipy na film.
