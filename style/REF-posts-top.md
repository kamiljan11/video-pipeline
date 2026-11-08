# REF: posty LinkedIn najlepszych twórców AI / tech / biznes (mechanika, nie treść)

Data badania: 2026-11-05. Laptop Linux. Cel: poprawić generator postów (`render/montaz/2026-11-04/work/build_posts_v2.py`). Werdykt Kamila o v2: "realnie nic dużo nie mówią, są niekompletne". Reguła Kamila (E): GRAFIKA sama, bez tekstu posta, niesie kompletny, zrozumiały i ciekawy przekaz; tekst tylko dopełnia.

Zasady tego dokumentu: tylko mechanika (format, struktura, liczby); żadnej kopii cudzej grafiki, tekstu ani brandingu. Nic nie logowałem, żadnych danych dostępowych. Wszystko, czego nie widziałem, ma znacznik [NIEPEWNE]. W proponowanych tekstach postów brak długich myślników.

Legenda tagów: [POMIAR] = policzone przeze mnie na widzianych postach; [ZRODLO] = liczba z cytowanego źródła; [KODOWANIE] = ręczna klasyfikacja jednego kodera (ja), bez drugiej oceny; [PROP] = moja propozycja; [NIEPEWNE] = brak pokrycia.

## Ograniczenia próby (czytaj najpierw)

1. Posty czytałem z publicznego widoku gościa (bez logowania): widać tekst, liczbę reakcji i komentarzy, pierwszy obraz. NIE widać wyświetleń (impressions), czasu czytania ani slajdów PDF. Sygnał skuteczności = reakcje znormalizowane (reakcje posta / mediana reakcji tego twórcy), czyli słaby proxy.
2. Wiek postów: 47 z 94 ma ok. 3 lat, 21 ma 2 lata, 16 ma 4 lata, tylko 10 ma 1 rok lub mniej (2025/2026). Mechanika grafik jest stabilna, ale algorytm się zmienił; fakty o algorytmie biorę z osobnej sekcji z datami, nie z wieku postów.
3. Wyszukiwarka dała posty "popularne w indeksie", więc jest skłonność do sukcesów (survivorship). Normalizacja do mediany twórcy nie usuwa tego w pełni.
4. Rozpoznanie formatu z DOM gościa: wideo, obraz, PDF wykryte; posty bez wykrytych mediów oznaczam "bez mediów w widoku" (u Justina Welsha 7 z 9 może to być niewykryty obraz, [NIEPEWNE]).
5. OCR (tesseract eng+pol, pewność >= 60) ZANIŻA liczbę słów na grafice (kolorowy, mały tekst ginie). Traktuj jako dolną granicę.

## Źródła

Źródła ludzkie i raporty (S), post-poziom (P), pomiary własne (M).

| ID | Źródło | Typ / data | Co z niego biorę |
|---|---|---|---|
| S1 | LinkedIn Engineering Blog, "Leveraging Dwell Time to Improve Member Experiences on the LinkedIn Feed", https://www.linkedin.com/blog/engineering/feed/leveraging-dwell-time-to-improve-member-experiences-on-the-linkedin-feed | pierwotne, 2024-10-01 | dwell time jako sygnał pozytywny; progi liczone z danych, aktualizowane codziennie |
| S2 | Socialinsider, 2026 LinkedIn Benchmarks, https://www.socialinsider.io/social-media-benchmarks/linkedin | vendor, 2026-03-16 | stopy zaangażowania wg formatu (strony firmowe 1K-1M obserwujących, 2,45 mln postów wg strony, formuła: reakcje+komentarze+udostępnienia / wyświetlenia); kwartał Q3 2026 na stronie jest niespójny z datą publikacji |
| S3 | Ordinal, "LinkedIn formatting" https://www.tryordinal.com/blog/linkedin-formatting | vendor, bez daty (powiązane wpisy 2026-10-28) | mediany zaangażowania wg formatu (n podane), U-krzywa długości, okno pierwszych minut; źródło i okres częściowo niepodane |
| S4 | Ordinal, "LinkedIn link penalty study" https://www.tryordinal.com/blog/linkedin-link-penalty-study | vendor, bez daty | kara za link: strony firmowe tak, profile osobiste prawie nie; cytuje LinkPost (358 tys. postów) i van der Blom (dane niepubliczne) |
| S5 | MagicPost, "Top LinkedIn creators", https://magicpost.in/nl/blog/top-linkedin-creators | vendor, aktualizacja 2026-05-05 (32 000 postów, 61 twórców, autor ujawnia doradcę) | obserwujący i wzorce haków kilku twórców (Welsh 853k, Hassid 832k, Hormozi 949k, Acosta, Herubel) |
| S6 | getchime na dev.to: rozbiór strategii Rubena Hassida https://dev.to/getchime/ruben-hassids-linkedin-strategy-broken-down-14ao | vendor, 13 tygodni do maja 2026, 75 postów | 78,7% pojedynczy obraz, 21,3% tekst, 0% karuzel; 5,77 postów/tydz.; 854K obserwujących |
| S7 | getchime na dev.to: rozbiór Kyle'a Poyara https://dev.to/getchime/kyle-poyars-107k-follower-linkedin-strategy-1p8i | vendor, 30 dni, 13 postów | 12 obrazów, 1 tekst, 0 karuzel; "grafika zatrzymuje, tekst przekonuje, link konwertuje"; ~3 posty/tydz. |
| S8 | getchime na dev.to: wzorce postów kwiecień-maj 2026 https://dev.to/getchime/viral-linkedin-posts-patterns-april-may-2026-55df | vendor, 16 postów | tabela reakcji kilku twórców; teza o 2-3x komentarzach bez danych (niepotwierdzona) |
| S9 | Josh Spector, "How Justin Welsh actually uses LinkedIn" https://joshspector.com/justin-welsh-linkedin-system/ | analiza zewnętrzna, bez daty, autor nie rozmawiał z Welshem | obraz w każdym poście, post dziennie, link dopisywany po publikacji |
| S10 | Favikon, Top LinkedIn Influencers in Poland https://www.favikon.com/blog/top-linkedin-influencers-poland | ranking, 2025-12-31 | pozycje polskich twórców (wyniki 0-100), 1. miejsce "ponad 200k" |
| S11 | arXiv 2501.16450 (360Brew) https://arxiv.org/abs/2501.16450 | preprint 2025-01-27, WYCOFANY (v4 2025-08-23) | tylko jako ostrzeżenie: nie opieram się na doniesieniach o "360Brew" |
| S12 | Richard van der Blom, Algorithm Insights | płatny raport; strona główna bez metodologii | NIEDOSTĘPNY, nie użyty ([NIEPEWNE]) |
| S13 | Favikon, Top 200 AI Leaders (2026-04-17) | pełna lista za formularzem | NIEDOSTĘPNY (publicznie próbka) |
| P | 94 posty z publicznych adresów `linkedin.com/feed/update/urn:li:activity:<ID>` (lista ID w sekcji Liczby) | pomiar własny, 2026-11-05 | wszystkie liczby oznaczone [POMIAR] |
| M | 38 pierwszych obrazów postów, OCR + klasyfikacja ręczna | pomiar własny, 2026-11-05 | liczby w sekcji Wzorce grafiki |

## Liczby

### Twórcy (wybór wg dowodów)

Liczba obserwujących: odczyt z publicznej strony posta w dniu 2026-11-05 (źródło główne), plus inne źródło tam, gdzie jest. Kryterium wyboru: duży zasięg w AI / tech / biznes (>= 400k dla EN), pozycja w rankingu Favikon dla PL, oraz istnienie widocznych postów. Hormozi (949k), Gary Vaynerchuk (5,9 M), Chris Donnelly, Matt Gray są w S5, ale ich postów nie próbkowałem.

| Twórca | Obserwujący (LinkedIn, 2026-11-05) | Inne źródło | n postów | Obrazy / wideo / bez mediów / PDF | Mediana reakcji | Mediana słów posta | Mediana 1. linii (zn.) | Post z linkiem w treści | Grafika "samodzielna" (A) / obrazy |
|---|---|---|---|---|---|---|---|---|---|
| Andrew Ng | 2 667 857 | | 5 | 1/1/3/0 | 7 419 | 463 | 224 | 5/5 | 0/1 |
| Allie K. Miller | 1 680 222 | wg jej nagłówka "2M" | 8 | 3/2/3/0 | 2 691 | 141 | 80 | 1/8 | 1/3 |
| Zain Kahn | 1 001 362 | | 8 | 6/0/2/0 | 4 076 | 54 | 46 | 7/8 | 5/6 |
| Ruben Hassid | 954 694 | S5: 832k (maj 2026); S6: 854K (maj 2026) | 8 | 3/4/0/1 | 1 600 | 278 | 43 | 2/8 | 2/3 |
| Justin Welsh | 890 321 | S5: 853k (maj 2026) | 9 | 2/0/7/0 | 1 718 | 124 | 55 | 3/9 | 2/2 |
| Sahil Bloom | 725 844 | | 8 | 4/2/2/0 | 2 432 | 342 | 44 | 5/8 | 4/4 |
| Lenny Rachitsky | 413 779 | | 8 | 4/1/3/0 | 1 086 | 104 | 94 | 6/8 | 4/4 |
| Lukas M. Ziegler (PL, robotyka/AI) | 273 478 | S10: #1 w Polsce, wynik 100/100, "ponad 200k" (2025-12-31) | 7 | 0/7/0/0 | 2 248 | 114 | 32 | 3/7 | 0/0 |
| Rowan Cheung | 105 708 (wartość z widoku gościa, [NIEPEWNE] czy aktualna) | | 8 | 2/5/1/0 | 78 | 110 | 66 | 5/8 | 0/2 |
| Aleksandra Przegalińska (PL, AI) | 65 933 | S10: #15, 90,6 | 5 | 3/1/1/0 | 297 | 92 | 196 | 2/5 | 0/3 |
| Gustaw Dudek (PL, Power BI) | 51 639 | S10: #6, 93,9 | 6 | 5/0/0/1 | 362 | 262 | 117 | 4/6 | 1/5 |
| Mateusz Chrobok (PL, AI/cyber) | 42 896 | S10: #13, 91,1 | 6 | 2/2/2/0 | 26 | 18 | 113 | 2/6 | 0/2 |
| Kamil Stanuch (PL, tech) | 16 928 | brak w S10 | 8 | 3/1/4/0 | 40 | 86 | 126 | 3/8 | 1/3 |

Razem: 94 posty, 13 twórców (8 EN, 5 PL). Posty z ID (do powtórzenia pomiaru) były wzięte z wyników wyszukiwarki dla publicznych adresów każdego twórcy; kolekcja skryptu Playwright jest odtwarzalna (adres `linkedin.com/feed/update/urn:li:activity:<ID>/`, selektory `data-test-id="main-feed-activity-card__commentary"`, `feed-images-content__list-item`, `social-actions__reaction-count`).

Uwaga o wartościach: reakcje nie są porównywalne między twórcami (inny zasięg, inny rok). Porównuję tylko wewnątrz twórcy (po normalizacji). Rowan Cheung ma bardzo niskie reakcje względem sławy w innych kanałach: w tej próbie LinkedIn nie jest jego głównym kanałem.

### Format (n = 94 posty, 13 twórców) [POMIAR]

| Format | n | twórcy | uwaga |
|---|---|---|---|
| Pojedynczy obraz lub galeria | 38 | 12 | 3 posty to galerie 2-5 obrazów |
| Natywne wideo | 26 | 10 | Ziegler 7/7 |
| Bez mediów w widoku (tekst, ew. link) | 28 | 10 | w tym niewykryte media, [NIEPEWNE] |
| PDF / karuzela (natywny dokument) | 2 | 2 | n=2: za mało danych |

Niezależnie od mojej próby: Hassid 0% karuzel w 75 postach (S6), Poyar 0 karuzel w 13 postach (S7). Wśród twórców AI karuzela PDF jest rzadkością; za to benchmarki marek (S2) stawiają dokumenty na szczycie. Sprzeczność opisana w Algorytm.

### Skuteczność wg formatu i klasy grafiki (reakcje / mediana twórcy; bootstrap 5000, 95% CI różnicy median) [POMIAR]

| Porównanie | n | Mediana (norm.) | Różnica median | 95% CI |
|---|---|---|---|---|
| Obraz vs bez mediów | 38 vs 28 | 1,30 vs 0,77 | +0,54 | 0,09 do 0,90 |
| Grafika samodzielna (A) vs reszta obrazów | 20 vs 18 | 1,50 vs 0,87 | +0,63 | 0,20 do 1,20 |
| Obraz vs wideo | 38 vs 26 | 1,30 vs 0,94 | +0,37 | -0,09 do 0,98 (nie rozstrzyga) |

W obrębie twórców, którzy mają zarówno grafikę A, jak i nie-A: A wygrywa u 4 z 5 (Zain 1,45 vs 0,11; Ruben 1,68 vs 0,35; Dudek 1,31 vs 0,81; Allie 3,24 vs 1,92; odwrotnie u Stanucha 0,99 vs 6,95, jeden viralowy zrzut rozmowy). Pułapka: reakcje to proxy; n małe.

Cechy tekstowe praktycznie NIE różnicują (Spearman z normalizowanymi reakcjami, n=68..94): długość 1. linii -0,17; słowa 0,12; liczba linii 0,03; punkty listy -0,03; link w treści 0,99 vs 1,01 (mediany norm.); hashtagi 0,98 vs 1,00; cyfra w haku 1,01 vs 1,00. Wniosek: dźwignia leży w GRAFICE, nie w mikro-regułach tekstu.

## Wzorce grafiki

Zbiór: pierwszy obraz z 38 postów (12 twórców); jeden obraz na post (galerie: tylko 1. kadr).

### Klasy [KODOWANIE]

| Klasa | Definicja | n | twórcy |
|---|---|---|---|
| A. Grafika samodzielna | tytuł lub teza + treść (lista, kroki, macierz, schemat, wykres, karta z tezą), czytelna bez tekstu | 20 | 8 (Allie 1, Dudek 1, Lenny 4, Ruben 2, Sahil 4, Stanuch 1, Welsh 2, Zain 5) |
| B. Zrzut źródła | zrzut komunikatu, artykułu, rozmowy | 5 | 3 |
| C. Zdjęcie / plakat | portret, plakat zaproszenia, okładka | 6 | 3 |
| D. Zrzut produktu / dashboardu | ekran aplikacji, dashboard, CV-przykład | 7 | 4 |

Grafika "samodzielna" jest najczęstszą klasą (53% obrazów), ale tylko u 5 z 12 twórców stanowi większość ich obrazów (Zain 5/6, Sahil 4/4, Lenny 4/4, Welsh 2/2, Ruben 2/3). Twórcy polscy z próby (Chrobok, Przegalińska, Stanuch, Dudek) używają głównie zdjęć, zrzutów i dashboardów (klasa B/C/D) i mają niskie wyniki: to nie wzór do kopiowania w sprawie grafiki.

### Parametry pierwotne grafiki A (n = 20 postów, 8 twórców) [POMIAR] [KODOWANIE]

| Parametr | Wartość |
|---|---|
| Format kadru | 1:1 (13/38 obrazów w pasmie 0,97-1,03) i 4:5 (0,8); proporcje A: mediana 1,0, IQR 0,8-1,0; 19/38 obrazów pionowych |
| Słowa na grafice (OCR, dolna granica) | mediana 67, IQR 19-214; ROZKŁAD DWUMODALNY: 10/20 do 60 słów, 8/20 co najmniej 180 słów |
| Udział powierzchni zajęty tekstem | mediana 10,1%, IQR 4,7-24,1% |
| Tytuł / teza na grafice | 11 z 20 (6 twórców); orientacyjnie 2-11 słów, mediana 6; pozycja przy górnej krawędzi u wszystkich 11 [n=11, za mało na twierdzenie liczbowe] |
| Liczba w tytule grafiki | nie policzone; za mało danych |

Dwa dominujące mechanizmy, oba spełniają regułę "grafika sama się broni":

1. Lista / kroki gęste (Zain: 20 pozycji, nazwa narzędzia + opis w jednej linii, ok. 210-230 słów; Hassid: 8 kroków w układzie infografiki, ok. 280 słów; szablon z adnotacjami). Post wtedy bywa krótki (Zain mediana 54 słowa) albo długi (Hassid, Bloom 280-340 słów, powtarzający treść).
2. Schemat / wykres / macierz rzadki (Lenny: cykl 3 faz z jedną etykietą środkową, wykres czasu dojścia do dopasowania produktu do rynku z tytułem; Bloom: macierz 2x2, krzywa 1,01^365 vs 0,99^365, schodki; Welsh: karta z tezą 18-32 słów, z liczbą polubień jako dowód społeczny). 3-35 słów, jeden pomysł, hierarchia: tytuł, element graficzny, podpis autora małą czcionką.

Porównanie gęste vs rzadkie (norm. reakcje): gęste 1,45 (n=8, 5 twórców) vs rzadkie 1,82 (n=9, 4 twórców): za mało danych, różnica w szumie.

### Typowe elementy wspólne klasy A (obserwacja, bez liczb) [KODOWANIE]

- Jeden tytuł lub teza jako największy tekst; reszta wyraźnie mniejsza (hierarchia dwóch poziomów).
- Struktura widoczna na pierwszy rzut oka: numeracja, kolumny, ćwiartki, oś czasu.
- Znak autora: uchwyt lub nazwa małą czcionką (Welsh, Bloom: widoczny; Zain: brak).
- Brak zdjęcia w tle; jasne lub bardzo ciemne tło, wysoki kontrast.
- Treść grafiki NIE jest powtórzeniem pytania z posta, tylko samą odpowiedzią (lista, kroki, schemat).

## Wzorce tekstu

Dane: 94 posty (długość, linie), 68 postów z flagami hak/CTA (9 twórców: Allie, Hassid, Kahn, Cheung, Ng, Rachitsky, Welsh, Bloom, Ziegler) [POMIAR].

| Parametr | n postów / twórcy | Wartość | Uwaga |
|---|---|---|---|
| Długość posta | 93 / 13 | mediana 730 znaków (IQR 331-1509); 117,5 słowa (IQR 54-255) | szeroki rozrzut; mediana twórców od 18 do 463 słów |
| Pierwsza linia (hak) | 93 / 13 | mediana 65 znaków (IQR 42-120); 78/93 mieści się w 140 | platforma ucina przy ok. 140-210 znaków (S3, zachowanie platformy) |
| Linie niepuste | 68 / 9 | mediana 10 (IQR 5-20) | |
| Listy (>= 3 linie punktowane/numerowane) | 68 / 9 | 33/68 posty u 8 twórców | |
| Cyfra w haku | 68 / 9 | 16/68 (24%), 7 twórców | S5: u Herubel 56%, Janvier 52% haków (niewidziane przeze mnie) |
| "How to ..." jako hak | 68 / 9 | 8/68 (12%), 5 twórców | norm. reakcje 1,42, n=8: za mało |
| Pytanie w 1. linii | 68 / 9 | 1/68 | |
| Pytanie na końcu posta | 68 / 9 | 4/68 (6%), 3 twórców | nasze v2: 5 z 9 |
| CTA do newslettera / zapisu (regex) | 68 / 9 | 32/68, 8 twórców | regex łapie też "join" w zwykłym zdaniu; wartość górna |
| CTA brak słowa kluczowego | 68 / 9 | 14/68 | |
| Link w treści posta | 94 / 13 | 48/94 (51%), każdy z 13 twórców choć raz | link w pierwszym komentarzu nie jest mierzalny w widoku gościa |
| Hashtagi | 94 / 13 | mediana 0; 18/94 postów z hashtagiem, 5 twórców (Dudek 25-30, Hassid 3-9 w starszych, Cheung, Chrobok, Przegalińska) | Hassid 2026: 0 |
| Emoji | 68 / 9 | mediana 0; 27/68 z emoji | |
| Częstotliwość | 3 twórców (vendor) | Hassid 5,77/tydz. (S6), Poyar ok. 3/tydz. (S7), Welsh 1/dzień (S9) | za mało danych |

Mechaniki tekstu, które powtarza próba (bez liczb skuteczności, bo nie różnicują): krótki hak w jednym zdaniu, jedna myśl w linii, listy numerowane dla treści enumerowalnych, link i zaproszenie do zasobu (newsletter, pobranie) zamiast pytania do komentarza, brak hashtagów.

## Algorytm (fakty z datami)

| # | Fakt | Źródło, data | Siła |
|---|---|---|---|
| F1 | LinkedIn używa czasu spędzonego (dwell time) w rankingu feedu; wcześniej krótki dwell był sygnałem negatywnym, teraz bierny odbiór jest sygnałem pozytywnym; progi nie są ręczne, wyliczane z danych | S1, 2024-10-01 | pierwotne; liczby wag niepodane |
| F2 | Benchmark marek 2025 (stopa zaangażowania na wyświetlenia): dokument 7,00%, multi-image 6,45%, wideo 6,00%, obraz 5,30%, tekst 4,50%, ankieta 4,20%, link 3,25% | S2, 2026-03-16 | vendor, strony firmowe 1K-1M; średnia 5,20% |
| F3 | Inny zbiór (mediana zaangażowania, wiele postów): multi-image 2,44% (n=16 307), wideo 2,26% (48 676), obraz 2,11% (97 682), dokument 2,11% (6 622), tekst 1,53% (45 651); średnie wyświetlenia: tekst 7 995, wideo 6 830, obraz 6 742, dokument 2 233 | S3, bez daty | vendor; dokument ma NAJNIŻSZY zasięg mimo wyższego zaangażowania, wyniki sprzeczne z F2 w rankingu dokument vs obraz |
| F4 | Długość: u S3 posty < 150 znaków i 2000-3000 znaków wypadają lepiej niż środek, najgorsze 600-1500; bez n i daty | S3 | słabe; nasza mediana 730 i v2 933 leżą w pasie "najgorszym" |
| F5 | Ucięcie posta w feedzie przy ok. 140-210 znakach zależnie od urządzenia | S3 | zachowanie platformy, nie wynik badania |
| F6 | Szybka pierwsza reakcja: pierwsze polubienie w 5 minut ok. 17 692 wyświetleń vs po godzinie 6 422 (2,75x) | S3, bez n i daty | słabe, [NIEPEWNE] |
| F7 | Kara za link zewnętrzny: strony firmowe 26,5% (wcześniej 5% w 2023 do 42% w 2025), profile osobiste prawie brak; LinkPost mediana 448 vs 705 wyświetleń (-36%, 358 tys. postów); wiele linków u van der Bloma: 2-3 linki ok. 7% poniżej bazy, 4+ ok. 24% | S4, bez daty | vendor; sprzeczne z doniesieniem o oświadczeniu LinkedIn, że kary nie ma ([NIEPEWNE], nie znalazłem pierwotnego źródła) |
| F8 | Link w pierwszym komentarzu: według S4 pomaga na stronach firmowych, ale "przestał być darmowy około 2024", mniej kliknięć; bez liczb | S4 | słabe |
| F9 | Twierdzenia, że algorytm "czyta tekst na obrazach" i że "slajd = dwell" | blogi praktyków (np. usevisuals, linkedinpreview) | [NIEPEWNE], brak pierwotnego źródła |
| F10 | "360Brew" jako model rankingu | S11: preprint wycofany | nie używać |
| F11 | Natywne wielo-obrazy (galeria) i dokumenty PDF są dziś osobnymi formatami; karuzela = PDF dokument | vendorzy 2026 | popularny przekaz, bez pierwotnego źródła |

Konsekwencja: jedyny pierwotny fakt (F1) mówi, że czytanie ma znaczenie; to wspiera grafikę, którą da się czytać dłużej (lista, schemat), ale nie rozstrzyga PDF vs obraz. Sprzeczność F2 vs F3 dla dokumentów jest nierozstrzygalna na danych publicznych.

## Co mamy / czego nie mamy (vs build_posts_v2.py i posty v2)

Zmierzone na `out_v2/posts/p01..p09/grafika.png` i `linkedin.json` [POMIAR]:

| Parametr | v2 | Próba (n=94 / 38 obrazów) | Ocena |
|---|---|---|---|
| Grafika samodzielna | OCR słów: p01 14, p02 13, p03 22, p04 19, p05 28, p06 16, p07 32, p08 30, p09 22 (mediana 22); w kadrze animacji: p01 0, p02 0, p03 10, p04 8, p05 8, p06 3, p07 14, p08 13, p09 5 słów | klasa A: mediana 67 słów, IQR 19-214 | BRAK. Tylko p07 (słupki 92% vs 18%) zbliża się do klasy A. 9/9 przechodzi własny filtr `alone: 3`, bo ocena dotyczy pomysłu, nie grafiki |
| Skład grafiki | `graphic()` (build_posts_v2.py:270): 1. zdanie posta jako nagłówek (6-16 słów, 4 linie przy 48-64 px) + kadr animacji z filmu w 85% sceny (linia 278) + stopka z nazwą; ok. 40% płótna zajmuje kadr animacji, w większości rozmyty gradient | A: tytuł + struktura (lista/schemat/macierz) + podpis | Kadr z filmu jest dekoracją, nie przekazem (p02: pusty panel z naklejką "ZABLOKOWANE") |
| Format główny | 1 obraz + karuzela PDF (5-7 slajdów, 810x1013 pt) | obraz 12/13 twórców; PDF 2/94 | Mamy oba; karuzela jest wersją dodatkową |
| Hak (1. linia) | 35-96 znaków, mediana 64 | mediana 65, IQR 42-120 | ZGODNE |
| Długość posta | 832-1083 znaków (mediana 933), 131-175 słów | mediana 730 znaków, 117 słów | W normie próby; według S3 w pasie najgorszym (słabe) |
| Linie / listy | 7-11 linii, p01, p02, p09 z listą | mediana 10 linii; listy 33/68 | ZGODNE |
| Pytanie na końcu | 5 z 9 (p02, p03, p05, p07, p09) | 4/68 | NIEZGODNE z próbą |
| Hashtagi | 4 w każdym | mediana 0; 18/94 postów | NIEZGODNE z próbą |
| Link | tylko w pierwszym komentarzu (ADR-0009) | 51% postów z linkiem w treści; skutek na zasięg: brak różnicy w mojej próbie | zasada Kamila (E) wygrywa |
| Wideo natywne | brak | 26/94, 10 twórców | nie mamy; film ma gotowe klipy |
| Samoocena | `score` alone/concrete/new/visual 0-3, próg >= 8 | | Nie mierzy grafiki; do zastąpienia testem OCR (patrz niżej) |

## Rozkład logik na parametry pierwotne i DLACZEGO

Każda logika jako parametry (z wartościami z próby) i problem czytelnika, który rozwiązuje. Szczegóły liczb: sekcja "Wystarczalność danych".

| Logika | Parametry pierwotne | DLACZEGO (problem czytelnika) |
|---|---|---|
| L1 Jeden obraz jako główny nośnik | typ = pojedynczy obraz; proporcje 4:5 lub 1:1; liczba plików 1; napisy w obrazie, nie w PDF | zatrzymać scroll (duża powierzchnia na telefonie), zero kliknięć do zrozumienia |
| L1b Karuzela PDF jako główny nośnik | typ = dokument; slajdy 5-7 | dłuższe czytanie, każdy slajd to osobne zatrzymanie (hipoteza praktyków) |
| L2 Grafika samodzielna | elementy: tytuł/teza + treść ustrukturyzowana + podpis; udział tekstu mediana 10%, IQR 5-24%; tekst posta nie jest warunkiem zrozumienia | zrozumieć bez tekstu; materiał "do zapisania"; dłuższy dwell na grafice |
| L3 Tryby gęstości | tryb A: schemat 3-35 słów, jeden pomysł; tryb B: lista/kroki 60-230 słów | wybór wg typu treści: pojedyncza teza vs wyliczenie |
| L4 Teza na grafice | tytuł 2-11 słów, mediana 6; największy tekst; górna część | w 1-2 s odpowiedzieć "o czym to"; przeczytać cel zanim zacznie się treść |
| L5 Hak | pierwsza linia mediana 65 zn., do ok. 100 zn.; samodzielne zdanie; liczba lub "How to" u ok. 1/3 | zmieścić sens przed "pokaż więcej" (cięcie ok. 140-210 zn.) |
| L6 Długość posta | trzy pasma: bardzo krótki, środek ok. 90-140 słów, długi > 250 | tekst ma dopełniać grafikę (reguła Kamila), nie powtarzać jej |
| L7 Układ linii | mediana 10 linii; jedna myśl na linię; lista przy >= 3 elementach | szybkie skanowanie na telefonie |
| L8 CTA | zaproszenie do zasobu (repo, film, newsletter) vs pytanie na końcu | cel: wejścia do zasobu vs komentarze |
| L9 Link | w treści vs w pierwszym komentarzu (ADR-0009) | uniknąć możliwej kary zasięgu vs ułatwić klikanie |
| L10 Hashtagi | liczba 0-3 vs 4 | dyskretny sygnał tematu bez szumu |
| L12 Wideo natywne | klip 20-60 s; napisy | zatrzymanie ruchem; dłuższy dwell |

## Wystarczalność danych

Reguła Kamila: próg ogólny >= 30 widzianych postów u >= 8 twórców (SPEŁNIONY: 94 / 13); twierdzenie o częstości: >= 5 twórców; parametr liczbowy: >= 20 postów zmierzonych; poniżej: "za mało danych". Wartość "twórcy" w tabeli = liczba twórców, u których zjawisko wystąpiło; mediana i IQR tylko dla liczb. [POMIAR] jeśli nie zaznaczono inaczej.

| Logika | Parametr | n postów | n twórców | Mediana | IQR | Werdykt |
|---|---|---|---|---|---|---|
| L1 | obraz jako format | 38 z 94 | 12 | n.d. | n.d. | OK (>= 5 twórców) |
| L1 | proporcje obrazu (szer./wys.) | 38 | 12 | 1,0 | 0,8-1,0 (A, n=20) | OK |
| L1b | PDF / karuzela jako format | 2 z 94 | 2 | n.d. | n.d. | za mało danych (n=2); odrzucone jako logika główna |
| L1b | liczba slajdów, słowa na slajd | 0 zmierzonych | 0 | n.d. | n.d. | za mało danych (n=0); wymaga dodatkowej próby |
| L2 | grafika klasy A | 20 z 38 obrazów | 8 | n.d. | n.d. | OK (>= 5 twórców, n >= 20) |
| L2 | udział powierzchni z tekstem (OCR) | 20 (A) / 38 (wszystkie) | 8 / 12 | 10,1% (A), 7,9% (wszystkie) | 4,7-24,1% (A); 4,2-15,2% (wszystkie) | OK (dolna granica OCR) |
| L2 | liczba elementów na grafice | 0 policzonych | 0 | n.d. | n.d. | nie mierzone; odrzucone jako parametr |
| L2 | A vs reszta: różnica skuteczności | 20 vs 18 | 8 vs 9 | 1,50 vs 0,87 | CI różnicy 0,20-1,20 | OK słabo (proxy reakcji; wewnątrz twórcy 4 z 5) |
| L3 | słowa na grafice A | 20 | 8 | 67 | 19-214 | OK liczbowo, ale rozkład dwumodalny: mediana wprowadza w błąd, używać dwóch trybów |
| L3 | porównanie gęste vs rzadkie | 8 vs 9 | 5 vs 4 | 1,45 vs 1,82 | n.d. | za mało danych (n < 20) |
| L4 | teza/tytuł obecne na A | 11 z 20 | 6 | n.d. | n.d. | OK jako częstość (6 twórców) |
| L4 | długość tytułu (słowa), pozycja | 11 | 6 | 6 | 2-11 (zakres) | za mało danych (n=11 < 20) |
| L5 | długość pierwszej linii (znaki) | 93 | 13 | 65 | 42-120 | OK |
| L5 | cyfra w haku | 16 z 68 | 7 | n.d. | n.d. | OK jako częstość (24%); bez sygnału skuteczności |
| L5 | "How to" w haku | 8 z 68 | 5 | n.d. | n.d. | OK na granicy (5 twórców); skuteczność za mało danych (n=8) |
| L6 | długość posta (znaki) | 93 | 13 | 730 | 331-1509 | OK opis; brak optimum (rho z reakcjami 0,12) |
| L6 | długość posta (słowa) | 92 | 13 | 117,5 | 54-255 | OK opis |
| L7 | linie niepuste | 68 | 9 | 10 | 5-20 | OK |
| L7 | lista >= 3 punkty | 33 z 68 | 8 | n.d. | n.d. | OK |
| L8 | pytanie na końcu | 4 z 68 | 3 | n.d. | n.d. | za mało danych dla tezy "pytanie działa" (3 twórców); częstość niska |
| L8 | CTA do zasobu/newslettera (regex) | 32 z 68 | 8 | n.d. | n.d. | OK jako częstość (wartość zawyżona regexem) |
| L9 | link w treści | 48 z 94 | 13 | n.d. | n.d. | OK jako częstość |
| L9 | link w pierwszym komentarzu | 0 zmierzonych (widok gościa nie pokazuje komentarzy w pełni) | 0 | n.d. | n.d. | za mało danych; decyduje zasada Kamila |
| L9 | skutek linku na zasięg | 94 (mój pomiar: 0,99 vs 1,01); S3/S4: wartości vendorów | 13 | n.d. | n.d. | OK jako brak różnicy w próbie; źródła vendorów sprzeczne |
| L10 | posty z hashtagiem | 18 z 94 | 5 | 0 (liczba hashtagów) | 0-0 | OK (brak hashtagów dominuje) |
| L12 | wideo jako format | 26 z 94 | 10 | n.d. | n.d. | OK jako częstość; mechanika wideo (napisy, długość) nie mierzona |
| ogólna | częstotliwość postów | 3 twórców (vendor) | 3 | n.d. | n.d. | za mało danych (n=3 < 5) |
| ogólna | wiek próby: posty <= 1 rok | 10 z 94 | 5 | n.d. | n.d. | za mało na ocenę "dziś" (stan 2025-2026) |
| ogólna | wyświetlenia i dwell | 0 | 0 | n.d. | n.d. | niemierzalne w widoku gościa |

Wniosek: logika przechodzi do "Kolejność wdrożenia" tylko jeśli jej parametry nie mają w tabeli "za mało danych" wymaganych do wdrożenia. Przechodzą: L1, L2, L4 (obecność tezy, bez twierdzeń o pozycji), L5, L7, L10, L3 (dwa tryby, bez twierdzenia "który lepszy"). Nie przechodzą: L1b mechanika, L8 (jako "pytanie działa"), L12 mechanika, częstotliwość. L6 przechodzi tylko jako opis; wdrożenie L6 wynika z reguły Kamila (E), nie z danych.

## Macierz logik

Skala 0-3 w każdej kolumnie; progi: A = liczba twórców (0: <= 2; 1: 3-4; 2: 5-7; 3: >= 8); B = udział twórców, u których logika jest większością ich postów (0: < 20%; 1: 20-39%; 2: 40-59%; 3: >= 60%); C = zgodność źródeł (0: brak lub sprzeczność; 1: jedno źródło vendora; 2: dwa niezależne źródła zgodne; 3: źródło pierwotne + vendor); D = sygnał skuteczności (0: brak; 1: słaby, n < 20 lub CI obejmuje 0; 2: CI różnicy wyklucza 0, ale proxy i konfundery; 3: CI wyklucza 0 + drugie źródło); E = reguła Kamila (wygrywa zawsze: + zgodna, - sprzeczna, 0 brak reguły). Σ = A+B+C+D (max 12).

| Logika | A | B | C | D | Σ | E | Werdykt |
|---|---|---|---|---|---|---|---|
| L1 obraz jako główny nośnik | 3 | 1 | 2 | 2 | 8 | + (grafika ma się bronić sama) | WYGRYWA |
| L1b karuzela PDF jako główny nośnik | 0 | 0 | 0 | 1 | 1 | 0 | przegrywa; karuzela tylko jako dodatek |
| L2 grafika samodzielna (klasa A) | 3 | 2 | 1 | 2 | 8 | + (to jest reguła Kamila) | WYGRYWA, obowiązkowa |
| L2b grafika jako haczyk (zdjęcie, zrzut, dashboard; treść w tekście) | 3 | 2 | 0 | 0 | 5 | - (sprzeczna z regułą) | PRZEGRYWA (także na wynikach: 0,87 vs 1,50) |
| L3 gęsty tryb (>= 180 słów) | 2 | 1 | 0 | 1 | 4 | 0 | równorzędny |
| L3 rzadki tryb (<= 35 słów) | 1 | 1 | 0 | 1 | 3 | 0 | równorzędny; wybór wg typu treści |
| L4 teza na grafice | 2 | 1 | 1 | 0 | 4 | + | WDRAŻAMY (E wygrywa) |
| L5 hak <= ok. 100 zn. | 3 | 3 | 1 | 1 | 8 | 0 | WYGRYWA (v2 już zgodne) |
| L6 środek 90-140 słów | 2 | 1 | 0 | 0 | 3 | 0 | |
| L6 bardzo krótki lub długi (U-krzywa) | 1 | 0 | 1 | 0 | 2 | + (krótki: tekst tylko dopełnia) | E decyduje: krótki |
| L7 układ linii i lista | 3 | 2 | 0 | 0 | 5 | 0 | ZGODNE, zostaje |
| L8 CTA do zasobu | 3 | 2 | 0 | 0 | 5 | 0 | WYGRYWA nad pytaniem |
| L8 pytanie na końcu | 0 | 0 | 1 | 0 | 1 | 0 | PRZEGRYWA w wymuszaniu |
| L9 link w treści | 3 | 2 | 0 | 1 | 6 | - (ADR-0009) | E WYGRYWA: link w komentarzu zostaje |
| L10 hashtagi 0-3 | 3 | 3 | 0 | 1 | 7 | 0 | WYGRYWA |
| L10 hashtagi 4 (v2) | 1 | 0 | 0 | 0 | 1 | 0 | PRZEGRYWA |
| L12 wideo natywne | 3 | 1 | 2 | 1 | 7 | 0 | DECYZJA KAMILA (nie z danych) |

Notatki do komórek (dowody):

- L1: A=3: obrazy u 12 z 13 twórców. B=1: obraz stanowi >= 50% postów u 5 z 13 (Kahn 6/8, Dudek 5/6, Przegalińska 3/5, Bloom 4/8, Rachitsky 4/8). C=2: S2 (obraz 5,30% > tekst 4,50%, 2025) i S3 (2,11% > 1,53%) zgodne co do obraz > tekst; osobno S6 (78,7% obrazów) i S7 (12/13). D=2: CI różnicy 0,09-0,90.
- L1b: A=0: 2 posty u 2 twórców; B=0; C=0: S2 daje dokumentowi pierwsze miejsce (7,00%), S3 daje dokumentowi równo z obrazem (2,11%) i najniższy zasięg (2 233 wyświetleń vs 6 742); D=1: n=2.
- L2: A=3: 8 twórców; B=2: grafika A to większość obrazów u 5 z 12 twórców z obrazami (42%); C=1: S7 i S6 to ten sam wydawca (jedno źródło); D=2: CI 0,20-1,20.
- L2b: A=3: 18 z 38 obrazów u 9 twórców; B=2: większość nie-A u 7 z 12 (58%); C=0; D=0: wynik niższy.
- L5: A=3: mediana 1. linii <= 100 zn. u 8 z 13 twórców; B=3: 62%; C=1: S3 (cięcie 140-210, zachowanie platformy); D=1: rho -0,17, krótkie (<= 65 zn.) 1,09 vs 0,93.
- L8 CTA do zasobu: regex, wartość zawyżona; "pytanie" 4/68, 3 twórców; S8 twierdzi, że komentarz wbudowany w strukturę daje 2-3x więcej komentarzy, bez danych (C=1).
- L9: C=0: S4 (profile osobiste prawie bez kary), LinkPost (-36%), S2 (linki najniżej, 3,25%) są niespójne; D=1: 0,99 vs 1,01.
- L10: 8 z 13 twórców nigdy nie dodaje hashtagu; D=1: 0,98 vs 1,00.
- L12: C=2: S2 (wideo 6,00% > obraz 5,30%) i S3 (2,26% > 2,11%) zgodne; D=1: CI obejmuje 0.

Konflikty i rozstrzygnięcie po wyniku:
1. Obraz vs karuzela: obraz 8 vs 1. Dodatkowo E: grafika bez tekstu musi być kompletna, a kolejne slajdy tego nie dają. Karuzela zostaje wyłącznie jako opcjonalny drugi plik, okładka = ta sama grafika samodzielna.
2. Grafika samodzielna vs haczyk: 8 vs 5, plus E i wynik 1,50 vs 0,87.
3. Gęsto vs rzadko: brak zwycięzcy w punktach (4 vs 3, n za małe); rozstrzyga typ treści (wyliczenie = gęsto, teza = rzadko).
4. Link w treści vs w komentarzu: wg Σ link w treści ma 6, ale E (ADR-0009) wygrywa; próba nie pokazuje różnicy skuteczności.
5. Pytanie vs zasób: 5 vs 1; pytanie przegrywa w roli wymuszonej końcówki.
6. Krótki tekst vs środek: dane nie rozstrzygają (D=0 u obu), E rozstrzyga na krótki.

## Kolejność wdrożenia

Tylko logiki z werdyktem "WYGRYWA" lub "WDRAŻAMY" i bez braków w sekcji Wystarczalność. Koszt: S = do 1 h, M = 0,5-1 dzień, L = > 1 dzień.

### P1 (zmienia werdykt Kamila: "niekompletne")

1. L2 + L1: osobny rendering "grafiki samodzielnej" zamiast `graphic()` ze stopklatką. Koszt M-L.
   - W `build_posts_v2.py` dodać do każdego posta pole `gfx` ze specyfikacją: `type` ("schemat" lub "lista"), `title` (2-11 słów, teza), `elements` (lista elementów: liczba, etykieta, krok), `footer`; usunąć wywołanie `ffmpeg` na `gfx/*.mov` jako domyślnej treści obrazu (stopklatka tylko, gdy w kadrze animacji jest cały schemat posta, jak p07).
   - Nowa funkcja `render_graphic(spec)` z dwoma szablonami: A: schemat/wykres/macierz 3-35 słów (tytuł u góry jako największy tekst, element graficzny w środku, podpis małą czcionką); B: lista/kroki 60-230 słów (tytuł, numerowane pozycje jedna linia, podpis). Płótno 1080x1350 (4:5). Brak zdjęcia w tle; ciemne tło motywu `style/themes/cetus.json` (kontrast).
   - Napisać 9 specyfikacji z faktów już obecnych w filmie (każdy fakt ma w `src` zakres słów): np. p07 = wykres słupków przed/dziś + teza; p01 = "3 z 4" + trzy filary; p05 = tabela poziom ryzyka vs kto sprawdza; p08 = pełne zdanie do skopiowania jako karta + trzy słowa statusu. Zadanie redakcyjne, nie kodowe.
2. Zastąpić ocenę ręczną `alone` testem maszynowym "grafika sama": OCR (`tesseract` jest na laptopie) na `grafika.png`: tytuł obecny (największy tekst >= 4% wysokości), liczba słów w zakresie 15-230, brak pustego pola > 35% powierzchni. Progi to [PROP] z rozkładu klasy A (min 3 słowa przy schemacie z etykietami; 8/20 powyżej 180), kalibrować na własnych postach. Koszt M. Dodać test w `tests/` (np. `test_gfx_alone.py`) i użyć jako warunek `make`.
3. L1: obraz główny, karuzela jako opcja. W `main()` generować `grafika.png` zawsze (dziś tylko z `--graphics`), PDF tylko gdy jawnie żądany; pierwszy slajd karuzeli = ta sama grafika. Koszt S.

### P2 (tanie, zgodne z próbą)

4. L10: hashtagi z 4 do 0-3 (`hashtags` w POSTS, linie 49, 78, 104, 129, 153, 178, 203, 230, 254). Koszt S.
5. L8: usunąć wymuszone pytanie końcowe w p02, p03, p05, p07, p09; zamienić na zdanie kierujące do zasobu (repo w pierwszym komentarzu, film). Koszt S (edycja tekstów).
6. L6 wg E: skrócić teksty do tego, czego grafika nie niesie; cel orientacyjny ok. 60-120 słów (dziś 131-175). To wynika z reguły Kamila, nie z danych; w próbie długość nie koreluje ze skutecznością (rho 0,12). Koszt M (9 tekstów, przegląd humanizer).
7. L5: zostawić (v2 zgodne); dodać miękki limit 1. linii <= 120 znaków do `linkedin.py check` lub lokalnego testu. Koszt S.
8. L9: bez zmian (ADR-0009).

### P3 (wymaga decyzji lub brakuje danych)

9. L12 wideo natywne z klipów filmu: decyzja Kamila; mechanika (napisy, długość, hak wizualny) niezmierzona. Koszt M po decyzji.
10. Karuzela jako dodatek: brak danych o mechanice (n=2). Zostawić obecną, mierzyć na własnym koncie.
11. Dane wyświetleń: własna analityka LinkedIn po publikacji pierwszych postów, aby zastąpić proxy reakcji. Koszt S (eksport), zysk duży.

## Decyzje otwarte dla Kamila

1. Obraz 4:5 jako główny, karuzela PDF jako drugi plik: tak? Dane publiczne rozstrzygają za obrazem u twórców AI, ale benchmarki marek dają dokumentowi pierwsze miejsce, a dokument ma najniższy zasięg w jednym z nich. Alternatywa: przez dwa tygodnie publikować po jednym poście w obu wersjach i porównać wyświetlenia z własnej analityki.
2. Link w pierwszym komentarzu (ADR-0009) zostaje? Próba nie widzi różnicy skuteczności, a według jednego vendora profile osobiste prawie nie ponoszą kary za link; zmiana wymagałaby zmiany ADR (reguła Kamila wygrywa, więc nic nie zmieniam bez Twojej decyzji).
3. Jak krótki ma być tekst (60-120 słów vs obecne ok. 146)? Dane nie mają optimum; to decyzja redakcyjna wynikająca z reguły "tekst tylko dopełnia".
4. Wideo natywne z filmu jako równoległy format: tak/nie?
5. Dwa tryby grafiki (schemat 3-35 słów, lista 60-230 słów): który typ dla którego posta zatwierdzasz sam, czy zostawiasz regule "wyliczenie = lista, teza = schemat"?
6. Próbka polska jest słaba: żaden z pięciu polskich twórców w próbie nie używa konsekwentnie grafiki samodzielnej na poziomie Zaina, Bloom, Rachitsky'ego. Wskaż 3-5 polskich twórców, których czytasz, a ich posty dopiszę do próby (cel: więcej niż 5 twórców polskich z klasą A).
7. Płatny raport van der Blom (S12) i pełny ranking Favikon AI (S13): kupić lub pominąć? Bez nich brak niezależnego, pierwotnego źródła o PDF vs obraz.

## Czego nie zweryfikowano

- Raport Richarda van der Bloma (płatny) i pełny ranking Favikon Top 200 AI Leaders: niedostępne.
- Wyświetlenia, dwell time, zapisy i udostępnienia pojedynczych postów: niewidoczne w widoku gościa; skuteczność mierzona proxy reakcji.
- Mechanika karuzel (liczba slajdów, słowa na slajd): n=0 zmierzonych; PDF-y nie były otwierane.
- Oświadczenie LinkedIn, że kary za link zewnętrzny nie ma: wspomniane w jednym źródle wtórnym, bez pierwotnego odnośnika.
- Twierdzenia o czytaniu tekstu z obrazów przez algorytm, o oknie pierwszej godziny (S3 bez n i daty), o 360Brew (preprint wycofany).
- Wiek próby: 80% postów ma 2-4 lata; stan "dziś" potwierdzają tylko 10 postów <= 1 rok.
- Klasyfikacja grafik wykonana przez jedną osobę; OCR zaniża liczbę słów.
- Rowan Cheung: wartość 105 708 obserwujących z widoku gościa wygląda na niską względem jego pozycji w innych kanałach, [NIEPEWNE].
- Posty bez wykrytych mediów u Welsha (7/9) i Rachitsky'ego: możliwe niewykryte obrazy.
- Polscy twórcy z rankingu Favikon (Brzoska, Pałka, Karwatka i inni) nie zostali próbkowani; ranking Favikon pochodzi z 2025-12-31.
