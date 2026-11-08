# Wzorzec: top shorty AI / tech / biznes, 6 twórców, 30 shortów (rozbiór 2026-11-05)

Źródło: 6 kanałów YouTube wybranych po liczbach (tabela niżej), z każdego 5 najczęściej oglądanych shortów z ostatnich 12 miesięcy (od 2025-11-05): **18 rdzeniowych** (3 na twórcę, nazwane w tabeli) + **12 dodatkowych** (miejsca 4-5, dobrane po dodatku Kamila o wystarczalności danych). Pliki lokalne `render/ref/shorts/top/<twórca>/<id>/v.mp4` + `v.info.json` (gitignorowane, razem 753 MB razem z klatkami analizy, limit 4 GB/6 GB nietknięty), tylko do nauki mechaniki. Z materiału nic nie uruchamiano; skrypty analizy leżą poza repo i czytają pliki jako dane.
Bierzemy mechanikę montażu, nie grafikę, maskotki, markę ani treść. W materiale są cudze loga, zrzuty tweetów, twarze osób trzecich i klipy: u nas jak dotąd (ADR-0008) tylko lokalnie, bez wstawiania.
Pozostałe wzorce: `REF-shorts-zackshutt.md`, `REF-shorts-breakingbreach.md`, `REF-shorts-memes.md`, `REF-shorts-proof-cards.md`, `RESEARCH.md`. Reguły Kamila (`ZASADY-KAMILA-SHORTY.md`) zawsze wygrywają. Szymon Negacz (film długi) poza zakresem.
Dźwięk: nie słuchałem, tylko mierzyłem. Wszystko o muzyce i SFX jest wnioskiem z pomiarów i oznaczone [NIEPEWNE].

## Źródło: twórcy i shorty

Dane o kanałach z `yt-dlp` 2026-11-05 (YouTube zaokrągla subskrypcje i wyświetlenia). Mediana wyświetleń = mediana z listy zakładki Shorts pobranej tym samym narzędziem (n w tabeli; to cała lista widoczna dla narzędzia, nie okno 12 miesięcy, bo lista nie podaje dat).

| twórca | kanał | subskrypcje | język | shortów na liście (n) | mediana wyświetleń | najwyższy short (12 mies.) | po co wzięty |
|---|---|---|---|---|---|---|---|
| Varun Mayya | @VarunMayya | 1,19 mln | en | 300 | 89 tys. | 7,76 mln | tech/AI newsy, narracja na materiale |
| Matt Wolfe | @mreflow | 1,03 mln | en | 300 | 14 tys. | 1,99 mln | AI i tech newsy, twarz + panel |
| Jeff Su | @JeffSu | 1,94 mln | en | 119 | 23 tys. | 233 tys. | AI produktywność, animowane wyjaśnienia |
| Ali Abdaal | @aliabdaal | 6,71 mln | en | 300 | 30 tys. | 1,69 mln | produktywność/AI (#ad), twarz + b-roll |
| Nate Herk | @NateHerk | 1,11 mln | en | 200 | 26 tys. | 247 tys. | automatyzacja AI / Claude Code, biznes |
| Adrian Kilar (PL) | UC5aRHitAgGy39hu7MCqdHEA | 154 tys. | pl | 115 | 45 tys. | 587 tys. | polski kanał AI/tech (jedyny z polskich, który ma Shorts z >100 tys. w ostatnich 12 mies.) |

Rowan Cheung odpadł: kanał `@RowanCheung` nie ma zakładki Shorts (yt-dlp: „does not have a shorts tab”). Jeff Su: jego najpopularniejszy short w ogóle (6,6 mln, „Unethical resume hack”) jest sprzed 12 miesięcy, więc nie wchodzi. Polskich kanałów AI sprawdzonych po liczbach: NetGonet (74,7 tys. subskr., top short 59 tys.), Aleks Szach (35,9 tys., spersonalizowane filmy wizytówkowe), Julia Jakubowska (9,2 tys.), Startuj AI (33,2 tys., 17 shortów, top 15 tys.), Beyond AI (7,4 tys.); tylko Adrian Kilar (154 tys.) ma shorty rzędu setek tysięcy.

### 18 shortów rdzeniowych (3 najpopularniejsze z 12 mies. na twórcę)

| twórca | id | data | wyśw. | x mediana | czas | fps | tytuł (skrót) |
|---|---|---|---|---|---|---|---|
| Varun Mayya | `4vIPxzPPweI` | 2026-05-05 | 7,76 mln | 87,2x | 115 s | 30 | This Is How Speed Streams From a Helicopter Wi |
| Varun Mayya | `KNWWZS4n1J8` | 2026-01-24 | 5,17 mln | 58,1x | 97 s | 30 | This Chinese Genius @xnzxnz  Built a Console T |
| Varun Mayya | `kAgRpHQlAFY` | 2026-01-25 | 1,80 mln | 20,3x | 64 s | 25 | Scientists Created 'Liquid Trees' and they're  |
| Matt Wolfe | `gC18kqOcCEI` | 2026-10-26 | 1,99 mln | 147,6x | 63 s | 30 | ANOTHER Flying Car? (Not Tesla / Not AI) |
| Matt Wolfe | `QzDCfJpVGN8` | 2026-06-08 | 1,01 mln | 74,7x | 104 s | 24 | Shopping Online Is About To Change Forever |
| Matt Wolfe | `Qy25rSEXpPQ` | 2026-06-18 | 339 tys. | 25,1x | 97 s | 30 | Midjourney Built What?!? |
| Jeff Su | `sfwax2dVPvI` | 2026-02-27 | 233 tys. | 10,1x | 57 s | 30 | When to use #ChatGPT, #Gemini, and #Claude |
| Jeff Su | `KS-p0e-KwBA` | 2026-03-26 | 156 tys. | 6,8x | 48 s | 30 | Claude Cowork: The #1 Thing To Know |
| Jeff Su | `Nfe5OCLeD38` | 2026-03-11 | 146 tys. | 6,4x | 52 s | 30 | NotebookLM is now bigger than Gemini |
| Ali Abdaal | `LE5uwaOvqEY` | 2025-11-21 | 1,69 mln | 56,4x | 80 s | 25 | My new favourite productivity gadget #ad |
| Ali Abdaal | `duDgVfn1lCk` | 2026-05-15 | 366 tys. | 12,2x | 59 s | 30 | Rating self-help & productivity books |
| Ali Abdaal | `OsQ4LK19KXw` | 2026-02-13 | 261 tys. | 8,7x | 8 s | 30 | Managing 3 girls in their 20s be like... |
| Nate Herk | `CV-k6rPJvJY` | 2026-10-14 | 247 tys. | 9,3x | 51 s | 30 | Claude has completely changed how I edit video |
| Nate Herk | `ezCmuRCAVXY` | 2026-10-20 | 192 tys. | 7,2x | 31 s | 30 | Claude Code + Blender = Insane 3D Renders |
| Nate Herk | `AUoYldwt_sA` | 2026-03-04 | 181 tys. | 6,8x | 157 s | 30 | How I Build $10,000 Apple-Style Websites with  |
| Adrian Kilar | `dQxAPuLEt6k` | 2025-11-05 | 587 tys. | 13,0x | 79 s | 25 | 3 prywatne ekrany w kawiarni! #ai #sztucznaint |
| Adrian Kilar | `t5pwlOjG_VY` | 2026-02-03 | 391 tys. | 8,7x | 52 s | 25 | AI coraz mniej „sztuczne”!!! Uwaga! #ai #sztuc |
| Adrian Kilar | `sqHedTHyT6U` | 2026-05-21 | 365 tys. | 8,1x | 104 s | 25 | Cyborgi stały się rzeczywistością. 😳 #ai #egzo |

### 12 shortów dodatkowych (miejsca 4-5)

| twórca | id | data | wyśw. | x mediana | czas | tytuł (skrót) |
|---|---|---|---|---|---|---|
| Varun Mayya | `lNTubupxkEM` | 2026-03-15 | 874 tys. | 9,8x | 49 s | This Guy Used ChatGPT To Build His Dog A Cance |
| Varun Mayya | `R2nesxy7uYU` | 2026-04-08 | 697 tys. | 7,8x | 64 s | Claude Mythos Is Finally Here - But Not For Yo |
| Matt Wolfe | `WXWFmwfo1JA` | 2026-10-16 | 175 tys. | 12,9x | 46 s | This Tesla Actually Flies (NOT AI) |
| Matt Wolfe | `dyrNQV0F3Zs` | 2026-10-22 | 160 tys. | 11,8x | 65 s | Personal Body Guard Robot - What could go wron |
| Jeff Su | `sEYbctQiycI` | 2026-05-20 | 53 tys. | 2,3x | 54 s | Google I/O 2026: 3 things you need to know |
| Jeff Su | `6PZCZWvNVHc` | 2026-04-02 | 50 tys. | 2,2x | 43 s | #claude Chat vs. Cowork: Biggest 3 differences |
| Ali Abdaal | `6R0QIkWyAdI` | 2025-11-05 | 217 tys. | 7,2x | 48 s | 3 Surprising Things I Learned As a New Dad |
| Ali Abdaal | `W8XNHsZWFSo` | 2026-04-02 | 207 tys. | 6,9x | 89 s | Claude's new features are insane #ad |
| Nate Herk | `0A3NGrPlp_w` | 2026-03-10 | 165 tys. | 6,2x | 112 s | Google's New Tool Just Solved A Major Claude C |
| Nate Herk | `7GTWAXCTy0o` | 2026-10-13 | 139 tys. | 5,3x | 91 s | I Built the Ultimate AI Board of Advisors |
| Adrian Kilar | `86wt-KaRv3c` | 2026-09-06 | 129 tys. | 2,9x | 101 s | "AI napisz Windowsa!" #ai #sztucznainteligencj |
| Adrian Kilar | `slDZd9O7hM8` | 2026-09-05 | 107 tys. | 2,4x | 73 s | GPT-6 i model 3D smoka 🥹 z Wiedźmina w 15 minu |

Uwagi do próby: (1) trzy shorty Ali Abdaala z top 3 to sponsorowane `#ad` (LE5uwaOvqEY), 8-sekundowy skecz (OsQ4LK19KXw) i recenzja książek (duDgVfn1lCk): to jego najpopularniejsze, ale nie typowy short „AI/tech”; (2) Kilar t5pwlOjG_VY to przemiana własnej twarzy w gwiazdy filmowe modelem AI (format nie do skopiowania, ale układ kadru mierzalny); (3) Varun Mayya i Matt Wolfe mają najbardziej zbliżony do „newsów AI” format; Jeff Su i Nate Herk to wyjaśnienia narzędzi. Pobrane pliki to 608x1080 (pionowe wideo 1080p w nomenklaturze YouTube = wysokość 1080), co przy limicie „max 1080p” jest maksimum; analiza klatek w 540x960.

## Metoda i granice pomiaru

- cięcia: `ffmpeg select='gt(scene,0.25)'` (też 0,15 i 0,4); długości ujęć z odstępów; **uwaga:** cięcia na tym samym tle (skok zoomu) i zmiany stanu elementów animacji tego progu nie przekraczają, więc `cięcia/s` zaniża tempo zmian (Jeff Su ma 0-1 cięcia w shorcie przy bardzo gęstej animacji);
- klatki 4 kl/s (540x960): detektor twarzy YuNet (`models/face_detection_yunet_2023mar.onnx`, ten sam co `face_track.py`), tesseract (eng, dla PL eng+pol) i whisper.cpp large-v3-q5 ze słowami;
- układ kadru z geometrii twarzy: **FULL** = twarz w górnej 62 % kadru, **LOW** = twarz niżej niż 0,62 H przy szerokości ramki >= 0,10 W (pas pod panelem albo kółko), **TINY** = ramka < 0,10 W, **NOFACE** = brak twarzy, a ten dzieli się na **GFX** (płaskie tło: dominujący kolor >= 40 % pikseli = diagram/UI/ekran/plansza) i **FOOT** (materiał filmowy). Gdy w kadrze jest twarz niżej i inna wyżej, bierzemy tę niższą (twórca w pasie, nie twarz z b-rollu);
- **walidacja detektora**: porównanie z kodowaniem wzrokowym (arkusze) hooków split: zgodność 16/18 shortów rdzeniowych (niezgodne: `CV-k6rPJvJY` i `dQxAPuLEt6k`). Detektor może mylić twarz twórcy z twarzą z b-rolla w FULL (stąd FULL i LOW traktuję jako przybliżenie, wizualne kodowanie jest nadrzędne tam, gdzie podaję „wizualnie”);
- napisy: OCR w 4 kl/s dopasowany do słów z whispera (linia, której >= 60 % słów pada w oknie -2 s...+1 s, to napis). Pokrycie OCR napisów waha się 8-94 % czasu mowy (stylizowane napisy gubi), więc **słów w grupie** i **pozycję** podaję z tego, co OCR złapał; tytuły, których słowa pokrywają się z mową, mogą trafić do „napisów” (jeden przypadek: `sfwax2dVPvI`);
- teksty na ekranie (czas widoczności): śledzenie linii OCR (podobieństwo >= 0,6 i pozycja y +-0,06) i grupowanie linii tej samej karty w blok. **OCR gubi tekst na tle wideo, więc czasy są dolną granicą**;
- obejrzane arkusze (kodowanie wizualne, tylko 18 rdzeniowych): A = pierwsze 5 s po 2 kl/s, B = reszta po 1 kl/s, oglądane do ok. 65 s. `OsQ4LK19KXw` (8 s) tylko A. Dalszych części B (powyżej 65 s) nie oglądałem, te odcinki są tylko liczbowe; dokładnej liczby obejrzanych arkuszy nie liczyłem;
- dźwięk: `ebur128`, `silencedetect -45 dB`, RMS co 50 ms poza oknami słów (poziom w przerwach względem mowy; impulsy >= 8 dB nad otoczeniem);
- baza porównawcza: **6 naszych shortów** przepuszczonych przez te same skrypty: 4 z `render/montaz/2026-11-04/out/` (s1_gotowe, s2_szlaban, s3_blizna, s4_jedno_zdanie) i 2 z `out_v2/shorts/` (s06_mutacje, s14_kto_sprawdza). Z `out_v2` tylko 2 z 18 (czas), więc to próbka orientacyjna.

## Liczby

### Per twórca (mediana z 5 shortów)

| miara | Varun Mayya | Matt Wolfe | Jeff Su | Ali Abdaal | Nate Herk | Adrian Kilar (PL) | nasze (n=6) |
|---|---|---|---|---|---|---|---|
| czas shorta [s] | 64 | 65 | 52 | 59 | 91 | 79 | 47 |
| słów/min | 207 | 203 | 197 | 274 | 266 | 166 | 143 |
| cięcia/s (scene>0,25) | 0,72 | 0,19 | 0,02 | 0,07 | 0,15 | 0,41 | 0,02 |
| ujęcie, mediana [s] | 1,1 | 4,3 | 23,9 | 9,5 | 4,9 | 1,7 | 21,4 |
| czas w FULL (twarz górą) | 18 % | 11 % | 2 % | 74 % | 11 % | 54 % | 90 % |
| czas w LOW (twarz w pasie/kółku) | 8 % | 88 % | 14 % | 1 % | 49 % | 11 % | 0 % |
| czas w GFX (płaska grafika, bez twarzy) | 27 % | 6 % | 73 % | 0 % | 0 % | 1 % | 6 % |
| czas w FOOT (materiał, bez twarzy) | 38 % | 5 % | 0 % | 0 % | 0 % | 13 % | 0 % |
| wejść w pełny ekran (>= 0,5 s) na 10 s | 2,64 | 0,41 | 0,57 | 0,00 | 0,55 | 1,38 | 0,24 |
| zdarzeń ruchu na 10 s (różnica klatek > 8) | 26 | 28 | 8 | 34 | 22 | 24 | 21 |
| napis: y modalne (% wysokości) | 0,74 | 0,94 | 0,74 | 0,72 | 0,58 | 0,50 | 0,74 |
| głośność [LUFS] | -15,2 | -20,5 | -17,1 | -14,9 | -14,0 | -14,1 | -14,9 |

Zdarzenia ruchu = liczba kroków 0,25 s, w których średnia bezwzględna różnica klatek (54x96, szarość) przekracza 8 poziomów: mierzą ruch obrazu (kamera, b-roll, gesty, animacje), nie liczbę cięć; ciasny kadr twarzy zawyża je ruchem głowy. Jeff Su (animacja stanów na ciemnym tle) ma 8, reszta 22-34; nasze krótkie shorty `out_v2` (split z kartą u góry) mają 3,4 i 8,0 (poniżej każdego twórcy poza Jeffem), starsze `out` 20-27 (ciasna twarz).

### Pooled (wszystkie 30 shortów)

| miara | n | mediana [Q1; Q3] | uwagi |
|---|---|---|---|
| długość ujęcia [s] | 699 ujęć | 1,56 [0,93; 2,75] | mediana ujęć twórcy: Varun 1,10, Jeff 4,15 (animacja bez cięć; w tabeli wyżej jest mediana z median shortów) |
| tempo mowy EN [słów/min] | 25 | 219 [201; 256] | Zack Shutt 203 (inny wzorzec); Kilar PL 166 [156; 174] n=5 |
| najdłuższa pauza między słowami [s] | 30 | 0,42 [0,27; 0,77] | maks. w shorcie |
| pierwsze słowo [s od klatki 0] | 30 | 0,05 [0,03; 0,08] | maks. 0,22 s (wszystkie 30 shortów) |
| cisza po ostatnim słowie [s] | 30 | 0,23 [0,14; 0,28] | <= 0,5 s w 26/30 |
| głośność całości [LUFS] | 30 | -15,9 [-20,1; -14,0] | rozstęp -24,2...-11,6; nasz cel -14 |
| poziom przerw względem mowy [dB] | 21 | -11,9 [-18,2; -10,1] | [NIEPEWNE] czy to podkład, czy pogłos |
| wysokość linii napisu [% H] | 29 | 0,03 [0,02; 0,03] | |

## Oś czasu (2 shorty)

### Varun Mayya `KNWWZS4n1J8` (97 s, 5,17 mln, split w hooku, potem materiał na cały ekran)

Obejrzane 0-64 s (arkusze); 65-97 s tylko liczby (cięcia, napisy). 70 cięć w 97 s = 0,72/s, mediana ujęcia 1,2 s.

| czas | co widać | co mówi (streszczenie) |
|---|---|---|
| 0:00-0:02,9 | **HAK, split**: u góry (y 0-0,52 H) materiał źródłowy, cięcia co 0,5-1 s (detal konsoli 0,0, youtuberka 0,5, render 1,5); na dole Varun w pasie (twarz y ok. 0,62-0,80, głowa+ramiona), napis w ciemnej pigułce na szwie. Od 1,5 s etykieta „GAMING CONSOLE” wjeżdża po słowie (2 linie, ok. 1 s) | „Here's how this Chinese YouTuber built a gaming console that runs PS5, Xbox…” |
| 0:03,0-0:05,5 | pełny ekran: zbliżenie konsoli, potem trzy plansze po 0,5-1 s na czarnym tle: „PS5”, „Xbox”, „Switch 2” (duży biały sans u góry, produkt na cokole), napisów mówionych na czas plansz nie ma | „…and Switch 2 all at once” (wyliczanka: słowo = plansza) |
| 0:05-0:08 | zestawienie trzech konsol (etykiety), potem ilustracja, materiał o bohaterce | „…high-tech jugaad. To begin with, she opened all three consoles” |
| 0:08-0:18 | materiał ujęcie co ok. 1 s, 9,0 siatka z 3 okien, 15-17 split: góra tekst/grafika, dół materiał; napis w pigułce y ok. 0,74 (1-3 słowa) | opis płyt i chłodzenia |
| 0:19-0:21 | plansza na białym tle: **animowany rozbity widok** (chłodzenie + zasilacz), tytuł „One Cooling System and One Power Supply” składa się frazami w 19,0 i 20,0 | „what if they all shared one cooling system and one power supply” |
| 0:22-0:43 | materiał z warsztatu (frezarka, aluminiowy pryzmat), 29-31 split (grafika u góry, materiał na dole), 38-40 materiał w ramce; **bez twarzy twórcy** | konstrukcja chłodzenia |
| 0:44 | **powrót Varuna** na pełny kadr ok. 1 s, ciasny, gest ręki | „But the real jugaad…” |
| 0:45-0:47 | wielka kwota „$700” na twarzy bohaterki: mała przekreślona w 46,0, duża w 47,0 (animowany tekst na słowie) | „A machine shop quoted her $700 to CNC it” |
| 0:48-0:64 | proces odlewu: ilustracja figurki, materiał, druk 3D, gips, piec; cięcia ok. 1 s, napisy w pigułce | „ancient lost wax casting… burned the plastic away at 700 degrees” |
| 0:65-1:37 | [tylko pomiar] 0,6-0,9 cięcia/s do końca; ostatnie słowo kończy się 0,06 s przed końcem pliku: **zero ekranu końcowego, zero CTA**, ostatnia fraza to puenta („Total respect.”) | wynik, zasilacz, przełączanie, „Total respect.” |

### Jeff Su `sfwax2dVPvI` (57 s, 233 tys., animowane wyjaśnienie)

0 cięć (scene > 0,25) w 57 s: zmiany tylko stanów elementów. Obejrzane całe.

| czas | co widać | co mówi |
|---|---|---|
| 0:00-0:05 | **HAK, split**: u góry (0-0,48 H) animowany diagram trzech paneli (ChatGPT, Gemini, Claude), **żółta ramka skacze po panelach co 0,5 s** (0,0 -> 0,5 -> 1,0 -> 2,0); na szwie karta tytułowa (logo, „WHEN TO USE” biały + „ChatGPT vs. Gemini vs. Claude” żółty) widoczna od 0,5 do 5,0 s; na dole Jeff (twarz y ok. 0,62-0,80). Napisów mówionych brak | „I use ChatGPT, Gemini, and Claude almost every day, and each one has a specific superpower.” |
| 0:05,5-0:13 | pełny ekran, ciemne tło z kropkami: panel „ChatGPT”, siatka 12 pól, **pola zapalają się po jednym co 0,5-1 s** do „12/12”; napisy: szara pigułka y ok. 0,77, 2-5 słów, zmiana co ok. 1 s | „ChatGPT's superpower is obedience…” |
| 0:14-0:19 | ten sam panel + „OTHER MODELS”: pola gasną na czerwono (8/12) | „other models might quietly skip a few steps” |
| 0:20-0:34 | „Gemini”: trzy ikony (obraz, dźwięk, tekst) -> strzałki zbiegają -> blok „synteza”; elementy wchodzą na zmianę co 0,5-1 s | „…multi-modality… synthesize all three in one go” |
| 0:35-0:46 | „Claude”: paski postępu „Draft 1-4” rosną, drugi panel Claude wjeżdża w 39,0 i dobija do pełnego paska | „first draft quality… replicates your tone almost perfectly” |
| 0:47 | **Jeff pełny kadr na 1 s** (jedyny powrót twarzy w środku), potem split: panel „THE BEGINNING / THE LAST MILE” u góry, twarz na dole | „For me personally, ChatGPT and Gemini handle the beginning…” |
| 0:57 | koniec 0,16 s po ostatnim słowie, brak CTA, brak planszy | „…toning that rough output into something polished.” |

## Opis techniczny

**Hak 0-3 s.** Mowa zaczyna się w 0,05 s (mediana, maks. 0,22 s, 30/30 shortów), czyli zero rozbiegu. Obraz w klatce 0 jest już „zajęty”: u 19 z 30 shortów (6 z 6 twórców) pierwsze 2 s to układ **split**: u góry (do ok. y 0,53 H) materiał źródłowy lub animowany diagram, na dole twórca w pasie. W 3 s pojawia się najczęściej tytuł lub etykieta (wizualnie 10 z 18 rdzeniowych, mediana startu 2,0 s, y 0,49 H, czyli na szwie), a materiał u góry zmienia się co 0,5-1 s (Varun) albo ramka-wskaźnik skacze co 0,5 s (Jeff). Hak bez splitu (Ali Abdaal, Kilar, `QzDCfJpVGN8`) to ciasna twarz z gestem, napisy od klatki 0.

**Układ.** Trzy dominujące rodziny, często mieszane w jednym shorcie: (1) **hak w splitcie, potem pełny ekran** (Varun 5/5, Jeff 4/5, Herk 3/5): split 2-5 s, potem materiał lub animacja na całym ekranie, powrót twarzy rzadki (Varun 1-2 razy po ok. 1 s, Jeff 1-2 razy); (2) **stały split** (Wolfe 4/5: LOW 75-100 % czasu; Herk 2/5): panel u góry wymieniany co kilka sekund, twarz w pasie cały czas, napis na szwie; (3) **twarz pełny kadr z nakładkami** (Ali 5/5: FULL 74 % mediana; Kilar 3/5). Szew panel/twarz leży w y = 0,53 H [0,49; 0,58] (n = 1624 klatek, 19 shortów, 5 twórców); twarz w pasie ma ramkę od y 0,64 do 0,80 H i szerokość 0,23 W [0,19; 0,29] (w pasie widać głowę i ramiona). Twarz w pełnym kadrze: środek ramki y 0,37 H [0,33; 0,41], szerokość ramki 0,33 W [0,22; 0,43] (rozrzut sugeruje dwa tryby, ok. 0,2 bazowo i 0,4-0,5 po punch-inie [NIEPEWNE: z arkuszy, osobno nie zmierzone]).

**Napisy.** 1-3 słowa w linii (mediana 2 [1; 3], n = 2640 grup z OCR), wielkość linii ok. 3 % wysokości (ok. 58 px na 1920), zmiana grupy co 0,25-0,5 s. Pozycja jest dwumodalna: **na szwie** y ok. 0,46-0,58 (Kilar 0,50, Herk, Wolfe w splitcie) albo **dolna połowa** y ok. 0,70-0,78 (Varun 0,74 we wszystkich 5, Jeff 0,74-0,78, Ali 0,70-0,74); Wolfe w splitcie bywa też na samym dole (0,94-0,98). Pigułka lub ciemny box za tekstem: 14/18 rdzeniowych, 6/6 twórców (Varun, Jeff, Kilar 100 % shortów; Wolfe tylko `QzDCfJpVGN8`, Ali tylko `LE5uwaOvqEY`). **Wyróżnienie aktywnego słowa lub słowa kluczowego** (kolor, pogrubienie) jest rzadkie: 5/18, 3/6 twórców (Herk zielony/biały, Ali pogrubione aktywne słowo i szare przyszłe, Wolfe magenta/żółty na nazwach). Wielkie litery: Wolfe i Herk; zdanie małymi literami: Varun, Jeff, Ali, Kilar. Wszystkie napisy wtopione.

**Zoomy.** Twardy skok szerokości twarzy w obrębie pełnego kadru (>= 1,18x, bez zmiany pozycji) ma mediana 1,28x [1,21; 1,42] (n = 60 skoków w górę, 15 shortów, 5 twórców). Odstęp między kolejnymi skokami w górę 5,8 s [2,0; 15,8] (n = 45), a na 10 s czasu w FULL 0,6 [0,0; 1,8] (n = 22 shortów z >= 4 s FULL). Skoki występują u 5 z 6 twórców (Kilar 5/5 shortów, Varun 4/5, Ali 3/5, Herk 2/5, Jeff 1/5, Wolfe 0/5), przy czym połowa jest na wykrytym cięciu, połowa poniżej progu `scene` (zoom na tym samym tle). Zoomu pod kartą nie ma (split: twarz w pasie stoi bez ruchu).

**Grafika wokół twarzy i b-roll.** Grafika autorska na płaskim tle (diagram, UI, etykiety kinetyczne, rozbity widok) to 12 z 30 shortów wg detektora, ale tylko w 3 twórcach (Jeff 57-86 % czasu, Varun 18-61 %, Herk 21-30 % w 2 shortach); wizualnie 11/18, 5/6 (Varun 3/3, Jeff 3/3, Wolfe 2/3, Herk 2/3, Ali 1/3). Odcinek takiej grafiki: mediana 1,75 s [1,0; 3,75] (n = 89 odcinków, 5 twórców; Jeff 13,5 s mediana, reszta 1,3-2,5 s). Materiał filmowy bez twarzy: odcinek 2,0 s [1,0; 3,0] (n = 125, 6 twórców). Wejść w pełny ekran (>= 0,5 s) na 10 s: 0,60 [0,12; 1,74] (mediana tempa 3,6 na minutę; Varun 2,6 na 10 s, Kilar 1,4, Ali 0). Między dwoma pełnymi ekranami twórca (lub panel z twarzą) wraca na 1,5 s [0,75; 3,5] (n = 132 przerw dodatnich). Naklejki/wycinki obok twarzy (Ali: wordmark i zdjęcie produktu pływające obok głowy, wycięta okładka książki z obrotem 3D i „8/10”): 2/18, 1 twórca. Kółko z twarzą na materiale: Kilar (1 z 3 rdzeniowych; kółko ok. 0,5 W średnicy na dole, twarz wypełnia je w 70 %). Licznik „1/9” w pigułce: Kilar; „#1 #2 #3”: Herk. Karty źródeł (tweet, UI): Varun 4vIPxzPPweI, Jeff KS-p0e-KwBA, Herk CV-k6rPJvJY (3/18, 3 twórców).

**Tekst na ekranie vs słowa.** Krótkie bloki (2-9 słów): widoczne 1,4 s [1,0; 2,0], czyli 0,42 s/słowo [0,29; 0,62] (n = 424 bloków, 28 shortów, 6 twórców); 41 % z nich przeszło szybciej niż 0,35 s/słowo. Karty >= 10 słów (tweet, UI, kod): 2,25 s [1,5; 3,25], 0,12 s/słowo (n = 126, 5 twórców) tj. karty nie są do przeczytania w całości, tylko do rozpoznania, a ważne zdanie podkreśla marker (Varun przy tweetach ok. 5,5 s). Czasy to **dolna granica** (OCR gubi tekst na wideo), ręcznie z arkuszy: tytuł Jeffa 4,5 s (5 słów), wyliczanki Varuna po 0,5-1 s na 1 słowo.

**Przejścia.** Twarde cięcie (większość), płynne wchodzenie elementów (stagger 0,5-1 s) wewnątrz animacji, przenikanie z rozmyciem przy materiale u Ali, tylko u Jeffa 0 cięć. Efektów glitch/flash prawie nie ma [wizualnie nie zauważyłem w arkuszach].

**Dźwięk [NIEPEWNE: tylko pomiary].** Głośność 30 shortów: -15,9 LUFS [-20,1; -14,0], rozstęp 8 dB (Herk i Kilar -14, Wolfe -20,5, Jeff -17). Poziom w przerwach między słowami -11,9 dB [-18,2; -10,1] poniżej mowy, `silencedetect` -45 dB zwraca 0 w 28/30 shortów: nigdy nie ma pełnej ciszy, więc pod mową jest coś ciągłego (podkład lub pogłos). Impulsów >= 8 dB w przerwach: mediana 0, maks. 1,6 na 10 s (Kilar), czyli osobnych SFX w przerwach prawie nie widać; SFX pod mową nie wykluczam. Odsłuch zalecany przed wejściem do kryteriów.

**Tempo.** Angielski: 219 słów/min [201; 256] (Ali 274, Herk 266 najszybciej, Jeff 197, Wolfe 203). Polski (jeden twórca, n=5): 166 [156; 174]. Najdłuższa pauza w shorcie 0,42 s [0,27; 0,77].

**CTA i koniec.** Ostatnie słowo kończy się 0,23 s [0,14; 0,28] przed końcem pliku, **brak ekranu końcowego u wszystkich 6**. CTA mówione (podział z transkrypcji ostatnich 18 s, 30 shortów): bez CTA 14 (Varun 5/5, Ali 3/5, Wolfe 3/5, Jeff 2/5, Kilar 1/5), „obserwuj” 5 (Kilar 4, Jeff 1), pytanie do komentarzy 3 (Jeff 2, Wolfe 1), „napisz słowo, wyślę” 3 (Herk), link do pełnego filmu 2 (Herk), link sponsora 3 (Ali 2, Wolfe 1). Żaden rodzaj nie ma 4 twórców, jedyna wspólna cecha to ucięcie tuż po ostatnim słowie. Pętli (ostatnia klatka podobna do pierwszej) nie wykryłem: najmniejsza różnica klatek 8 (twarz w tym samym tle), mediana 56 na 255, a ostatnie zdanie nie wraca do hooka w żadnym z 18 rdzeniowych.

## Logiki rozłożone na parametry pierwotne

Każda logika jako: **wyzwalacz** (co w mowie lub treści ją uruchamia), **umiejscowienie** względem twarzy (rozmiar w % kadru 1080x1920), **wejście/wyjście** (ruch i czas), **czas na ekranie**, **częstość** (na 10 s), **co zastępuje** u nas, **dlaczego** (problem widza). Wartości z tabeli „Wystarczalność danych”; tam, gdzie próg nie jest spełniony, jest napisane „za mało danych”.

### T1. Hak w splitcie: panel nad twarzą w pierwszych 2-5 s
- **Wyzwalacz:** początek shorta (t = 0), bez wyzwalacza w mowie. Tytuł/etykieta w panelu na szwie dochodzi w 0,5-3,5 s (mediana 2,0 s, n = 33).
- **Umiejscowienie:** panel (materiał źródłowy lub animowany diagram) y 0-0,53 H [0,49; 0,58], pełna szerokość; twórca w pasie poniżej: ramka twarzy y 0,64-0,80 H, szerokość 0,23 W [0,19; 0,29], głowa + ramiona widoczne w całości; napis (lub tytuł) na szwie y ok. 0,5.
- **Wejście/wyjście:** wejścia brak (jest w klatce 0); wyjście twardym cięciem na pełny ekran (Varun, Jeff) albo panel zostaje i tylko się wymienia (Wolfe, Herk). Pojedynczy odcinek splitu 2,9 s [1,5; 5,1] (n = 78, 6 twórców); sam hak od klatki 0: 2,75 s [1,75; 4,6] (n = 11, 4 twórców, **za mało danych**).
- **Częstość:** 1 na short na starcie (19/30 auto, 12/18 wizualnie); w obrębie panelu zmiana obrazu co 0,5-1 s (Varun) lub skok ramki co 0,5 s (Jeff).
- **Zastępuje:** nasz hak = twarz pełny kadr + `hook_text` pigułką; układ `SPLIT` (karta nad boksem 820x680) zostaje jako wariant.
- **Dlaczego:** w 0,0 s widz widzi ruch i informację (panel) oraz człowieka (zaufanie), a napis na szwie nie zasłania ani jednego, ani drugiego; rozwiązuje „przeskrol w 1-2 s”.

### T2. Stały split: twarz w pasie cały short, panel się wymienia
- **Wyzwalacz:** brak (układ stały). **Umiejscowienie:** jak T1 (szew 0,5 H, twarz y 0,64-0,80). **Wejście/wyjście:** wymiana zawartości panelu co 1-4 s, twarz nie rusza się. **Czas na ekranie:** LOW 75-100 % czasu (Wolfe 4/5, Herk 2/5). **Częstość:** 6 z 30 shortów, 2 z 6 twórców (Kilar liczony przez detektor to kółko, nie split). **Zastępuje:** zmianę układów co kilka sekund (A/B/C z `ZASADY`). **Dlaczego:** nie ma skoków do osobnych ekranów, a ruch jest cały czas.
- **Wystarczalność: za mało danych (n = 6 shortów, 2 twórców).** Zgodność z regułą Kamila (twarz zawsze widoczna) jest, ale parametrów nie wolno brać z 2 twórców.

### T3. Pełny ekran bez twarzy (materiał lub grafika), narracja głosem
- **Wyzwalacz:** rzeczownik, który da się pokazać (nazwa produktu, miejsce, proces), albo zmiana wątku. **Umiejscowienie:** cały kadr, napis y 0,74 (dolna połowa). **Wejście/wyjście:** twarde cięcie, ujęcie 2,0 s [1,0; 3,0] (materiał) lub 1,75 s [1,0; 3,75] (grafika; Jeff 13,5 s). **Częstość:** 0,60 wejść na 10 s [0,12; 1,74] (3,6 na minutę); Varun 2,6, Kilar 1,4, Ali 0. **Powrót twarzy między ekranami:** 1,5 s [0,75; 3,5]. **Zastępuje:** karty `web`/`scene` w układzie z twarzą. **Dlaczego:** mocny pattern interrupt i dosłowna ilustracja; widz „widzi to, o czym mowa”.
- **Konflikt z regułą Kamila (E):** „zbyt często przenosimy się na osobny ekran i to rozprasza”, `checklist` (long) `screen_switches <= 1,5/min`, `speaker_back >= 3 s`. Twórcy w shortach: 3,6/min mediana, a powrót twarzy 1,5 s. Wartość dopuszczalna dla shortów nie jest ustalona: decyzja Kamila (niżej).

### T4. Animowana grafika autorska na płaskim tle (diagram, UI, etykiety kinetyczne)
- **Wyzwalacz:** pojęcie, liczba, porównanie, lista; słowo kluczowe wchodzi na swoim słowie (np. „$700” rośnie w chwili słowa, trzy nazwy konsol po jednej planszy). **Umiejscowienie:** panel nad twarzą albo cały ekran; elementy w stałym układzie, zmieniają się **stany**. **Wejście/wyjście:** stagger 0,5-1 s, pola zapalają się po jednym, ramka skacze, licznik rośnie; bez zanikania całej karty. **Czas na ekranie:** odcinek 1,75 s [1,0; 3,75] (n = 89, 5 twórców). **Częstość:** u Jeffa 57-86 % czasu, u Varuna 18-61 %. **Zastępuje:** napis słowny / karta `kw` / statyczna karta. **Dlaczego:** pokazuje mechanizm zamiast opisu; ruch niesie uwagę bez cięć.
- **Wystarczalność:** prevalence wizualna 11/18 i 5/6, ale detektor płaskiego tła widzi ją tylko u 3 twórców (12/30), więc **A = 2**. Kadencja zmian stanu (s między zmianami) **nie jest zmierzona automatycznie**; ręcznie ok. 0,5-1,5 s (n ok. 10, 2 twórców): **za mało danych**.

### T5. Twardy skok zoomu na twarzy (punch) w pełnym kadrze
- **Wyzwalacz:** puenta, zwrot, liczba (nie zmierzone, tylko wizualnie), plus skok maskujący cięcie. **Umiejscowienie:** twarz FULL, środek ramki y 0,37 H bez zmiany pozycji x (< 0,15 W). **Wejście/wyjście:** twarde cięcie (bez rampy), czyli następna próbka 0,25 s później ma już nową skalę; skala 1,28x [1,21; 1,42] (n = 60). **Czas:** do następnego skoku 5,8 s [2,0; 15,8] (n = 45). **Częstość:** 0,6 na 10 s czasu w FULL [0,0; 1,8] (n = 22). **Zastępuje:** `zoom_every_cut` + `punch` z sufitem 1,38 i rampą 0,3 s. **Dlaczego:** resetuje uwagę przy statycznej twarzy bez zmiany kadru.

### T6. Napisy: 1-3 słowa w ciemnej pigułce, pasmo y 0,46-0,78
- **Wyzwalacz:** każde słowo (zmiana grupy co 0,25-0,5 s). **Umiejscowienie:** wyśrodkowane, linia 3 % H; **na szwie** y 0,46-0,58, gdy jest split lub nakładka; **y 0,70-0,78** w pełnym kadrze (mediana modalna 0,74 [0,54; 0,78], n = 29). **Wejście/wyjście:** nie zmierzone (OCR 4 kl/s za rzadki). **Czas:** grupa 0,25-0,5 s. **Zastępuje:** napisy bez boxu z akcentem na aktywnym słowie (nasz `caption_box` jest od 04.11). **Dlaczego:** czytelność na dowolnym tle (materiał, jasna grafika) bez zależności od koloru tła.
- Wyróżnianie aktywnego słowa **nie jest standardem** (5/18, 3/6): nasza obecna praktyka (`caption_pop`, akcent na słowie) nie ma tu poparcia, ale też nie ma dowodu, że szkodzi.

### T7. Tytuł / etykieta w hooku do 3 s
- **Wyzwalacz:** t = 0,5-3,5 s (mediana 2,0 s). **Umiejscowienie:** szew y 0,49 H [0,43; 0,70], 2-9 słów, wysokość znaku >= 2 % H. **Wejście/wyjście:** wjazd po słowie (kinetyczny) lub wipe, zostaje 1,5 s [1,0; 2,25] (OCR, dolna granica; ręcznie Jeff 4,5 s, Varun 2,5-10 s). **Częstość:** 1 na short (10/18). **Zastępuje:** `hook_text` pigułka (nie zmierzono tam podobnej). **Dlaczego:** obietnica tematu, zanim widz zdecyduje.

### T8. Mowa od klatki 0 i ucięcie tuż po ostatnim słowie
- **Wyzwalacz:** zawsze. **Wartości:** pierwsze słowo 0,05 s [0,03; 0,08] (maks. 0,22), cisza po ostatnim słowie 0,23 s [0,14; 0,28] (26/30 <= 0,5 s), brak planszy końcowej. **Zastępuje:** ogon 3,1 s w naszych 6 shortach (mierzone). **Dlaczego:** oddech trzyma retencję do końca, a „koniec” nie daje pretekstu do wyjścia przed ostatnią frazą.

### T9. Kadr twarzy
- **Pełny kadr:** środek ramki y 0,37 H [0,33; 0,41], szerokość 0,33 W [0,22; 0,43] (n = 23 shortów, 6 twórców). **W pasie:** środek y 0,70 [0,67; 0,74], szerokość 0,23 W [0,19; 0,29] (n = 25). **Zastępuje:** nasz pełny kadr 0,53-0,55 W (mediana z 6 shortów) i twarz w pasie y 0,79-0,80 o szerokości 0,29-0,30 W (2 shorty `out_v2`). **Dlaczego:** twarz wyżej w pełnym kadrze zostawia miejsce na napisy i nakładki; w pasie niżej i ciaśniej niż twórcy oznacza krótszy panel i „zbyt blisko” (reguła Kamila).

### Brak danych do skopiowania (za mało danych, tylko odnotowane)
- **T10 Naklejka/wycinek obok twarzy** (Ali Abdaal): 2 z 18 shortów, 1 z 6 twórców (n = 2): wymiary, czas, ruch nie do uogólnienia. Kamil chce ten układ (memy jako naklejki), ale nie ma z kogo brać liczb: potrzebna konkretna referencja.
- **T11 Kółko z twarzą na materiale** (Kilar): 1 z 18 (n = 1) + miniatura u Varuna: za mało danych. Zgodność z regułą Kamila o kółku: kółko u Kilara ma ok. 0,5 W średnicy i twarz wypełnia je w ok. 70 % (obejrzane w `dQxAPuLEt6k`), czyli to samo „ciasne” kółko, które Kamil odrzucił: **nie kopiować**.
- **T12 Licznik / pigułka postępu** (Kilar „1/9”, Herk „#1-#3”): 2 z 18, 2 twórców (n = 2): za mało.
- **T13 Karta źródła (tweet/UI/nagłówek) z markerem** (Varun, Jeff, Herk): 3 z 18, 3 twórców; Zack Shutt rozbiór już to opisuje, tu nie dochodzi nowy dowód.
- **T14 CTA:** samo „jest jakieś CTA” ma 10/18 w 5 twórcach (próg spełniony), ale to mieszanka rodzajów i żaden rodzaj nie ma 4 twórców (bez CTA 14/30, „obserwuj” 5, pytanie 3, „napisz słowo” 3, link 5): brak wspólnej logiki.
- **T15 Tempo polskie:** 1 twórca (n = 5): za mało. **T16 Głośność:** brak zgody (8 dB rozstępu), nic do zmiany. **Pętla:** 0/18, zero dowodu.

## Wystarczalność danych

Próg z dodatku Kamila: **prevalence** >= 4 z 6 twórców i >= 9 z 18 shortów rdzeniowych (przy detekcji automatycznej na 30: >= 15); **parametr** (czas, rozmiar, pozycja) >= 20 zmierzonych zdarzeń u >= 4 twórców; poniżej: „za mało danych (n=X)”. Zdarzenia = próbki co 0,25 s (dla pozycji i rozmiarów), odcinki, bloki lub shorty (jednostka w kolumnie „param”). Mediana [Q1; Q3] pooled, nie per twórca.

| logika | parametr | n zdarzeń | n shortów | n twórców | mediana | IQR | werdykt |
|---|---|---|---|---|---|---|---|
| T1 | prevalence hooka w splitcie (wizualnie, 18) | 12 z 18 | 12 | 5 | - | - | OK |
| T1 | prevalence hooka w splitcie (detektor, 30) | 19 z 30 | 19 | 6 | - | - | OK |
| T1 | szew panel/twarz y (% H), klatki w LOW | 1624 | 19 | 5 | 0,53 | 0,49; 0,58 | OK |
| T1 | twarz w pasie: góra ramki y (% H) | 2903 | 27 | 6 | 0,64 | 0,61; 0,67 | OK |
| T1 | twarz w pasie: dół ramki y (% H) | 2903 | 27 | 6 | 0,80 | 0,79; 0,82 | OK |
| T1 | twarz w pasie: szerokość ramki (% W), mediana shorta | 25 | 25 | 6 | 0,23 | 0,19; 0,29 | OK |
| T1 | czas jednego odcinka splitu [s] | 78 | 25 | 6 | 2,88 | 1,50; 5,12 | OK |
| T1 | czas splitu od klatki 0 [s] | 11 | 11 | 4 | 2,75 | 1,75; 4,62 | za mało danych (n=11) |
| T2 | prevalence stałego splitu (detektor, 30) | 6 z 30 | 6 | 2 | - | - | NIE: 2 z 6 twórców, 6 z 30 |
| T3 | prevalence pełnych ekranów bez twarzy >= 20 % czasu (30) | 19 z 30 | 19 | 6 | - | - | OK |
| T3 | czas odcinka bez twarzy (GFX+FOOT) [s] | 130 | 23 | 6 | 2,50 | 1,50; 6,25 | OK |
| T3 | wejść w pełny ekran na 10 s (short) | 30 | 30 | 6 | 0,60 | 0,12; 1,74 | OK |
| T3 | powrót twarzy między dwoma ekranami [s] | 132 | 17 | 6 | 1,50 | 0,75; 3,50 | OK |
| T4 | prevalence grafiki autorskiej (wizualnie, 18) | 11 z 18 | 11 | 5 | - | - | OK |
| T4 | prevalence grafiki autorskiej (detektor płaskiego tła, 30) | 12 z 30 | 12 | 3 | - | - | NIE: 3 z 6 twórców, 12 z 30 |
| T4 | czas odcinka grafiki na płaskim tle [s] | 89 | 18 | 5 | 1,75 | 1,00; 3,75 | OK |
| T4 | kadencja zmian stanu elementów [s] | ok. 10 (ręcznie) | 3 | 2 | ok. 1 | - | za mało danych (n=10) |
| T5 | prevalence skoków zoomu w FULL (30) | 15 z 30 | 15 | 5 | - | - | OK |
| T5 | skala skoku w górę (w po/przed) | 60 | 15 | 5 | 1,28 | 1,21; 1,42 | OK |
| T5 | odstęp między skokami w górę [s] | 45 | 12 | 5 | 5,75 | 2,00; 15,75 | OK |
| T5 | skoków na 10 s czasu w FULL (short z >= 4 s FULL) | 22 | 22 | 6 | 0,62 | 0,00; 1,78 | OK |
| T6 | prevalence napisów w pigułce/boxie (wizualnie, 18) | 14 z 18 | 14 | 6 | - | - | OK |
| T6 | słów w grupie napisu (OCR) | 2640 | 29 | 6 | 2,00 | 1,00; 3,00 | OK |
| T6 | pasmo y napisu, modalne (% H), short | 29 | 29 | 6 | 0,74 | 0,54; 0,78 | OK |
| T6 | wysokość linii napisu (% H), short | 29 | 29 | 6 | 0,03 | 0,02; 0,03 | OK |
| T6 | prevalence wyróżnienia aktywnego słowa (wizualnie) | 5 z 18 | 5 | 3 | - | - | NIE: 3 z 6 twórców, 5 z 18 |
| T7 | prevalence tytułu/etykiety do 3 s (wizualnie, 18) | 10 z 18 | 10 | 5 | - | - | OK |
| T7 | start tytułu [s] | 33 | 20 | 6 | 2,00 | 0,50; 3,50 | OK |
| T7 | y tytułu (% H) | 33 | 20 | 6 | 0,49 | 0,43; 0,70 | OK |
| T7 | czas widoczności tytułu [s] (OCR, dolna granica) | 33 | 20 | 6 | 1,50 | 1,00; 2,25 | OK |
| T8 | pierwsze słowo [s] | 30 | 30 | 6 | 0,05 | 0,03; 0,08 | OK |
| T8 | cisza po ostatnim słowie [s] | 30 | 30 | 6 | 0,23 | 0,14; 0,28 | OK |
| T9 | środek ramki twarzy FULL y (% H), mediana shorta | 23 | 23 | 6 | 0,37 | 0,33; 0,41 | OK |
| T9 | szerokość ramki twarzy FULL (% W), mediana shorta | 23 | 23 | 6 | 0,33 | 0,22; 0,43 | OK |
| T9 | środek ramki twarzy w pasie y (% H), mediana shorta | 25 | 25 | 6 | 0,70 | 0,67; 0,74 | OK |
| T10 | naklejka/wycinek obok twarzy (wizualnie) | 2 z 18 | 2 | 1 | - | - | NIE: 1 z 6 twórców, 2 z 18 |
| T11 | kółko z twarzą na materiale (wizualnie) | 1 z 18 | 1 | 1 | - | - | NIE: 1 z 6 twórców, 1 z 18 |
| T12 | licznik / pigułka postępu (wizualnie) | 2 z 18 | 2 | 2 | - | - | NIE: 2 z 6 twórców, 2 z 18 |
| T13 | karta źródła/UI (wizualnie) | 3 z 18 | 3 | 3 | - | - | NIE: 3 z 6 twórców, 3 z 18 |
| T14 | CTA: najczęstszy rodzaj poza brakiem („obserwuj”) | 5 z 30 | 5 | 2 | - | - | NIE: 2 z 6 twórców |
| T15 | tempo mowy EN [słów/min] | 25 | 25 | 5 | 219 | 201; 256 | OK |
| T15 | tempo mowy PL [słów/min] | 5 | 5 | 1 | 166 | 156; 174 | za mało danych (n=5) |
| T16 | głośność [LUFS] | 30 | 30 | 6 | -15,9 | -20,1; -14,0 | OK |
| T17 | czas widoczności krótkiego bloku 2-9 słów [s] (OCR) | 424 | 28 | 6 | 1,38 | 1,00; 2,00 | OK |
| T17 | s na słowo, krótki blok | 424 | 28 | 6 | 0,42 | 0,29; 0,62 | OK |
| T17 | czas widoczności karty >= 10 słów [s] (OCR) | 126 | 15 | 5 | 2,25 | 1,50; 3,25 | OK |
| T18 | długość ujęcia [s] | 699 | 30 | 6 | 1,56 | 0,93; 2,75 | OK |

Uwagi do tabeli: n zdarzeń przy pozycjach i rozmiarach to próbki 0,25 s (nie niezależne), więc liczba shortów i twórców jest uczciwszą miarą; odstęp między skokami i czas hooku od klatki 0 mają duży rozrzut (IQR ponad 2x mediana).

## Co mamy / czego nie mamy

Nasza baza: 6 shortów (4 z `out/` 04.11, 2 z `out_v2/shorts` 05.11) przepuszczonych tymi samymi skryptami. Nasze mediany: cięcia/s 0,02, ujęcie 21,4 s, czas w FULL 90 %, szerokość twarzy FULL 0,54 W (środek y 0,42), ogon po ostatnim słowie 3,1 s, tempo 143 słów/min.

| technika | u twórców (n, twórcy) | u nas (zmierzone) | mamy? | co zbudować / zmienić |
|---|---|---|---|---|
| T1 hak w splitcie (panel + twarz w pasie, 2-5 s) | 12/18, 5/6; split 2,9 s | `out`: LOW 0 %; `out_v2`: LOW 63-82 % (stały split, twarz y 0,79-0,80, szerokość 0,29-0,30) | **częściowo**: `layout: split` (karta + boks), hak = twarz + `hook_text` | **P2** `layout: "hook_split"`: panel 0-0,53 H z `scene`/b-roll, twarz w pasie y 0,64-0,80 (szerokość <= 0,26 W), tytuł na szwie, powrót do planu po 2-5 s. Sprawdzić `head_check.py` (głowa + ramiona całe, broda nad napisem) |
| T2 stały split | 6/30, 2/6 (Wolfe, Herk) | `out_v2` ma stały split (s06, s14) | **tak** (v2) | nic: **za mało danych** u twórców do zmiany parametrów |
| T3 pełne ekrany bez twarzy | 19/30, 6/6; 0,6 na 10 s, powrót 1,5 s | `nof10` 0,24 na 10 s; karty `web`/`scene` w FULL | **tak**, ale E: Kamil mówi „za często” | **decyzja Kamila** (limit na minutę, minimalny powrót) zanim cokolwiek się doda; ewentualnie krytyk `critic` jako ostrzeżenie |
| T4 animowana grafika autorska | 11/18, 5/6; odcinek 1,75 s | GFX 6 % czasu | **tak** (`scene`, `list`, `kw`) | **P2** użyć `scene` także jako panelu w hooku; odcinek grafiki 1,0-3,75 s; wejścia po 0,5-1 s; nie dokładać nowych typów |
| T5 skok zoomu w FULL | 15/30, 5/6; 1,28x, co 5,8 s | `ups10` 0,00 (0 skoków w 5 z 6) | **częściowo**: `beats`/`punch` z rampą, `zoom_every_cut` | **P1** `jump_zoom`: twardy skok 1,2-1,4x (nie 1,6x jak Zack) z `face_track.zmax_at`, odstęp 3-8 s, tylko FULL (nie pod kartą) |
| T6 napisy w pigułce, 1-3 słowa, y 0,70-0,78 lub na szwie | 14/18, 6/6 | box w `caption_box` (ok. 63 % H w v2: y 0,62), 1-3 słowa; modalne y 0,74 w `out` | **tak** | **P1** reguła: przy splitcie napis na szwie (y 0,50-0,58), w pełnym kadrze y 0,70-0,78; box półprzezroczysty ciemny; bez zmiany aktywnego słowa jako warunku |
| T7 tytuł w hooku do 3 s | 10/18, 5/6; start 2,0 s, y 0,49 | `short.hook_early` <= 1,0 s w checklist | **tak** | **P2** tytuł wsuwany na słowach na szwie; sprawdzić start <= 3,5 s i dwuwierszowość (2-9 słów) |
| T8 mowa od klatki 0 i ucięcie po ostatnim słowie | 30/30; 26/30 <= 0,5 s | pierwsze słowo 0,10 s; ogon **3,1 s** | **częściowo** (ogon 3 s) | **P1** `critic`: ostrzeżenie, gdy `tail` > 0,6 s i brak karty końcowej; sprawdzić, czy ogon 3,1 s to plansza końcowa albo pauza (u Zacka brak planszy) |
| T9 kadr twarzy | FULL y 0,37, szer. 0,33; pas y 0,70, szer. 0,23 | FULL y 0,42, szer. **0,54**; pas y 0,79-0,80, szer. 0,29-0,30 | **częściowo** | **P2** bazowy kadr FULL szer. ok. 0,33 [0,22; 0,43] (zmiana `face_target_y`/crop); w pasie szer. <= 0,26 i y <= 0,74 |
| T10-T13 naklejki, kółko, licznik, karta źródła | za mało danych (1-3 twórców) | `meme`, `face_corner`, `web`, `count` | **tak** | nie budować nic nowego na tej podstawie |
| tempo mowy | EN 219; PL 166 (1 twórca) | 143 (PL) | **tak** (`pads`) | do decyzji: czy skracać pauzy do poziomu EN; dla PL jest tylko 1 twórca |

## Macierz logik

Punktacja (0-3 każde A-C, 0-2 D, bez wag; **E** zawsze wygrywa i może zablokować): **A** prevalence: 3 = >= 4/6 twórców i >= 9/18 (auto 15/30), 2 = >= 3 twórców i >= 6/18, 1 = 2 twórców, 0 = 1; przy dwóch metodach liczy mniejsza. **B** spójność: ilu z 6 twórców ma cechę w >= 60 % (auto) lub >= 2/3 (wizualnie) swoich shortów: 3 = >= 5, 2 = 4, 1 = 3, 0 = <= 2. **C** zgodność z naszymi REF i RESEARCH: 3 = >= 3 źródeł się zgadza, 2 = dwa, 1 = jedno, odjęte 1 za sprzeczność. **D** sygnał wyników: w ilu twórcach short z cechą ma więcej wyświetleń (x mediana kanału) niż bez niej wśród swoich 5; 2 = >= 3 twórców porównywalnych i >= 75 %, 1 = >= 50 %, 0 = mniej; **słaby (n = 2-5 na twórcę, same top shorty)**. **E:** + = zgodne z regułą/uwagą Kamila, 0 = neutralne, **X = sprzeczne (blokada bez jego zgody)**.

| logika | A | B | C | D | E | suma A-D | nasza reguła dziś | werdykt |
|---|---|---|---|---|---|---|---|---|
| T1 hak w splitcie | 3 | 2 | 3 | 1 (1/2) | + | **9** | `ZASADY` układ A (split), hak `hook_text`, `layouts >= 1` | BIERZEMY (P2), pod A/B test |
| T2 stały split | 1 | 0 | 2 | 0 (0/2) | + | **3** | `ZASADY` zmiana układu co kilka s (A/B/C) | za mało danych (2 z 6 twórców); zostaje to, co jest w v2 |
| T3 pełne ekrany bez twarzy | 3 | 2 | 3 | 2 (4/4) | X | **10** | `ZASADY` B pełna karta + kółko; `long.screen_switches <= 1,5/min`, `speaker_back >= 3 s` | BLOKADA (E): tylko po decyzji Kamila o limicie |
| T4 grafika autorska animowana | 2 | 2 | 3 | 0 (1/3) | + | **7** | `scene`/`list`/`kw`; Kamil: animowane rysunki zamiast słów | BIERZEMY w zakresie czasu odcinka; kadencja do zebrania |
| T5 skok zoomu w FULL | 3 | 1 | 3 | 2 (4/4) | + | **9** | `short.punch >= 3/min`; `ZASADY`: brak zoomu pod kartą | BIERZEMY (P1), skala 1,2-1,4x |
| T6 napisy w pigułce | 3 | 2 | 1 | 1 (1/2) | 0 | **7** | `caption_box`, `caption_pop`; napisy wtopione | BIERZEMY (P1) z pozycją zależną od układu |
| T7 tytuł w hooku do 3 s | 3 | 2 | 3 | 0 (1/4) | + | **8** | `short.hook`, `short.hook_early <= 1,0 s` | BIERZEMY (P2) |
| T8 mowa od 0, ucięcie po słowie | 3 | 3 | 2 | n/d (brak wariancji: 30/30) | 0 | **8** | `pads`, `ZASADY`: zostaw oddech, nie ucinaj głosek | BIERZEMY (P1) jako sprawdzenie |

Uzasadnienie C: T1: Zack: panel 37 % nad pełną twarzą w hooku; proof-cards: układ A; memes: Taher Shabaan panel u góry, twarz na dole; T2: memes: Norbert 80-90 % splitu; proof-cards: split domyślny; T3: Zack: grafika 61 % czasu; proof-cards: karta pełna B/D; BB: scena bez twarzy; T4: BB: stany w jednej scenie; Zack: skecz czatu; proof-cards: ruch w karcie; T5: Zack: skok 1,6x co 7 s; RESEARCH: punch co 5-6 s; memes: zoom-out na starcie. Skala 1,28x bliższa RESEARCH 1,12-1,22 niż Zack 1,6x; T6: Zack: ciemny półprzezroczysty box zgodny; proof-cards: bez boxu; RESEARCH #13: akcent na słowie (inny); T7: proof-cards: tytuł-hook 0-3,4 s; Zack: hak z grafiką; RESEARCH #12: tekst hooka 5-8 słów; T8: Zack: pierwsze słowo 0,03 s, koniec 0,2 s; RESEARCH #12: hak do 3 s.

**Sprzeczności i nakładki, kto wygrywa:**
1. **T1 (hak w splitcie) vs `layout: "top"` z REF Zacka (panel 37 % nad pełną twarzą, twarz ucięta czapką):** T1 wygrywa (suma 9), bo twarz jest cała (ramka y 0,64-0,80, głowa + ramiona, zgodnie z `ZASADY` „nigdy połowa twarzy”), a panel ma ok. 0,53 H zamiast 0,37 H. Zack `top` zostaje jako dowód, nie jako plan.
2. **T2 (stały split) vs T3 (pełne ekrany):** oba odpowiadają na „utrzymaj nowy obraz bez utraty twarzy”. Punktowo T3 ma więcej (10 vs 3), ale **E blokuje T3** (Kamil: za często osobny ekran), a T2 ma E = +. Reguła „E zawsze wygrywa” daje T2/T1, lecz T2 nie przechodzi progu danych (2 z 6 twórców). Wniosek: **nie wybieram T3 ani T2 do wdrożenia**, tylko T1 (split jako hak) z istniejącym stałym splitem z v2; limit T3 decyduje Kamil.
3. **T6 (napisy w pigułce) vs napisy z akcentem aktywnego słowa (nasze `caption_pop`):** pigułka wygrywa jako domyślne tło (14/18, 6/6 vs 5/18, 3/6); akcent na aktywnym słowie nie jest standardem u top twórców, ale nie ma dowodu, że szkodzi (Zack go ma). Nie zmieniać `caption_pop`, tylko dodać pozycję zależną od układu.
4. **T5 (skala skoku 1,28x) vs Zack `jump_zoom` 1,6x:** dane z 5 twórców (n = 60) dają 1,28x [1,21; 1,42], a Zack 1,6x to jeden twórca; wybieram zakres 1,2-1,4x. 1,6x tylko, gdy `face_track` pozwala zachować brodę w kadrze.

## Kolejność wdrożenia

Wchodzą tylko logiki, które przeszły próg danych (T1, T5, T6, T7, T8 oraz część T4 i T9). Koszt: S = do pół dnia, M = 1-2 dni, L = kilka dni.

**P1 (tanie, wpływ na każdy short):**
1. **T8 sprawdzenie końca** (`critic`/`film_check`): ostrzeżenie, gdy cisza po ostatnim słowie > 0,6 s, i `tail` w `film_check` (S). Cel zmierzony: 0,23 s [0,14; 0,28]; u nas 3,1 s.
2. **T5 `jump_zoom`**: twardy skok 1,2-1,4x w FULL, odstęp 3-8 s, bez zoomu pod kartą (`ZASADY`), bez rampy; kamera punch zostaje jako akcent puenty (S-M). Metryka: skoków na 10 s czasu w FULL: mediana 0,6, IQR 0-1,8 (rozrzut duży, 5 z 6 twórców to robi, 1 nie), skala 1,21-1,42.
3. **T6 pozycja napisu zależna od układu**: split/nakładka -> na szwie y 0,50-0,58; pełny kadr -> y 0,70-0,78 (S). Metryka: modalne y napisu w pasmie 0,46-0,78.

**P2 (średnie):**
4. **T1 `layout: "hook_split"`**: panel 0-0,53 H (`scene`, b-roll lub karta `web`), twarz w pasie y 0,64-0,80, szerokość <= 0,26 W, tytuł na szwie, wyjście do planu po 1,5-5 s (czas odcinka splitu n = 78, OK; czas samego haku od klatki 0 ma n = 11, za mało danych) (M). Metryka: w pierwszych 2 s twarz LOW, `head_check` bez ucięcia głowy, A/B z obecnym hookiem (thumbnails A/B zasada).
5. **T7 tytuł w hooku**: wsuwany na słowach, 2-9 słów, start <= 3,5 s, widoczny >= 2 s (nasz `reading` już wymaga min. 3 s sceny w shorcie) (M).
6. **T4 grafika autorska**: użyć istniejącego `scene` jako panelu w hooku (patrz T1), odcinek 1,0-3,75 s, wejścia po 0,5-1 s (M, bez nowych typów).
7. **T9 kadr twarzy**: bazowy FULL ok. 0,33 W [0,22; 0,43] zamiast 0,53 (docelowo w tym przedziale, wartość do wyboru przez Kamila); w pasie <= 0,26 W (M-L, dotyka `face_target_y`/crop, ryzyko `head_check`).

**P3 (po decyzji Kamila lub po zebraniu danych):** limit pełnych ekranów T3 jako ostrzeżenie `critic`; stały split T2 po dodaniu 2-3 twórców z takim układem; naklejki i kółko dopiero po wskazaniu referencji.

## Decyzje otwarte dla Kamila

1. **Pełne ekrany bez twarzy w shortach (T3):** twórcy wchodzą w pełny ekran 3,6 razy na minutę (mediana; Varun 16/min, Ali 0), wracając twarzą na 1,5 s; nasza reguła z longa to <= 1,5/min i powrót >= 3 s. Jaki limit dla shortów? Do tego czasu nie dodaję nic, co zwiększa skoki.
2. **Hak w splitcie (T1) zamiast „twarz + pigułka”:** 12/18 rdzeniowych, ale sygnał wyników słaby i niejednoznaczny (z cechą mają więcej wyświetleń u 1 z 2 porównywalnych twórców, detektor 2 z 5): potrzebny A/B na własnych shortach.
3. **Szerokość twarzy:** nasza twarz w pełnym kadrze to 0,53-0,55 W (stale ciasna), twórcy 0,33 [0,22; 0,43]. Zgoda na szerszy bazowy kadr (T9)? To zmiana w każdym shorcie.
4. **Ogon 3,1 s po ostatnim słowie:** czy to zamierzona plansza końcowa? U 6 twórców jej nie ma.
5. **Naklejki obok twarzy:** jedyny twórca z takim układem to Ali Abdaal (2 shorty). Potrzebna wskazana referencja, żeby wziąć liczby.
6. **Polski kontekst:** w próbie jeden polski twórca (Kilar), a jego format (materiał + kółko, napisy 1-2 słów na środku) różni się od reszty; wnioski dla polskiego tempa i napisów oparte są na n = 5. Dodać 2-3 polskich twórców (np. kanały z shortami technologicznymi) przed zmianą pacingu.
7. **Czy sponsorowane `#ad` i skecz 8 s traktować jako wzorzec:** zostawiłem je w 18 rdzeniowych zgodnie ze strict top 3 (Ali Abdaal); jeśli Kamil woli samą tematykę AI/tech, zamienić na miejsca 4-5 (`6R0QIkWyAdI`, `W8XNHsZWFSo`).

## Czego nie zmierzyłem

- Dźwięk (muzyka, SFX): bez odsłuchu; tylko poziomy i impulsy [NIEPEWNE].
- Kadencja zmian stanu w animacjach (s między zmianami elementów), wejście/wyjście ruchu napisu (OCR 4 kl/s), czas wejścia grafiki w ms.
- Rozpoznanie, czy punch-in pada na puencie/liczbie (nie powiązałem skoków z typem zdania).
- Wizualne kodowanie obejmuje 18 rdzeniowych; 12 dodatkowych tylko automatycznie. Druga część arkuszy B (ponad 65 s) nieoglądana.
- Szerokość twarzy to ramka detektora (czoło-podbródek), nie głowa z włosami; głowa to ok. 1,3-1,4x ramki. Zack podaje głowę, więc liczby nie są wprost porównywalne.
- Wpływ na retencję: brak dostępu do danych retencji twórców; D opiera się wyłącznie na wyświetleniach i jest słabe.
