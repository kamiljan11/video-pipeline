# Wzorzec: short z kartami-dowodami (rozbiór 2026-10-31)

Źródło: YouTube Shorts `2EUMJ8e2uRA` (kanał Nick Automates, 31.10.2026, 39,5 s, 1080x1920@30, -15,9 LUFS).
Rozbiór: klatki co 0,5 s, detekcja scen (`select=gt(scene,0.2)`), whisper.cpp large-v3 (słowa), `volumedetect`, `silencedetect`.
Bierzemy mechanikę montażu, nie treść ani grafikę autora.

## Oś czasu (scene detect, s)

3,37 · 5,17 · 5,3 · 6,7 · 9,6 · 14,7 · 16,1 · 23,47 · 28,47 · 32,53 · 35,13 · 37,23 · 37,87

Twarde zmiany układu co ~2,5-5 s. Wewnątrz karty coś się rusza częściej (podświetlenie, kursor, licznik, przewinięcie), więc obraz zmienia się mniej więcej co 1-1,5 s.

## Cztery układy kadru (przełączane na cięciach)

| układ | geometria (px na 1080x1920) | kiedy |
|---|---|---|
| **A. split** | tło jasne (gradient + cień liści); karta-okno przeglądarki u góry ~y 140-980, w 0,89 szerokości; napis ~y 1030-1110; twarz w boksie z zaokrąglonymi górnymi rogami ~x 54-1040, y 1300-1920 (spada za dolną krawędź) | domyślny, gdy jest czego dowieść: zrzut, wykres, repo |
| **B. karta pełna, ciemne tło** | tło: rozmyty, ciemnoszary radial; karta na środku, większa (~y 270-1280); napis pod kartą ~y 1400; brak twarzy | dowód sam w sobie: cytat z bloga, demo w apce, terminal |
| **C. twarz pełna, ciasno** | twarz w całym kadrze, mocny zoom (oczy ~y 0,3); napis nisko, na klatce piersiowej ~y 0,72 | zwrot myśli ("but…", CTA na końcu) |
| **D. karta pełna, jasne tło** | jak B, tylko jasne tło; napis duży pod kartą | wyliczanka czynników ("holidays, weather, prices") |

Kolejność w tym shorcie: A (hook) → B (repo, cytat 100 mld) → B (Trends, Wikipedia) → A (terminal: "normalnie trenowałbyś…") → C ("but TimesFM skips") → B (demo Sheets) → B (cytat z bloga) → A (wykres best/worst case) → D (cytat: czynniki) → B (Claude Code) → B (Sheets/BigQuery) → A → C (CTA "link w przypiętym komentarzu").

## Warstwy (od dołu)

1. **Tło**: jasne (A, D) albo ciemne rozmyte (B); twarz tylko w A i C.
2. **Karta**: okno macOS (3 kropki, pasek adresu z domeną), zaokrąglone rogi, cienka obwódka w kolorze akcentu, miękki cień. W środku zrzut strony albo nagranie ekranu, które jest odtworzone (terminal pisze sam, kursor klika).
3. **Ruch w karcie, zsynchronizowany ze słowem**:
   - marker (niebieski, półprzezroczysty) przesuwa się po cytowanym zdaniu w chwili, gdy słowo pada ("100 billion time-points", "holidays");
   - ramki (pomarańczowe) na kolumnach tabeli;
   - etykiety "best case" i "worst case" wyskakują na wykresie;
   - licznik liczby (rolka 1→9→100 billion) w pigułce nad kartą;
   - przewinięcie albo zoom na fragment.
4. **Napisy**: 1-3 słowa, małe litery jak w zdaniu (nie CAPS), gruby sans. Czarne na jasnym tle, białe na ciemnym. **Słowo kluczowe innym krojem** (italic, niebieskie: "Wikipedia", "Google Sheets", "TimesFM") albo samym kolorem ("future", "billion"). Słowo, które jeszcze nie padło, stoi szare (podgląd), mówione robi się pełne.
5. **Tytuł-hook** (0-3,4 s): 2 linie u góry. Pierwsza z kolorowym logo marki, druga biała italic na niebieskim boksie, który wjeżdża wipe'em. Potem znika, a jego miejsce zajmuje etykieta sekcji ("It's Called" w niebieskim boksie).
6. **Dźwięk**: whoosh na starcie (-13,9 dB w pierwszych 0,1 s). Podkład gra cały czas (w przerwie mowy -23 dB, mowa ~-17 dB, czyli ~6 dB pod głosem; nigdzie nie ma ciszy < -45 dB). Głośność całości -15,9 LUFS.

## Logika wyboru (co mówi, to widać)

- Każde zdanie z rzeczownikiem, który da się pokazać (produkt, liczba, źródło, narzędzie), dostaje **dowód z prawdziwego źródła**: repo, blog, Trends, demo. Stocku nie ma ani jednego ujęcia.
- Liczba wypowiedziana na głos jest jednocześnie podświetlona w cytacie i powiększona w liczniku.
- Twarz wraca w pełnym kadrze tylko na zwrocie myśli i na CTA. Przez resztę czasu siedzi w boksie pod dowodem.
- Wyliczanka = jedna karta i podświetlenie słowo po słowie (weather → promotions → holidays).

## Co z tego mamy, czego nie mamy (pipeline 2026-10-31)

| element | u nas | luka |
|---|---|---|
| karta-okno ze zrzutem strony, przewinięcie do cytatu, marker | **jest** (`gfx` typ `web`: `webshot.mjs` + `render.mjs`) | 9:16 od 2026-10-31: zoom na cytat (`vZoom`) |
| układ split (karta u góry, twarz w boksie na dole) | **jest od 2026-10-31** (`web` + `canvas: "v"`, `layout: "split"`) | — |
| karta pełna na ciemnym tle w 9:16 | **jest od 2026-10-31** (`layout: "full"`) | jasne tło (układ D): później |
| napisy: słowo przed wypowiedzeniem szare | nie (cała grupa biała, mówione w akcencie) | **etap 2**: klucz planu |
| napisy małymi literami, słowo kluczowe innym krojem | CAPS Montserrat, akcent kolorem | etap 2 |
| licznik liczby | **jest** (`count`) | w 9:16 nad kartą: etap 3 |
| twarz ciasno na zwrocie myśli | **jest** (punch, `zoom_every_cut`) | nic |
| podkład ~6 dB pod głosem, whoosh na wejściu karty | **jest** (`music_duck`, `CARD_WHOOSH`) | nic |
| b-roll | stock z Pexels po słowie kluczowym | w tym wzorcu dowód > stock; z kartami `web` stock schodzi na drugi plan |
