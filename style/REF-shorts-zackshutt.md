# Wzorzec: short z gadającą głową i kartami-dowodami, Zack Shutt (rozbiór 2026-11-04)

Źródło: YouTube Shorts `74ZMAi8FzX8` Zack Shutt, „Claude Won't Reverse Engineer Games Anymore” (90,6 s, 1080x1920, **60 fps**, AV1, mowa po angielsku). Plik lokalny `render/ref/shorts/74ZMAi8FzX8/v.mp4`, tylko do nauki stylu.
Rozbiór: `select=gt(scene,0.25)` (też 0,1 i 0,15), klatki co 0,5 s w 8 arkuszach 6x4 (`frames/sheet_*.png`) oraz pełne klatki w kluczowych momentach (`frames/full_*.png`, `cmp1.png`, `cmp2.png`), pasek napisów co 0,1 s (`frames/capstrip.png`), whisper.cpp large-v3 q5 ze słowami (`work/words.json`, `work/w.json`), `ebur128`, `silencedetect`, spektrogram (`work/spec.png`), RMS co 50 ms.
Bierzemy mechanikę montażu, nie grafikę, postać, kanał ani treść autora. W materiale są cudze logotypy, zrzuty tweetów i postów oraz klip filmowy (mem): u nas tak samo jak dotąd, obrazy cudze tylko lokalnie, klipów filmowych nie wstawiamy (ADR-0008).
Dźwięk: nie słuchałem, tylko mierzyłem. Wszystko o SFX i muzyce niżej jest wnioskiem z pomiarów, oznaczone [NIEPEWNE], dopóki Kamil nie posłucha.

## Liczby

| miara | wynik |
|---|---|
| cięcia (scene > 0,25) | 31 w 90,6 s: średnie ujęcie 2,8 s, mediana 2,4 s, **20,5 cięć/min**, najdłuższe ujęcie 10,9 s (w nim wymiany kart bez twardego cięcia). Przy progu 0,1: 87 zmian |
| grafika w górnym pasie | ok. 61 % czasu (ok. 55 s z 90), **24 różne grafiki** (średnio co 3,7 s), z czego 10 to tekstowe karty źródeł (tweet, nagłówek, post, mail, komunikat) |
| najdłuższy odcinek bez grafiki | ok. 4,6 s (hak 0-4,6 ma animowany czat), potem najczęściej 1-3 s; od 78 do końca (12 s) tylko twarz z najazdem i zoomem |
| tempo mowy | 305 słów w 90,4 s = **203 słów/min** (en). Pauzy między słowami: 21 powyżej 80 ms, **najdłuższa 0,32 s**. Pierwsze słowo pada w 0,03 s. Ostatnie słowo kończy się w 90,38 s, film w 90,57 s |
| napisy | zmiana linii średnio co ok. 0,7 s, 1-3 słowa w linii |
| głośność | **-12,4 LUFS** (zakres LRA 1,2 LU, szczyt -3,9 dBFS): głos mocno sprężony. U nas cel -14, YouTube i tak ścisza do ok. -14, więc głośniej nie znaczy lepiej |
| zoom twarzy | szeroki ok. 1,0 (głowa ~28 % szerokości), punch-in ok. 1,6x (głowa ~46 %), jeden zoom-out ok. 0,55x |

## Oś czasu (po czasie w filmie)

| czas | co widać | co mówi (streszczenie) |
|---|---|---|
| 0:00-0:04,5 | HAK: biały ekran „czatu” z Claude, u dołu twarz **wycięta z tła** na białym, cień pod nią; w górnym pasie ok. 37 % wysokości animowany skecz: pole wpisywania, wiadomość użytkownika (1,0), odpowiedź (1,5), kolejna wiadomość wpisana w polu (2,5) i wysłana (3,0), druga odmowa (3,5). Napisy od 0,0 | teza z „podobno” + „już są wkurzeni”, 13 słów w 4,6 s |
| 0:04,6 | **twarde cięcie na punch-in** (tło studia ciemne, twarz ok. 1,6x), napis „WHAT'S GOING ON?” | pytanie otwierające pętlę |
| 0:05,5-0:05,8 | glitch / rozmycie i mieszanie klatek do logo Claude (0,5 s), potem logo w górnym pasie 5,8-6,9 | wejście w temat |
| 0:07-0:08,3 | zrzut wideo gry w oknie przeglądarki (górny pas, fioletowa ramka) | „rebuild real games” |
| 0:08,3-0:09,8 | **punch-in** na twarz, gest palcem | „…pirate them, by the way” |
| 0:09,8-0:13,5 | seria **po jednej grafice na wymienianą nazwę**: wideo wyspy (10,0), Minecraft (12,0), karta sklepu z grą (13,0), 0,5-3 s każda; słowa padają dokładnie na zmianie | wyliczanka trzech gier |
| 0:14,6-0:15,9 | punch-in, najazd rośnie do końca zdania | „just shut that down” |
| 0:16-0:24 | karta tweeta (16-19,5), potem zrzut kodu (19,5), **najazd na jedną linię z podświetleniem** (20,5-23,5), twarz pod spodem cały czas | cytat z reguły (cytuje słowa reguły) |
| 0:23,5-0:24,4 | punch-in na „so just to recap here” | puenta ironiczna |
| 0:24,5-0:32 | dwie karty nagłówków na ciemnym tle w gwiazdki: wejście z obwódką (24,5), **wymiana kart rozmyciem w bok** (28,0), twarz pod spodem | porównanie dwóch absurdów |
| 0:31,8-0:34,4 | punch-in „NOTED.” (1 s), potem twarz ciasno bez karty 2 s | reakcja na puentę |
| 0:34,4-0:38,5 | wideo AI (programista przy monitorach) 1,5 s, potem karta nagłówka | „devs say Claude refuses…” |
| 0:39-0:42 | karty postów (okno komentarza, „Bug Description”), wymiana w bok rozmyciem (40,0) | „modding, crash reports” |
| 0:42-0:44,5 | glitch, logo i telefon Claude na jasnym tle (stock) | „they really locked it down” |
| 0:44,4-0:47,4 | punch-in i twarz bez karty | „AI companies trained on everything” |
| 0:47,5-0:52,5 | zdjęcie osoby (1,5 s), karta nagłówka z **żółtym markerem rysowanym po cytacie** w chwili, gdy cytat pada (50,5-52,5) | cytat dyrektora |
| 0:53-0:58,7 | punch-in, w 0:56,35 **whip-zoom z rozmyciem ruchu** na „got it” | zwrot |
| 0:59,3-1:07 | karta tweeta na tle rozmytej grafiki gry (59,5), mail (62,0), post Reddita na tle mapy gry (65,5), wymiany w bok | „indie devs get extortion emails” |
| 1:07,5-1:10 | komunikat o anulowaniu, szary, z kreską pod zdaniem | skutek |
| 1:10-1:13,6 | twarz bez karty, najazd (ok. 3 s) | „but yeah, sure” |
| 1:13,6-1:16,3 | logo Grok i Gemini w górnym pasie, ukośny podział | „just open Gemini or Grok” |
| 1:16,5-1:17,9 | **klip filmowy** (aktor pisze szybko na komputerze), ok. 1,4 s | „…ask the same thing five minutes later” |
| 1:18-1:23,5 | tylko twarz, powolny najazd 1,0 -> 1,5 | żart o dzieciaku z kartami graficznymi |
| 1:23,5-1:25,2 | **zoom-out na plan szeroki** (cała sylwetka, ok. 0,55x) | „so who's wrong?” (pytanie do komentarzy) |
| 1:25,2-1:30,6 | twarz ciasno, powolny najazd do końca; koniec bez planszy | pytanie 85-87,5; CTA „follow me” ok. 1:28; obietnica „I'll keep telling you what your AI won't” |

## Opis techniczny

**Hak 0-3 s.** Obraz: kolorystyka i układ czatu produktu, o którym mowa (jasne tło), twarz wycięta i osadzona na tym tle, a w górnym pasie krótki skecz zsynchronizowany ze słowami (ok. 1 zdarzenie na sekundę: wiadomość, odpowiedź, wpisywanie). Tekst: napisy od klatki 0. Dźwięk: mowa zaczyna się w 0,03 s (zero rozbiegu), SFX ani muzyki nie wykryłem [NIEPEWNE]. Pętla otwarta do 4,6 s, gdzie twarde cięcie na punch-in z pytaniem „WHAT'S GOING ON?” daje pierwszy reset uwagi.

**Układ.** Dwa stany. (1) **Twarz pełny kadr + panel u góry**: panel zakrywa górne ok. 37 % (do ok. y 700 z 1920), twarz **nie jest w boksie**, tylko przycięta panelem (czapka ucięta, oczy widoczne), napisy na ok. 71 % wysokości (środek ok. y 1365), czyli na klatce piersiowej pod brodą. (2) **Sama twarz**, w trzech skalach: szeroka 1,0, punch-in 1,6, szeroki plan 0,55. Brak kółka w rogu, brak boksu, brak paska postępu, brak lower thirda, brak ekranu końcowego. Grafika zawsze wymienia się twardym cięciem albo rozmyciem w bok, bez zanikania.

**Napisy.** Gruby, kwadratowy sans (podobny do Rajdhani/Saira Bold, nazwy kroju nie ustaliłem [NIEPEWNE]), WIELKIE litery, **linia 1-3 słów**, zmiana linii na granicy słów i przecinków; biały tekst, **aktualnie mówione słowo żółte** (ok. #FFD400), słowa nie dim; za tekstem ciemny półprzezroczysty box z zaokrąglonymi rogami (ok. 60-70 % czerni, twarz przez niego nie prześwituje wyraźnie); bez pop-skali wejścia, którą by się dało zmierzyć z klatek co 0,1 s. Wszystkie linie wtopione. Pozycja stała mimo zmian kadru.

**Zoomy.** Punch-in to **twarde cięcie** (scena > 0,25), nie rampa: 4,6, 8,3, 14,6, 31,8, 44,3, 53,0, 56,4 (z rozmyciem), 58,8, 70,2, 71,0, 83,6 i 85,2. Ok. 12 w 90 s = jeden co ok. 7 s, głównie na puentach i zwrotach („noted”, „got it”, „so who's wrong”). Na końcu i w środku powolny najazd w obrębie jednego ujęcia (ok. +0,5 w 4-5 s). Pod kartą zoomu nie ma (jak u nas).

**Grafika i dowody.** Karty źródeł są przerysowane (czysty tekst na białej karcie, serif dla nagłówków, sans dla tweetów, awatar i znaczek „zweryfikowany”), na ciemnym tle z gwiazdkami; część kart ma rozmytą okładkę tematu zamiast ciemnego tła (59,5, 65,5). Treść karty jest widoczna 2,5-4 s; w środku karty rusza się podświetlenie (marker, podkreślenie, zoom na linię kodu). Wymienianie nazw (gry, firmy) dostaje osobną grafikę na 0,5-3 s dokładnie na słowie. Memy: jeden klip filmowy 1,4 s i zero memów obrazkowych. Emoji i ikon nie ma.

**Przejścia.** Twarde cięcie (większość), wymiana kart rozmyciem w bok ok. 0,15-0,25 s (28,0, 38,5, 40,0, 62,0, 67,0), glitch lub rozmycie z mieszaniem klatek przy logo (5,5, 42,0), whip-zoom z rozmyciem ruchu (56,4).

**Dźwięk [NIEPEWNE: tylko pomiary].** RMS co 50 ms: poza oknami słów nie ma ani jednego impulsu wyższego o 8 dB od sąsiedztwa, czyli brak oddzielnych SFX w przerwach między słowami (przerwy są za krótkie, żeby je zmierzyć, więc SFX pod mową nie wykluczam). Cichych odcinków w pasmach do -45 dB nie ma (`silencedetect` zwraca 0), poziom w przerwach -20..-36 dBFS i zmienny, więc stałego podkładu muzycznego głośniejszego niż ok. -36 dBFS nie widać. Wniosek: głos prawie solo, ewentualnie bardzo cichy podkład. Kamil powinien posłuchać, zanim to wejdzie do kryteriów.

**Tempo.** 203 słów/min, przerwy do 0,32 s: cięcie bardzo ciasne, praktycznie bez oddechu. U nas domyślnie `pads` zostawia 0,15 + 0,12 s z pauzy powyżej 0,45 s (czyli ok. 0,27 s), więc jesteśmy blisko, ale `ZASADY-KAMILA-SHORTY.md` każe zostawiać oddech między zdaniami.

**CTA i koniec.** Pytanie do komentarzy tuż przed CTA („kto się myli: X czy Y”), potem CTA ze słowami obiecującymi wartość (co autor będzie mówił dalej) w ostatnich 3 s, twarz ciasno, **brak planszy**, twarde ucięcie 0,2 s po ostatnim słowie. **Pętli nie ma**: ostatnie zdanie nie łączy się z pierwszym (to zwykły koniec, bez domknięcia hakiem).

## Co mamy, czego nie mamy

Priorytet 1 = największy wpływ na retencję przy małym koszcie, 3 = dopieszczenie.

| technika | czas w filmie | mamy? | co zbudować |
|---|---|---|---|
| napisy: 1-3 słów, aktywne słowo w akcencie, linia kończy się na przecinku | cały film | **tak**: `build_edl.py` (grupy do 3 słów i 18 znaków, `caption_ahead: "same"`, `caption_pop`) | nic; różnica: box u nas pełny, nieprzezroczysty (patrz niżej) |
| punch-in twarz na puentach, powolny najazd na długim ujęciu | co 7 s; 4,6, 8,3, 14,6 ... 85,2 | **częściowo**: `beats`/`beatfx` + `zoom_every_cut` + `drift` 0,05; kamera punch ma sufit `1.38` w `build_edl.py` (rampa 0,3 s) | **P1 `jump_zoom`**: klucz planu, który na początku zdania/puenty robi twarde cięcie na 1,6 i trzyma do końca zdania, bez rampy; sufit 1,65 tylko gdy `face_track.zmax_at` pozwala na zachowanie brody w kadrze. Zmierzyć: stosunek szerokości głowy po do przed (cel 1,5-1,7) i odstęp między skokami (cel 6-9 s) |
| karty-źródła z czystego tekstu (tweet, nagłówek, post, mail, komunikat), serif/sans, awatar, badge | 16-19,5; 24,5-31,5; 36-38; 39-41,5; 49-52,5; 59,5-65; 65,5-67; 67,5-69,5 | **nie**: `web` wymaga prawdziwej strony (https, zrzut Chrome), `maxim` to zwykły tekst bez wyglądu źródła | **P1 `quote`**: typ karty 9:16 w górnym pasie z polami `kind` (tweet / headline / post / mail / notice), `source`, `handle`, `text`, `mark` (fraza do podświetlenia) i `mark_word` (słowo kotwica, na którym marker się rysuje); wygląd generyczny (nie kopia cudzej marki), flaga „przerysowane, wymagana zgodność z oryginałem” w specu (ZASADY: każde twierdzenie prawdziwe). Zmierzyć: udział zdań z dowodem (cel >= 40 % czasu z grafiką) |
| marker rysowany po cytacie w chwili, gdy słowo pada | 50,5-52,5; 68 | **tak**: `web` (marker na cytowanym zdaniu, `vZoom`) | podpiąć ten sam mechanizm pod `quote.mark_word` |
| wymiana kart rozmyciem w bok bez pustej klatki | 28,0; 38,5; 40,0; 62,0; 67,0 | **częściowo**: `no_fade_out` + `no_fade_in` (zakładka 1 klatka, bez rozmycia) | **P2 `swap: "blur_x"`**: ostatnie 0,15 s karty ucieka w bok z rozmyciem ruchu, następna wjeżdża z drugiej strony; filtr CSS w karcie, bez ffmpeg. Zmierzyć: brak klatki gołej twarzy (`viewer_pack.py`) |
| grafika na każdą wymienianą nazwę, 0,5-3 s, na słowie | 10,0; 12,0; 13,0; 73,6 (Grok/Gemini) | **częściowo**: `broll.py` (Pexels, kotwica słowo) i `meme`; brak krótkiej karty obrazu/loga na słowo, a ZASADY wymagają min. 3,5 s na kartę `web` (to dla kart do czytania) | **P1 `flash_visual`**: obraz lub logo (lokalny plik, `style/logos/`, bez pobierania cudzych znaków do repo) 0,5-1,5 s przypięty do słowa, w górnym pasie. Wyjątek od 3,5 s tylko dla tego typu (nic do czytania). Zmierzyć: liczba wymienionych nazw własnych z wizualizacją (cel >= 60 %) |
| układ: panel na górnym ok. 37 %, twarz pełny kadr pod nim bez boksu, napisy na ok. 71 % | 0-4,6; 6-8,3; 16-32; 34-42 ... | **nie**: `SPLIT` ma boks twarzy 820x680 z zaokrągleniem, a `ZASADY` zabraniają „połowy twarzy” (u Zacka głowa ucięta tylko czapką) | **P2 `layout: "top"`**: panel 700 px wysokości na pełnoekranowej twarzy, `face_target_y` ok. 0,55 żeby brodę zostawić nad napisami, napisy `caption_y` ok. 1365. Sprawdzić `head_check.py`: cała broda widoczna, uszy poza panelem |
| tło panelu: ciemne z gwiazdkami; inne: rozmyta okładka tematu | 24,5-32; 59,5-67 | **nie** (motyw: statyczny gradient) | **P3**: tło karty `bg_img` (rozmyty lokalny obraz) i animowane drobne cząsteczki (CSS, tanio) |
| hak jako skecz w UI produktu na tle w kolorze produktu, twarz wycięta na tym tle | 0-4,5 | **częściowo**: `scene` ma element `chat` i `say`; maska mówcy w `behind.py` (RVM) | **P2 `bg_swap` hook**: pierwsze 4 s twarz z maski na kolorze tła z motywu, panel `scene` z czatem sterowany słowami; po 4,6 s cięcie na tło studia. Koszt: matting całego haka (RVM CPU). Zmierzyć: obraz zmienia się co <= 1 s w pierwszych 4 s |
| pytanie otwierające pętlę i twarde cięcie z punch-inem w 4,6 s | 4,6 | **częściowo**: `critic` C3 (zmiana w 1,5 s), hak `maxim pill` | **P2 reguła haka** w `grammar.json`: po haku (<= 4,5 s) obowiązkowy reset uwagi (punch-in lub nowa grafika) w 4-5 s; do `critic` jako ostrzeżenie |
| zoom-out na szeroki plan na pytaniu do komentarzy | 83,5-84,5 | **nie** (zoom nie schodzi poniżej 1,0) | **P3 `wide_reveal`**: jeden skok na 0,6x z oddychającym kadrem 1 s przed końcowym pytaniem, tylko gdy materiał ma zapas kadru (nagranie 4K lub szeroki kadr); `face_track` musi znać dolną granicę |
| przejście glitch / mieszanie klatek do logo | 5,5; 42,0 | **nie** | **P3**: flash 0,2-0,3 s (`light-leak` już na liście `REF-shorts-memes.md` nr 2); wspólny klucz `transition: "glitch"` |
| whip-zoom z rozmyciem ruchu na „got it” | 56,35 | **nie** | **P3**: wariant `jump_zoom` z 3 klatkami rozmycia radialnego (ffmpeg `zoompan` + `gblur`); używać 1-2 razy na film |
| klip filmowy (mem wideo) 1,4 s pod żartem | 76,5-77,9 | **nie z założenia** (ADR-0008, ryzyko Content ID) | **nie budować**; zostaje mem obrazkowy (`meme`). Decyzja Kamila |
| CTA: pytanie do komentarzy, potem obietnica kolejnych treści, bez planszy, ucięcie 0,2 s po słowie | 1:25-1:30,6 | **częściowo**: karty `end`/`cta`; `RESEARCH.md` pkt 12 (pętla) i `tail` | **P2 reguła treści** (zero kodu): ostatnie 8 s = pytanie do komentarzy + zdanie obiecujące, co dalej na kanale; w `critic` ostrzeżenie, gdy short ma plansze końcową dłuższą niż 1 s. Pętla Zacka nie zamyka się, więc nie traktować jako wzoru domknięcia |
| tempo 203 słów/min, przerwy do 0,32 s | cały film | **tak**: `pads` (`mingap` 0,45, `keep_l` + `keep_r` = 0,27 s) | **P1 decyzja**: pozwolić na `pads: {"mingap": 0.35, "keep_l": 0.14, "keep_r": 0.12}` w shortach i dopisać w `ZASADY` wyjątek („oddech tylko po zdaniu kończącym wątek”). Zmierzyć: słowa/min i maks. przerwa po montażu (`verify_cut.py`), nie obcinać głosek |
| napisy w boxie półprzezroczystym (ciemny, zaokrąglony) | cały film | **częściowo**: `caption_box` (nieprzezroczysty `--ink`, ASS) | **P3**: box jako PNG/karta zamiast ASS BorderStyle 3 (README: libass rysuje box osobno dla każdego koloru). Koszt wyższy niż zysk, najpierw `caption_box` w ciemnym `--ink` |
| 60 fps | cały film | **nie** (`FPS = 30`, `assemble.py fps=30`), plan z `REF-shorts-breakingbreach.md` | **P3**: źródło Zacka 60 fps, nasza kamera 30; płynność tylko kart. Nie zmieniać przed zmianą kamery |
| głośność -12,4 LUFS | cały film | u nas -14 (`final_check.sh`) | nic: YouTube ścisza do ok. -14, więcej nie daje retencji |
| SFX, muzyka | cały film | `music_duck`, `CARD_WHOOSH`, `sfx_style v2` | brak dowodu, że wzorzec je ma [NIEPEWNE]; nie zmieniać do czasu odsłuchu |

## Kolejność wdrożenia (propozycja)

1. `jump_zoom` (twarde cięcia 1,6x, cel: odstęp 6-9 s) i wyjątek `pads` dla shortów: **obie tanie, obie wpływają na każdy short**.
2. `quote` (tekstowe karty źródeł z markerem na słowie): 10 z 24 grafik wzorca, usuwa zależność od zrzutów stron.
3. `flash_visual` (grafika na każdą wymienioną nazwę, 0,5-1,5 s): odpowiada za wrażenie „stale coś się dzieje” (grafika w 61 % czasu).
4. `layout: "top"` (panel 37 % nad pełną twarzą) i `swap: "blur_x"`.
5. Hak z `bg_swap` i reguła „reset uwagi w 4-5 s”.

Uwagi do pamiętania: `ZASADY-KAMILA-SHORTY.md` mają pierwszeństwo przed wzorcem (zakaz zoomów pod kartą, brak pustej klatki, karta `web` min. 3,5 s). Wzorzec Zacka łamie dwie zasady Kamila (twarz uciętą panelem i krótkie karty), więc `layout: "top"` i `flash_visual` wymagają jego zgody przed budową.
