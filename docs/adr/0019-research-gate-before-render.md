# ADR-0019 — Rejestr badań jako bramka renderu i folderu out

Data: 2026-11-08 | Status: przyjęte (Kamil 8.11: „dlaczego nic nie weszlo!? … po to robisz reserache zeby ulepszyć video pipeline i dopiero zregenerować całe video”, „czy realnie wprowadziles nowe logiki??? sprawdzales to”) | Drzwi: dwukierunkowe |
Przegląd: po pierwszym filmie zrobionym w całości pod bramką (film 2026-11-04 v4) — ile renderów zatrzymała i ile z tego to błędny pomiar

**Kontekst:** nocny render 2026-11-04 nie miał w sobie żadnej z 24 pozycji badań dla longa. Pozycje miały w rejestrze
(`creator-study/round2/ledger.jsonl`) status `done`, bo był do nich kod, ale nic nie sprawdzało, czy film ich używa.
Większość punktów badań w `film_check` ma poziom `warn`, więc film mógł je pominąć i przejść.

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| pozycja `done` | musi wskazać punkt `film_check`, który ją mierzy w filmie (`ref` zawiera `check:<id>`, id w `style/checklist.json`); sam kod to nie „użyte” | `research_gate.py` `problems` |
| przed renderem | `research_gate.py <forma>`: pozycja `todo` (albo `merged` do otwartej) zatrzymuje render formy | `run_v4.sh` |
| po `film_check` | `research_gate.py <forma> --report fc.json`: każdy `check:<id>` pozycji `done` ma w raporcie wiersz OK dla każdego filmu formy z raportu; WARN/FAIL albo brak wiersza = nie spełnione; SKIP = INFO z powodem z planu | `run_v4.sh` `research_used`, `report_problems` |
| folder out | `out_gate.py <work> <out>`: `film_check --out` bez FAIL i pozycje `out.*` spełnione w tym raporcie; ostatni krok przed oglądaniem przez Kamila | `out_gate.py`, `work/fc_out.json` |
| zły raport | pusty, nieczytelny albo bez pól `film/id/status/detail` = exit 2 (błąd użycia), nie przejście | `check_report` |
| wyjście | `skip` z powodem w planie (raport SKIP), `deferred` z `Kamil:`/`data:`, `rejected` z powodem | `research_gate.py` |

**Odrzucone:** tylko ostrzeżenie w raporcie (tak było; nikt go nie czytał przed renderem); podniesienie każdego punktu badań
do poziomu `fail` w `film_check` (zablokowałoby stare filmy bez pozycji w rejestrze); sprawdzanie obecności kodu (grep) zamiast
pomiaru w filmie.
**Koszt:** zablokowany render przy błędnym pomiarze; obejście = `skip` z powodem w planie (widać go w raporcie jako INFO)
albo `RESEARCH_GATE=off` w `run_v4.sh` (WARN w logu). `film_check --json` chodzi drugi raz po zwykłym przebiegu (sekundy).
**Metryka:** pozycje `done` niespełnione w filmie (`research_gate <forma> --report <fc.json>`, ostatnia linia wyjścia): film 2026-11-04 v2 shorty 142 (raport `film_check --json` planów v2), v3 0 dla każdego z 18 shortów; long v3 0. Liczby do przeglądu: `render/render.log` każdego renderu (krok `research_used`) i `work/fc_out.json`.
Koszt cykliczny: 0 zł (lokalnie).
