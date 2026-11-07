# ADR-0016 — Lint hooków shortów i bank hooków

Data: 2026-11-07 | Status: przyjęte (Kamil 7.11: „dawaj dalej P1 taski”, Skool CCC Taski #13) | Drzwi: dwukierunkowe |
Przegląd: po 10 opublikowanych shortach z `hook_from` (wypełnione `result` vs shorty sprzed banku)

**Kontekst:** hooki shortów (`clips.json` `hook` -> plan `hook_text`) pisała rola bez reguły i w jednym wariancie. Kurs Skool CCC:
kurs C, „6 zabójców hooka”, sprawdzane listą słów, bez modelu; kurs B, 3 warianty hooka na short; bank sprawdzonych hooków
według typu, z którego każdy nowy hook startuje (mechanizm zostaje, słowa nigdy cudze).

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| lint | 6 zabójców: powitanie, tytuł-lista, rozbieg, mglista obietnica lub stos przymiotników, brak stawki, brak tekstu w 1. klatce; <= 12 słów | `hook_check.py`, bramka `short.hook_lint` |
| słowniki | dane, nie kod: słaby hook, który przeszedł = dopisać słowo | `style/hook_lint.json` |
| warianty | >= 3 w `clips.json` `hooks` (rola: 5), `hook` jeden z nich, `hook_from` = wiersz banku | `team/roles/scout-shortow.md`, bramka `out.hooks` |
| bank | wiersze `own-*` (nasze z filmów) i `mech-*` (mechanizmy ze slotami); `result` = null do pomiaru | `style/hook_bank.json` |
| metryka | `result` = wyświetlenia shorta / mediana wyświetleń kanału z 28 dni (YouTube Studio), wpisuje ręcznie Kamil albo rola social w przeglądzie tygodnia; brak skryptu (API YouTube Analytics = decyzja o OAuth, odłożona) | `style/hook_bank.json` `_doc` |

**Odrzucone:** generowanie hooków modelem w bramce (koszt i niepowtarzalność; generuje rola, bramka tylko sprawdza);
słownik rzeczowników do zabójcy „brak rzeczownika” (za duży, za kruchy; zamiast tego kotwica: liczba, akronim, cudzysłów, nazwa).

**Kalibracja:** 18 hooków filmu 2: 14 czystych, 4 bez stawki (metafory bez straty i zysku: s04, s11, s12, s13).

**Konsekwencje / cofnięcie:** film 2 (`out_v2`) nie przechodzi `out.hooks` (brak wariantów), poprawka w rundzie korekt.
Cofnięcie: usunąć `short.hook_lint` i `out.hooks` z `style/checklist.json`.
**Koszt cykliczny:** 0 zł.
