# ADR-0025 — Long-lite: granice procesu zamiast kolejnych bramek po renderze

Data: 2026-11-10 | Status: przyjęte (Kamil: „przekombinowalismy”, „moze postawienie granic lepszych procesowch”, „czekamy… mozna sprobowac dzialac juz teraz”) | Drzwi: dwukierunkowe |
Przegląd: po pierwszym longu zrobionym na tych zasadach — godziny od RAW do mp4, liczba renderów, % limitu (cel: 4–6 h, 1 próbny + 1 pełny, 5–10 %)

**Kontekst:** long 2026-11-04: ~6 dni od nagrania do `long.mp4`, 5 pełnych renderów (30–50 min każdy) + noc bez wyniku, 202 commity
w trakcie filmu (`style/NOTES_LOG.md` wiersze 31–38). Bramki złapały 3 prawdziwe błędy (35, 36, 38), ale dopiero po renderze;
reszta strat to proces: kod zmieniany w trakcie filmu (31), bramka wyłączona przełącznikiem z samym wpisem w logu (5 shortów
`LIP_CHECK=off`), kontrola tylko części filmów przed renderem (34). Plan i mikrokroki: `docs/designs/2026-11-10-long-lite.md`,
`docs/designs/2026-11-10-long-lite-steps.md`.

**Decyzje:**
| # | granica | wymuszenie w kodzie |
|---|---|---|
| 1 | system ≠ film: system zmieniamy między filmami, na gałęzi, test na fragmencie (~3 min), nie na całym longu | proces + punkt 3 (zmiana kodu unieważnia próbny render) |
| 2 | pełny render dopiero po zielonym próbnym tego samego filmu | `run_v4.sh DRY=1` -> `assemble.py --dry` (obraz 640 px, pełny dźwięk z masterem) + wszystkie kontrole po renderze -> `dry_<film>.json`; bez niego `FAILED dry_run` (`dry_run.py need`, bez wyłącznika) |
| 3 | zamrożenie kodu filmu = commit z próbnego renderu | `dry_run.needed`: `manifest.code_changed(commit, film=True)` albo niezacommitowany kod -> odmowa; zmiana `edl_<film>.json` / `gfx_specs.json` -> odmowa |
| 4 | wyłączona bramka wymaga słów Kamila w planie | `waivers.py`: `"waivers": {"lip_check": "Kamil RRRR-MM-DD: …"}`; brak -> `FAILED waivers`, nic się nie renderuje; `SKIPPED_GATES:` w każdym `render.log`; żaden kod nie pisze tego klucza (`tests/test_waivers.py`) |
| 5 | nowa bramka najpierw raportuje, blokuje dopiero po realnym błędzie w filmie; najwyżej 1–2 nowe między filmami | przegląd przy ADR (proporcjonalność, CLAUDE.md 2026-10-13) |
| 6 | long zaakceptowany przez Kamila, potem reszta form na „jedź dalej” | `accept.py` + odmowa etapu B (faza 6 mikrokroków) |

**Odrzucone:** przejście na cudzy system (herk-edit-kit: inny silnik, licencja niejasna; tracimy 99 reguł Kamila); kasowanie
modułów teraz (brak danych, które nigdy nic nie łapią — decyzja po 2 filmach); osobne `manifest.py freeze` (zapis próbnego
renderu już niesie commit, drugi mechanizm = drugie miejsce do rozjechania).

**Ryzyko:** kontrola ust i dźwięku na obrazie 640 px może dawać inny wynik niż na pełnym (do zmierzenia na fragmencie, faza 7);
sesja ma zapis do repo, więc obejście jest technicznie możliwe, ale każde = commit, który unieważnia próbny render i zostaje w historii.

**Rollback:** `git revert` commitów fazy 1–2 na `feat/long-lite`; `run_v4.sh` wraca do renderu bez próbnego.
