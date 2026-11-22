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
| face_full | udział czasu longa, w którym na twarzy nie ma niczego z EDL (karta, float, sticker, scena, lower, chap, end, b-roll); `film_check` long.face_full <= 0,35 (autor kursu CCC, n=1, do rewizji po szerszym badaniu); liczy każdy overlay, więc jest niższy niż pomiar detektorem twarzy na renderze (twarz widać też w PiP, obok kart kw i stickerów) |
| faza (`phase`) | punkt `style/checklist.json` sprawdzany osobnym wywołaniem `film_check.py --phase <nazwa>` (`behind`: po `behind.py`) |
| short / rolka | film 9:16 z fragmentu longa (`plan_<id>.json`, `"vertical": true`); „rolka” = to samo na Instagramie |
| fragment testowy (`fragment.py`, `FRAGMENT.json`) | okno słów longa (keeps w kolejności odtwarzania) wycięte z `plan_long.json` do nowego work dir, żeby sprawdzić pipeline longa na ~3 min przed renderem całego (long-lite faza 7); != fragment longa na short |
| karuzela (Instagram) | post z 5-10 slajdów 1080x1350 (`out/instagram/<post>/slide_NN.png` + `caption.json` z `alt[]`), sprawdza `ig_check.py`; slajdy z `carousel.json` (hak, 3-8 myśli, wezwanie), renderuje `ig_carousel.py` + `gfx/carousel_gfx.mjs` |
| Reel | short wrzucony na Instagram; podpis w `out/instagram/reels/<short>.json`, link „w bio”, bo w podpisie nie jest klikalny |
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
| ogon (`tail`) | sekundy obrazu po ostatnim słowie (plan/EDL `tail`, ffmpeg tpad/apad); w shorcie <= 0,6 s i bez karty `end` (bramka `short.end`, ADR-0014) |
| `gfx_lead` | o ile sekund grafika wchodzi przed swoim słowem (klucz planu, -0,5..-0,1 s; ADR-0015) |
| głos (`style/voice.md`) | jak Kamil pisze, z jego tekstów; lista `## Zakazane` blokuje posty i artykuły |
| artykuł | wpis na blog kamiljan.com z filmu (`out/blog/<slug>/article.json`, `article_check.py`); wchodzi PR-em `publish_post.py`, merge = Kamil |
| hook | pierwsze słowa shorta, na ekranie od 0 s (`hook_text` planu); z `clips.json` `hook` |
| zabójcy hooka | 6 błędów, które `hook_check.py` odrzuca: powitanie, tytuł-lista, rozbieg, mglista obietnica, brak stawki, brak tekstu w 1. klatce (ADR-0016) |
| bank hooków | `style/hook_bank.json`: sprawdzone hooki (`own-*`) i mechanizmy (`mech-*`); `result` = wyświetlenia / mediana kanału, null do pomiaru |
| `hook_from` | id wiersza banku, od którego wyszedł hook shorta (`clips.json`) |
| wariant hooka | jeden z >= 3 hooków kandydata w `clips.json` `hooks`; wybrany = `hook` |
| still (stopklatka karty) | jedna klatka karty graficznej, gdy wszystko już weszło (`still` w specu albo ostatnie wejście + 0,6 s), na prawdziwej klatce filmu, ze zdaniem mówionym pod nią (`stills.py`) |
| akceptacja stilla | klucz renderu karty w `gfx/stills/accepted.json` (`stills.py accept`); od pierwszego arkusza bez niej `render.mjs` nie robi `.mov` (ADR-0018) |
| tokeny ruchu | czasy ruchu kart w klatkach przy 30 fps, 4 krzywe (land, pop, shift, leave), 5 staggerów; `gfx/motion_tokens.mjs` (ADR-0017) |
| `"motion": "tokens"` | klucz karty sceny: czasy z tokenów; bez klucza = `legacy`, czasy sprzed tokenów (gotowe filmy bez zmian) |
| stagger | odstęp wejścia kolejnych elementów grupy (wiersze, linie terminala, wiadomości), w klatkach; max 12 |
| `{{LONG_URL}}` | znacznik w opisie shorta w miejscu linku do longa; po publikacji longa `python3 desc_check.py --fill-long <url> out` wstawia prawdziwy link (desc_check daje WARN, dopóki znacznik jest) |
| `publish_day` | dzień publikacji posta w `posts.json`, liczony od premiery longa (0 = dzień premiery); jeden post dziennie |
| `cta_variant` | forma zamknięcia posta LinkedIn: `question` (ostatnia linia = pytanie) albo `ps` („P.S. …?”); zapisana w `linkedin.json`, do przeglądu ADR-0015 (do czasu `results.jsonl` przegląd czyta ją z `out/posts/*/linkedin.json`) |
| end screen | elementy YouTube Studio (film, playlista, subskrypcja) w ostatnich 5-20 s longa; `## End screen` w long.md mówi, na co wskazują |
| `first_comment` | tekst pierwszego komentarza pod postem LinkedIn (`linkedin.json`); tam idą linki ponad jeden w treści (dziś wklejany ręcznie, kod go nie sprawdza) |
| rejestr badań (ledger researchu) | `creator-study/round2/ledger.jsonl`: jedna reguła z badań = jeden wpis z `id`, `form`, `status` (`todo`/`done`/`merged`/`deferred`/`rejected`) i `ref`; nie mylić z rejestrem muzyki `render/music_ledger.json` (ADR-0019) |
| `done` vs OK w filmie | `done` w rejestrze = jest kod i punkt `film_check` (`check:<id>`); OK w filmie = ten punkt przeszedł w raporcie danego filmu (`research_gate --report`); render wymaga obu |
| `read_along` | zaznaczenie linii cytatu (terminal, okno, plik) w chwili, gdy Kamil ją czyta (L16b); w planie indeksy słów |
| `roadmap` / `part_tag` | `chap_style` karty `chap` (L9): `roadmap` = cała mapa części (zrobione / bieżąca / następne), `part_tag` = mała plakietka części w lewym górnym rogu, mówca zostaje |
| definicja (`define`) | karta `lower` z `define: true` (L12): termin w kolorze akcentu i definicja do 20 słów |
| `note` | mała karta z ikoną lucide i jednym zdaniem (L21), np. „Link do repozytorium w opisie” |
| nie kandydat (`odd_face`) | klatka, której `frame_pick.py` w ogóle nie bierze na miniaturę ani okładkę: wzrok w bok, w dół lub w górę, przymknięte oczy, dziubek, wciągnięte usta, głowa odwrócona lub przechylona (MediaPipe, ADR-0020) |
| blendshapes | 52 liczby 0..1 z MediaPipe Face Landmarker opisujące ruch twarzy (np. `eyeLookOutLeft`, `eyeBlinkLeft`, `mouthPucker`, `jawOpen`); `frame_pick.expression` liczy z nich wzrok i minę |
| yaw / pitch / roll | obrót głowy w stopniach: w bok / góra-dół / przechył (macierz MediaPipe); okładka: najwyżej 10° / 12° / 9° |
| mishear | whisper nie usłyszał słowa, które w filmie jest wyraźne (głos ≥ 10 dB nad muzyką albo słychać je w krótkim oknie); `words_check sound` daje wtedy WARN, nie FAIL (ADR-0021) |
| stemy głosu / podkładu | dwa osobne ślady audio (sam głos i muzyka+efekty) wyrenderowane z grafu `assemble.audio.args.json`; z nich `words_check` mierzy, o ile dB głos jest nad podkładem |
| „not measured” | `words_check` nie mógł zmierzyć flagi (brak stemów, brak miejsca na osi, ffmpeg padł): zostaje FAIL |
| „not judged” | `short.punch` przy < 10 s twarzy z miejscem na punch: wynik 99 z tym opisem w raporcie, short oceniają reguły kart (ADR-0021) |

## Synchronizacja obrazu i dźwięku (ADR-0022)
- **desync** — o ile ms głos gotowego filmu jest za (+) albo przed (−) ustami, względem nagrania; `lip_check.py` mierzy go na kawałkach bez kart (ruch obrazu + obwiednia głosu).
- **siatka klatek nagrania** — czasy klatek `v0 + k/30` (film 2026-11-04: `v0` = 0,033 s, dźwięk od 0); `timeline.snap_in` stawia `-ss` tuż przed najbliższą klatką, żeby obraz i dźwięk kawałka zaczynały się w tym samym miejscu.
- **opóźnienie łańcucha audio** — ile ms filtry `audio` planu przesuwają głos (afftdn 25 ms, alimiter 5 ms bez `latency=1`); `av_latency.chain_ms` mierzy je sygnałem testowym, `assemble.py` je odcina.

## Mapa funkcji (ADR-0023)
- **funkcja (capability)** — rzecz, którą pipeline umie dać filmowi: typ karty, opcja specu karty/sceny (`opt.behind`), element sceny, tło, wejście, klucz planu, menu; wpis `kind.name` w `style/capabilities.json` z właścicielem (karta roli) i bramką.
- **use** — dla formy (long/short): `required` (w filmie albo `skip cap.<id>` z powodem), `report` (WARN, gdy nieużyta), `infra` (kod robi zawsze), `never` (nie dla tej formy, z `why`), `menu` (lista do wyboru — memy, palety, moody, dźwięki kart; `brief` pokazuje wartości z kodu, film nie jest z nich rozliczany).
- **punkt designu** — numerowana pozycja `## Order of work` w `docs/designs/*.md`; wiersz `design:<plik>:<n>:<forma>` w rejestrze badań.


## Cięcie
- **dubel (retake)** — to samo zdanie powiedziane dwa razy, bo pierwsze się nie udało; w filmie zostaje jedno, lepsze ujęcie. Bramka `long/short.retakes` (`film_check.retakes_left`: te same 4 słowa 2x w 20 s czasu filmu, bez skipu); powtórzenie celowe = klucz w planie `retakes_ok` z całą powtórzoną frazą i powodem.
- **dubel słyszany w cięciu (`retake_check.py`)** — druga droga wykrycia dubla, w dry runie: dźwięk cięcia dzielony na wypowiedzi po pauzach, każda transkrybowana osobno, potem ta sama reguła co wyżej (`retakes.py`, wspólna dla obu dróg). Powód: transkrypt całego nagrania zgubił jedno z dwóch podejść (fragment 2026-11-14, 1:00), więc plan słów dubla nie widział. Final nie odpala jej ponownie: bez zaliczonego dry runu final nie rusza (`dry_run.py`), a cięcie jest to samo.
- **muzyka pod głosem (`music_check.py`)** — bramka longa: mediana „głos minus podkład” w oknach z mową ma leżeć w 14–28 dB (stałe `MIN_DB` / `MAX_DB`), mierzone na rozdzielonych ścieżkach z grafu audio `assemble.py`. Poniżej = muzyka walczy ze słowami, powyżej = muzyki nie słychać (fragment 2026-11-14: 48 dB). Strojenie filmu = dane planu: `music_db`, `music_duck` (`threshold`, `ratio`, `mix`; `mix` < 1 = podłoga, muzyka trzyma jeden poziom pod głośnym i cichym słowem). Zakres ustawiony na jednym fragmencie: po pierwszym filmie z inną muzyką sprawdzić i wpisać wynik do NOTES_LOG.
- **czyszczenie głosu (`voice_clean`)** — klucz planu `"voice_clean": "dfn"`: głos surowego cięcia przechodzi przez DeepFilterNet (`voice_clean.py`, binarka poza repo: `VP_DEEP_FILTER` albo `~/.local/share/vp-voice/dfn/deep-filter`) przed łańcuchem `audio`; łańcuch nie ma wtedy `afftdn` ani `acompressor`. Pomiary wyboru: nagłówek `voice_clean.py`.

## LinkedIn (`linkedin.py`, ADR-0009, ADR-0027)

| termin | znaczenie |
|---|---|
| spec | `<dir>/linkedin.json`: tekst posta, hashtagi, pierwszy komentarz i media (`carousel`, `video` albo `grafika.png` obok) |
| kod akceptacji | 12 znaków skrótu tego, co wychodzi publicznie (tekst, tytuł/alt text, komentarz, bajty pliku); drukuje go dry run, `--publish` i kolejka go wymagają |
| dry run | `linkedin.py publish <spec>` bez `--publish`: sprawdza token i autora, pokazuje treść i kod, nic nie wysyła |
| rekord | `<dir>/linkedin.published.json`: zakładany przed pierwszym zapisem do LinkedIn; `published` = post jest, `pending`/`unknown` = mógł wyjść |
| SEEN | `~/.local/state/vp-linkedin/seen/`: ten sam tekst posta z innego katalogu = odmowa (bez duplikatów) |
| kolejka | `~/.local/state/vp-linkedin/queue.jsonl`: pozycje (czas Europe/Warsaw, spec, kod akceptacji) dla `run-due` |
| `waiting` / `due` / `done` | czas nie minął / minął, do publikacji / rekord `published` |
| `late` | czas minął o > 3 h (`MAX_LATE_H`): nie publikujemy starych postów hurtem |
| `stuck <stan>` | rekord istnieje, ale nie `published`: publikacja przerwana, sprawdź profil (RUNBOOK) |
| tik | jedno uruchomienie timera (co 15 min): najwyżej jeden post |

## Podcast (ADR-0031)
- **L / R** — osoba po lewej / po prawej stronie kadru szerokiego (tak widzi to kamera, nie widz z miejsca rozmówcy).
- **ujęcie `wide`** — cały kadr z obiema osobami; `L` / `R` — wycinek jednej osoby z tego samego nagrania 4K („wirtualny multicam”).
- **`stack`** — short 9:16 z dwoma panelami: L na górze, R na dole; napisy na styku.
- **backchannel** — krótkie „mhm”, „no”, śmiech słuchacza; nie odbiera głosu i nie przełącza ujęcia (`backchannel_s`).
- **ruch ust** — miara mówcy w `podcast_faces.py`: zmiana obrazu w dolnej części twarzy między klatkami, każda osoba względem swojej mediany.
- **motyw `dworak`** — kolory kanału ArkadiuszDworak.pl (`style/themes/dworak.json`, wariant ciemny strony); wybór przez `work/theme.json`. Nasze filmy zostają na motywie domyślnym / `cetus`.
- **`word_punches`** — EDL trybu podcast: `[{t, amt, speed}]` = czasy filmu najazdów na słowa z `emph`; `podcast.py` kładzie je na kawałkach (`build_edl` nie zmienia zoomu segmentów).
- **rodzaj materiału (`content_kind.json`)** — `solo` (jedna osoba do kamery, reguły jak dotąd) albo `talk` (dwie osoby w jednym kadrze, reguły podcastu). Mierzy `content_kind.py` (klatki z całego nagrania, YuNet, progi `style/content_kind.json`; niejasno = solo + WARN); czyta `kind.is_talk()`: klucz `"podcast"` w planie wygrywa, bez niego pomiar, bez pomiaru solo. ADR-0032.
- **`punch_off`** — EDL trybu podcast: `[[od, do], ...]` okna kart nad twarzą (`SIDE_BOX`, nie `beside`), pod którymi nie ma najazdu; raport `podcast.py`: `punches`, `punch_under_card` (pod kartą), `punch_skipped` (na stacku albo za blisko cięcia), `stack_under_card`.

## Objaśnienie jak u arjay (style/REF-shorts-arjay.md, ADR-0028)
- **look paper** — jasna strona sceny (`"look": "paper"`): ciepła biel, białe karty, czarny tusz, jeden limonkowy zakreślacz (ton `lime`).
- **cam grow** — kamera sceny kadruje tylko elementy już na ekranie; pierwszy wypełnia pole, kadr poszerza się z każdym wejściem (`grow_zmax`).
- **set / set_cell / state** — zmiana w tym samym elemencie na słowo: nowa wartość pigułki, liczby, komórki tabeli; wiersz zapalony (bad/ok/hl/off).
- **tag** — etykieta (osoba, rzecz) z linią prowadzącą do pudełka albo wiersza (`"tabela.1"`).
- **kotwica wiersza** — `"<id>.<n>"`: n-ty wiersz okna, terminala, czatu, tabeli albo linia kodu, mierzone w Chrome (`gfx/anchor_lib.mjs`).
- **scene_beat / scene_concrete** — bramki (warn): scena zmienia coś co <= 2,5 s; najwyżej 1/3 wierszy to szare `~`.
- **gramatyka obrazu** — reguła „rodzaj myśli -> rysunek”: proces = `flow`, ilość = `grid`, porównanie = `bars`, czas = `timeline`, wybór = `quiz`, rzecz/stan = `form` (style/REF-shorts-arjay.md).
- **scene_visual** — bramka (warn): najwyżej połowa własnych elementów sceny tylko pisze (`chip`, `text`, `say`, `big`, `stat`, `steps`).

## Płynność (`smooth_check.py`)
- **puls klatki kluczowej** — skok obrazu na klatce kluczowej x264 (domyślnie co 250 klatek = 8,33 s) względem klatek obok; przy słabym kodowaniu widać go jako „klatkowanie co parę sekund”. Limit 1,8x.
- **podwojona klatka** — klatka równa poprzedniej, gdy obraz wokół się rusza (zgubiony ruch).
