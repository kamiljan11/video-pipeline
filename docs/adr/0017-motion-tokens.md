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
| cache | hash scen obejmuje też `motion_tokens.mjs` | `render.mjs` `SCENE_LIB` |

**Odrzucone:** od razu tokeny dla wszystkich kart (zmieniłoby gotowy film 2 bez decyzji Kamila; reguła repo: zmiana wyglądu za
kluczem); lint dla kart bez klucza (22 z 89 scen longa filmu 2 by padło po fakcie; liczone, nie blokowane); dwa nastroje
„snappy” / „soft” (na razie jeden zestaw; drugi, gdy Kamil zobaczy pierwszy).
