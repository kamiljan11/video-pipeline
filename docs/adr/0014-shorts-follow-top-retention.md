# ADR-0014 — Shorty wg praktyk twórców z najlepszą retencją

Data: 2026-11-05 | Status: przyjęte (Kamil 5.11: „everything decide on practices of most best retention watched master creators”) |
Drzwi: dwukierunkowe | Przegląd: po pierwszych danych retencji z YouTube Studio (film 2)

**Kontekst:** `style/REF-shorts-top.md` (30 top shortów, 6 twórców, 12 mies.) zostawił 7 decyzji otwartych. Kamil przekazał je
regule „rób jak najlepsi”. Reguły Kamila z poprawek longa (`long.screen_switches`, `long.speaker_back`) dotyczą longa.

| # | logika (REF) | twórcy (mediana [Q1; Q3]) | my przed | decyzja |
|---|---|---|---|---|
| T8 | koniec shorta | 0,23 s ciszy po ostatnim słowie, 0/30 z planszą | plansza 3,5 s „Pełny odcinek…” | bez planszy, `tail` 0; bramka `short.end` (`tail_max` 0,6 s w `style/checklist.json`). Plansza tylko ze `skip` i powodem |
| T3 | powrót twarzy między pełnymi ekranami | 1,5 s [0,75; 3,5] | 0,1 s (mignięcie twarzy między scenami) | luka < 0,75 s = jeden blok; bramka `short.speaker_back` >= 0,75 s |
| T3 | pełne ekrany na minutę | 3,6 (0,6 na 10 s [0,12; 1,74]) | 1,3-4,5 po złączeniu bloków | w przedziale twórców, bez osobnej bramki |
| T9 | szerokość twarzy w 9:16 | 0,33 W [0,22; 0,43] | 0,54 W | **niewykonalne na tym nagraniu**: 9:16 z 1440 px wysokości = 810 px, twarz ok. 437 px; 0,38 W wymaga kadru ok. 1150 px = 2044 px wysokości. Na przyszłość: nagranie z dalszej odległości (twarz ok. 0,12 szerokości kadru 16:9, dziś 0,17) |
| T5 | twardy skok zoomu 1,28x co 5,8 s | 15/30 shortów, 5/6 twórców | `zoom_every_cut` 1,0/1,15, `face_track` przycina do ~1,0 (głowa 73 % wysokości) | czeka na T9: przy twarzy 0,54 W skok 1,28x ucina głowę (`head_check`) |
| T1 | hak w splitcie | 12/18, sygnał retencji niejednoznaczny | scena + kółko z twarzą | bez zmiany; A/B na własnych shortach po publikacji |
| T6/T7 | napis w pigułce y 0,70-0,78, tytuł w haku do 3 s | 14/18, 6/6 | `caption_box`, `caption_v` 450 (y 0,77), `hook_text` 2,6 s | już zgodne |
| - | memy w shorcie | n/d | memy 2,7-4,3 s między scenami (nie do przeczytania) | mem dostaje czas czytania albo wypada; `short.meme` ze `skip` i powodem, gdy nie ma miejsca |

**Odrzucone:** limit pełnych ekranów z longa (1,5/min) dla shortów: twórcy w shortach przełączają ok. 2,4 razy częściej, a nasze
shorty mają twarz w kółku przez cały czas sceny. Plansza końcowa z CTA: 0 z 30 top shortów; mówione CTA zostaje w treści.

**Konsekwencje / cofnięcie:** stary plan shorta z `"tail": 3` + `END` dostaje FAIL `short.end`; cofnięcie = `skip` w planie albo
usunięcie punktu z `style/checklist.json`. Metryka: retencja i % obejrzeń do końca w YouTube Studio vs shorty filmu 1 (z planszą).
**Koszt cykliczny:** 0 zł.
