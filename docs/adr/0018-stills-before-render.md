# ADR-0018 — Stopklatki kart przed renderem i bramka akceptacji

Data: 2026-11-07 | Status: przyjęte (Kamil 7.11: „dawaj dalej P1 taski”, Skool CCC Taski #9; „ja chcę oglądać najpierw”) | Drzwi: dwukierunkowe |
Przegląd: po pierwszym filmie przejściu całej pętli (arkusz, akceptacja, render) — czas Kamila na arkusz vs uwagi po renderze

**Kontekst:** błędy kart (element na słowie, karta nie do zdania, którą ilustruje) Kamil widział dopiero w gotowym filmie,
po godzinach renderu. Kurs Skool CCC (pakiet storyboard): stopklatka strony na prawdziwej klatce wideo ze słowami pod nią,
najpierw 2 najważniejsze, potem arkusz; dopiero po akceptacji budowa.

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| stopklatka | ta sama strona co `.mov` (`render.mjs --stills`), chwila = `still` w specu, inaczej ostatnie wejście sceny + 0,6 s, inaczej 60 % karty | `gfx/render.mjs` `stillTime` |
| tło | klatka źródła w chwili karty (EDL `at` przez segmenty), bez zoomu EDL; short: wycinek 9:16 wokół `face` | `stills.py` `source_at`, `frame` |
| zdanie | słowa słyszane, gdy karta jest na ekranie (`viewer_pack.film_words`) | `stills.py` `said` |
| arkusz | 2 kolumny, komórka 960x540 + 110 px podpisu (id, czas, zdanie), kolejność filmu; `sheet.md` ze zdaniami po polsku | `gfx/stills/sheet.jpg` |
| bramka | karta filmu, który ma arkusz (jej id w `gfx/stills/scope.json` pod nazwą planu filmu: każdy arkusz, także `--only`, zapisuje wszystkie karty z EDL filmu i zastępuje jego listę, więc karta usunięta z EDL wypada z bramki), renderuje się tylko z kluczem renderu zaakceptowanym po ostatniej zmianie; wszystkie odmowy nazwane przed renderem; `gfx/` jest wspólny dla longa i shortów, więc karty filmu bez arkusza i nieużywane nie są tu blokowane; `STILLS=off` = obejście z WARN | `render.mjs`, `stills.py accept` |
| zakres | filmy bez arkusza (stare, testy) bez zmian w renderze; checklista `long/short.stills` wymaga arkusza od filmu z kartami | brak `scope.json` = brak bramki renderu |

**Odrzucone:** bramka zawsze włączona (zablokowałaby testy i filmy sprzed stills bez korzyści); zgoda na cały arkusz jednym
kliknięciem jako domyślna (`--all` jest, ale rola nie powinna go używać za Kamila); podpis polskimi literami na arkuszu
(cv2 nie ma ą/ę; polskie zdania są w `sheet.md`).
**Luka zamknięta:** film bez arkusza nie przejdzie checklisty: `long.stills` / `short.stills` w `film_check` (każda karta filmu w `accepted.json`); bramka w `render.mjs` pilnuje, że wersja zaakceptowana = renderowana (`film_check` sprawdza tylko obecność id: klucz renderu liczy JS, więc karta zmieniona po akceptacji przechodzi checklistę i staje dopiero w renderze z nazwaną komendą).
**Metryka:** uwagi Kamila do kart po renderze vs przed stillami (film 2: lista w `POPRAWKI-2026-11-05.md`); czas arkusza z wyniku `stills.py` („N stills in S s”), film 2 long: 93 karty, 57,7 s.
Koszt cykliczny: 0 zł (lokalnie: Chrome, ffmpeg); ok. 1 min na arkusz filmu.
