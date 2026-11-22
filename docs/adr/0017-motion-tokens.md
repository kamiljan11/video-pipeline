# ADR-0017 — Tokeny ruchu dla scen (opt-in na karcie)

Data: 2026-11-07 | Status: przyjęte (Kamil 7.11: „dawaj dalej P1 taski”, Skool CCC Taski #10, plan wizualny krok 4) | Drzwi: dwukierunkowe |
Przegląd: gdy Kamil obejrzy pierwsze karty z `"motion": "tokens"` (podgląd przed renderem filmu 3)

**Kontekst:** `gfx/scene_lib.mjs` miał kilkanaście czasów i krzywych wpisanych w miejscach użycia (`.5s`, `.55s`, `.4s`, pięć
różnych cubic-bezier). Rysowanie kreski, kółka i tiku jechało krzywą ease-in-out, więc element „waha się” przed wejściem.
Kurs Skool CCC (pakiet mograph, referencja ruchu: tylko mechanika i liczby): czasy w klatkach przy 30 fps, krzywe według roli,
wyjście = połowa wejścia, stagger w klatkach z limitem.

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| tokeny | klatki przy 30 fps (tick 2, micro 4, fast 6, base 12, slow 24), 4 krzywe (land, pop, shift, leave), 5 staggerów (glyph 1, word 3, grid 2, step 5, object 8), max 12 | `gfx/motion_tokens.mjs` |
| włączanie | klucz karty `"motion": "tokens"`; bez klucza tabela `legacy` = dokładnie dawne czasy (222 sceny filmu 2 bajt w bajt te same przed i po zmianie) | `scene_lib.mjs` `MOTION` |
| lint | karta z tokenami: zero wejść, których krzywa łagodzi oba końce; `step` <= 12 klatek | `motionProblems`, `staggerProblems`, `scene_check.mjs` |
| cache | klucz karty z tokenami obejmuje `motion_tokens.mjs` | `render.mjs` `TOKENS` |

**Odrzucone:** od razu tokeny dla wszystkich kart (zmieniłoby gotowy film 2 bez decyzji Kamila; reguła repo: zmiana wyglądu za
kluczem); lint dla kart bez klucza (22 z 89 scen longa filmu 2 by padło po fakcie; liczone, nie blokowane); dwa nastroje
„snappy” / „soft” (na razie jeden zestaw; drugi, gdy Kamil zobaczy pierwszy).
**Usunięcie `legacy`:** gdy Kamil zaakceptuje tokeny na kartach filmu 3, `motion: "tokens"` staje się domyślne dla nowych filmów; tabela `legacy` zostaje tak długo, jak gotowy film ma się renderować bez zmian (korekty filmu 2).
**Metryka:** brak liczbowej; ocena Kamila na podglądzie (zgoda albo uwaga do ruchu) i 0 problemów lintu na kartach z tokenami.
**Zakres tokenów (znany, do domknięcia z krokiem 4 planu wizualnego):** z tokenów idą wejścia kart, znaczniki, podświetlenia, wiersze, linie terminala, czat, rysowanie kresek i kółek, wyjścia; czasy `scword`, `scburst`, `scrip`, `scfill`, kursora i pakietu na linii zostają dawne. Lint sprawdza krzywe i stagger, nie limit F.slow.
**Cache:** `motion_tokens.mjs` jest w kluczu tylko kart `"motion": "tokens"` (zmiana tokenów nie renderuje ani nie unieważnia akceptacji kart legacy).
Koszt cykliczny: 0 zł.
