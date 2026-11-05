# Słownik (video-pipeline)

Pełny słownik planu i EDL: repo panelu, `docs/GLOSSARY.md`. Tu terminy z montażu zespołowego (ADR-0011) i kart.

| Termin | Znaczenie |
|---|---|
| karta (grafiki) | jedna grafika na ekranie, wpis w `gfx_specs.json` renderowany do `gfx/<id>.mov` (`chap`, `kw`, `slide`, `web`, `scene`, `float`, `lower`, `end` …) |
| karta roli | plik `team/roles/<rola>.md`: misja, wejście, wyjście, kiedy etap skończony. Nie mylić z kartą grafiki |
| scena (`scene`) | karta-schemat: elementy (`k`) na płótnie 2560x1440 i kamera, która je kadruje (ADR-0010) |
| element (piece, `k`) | jedna rzecz w scenie: okno, terminal, węzeł, napis `say` … (lista: README › Scena) |
| przystanek kamery (`cam`) | `{t, on}`: co kamera kadruje w chwili `t` |
| rozdział / `chap` | część filmu z `story.json`; karta `chap` otwiera ją na ekranie (do 3 s od pierwszego słowa części) |
| bramka | sprawdzenie, które zatrzymuje render z nazwą: `edl_guard`, `scene_check`, `film_check` |
| lista kontrolna (checklist) | `style/checklist.json`: co każdy long, short i folder `out/` musi mieć; `skip` w planie = pominięcie z powodem |
| paleta (muzyki) | `music_palette {name, key}`: inny utwór na każdy film; rejestr w `render/music_ledger.json` |
| behind | karta za postacią: tekst między tłem a mówiącym (`behind.py`, ADR-0005) |
| cover | część karty `behind` zasłonięta przez mówiącego (0–1, `gfx/<id>.cover.json`); `film_check` przepuszcza najwyżej 0,15 |
| faza (`phase`) | punkt `style/checklist.json` sprawdzany osobnym wywołaniem `film_check.py --phase <nazwa>` (`behind`: po `behind.py`) |
| short / rolka | film 9:16 z fragmentu longa (`plan_<id>.json`, `"vertical": true`); „rolka” = to samo na Instagramie |
| kandydat (`clips.json`, `posts.json`) | fragment albo post oceniony w rubryce 0-3; `"make": true` = musi być w `out/` |
| pakiet | `out/youtube/*.md` (tytuły A/B/C, opis, rozdziały, tagi), `out/thumbnails/`, `out/posts/` |
| mem (`meme`) | karta ze znanym memem (szablon z `style/memes.json`, obraz w `render/memes/`, ADR-0008) i naszym tekstem w jego polach; 9:16: `split` / `full` / `corner`, 16:9: obraz na lewo od PiP |
| naklejka (`sticker`) | 16:9: wycięta postać albo twarz z mema obok mówiącego, w wolnym polu po prawej (`render.mjs` STICKER_BOX); nie osobny ekran, bez PiP (Kamil 2026-11-05: „memy wycinać i wklejać dookoła mnie”) |
| układ `side` | 16:9: scena do 5 elementów rysowana obok mówiącego (`scene_lib.mjs` SIDE), on zostaje na pełnym kadrze; `screen_grammar.py` nadaje go sam |
| osobny ekran | karta, która zasłania mówiącego (`gfx_types.is_full`); `film_check` liczy ich częstotliwość, udział czasu i przerwy między nimi |
| układ `corner` | 9:16: grafika na cały ekran, Kamil w kółku w prawym dolnym rogu (`gfx_types.CORNER`) |
| PiP | 16:9: twarz w okienku w rogu nad pełnoekranową kartą (`slide`, `web`, `scene`, `meme`; `assemble.py`). Okienko wycinane jest z nagrania wokół głowy danego fragmentu (`gfx_types.pip_window`: głowa = 62% wysokości okienka, nad nią 12% zapasu), a nie z przybliżonego obrazu (Kamil 2026-11-05: „scentruj”); tylko z kluczem planu `"head_track": true` (stare EDL-e bez klucza renderują się jak dawniej), `film_check` wymaga go przy oknach z twarzą |
| grafika posta | `grafika.png` posta LinkedIn (`gfx/post_gfx.mjs`): sama niesie przekaz, bez tekstu posta; `post_check.py` sprawdza OCR-em, czy widać jej słowa, i kontrast WCAG |
| punch-in | szybki najazd kamery na twarz na ważnym słowie (`emph` w planie); pod kartą z twarzą w boksie/kółku/PiP go nie ma |
| `punch_headroom` | ile nad twarzą zoom musi zostawić: `"hair"` cała głowa, `"face"` czoło-broda (ADR-0012) |
