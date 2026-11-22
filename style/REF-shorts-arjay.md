# Wzorzec: rysowane objaśnienie w shorcie, arjay_the_dev (rozbiór 2026-11-16)

Źródło: 15 ostatnich shortów kanału YouTube `@arjay_the_dev` (stan 2026-11-16), 1080x1920, 30 fps, 31–108 s, razem 1165 s.
Pliki lokalne `render/ref/arjay/<id>/v.mp4` (tylko do nauki stylu, poza repo), arkusze klatek co 2 s `frames/sheet.png`,
pasek ruchu co 0,33 s `LjuB0UjShyM/frames/motion_18.png`, pomiary skryptem `render/ref/arjay/measure.json`.
Kamil 2026-11-16: „zajebiście rysuje szczegółowo, fajnie jak opowiada… zdefiniuj gdzie my jesteśmy słabsi i ulepsz dla longów i shortów”.
Decyzja: `docs/adr/0028-explainer-scene-arjay.md`. Bierzemy mechanikę rysowania i opowiadania, nie grafikę, postać, aplikację autora (devmaxx) ani treść.
Napisów i mowy nie transkrybowałem (YouTube zwrócił 429 na napisy); wszystko o mowie poniżej jest z napisów wtopionych w klatki.

ID: OnzEz_m9Ito, KmALeOL4XLk, Kfg1XeS8o-w, TJWr9AbQb_Q, PNNx9a92QS4, u5NKNWPpLOw, LjuB0UjShyM, Cr69N5pG258, ouF-P31T2O4,
qH2kD_kvhy4, qIS5lNj1b5w, RNn3G01CDQQ, BGUcZNm5nrA, 8z-4eQ9Qbc0, L-dJaClp0Zg.

## Liczby (measure.json, górna połowa kadru, 6 klatek/s)

| miara | wynik |
|---|---|
| układ | 11/15: jasny panel u góry (~50 % wysokości), twarz u dołu; 2/15 przy telewizorze z diagramem; 2/15 inne (skecz, montaż) |
| najdłuższy przestój panelu | mediana 2,3 s (zakres 0,2–7,2 s; 7,2 s tylko TJWr9AbQb_Q) |
| udział klatek z jakąkolwiek zmianą w panelu | mediana 0,48 |
| twarde cięcia | mediana 13,8/min (shorty z panelem: 7–29/min) |

## Jak rysuje (to, co nas wyprzedza)

1. **Konkret zamiast abstrakcji.** Tabela `products` z wierszami „41 Red kettle 3 / 42 Blue mug 5 / 43 Oak tray 8”, ludzie z imionami
   i kolorami (Sam niebieski, Riya pomarańczowa), prawdziwy SQL, prawdziwe liczby („$276 total API bill”, „4 608 requests”). Żadnych
   szarych kresek zamiast tekstu.
2. **Stan zmienia się w tym samym elemencie, na słowo.** Wiersz robi się czerwony z ikoną konfliktu, „version 5” -> „6” w limonkowej
   pigułce, „Save” zmienia kolor, „nie uruchomiono” -> „FAIL”. Widz śledzi jeden obiekt, nie czyta nowej karty.
3. **Kompozycja rośnie i przestawia się.** Karta formularza wchodzi duża; gdy mówi „app”, karta maleje i jedzie w lewo, dochodzi strzałka
   i pudełko App, potem DB. Kadr zawsze wypełniony (element ~70–80 % szerokości panelu), nigdy mały rysunek w pustym polu.
4. **Wymiana kompozycji zamiast tłoku.** W panelu 9:16 naraz 1–3 elementy; poprzednie znikają, gdy wchodzi nowy wątek (formularz ->
   SQL -> wynik „0 rows”).
5. **Kod pisany linia po linii, marker na frazie.** `UPDATE … WHERE id = 42 AND version = 5;` pojawia się linia po linii, limonkowy
   marker rośnie pod „AND version = 5” dokładnie, gdy pada „only if the version is still 5”, pod spodem podpis.
6. **Tagi z linią prowadzącą.** Kolorowa etykieta „Sam: "Blue mug, 350 ml"” z cienką linią do wiersza, którego dotyczy; kursory
   w kolorze osoby.
7. **Wielka liczba jako puenta.** Szeryfowe „0 rows”, „55% got it wrong”, „98%”, „280,000” na pół panelu.
8. **Jedna paleta.** Ciepła biel (#f4f3ee), czarny tusz, jeden limonkowy zakreślacz, czerwony tylko na błąd, małe etykiety mono
   kapitalikami („LATENCY”, „USERS • LIVE”), „example: $12 server” jako uczciwy dopisek przy przykładzie.
9. **Tempo.** Coś w panelu zmienia się co ~0,5–1 s (litera, wiersz, wartość, strzałka); przestój dłuższy niż ~2,3 s rzadko.

## Gdzie jesteśmy słabsi (pomiar na naszej scenie `s_gotowe`, long 2026-11-04, 34–50 s)

| # | u arjay | u nas przed zmianą | zmiana (ten commit) |
|---|---|---|---|
| 1 | element wypełnia ~75 % panelu, kadr rośnie z rysunkiem | okno „Claude Code” ~15 % kadru przez 10 s, kamera `*` kadruje od 0 s cały KOŃCOWY rysunek | `"cam": "grow"`: kamera kadruje tylko to, co jest na ekranie; pierwszy element duży (do `grow_zmax` 1,5), kadr szerzej przy każdym wejściu; scena zawsze cała (NOTES_LOG 50) |
| 2 | zmiana co ~1 s, max ~2,3 s | ~10 s bez zmiany stanu (jedno podświetlenie) | bramka `scene_beat` (long + short, warn): zmiana co <= 2,5 s, liczą się też `set`, `state`, `mark`, słowa, wiersze |
| 3 | prawdziwe wiersze, imiona, liczby | szare kreski `~70` jako domyślne wiersze okna | bramka `scene_concrete` (warn): <= 1/3 wierszy i dymków to `~`; nowy element `table` z prawdziwymi wierszami |
| 4 | wartość zmienia się w miejscu („5” -> „6”) | brak: nowa wartość = nowy element | `"set": [[s, "nowa"]]` na `chip`, `text`, `big`, `stat`; `set_cell` i `state` w `table` (wiersz bad/ok/hl/off) |
| 5 | SQL pisany linia po linii, marker na frazie | `term` pisze tylko jedną komendę, brak kodu z kolorami | `code`: linie pisane 1ch/znak, kolory sql/js/py/sh, `mark: [[s, linia, "fraza"]]` |
| 6 | etykieta osoby z linią do wiersza | brak | `tag` (`to`: punkt albo id, także wiersz `"tabela.1"`, linia do krawędzi pudełka) |
| 7 | wielka szeryfowa liczba | `stat` 140 px bezszeryfowy | `big` (domyślnie 220 px, szeryf) |
| 8 | jasny panel, jeden zakreślacz | tylko ciemne płótno | `"look": "paper"` + ton `lime` |
| 9 | short: 1–3 elementy naraz, pion | ten sam rysunek co w longu skalowany do 0,39 (tekst 22 px, `scene_check` czerwony) | zasada w README i roli motion designera: short = osobny układ w pionie, szer. <= ~940, stare elementy `gone` |

## Gramatyka obrazu (runda 2, 2026-11-16)

Kamil po rundzie 1: „jakość rysunków jest też inna, on bardziej wizualizuje więcej rzeczy, a my tylko napisy, on wizualizuje
procesy myślowe”. Sprawdzone na arkuszach LjuB0UjShyM, OnzEz_m9Ito, qH2kD_kvhy4: każda myśl ma swój rysunek, napis jest dodatkiem.
U nas brakowało kroku „zdanie -> jaki obraz” (rola motion designera go nie miała), więc domyślnie wychodził tekst.

| rodzaj myśli | u arjay (klatka) | u nas teraz |
|---|---|---|
| proces / przyczyna | Server -> 1. db transaction -> 2. read outbox -> worker -> 3. mq, krok zapala się na słowo (qH2kD) | `flow` (`lit`, `packet`) |
| awaria | „server crashes” i X na strzałce, która nie doszła | `flow` `fail` |
| ilość / udział | „144 answers, 1 tile each”, waffle 55 % (OnzEz, LjuB0) | `grid` (`show`, `fill`) |
| mnożenie | 16 x 8 x 4 x 3, siatka rośnie do 144 | `grid` `show` w krokach |
| porównanie | słupki 57 / 45 / 73 %, „asked 61 % -> built 10 %” na osi | `bars` (z `b` = dwie kropki) |
| czas / trwanie | tor open -> editing -> save, „locked the whole time” | `timeline` (`segs`, `head`) |
| wybór / decyzja | quiz A–D, zaznaczona odpowiedź juniorów | `quiz` (`pick`, `reveal`) |
| rzecz / stan | karta „Product #42”, version 5 -> 6, [Save] | `form` (`fields.set`, `button`, `note`) |
| czego nie ma | przekreślone „system prompt, tools, memory” | `strike_at` (było) |

Reguła w `team/roles/motion-designer.md` i README › Scena; bramka `scene_visual` (warn): najwyżej połowa własnych elementów sceny
tylko pisze. Short = każda myśl to nowa pełna kompozycja (`gone` + `cam: grow`), nie dokładanie do jednej sceny (runda 1: tekst malał
z każdym wejściem, bo `grow` oddalał kamerę).

## Zostaje do zrobienia

- Napisy w stylu arjay (szeryf, małe litery, na granicy panelu i twarzy) — osobny system napisów, nie rysowanie.
- Wykres liniowy (linia rosnąca do czerwonej kropki) i histogram p50/p95.
- Przestawianie układu (FLIP: element maleje i jedzie w bok) — teraz „grow” przesuwa kamerę, elementy nie zmieniają miejsca.
- Bramki zaczynają jako `warn` (proporcjonalność: nowa blokada dopiero po incydencie); podnieść na błąd po pierwszym filmie.

## Demo

`render/ref/arjay/_ours/demo/specs.json` (`demo_long`, `demo_short`): nasza scena „Gotowe! Wszystko działa.” przerysowana tym
wzorem (czat -> tag -> tabela testów „nie uruchomiono” -> „0 testów przed Gotowe!” -> `npm test` -> wiersze FAIL -> pieczątka
-> status „gotowe” -> „do poprawy”). Arkusze `short_sheet.png`, `long_sheet.png`. `scene_check`: short 0 kolizji; long 2 ostrzeżenia
czytelności (chip 39 px przy progu 40, układ do zwężenia).

Runda 2: `render/ref/arjay/_ours/demo2/specs.json` (`demo2_short`, `demo2_long`): ta sama historia gramatyką obrazu, każda myśl
osobną kompozycją: proces z pominiętym krokiem testów (`flow`, `fail` na strzałce do „Testy”, „Gotowe!” i tak się zapala) -> quiz
„Co robisz?” -> oś czasu „bez testów: bug u klienta / z testami: fix przed wdrożeniem” -> karta PR (status „gotowe” -> „do poprawy”,
testy -> „2 failed”, merge zablokowany); long dodatkowo siatka 48 testów, 2 czerwone, i „2 z 48”. Arkusze `short_sheet.png`,
`long_sheet.png`; `scene_check`: 0 kolizji. Liczby w demo (48 testów, 2 czerwone) są ilustracją, nie pomiarem.
