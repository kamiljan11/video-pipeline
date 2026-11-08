# ADR-0013 — Grafika posta sprawdzana OCR (tesseract) i gramatyka ekranu longa

Data: 2026-11-05 | Status: przyjęte (runda poprawek filmu 2) | Drzwi: dwukierunkowe | Przegląd: przy filmie 3

**Kontekst:** Kamil 5.11 o postach LinkedIn: „grafika sama musi nieść przekaz”; o longu: „zbyt często przenosimy się na osobny
ekran”, „nie zdąży się przeczytać”, „memy wycinać i wklejać dookoła mnie”. Pomiary: `style/REF-posts-top.md` (94 posty),
`style/REF-long-negacz.md` (1,3 przejścia na osobny ekran na minutę vs nasze 2,9 w v2).

**Opcje (grafika posta):**
| opcja | za | przeciw |
|---|---|---|
| A. grafika z PIL w builderze filmu | już była | tekst ucięty, cienki font, nic nie sprawdza czytelności |
| B. `gfx/post_gfx.mjs` (szablony HTML w Chrome) + `post_check.py` (OCR tesseract + kontrast WCAG) | te same fonty i motyw co karty; maszyna mierzy, czy słowa da się przeczytać | nowa zależność systemowa (tesseract + dane `pol`) |
| C. B bez OCR, tylko pomiar overflow w Chrome | bez nowej zależności | nie łapie słabego kontrastu ani słów schowanych pod innym elementem |

**Decyzja:** B. Tesseract daje binaryzację adaptacyjną i czyta nawet granat na granacie, więc kontrast liczony osobno (WCAG AA
w ramce każdego słowa). Strona grafiki: lista dozwolonych wartości (`tone`, `theme`), CSP `default-src 'none'`, JS wyłączony
(review 2026-11-05: `tone` z HTML wklejał `/etc/passwd` do PNG).

**Gramatyka ekranu:** `screen_grammar.screen_pass` w builderze planu (nie w renderze): mem z wycinkami `sticker` -> naklejka obok
twarzy, prosta scena (<= `side_max_els`) -> `layout: "side"`, karta trzyma czas czytania (`film_check.reading_need`), dwa osobne
ekrany bliżej niż `long.speaker_back` -> jeden blok. Progi = dane: `style/screen_grammar.json` + `style/checklist.json`.
Odrzucone: reguły w `build_edl.py` (EDL nie zna treści karty) i w `render.mjs` (za późno, plan już ma czasy).

**Koszt cykliczny:** 0 zł. `apt install tesseract-ocr tesseract-ocr-pol fonts-dejavu-extra` lokalnie i w CI
(`.github/workflows/quality.yml`, ok. 20 s na przebieg). OCR: 2 przebiegi tesseract na grafikę, ok. 1-2 s.

**Konsekwencje / cofnięcie:** brak tesseract = nazwany problem w `out.posts` (nie traceback). Cofnięcie: punkt `out.posts`
wraca do sprawdzenia samej obecności pliku, `screen_pass` wypada z buildera planu (gfx_specs bez zmian w formacie).
Metryka: `long.screen_switches`, `long.screen_block`, `long.speaker_back`, `long.reading` w `film_check`; retencja z YouTube
Studio po publikacji (zewnętrzna, ręcznie).
