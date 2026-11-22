# Wzorzec: długie filmy gadane, Szymon Negacz (rozbiór 2026-11-05)

Źródło: kanał YouTube @SzymonNegacz (WiseBusinessSchool, biznes B2B, sprzedaż, AI w firmie), zakładka „Filmy”, 230 pozycji na liście. Wybrane 10 filmów długich po polsku: 7 najnowszych i 3 najczęściej oglądane z ostatnich 12 miesięcy (05.11.2025-04.11.2026; w tym oknie film `h7aJxwJf3X4` z 221 tys. wyświetleń wypada 3 tygodnie za wcześnie, więc go nie ma). Pliki lokalnie w `render/ref/long/negacz/<id>/` (gitignore `/render`), `yt-dlp` 720p (avc1 + opus), `v.info.json`, napisy automatyczne YouTube `v.pl.vtt` (słowa z czasami). Całość 3,4 GB razem z klatkami roboczymi (limit 8 GB). Bierzemy mechanikę montażu, nie grafikę, maskotkę (brak), markę WiseGroup, studio ani treść autora; w materiale są cudze zdjęcia i klipy stockowe i strony firm: u nas tak samo jak dotąd, tylko lokalnie (ADR-0008).

Uwaga o pobraniu: po ok. 10 pobraniach YouTube zwrócił „Sign in to confirm you're not a bot”. Nie używałem ciasteczek z przeglądarki ani zmiany klienta; ponowiłem po ok. 10 minutach pauzy i przeszło. Wszystkie 10 pobrane.

| # | id | data | czas | wyświetlenia | format | rozdziały |
|---|---|---|---|---|---|---|
| 1 | `2-Nv4bfTtRw` | 04.11.2026 | 44:08 | 4 622 (film z wczoraj) | wywiad (gość + prowadzący) | 9 |
| 2 | `s2ymM30Eh8A` | 28.10.2026 | 24:14 | 13 107 | solo, studio neonowe | 17 |
| 3 | `-_i6TpZtHfY` | 14.10.2026 | 32:47 | 18 499 | solo, studio | 18 |
| 4 | `A49_2fG_6M0` | 07.10.2026 | 44:42 | 21 226 | solo, studio + oprowadzanie po stronach (Velux vs Fakro) | 10 |
| 5 | `s36xTLeEvaI` | 30.09.2026 | 71:46 | 15 209 | wywiad | 8 |
| 6 | `pnUuqmDNiUc` | 23.09.2026 | 22:46 | 16 061 | solo w biurze + nagrania ekranu, 60 fps | 6 |
| 7 | `ipjJvDQQ4ZA` | 16.09.2026 | 36:14 | 37 473 | vlog (auto, wizyta w biurze), 60 fps | 7 |
| 8 | `4AW07yxy3Y4` | 18.03.2026 | 25:21 | **71 009** (top 1) | solo, studio | 10 |
| 9 | `3cKA4WbFohA` | 21.01.2026 | 46:42 | **57 820** (top 2) | solo, studio | 15 |
| 10 | `wE92La-FpZc` | 29.04.2026 | 28:23 | **53 858** (top 3) | solo, studio | 16 |

Mediana wyświetleń wszystkich 230 wylistowanych filmów (lista płaska YouTube, wartości zaokrąglone): **17 458**. Mediana 10 wybranych: 19 863. Filmy 1 i 5 to wywiady (montaż prawie bez grafiki, patrz niżej), 6 i 7 mają inną scenografię niż studio. Logiki grafiki liczę więc głównie z ośmiu filmów solo (`SOLO8` = 2-10 bez wywiadów), a z sześciu filmów w studiu (`2, 3, 4, 8, 9, 10`) tam, gdzie liczy się kadr studia.

## Metoda i ograniczenia (czytaj przed liczbami)

- Cięcia: `select='gt(scene,0.25)'` i `0.1` na klatkach 320 px, całe filmy. Wejścia grafik NIE są cięciami (scena sama zmienia stany), więc cięcia/min zaniżają „ile się dzieje”.
- Układ kadru: 1 klatka/s (480x270) dla całego filmu (22 590 s). Klasyfikacja: detektor twarzy YuNet (ten sam model co `face_track.py`) plus odległość od wzorca kadru studia. Klasy: **W** studio szeroko (mówca, ok. 7,5 % szerokości głowy), **K** ciasny kadr mówcy (głowa ok. 20 %), **C** mówca w kółku nad sceną, **S** brak mówcy (pełnoekranowa scena). Typ sceny: tło płaskie `#363465` = rysunek odręczny (sketch), jasne = strona WWW, krawędzie gęste = stock, ciemny gradient z małą ilością krawędzi = karta tekstowa, reszta = ciemna scena (wykres, licznik, 3D, ciemny zrzut). Ręczna weryfikacja na arkuszach: klasy zgadzały się w ok. 90 % sekund; **błędy**: stockowe twarze bywają zliczone jako K lub C (np. s2y 0:19-0:24), w filmach 6 i 7 „K” obejmuje też twarze kolegów z biura. Rozdzielczość czasu 1 s: przebiegi krótsze niż 2 s liczone tylko w zbiorczych statystykach.
- Przejścia: pełne klatki (25 lub 60 fps) 64x36 szarości, estymator mieszania A/B na ±0,8 s wokół granicy. Rozdzielczość 40 ms; wolny ruch kamery może wyglądać jak „miękkie”.
- OCR kart tekstowych: `tesseract pol` na jednej klatce karty (n = 125 kart, 92 z odczytanymi słowami).
- Obejrzane obrazy: 26 arkuszy kontaktowych (`sheets/A_first90.png`: pierwsze 90 s po 2 klatki/s, 10 filmów, s2y tylko wersja 1 fps; `B_mid_chapter.png`: środek 45 s + okno przy zmianie rozdziału 45 s po 1 klatce/s, 8 filmów; `D_last60.png`: ostatnie 60 s, 8 filmów) i 3 zestawy pełnych klatek w kluczowych momentach (`F1_key`, `F2_keys_multi`, pasek wejścia i wyjścia kółka co 0,08 s). Nie obejrzałem: B ipjJ i s36x, D 2-Nv i s36x. Limit 40 arkuszy zachowany.
- Dźwięk: nie słuchałem, tylko mierzyłem (`ebur128`, `silencedetect -40 dB`, RMS co 50 ms). Wszystko o SFX i muzyce [NIEPEWNE].
- Wyświetlenia zależą od wieku filmu i od tego, że 3 filmy wybrałem właśnie po wyświetleniach (patrz kolumna D macierzy).

## Liczby

| id | cięcia/min (0,25) | mediana ujęcia | p90 ujęcia | cięcia/min (0,1) | słów/min (auto) | cisza ≥0,4 s | głośność (LUFS) |
|---|---|---|---|---|---|---|---|
| `2-Nv` | 3,0 | 13,5 s | 47,5 s | 5,0 | 176 | 3,5 % | -21,2 |
| `s2ym` | 4,3 | 7,8 s | 33,2 s | 5,5 | 155 | 6,9 % | -23,6 |
| `-_i6` | 3,8 | 10,4 s | 35,3 s | 5,2 | 165 | 6,9 % | -23,0 |
| `A49_` | 6,6 | 4,4 s | 22,0 s | 20,2 | 150 | 7,1 % | -21,8 |
| `s36x` | 5,7 | 3,5 s | 30,0 s | 6,0 | 181 | 6,8 % | -25,2 |
| `pnUu` | 3,6 | 7,2 s | 31,1 s | 6,1 | 167 | 4,0 % | -22,7 |
| `ipjJ` | 4,2 | 4,9 s | 29,8 s | 6,6 | 165 | 5,0 % | -23,2 |
| `4AW0` | 5,3 | 7,7 s | 24,2 s | 9,2 | 161 | 4,6 % | -22,7 |
| `3cKA` | 4,4 | 7,6 s | 30,6 s | 9,4 | 165 | 6,2 % | -20,0 |
| `wE92` | 4,8 | 7,8 s | 27,9 s | 7,2 | 162 | 9,6 % | -22,0 |
| **mediana 10** | **4,4** | **7,6 s** | **30,3 s** | **6,6** | **165** | **6,3 %** | **-22,7** |

Wniosek: **bardzo mało twardych cięć** (4-6/min, ujęcie typowo 8 s, p90 30 s). Zmiany obrazu to głównie zmiana kadru i scena, nie cięcie gadającej głowy. Głośność -20 do -25 LUFS jest cicha; to nie jest wzór do kopiowania (u nas -14, `final_check.sh`).

Układ kadru w całym filmie (% czasu; sekundy z klasyfikatora; wywiady i vlog tylko orientacyjnie):

| id | W | K | C (mówca w kółku) | S (sama scena) | scena razem (C+S) | zmian na scenę /min | mediana bloku sceny | odstęp między początkami bloków (mediana) | mediana powrotu mówcy |
|---|---|---|---|---|---|---|---|---|---|
| `s2ym` | 27,2 | 4,5 | 25,2 | 43,2 | 68 % | 1,44 | 26 s | 38,5 s | 11 s |
| `-_i6` | 33,3 | 5,4 | 34,1 | 27,2 | 61 % | 1,22 | 17 s | 44 s | 12 s |
| `A49_` | 16,9 | 4,3 | 23,0 | 55,8 | 79 % | 1,34 | 19 s | 30 s | 4 s |
| `pnUu` | 0,1 | 7,3 | 14,1 | 78,4 | 93 % | 1,71 | 3 s | 7 s | 2 s |
| `ipjJ` | 0 | 20,1 | 0,5 | 79,4 | 80 % | 1,08 | 21 s | 22,5 s | 3,5 s |
| `4AW0` | 46,5 | 6,1 | 7,9 | 39,5 | 47 % | 1,30 | 17 s | 43 s | 13,5 s |
| `3cKA` | 44,0 | 7,3 | 21,8 | 26,9 | 49 % | 1,26 | 14 s | 44 s | 14 s |
| `wE92` | 31,8 | 6,0 | 23,1 | 39,1 | 62 % | 1,44 | 18 s | 38,5 s | 13 s |
| **SOLO8: mediana (IQR)** | | | **22,5 (12,5-23,5)** | **41,5 (36,0-61,5)** | **65 % (58-79)** | **1,32 (1,25-1,44)** | **16 s (7-37), n = 346 bloków** | **38,5 s (28-43)** | **7 s (3-19), n = 349** |

Najważniejsze: jego czas na „osobnym ekranie” (C+S) to ok. 65 %, czyli tyle co u nas (63 %). Różni się **rzadkość i długość skoków**: 1,3 skoku na minutę (co ok. 46 s) wobec naszych 2,9/min (co 21 s); blok sceny trwa mediana 16 s, a w jednej trzeciej tego czasu (C) mówca zostaje widoczny w kółku. W sześciu filmach studia liczba skoków/min mieści się w 1,22-1,44. Najdłuższy odcinek samego mówcy (W+K bez sceny) mediana 74 s (IQR 56-102; pnUu 9 s, ipjJ 141 s).

Opening, pierwsze 60 s (SOLO8): **10-13 zmian typu obrazu** (mediana 11,5), 6-19 cięć `scene>0,25` (mediana 10), udział sceny (C+S) 55-93 % (mediana 85 %). Mówca w pierwszych 60 s pojawia się łącznie na 5-12 s, zwykle zaczyna od szerokiego kadru studia 1-5 s, po czym wchodzi scena.

Dźwięk (wszystko [NIEPEWNE]): ciche ramki (RMS 50 ms poniżej -50 dBFS) to 9,6-16,9 % czasu we wszystkich 10 filmach, więc **nie ma stałego podkładu muzycznego głośniejszego niż ok. -50 dBFS**; pojedyncze impulsy w ciszy 0,5-1,8/min, tylko 5-16 % z nich pada w ±0,4 s od cięcia (szansa 4-8 %), czyli związek z cięciami niepotwierdzony (n = 11-84 na film).

## Oś czasu (po czasie w filmie)

**`s2ymM30Eh8A`** „Dlaczego Twoja firma zarabia coraz mniej” (24:14). Pierwsze 90 s, z arkuszy 1 fps:

| czas | co widać | typ |
|---|---|---|
| 0:00-0:01 | studio szeroko, mówca przy biurku | W |
| 0:01-0:09 | wykres słupkowy zielony/czerwony, etykieta „ZYSK: ...” zmienia wartość 5 razy (1 500 000 -> 1 400 000), liczby przy słupkach | ciemna scena |
| 0:09-0:12, 0:15-0:24 | trzy klipy stock (toast, para z kwiatami, szampan) po 3-9 s | stock |
| 0:12-0:14 | studio szeroko | W |
| 0:25-0:28 | wykres z licznikami (+2 767, -88 90..., -100 000, +3 000 000) | ciemna scena |
| 0:29 | czarna klatka 1 s | black |
| 0:30 | studio szeroko 1 s | W |
| 0:31-0:34 | zrzut własnej listy filmów z napisem „LINK W OPISIE” (karta 3D), potem stół 3D | web / ciemna scena |
| 0:35-0:53 | tło `#363465`, osie i linia wzrostu rysowane cienką pomarańczową kreską, procenty dopisywane; mówca w kółku (prawy górny róg) | sketch + C |
| 0:54-1:07 | stock biuro, tekst cytatu w lewym górnym rogu (od 0:57) | stock |
| 1:08-1:12 | ciasny kadr mówcy (punch-in) | K |
| 1:13-1:14 | studio szeroko | W |
| 1:15-1:23 | sketch z kółkiem | sketch + C |
| 1:24-1:30 | ciemny zrzut strony kanału | ciemna scena |

W ciągu pierwszych 60 s mówca jest widoczny ok. 5 s, a kolejnych zmian obrazu jest 13. Rozdziały (17): np. 12:10 „DRUGA SYTUACJA” (szara pigułka, nad nią tytuł „ŁATANIE PROBLEMÓW ETATAMI” wypisywany słowo po słowie, ciemny gradient, ok. 6 s), potem 12:16-12:28 rysunek odręczny „P -> uśmiech” z kółkiem. Koniec: karta „SPRAWDŹCIE KLUCZOWE METRYKI” 5 s, studio 27 s (w tym punch-in 23:36-23:41), pochylona strona firmy 10 s, studio 4 s, **strona kanału z animowanym kliknięciem „Subskrybuj” 12 s**, koniec w ostatniej klatce bez planszy.

**`4AW07yxy3Y4`** „6 pomysłów na biznes w dobie AI” (25:21, 71 tys.). Pierwsze 90 s: 0:00-0:05,5 studio; **0:06-0:27 animowana scena 3D bez mówcy (kolorowe i żółte bloki rosną w rzędzie, 21 s)**; 0:28-0:29 punch-in; 0:29-0:31 studio; 0:31,5-0:33,5 czarny ekran; 0:33,5-1:00 animowana plansza marki (identyfikator firmowy ze słowem kinetycznym „biznes musi działać jako całość”, 27 s; w `wE92` ta sama plansza jest outro 28:05-28:22); 1:01-1:05 studio; 1:06-1:13 punch-in; 1:13-1:24 sketch z kółkiem i odręcznymi etykietami; 1:25-1:30 ciemna scena „KUPIĆ HALĘ” z rysowaną igłą. Środek: 12:20-12:31 pasek pigułek słów, aktywna podświetla się na niebiesko; 12:38-13:02 karta produktu z licznikiem marży (0 % -> 15 %, drugi produkt 44 % -> 60 %).

## Opis techniczny (jak to działa, zasady pierwsze)

### Przegląd logik jako parametry

| id | logika | wyzwalacz | miejsce (% kadru) | wejście / wyjście | czas na ekranie | częstość | zastępuje | po co (problem widza) |
|---|---|---|---|---|---|---|---|---|
| L1 | rzadkie, długie sceny | początek punktu / rozdziału, liczba, porównanie, przykład | pełny kadr (S) albo scena + kółko (C) | wejście twardym cięciem (79-85 % do W i sketch) albo miękko 0,5 s (68 % do ciemnej sceny), wyjście twardym cięciem | blok mediana 16 s (IQR 7-37) | 1,3 / min (IQR 1,25-1,44) | dłuższe tłumaczenie słowami, tabela w prezentacji | uwaga: nowy obraz co ok. 46 s przy równym 65 % czasu pod grafiką, widz ma czas ją przeczytać |
| L2 | mówca w kółku nad sceną | scena, w której mówca nadal tłumaczy (rysunek odręczny, oprowadzanie po stronie) | kółko o średnicy **24,1 % szerokości** (IQR 21-24,9; 43 % wysokości), środek x 0,846 (IQR 0,836-0,866), y 0,44 (5 z 6 filmów; 1 z 6: 0,24), obwódka niebieska | pojawia się i znika **razem ze sceną**, 1 klatka (twarde cięcie, pasek 12 fps), zero skali i zanikania | cały blok sceny (mediana 23 s przy rysunku) | 0,47 sceny z kółkiem / min | mówca znikający na 20 s | widz widzi, że to on mówi (więź), a obraz jest sceną |
| L3 | rysunek odręczny na płaskim tle | wyliczanie kroków, porównanie dwóch rzeczy, oś / wzrost | tło `#363465` cały kadr, rysunek w lewych 2/3, kółko prawa strona | linia rysowana stopniowo przez cały blok (kreska cienka, pomarańczowa lub zielona, krój pisma ręcznego) | mediana 19 s (IQR 11-37; ≥6 s: 23 s) | 0,47 / min (IQR 0,13-0,55) | słowa na kartach, listy punktowane | czytanie zastępuje obserwowanie, rysunek rośnie w tempie mowy |
| L4 | początek rozdziału = zmiana sceny | start rozdziału (80 z 106 rozdziałów ma scenę nie-mówcę w oknie -3..+10 s) | karta ciemna, tytuł na środku, pigułka 2 słowa nad nim („DRUGA SYTUACJA”) | tytuł wypisywany słowo po słowie, bez wipe | mediana karty tekstowej 4 s (IQR 2-7) | 0,41 / min (kart w ogóle) | plansza z numerem | orientacja: „gdzie jestem w liście” |
| L5 | ciasny kadr mówcy (punch-in jako cięcie) | podkreślenie zdania, przejście do puenty, pytanie | głowa 20 % szerokości zamiast 7,5 % (×2,67; IQR per film 2,66-3,01) | twarde cięcie, brak rampy | mediana 4 s (IQR 2-6) | 0,73 / min (IQR 0,62-0,92) | wolny najazd | akcent bez grafiki, odświeża kadr stałego ujęcia |
| L6 | szeroki kadr studia bez nakładek | wszystko inne | mówca ok. 7,5 % szerokości głowy, 0 nakładek obok głowy | cięcie do i ze sceny | mediana 9 s (IQR 5-19); najdłużej 74 s (IQR 56-102) | 1,6 / min | grafika obok głowy | kontekst „rozmowy”, odpoczynek od grafiki |
| L7 | przejścia: twardo do mówcy, miękko do grafiki | zmiana typu | cały kadr | do W 79 % twardo (240/305), do sketch 85 % (81/95); do ciemnej sceny mediana 480 ms (IQR 40-1120), do stocku 750 ms, do strony WWW 560 ms | 0-1,4 s | 4,9 zmian typu / min | blur, glitch, whoosh (w filmach solo nie wykryłem) | płynne wejście bez pustego ekranu |
| L8 | otwarcie: zimny start sceną | początek filmu | W 0-5 s, potem scena i ok. 11 zmian w 60 s | cięcia i sceny | 85 % pierwszej minuty to scena | 11,5 zmian / 60 s | wstęp „cześć, jestem...” | trzymanie uwagi zanim padnie pierwsze zdanie argumentu |
| L9 | CTA: pochylona karta strony / filmu w ostatnich 60 s | zdanie z linkiem lub ofertą | karta 3D w perspektywie, pełny kadr | wjazd z obrotem, bez kółka | 7-17 s, 11 zdarzeń | 7 z 8 filmów solo | plansza końcowa | widz widzi, gdzie kliknąć |
| L10 | brak napisów w filmach solo | - | - | - | - | 0 napisów w 8 filmach solo | napisy wypalone | film oglądany z dźwiękiem, ekran wolny |

Poniżej szczegóły z dowodami.

### L1, L6, L8: rytm sceny i mówcy
Mówca w studiu jest w trzech stanach: szeroki (W, głowa ok. 7,5 % szerokości), ciasny (K, ok. 20 %, tło nieostre, kolor rozjaśniony), i w kółku nad sceną (C). Cała grafika to **pełny kadr** (S) albo scena z kółkiem (C); **żadnych nakładek obok głowy w kadrze szerokim**: w pięciu filmach 0 z ok. 3 500 sekund W ma nakładkę >12 % kadru po bokach (jeden film `wE92` zgłosił 88 s, na arkuszach to pulsowanie kolorów neonu studia, nie grafika). Skoki na scenę są rzadkie (1,3/min), ale blok trwa średnio 16 s i w nim obraz się rusza (rysunek rośnie, licznik liczy, słupki rosną), więc „ilość zdarzeń na minutę” jest wysoka mimo rzadkich skoków (zmian typu 4,9/min, w tym W <-> K).
Otwarcie to zimny start: pierwsze 1-5 s studio, potem scena. Przykłady: `-_i6` (od 0:02 licznik „1 300 firm” rośnie 0 -> 1 300 w 8 s, potem 40 s scen bez mówcy), `4AW0` (21 s bloków 3D), `3cKA` (kółko z awatarem „Nowoczesny handlowiec B2B”, oś lat 2006-2026, słupki). W `A49_` otwarcie to **zapowiedź z fragmentów odcinka** z paskiem „W DZISIEJSZYM ODCINKU:” u dołu (pogrubiony napis wersalikami, nad nim mała linia napisów z fragmentu); 0:00-0:29.

### L2: kółko
Mierzone 78 razy w 6 filmach (Hough na klatce środkowej każdego bloku): średnica 0,241 szerokości, per film 0,209-0,252; środek poziomo 0,846 (0,836-0,866), pionowo 0,44 w pięciu filmach (0,43-0,50) i 0,24 w jednym (`s2ym`: prawy górny róg). Głowa w kółku: ramka twarzy YuNet (brew-podbródek) = **0,327 średnicy** (IQR 0,317-0,339, n = 1 636 klatek, 6 filmów, per film 0,31-0,37), czyli głowa z włosami ok. 47 % średnicy: widać też ramiona i mikrofon, oczy mniej więcej na środku koła. Obwódka niebieska z gradientem, bez cienia i bez poświaty. Wejście i wyjście: twarde cięcie razem ze sceną (pasek 12 fps na `s2ym` 35,2 -> 35,3 i 53,7 -> 53,8; automat: mediana 0,08 s, ale IQR 0-1,07 s, n = 74 w 5 filmach, bo twarz w kółku się porusza). Kółko widać prawie wyłącznie przy rysunku odręcznym (74 z 87 bloków sketch ≥6 s ma kółko ≥60 % czasu) i przy oprowadzaniu po stronach (`A49_`). Przy wykresach, licznikach i kartach tytułowych kółka nie ma.

### L3: rysunek odręczny
Płaskie tło `#363465` (RGB 54, 52, 101), cienkie linie rysowane w czasie (oś, strzałka, okrąg, wykres „P -> uśmiech”, dopisywane etykiety „PROBLEMY”, „1 FILTR: PIĘKNOŚĆ / 2 FILTR: PRZEWAGA / 3 FILTR: KLIENT” w kroju pisma ręcznego, kolor żółty lub zielony kredowy). Jeden blok trwa często 20-60 s, np. `s2ym` 0:35-0:53 (19 s), 1:31-2:19 (49 s), `-_i6` 16:01-16:45 (45 s). Zawsze z kółkiem mówcy. To odpowiada skardze Kamila „animowane rysunki zamiast słów”.

### L4: rozdziały i karty tekstowe
Rozdziały YouTube w opisie: 6-18 na film. W oknie -3..+10 s od początku rozdziału jest scena inna niż mówca w 80 z 106 rozdziałów (75 %; per film: 0,43-1,0, mediana 0,80, IQR 0,67-0,83). Karta tytułowa z pigułką porządkową („PIERWSZA SYTUACJA”, „DRUGIE ROZWIĄZANIE”, „RADA NR 2”) potwierdzona OCR w `s2ym` (12 z 16 rozdziałów) i obejrzana na arkuszach w `3cKA` i `wE92` (filmy z numerowaną listą); w pozostałych filmach tytułem rozdziału bywa wykres, licznik albo rysunek. OCR 92 kart: mediana 3 słowa (IQR 2-5), czas na ekranie mediana 4 s (IQR 2-7), czyli **ok. 1,5 s na słowo** (czytanie ok. 0,3-0,5 s na słowo) przy minimum 2 s. Tekst na karcie jest wypisywany przez ok. 1-3 s słowo po słowie; mały szary, wersaliki, ok. 3-4 % wysokości kadru dla tytułu i ok. 1,5 % dla zdania pod nim w `wE92` 9:26-9:29. Ciemne tło: gradient granat-turkus-fiolet, powoli pływające plamy.

### L5: punch-in
K to **drugie, ciaśniejsze ujęcie** (prawdopodobnie przycięcie 4K, tło nieostre i inny odcień; nie rozstrzygam) o szerokości głowy 0,20 wobec 0,075 (×2,67; per film 2,61-3,57, n = 65-204 klatek na film). Wejście i wyjście twardym cięciem. Mediana 4 s, 0,73/min. W kadrze W nie ma wolnego najazdu (szerokość głowy stała). To odwrotność naszej logiki rampy 0,3 s do 1,38.

### L7: przejścia
Twarde cięcie do mówcy (W) w 79 % wejść i do rysunku w 85 %. Do ciemnej sceny 68 % wejść miękkich (mediana 480 ms, IQR 40-1120), do kart WWW 70 % miękkich (560 ms), do stocku 79 % miękkich (750 ms): to przenikanie, nie przez czerń (czarna klatka pojawia się tylko 7 razy w 7 filmach, 1-2 s, np. między zapowiedzią a identyfikatorem). Glitchy i rozmycie: w filmach solo nie wykryłem; w wywiadach jedno przejście z cyfrowym glitchem (`2-Nv` 0:09,5 i 0:25,5, `s36x` 0:30,5 i 0:49) przy wejściu z zapowiedzi do rozmowy.

### L9: koniec i CTA
Ostatnie 60 s: w siedmiu z ośmiu filmów solo jest pochylona karta strony firmy, kanału (z kliknięciem „Subskrybuj”) albo innego filmu (7-17 s, 11 zdarzeń); film kończy się planem mówcy (14-35 s, ipjJ 141 s) bez planszy końcowej; wyjątki: `s2ym` kończy się stroną kanału, `wE92` outro-identyfikatorem marki 25 s, `A49_` cytuje w napisie komentarz widza i kończy się na mówcy.

### Zagadnienia wprost z pytań Kamila

| skarga Kamila (film v2) | co robi Negacz (dowód) | wniosek |
|---|---|---|
| za dużo skoków na osobny ekran (u nas co 21 s, 63 %) | tyle samo czasu pod sceną (65 %, IQR 58-79), ale **co 46 s, 1,3 skoku/min**, blok mediana 16 s, 1/3 czasu sceny z mówcą w kółku | zmniejszyć liczbę skoków, nie udział; kółko w scenach rysunkowych i oprowadzających |
| elementy znikają, zanim da się je przeczytać | karta tekstowa mediana 4 s dla 3 słów (1,5 s/słowo, min 2 s); rysunek rośnie w tempie mowy 20-60 s | minimum czasu na ekranie liczone ze słów (np. 1,2 s/słowo, min 2,5 s) |
| memy jako naklejki obok niego | **brak danych**: w filmach solo 0 nakładek obok głowy w szerokim kadrze; memy pełnoekranowe tylko w stocku (n = 78 klipów, bez postaci wyciętych) | z tego kanału nie wynika nic o naklejkach; zostaje `sticker` wg `REF-shorts-memes.md` |
| animowane rysunki zamiast słów | tak: L3, rysunek odręczny, 101 bloków, 8 filmów | potwierdzone |
| PiP źle skadrowany | kółko 24 % szerokości, głowa ok. 47 % średnicy z ramionami, środek 0,85/0,44 | porównać z naszym oknem 600 px (31 % szerokości, wypełnienie 0,62, prawy dół, zaokrąglony kwadrat) |
| tekst za głową nieczytelny | **brak danych**: w żadnym filmie nie ma tekstu za głową; tekst obok głowy tylko w otwarciach wywiadów (n = 2 filmy): połowa kadru na słowa, głowa przy krawędzi, napis na środku drugiej połowy | patrz „za mało danych” |

## Co mamy, czego nie mamy

| technika | w nim | mamy? | uwaga |
|---|---|---|---|
| rzadkie skoki na scenę, długie bloki | 1,3/min, 16 s | **częściowo**: `scene`, `slide`, `web` pełny kadr; brak limitu skoków na minutę, `long.graphics ≥4/min` zachęca do skoków | dodać metrykę `screen_switches_per_min` (cel ≤1,5) obok `graphics_per_min` |
| kółko mówcy nad sceną | 24 %, środek x 0,85 y 0,44 | **częściowo**: `PIP` (zaokrąglony kwadrat 600 px prawy dół), `CORNER` koło tylko w 9:16 | wariant koła w 16:9 dla scen z `scene` |
| rysunek odręczny na płaskim tle | 101 bloków | **częściowo**: `scene_lib.mjs` (sceny), brak pisma odręcznego i linii rysowanej | nowy typ sceny `sketch` |
| karta rozdziału: pigułka + tytuł słowo po słowie | 125 kart | **tak**: `chap` | zmiana: tytuł wypisywany słowo po słowie, czas liczony ze słów |
| punch-in jako twarde cięcie ×2,7, 4 s | 0,73/min | **częściowo**: `beats`/`beatfx` rampa do 1,38 | tryb `jump_zoom_long` (patrz `REF-shorts-zackshutt.md`) |
| dwa kadry mówcy (szeroki + ciasny), studio | 466 + 212 przebiegów | **tak**: `punch`, `zoom_every_cut` | - |
| zimny start sceną | 11,5 zmian / 60 s | **tak**: `long.opening ≥8` | próg 8 zgadza się z niższym kwartylem |
| pochylona karta CTA | 11 zdarzeń / 7 filmów | **częściowo**: `web` | tilt w perspektywie jako opcja `web.tilt` |
| zapowiedź z fragmentów + pasek „W DZISIEJSZYM ODCINKU” | 1 film z 10 | nie | za mało danych (n = 1) |
| wywiad: połowa kadru na słowa kinetyczne | 2 filmy | nie | za mało danych (n = 2) |
| brak napisów w long solo | 0/8 | **zgodne** (long bez napisów u nas) | - |
| brak stałej muzyki, cisza -50 dB 10-17 % | 10/10 [NIEPEWNE] | **nie zgodne**: `music_duck`, nowa muzyka per film (Kamil 4.11) | nie kopiować, wygrywa reguła Kamila |
| głośność -22,7 LUFS | 10/10 | nie zgodne (-14) | nie kopiować |

## Wystarczalność danych

Zasada (Kamil): twierdzenie o częstości/występowaniu wymaga ≥5 z 10 filmów; parametr czasu/rozmiaru/miejsca wymaga ≥20 zdarzeń w ≥4 filmach; poniżej: „za mało danych”. IQR = rozstęp ćwiartek. n zdarzeń liczone na kliknięciach klasyfikatora 1 s (patrz Metoda), o ile nie zaznaczono „ręcznie”.

| logika | parametr | n zdarzeń | n filmów | mediana | IQR | werdykt |
|---|---|---|---|---|---|---|
| L1 skoki na scenę | częstość (bloków/min na film) | 346 bloków | 8 z 8 solo (6 studio: 1,22-1,44) | 1,32 | 1,25-1,44 | **wystarcza** |
| L1 | czas bloku | 346 | 8 | 16 s | 7-37 s | **wystarcza** |
| L1 | powrót mówcy | 349 | 8 | 7 s | 3-19 s | **wystarcza** |
| L1 | udział czasu pod sceną | 8 filmów | 8 | 65 % | 58-79 % | **wystarcza** (prewalencja) |
| L2 kółko | prewalencja | 78 | 7 z 10 | - | - | **wystarcza** |
| L2 | średnica (% szerokości) | 78 | 6 | 24,1 % | 21,0-24,9 % | **wystarcza** |
| L2 | środek x | 78 | 6 | 0,846 | 0,836-0,866 | **wystarcza** |
| L2 | środek y | 78 | 6 | 0,442 | 0,438-0,442 (ale s2ym 0,24: 1 z 6) | wystarcza, z zastrzeżeniem |
| L2 | wielkość głowy (ramka twarzy / średnica) | 1 636 klatek | 6 | 0,327 | 0,317-0,339 | **wystarcza** |
| L2 | wejście / wyjście (czas) | 74 (automat), 2 ręcznie na pasku 12 fps | 5 | 0,08 s | 0-1,07 s | **słabe**: automat nieostry, dowód wizualny n = 2; werdykt „twarde cięcie z sceną”, nie standaryzować czasu |
| L3 rysunek odręczny | prewalencja | 101 | 8 z 10 | - | - | **wystarcza** |
| L3 | czas bloku | 101 | 8 | 19 s (≥6 s: 23 s) | 11-37 s (14-40 s) | **wystarcza** |
| L3 | pismo odręczne (krój, kolor, tempo) | ręcznie ok. 10 | 5 | - | - | za mało danych (n≈10 ręcznie) |
| L4 początek rozdziału = scena | udział rozdziałów | 106 rozdziałów | 10 | 0,80 | 0,67-0,83 | **wystarcza** |
| L4 | karta z pigułką porządkową | 32 (s2ym 12, 3cKA 10, wE92 10) | **3** | - | - | **za mało danych (3 z 10 filmów)**: nie uogólniać; reguła tylko dla filmów z listą numerowaną |
| L4 | czas karty tekstowej | 125 | 8 | 4 s | 2-7 s | **wystarcza** |
| L4 | liczba słów na karcie (OCR) | 92 | 8 | 3 | 2-5 | **wystarcza** |
| L4 | czas na słowo | 92 | 8 | 1,5 s | 0,8-2,7 s (liczone z `len`/`words`) | **wystarcza** |
| L5 punch-in | częstość / min | 212 | 8 | 0,73 | 0,62-0,92 | **wystarcza** |
| L5 | czas | 212 | 8 | 4 s | 2-6 s | **wystarcza** |
| L5 | skala (szerokość głowy K/W) | 6 filmów, 65-204 klatek K | 6 | ×2,67 | 2,66-3,01 | **wystarcza** (per film n = 6; zdarzeń ≥20) |
| L6 szeroki kadr bez nakładek | brak nakładek | ok. 3 500 s W | 6 studio | 0 nakładek w 5 filmach | - | **wystarcza** (prewalencja) |
| L7 przejścia | twarde do W | 305 | 6 | 40 ms (79 % ≤2 klatki) | 40-40 ms | **wystarcza** |
| L7 | miękkie do ciemnej sceny | 341 | 8 | 480 ms | 40-1120 ms | **wystarcza**, rozrzut duży |
| L7 | miękkie do stocku / WWW | 81 / 142 | 8 / 8 | 750 / 560 ms | 280-1360 / 40-1025 | **wystarcza**, rozrzut duży |
| L8 otwarcie | zmian / 60 s | 8 filmów | 8 | 11,5 | 11-12 | prewalencja **wystarcza**; parametr czasu: n = 8 <20, nie liczony per zdarzenie |
| L9 CTA karta pochylona | prewalencja | 11 | 7 z 8 solo | - | - | **wystarcza** (≥5 filmów) |
| L9 | czas, rozmiar, tilt | 11 ręcznie | 7 | ok. 9 s | ok. 7-12 s | **za mało danych (n = 11 <20)** |
| L10 brak napisów | prewalencja | 8 filmów | 8 | 0 | - | **wystarcza** |
| wywiad: połowa kadru na słowa kinetyczne | wszystkie | ok. 21 fraz | **2** | 1,25 s / fraza | - | **za mało danych (n = 2 filmy)** |
| naklejka / mem obok głowy | wszystkie | 0 | 0 | - | - | **brak danych**: nie wynika z tego kanału |
| liczniki liczbowe (0 -> 15 %) | wszystkie | ok. 9 ręcznie | 6 | - | - | **za mało danych (n = 9 <20)** |
| tekst na stocku (cytat, czerwony napis) | wszystkie | ok. 6 ręcznie | 4 | - | - | **za mało danych (n = 6)** |
| czarna klatka 1-2 s | czas | 7 | 7 | 2 s | 2-2,5 | **za mało danych (n = 7)** |
| zapowiedź z paskiem „W DZISIEJSZYM ODCINKU” | wszystkie | 1 | 1 | - | - | **za mało danych (n = 1)**: nie liczyć |
| ścieżka dźwiękowa: brak podkładu | prewalencja | 10 | 10 | cisza <-50 dB 9,6-16,9 % | - | wystarcza, ale [NIEPEWNE] (pomiar, nie odsłuch) |

Rzadkich logik (L9 parametry, wywiad, liczniki, tekst na stocku, czarna klatka, zapowiedź) nie dosamplowałem: próbkowanie dodatkowymi arkuszami nie podniosłoby n ponad 20 w ≥4 filmach bez pobrania kolejnych filmów, a to wykraczało poza zlecenie. Odnotowane w „Otwarte decyzje”.

## Macierz logik

Punktacja: **A** rozpowszechnienie = w ilu z 10 filmów występuje (n/10; 8/10 oznacza „we wszystkich filmach solo”). **B** spójność 0-3: 3 gdy IQR/mediana między filmami <0,25, 2 <0,5, 1 <1, 0 powyżej. **C** zgodność źródeł 0-2: ile innych źródeł (REF-shorts-*.md, `render/ref/research/teardowns.md`, `RESEARCH.md`, `grammar.json`/`checklist.json`) potwierdza. **D** sygnał wyświetleń: znak +/0/-, informacyjnie, **nie punktowany** (n = 10, 3 filmy wybrane po wyświetleniach, wiek filmu myli, więc to słaby dowód). **E** reguły Kamila (ZASADY, jego skargi z 4-5.11): TAK wzmacnia, NIE wyklucza lub wygrywa nad logiką, 0 brak wpływu. Suma = A + B + C; E rozstrzyga remisy i konflikty.

| # | logika Negacza | A | B | C | suma | D | E | co mamy | werdykt: która jest silniejsza |
|---|---|---|---|---|---|---|---|---|---|
| M1 | zimny start sceną, 11-12 zmian w 60 s | 8 | 3 | 2 (`long.opening`, Jeff Su 38 s bez twarzy) | **13** | 0 | TAK (Kamil 4.11 „za mało bajerów”) | `long.opening ≥8` | **oba zgodne**: jego mediana 11,5 > nasz próg 8; podnieść próg do 10 |
| M2 | rzadkie, długie sceny (1,3/min, 16 s) | 8 | 3 | 1 (Jeff Su: po 1. minucie 6-7 cięć/min, ruch w scenie; zanegowane: `long.graphics ≥4/min`) | **12** | 0 | TAK (skarga „za dużo skoków”) | skoki co 21 s | **jego logika wygrywa** nad naszym `graphics ≥4/min` w tej części; rozdzielić metryki (skoki vs zdarzenia w scenie) |
| M3 | początek rozdziału = nowa scena (karta, rysunek, wykres) | 7 | 3 | 2 (`long.chapters`, Jeff Su 3,4 s karta) | **12** | 0 | TAK („wejście na ekranie”) | `chap` | **zgodne**; dodać: czas karty ze słów |
| M4 | mówca w kółku nad sceną rysunkową, 24 %, środek 0,85/0,44 | 7 | 3 | 2 (ZASADY „kółko”, Jeff Su PiP 20-22 %) | **12** | 0 | TAK („PiP źle skadrowany”) | okno 31 %, kółko tylko 9:16 | **jego wymiary i głowa 47 % średnicy** zamiast okna 600 px z wypełnieniem 0,62 |
| M5 | punch-in jako cięcie ×2,7, 4 s, 0,73/min | 8 | 2 | 2 (Zack: cięcie ×1,6, Jeff 3-4/min: zgodne w mechanice, nie w częstości) | **12** | 0 | TAK („pominąłeś zoomy”), ale liczba nie ustalona | `punch` ramp 1,38, ≥2/min | **mechanika (cięcie)** jego; **częstość: konflikt** (0,73 vs 2-4); decyzja Kamila |
| M6 | przejścia: twardo do mówcy, miękko 0,5 s do scen, nigdy przez czerń | 8 | 2 | 1 (ZASADY „bez zanikania”, `REF-zackshutt` twarde cięcia) | **11** | 0 | TAK („zero klatek gołej twarzy”) | `no_fade_*` | **zgodne**, dodać miękkie wejście 0,5 s |
| M7 | rysunek odręczny na płaskim tle | 8 | 1 | 1 (Jeff Su diagram stan po stanie) | **10** | 0 | TAK („animowane rysunki zamiast słów”) | `scene` bez pisma | **jego**; nowy typ `sketch` |
| M8 | pochylona karta CTA w ostatnich 60 s | 7 | 1 | 1 (`long.end`, `REF-zackshutt` CTA) | **9** | 0 | 0 (Kamil: `long.end` karta „co dalej”) | `end` | konflikt częściowy: jego koniec bez planszy; decyzja Kamila |
| M9 | szeroki kadr bez nakładek obok głowy | 6 | 3 | 0 | **9** | 0 | NIE (Kamil chce naklejki obok głowy) | `sticker`, `float` | **wygrywa E**: naklejka obok głowy zostaje; Negacz nie dostarcza danych |
| M10 | brak napisów w long solo | 8 | 3 | 0 | **11** | 0 | 0 | brak w long | zgodne |
| M11 | brak stałego podkładu muzycznego, -22,7 LUFS | 10 | 2 | 1 (Zack [NIEPEWNE]) | **13** | 0 | NIE („co filmik nowa muzyczka”, cel -14) | podkład, ducking | **wygrywa E**, nie kopiować |
| M12 | karta rozdziału z pigułką porządkową | 3 | - | 1 | 4 | 0 | TAK | `chap` | za mało danych (3/10): tylko dla list numerowanych |
| M13 | połowa kadru na słowa kinetyczne (wywiady) | 2 | - | 0 | 2 | 0 | 0 | brak | za mało danych (n = 2) |

D szczegóły (informacyjnie): sceny pod grafiką ≥60 % czasu (6 filmów: `s2ym`, `-_i6`, `A49_`, `pnUu`, `ipjJ`, `wE92`): mediana wyświetleń 19 863; <60 % (4 filmy: `2-Nv`, `s36x`, `4AW0`, `3cKA`): 36 515. Kółko ≥20 % czasu (5 filmów: `s2ym`, `-_i6`, `A49_`, `3cKA`, `wE92`): 21 226; poniżej (5 filmów): 16 061. **Znak niejednoznaczny, n = 10, trzy najpopularniejsze filmy wybrane po wyświetleniach (konstrukcja próby), film z 04.11 ma 1 dzień. Nie używam tego do decyzji.**

## Kolejność wdrożenia

Tylko logiki, które przeszły „Wystarczalność danych”. Koszt: S ≈ pół dnia, M ≈ 1-2 dni, L ≈ 3+ dni.

**P1 (mała zmiana, duży wpływ na skargi Kamila):**
1. Metryka `screen_switches_per_min` w `film_check.py`/`checklist.json` (cel ≤1,5/min, mediana bloku ≥10 s), osobno od `graphics_per_min`; krytyk grupuje sąsiednie karty w jeden blok sceny. Koszt S. Rozwiązuje skargę „za dużo skoków”.
2. Czas na ekranie karty tekstowej liczony ze słów: ≥1,2 s/słowo, minimum 2,5 s (jego 1,5 s/słowo, min 2 s). Koszt S. Rozwiązuje „znikają zanim można przeczytać”.
3. Okno PiP w 16:9 jako koło 24 % szerokości, środek x 0,85 y 0,44 (opcjonalnie prawy górny róg), głowa ramka twarzy 0,33 średnicy, ramiona widoczne, wejście i wyjście twardym cięciem ze sceną. Koszt M (`pip_assets.mjs`, `gfx_types.pip_window` `fill` 0,45). Rozwiązuje „PiP źle skadrowany”.
4. `long.opening`: podnieść próg z 8 do 10. Koszt S.

**P2:**
5. Nowy typ sceny `sketch` (tło `#363465`, linie rysowane w czasie, pismo odręczne, kółko mówcy). Koszt L. Rozwiązuje „rysunki zamiast słów”; 101 bloków w 8 filmach, mediana 19 s.
6. Miękkie wejście 0,5 s (przenikanie, bez czerni) do ciemnych scen, stocku i kart WWW, twarde do mówcy. Koszt S-M. Zgodne z ZASADY (bez klatki gołej twarzy).
7. Tryb `jump_zoom_long` (twarde cięcie ×2,7 na 4 s) obok rampy; częstość wg decyzji Kamila. Koszt M.
8. Karta rozdziału: tytuł słowo po słowie, czas z liczby słów. Koszt S-M.

**P3 / decyzja zanim cokolwiek:** pochylona karta CTA (parametry za mało danych, n = 11), liczniki liczbowe, pigułka porządkowa tylko w listach numerowanych (3 filmy), napisy kinetyczne obok głowy w wywiadach (2 filmy), tekst na stocku. Nie budować przed decyzją i danymi.

**Nie kopiować (E wygrywa):** brak muzyki, głośność -22,7 LUFS, brak nakładek obok głowy (Kamil chce naklejki).

## Otwarte decyzje dla Kamila

1. Punch-in w długim filmie: jego 0,73/min (cięcie ×2,7, 4 s) czy nasz gate ≥2/min? W Twojej skardze („pominąłeś zoomy”) nie ma liczby.
2. Liczba skoków: zgoda na cel ≤1,5/min przy zachowaniu ok. 60-65 % czasu pod sceną? To zmienia sens `long.graphics ≥4/min`.
3. Koniec filmu: Negacz kończy na mówcy (14-35 s) po kartach CTA; `long.end` wymaga karty „co dalej”. Zostawić kartę czy iść jego drogą?
4. Kółko: zgoda na koło 24 % w środku-prawo (y 0,44) zamiast prawego dołu? Jego `s2ym` ma prawy górny róg.
5. Rysunek odręczny: czy robimy własny krój pisma ręcznego i kredową kreskę (nie kopiujemy jego grafiki)?
6. Wywiady (2 z 10 filmów) mają połowę kadru ze słowami przy głowie: czy to rozważamy jako odpowiedź na „tekst za głową nieczytelny”? Dane za słabe (n = 2).
7. Czy dobrać dalsze filmy (inne kanały lub inne filmy tego), żeby zwiększyć n dla CTA, liczników i tekstu na stocku?

## Czego nie zmierzyłem

- Dźwięk: bez odsłuchu; podkład, SFX i whoosh [NIEPEWNE].
- Dokładny czas wejścia i wyjścia grafik krótszy niż 40 ms; krój pisma i kolory (rozdzielczość 720p i JPEG klatek).
- Liczba „zdarzeń w scenie” (licznik, rysowana linia) na minutę: nie da się wiarygodnie wyliczyć klatkami 1 fps, tylko ręcznie (ok. 9 liczników w 6 filmach).
- Naklejki, memy wycięte i grafiki obok głowy w kadrze szerokim: nie wystąpiły w tym kanale, więc nie ma n.
- Skuteczność (retencja): brak dostępu do retencji; D jest tylko wyświetleniami.
- Filmy 1 i 5 (wywiady) i 7 (vlog) nie dają porównywalnych statystyk układu; wyłączone z `SOLO8` tam, gdzie zaznaczono.
