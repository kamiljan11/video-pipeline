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
| short / rolka | film 9:16 z fragmentu longa (`plan_<id>.json`, `"vertical": true`); „rolka” = to samo na Instagramie |
| kandydat (`clips.json`, `posts.json`) | fragment albo post oceniony w rubryce 0-3; `"make": true` = musi być w `out/` |
| pakiet | `out/youtube/*.md` (tytuły A/B/C, opis, rozdziały, tagi), `out/thumbnails/`, `out/posts/` |
| mem (`meme`) | karta ze znanym memem (szablon z `style/memes.json`, obraz w `render/memes/`, ADR-0008) i naszym tekstem w jego polach; 9:16: `split` / `full` / `corner`, 16:9: obraz na lewo od PiP |
| układ `corner` | 9:16: grafika na cały ekran, Kamil w kółku w prawym dolnym rogu (`gfx_types.CORNER`) |
| PiP | 16:9: twarz w okienku w rogu nad pełnoekranową kartą (`slide`, `web`, `scene`, `meme`; `assemble.py`) |
| punch-in | szybki najazd kamery na twarz na ważnym słowie (`emph` w planie); pod kartą z twarzą w boksie/kółku/PiP go nie ma |
| `punch_headroom` | ile nad twarzą zoom musi zostawić: `"hair"` cała głowa, `"face"` czoło-broda (ADR-0012) |
