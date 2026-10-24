# ADR-0004 — Motyw kolorów jako dane (`work/theme.json` → `style/themes/<nazwa>.json`)

Data: 2026-10-24 | Status: przyjęte | Drzwi: dwukierunkowe (usunięcie `theme.json` = stare kolory) | Przegląd: 2027-01-15

**Kontekst:** Kamil chce grafik w barwach Cetus (granat #0A1430, niebieski #086AD8, akcent #6FA7EC; źródło: artifact ECLMjWrcqos833GzxyoCVy) zamiast turkusu szablonu. Kolejny klient = kolejna paleta. Kolory były wpisane na sztywno w `gfx/template.html`, `build_edl.py` (napisy ASS), `assemble.py` (pasek postępu) i `gfx/pip_frame.png`.

**Decyzja:** paleta jest plikiem danych. `work/theme.json` `{"theme": "cetus"}` wybiera `style/themes/cetus.json`; jego `"css"` (tokeny `--acc`, `--ink`, `--bg-a`…) nadpisuje `:root` szablonu kart. Ten sam plik czytają: `gfx/theme_lib.mjs` (karty; stempel `<id>.mov.key` wymusza przerender po zmianie motywu) i `themes.py` (akcent napisów, tło haka, pasek, ramka PiP). Bez `theme.json` wynik jest jak przed zmianą (szablon ma te same wartości w tokenach; test bit w bit ASS w `panel/tests/test_pipeline_compat.py`).

**Odrzucone alternatywy:**
- **Podmiana kolorów w szablonie na Cetus:** najprostsze, ale druga paleta (klient) znów wymaga edycji kodu w 4 miejscach.
- **Motyw w planie filmu (`plan_*.json`):** karty są wspólne dla całego projektu (`gfx_specs.json`), więc motyw per film rozjechałby się z kartami.
- **Jeden loader (np. Python generuje CSS dla Node):** dodatkowy krok w `run_v4.sh`; dwie małe funkcje z tymi samymi regułami są tańsze niż nowy etap.

**Konsekwencje (koszt):**
- Reguły nazwy i walidacji są w dwóch miejscach (`themes.py`, `gfx/theme_lib.mjs`); obie mają testy (`tests/test_themes.py`, `gfx/test/theme.test.mjs`).
- Domyślny turkus zostaje jako literał w `template.html`, `build_edl.py`, `themes.bar_hex` i `pip_frame.png`: to cena obietnicy „bez motywu nic się nie zmienia”. Zmiana domyślnej marki = nowy motyw, nie edycja tych literałów.
- Ramka PiP to PNG generowany na motyw: `node gfx/pip_assets.mjs 600 <#acc> <nazwa>` → `gfx/pip_frame_<nazwa>_<RRGGBB>.png`. Akcent jest w nazwie pliku, więc po zmianie `--acc` `assemble.py` przerywa z gotową komendą zamiast użyć starej ramki.
- Własne kolory w HTML slajdów (`gfx_specs.json`) piszemy jako `var(--…)`, inaczej nie zmienią się z motywem.

**Koszt cykliczny:** 0 zł; nowy motyw = 1 plik JSON + 1 PNG ramki.

**Kryterium przeglądu (2027-01-15):** zostaje, gdy co najmniej jeden opublikowany film powstał z `theme.json`. Gdy żaden, rozważyć powrót do jednego zestawu kolorów w szablonie.
