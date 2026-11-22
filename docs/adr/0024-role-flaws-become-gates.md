# ADR-0024 — Błąd roli = bramka; wyjście tylko nazwane i z powodem

Data: 2026-11-09 | Status: przyjęte (Kamil: „a da sie system enforcowac zeby nie pominal rzeczy”, „decyduj autonomicznie”) | Drzwi: dwukierunkowe |
Przegląd: po filmie v5 z nagrania 04.11 — ile skipów i `retakes_ok` napisały role i czy któryś był wymówką

**Kontekst:** przy budowie v5 role (montażysta, motion designer, producent shortów) oddały plany z zielonymi bramkami, a
`run_v4.sh` i tak by ich nie wyrenderował albo film miałby błąd: 8 z 18 shortów miało sceny, które `gfx/scene_check.mjs`
odrzuca; long miał dubel (Kamil powiedział coś dwa razy, „wytnij i zostaw lepszą wersję”); `critic.py` liczył surowe
długości kawałków przy `seg_exact` i zgłaszał fałszywe C2; `broll.py` i `spot_check.py` liczyły czas filmu bez `seg_exact`
(pg-review T3 data-1). Każdy błąd złapał dopiero człowiek albo render.

**Decyzje:**
| # | co | gdzie |
|---|---|---|
| 1 | scena, której `scene_check.mjs` nie przyjmuje = film nie przechodzi listy (`long.scenes`, `short.scenes`, `no_skip`); brak node / timeout / pusty wynik = FAIL z powodem | `film_check.scenes_valid`, `style/checklist.json` |
| 2 | dubel (>= 4 te same słowa w <= 20 s) zostaje w filmie tylko z `retakes_ok` w planie: klucz = CAŁA powtórzona fraza, powód mówi czemu | `film_check.retakes_left`, `docs/GLOSSARY.md` „Cięcie — dubel” |
| 3 | jeden zegar filmu: każde miejsce liczy czas wyjścia przez `timeline.src2out` / `timeline.total` z `seg_exact` EDL-a | `timeline.py`, `critic.py`, `broll.py`, `spot_check.py`, `build_edl.py` |
| 4 | karta producenta shortów: sceny shortów rysuje motion designer ze scen longa, nie szablon chipów | `team/roles/producent-shortow.md` |

**Wyjścia (jedyne):** `skip <punkt>` / `skip cap.<id>` z powodem (ADR-0023) albo `retakes_ok` z całą frazą. Punkt z
`no_skip` nie ma wyjścia. Nowa bramka tylko po realnym błędzie roli (proporcjonalność, CLAUDE.md 2026-10-13).
