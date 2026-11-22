# ADR-0028 — Scena-objaśnienie jak u arjay: konkret, zmiana stanu na słowo, kadr rośnie

Data: 2026-11-16 | Status: przyjęte (Kamil: „zdefiniuj gdzie my jestesmy slabsi i ulepsz dla longow i shortow”) | Drzwi: dwukierunkowe |
Przegląd: po pierwszym filmie nagranym po tej zmianie

**Kontekst:** rozbiór 15 shortów `@arjay_the_dev` (`style/REF-shorts-arjay.md`): panel nie stoi dłużej niż ~2,3 s (mediana), pokazuje
prawdziwe wiersze i imiona, wartości zmieniają się w tym samym pudełku, kadr jest wypełniony. Nasza scena `s_gotowe` (long 2026-11-04):
okno ~15 % kadru przez 10 s, szare kreski, kamera `*` kadruje od 0 s cały końcowy rysunek. W shorcie ten sam rysunek co w longu
schodził do skali 0,39 (tekst 22 px).

**Decyzje:**
| # | co | gdzie |
|---|---|---|
| 1 | nowe elementy `table`, `code`, `big`, `tag`; klucz `set` na chip/text/big/stat; `look: paper`; `cam: grow` — wszystko opcjonalne, scena bez tych kluczy bajt w bajt jak dotąd (golden w `gfx/test/motion.test.mjs`) | `gfx/scene_lib.mjs`, `gfx/anchor_lib.mjs` |
| 2 | `cam: grow` zamiast zoomu na element: scena zawsze cała (NOTES_LOG 50), tylko bez przyszłych elementów | `frameStops.grow` |
| 3 | short = osobny pionowy układ (1–3 elementy naraz, `gone`), nie long w pionie; pilnuje go istniejący pomiar tekstu w `scene_check` | README › Scena, `team/roles/motion-designer.md` |
| 4 | bramki `scene_beat` (zmiana co <= 2,5 s) i `scene_concrete` (<= 1/3 szarych wierszy) jako `warn` | `film_check.py`, `style/checklist.json` |
| 5 | runda 2 (Kamil: „on wizualizuje procesy myślowe, a my tylko napisy”): gramatyka obrazu = rodzaj myśli -> rysunek; nowe elementy `flow`, `grid`, `bars`, `timeline`, `quiz`, `form`; bramka `scene_visual` (warn, <= 1/2 elementów tylko pisze) | `gfx/scene_lib.mjs`, `team/roles/motion-designer.md`, `film_check.py` |

**Kryterium warn -> błąd:** pierwszy film po zmianie; jeśli jego sceny przechodzą obie bramki bez przeróbek albo po przeróbkach
Kamil akceptuje stille, `level` zostaje usunięty (błąd). Miara: liczba scen z ostrzeżeniem na film (`film_check` wypisuje je z nazwą).

**Koszt cykliczny:** runda 1: 4 drawery + CSS (~150 linii), testy w `gfx/test/explain.test.mjs`; runda 2: 6 drawerów + CSS (~250 linii),
walidacja i `shiftPiece` dla `extends`, testy w `gfx/test/visual.test.mjs`. Każdy nowy klucz czasu musi trafić do `shiftPiece`, `film_check.scene_events`
i `checkScene` (trzy miejsca; pg-review 2026-11-16 złapał brak w `shiftPiece`). Zmiana `scene_lib.mjs` renderuje sceny od nowa (klucz cache),
więc nie zmieniać w trakcie zaakceptowanego renderu (NOTES_LOG 31). Runda 2 nie ma jeszcze filmu, który jej używa: pierwszy film po zmianie
jest jej sprawdzianem (to samo kryterium warn -> błąd).

**Odrzucone:** przestawianie układu (FLIP, element maleje i jedzie w bok) — więcej kodu pomiaru; wraca, jeśli `grow` z pełnymi
kompozycjami nie wystarczy. Wykres liniowy i histogram — do zrobienia, gdy film ich potrzebuje.
