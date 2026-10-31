# Teardown: Norbert Bodziony (6 shortów) + Taher Shabaan (FB reel)

Źródła: YouTube Shorts Norberta Bodzionego (afC6qx6GHlw, OpBG1d1GQXk, L7FNtzmfwUY, 8czAAAim5G8, W2-b709Ds54, COMgWgcgHBk) i reel FB Tahera Shabaana (wskazane przez Kamila 2026-10-31). Więcej reeli z FB wymaga logowania: nie pobierane.

Metoda: sheety 2 fps oraz pełnorozdzielcze klatki (30 fps) w miejscach zmian. Każdy klaster cięć z `scenes.txt` obejrzałem klatka po klatce. Do tego analiza audio (RMS, płaskość widma, autokorelacja basu) i pomiar skali tła ORB/RANSAC (zoom twarzy). Współrzędne w px dla kadru 1080x1920, błąd ok. ±10 px. Czego nie dało się sprawdzić bez odsłuchu, oznaczam [NIEPEWNE].

Zestaw (daty 2026-10-15..30):
- Norbert, 3 explainery: 8cz (42 s), afC6 (30 s), COM (27 s).
- Norbert, 3 sketche POV: L7F (14 s), OpBG (13 s), W2 (10 s).
- Taher, FB: taher1 (39 s).

## 0. Memy (najważniejsze, uczciwie)

W tych 7 materiałach nie ma klasycznych memów. Nie znalazłem szablonów (Drake, Wojak itd.), reaction images ani clipów, fragmentów filmów ani meme-dźwięków. Sprawdziłem wszystkie klatki co 0,5 s i każdy klaster cięć. Overlay krótszy niż 0,5 s bez cięcia mógł mi umknąć.

Jako "znane referencje" występują:
- naklejki marek i symboli: ikony Adobe Ps/Pr/Ae/Lr/CC, logo Claude, flaga Korei Płn., nagrobek "RIP DAY TRADERS";
- rolling counter "16000000";
- pasjans na monitorze jako puenta sketcha W2;
- memiczne frazy korporacyjne w dialogach sketchy ("jak rodzina", "udziały zamiast pensji", "Pana CV napisało AI") — tylko mowa i napis, bez obrazka.

Dla pipeline: slot "sticker brandowy/symbol" ma tu realny wzorzec. Slot "meme/reaction clip" nie ma żadnego. Jeśli Kamil chce wzorców memów, trzeba zrobić osobny research na kanałach, które ich używają.

## 1. Osie czasu

Skróty: face-full = twarz na cały kadr. Split = góra ok. 43% (0-840 px) dowód, dół twarz.

### 1.1 Norbert 8czAAAim5G8, "Pakiet Adobe całkowicie za darmo!?" (42 s, 30 fps, 19k views, -9,1 LUFS)

| t (s) | warstwa/efekt | linia | uwagi |
|---|---|---|---|
| 0.0-0.4 | face-full, zoom-out snap skala 1.20 -> 1.00 w 0.4 s (zmierzone) | "Jeden programista zrobił właśnie darmową wersję…" | napis 1 słowo, pop-in |
| 0.4-3.2 | stickery Ps, Pr, Ae, Lr (+ CC wstawione w środek ok. 2.5); rząd lewy-górny y~400, ikona ~125 px, odstęp ~200 px, nowa co 0.5 s, rząd się recentruje | "…całego pakietu Adobe." (Adobe @2.74) | zwykły overlay, bez maski głowy |
| 3.10-3.35 | flash: pomarańczowy light-leak od lewej -> 2 kl. czystej bieli -> twarde cięcie | "Adobe." -> "Sam w kilka dni" | ok. 0.25 s; szum szerokopasmowy (płaskość 0.45) [NIEPEWNE: whoosh] |
| 3.37-5.33 | face-full po cięciu, skala 1.03 -> 1.15 (0.07/s) | "Sam w kilka dni, za pomocą AI." | |
| 4.40-5.33 | logo Claude (pomarańczowy sunburst, zaokrąglony kwadrat ~250 px) wynurza się zza głowy w górę + fade-in ~0.4 s; dół zasłonięty głową | "za pomocą AI." | AI = Claude; wchodzi 0.9 s przed "Opusa" |
| 5.33 | twarde cięcie do split: góra UI aplikacji Claude | "Korzystał z Opusa 5.5" | twarz skala ~0.75 vs full; gradient ~100 px na szwie; napis na szew y~918 |
| 6.97-11.3 | góra: strona "Twelve apps. One craft." + pasek 12 ikon (screen recording z kursorem) | "i od zera napisał 7 programów w Adobe. Wszystko jest darmowe, legalne i z otwartym kodem." | |
| 11.4-14.8 | PhotoCraft (klon Photoshopa), potem repo GitHub | "Projekt w kilka dni zebrał ponad 40 tysięcy gwiazdek na GitHubie." | liczba udowodniona ekranem repo |
| 14.9-17.9 | lista VectorCraft/PhotoCraft/PdfCraft, niebieskie zaznaczenie tekstu "Photoshop" | "Działa na Macu, Windowsie oraz przeglądarce." | |
| 18.17-20.0 | edytor wideo (FilmCraft, timeline) | "Otwiera twoje pliki PSD i ma większość narzędzi programów Adobe." | |
| 20.03-21.2 | face-full, skala 1.04 -> 1.11 w 1 s | "Ale to nie jest najważniejsza rzecz." | mocny push |
| 21.27-28.47 | promo Adobe Firefly Boards z kursorem (obcy produkt) | "Nie użył ani jednej linijki kodu Adobe. Patrzył, jak działa każde narzędzie i kazał AI odtworzyć je kompletnie od zera. Ale nie zatrzymał się tylko na Adobe." | 7 s jednej sceny |
| 29.1-32.8 | karty CADCraft/GridCraft/DeckCraft/WordCraft (zoomowany screen) | "Na stronie projektu są już darmowe odpowiedniki Worda, Excela czy PowerPointa." | |
| 32.8-40.0 | znów "Twelve apps. One craft." + kolaż | "Jeden człowiek z AI otwarza programy… Pytanie brzmi, jaka aplikacja będzie następna?" | |
| 40.03-41.8 | face-full, 1.04 -> 1.15 | "Zaobserwuj po więcej newsów z AI." | CTA mówione, brak end-card |

### 1.2 Norbert afC6qx6GHlw, "Binance shakowany!!" (30 s, 29.97 fps, 1.5k views, -9,4 LUFS)

| t | warstwa/efekt | linia | uwagi |
|---|---|---|---|
| 0.0-0.4 | face-full, zoom-out snap 1.20 -> 1.00 | "Korea Północna ukradła…" | |
| 0.4-1.4 | flaga Korei Płn. ~565 px szer., y~440-800, ZA głową, dryf w dół ~40 px/0.6 s | "Północna ukradła ponad" | |
| 1.5-3.0 | gigant "6 miliardów" (biały bold ~140 px, x 132-939, środek y~640) na twarzy + zwykły napis dolny | "6 miliardów dolarów w 20 minut." | stat jako headline |
| 3.17-3.37 | flash | | |
| 3.4-5.5 | karta (artykuł PL o ataku na Binance) na ciemnym tle z siatką, blur-in ~0.2 s, ~865 px szer., środek y~955, rounded ~30 px, cień | "Okradli Binance, czyli największą giełdę na świecie." | napis y~1210 (63%) |
| 5.5-5.7 | flash (karta -> twarz) | | |
| 5.7-9.3 | face-full 0.97 -> 1.05 | "I jest to ponad dwa razy więcej niż hakerzy ukradli przez cały poprzedni rok." | |
| 9.28-13.0 | stock: Ziemia nocą z sieciami | "Firmy, które śledzą przelewy krypto, sprawdziły gdzie tak naprawdę poszły te pieniądze." | cięcie bez flasha |
| 13.0-14.9 | karta TRM "North Korea Steals USD 6.36 Billion…", lekki tilt 3D | "I wszystko prowadzi do Korei Północnej," | |
| 15.0 | flash (karta -> karta) | | |
| 15.1-18.5 | karta FBI PSA ($1.5B Bybit hack), tilt ±~5° | "która rok wcześniej ukradła ponad 1,5 miliarda dolarów z giełdy Bybit." | napis z cieniem na karcie |
| 18.5-18.8 | flash | | |
| 18.8-22.2 | face-full 0.97 -> 1.02 | "I pomimo, że połowa środków została zablokowana, to zrobili to za późno." | |
| 22.26-24.5 | karta posta X Binance | "Binance obiecuje pokryć całość z własnej kieszeni." | |
| 24.5-24.6 | flash | | szum 0.36 |
| 24.7-28.4 | karta BBC (wykres rozmiaru hacków) | "A wszystko zaczęło się od tego, że hakerzy włamali się na laptopa jednego z inżynierów." | |
| 28.4-29.6 | flash -> face-full | "Obserwuj po więcej newsów." | szum 0.43 |

### 1.3 Norbert COMgWgcgHBk, "OpenCode został zhakowany!!" (27 s, 30 fps, 7.7k views, -8,8 LUFS)

| t | warstwa/efekt | linia | uwagi |
|---|---|---|---|
| 0.0-1.6 | split od klatki 0. Góra: licznik czerwonych cyfr 4333300 -> 10833300 -> 16000000 (bez separatorów, ~110 px, y~465, motion blur, start biały z obrysem -> czerwony); pod spodem rozmyte karty (mail + tweet) | "16 milionów użytkowników właśnie zostało schakowanych." | liczenie ~1.0 s |
| 2.97-3.17 | flash | "OpenCode," | |
| 3.2-7.9 | góra: wordmark "opencode" (pixel-font) + zrzut terminala | "…popularna aplikacja do kodowania, przyznała, że API klucze ich użytkowników wyciekły." | wordmark rośnie |
| 8.0-12.2 | stos 3 kart (mail "Action Required: Potential provider key breach" + 2 tweety), siatka | "Tysiące osób obudziło się z gigantycznymi rachunkami za tokeny AI, których sami nie użyli." | |
| 12.2-12.4 | flash | | |
| 12.4-13.5 | żółte tło halftone, pochylony zrzut UI ("Fixing audio s…") z zoomem | "OpenCode twierdzi, że" | [NIEPEWNE: jaki produkt] |
| 13.6-16.0 | karta tweeta OpenCode, żółty marker na "impacted 1.4% of OpenCode Console users" | "problem dotyczy tylko 1,5% ich userbase'u" | highlighter na kluczowej frazie |
| 16.2-16.4 | flash | | |
| 16.4-18.5 | b-roll: przewijany terminal agenta | "niemniej jednak jest to aż ćwierć miliona osób." | |
| 18.5-21.4 | face-full 0.97 -> 1.07; od 19.5 sticker OpenBot (fioletowy kwadrat z szkicowymi oczami ~290 px, y~320-800) ZA głową | "I właśnie dlatego budujemy OpenBota zupełnie inaczej." | własny produkt jako sticker |
| 21.4 | flash | | szum 0.44 |
| 21.5-24.6 | split, góra UI OpenBot (lista agentów "Cloud server") | "Twoje czaty, pliki i polecenia zostają u Ciebie, na Twoim komputerze." | |
| 24.7-26.6 | góra: karta profilu X Norberta z żółtym highlightem | "Pobierz OpenBota i chroń swoje dane." | film kończy się na twarzy, bez end-card |

### 1.4 Sketch L7FNtzmfwUY, "Rekrutacja w 2026 roku…" (14 s, 60 fps, 36k views, -9,8 LUFS)

Format: dwie kamery, shot/reverse-shot, cięcie na granicy kwestii. Cięcia: 2.47, 3.5, 5.63, 6.6, 7.27, 8.07, 10.17, 12.1, czyli 8 cięć / 14 s (5.7 na 10 s, ASL 1.55 s). Ujęcia statyczne, bez muzyki i SFX.
- Tytuł "POV: Rekrutacja 2026r." od 0.0 do końca: biały bold ~60 px, 2 linie, środek y~405, bez ramki.
- Napisy: kondensowane bold WERSALIKI ~45 px, biały z czarnym obrysem, środek y~1500 (78%). Cała kwestia w jednej linii (3-5 słów), aktywne słowo w niebieskiej zaokrąglonej podkładce (#0070F8) przesuwanej słowo po słowie.

| t | ujęcie | linia |
|---|---|---|
| 0-2.5 | ona | "Na pensję niestety nie mamy, ale dajemy udziały." |
| 2.5-3.5 | on | "A ile one są warte?" |
| 3.5-5.5 | ona | "Na razie zero, ale w przyszłości miliardy." |
| 5.5-6.5 | on | "Kiedy są podwyżki?" |
| 6.5-7.3 | ona | "Raz w roku." |
| 7.3-8.0 | on | "A dokładnie kiedy?" |
| 8.0-10.0 | ona | "Właśnie minęły. Pana CV napisało AI." |
| 10.0-12.0 | on | "No tak, a kto je u Was przeglądał?" |
| 12.0-14.0 | ona | "Też AI, dlatego Pan tutaj jest." |

Bez CTA ani outro, naturalna pętla do 0.0.

### 1.5 Sketch OpBG1d1GQXk, "Rekrutacja w 2026 roku…" (13 s, 60 fps, 49k views, -10,0 LUFS)

Ten sam format. Tytuł "POV: Typowa rekrutacja w 2026 r." (y~405). 6 cięć / 13 s (4.6 na 10 s, ASL 1.9 s). To najwyższe views w zestawie przy najprostszej obróbce.
- 0-1.8 ona: "W tej firmie jesteśmy jak rodzina."
- 1.8-3.9 on: "Czyli jak będę miał problem, to mi pomożecie?"
- 3.9-7.1 ona: "Nie, czyli w święta też Pan pracuje. Pana CV napisał AI."
- 7.1-9.0 on: "No tak, a kto je u Was przegląda?"
- 9.0-11.9 ona: "Też AI, dlatego Pan tutaj jest. Pensja jest do negocjacji."
- 11.9-12.6 on: "To negocjujmy."
- 12.6-13.3 ona: "Tylko w dół." (puenta w ostatnich 0.7 s)

### 1.6 Sketch W2-b709Ds54, "Szef znowu coś od Ciebie chce…" (10 s, 60 fps, 16k views, -9,1 LUFS)

Tytuł: lila pill (#D0A0F0, zaokrąglony, biały bold z cieniem, 2 linie, środek y~570, x 163-917). Napisy jak w L7F.

| t | ujęcie | linia / efekt |
|---|---|---|
| 0.0-3.7 | szeroki plan open space | "Marta, chodź tutaj szybko, pilne!!" (0.5-2.9); 2.5-3.5 ona wstaje i biegnie (whip-pan, motion blur) |
| 3.7-5.4 | jego stanowisko, zgarbiony przy monitorze | "Na kiedy szefie?" |
| 5.4-6.27 | ona stoi, on z głową na ręce | "Jak się w to gra." |
| 6.27-10.2 | POV szefa: monitor z pasjansem, ręka na myszce, 3.9 s statyki bez dialogu | puenta wizualna; audio spada do -30..-44 dBFS (sam pokój), brak SFX i muzyki |

### 1.7 Taher FB taher1, "Claude can now do literally anything!!!" (39.2 s, 25 fps, 37k views, -14,1 LUFS)

Stałe elementy:
- Panel górny 1080x840: animacje w stylu HTML, kremowa paleta, pixel-art pomarańczowy maskotek [NIEPEWNE: wygląda jak maskotka Claude Code].
- Dół: twarz 1080x1080, twardy szew y=840 (bez gradientu).
- Napis: 2-3 słowa, biały bold ~40 px w ciemnej półprzezroczystej zaokrąglonej podkładce (#383838, ok. 230x75 px dla 2 słów, promień ~14), środek ZAWSZE y~838 (także gdy twarz jest ukryta), małe litery jak w mowie.
- Język EN, 213 wpm.

| t | warstwa | linia |
|---|---|---|
| 0.0-1.6 | split: trzy monitory + maskotek; 0.4 nagrobek "RIP DAY TRADERS" spada na monitory | "Claude just killed day traders" |
| 1.64-4.64 | full-screen animacja (twarz ukryta): symulacja "Your trade" z chmurą ścieżek, paski Target/Stop/Neither | "and that's because you can now run full-on market research right inside Claude completely for free" |
| 4.64-6.72 | monitor TSLA, karta "BUY TSLA" ze stemplem PAPER | |
| 6.72-9.6 | "day-trader-skill", siatka 11 skilli; tagi FREE / No API key wskakują | "and it's not one skill it's 11 each with its own job" |
| 9.6-11.88 | split: siatka miniatur wykresów + czerwona linia skanera | "one scans thousands of charts for setups" |
| 11.88-17.96 | full-screen: watchlista newsów -> entry bar-by-bar -> exit plan | "one tracks breaking news the second it drops and one helps you spot the entry levels everyone else is watching" |
| 17.96-19.96 | split: lista skilli, wybrany "Time Machine" | "But the wild part is the backtesting skill" |
| 19.96-27.16 | full-screen: backtest, licznik replays 0 -> 10,000 | "before you put a single dollar on the line it runs your strategy against years of real market history…" |
| 27.16-34.04 | split ze stockami i zrzutami: wykres BTC, rozmyty order-book (rack-focus), tabela transakcji Kongresu, UI Claude "Basket placed", Buy/Sell z kursorem | "it won't trade for you and it can't promise you a win because nothing can…" |
| 34.04-37.0 | split: okno Claude, URL repo wpisywany znak po znaku + "install skill" | "to set it up paste this link into Claude and say install skill" |
| 37.0-39.2 | góra: biała karta, czarne WERSALIKI ~70 px "NOW COMMENT "TRADE" AND I'LL SEND YOU THE LINK" | "now comment trade and I'll send you the link" (CTA komentarz-za-link, bez pętli) |

## 2. Katalog memów / referencji

Szablonów memów brak, poniżej wszystko, co działa jako znana referencja. "Audio własne": nie wykryto w żadnym przypadku (poza W2: cisza).

| film | t (s) | co | linia | tryb | czas |
|---|---|---|---|---|---|
| 8cz | 0.4-3.2 | ikony Adobe Ps/Pr/Ae/Lr/CC | "…całego pakietu Adobe." | rząd lewy-górny, y~400, wskakują co 0.5 s | 2.8 s |
| 8cz | 4.4-5.33 | logo Claude | "za pomocą AI." | wynurza się zza głowy + fade 0.4 s | 0.9 s |
| 8cz | 21.3-28.5 | promo Adobe Firefly (screen z kursorem) | "Nie użył ani jednej linijki kodu Adobe" | góra split | 7.2 s |
| afC6 | 0.4-1.4 | flaga Korei Płn. | "Korea Północna ukradła…" | za głową, y~440-800, dryf w dół | ~1.0 s |
| afC6 | 1.5-3.0 | napis "6 miliardów" | "…ponad 6 miliardów dolarów w 20 minut." | na twarzy ~140 px | 1.5 s |
| afC6 | 15.1-18.5 | karta FBI PSA (autorytet jako dowód) | "…1,5 miliarda dolarów z giełdy Bybit" | karta na siatce, tilt 3D | 3.4 s |
| COM | 0.0-1.6 | licznik "16000000" | "16 milionów użytkowników…" | góra split | 1.6 s |
| COM | 19.5-21.4 | logo OpenBota (własny produkt) | "budujemy OpenBota" | za głową, y~320-800 | 1.9 s |
| FB | 0.4-1.6 | nagrobek "RIP DAY TRADERS" | "Claude just killed day traders" | spada na monitory w panelu górnym | ~1.2 s |
| W2 | 6.27-10.2 | pasjans na monitorze | "Jak się w to gra." | pełny kadr POV, statyk, cisza | 3.9 s |
| L7F/OpBG | cały | frazy: "jak rodzina", "udziały zamiast pensji", "podwyżki raz w roku/właśnie minęły", "Pana CV napisało AI", "Tylko w dół" | dialog | tylko mowa + napis | n/d |

## 3. Wzorce między filmami

**Layouty**
- Explainery Norbert: face-full tylko ok. 11% czasu (8cz), 38% (afC6), 11% (COM). Reszta to dowód w trzech formach:
  - split top-43% (8cz 79%, COM 89% czasu),
  - karta na ciemnej siatce w pełnym kadrze, twarz ukryta (afC6, 6 kart),
  - b-roll stock (afC6 Ziemia, COM terminal).
- FB: animacja pełnokadrowa (twarz ukryta) ok. 56% czasu, split ok. 44%.
- Sketche (3): 100% live action, bez proofu.
- Dowód to prawie zawsze realny artefakt (strona, repo, tweet, mail, artykuł, wykres, zrzut aplikacji). Abstrakcyjny stock tylko 2x (Ziemia, rozmyty order-book).

**Tempo**

| film | zdarzeń wizualnych | na 10 s | ASL | wpm |
|---|---|---|---|---|
| 8cz | 11 klastrów (ok. 17 zmian treści) | 2.6 (ok. 4.0) | 3.8 s (ok. 2.5 s) | 189 |
| afC6 | 8 (ok. 13) | 2.7 (ok. 4.3) | 3.7 s | 196 |
| COM | 7 (ok. 12) | 2.6 (ok. 4.5) | 3.8 s | 164 |
| L7F | 8 | 5.7 | 1.55 s | 210 |
| OpBG | 6 | 4.6 | 1.9 s | 222 |
| W2 | 3 + whip-pan | 3.0 | 2.5 s | 78 |
| FB | 13 + animacje wewnętrzne | 3.3 | ok. 3.0 s | 213 |

Przerwy między zdaniami w explainerach to 0.04-0.16 s (z `words.srt`), czyli twarde jump-cuty po oddechu.

**Napisy**
- Norbert explainer:
  - biały bold sans (Inter/SF-podobny) ~56 px, miękki cień, bez podkładki, bez highlightu słowa;
  - sentence-case z interpunkcją, 1-3 słowa (8cz ok. 1.4 słowa/grupa, hold 0.27-0.55 s);
  - pop-in skala ~0.8 -> 1.0 w 3-4 klatkach (0.1 s);
  - pozycja: face-full i karty y~1215 (63%), split 8cz y~918, split COM y~835.
- Sketche Norbert: wersaliki ~45 px z obrysem, niebieska podkładka pod aktywnym słowem, 1 linia, y~1500.
- Taher: 2-3 słowa w ciemnej podkładce na szwie y~838.
- Hook-tekst: sketche "POV: …" od klatki 0. Explainery: pierwsze zdanie jako napis plus stat-gigant (afC6) albo licznik (COM).

**Zoom i ruch**
- Zoom-out snap na starcie: 8cz i afC6, 1.20 -> 1.00 w 0.4 s (zmierzone).
- Wolny push-in na każdym segmencie face-full, reset po cięciu:
  - 8cz: 1.03 -> 1.15 (0.07/s), 1.04 -> 1.11 w 1 s, 1.04 -> 1.15 w 1.5 s;
  - afC6: 0.016-0.025/s;
  - COM: 0.02-0.04/s;
  - start każdego segmentu 0.97-1.04.
- Karty: blur-in ~0.2 s i kołyszący tilt 3D ±~5°.
- Brak shake'ów, speed-rampów i freeze-frame w żadnym z 7 filmów.

**Przejścia**
- Flash light-leak: pomarańcz -> biel, ok. 0.2-0.27 s, 2 klatki czystej bieli, cięcie w szczycie.
  - 8cz 1x; afC6 6x (3.2, 5.6, 15.0, 18.7, 24.6, 28.4); COM 4x (3.0, 12.3, 16.3, 21.4); FB i sketche 0.
  - Stosowany przy wejściu/wyjściu z proofu i między kartami, nie przy każdym cięciu (8cz 5.33, afC6 9.28 i 22.26 to cięcia twarde).

**Audio**
- Głośność: Norbert -8,8..-10,0 LUFS, FB -14,1 LUFS.
- Podłoga ciszy: explainery min ok. -27..-31 dBFS, sketche -35..-46, FB -53.
- W trzech explainerach jest ciągła warstwa i peak autokorelacji basu przy lagu ~0.75 s (0.23-0.28). Prawdopodobnie ta sama podkładka ok. 80 BPM, poziom <= -27 dBFS (>=15 dB pod głosem) [NIEPEWNE: bez odsłuchu].
- SFX: szum szerokopasmowy (płaskość 0.33-0.45 vs p90 tła 0.29) pasuje do 5 z ok. 11 flashy: 8cz 3.1; afC6 5.45, 24.4, 28.35; COM 21.25 [NIEPEWNE: whoosh]. Pop, ding i record-scratch nie wykryte. Meme-dźwięków brak. Puenta W2 to cisza 3.9 s.

**Elementy graficzne**
- Emoji, strzałki, kółka: 0.
- Wskaźniki uwagi: żółty marker na frazie w screenshotcie (COM 2x), zaznaczenie tekstu w screen recordingu (8cz).
- Stickery brandowe: 8cz 5 ikon + logo, afC6 flaga, COM logo. Za maską głowy: flaga, logo Claude, OpenBot.

**Zakończenia**
- Norbert: mówione CTA, 1.5-2.0 s face-full, bez end-card i pętli.
- Taher: karta CTA 2.2 s z komentarzem-za-link.
- Sketche: bez CTA, puenta w ostatniej kwestii.

## 4. Mechaniki, ranking (wpływ na retencję x łatwość automatyzacji)

Wpływ 1-5 to moja ocena z obserwacji, danych retencji tych filmów nie mam [NIEPEWNE]. Łatwość 1-5 pod pipeline JSON -> HTML + ffmpeg.

| # | mechanika | wpływ | łatwość | parametry (1080x1920) |
|---|---|---|---|---|
| 1 | Napisy 1-2 słowa z pop 0.1 s | 5 | 5 | Inter/SF Bold ~56 px biały, cień ~0 2 6 rgba(0,0,0,.5), środek x=540, y=1215. Grupa 1-3 słowa (śr. ~1.4), hold = timing słowa 0.27-0.55 s. Skala 0.8 -> 1.0 w 3-4 kl. Sentence-case z interpunkcją, bez podkładki. W split napis na szwie (y 835-920) |
| 2 | Karta dowodu na słowo-klucz (tweet, artykuł, repo, zrzut) | 5 | 5 | HTML card ~865 px szer. (80%), środek y~955 (pełny kadr) lub w górnych 840 px (split), zaokrąglenie ~30 px, cień, tło #1A1A1A + siatka. Wejście blur 8 px -> 0 w 0.2 s, tilt 3D ±5°. Trzymanie 2-4 s (cały span zdania). Źródło obce i wiarygodne (BBC, FBI, X) |
| 3 | Split: dowód 0-840, twarz dół | 5 | 4 | Góra 43% (840 px), twarz skala ~0.75 vs full, gradient 60-100 px na szwie (Norbert) lub twardy szew (FB), napis na szwie |
| 4 | Hook od klatki 0: teza + liczba | 5 | 4 | Zoom-out snap 1.20 -> 1.0 w 0.4 s. Gigant "6 miliardów" y~640, ~140 px, biały bold, 1.5 s. Albo licznik czerwonych cyfr ~110 px, y~465, 0 -> N w ~1.0 s |
| 5 | Ciasne jump-cuty | 4 | 5 | Przerwa między zdaniami 0.04-0.16 s, 165-196 wpm. ASL sketcha 1.5-1.9 s, explainera ok. 3.5 s |
| 6 | Flash light-leak przy wejściu/wyjściu proofu | 4 | 5 | 0.2-0.27 s, pomarańcz (#FF9A4D) -> biel, szczyt 2 kl., cięcie w szczycie, reset zoomu pod spodem. 2-6 flashy / 30 s, nie na każde cięcie |
| 7 | Wolny push-in na face-full z resetem | 3 | 5 | +0.015..0.07/s do ok. 1.15, start 0.97-1.04 po każdym cięciu; zoom-out snap na t=0 |
| 8 | Sticker symbolu/marki na nazwie własnej | 4 | 3 | Rząd ikon y~400, ~125 px, odstęp ~200 px, stagger 0.5 s. Albo pojedynczy sticker 250-300 px nad głową (y~320-800), wynurza się zza głowy 0.4 s (wymaga maski sylwetki), flaga ~565 px. Wchodzi 0.5-1 s przed lub przy słowie |
| 9 | Rolling counter statystyki | 3 | 4 | Cyfry bez separatorów, czerwone (~#FF2A2A), ~110 px, y~465, ok. 1 s, motion blur na starcie |
| 10 | Highlighter na frazie w screenshocie | 3 | 4 | Żółty marker na kluczowej liczbie, wchodzi razem z wypowiedzią (COM 14.0-15.5) |
| 11 | CTA końcowe | 3 | 5 | Norbert: 1.5-2.0 s face-full z napisem "Obserwuj po więcej newsów". Taher: biała karta 2.2 s, wersaliki ~70 px |
| 12 | Podkład muzyczny ok. 80 BPM | 2 | 4 | <= -27 dBFS (>=15 dB pod głosem) [NIEPEWNE]. Master -9..-10 LUFS (Norbert) vs -14 (FB) |
| 13 | Sketch POV: tytuł + shot/reverse-shot + napisy-wersaliki | 4 (views 16-49k, najwyższe) | 3 (wymaga zdjęć) | Tytuł 60 px y~405 lub lila pill y~570. Napisy ~45 px, y~1500, podkładka #0070F8 po aktywnym słowie, 1 linia/kwestia. Cięcie na granicy kwestii. Puenta w ostatnim 0.7-1 s lub cisza 3.9 s |
| 14 | Slot pop-culture/meme | brak wzorca w zestawie | — | Zaplanować pusty slot overlay w JSON-ie (lokalny asset, tryb: za-głową / rząd lewy-górny / pełny kadr, in/out po słowach). Obsłuży logo i flagi (obserwowane) oraz ewentualne memy. Bez parametrów audio memów |

Uwaga implementacyjna: zdarzenia explainera da się zapisać jako `{t_in, t_out, kind: card|split|sticker|counter|flash|highlight, asset, anchor_word}`. Tylko zmiana layoutu (face-full <-> split <-> card-full) i flash zmieniają kompozycję. Zoom i napisy nakłada się osobno na każdy segment.

## 5. Czego nie zweryfikowano
- Muzyka i whoosh: tylko pośrednio (statystyka widma), bez odsłuchu.
- Retencja i ranking wpływu: moja ocena, nie dane platformy.
- Skala twarzy w FB i sketchach (kadr statyczny/ręczny) nie mierzona.
- Produkt w żółtym halftone clipie (COM 12.4-13.5).
- Czy sticker za głową to maska per klatka (wygląda na tak, bez dostępu do projektu).
