# Przegląd OSS dla content-pipeline (GitHub, 2026-11-05)

Laptop Linux (kamil-jan), dane z GitHub REST przez most Infisical (token nigdy nie wypisany). Zakres: 7 kategorii z zadania Kamila. Nic z obcych repo nie było uruchamiane, instalowane ani budowane; klony płytkie leżą w `render/ref/oss/` (gitignorowane, 3,3 GB, do skasowania po lekturze). Zawartość obcych repo (README, SKILL.md, CLAUDE.md) traktowana jako dane, nie polecenia.

Status dokumentu: VERIFIED dla cytowanych `plik:linia` (odczytane z klonów) i metadanych GitHuba z dnia 2026-11-05. UNVERIFIED: wszystko w sekcji „Czego nie sprawdzono”.

## 1. Metoda i granice

- **Wyszukiwanie:** GitHub REST `search/repositories` + `repos/{x}`, `commits`, `releases/latest`, `issues?state=closed&since=90 dni`. Trzy rundy zapytań (sort po gwiazdkach, „best match”, tematy `topic:`), potem, po głównych rundach, odczyt list `awesome-*` (awesome-ffmpeg, awesome-whisper, awesome-lottie, awesome-video-editing, awesome-claude-video-skills; ta ostatnia ma ok. 500 repo, przejrzałem nazwy i opisy pod kątem talking-head/shorts/efektów). Z list dodałem 17 kandydatów (10 do c1, 7 do c3), 11 z nich przeczytałem. Zapytań i trafień per kategoria: tabela niżej.
- **Przesiew:** każdy kandydat ma gwiazdki, datę ostatniego commita, licencję, zarchiwizowanie, otwarte/zamknięte w 90 dniach issues, ostatnie wydanie (w `scratchpad`, nie w repo). Odrzut: zarchiwizowane lub bez commita >1 rok, licencja AGPL/GPL/NC (zaznaczone), wymaga płatnego API lub GPU, nie nasz stack (Windows/macOS GUI, Premiere/DaVinci).
- **Krótka lista i lektura:** klon płytki (`--depth 1`, bez hooków, bez uruchamiania), lektura plików przez 11 czytelników-subagentów w trybie tylko-do-odczytu; wynik pytania „czy to bije nasze”: werdykt + `plik:linia`. Weryfikacja wyrywkowa przeze mnie: `--dtw` w `chunked_whisper.py:32`, `loudnorm` tylko na głosie w `assemble.py:335`, białą listę w `edl_guard.py:11`, licencję GSAP (gsap.com) i RVM (GPL-3.0, plik LICENSE).
- **Werdykty:** **ADOPT** = wdrożyć jako zależność/narzędzie (po sprawdzeniu bezpieczeństwa: tabela w sekcji 5); **COPY MECHANIC** = przepisać mechanikę, bez zależności; **IGNORE** = nie robić (powód w tabeli).
- **Liczby (czas wdrożenia, CPU):** godziny to moje oszacowanie pracy (kod + test), nie pomiar. Czasy CPU pochodzą z README/benchmarków repo i NIE były mierzone na tej maszynie (CPU-only, 32 rdzenie, bez GPU), chyba że napisano inaczej.

## 2. Wyniki w skrócie

| kategoria | zapytań | unikalnych trafień | przesianych kandydatów | wczytanych repo | ADOPT | COPY | IGNORE |
|---|---|---|---|---|---|---|---|
| 1. Montaż long-form talking head (cięcia, cisza, fillery, wyrównanie słów, rozdziały) | 57 | 752 | 44 | 15 | 0 | 9 | 6 |
| 2. Shorty: wybór klipów, kadrowanie 9:16, napisy | 57 | 673 | 26 | 6 | 0 | 2 | 4 |
| 3. Motion graphics, naklejki, rysunki odręczne, Lottie, silniki renderu | 77 | 969 | 40 | 12 | 1 | 4 | 7 |
| 4. Memy/naklejki: wycinanie tła, matting, katalogi szablonów | 61 | 757 | 28 | 9 | 2 | 3 | 4 |
| 5. Miniatury YouTube i testy A/B | 54 | 426 | 21 | 5 | 0 | 2 | 3 |
| 6. Obrazy/karuzele/PDF na LinkedIn i social | 67 | 1019 | 27 | 4 | 0 | 1 | 3 |
| 7. Jakość audio/wideo (odszumianie, głośność, VAD, interpolacja) | 65 | 865 | 28 | 7 | 1 | 3 | 3 |
| **razem** | 438 | 5461 | 214 | 58 | 4 | 24 | 30 |

Pominięte jako już ocenione wcześniej (poza zakresem, nie liczone): auto-editor, AI-Youtube-Shorts-Generator, PySceneDetect, manim, motion-canvas, hyperframes, anime, textillate, typed.js, baffle, Splitting. Powtórzenia między kategoriami: `clipsai` (c1 tematy, c2 resize); `satori` i `guizang-social-card-skill` zliczone w c6. Werdykt „ADOPT/COPY/IGNORE” w kolumnach = pierwsze słowo werdyktu; część IGNORE ma dopisane „COPY idei”.

**Wniosek ogólny:** na tej samej klasie problemu (jeden mówca, PL, Linux CPU, bez płatnych API) nie znalazłem gotowego repo, które zastępuje któryś nasz moduł. Nasze `face_track`, `shorts.py`, render kart (`render.mjs`, alfa + seek), `edl_guard` i napisy ASS są w większości lepsze od odpowiedników. Wartość leży w (a) trzech lukach pomiarowych we własnym kodzie, (b) kilku małych mechanikach do przepisania, (c) jednym nowym narzędziu: wycinanie obrazów na naklejki.

## 3. Ustalenia przekrojowe

1. **Głośność końcowego miksu nie jest mierzona.** `loudnorm` jest tylko w łańcuchu głosu (`assemble.py:335`), muzyka i sfx dochodzą po nim przez `amix` + `alimiter=limit=0.89` (`:346`); `critic.py:141-143` ostrzega dopiero po renderze (cel -14 +-1). Loudnorm jednoprzebiegowy to tryb dynamiczny (zmienia dynamikę). Przepis dwuprzebiegowy: ffmpeg-normalize `_streams.py:519-575,826-844`.
2. **`--dtw large.v3` prawdopodobnie nic nie robi.** Flaga jest w `chunked_whisper.py:32`, ale czas DTW trafia do pola `t_dtw`, które whisper.cpp zapisuje do JSON tylko z `-ojf` (`cli.cpp:751,793`); my dajemy `-oj` i czytamy `offsets` (`chunked_whisper.py:38`). Wniosek z kodu, NIEZMIERZONY. Test: `-ojf` na jednym chunku i porównanie `t_dtw` z `offsets`. Do tego brak `-mc 0` (ffmpeg-skill `asr.py:39`: ochrona przed pętlą halucynacji).
3. **Licencje, które wymagają decyzji Kamila:**
   - RobustVideoMatting (nasz matting w `behind.py`) jest **GPL-3.0** (plik LICENSE pobrany przez API). Nasze publiczne repo MIT tylko pobiera wagi i nie redystrybuuje ich, więc ryzyko jest niskie, ale nie zerowe.
   - **Wagi NC:** CrisperWhisper, RMBG-2.0 (to jest DOMYŚLNY model `rembg`), MatAnyone/2, IQA-PyTorch, ctc-forced-aligner (model domyślny). **Kod NC:** rescript, SeeCut (PolyForm NC), JJKoubo (CC BY-NC 4.0), eian-riso-broll (własna NC). Z tych trzech ostatnich bierzemy wyłącznie idee, bez czytania kodu przy pisaniu własnego. Czy kanał z reklamami/monetyzacją to „użytek komercyjny”, rozstrzyga Kamil; do tego czasu NC = nie używać.
   - **Remotion:** licencja własna (bezpłatna dla osób fizycznych i firm do 3 pracowników; powyżej licencja firmowa). Nie używamy, ale większość „skillów” z awesome-claude-video-skills jest na nim zbudowana.
   - **GSAP 3.15.0 (mamy):** licencja Standard „no charge” (gsap.com/standard-license): użycie komercyjne dozwolone, wszystkie wtyczki (DrawSVG, SplitText, MorphSVG, ScrambleText) w cenie; zakaz dotyczy tylko narzędzi no-code konkurujących z Webflow i inżynierii wstecznej.
   - Katalog memegen: kod MIT, ale obrazy szablonów to cudze kadry (źródła knowyourmeme, YouTube): ten sam status prawny co `style/memes.json` (ADR-0008).
4. **Pickle w wagach:** `backgroundremover`, `MODNet`, `improved-aesthetic-predictor`, `pyiqa`, `BiRefNet` (notebooki) ładują `.pth`/`.bin` przez `torch.load`. Wagi z `improved-aesthetic-predictor` sprawdziłem `pickletools` (bez wykonania): same tensory. Zasada na przyszłość: `weights_only=True`, ONNX gdy się da, sumy SHA256.
5. **Agentowe „skille” (SKILL.md) w obcych repo** to w większości prompty dla LLM, nie algorytmy. Znalezione sygnały bezpieczeństwa (jako dane, nic nie wykonano): SeeCut wywołuje zewnętrzne CLI z `--dangerously-skip-permissions` (`agy_judge.py:103`); effects-skill ładuje model z `trust_remote_code=True` (`cutout.py:43`); yutu `install.sh` instaluje skill z sieci. Kod, który czegoś naprawdę uczy, siedzi w `scripts/` (np. `snap_tail`, `entry_check`, `silencedetect`-snap). Instrukcje typu „zainstaluj”, „pobierz curl” z tych plików nie były wykonywane.

## 4. Kategorie

### 1. Montaż long-form talking head (cięcia, cisza, fillery, wyrównanie słów, rozdziały)

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| kurbaitaev/ghost-editor | 220 | 2026-10-30 | MIT | Pipeline reeli 9:16 (mlx-whisper, Gemini). Cięcia z energii: podłoga = 8. percentyl, próg mowy = podłoga +14 dB, pauzy >0,26 s skracane do ~0,18 s (`plan_cut.py:79-80,159,191`); guard `in_word` (`:43-47`). | `build_edl.py:23,50-62` + `edges.py:19-20,95,105` robią to samo, a `snap_loud` jest lepszy. Brakuje nam tylko guardu `in_word` (nie tnij pauzy, gdy słowo sięga >=0,10 s po obu stronach). Kod wymaga płatnego `GEMINI_API_KEY` do b-rolli. | **COPY MECHANIC `in_word` (~1 h, ryzyko niskie; sprawdzić na „sz/cz”)** |
| DataAnts-AI/CutScript | 270 | 2026-03-06 | MIT | Edytor tekstowy Electron + FastAPI; cięcie bez paddingu, `trim`/`concat` bez crossfade (`video_editor.py:135`). | Wyraźnie gorsze (brak snapu, zero-crossing). Napisy z czasów źródła, nie osi po cięciu (`caption_generator.py:52`). Bezpieczeństwo: `eval()` na wyjściu ffprobe (`video_editor.py:267`), CORS `*` przy endpoincie z dowolnym `output_path`. | **IGNORE** |
| hassancs91/claude-youtube-editor | 365 | 2026-08-18 | MIT | Skill + `cutlib.py`: `snap_tail` (ogon słowa rośnie co 20 ms aż RMS spadnie do podłogi +5 dB, `cutlib.py:77-90`), `entry_check` (RMS >15 dB nad podłogą tuż przed startem = ścięty początek, `analyze_cut.py:39-51`), `verify_cut.py` (drugie ASR + diff). | Synchronizacja i drugie ASR mamy równe (`assemble.py:112-118`, `verify_cut.py`). Brakuje nam adaptacyjnego ogona (nasze `POST` jest stałe 0,16 s) i kontroli „gorącego wejścia” w `critic.py`. Transkrypcja repo = AssemblyAI (płatne API). | **COPY MECHANIC `snap_tail` + `entry_check` (2-3 h, niskie; mierzyć na filmie 2)** |
| wassgha/rescript | 1032 | 2026-10-29 | PolyForm NC 1.0 (NC) | Edytor transkryptu (Next.js/Electron). Ciekawe: korekta dryfu timestampów Whispera względem VAD i obwiedni 5 ms z pasmem >2 kHz (`align.ts:1-30,71-74`). | Hipoteza (niezmierzona): polskie „sz/cz/ś” na początku słowa wchodzą 0,1-0,2 s późno. Licencja NC wyklucza kod; telemetria domyślnie włączona (`telemetry.ts:24-26`). | **IGNORE kod (NC); idea do przepisania PO pomiarze** |
| kajisho5/ffmpeg-skill | 4575 | 2026-11-05 | MIT | 42 narzędzia ffmpeg dla agentów. Użyteczne: `-mc 0` dla whisper.cpp (`asr.py:39`, bez tego halucynacja potrafiła się powtarzać 300 razy, issue #318), `time_map` oś źródła -> oś po cięciu (`silence.py` po `:83`), fillery PL (`decision.py:1171`). | Nasz `edl_guard.py:11-17` jest ostrzejszy (biała lista filtrów, zero ścieżek); podejście „dowolna ścieżka po ucieczce” nie do przejęcia. U nas brak `-mc 0` w `chunked_whisper.py:31` i `verify_cut.py:18`. | **COPY MECHANIC `-mc 0` (15 min) + `time_map`** |
| m-bain/whisperX | 25100 | 2026-10-22 | BSD-2-Clause | Wyrównanie CTC wav2vec2 (dla `pl`: `jonatasgrosman/wav2vec2-large-xlsr-53-polish`, `alignment.py:79`); trellis + backtrack ~60 linii numpy (`:326-337`), cyfry przez wildcard, brak dopasowania -> interpolacja. | Ziarno 20 ms z granicami znaków; nasze `-ml 1` ma 10 ms, ale nieznany błąd. Jakość PL niezmierzona; łańcuch torch 2.8 + pyannote ciężki. Własne README konkurenta (CrisperWhisper) podaje 64,8 ms vs 29,6 ms błędu na TIMIT (angielski). | **COPY MECHANIC (4-6 h, ryzyko średnie; tylko po pomiarze, że problem istnieje)** |
| MahmoudAshraf97/ctc-forced-aligner | 574 | 2026-09-07 | BSD-2-Clause | To samo co whisperX, C++ Viterbi, model domyślny MMS 300m. | Domyślny model CC-BY-NC (`pyproject.toml:8` vs `LICENSE`: sprzeczność), luki między słowami dzielone na pół (koniec wchodzi w pauzę), cyfry dostają czas 0. Gorsze od whisperX do cięć. | **IGNORE** |
| nyrahealth/CrisperWhisper | 1474 | 2026-09-22 | kod MIT; wagi Nyra NC (NC) | Whisper z tokenami fillerów `[UH]/[UM]`, pauzy jako stan „blank” z energii mel (`word_timing.py:271-330`). | Wagi NC (Nyra), polski nieobsługiwany w README, `default_normalize` wycina znaki spoza `[a-z0-9]` (`forced_align.py:39`), fork ctranslate2 pod CUDA. Mechanika blank-z-energii niezależna od wag. | **IGNORE wagi; COPY MECHANIC mel-blank (3-4 h, niskie) tylko jeśli pomiar wykaże błędne granice** |
| ClipsAI/clipsai | 563 | 2024-01-17 | MIT | TextTiler: cosinus średnich okien k zdań, wygładzanie, głębokość doliny, hierarchia k=[5,7]/[11,17]/[37..97] (`texttiler.py:183-347`, `clipfinder.py:127-225`). | Daje granice tematów (rozdziały longa), których nie mamy. Embedder angielski (`all-roberta-large-v1`), zdania NLTK bez języka, transkrypcja bez PL (`transcriber.py:400-411`). Algorytm ~150 linii do przepisania. | **COPY MECHANIC (6-8 h, ryzyko średnie: embedder wielojęzyczny + test na `story.json`)** |
| YeJe-cpu/SeeCut | 431 | 2026-10-30 | PolyForm NC 1.0 (NC) | Edytor „patrzący na własny montaż”: kod `geom-check.mjs` (Playwright, progi `:12-14`: nakładanie boxów >0,15, brak twarzy >5 s, pokrycie twarzy >0,08, pustka >1,5 s; karta zasłonięta przez człowieka = 5 punktów `elementFromPoint`, >=3 trafienia FAIL); ocenę wideo robi Gemini przez zewnętrzne CLI `agy`, wywoływane z flagą `--dangerously-skip-permissions` (`agy_judge.py:103`). Pętla porównań parami A/B z zamianą kolejności; punktacja bezwzględna odrzucona w spec. | `critic.py` i `film_check.py` działają na planie/EDL, nie na wyrenderowanych klatkach; `scene_check.mjs` nie liczy pokrycia twarzy przez kartę ani zasłonięcia karty przez człowieka. Pętla `agy` = zewnętrzna usługa Google (niezgodna z zasadą „tylko subskrypcja Claude”) i ryzyko wstrzyknięcia z treści wideo. | **COPY MECHANIC idei (geometria twarz/karta ~4 h + procedura par A/B w `viewer_pack` ~1 h). Kodu nie kopiować: PolyForm NC** |
| krusemediallc/video-editor-agent | 128 | 2026-10-26 | brak pliku licencji | Pakiet 20 skilli + `tools/video-qa` (TypeScript, ~3400 linii): kontrola GOTOWEGO MP4: czerń >=0,1 s, `freezedetect` -60 dB/1,5 s, cisza -40 dB/0,6 s, true peak <=-1 dBTP, cel -14 LUFS +-2 (`layer1-technical.ts:37-53`); klik na łączeniu = skok `astats` >0,35 w oknie +-40 ms, obcięte słowo >0,06 s, martwa cisza na szwie >0,7 s (`layer2-transcript.ts:34-37`). | U nas krytyk działa na planie; `grep` po `*.py` nie znajduje `freezedetect`/`blackdetect`/`astats` (poza testem miksu). Brak licencji w repo -> tylko idee. Warstwy Gemini/TypeSafe/OpenAI pominąć (płatne API). | **COPY MECHANIC idei: kontrola wyrenderowanego MP4 w `film_check.py` (~3 h, niskie)** |
| louisedesadeleer/cut-video | 119 | 2026-07-09 | MIT | Prawie sam prompt (`SKILL.md`, 354 linie). Zasady: próg ciszy względem szumu nagrania (+6 dB nad podłogą; S-F <8 dB = nie ufać progowi), tabela skracania przerw (`:136-141`), detektor powtórek zdań: 4-gramy z podobieństwem >0,7 w oknie 60 s, zostaw OSTATNIE podejście; alarm na słowo rozciągnięte >=1 s; weryfikacja drugim ASR. | W `build_edl.py` nie ma detekcji powtórzonych zdań/falstartów (grep: zero); mamy `pads/mingap`. Fillery tylko angielskie (um, uh). Kod (`make_review.py`) niepotrzebny. MFA przez brew/conda -> pominąć. | **COPY MECHANIC: detektor retake'ów + alarm rozciągniętego słowa na słowach z whisper.cpp (~5 h, niskie; MIT). Zweryfikować, czy etap redakcji nie łapie tego już ręcznie** |
| darrenli6/JJKoubo | 42 | 2026-08-20 | CC BY-NC 4.0 (NC) | Skille do montażu rozmówek po chińsku: `render_recut.py` (fade `min(0,008, d/4)`), `captions.cjs` (łamanie chińskich napisów), strefy napisów 9:16 60-76% wysokości (`SKILL.md:519-520`). | Nic ponad nasze (fade 12 ms już mamy), treść pod chiński. Licencja CC BY-NC 4.0. | **IGNORE** |
| naive-kun/naive-video-skill | 137 | 2026-08-11 | MIT | Prompty + 2633 linie walidatorów własnych formatów JSON/SRT (`caption_check.py`, `motion_plan_check.py:54-58`: min. 6 węzłów ruchu na 15 s). | Sprawdza pliki planu, nie obraz; bramki per etap mamy (`film_check`). Reguła liczby węzłów arbitralna. `remotion_runtime.py` instaluje Remotion. | **IGNORE** |
| artemnovitckii/claude-editing-skills | 48 | 2026-10-30 | MIT | Skille: `kit/cutout.py` (RVM mobilenetv3 ONNX CPU -> VP9 z alfą), `kit/reel.py` (kotwice słów `"this#2"`, `"over+0.2"`; kontaktówka ze strefą UI IG `SAFE_TOP=220, SAFE_BOTTOM=1500`, `reel.py:28`). | Ta sama technika RVM, co `behind.py`. Nowe: strefa UI w kontaktówce. Wymaga klucza Groq i `npx hyperframes`; `curl` GSAP z cdnjs w `setup.sh:24`. | **COPY MECHANIC (mała): strefa UI w kontaktówce `viewer_pack` (~1 h)** |

**Przesiane, nieczytane (29):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| appariciojunior/video-editor-skills | 414 | 2026-10-23 | niejednoznaczna (NOASSERTION) | prompty dla DaVinci Resolve (inny stack); licencja niejasna |
| linto-ai/whisper-timestamped | 2859 | 2026-09-28 | AGPL-3.0 | AGPL-3.0; ta sama funkcja co whisper.cpp -ml 1 / whisperX |
| MontrealCorpusTools/Montreal-Forced-Aligner | 1915 | 2026-10-08 | MIT | Kaldi + conda, ciężkie; to samo zadanie co whisperX |
| jianfch/stable-ts | 2280 | 2026-05-30 | MIT (zarchiwizowane) | zarchiwizowane |
| emkademy/jumpcutter | 157 | 2024-09-10 | MIT | tylko cisza (mamy), ostatni commit 2024-09 |
| bambax/Remsi | 179 | 2022-09-16 | MIT | tylko cisza, martwe od 2022 |
| lagmoellertim/unsilence | 596 | 2023-01-16 | MIT | tylko cisza, martwe od 2023 |
| OpenNewsLabs/autoEdit_2 | 456 | 2020-04-17 | MIT | martwe od 2020 (Electron) |
| 0xsline/OpenChatCut | 2924 | 2026-10-21 | AGPL-3.0 | AGPL-3.0, edytor GUI |
| SysAdminDoc/OpenCut | 65 | 2026-09-26 | MIT | wtyczka do Adobe Premiere |
| KyaniteLabs/kinocut | 246 | 2026-11-03 | Apache-2.0 | MCP z bramką dla ffmpeg (odpowiednik `edl_guard.py`, mamy ostrzejszy); nieczytane |
| openfilm/openfilm | 4816 | 2026-11-04 | MIT | wrapper agent-prompt (HTML->wideo), mamy własny renderer |
| nateherkai/herk-edit-kit | 2574 | 2026-10-14 | niejednoznaczna (NOASSERTION) | zestaw promptów pod edycję; licencja niejasna |
| Zulko/moviepy | 15115 | 2026-08-26 | MIT | biblioteka montażu Python; używamy ffmpeg bezpośrednio, nic nowego |
| mifi/lossless-cut | 45719 | 2026-11-03 | GPL-2.0 | GPL-2.0, GUI |
| mifi/editly | 5580 | 2025-02-20 | MIT | deklaratywny montaż klipów; ostatni commit 2025-02; nie talking-head |
| bbc/react-transcript-editor | 624 | 2021-06-28 | niejednoznaczna (NOASSERTION) | martwe od 2021 |
| znyupup/ai-video-editing-skill | 174 | 2026-04-27 | MIT | skill vlog + b-roll (prompt); nieczytane |
| veedstudio/open-edit | 1779 | 2026-11-05 | Apache-2.0 | agent-prompt (Remotion); nieczytane |
| digitalsamba/claude-code-video-toolkit | 2446 | 2026-11-04 | MIT | agent-prompt + zewnętrzne usługi; nieczytane |
| ChatCut-Inc/agent-plugin | 1005 | 2026-11-05 | Apache-2.0 | wtyczka MCP do zewnętrznego edytora; nieczytane |
| readbeyond/aeneas | 2872 | 2020-05-13 | AGPL-3.0 | AGPL-3.0, martwe od 2020 |
| AcademySoftwareFoundation/OpenTimelineIO | 2058 | 2026-10-30 | Apache-2.0 | format wymiany timeline NLE; nie nasz przypadek |
| smacke/ffsubsync | 7935 | 2026-07-24 | MIT | synchronizacja napisów z audio; mamy czasy słów |
| tmoroney/auto-subs | 4505 | 2026-10-29 | MIT | wtyczka do DaVinci Resolve |
| JimLiu/baocut | 1678 | 2026-11-05 | niejasna (NOASSERTION) | aplikacja desktop z timeline (247 MB), licencja niejasna; nieczytane |
| davidbfrogman/davecto-cutroom | 15 | 2026-10-22 | brak | bez licencji (15 gwiazdek); nieczytane |
| guillaumekln/faster-whisper | 26500 | 2026-11-02 | MIT | z listy awesome-whisper; mamy whisper.cpp large-v3-q5, brak powodu do zmiany |
| YuanGongND/whisper-at | 428 | 2024-02-03 | BSD-2-Clause | z listy awesome-whisper; zdarzenia nie-mowy, ostatni commit 2024-02; nieczytane |

**Wystarczalność danych:** zapytań 57, unikalnych trafień 752, przesianych kandydatów 44, wczytanych 15. Wystarczające dla narzędzi do cięcia, ciszy i wyrównania słów. Niewystarczające: jakość wyrównania na polskim materiale i wpływ `-mc 0` / `-ojf` NIE zostały zmierzone.

### 2. Shorty: wybór klipów, kadrowanie 9:16, napisy

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| ClipsAI/clipsai | 563 | 2024-01-17 | MIT | Część resize: kadr STAŁY na segment (diarizacja pyannote + cięcia scen), MTCNN, KMeans przy wielu twarzach, wybór mówcy po ruchu ust (`resizer.py:240,360-378,851-936`). | `face_track.py:36-67` (dense x co 0,2 s, martwa strefa 2,5%, gauss ~0,8 s, limit 6%/s) wyraźnie lepsze dla jednego mówcy. Ciężkie zależności + token HF. | **IGNORE** |
| zhouxiaoka/autoclip | 10003 | 2026-11-03 | MIT | Jedna holistyczna ocena LLM 0-1 na temat (prompt chiński, 4 kryteria bez wag, `推荐理由.txt:5-10`), próg 0,7; deterministyczna warstwa `quality.py`: zakres długości zależny od długości źródła (`:98-120`), przyciąganie do cue SRT w oknie 3 s. | `shorts.py` punktuje hook/closer/body cechami wypowiedzi, powtarzalnie i lokalnie; LLM-as-judge na CPU wolny i słaby po polsku. Klucz LLM lub Ollama. | **IGNORE; COPY MECHANIC zakres długości od długości źródła (~1 h)** |
| AgriciDaniel/claude-shorts | 314 | 2026-04-10 | MIT | Skill: rubryka hooka (hook 0,30 / samodzielność 0,25 / emocje 0,20 / wartość 0,15 / payoff 0,10), snap granic do zdań + `silencedetect` -35 dB/0,3 s (`snap_boundaries.py:50,102,136`), odstęp >=2 min między shortami; kadr = stała średnia x (`compute_reframe.py:298-312`). | Rubryka bliska naszym HOOKS/LANDS/BODY (`shorts.py:30-33`); kadrowanie gorsze niż `face_track.py`; brak u nas jawnego odstępu między shortami i archetypów hooka. Napisy Remotion (licencja firmowa). | **COPY MECHANIC archetypy hooka + `silencedetect` jako sygnał granic + odstęp 2 min (1-2 h, niskie)** |
| francozanardi/pycaps | 230 | 2026-09-30 | MIT | Napisy: Chrome renderuje statyczne sprity PNG per (słowo, stan) z cache, animacje (pop, zoom) liczone w Pythonie i składane w movielite (`css_subtitle_renderer.py:137-203`, `primitive_animation.py:30-60`). | Nasz ASS (`build_edl.py:262-360`) jest równy lub lepszy (pauza pod kartą, pozycje po twarzy). Wzorzec sprite-per-stan jest TAŃSZY niż `render.mjs` (screenshot na klatkę); daje gradient, zaokrąglone pudełko, emoji, czego ASS nie umie. `movielite` licencja niesprawdzona; emoji przez OpenAI. | **COPY MECHANIC wzorca tylko jeśli Kamil chce gradient/emoji w napisach (6-10 h, średnie); biblioteka IGNORE** |
| remotion-dev/template-tiktok | 302 | 2026-11-02 | UNLICENSED (brak) | Napisy TikTok: grupowanie w `@remotion/captions` (okno 1200 ms, `index.tsx:53,99-103`), spring 5 klatek. | Brak licencji (`package.json:13` UNLICENSED), algorytm leży w paczce npm (nie w repo, UNVERIFIED). Nasze grupowanie po znakach (`build_edl.py:342-344`) lepsze dla PL. | **IGNORE; idea okna ms jako drugi próg (0,5 h)** |
| google-ai-edge/mediapipe (autoflip) | 37563 | 2026-11-05 | Apache-2.0 | AutoFlip: per scena tryb „stoi” (ruch <30% zakresu), „śledzenie” lub sweep; solver wielomianowy lub kinematyczny (`scene_camera_motion_analyzer.cc:105-182`, `kinematic_path_solver.cc`). | Dla jednego mówcy `face_track.py` równe (martwa strefa = `min_motion_to_reframe`, limit 6%/s = `max_velocity`). Brakuje nam jawnej heurystyki „scena stoi”. Bazel/C++, nie do uruchomienia u nas. | **IGNORE kod; opcjonalnie COPY MECHANIC „scena stoi” (1-2 h) jeśli widać mikrodrżenie kadru** |

**Przesiane, nieczytane (20):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| FujiwaraChoki/supoclip | 2569 | 2026-11-05 | AGPL-3.0 | AGPL-3.0 |
| RafaelGodoyEbert/ViralCutter | 442 | 2026-09-10 | GPL-3.0 | GPL-3.0 |
| RayVentura/ShortGPT | 8111 | 2025-02-10 | MIT | faceless/LLM+stock, ostatni commit 2025-02 |
| fralapo/clippyme | 62 | 2026-10-13 | MIT | klon OpusClip (62 gwiazdki); nieczytane |
| ColinGPT9/clips-studio | 207 | 2026-11-05 | AGPL-3.0 | AGPL-3.0 |
| Shaarav4795/ClippedAI | 230 | 2026-09-04 | niejasna (NOASSERTION) | licencja niejasna |
| SamurAIGPT/ai-clipping-generator | 110 | 2026-10-22 | MIT | SaaS Next.js; nieczytane |
| toki-plus/ai-highlight-clip | 106 | 2026-08-08 | MIT | LLM-scoring jak autoclip (chiński); nieczytane |
| oktaydbk54/vibeclip | 67 | 2026-06-14 | AGPL-3.0 | AGPL-3.0 |
| dmtrKovalenko/subtitler | 387 | 2026-10-17 | BSD-3-Clause | aplikacja webowa napisów; nieczytane |
| nicolaigaina/ai-video-captions | 70 | 2026-03-27 | MIT | 70 gwiazdek; nieczytane |
| TaoRuijie/TalkNet-ASD | 519 | 2023-10-23 | MIT | wykrywanie aktywnego mówcy (wielu mówców; my mamy jednego); ostatni commit 2023 |
| Junhua-Liao/Light-ASD | 194 | 2025-03-23 | MIT | jak wyżej (ASD); 2025-03 |
| jipraks/yt-short-clipper | 1070 | 2026-09-20 | MIT | aplikacja Windows |
| modelscope/FunClip | 6499 | 2026-11-01 | MIT | FunASR chiński + LLM; nieczytane |
| unconv/captacity | 141 | 2024-06-07 | MIT | proste napisy MoviePy, ostatni commit 2024-06 |
| leamsigc/ShortsGenerator | 360 | 2026-10-11 | MIT | faceless; nieczytane |
| Chamanrajragu/purffle-shorts | 62 | 2026-11-02 | MIT | faceless; 62 gwiazdki |
| mutonby/shortcast | 395 | 2026-06-04 | Apache-2.0 | aplikacja macOS |
| Upload-Post/skill-autoshorts | 158 | 2026-05-02 | brak | brak licencji + Gemini API (płatne) |

**Wystarczalność danych:** zapytań 57, unikalnych trafień 673, przesianych kandydatów 26, wczytanych 6. Wystarczające dla wyboru klipów, kadrowania i napisów. Luka: aplikacje AGPL/GPL odrzucone bez lektury (licencja); modele wykrywania aktywnego mówcy (TalkNet, Light-ASD) nieczytane, bo mamy jednego mówcę.

### 3. Motion graphics, naklejki, rysunki odręczne, Lottie, silniki renderu

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| nexu-io/html-video | 4810 | 2026-06-21 | Apache-2.0 | Meta-warstwa nad Hyperframes i Remotion; render = nagrywanie realtime (`recordVideo`, `render.ts:71-82,311-318`), h264 bez alfy mimo deklaracji `alpha: true` (`capabilities.ts:9-10`). | `gfx/render.mjs:222-246` jest lepszy: deterministyczny seek klatka po klatce, ProRes 4444 alfa. Wymaga płatnych kluczy (MiniMax). | **IGNORE** |
| tungs/timecut | 655 | 2022-09-21 | BSD-3-Clause | Podmiana zegara (Date, rAF, timery), pipe PNG do `ffmpeg -f image2pipe` bez backpressure (`index.js:187-205`), `--threads` (sharding zakresów klatek), puppeteer 2.x. | CSS animations/transitions NIE obsługiwane (README:10) -> dyskwalifikacja. Martwy od 2022. Pomysły dla `render.mjs`: pipe z `drain` (mniej dysku), sharding klatek jednej karty (dziś równoległość tylko między kartami). Zysk czasu niezmierzony. | **IGNORE; COPY idei pipe+sharding (2-4 h każda, niskie; najpierw pomiar, gdzie idzie czas)** |
| Remocn/remocn | 1671 | 2026-10-29 | MIT | 290 komponentów Remotion w pikselach i klatkach @30 fps; paleta: `spring-scale-in`, `caption-word-pop`, `spring-settle`, `mask-reveal-up`, `rolling-number`, `iris-wipe` (parametry w `registry/remocn/*/index.tsx`). | `template.html:11,22,29,40` używa jednej krzywej `cubic-bezier(.2,1.6,.4,1)` do wszystkiego; Remocn daje osobne profile (słowo, scena, liczba, uderzenie). Matematyka przenosi się bez Remotiona (cubic-bezier 1:1, spring -> próbkowany CSS `linear()`). Shader-tła WebGL = wolne na CPU. | **COPY MECHANIC wzorce 1-4 i 8 + generator `linear()` ze sprężyny (3-5 h, niskie)** |
| gkurt/tegaki | 3295 | 2026-11-05 | MIT | Pismo odręczne po pociągnięciach liczonych offline z konturu fontu; `textToSvg()` bez DOM zwraca SVG z `stroke-dashoffset` (`svgExport.ts:365-397`); tryb `controlled` + `window.__seek` (`engine.ts:1006-1009`). | Mamy `maxim_lib.mjs` (litery z kursorem), nie prawdziwe pismo. Seek: `loop`/CSS widoczny w `getAnimations()` (zgodny z `render.mjs:222`), SMIL nie. BLOKADA: 4 gotowe fonty łacińskie mają 90 glifów bez ą ę ł ń ś ź ż (`textToSvg.ts:184` pomija po cichu); jest generator Latin-Ext (`charsets.ts:138-164`). Bun + harfbuzzjs. | **ADOPT warunkowo (8-12 h, ryzyko średnie: ogonki do obejrzenia, Bun)** |
| geeklee/srt-whiteboard-animation | 5396 | 2026-07-27 | MIT | Odsłania gotowy RASTROWY rysunek wzdłuż szkieletu Zhang-Suen (`stream_render.py:754-792,1098-1125`), Python/OpenCV, mp4 bez alfy. | Stan kumulowany -> brak seeku losowego; nasz `scene` robi wektory z alfą (`scene_lib.mjs:238,269`). Grafika `drawing-hand.png` o niejasnym pochodzeniu. | **IGNORE** |
| rough-stuff/rough-notation | 9729 | 2020-10-30 | MIT | Adnotacje SVG (podkreślenie, kółko, ramka, highlight) przez roughjs + CSS `stroke-dashoffset` (`render.ts:68-264`). | Nasze linie proste (`scene_lib.mjs:238,269`); nowe: wobble i 7 typów znaczników. Seed losowy (`rough-notation.ts:13`) -> wołać `renderAnnotation` ze stałym seedem; timer 400 ms na resize zabija animację. Seek działa przez `getAnimations()`. | **COPY MECHANIC (3-4 h; `roughjs` MIT do potwierdzenia); tańsza alternatywa: plugin `annotate` z tegaki** |
| greensock/gsap-skills | 17917 | 2026-04-21 | MIT | Oficjalne skille GSAP: skrót dokumentacji, nic o renderze klatka po klatce. | Mamy GSAP 3.15.0 z pluginami lokalnie (`node_modules/gsap`); „no charge” licencja Standard (zweryfikowane na gsap.com). Marketing w skillach („recommend GSAP by default”). | **IGNORE** |
| aaksa/facecammaxxing | 19 | 2026-10-27 | MIT | Skill efektów na kamerce: `track.py` (246 linii): kolor krawędzi RVM = piksele klatki gdzie alfa >0,985, na miękkich brzegach kolor z macierzy (`:181`); wykrywanie statycznej kamery `phaseCorrelate` (`:197-205`); czysta płyta tła z mediany + `inpaint`. `docs/motion-rules.md`: wejście od skali 1,45 i -6 stopni w ~6 klatek, punch-in 1->1,06-1,08 w 5 klatek, strefy 1080x1920, liczba bohatera >=4% wysokości. | W `behind.py` nie widziałem tej logiki koloru krawędzi (grep `fgr/despill/0.98` pusty); zmniejsza halo. 22 pozostałe efekty = Remotion/Three.js (licencja firmowa Remotion). | **COPY MECHANIC: kolor krawędzi RVM (~2 h) + liczby z motion-rules jako lista kontrolna (~0,5 h)** |
| Dryxio/effects-skill | 7 | 2026-10-26 | MIT | 36 efektów Remotion na kamerce; `cutout.py` = BiRefNet-portrait osobno na każdej klatce, 15 fps (komentarz `setup.sh`: ok. 15 s na klatkę na CPU). | Gorsze niż RVM (brak pamięci czasowej, migotanie, wolne). `trust_remote_code=True` (`cutout.py:43`) = wykonanie kodu z HuggingFace. | **IGNORE** |
| YIAN6557/eian-riso-broll | 358 | 2026-10-19 | własna osobista NC (NC) | Szablony HTML + `audit()` w `assets/riso.js:357`: strefa bezpieczna `ZONE` (`:24`), błąd przy tekście <28 px (`:384`), kontrast <4,5 dla tekstu <100 px (`:389`), dwa teksty nakładające się >3% = błąd, to samo słowo dwa razy w klatce = błąd. | Mamy kolizje części sceny (`scene_check.mjs`) i kontrast tylko grafiki posta (`post_check.py`); brak ogólnego audytu wszystkich kart. Licencja własna osobista NC, zakaz redystrybucji: nie czytać kodu pisząc własny. | **COPY MECHANIC idei: audyt wszystkich kart w `scene_check.mjs` (font >=28, kontrast, strefa UI, duble słów; ~3 h)** |
| artemnovitckii/claude-animation-skills | 395 | 2026-11-01 | MIT | Generatory animacji bez materiału (wykres, mapa trasy, stick-figure, three.js), `kit/anim.py`, SFX z numpy. | Nie dotyczy nagrania z człowiekiem; SFX z numpy mamy (`music/make_beds.py`). Pobiera modele Kokoro/Parakeet, opcjonalnie ElevenLabs. | **IGNORE** |
| diffusionstudio/lottie | 5689 | 2026-07-25 | MIT | Skill (prompt) każący pisać JSON Lottie ręcznie + odtwarzacz na `canvaskit-wasm` (Skottie): `canvas.tsx:97,482-483` (`seekFrame` + `render`). | Generatora nie ma. Render Lottie bez Remotiona jest możliwy (canvaskit w Chrome albo `lottie-web` `goToAndStop`), wpina się w `render.mjs:222-230`, ale NIEPRZETESTOWANE; Skottie vs lottie-web mogą wyglądać różnie. | **IGNORE teraz (opcja: karta `lottie`, 3-4 h, średnie)** |

**Przesiane, nieczytane (28):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| remotion-dev/remotion | 70942 | 2026-11-05 | własna (Remotion License) | licencja własna: bezpłatna dla osób fizycznych i firm do 3 pracowników, powyżej licencja firmowa; mamy HTML+Chrome |
| av/remotion-bits | 509 | 2026-09-15 | brak | brak licencji; komponenty Remotion |
| midrender/revideo | 4179 | 2026-07-15 | MIT | wg mojej wiedzy rozwidlenie Motion Canvas (oceniony wcześniej); inny model scen |
| dmtrKovalenko/fframes | 3179 | 2026-11-02 | MIT | inny model scen niż HTML+Chrome; nieczytane |
| airbnb/lottie-web | 32365 | 2024-11-19 | MIT | tryb maintenance, ostatni commit 2024-11; w pipeline brak źródła plików Lottie |
| LottieFiles/dotlottie-web | 938 | 2026-11-02 | MIT | odtwarzacz Lottie; brak potrzeby bez biblioteki plików .json |
| thorvg/thorvg | 1905 | 2026-11-05 | MIT | silnik C++ Lottie/SVG; nieczytane |
| Samsung/rlottie | 1445 | 2026-09-30 | niejednoznaczna (NOASSERTION) | odtwarzacz C++; nieczytane |
| ed-asriyan/lottie-converter | 1041 | 2026-10-05 | MIT | konwersja Lottie; nieczytane |
| rive-app/rive-wasm | 1020 | 2026-11-05 | MIT | runtime Rive; inny format |
| rough-stuff/rough | 21348 | 2023-11-20 | MIT | biblioteka pod rough-notation (roughjs) — patrz tabela wyżej |
| steveruizok/perfect-freehand | 5799 | 2026-02-01 | MIT | kreski z naciskiem; nieczytane |
| maxwellito/vivus | 15474 | 2022-07-06 | MIT | martwe od 2022; DrawSVG z GSAP robi to samo |
| hi-nikola/hand-drawn-explainer-video-nikola | 458 | 2026-09-02 | Apache-2.0 | skill-prompt (chiński); nieczytane |
| mojs/mojs | 18879 | 2026-04-14 | MIT | toolkit ruchu JS; mamy GSAP+WAAPI |
| iart-ai/motion-skills | 1228 | 2026-10-25 | MIT | skille-prompty; nieczytane |
| LottieFiles/motion-design-skill | 2799 | 2026-05-18 | MIT | zasady ruchu jako prompt; nieczytane |
| cduck/drawsvg | 696 | 2026-10-29 | MIT | generator SVG w Pythonie; nieczytane |
| chr15m/DoodleCSS | 1211 | 2026-04-26 | MIT | motyw CSS; nie dla wideo |
| timqian/chart.xkcd | 7871 | 2026-07-21 | MIT | wykresy w stylu xkcd; nieczytane (wykresów nie robimy) |
| kaomei/stickman-video-director | 4339 | 2026-11-04 | MIT | skill-prompt (wideo z figur); nieczytane |
| Alisa0808/vox-director | 2646 | 2026-10-05 | MIT | skill-prompt; nieczytane |
| useAnimations/react-useanimations | 1261 | 2026-10-30 | MIT | ikony React |
| basmilius/meteocons | 1685 | 2026-04-12 | MIT | ikony pogodowe |
| shadcn-labs/snapcn | 570 | 2026-11-05 | MIT | komponenty Remotion dla dem produktowych |
| ChenShuo2004/cs-board | 799 | 2026-10-01 | MIT | whiteboard + TTS (chiński); nieczytane |
| transitive-bullshit/puppeteer-lottie | 387 | 2021-03-29 | brak | z listy awesome-lottie; martwe od 2021, brak licencji |
| transitive-bullshit/ffmpeg-gl-transition | 721 | 2022-11-16 | brak | z listy awesome-ffmpeg; martwe od 2022, GL w ffmpeg bez GPU |

**Wystarczalność danych:** zapytań 77, unikalnych trafień 969, przesianych kandydatów 40, wczytanych 12. Najszersza kategoria (77 zapytań). Luka: Lottie (lottie-web, thorvg, dotlottie, rlottie) przesiane, nieczytane, bo pipeline nie ma źródła plików Lottie; frameworki Remotion/revideo/fframes odrzucone licencją lub modelem scen, nie lekturą kodu.

### 4. Memy/naklejki: wycinanie tła, matting, katalogi szablonów

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| danielgatis/rembg | 25345 | 2026-11-02 | MIT | ONNX: u2net, isnet-anime, birefnet-*, sam, bria-rmbg (domyślny!); `alpha_matting` + `decontaminate` przez pymatting (`bg.py:46-115`); modele z hashem (pooch). | Nie mamy narzędzia do wycinania obrazów/GIF-ów (naklejki z memów). Domyślny `bria-rmbg` = NC; licencje wag birefnet/isnet niezweryfikowane. Brak telemetrii. | **ADOPT jako narzędzie offline do obrazów: `-m birefnet-general` lub `isnet-anime` + `-dc`, NIE domyślny model (2 h)** |
| ZhengPeng7/BiRefNet | 4368 | 2026-10-25 | MIT | Segmentacja wysokiej rozdzielczości (Swin-L), warianty portrait/DIS/HR; `refine_foreground` (`image_proc.py:8-30`). | Najlepszy do obrazów i rysunków (DIS = cienkie struktury). Wideo: klatka po klatce bez stabilizacji, gorszy niż RVM; CPU: sekundy na klatkę. Licencja wag niezweryfikowana. | **COPY MECHANIC przez rembg (1 h); własny ONNX tylko dla `refine_foreground` (3 h)** |
| nadermx/backgroundremover | 8159 | 2026-07-10 | MIT | U2Net 320 px na klatkę, maska jako wideo mpeg4 (stratne), `alphamerge` do ProRes 4444/WebM VP9 (`utilities.py:27-42,369`). | Gorsze niż RVM (brak wygładzania w czasie). `torch.load` bez `weights_only` (`bg.py:150`), modele z `raw.githubusercontent` bez hasha. | **IGNORE** |
| plemeri/transparent-background | 1301 | 2026-07-08 | MIT | InSPyReNet; wideo bez alfy (`Remover.py:312` blokuje `rgba` dla wideo). | Nic ponad rembg dla obrazów. | **IGNORE** |
| ZHKKKe/MODNet | 4388 | 2022-07-29 | Apache-2.0 | Lekki matting portretowy; trik OFD NIE zaimplementowany (README webcam:14). | RVM ma stan rekurencyjny, MODNet nie wnosi do `behind.py`. `torch.load` z Google Drive. | **IGNORE** |
| pymatting/pymatting | 1923 | 2026-09-08 | MIT | `estimate_foreground_ml` — wielopoziomowa estymacja koloru pierwszego planu (`estimate_foreground_ml.py:62-183`) usuwa jasne/ciemne obwódki przy składaniu na nowe tło. | Brak u nas. Wymaga alfy w skali szarości (GIF 1-bit: najpierw pas trimapy). MIT, org. od 2019, wydanie v1.1.16 z 2026-09. Czas 1000x1000 niezmierzony (README nie podaje). | **ADOPT jako biblioteka (3-4 h, niskie; numba JIT, uruchamiać z `-I`)** |
| jacebrowning/memegen | 1759 | 2026-11-05 | MIT | Katalog 211 szablonów z polami tekstu (`anchor_x/y`, `scale`, `angle`, `style`); autofit `get_font`/`wrap` (`app/utils/images.py:703-826`). | Pola mapują się 1:1 na `[fx,fy,fw,fh]` w `style/memes.json`; mamy 13 z 19 naszych szablonów w katalogu memegen. Obrazy to cudze kadry (źródła: knowyourmeme, YouTube): ryzyko prawne jak w ADR-0008. | **COPY MECHANIC autofit + pozycje pól (2-3 h); obrazy zostają poza repo** |
| CatsJuice/sticker-forge | 754 | 2026-08-01 | MIT | Obrys naklejki: dokładna EDT Felzenszwalba (`lib/source.ts:467-582`, pokrycie `clamp(r+0.5-d,0,1)`), `repairTransparentEdgeColors` (`export-encoders.ts:120-190`), ProRes 4444. | Brak u nas obrysu naklejki; algorytm ~80 linii (w Pythonie `scipy.ndimage.distance_transform_edt`). Aplikacja Next 16 + WebGL do niczego nam niepotrzebna. LGPL tylko dla HEIC. | **COPY MECHANIC `expandAlpha` + `repairTransparentEdgeColors` -> `sticker_cut.py` (4-6 h, niskie)** |
| AdolphGong/aged-despill | 84 | 2026-06-15 | MIT | Despill „zielony = max(R,B)” z bramką na alfie pośredniej (`aged_scalar.cpp:14-46`). | Dotyczy zielonego ekranu, którego nie mamy; README (SIMD, 4K@60) nie zgadza się z kodem; licencja z placeholderem „[Your Name]”. | **IGNORE** |

**Przesiane, nieczytane (19):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| PeterL1n/RobustVideoMatting | 9588 | 2023-03-13 | GPL-3.0 (używamy) | to jest nasz obecny matting (`behind.py`); GPL-3.0 wag/kodu (patrz uwagi przekrojowe) |
| PeterL1n/BackgroundMattingV2 | 7200 | 2023-12-22 | MIT | wymaga zdjęcia tła (plate); ostatni commit 2023-12 |
| pq-yang/MatAnyone | 1642 | 2026-03-04 | S-Lab NC (NC) | licencja S-Lab NC |
| pq-yang/MatAnyone2 | 935 | 2026-07-28 | S-Lab NC (NC) | licencja S-Lab NC |
| FudanCVL/SAM2Matting | 151 | 2026-06-30 | niejednoznaczna (NOASSERTION) | licencja niejasna, 151 gwiazdek |
| facebookresearch/sam2 | 20102 | 2024-12-16 | Apache-2.0 | segmentacja z promptem punktowym; ostatni commit 2024-12; GPU |
| xuebinqin/U-2-Net | 9894 | 2024-01-13 | Apache-2.0 | model jest w rembg; ostatni commit 2024-01 |
| imgly/background-removal-js | 7361 | 2025-07-18 | AGPL-3.0 | AGPL-3.0 |
| withoutbg/withoutbg-python | 1302 | 2026-11-04 | niejednoznaczna (NOASSERTION) | SDK z wariantem chmurowym; licencja niejasna |
| nikopueringer/CorridorKey2.0 | 2048 | 2026-10-15 | niejednoznaczna (NOASSERTION) | zielony/niebieski ekran (nie mamy) |
| feyninc/nobg | 170 | 2026-08-26 | Apache-2.0 | 170 gwiazdek; nieczytane |
| egeorcun/lucida | 176 | 2026-07-24 | MIT | 176 gwiazdek; nieczytane |
| MemeCrafters/meme-generator | 1044 | 2025-12-30 | MIT | chińskie szablony, ostatni commit 2025-12; nieczytane |
| voxmedia/meme | 1993 | 2014-09-09 | BSD-3-Clause | martwe od 2014 |
| Bria-AI/RMBG-2.0 | 347 | 2025-12-11 | wagi NC (NC) | wagi NC |
| 1038lab/ComfyUI-RMBG | 2218 | 2026-10-20 | GPL-3.0 | GPL-3.0, ComfyUI |
| ibaiGorordo/ONNX-SAM2-Segment-Anything | 288 | 2024-08-29 | MIT | SAM2 ONNX, 2024-08 |
| Gy920/segment-anything-2-real-time | 603 | 2025-06-03 | Apache-2.0 | SAM2 strumień; GPU |
| ihmily/image-matting | 397 | 2026-01-26 | MIT | API online; nieczytane |

**Wystarczalność danych:** zapytań 61, unikalnych trafień 757, przesianych kandydatów 28, wczytanych 9. Wystarczające: wczytane wszystkie główne silniki wycinania obrazów oraz generatory memów. Luki: licencje wag (birefnet, isnet, u2net, InSPyReNet) niezweryfikowane; żadne repo nie rozwiązuje migotania alfy w GIF-ach; czasy CPU nie zmierzone.

### 5. Miniatury YouTube i testy A/B

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| bdebon/youtube-thumbnail-tester-chrome-extension | 132 | 2025-09-17 | MIT | Podmienia `src` w prawdziwym DOM zalogowanego youtube.com (`content.js:64-112`). | Nie wnosi wymiarów kafelka (grep po CSS/README: zero). Wymiary trzeba zmierzyć samemu: Playwright + `getBoundingClientRect` na `ytd-rich-item-renderer img` (mobile 390x844 i desktop). | **IGNORE kod; COPY idei `feedPreview()` w `thumbs.mjs` (3-4 h, niskie)** |
| christophschuhmann/improved-aesthetic-predictor | 1347 | 2023-10-12 | Apache-2.0 | CLIP ViT-L/14 + MLP 768->...->1 (`simple_inference.py:46-117`); wagi 3x~3,7 MB w repo, Apache-2.0. | Daje ocenę klatek, której `thumbs.mjs` nie ma; ogólna estetyka (zdjęcia, sztuka), nie CTR ani mimika. CPU: ok. 0,46 s/obraz (benchmark IQA-PyTorch). Skrypt wymaga CUDA i zbędnych importów; `torch.load` bez `weights_only`, ale opkody `.pth` czyste (pickletools). | **COPY MECHANIC ~40 linii (3-5 h, niskie): wagi + `open_clip` lokalnie + `weights_only=True`** |
| chaofengc/IQA-PyTorch (pyiqa) | 3442 | 2026-11-04 | PolyForm NC + S-Lab NC (NC) | Rejestr metryk NR-IQA (niqe, brisque, musiq, clipiqa, topiq_nr, laion_aes, `topiq_nr-face`). | PolyForm NC + S-Lab NC; `torch.load(weights_only=False)` na wagach z HF bez hasha. Dla samej ostrości twarzy wystarczy `cv2.Laplacian(...).var()` na wycinku z `face_track.py`. | **IGNORE (NC)** |
| eat-pray-ai/yutu | 713 | 2026-10-31 | Apache-2.0 | CLI/MCP Go na YouTube Data API: `thumbnails.set`, `videos.insert`; kwoty wg repo: 50 jednostek na miniaturę. | Nasze `youtube/yt_upload.py:42-48` dojrzalsze (kontrola kanału, domyślnie private, resumable). Brak u nas tylko `num_retries` przy `next_chunk()`. Test & Compare: brak API, brak obejścia. `install.sh` pobiera binarkę bez sumy. | **IGNORE; dopisać `num_retries=5` (1 h)** |
| Jakeschincariol/youtube-agent-skill | 4636 | 2026-09-16 | MIT | Reguły pakietu: miniatura max 3 słowa, miniatura nie powtarza tytułu (przecięcie słów bez stop-słów, `title.py:47-51`), tytuł 60 znaków desktop / 40 mobile. | Nasze `big <= 18 znaków` (`thumbs.mjs:26`) mierzalne, ale brak testu „miniatura != tytuł” i limitu słów. „Squint test” = tylko proza, nie kod. | **COPY MECHANIC (1 h, niskie): test rozłączności słów w `checkThumbs` + ostrzeżenie dla tytułu >40 znaków** |

**Przesiane, nieczytane (16):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| emnerson/youtube-thumbnail-averager | 121 | 2025-10-05 | MIT | skrypt uśredniania miniatur kanału; inspiracja, nie narzędzie |
| ajayyy/DeArrow | 2344 | 2026-10-17 | GPL-3.0 | GPL-3.0, crowdsourcing |
| dragonwolfshovel/youtube-uploader | 426 | 2026-11-05 | MIT | mamy własny `youtube/yt_upload.py` |
| yoanbernabeu/NanoThumbnail | 54 | 2026-09-27 | MIT | generuje miniatury modelem AI; nieczytane |
| AgriciDaniel/claude-youtube | 674 | 2026-04-10 | MIT | skill-prompty YouTube (SEO); nieczytane |
| AgriciDaniel/youtubepro | 431 | 2026-08-27 | Apache-2.0 | badania i skrypty z AI; nieczytane |
| darkzOGx/youtube-automation-agent | 5010 | 2026-10-27 | MIT | pełna automatyzacja kanału z LLM API; nieczytane |
| LAION-AI/aesthetic-predictor | 745 | 2022-08-15 | MIT | starszy poprzednik improved-aesthetic-predictor (2022) |
| shunk031/simple-aesthetics-predictor | 47 | 2024-06-14 | MIT | wrapper HF na ten sam model |
| flavioribeiro/video-thumbnail-generator | 329 | 2024-03-19 | Apache-2.0 | sprite'y do paska postępu; ostatni commit 2024-03 |
| elliotwaite/thumbnail-rating-bar-for-youtube | 273 | 2026-08-11 | MIT | rozszerzenie z paskiem oceny; nie dla A/B własnych |
| eddieoz/youtube-clips-automator | 166 | 2023-02-02 | MIT | ostatni commit 2023-02 |
| fraigo/online-video-thumbnail-generator | 82 | 2025-01-30 | MIT | narzędzie online; 82 gwiazdki |
| woshidandan/TANet-image-aesthetics-and-quality-assessment | 375 | 2025-09-25 | Apache-2.0 | model badawczy; wagi niezweryfikowane |
| stevezau/media_preview_generator | 310 | 2026-11-03 | MIT | pod Plex/Jellyfin |
| pietervanheijningen/clickbait-remover-for-youtube | 405 | 2025-03-21 | MIT | rozszerzenie przeglądarki; ostatni commit 2025-03 |

**Wystarczalność danych:** zapytań 54, unikalnych trafień 426, przesianych kandydatów 21, wczytanych 5. Najsłabsza baza: brak utrzymywanego OSS do testów A/B miniatur (Test & Compare działa tylko w YouTube Studio, bez API); rozmiary kafelka YouTube nie występują w żadnym przeczytanym repo i trzeba je zmierzyć samemu.

### 6. Obrazy/karuzele/PDF na LinkedIn i social

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| marp-team/marpit | 1392 | 2026-09-30 | MIT | Skaluje cały slajd przez SVG `viewBox` + `foreignObject` (`inline_svg.js:47-54`). | Auto-fit tekstu jest w marp-core (nieklonowany). Nasz problem to wysokość (`carousel.mjs:31`), nie skalowanie slajdu. | **IGNORE** |
| vercel/satori | 14165 | 2026-10-20 | MPL-2.0 | HTML/CSS -> SVG (Taffy WASM + HarfBuzz); fonty zmienne tylko domyślna instancja, brak PDF, brak wierności 1:1 z przeglądarką (README). | Chrome daje pełny CSS i `page.pdf`; satori traci wagi VF (Montserrat 800). MPL-2.0 plikowy copyleft. | **IGNORE** |
| kane50613/takumi | 3175 | 2026-11-04 | MIT lub Apache-2.0 | Silnik Rust, port układu tekstu Chromium, PNG/SVG/PDF; `text-fit: shrink` dopasowuje DO SZEROKOŚCI linii (`text_fit_utils.rs:385-440`); benchmark 26 ms vs 198 ms Puppeteer (M1 Pro, faktura). | Nie rozwiązuje naszego błędu „za wysoki tekst” (wysokość pola). Węższe CSS niż Chromium, PDF bez `filter`. Brak dowodu, że Chrome jest u nas wąskim gardłem. | **COPY MECHANIC idei: pętla shrink w Chrome na `.box` (2-3 h); przejście na takumi IGNORE** |
| op7418/guizang-social-card-skill | 7983 | 2026-10-30 | AGPL-3.0 (package.json: ISC) | Eksport `el.screenshot()` per plansza (`render.mjs:49-78`) i walidatory: R1 scrollHeight, R4 minimalny font, R6 limit linii tytułu, R8 zasięg treści/puste miejsce, R9 odstęp (`validate-social-deck.mjs:9-232`). | Nasze `carousel.mjs:31` robi tylko R1 (+ szerokość). Zasada „skróć tekst, nie zmniejszaj czcionki”. AGPL-3.0 (+ oferta licencji komercyjnej, `package.json`: ISC) -> bez kopiowania kodu. | **IGNORE kod; COPY idei walidatorów R4/R6/R8 (w tej samej zmianie co pętla shrink)** |

**Przesiane, nieczytane (25):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| marp-team/marp-cli | 3907 | 2026-09-08 | MIT | pochodna Marpit; slajdy z Markdown |
| slidevjs/slidev | 49377 | 2026-11-05 | MIT | slajdy Vue; mamy własne karty |
| linebender/resvg | 4174 | 2026-11-05 | Apache-2.0 | renderer SVG, nie HTML |
| Kozea/WeasyPrint | 9760 | 2026-11-05 | BSD-3-Clause | HTML->PDF bez Chrome, CSS ograniczone; alternatywa dla `page.pdf`, nieczytane (brak problemu do rozwiązania) |
| typst/typst | 57000 | 2026-10-28 | Apache-2.0 | inny język składu |
| gotenberg/gotenberg | 13522 | 2026-11-05 | MIT | kontener Chrome->PDF; mamy Chrome lokalnie |
| astefanutti/decktape | 2437 | 2026-10-21 | MIT | eksport slajdów HTML do PDF; mamy `page.pdf` |
| pdfme/pdfme | 5016 | 2026-11-01 | MIT | generator PDF z szablonów; nieczytane |
| bubkoo/html-to-image | 7272 | 2026-11-02 | MIT | screenshot DOM w przeglądarce; mamy headless Chrome |
| qq15725/modern-screenshot | 2090 | 2026-04-16 | MIT | jak wyżej |
| zumerlab/snapdom | 8227 | 2026-11-04 | MIT | jak wyżej |
| frinyvonnick/node-html-to-image | 886 | 2026-07-13 | Apache-2.0 | opakowanie Puppeteera |
| microlinkhq/browserless | 1845 | 2026-11-03 | MIT | sterownik Chrome nad Puppeteerem |
| gitroomhq/postiz-app | 40955 | 2026-11-05 | AGPL-3.0 | AGPL-3.0, planer publikacji |
| SamurAIGPT/postiz-cheap | 1394 | 2026-10-26 | MIT | planer publikacji (poza zakresem generowania) |
| simonhaenisch/md-to-pdf | 1984 | 2025-12-03 | MIT | Markdown->PDF; nieczytane |
| pikepdf/pikepdf | 2819 | 2026-11-01 | MPL-2.0 | MPL-2.0, edycja PDF; nieczytane |
| Hopding/pdf-lib | 8668 | 2021-11-12 | MIT | ostatni commit 2021-11 |
| typpo/quickchart | 2058 | 2024-06-18 | AGPL-3.0 | AGPL-3.0 |
| lowlighter/metrics | 17366 | 2023-12-18 | MIT | ostatni commit 2023-12 |
| alonw0/web-asset-generator | 531 | 2026-01-28 | MIT | favicony/ikony; nieczytane |
| sergebulaev/instagram-skills | 753 | 2026-10-27 | MIT | skille-prompty; nieczytane |
| odoo/paper-muncher | 313 | 2026-11-05 | LGPL-3.0 | LGPL-3.0; silnik HTML->PDF |
| vivliostyle/vivliostyle-cli | 238 | 2026-10-19 | AGPL-3.0 | AGPL-3.0 |
| pagedjs/pagedjs | 1561 | 2026-10-20 | MIT | paginacja CSS dla druku; nieczytane |

**Wystarczalność danych:** zapytań 67, unikalnych trafień 1019, przesianych kandydatów 27, wczytanych 4. Mała próba czytana (4), bo pole dobrze pokrywa Chrome `page.pdf` / `el.screenshot`. Luki: marp-core (właściwy auto-fit) nie sklonowany; polskie diakrytyki w satori i takumi bez testu w obu repo.

### 7. Jakość audio/wideo (odszumianie, głośność, VAD, interpolacja)

**Przeczytane (kod, nie tylko README):**

| repo | gwiazdki | ostatni commit | licencja | co robi (plik:linia) | vs nasze | werdykt |
|---|---|---|---|---|---|---|
| slhck/ffmpeg-normalize | 1540 | 2026-10-14 | MIT | Dwuprzebiegowy `loudnorm`: przebieg 1 `print_format=json` po pre-filtrze, przebieg 2 z `measured_*` + `linear=true` (`_streams.py:519-575,826-844`); fallback do dynamicznego, gdy LRA celu < zmierzone. | KLUCZOWE: u nas `loudnorm` stoi tylko na głosie (`assemble.py:335`), muzyka i sfx dochodzą po nim (`amix` + `alimiter=0.89`, `:346`) -> końcowy miks nigdy nie jest mierzony przed renderem; `critic.py:141-143` ostrzega po fakcie. Nasz loudnorm jednoprzebiegowy = tryb dynamiczny. | **COPY MECHANIC przepis (nie pakiet): pomiar audio-only pełnego miksu + render z `measured_*` (3-4 h, niskie)** |
| Rikorose/DeepFilterNet | 4955 | 2024-10-17 | MIT lub Apache-2.0 (wagi: brak licencji) | Odszumianie głębokie; wtyczka LADSPA `deep_filter_mono` (48 kHz), CLI `deep-filter` (WAV 48 kHz); ostatni commit 2024-10-17. | README bez RTF i bez liczb; wagi bez osobnej licencji; w ffmpeg `ladspa` jest, ale `edl_guard.py:11-12` go nie dopuszcza. Najpierw `arnndn` (już w ffmpeg). | **COPY MECHANIC / opcjonalne po A/B z arnndn (3-5 h, średnie)** |
| GregorR/rnnoise-models | 388 | 2018-09-02 | brak pliku (autor: bez praw) | Wagi `.rnnn` (~300 KB) do filtra `arnndn`: `sh` (sama mowa), `bd`, `lq`, `cb`, `mp`. | `arnndn` jest w naszym ffmpeg 8.0.1, filtr nie na liście `edl_guard.py:11-12`. Różnicę względem `afftdn=nf=-30` da tylko odsłuch A/B. Brak licencji, autor: „none of this is copyrightable”. | **COPY MECHANIC: test A/B `sh.rnnn` (1-2 h, niskie)** |
| Digitalone1/EasyEffects-Presets | 539 | 2026-03-26 | MIT | Preset „Loudness Equalizer” do słuchania filmów (gate, upward compressor, multiband, limiter). | Nie jest presetem mowy; release 600 ms, inna rola niż nasz `acompressor`. Nic o kompresji mowy. | **IGNORE** |
| snakers4/silero-vad | 10604 | 2026-10-22 | MIT | VAD ONNX 2,3 MB, MIT, okno 32 ms, `get_speech_timestamps` (`utils_vad.py:281-366`), README: <1 ms na 30 ms audio. | Odróżnia mowę od oddechu/kliknięcia/szumu (RMS tego nie umie), ale granice co 32 ms + `speech_pad_ms`; nasz RMS 10 ms ostrzejszy. Dodatek do `edges.py`, nie zamiennik. 48 kHz decymowane bez filtra -> `aresample` ffmpegiem do 16 kHz przed wejściem. | **ADOPT jako uzupełnienie `edges.py` (3-4 h, niskie; wariant ONNX bez torcha)** |
| hzwer/Practical-RIFE | 1036 | 2026-08-27 | MIT | Interpolacja klatek; repo bez sieci i wag (Google Drive), `numpy<=1.23.5`, `os.system` z nazwami plików w stringu (`inference_video.py:31-41`). | `dejudder.py` zamienia tylko powtórzone klatki (flow OpenCV 640 px); RIFE na CPU to przesada i ryzyko artefaktów twarzy. | **IGNORE** |
| Xiaobin-Rong/gtcrn | 766 | 2026-08-03 | MIT | Mikro-model odszumiania 48 K parametrów; `assert fs == 16000` (`infer.py:19`). | Tylko 16 kHz -> traci pasmo >8 kHz, brzmi gorzej niż `afftdn` przy pełnym paśmie. | **IGNORE** |

**Przesiane, nieczytane (21):**

| repo | gwiazdki | ostatni commit | licencja | powód pominięcia |
|---|---|---|---|---|
| csteinmetz1/pyloudnorm | 790 | 2026-01-04 | MIT | pomiar BS.1770 w Pythonie; pomiar mamy w ffmpeg `ebur128`/`loudnorm` |
| jiixyj/libebur128 | 494 | 2021-02-14 | MIT | biblioteka C, ostatni commit 2021 |
| xiph/rnnoise | 5939 | 2025-02-22 | BSD-3-Clause | kod stoi za `arnndn` w ffmpeg; ostatni commit 2025-02 |
| ceva-ip/DPDFNet | 181 | 2026-09-09 | Apache-2.0 | model 2026-09 (Apache-2.0), nieczytane — kandydat do A/B po arnndn |
| k2-fsa/sherpa-onnx | 15757 | 2026-11-05 | Apache-2.0 | duży toolkit ONNX (STT/VAD/enhancement); nieczytane |
| modelscope/ClearerVoice-Studio | 4607 | 2025-08-14 | Apache-2.0 | modele na ModelScope, GPU; nieczytane |
| resemble-ai/resemble-enhance | 2486 | 2024-12-03 | MIT | regeneracja głosu zmienia barwę; ostatni commit 2024-12 |
| haoheliu/voicefixer | 1397 | 2025-02-17 | MIT | restauracja mowy 44,1 kHz; nieczytane |
| TEN-framework/ten-vad | 2302 | 2026-11-04 | niejednoznaczna (NOASSERTION) | licencja niejasna (NOASSERTION); silero-vad wystarcza |
| wiseman/py-webrtcvad | 2504 | 2021-02-15 | niejednoznaczna (NOASSERTION) | nieutrzymywane od 2021 |
| hzwer/ECCV2022-RIFE | 5664 | 2025-09-10 | MIT | oryginał Practical-RIFE |
| nihui/rife-ncnn-vulkan | 1128 | 2022-10-23 | MIT | Vulkan/GPU, ostatni commit 2022-10 |
| k4yt3x/video2x | 22614 | 2026-03-07 | AGPL-3.0 | AGPL-3.0, upscaling |
| xinntao/Real-ESRGAN | 37372 | 2024-04-02 | BSD-3-Clause | upscaling; nie potrzebujemy; ostatni commit 2024-04 |
| Netflix/vmaf | 5579 | 2026-11-02 | niejednoznaczna (NOASSERTION) | metryka jakości wideo; przydatna do regresji kodeka, nie do treści; nieczytane |
| slhck/ffmpeg-quality-metrics | 561 | 2026-10-25 | MIT | opakowanie VMAF/SSIM; jak wyżej |
| georgmartius/vid.stab | 988 | 2026-08-14 | niejednoznaczna (NOASSERTION) | jest już w ffmpeg (vidstab); stabilizacji nie potrzebujemy |
| m-tassano/fastdvdnet | 689 | 2024-02-01 | MIT | odszumianie wideo na GPU, 2024-02 |
| lucianodato/noise-repellent | 573 | 2026-11-02 | niejednoznaczna (NOASSERTION) | wtyczka LV2; licencja niejasna |
| werman/noise-suppression-for-voice | 6966 | 2024-05-18 | GPL-3.0 | GPL-3.0 |
| sayampy/deepdenoiser | 269 | 2026-09-07 | GPL-3.0 | GPL-3.0 (aplikacja nad DeepFilterNet3) |

**Wystarczalność danych:** zapytań 65, unikalnych trafień 865, przesianych kandydatów 28, wczytanych 7. Wystarczające dla głośności, VAD i odszumiania. Luki: brak odsłuchu A/B (arnndn, DeepFilterNet) na naszym nagraniu; czasy CPU z README (wiele repo ich nie podaje).

## 5. Top 10 do wdrożenia

Kolejność = wartość / koszt. Pozycje 1-3 to naprawa pomiarów we własnym kodzie (bez cudzego kodu). Godziny = kod + test, moje szacunki. Ryzyko = ryzyko regresji lub licencyjne.

| # | co | źródło (werdykt) | gdzie u nas | koszt | ryzyko | dowód i uwaga |
|---|---|---|---|---|---|---|
| 1 | **Pomiar głośności pełnego miksu**: loudnorm dwuprzebiegowy (pomiar audio-only miksu głos+muzyka+sfx, render z `measured_*` + `linear=true`, fallback dynamiczny gdy LRA celu < zmierzone) | ffmpeg-normalize `_streams.py:519-575,826-844` (COPY MECHANIC) | `assemble.py:335-346`, `critic.py:141-143` | 3-4 h | niskie | Luka potwierdzona w kodzie: loudnorm tylko na głosie, miks po nim niezmierzony. Przepis, nie pakiet. |
| 2 | **Kontrola gotowego MP4 w `film_check.py`**: czerń >=0,1 s, `freezedetect` -60 dB/1,5 s, klik na szwie (skok `astats` >0,35 w oknie +-40 ms), obcięte słowo >0,06 s, true peak <=-1 dBTP | video-editor-agent `layer1-technical.ts:37-53`, `layer2-transcript.ts:34-37` (COPY MECHANIC idei; repo bez licencji -> własny kod) | `film_check.py`, `critic.py` | ~3 h | niskie | Dziś krytyk działa na planie/EDL; `grep` w `*.py` nie znajduje `freezedetect`/`blackdetect`. Łączyć z poz. 1 (jeden przebieg ffmpeg). |
| 3 | **Pomiar i naprawa wyrównania słów**: (a) `-ojf` i porównanie `t_dtw` z `offsets` na 1 chunku; jeśli DTW martwe -> usunąć `--dtw` (CPU) albo użyć `t_dtw`; (b) `-mc 0` w `whisper-cli` | ffmpeg-skill `asr.py:39` (COPY MECHANIC) + własny kod | `chunked_whisper.py:31-32`, `verify_cut.py:18` | 1-2 h (z pomiarem na PL) | niskie | `--dtw` martwe = wniosek z kodu whisper.cpp, niezmierzony; `-mc 0` bez pomiaru na PL to hipoteza. |
| 4 | **Detektor powtórek (retake) i rozciągniętych słów**: 4-gramy z podobieństwem >0,7 w oknie 60 s, zostaw ostatnie podejście; alarm na słowo >=1 s; próg ciszy względem szumu nagrania | cut-video `SKILL.md:136-141` i sekcje retake (COPY MECHANIC, MIT) | `build_edl.py` (po stworzeniu słów), `critic.py` | ~5 h | niskie-średnie (fałszywe trafienia) | W kodzie brak detekcji powtórek (grep zero). Najpierw sprawdzić, czy etap redakcji ręcznie łapie je już dziś; bez problemu na filmie 2 = nie wdrażać. |
| 5 | **Krawędzie cięć**: `snap_tail` (ogon słowa do rozpadu RMS zamiast stałego POST 0,16 s), `entry_check` (ścięty początek słowa) w `critic.py`, guard `in_word` | claude-youtube-editor `cutlib.py:77-90`, `analyze_cut.py:39-51`; ghost-editor `plan_cut.py:43-47` (COPY MECHANIC) | `build_edl.py:23`, `edges.py`, `critic.py` | 3-4 h | niskie-średnie | Najpierw zmierzyć, ile cięć na filmie 2 ma gorące wejście. |
| 6 | **Audyt wszystkich kart** w `scene_check.mjs`: pokrycie twarzy przez kartę (>0,08), zasłonięcie karty przez człowieka (`elementFromPoint`, 5 punktów), font >=28 px, kontrast >=4,5, strefa UI, to samo słowo dwa razy | SeeCut `geom-check.mjs:12-14` (PolyForm NC: tylko idea), eian-riso-broll `riso.js:357-389` (NC: tylko idea) | `gfx/scene_check.mjs`, `head_check.py` | ~6-7 h | niskie (nie czytać kodu NC przy pisaniu) | Dziś: kolizje części sceny i kontrast grafiki posta; brak pokrycia twarzy/zasłonięcia. |
| 7 | **Karuzela LinkedIn: auto-dopasowanie wysokości + walidatory** (pętla shrink `font-size` w Chrome do minimum, potem błąd; kontrole minimalnego fontu, limitu linii tytułu, pustego miejsca) | takumi `text-fit` (idea), guizang `validate-social-deck.mjs:9-232` (idea; AGPL: bez kodu) | `~/Dane/vp-linkedin/gfx/carousel.mjs:31` | 2-3 h | niskie | Dziś błąd „text does not fit (shorten it)” zatrzymuje render zamiast dopasować. |
| 8 | **Miniatury: trzy tanie bramki** (a) test „miniatura != tytuł” + max 3 słowa + ostrzeżenie dla tytułu >40 zn.; (b) `feedPreview()` na zmierzonych wymiarach kafelka (Playwright na youtube.com, mobile 390x844 i desktop); (c) ranking klatek improved-aesthetic-predictor + ostrość twarzy `cv2.Laplacian` | youtube-agent-skill `title.py:47-51`; improved-aesthetic-predictor `simple_inference.py:46-117` (COPY MECHANIC) | `gfx/thumbs.mjs:26`, `checkThumbs` | (a) 1 h, (b) 3-4 h, (c) 3-5 h | niskie | (c) to ogólna estetyka, nie CTR: tylko odsiew brzydkich klatek. Rozmiarów kafelka brak w repo: zmierzyć. |
| 9 | **Wycinanie obrazów na naklejki z memów/GIF-ów**: `rembg -m birefnet-general` (lub `isnet-anime`) + `-dc`; pymatting `estimate_foreground_ml`; obrys EDT + `repairTransparentEdgeColors` z sticker-forge -> `sticker_cut.py` (RGBA / ProRes 4444) | rembg (ADOPT), pymatting (ADOPT), sticker-forge `source.ts:467-582`, `export-encoders.ts:120-190` (COPY MECHANIC) | nowy moduł; karta `sticker` w `render.mjs` już jest | ~10 h (2 + 3-4 + 4-6) | średnie: licencje wag birefnet/isnet niezweryfikowane, domyślny model rembg NC | GIF: alfa 1-bit -> eksport WebM VP9 `yuva420p`/APNG; migotanie klatka po klatce tłumić (mediana alfy po 3 klatkach). |
| 10 | **Paleta ruchu z Remocn**: osobne profile dla słowa (scale-in ~370 ms), sceny (punch-in, ζ~0,84), cytatu (rise+blur), liczby (rolling-number) + generator `linear()` ze sprężyny | Remocn `spring-scale-in`, `caption-word-pop`, `spring-settle`, `mask-reveal-up`, `rolling-number` (COPY MECHANIC) | `gfx/template.html:11,22,29,40`, `scene_lib.mjs` | 3-5 h | niskie (ocena wzrokowa na 1 shorcie) | Dziś jedna krzywa `.2,1.6,.4,1` do wszystkiego. Parametry: px x2 (2560x1440), klatki/30 x 1000 = ms. |

### Tanie dodatki (1-3 h każdy, poza top 10)

| pomysł | źródło | koszt | uwaga |
|---|---|---|---|
| A/B odszumiania: `arnndn` z `sh.rnnn` (i `bd.rnnn`) kontra `afftdn=nf=-30`, odsłuch na tym samym nagraniu | rnnoise-models (COPY MECHANIC) | 1-2 h | `arnndn` dopisać do `edl_guard.py:11-12`; filtr tylko 48 kHz, wagi bez licencji. DPDFNet/DeepFilterNet tylko jeśli arnndn nie wystarczy. |
| Kolor krawędzi RVM (piksele klatki tam, gdzie alfa >0,985) i wykrywanie statycznej kamery | facecammaxxing `track.py:181,197-205` (COPY MECHANIC, MIT) | ~2 h | Zmniejsza halo w `behind.py`; porównać wzrokowo na jednej scenie. |
| Mechaniki shortów: archetypy hooka, „hook nie powtarza pierwszych słów”, `silencedetect` -35 dB jako sygnał granic, odstęp >=2 min, zakres długości od długości źródła | claude-shorts `snap_boundaries.py:50,102,136`; autoclip `quality.py:98-120` | 1-2 h | `shorts.py` jest już bliski; zysk = doprecyzowanie. |
| Autofit tekstu memów (`get_font`/`wrap`) + pola `anchor/scale/angle` do `style/memes.json` | memegen `images.py:703-826` | 2-3 h | Obrazy POZA repo (ADR-0008). 13 z 19 naszych szablonów jest w memegen. |
| Strefa UI na kontaktówce `viewer_pack`; procedura par A/B z zamianą kolejności dla agenta-oglądacza | claude-editing-skills `reel.py:28`; SeeCut spec | ~1-2 h | Idee, nie kod. |

### Warunkowe i odłożone (nie w top 10)

| pomysł | źródło | koszt | dlaczego odłożone |
|---|---|---|---|
| Karta „napis pisany odręcznie” | tegaki (ADOPT warunkowo) | 8-12 h | polskie ogonki: gotowe fonty mają 90 glifów bez ą ę ł ń ś ź ż; trzeba bundla Latin-Ext + Bun + obejrzeć wynik. Awaryjnie zostaje karta `maxim`. |
| Wyrównanie CTC (whisperX, 20 ms) zamiast heurystyki `-ml 1` | whisperX `alignment.py:326-337` | 4-6 h | zależy od pozycji 3: najpierw zmierzyć błąd granic na PL; ciężki łańcuch torch. |
| Rozdziały longa z embeddingów (TextTiler) | clipsai `texttiler.py:183-347` | 6-8 h | trzeba wielojęzycznego embeddera i testu; zysk: automatyczne chaptery/YouTube. |
| Adnotacje odręczne (kółko, podkreślenie) ze stałym seedem | rough-notation `render.ts:68-264` | 3-4 h | czysto kosmetyczne; tańsze: plugin `annotate` z tegaki. |
| Silero-VAD jako drugi sygnał w `edges.py` | silero-vad `utils_vad.py:281-366` | 3-4 h | ADOPT, ale zysk niezmierzony: najpierw pozycja 5. |
| Szybszy render kart: pipe PNG do ffmpeg z `drain`, sharding klatek jednej karty | timecut `index.js:187-205` | 2-4 h każdy | nie wiemy, gdzie idzie czas; wąskim gardłem może być kodowanie PNG w Chrome, nie dysk. Pomiar przed zmianą. |
| Sprity napisów (słowo x stan) z Chrome zamiast ASS | pycaps `css_subtitle_renderer.py:137-203` | 6-10 h | ASS jest równy; sens tylko dla gradientu/emoji w napisach. |
| „Scena stoi” w `face_track.py` | autoflip `scene_camera_motion_analyzer.cc:105-182` | 1-2 h | tylko jeśli widać mikrodrżenie kadru. |
| Mel-blank (energia mel -> pauzy) | CrisperWhisper `word_timing.py:271-330` | 3-4 h | tylko jeśli pozycja 3 wykaże złe granice. |

### Bezpieczeństwo pozycji ADOPT (sprawdzone przed wdrożeniem)

| repo | wydawca / historia | wydania i aktywność | zależności i sieć | uwaga |
|---|---|---|---|---|
| danielgatis/rembg | konto osobiste od 2008, 393 commity głównego autora, 25 tys. gwiazdek | v2.0.86 z 2026-10-21, 23 zamknięte issues w 90 dniach | modele ONNX z GitHub Releases `danielgatis/rembg v0.0.0` przez `pooch` z hashem md5/sha256; sesje chmurowe (`withoutbg`, `atlascloud`) są płatne i NIE używać; domyślny `bria-rmbg` = NC | instalować w venv; `-m` jawnie; weryfikować hash modeli; Python >=3.11 |
| pymatting/pymatting | organizacja od 2019, 2 główni autorzy | v1.1.16 z 2026-09-08 | numpy, pillow, numba>=0.60, scipy; brak sieci, shell, eval | numba JIT zapisuje cache obok kodu: kopiować do katalogu tymczasowego, uruchamiać `python -I` |
| snakers4/silero-vad | konto od 2015, 287+178 commitów dwóch autorów | v6.2.3 z 2026-09-23, 19 zamkniętych issues w 90 dniach | wariant `onnx-cpu` z onnxruntime, wagi 2,3 MB w repo, brak telemetrii; unikać `torch.hub.load(trust_repo=True)` | użyć pliku ONNX, nie `.jit` (pickle) |
| gkurt/tegaki (warunkowo) | konto od 2013, repo od 2026-03, 443 commity autora + 35 od `claude` | tegaki@1.1.0 z 2026-10-11 | runtime Bun, generator: harfbuzzjs, opentype.js, d3-delaunay; renderer bez zależności; sieć tylko `fetch` fontu (`lib/font.ts:94`) | młode repo, `internal` poza semver (`AGENTS.md:45`); `.claude/settings.json` z hookiem `bun format` w repo — nie przenosić |

Nie sprawdzałem sum kontrolnych paczek na PyPI/npm ani podpisów wydań; to krok przed instalacją (`pip download --no-deps` + porównanie SHA256 w venv).

## 6. Decyzje dla Kamila

1. **NC a kanał:** czy monetyzowany kanał YouTube/LinkedIn to „użytek komercyjny”? Od tego zależy, czy wolno używać wag CrisperWhisper, RMBG-2.0, MatAnyone, pyiqa oraz kodu SeeCut (PolyForm NC), JJKoubo (CC BY-NC), eian-riso-broll (własna NC) i rescript (PolyForm NC). Rekomendacja: traktować NC jako zakazane (nie ma ich w top 10).
2. **RVM GPL-3.0:** zostajemy przy RVM (nic lepszego do wideo nie znalazłem), z notatką licencyjną w README. Alternatywa bez GPL: brak gotowej (BackgroundMattingV2 wymaga zdjęcia tła, MODNet gorszy).
3. **Naklejki (poz. 9):** czy budujemy osobne narzędzie `sticker_cut.py` (~10 h), czy na razie ręczne wycinki w `memes.json`? Dla GIF-ów z alfą: WebM VP9/APNG zamiast GIF.
4. **Karta odręczna (tegaki):** czy warto 8-12 h (Bun + font z polskimi znakami + test), czy zostajemy przy karcie `maxim`?
5. **Napisy shortów:** zostajemy przy ASS (rekomendacja), czy chcemy gradient/emoji (wtedy sprity w stylu pycaps, 6-10 h)?
6. **Pomiary przed zmianami:** zgoda na 2-godzinną rundę pomiarową na filmie 2 (DTW vs offsets, `-mc 0`, liczba gorących wejść, czas klatki w `render.mjs`), zanim wejdą pozycje 4-5 i „odłożone”. Rekomendacja: tak.
7. **Sprzątanie:** `render/ref/oss/` zajmuje ok. 3,3 GB (klony płytkie, gitignorowane). Skasować po zatwierdzeniu dokumentu? Rekomendacja: tak, zostawić tylko ten plik.

## 7. Czego nie sprawdzono

- **Licencje wag modeli** (BiRefNet, U2Net, isnet, InSPyReNet, wav2vec2 PL, all-roberta-large-v1, DeepFilterNet): w klonach nie ma kart modeli ani wag, a odczytu HuggingFace nie robiłem.
- **Czasy CPU:** żadnego repo nie uruchamiałem. Liczby (BiRefNet, takumi 26 ms vs 198 ms, DeepFilterNet RTF, RIFE, pymatting 1000x1000) są z README, benchmarków lub w ogóle nieznane.
- **Jakość na polskim:** wyrównanie CTC (whisperX), `-mc 0`, `-ojf`/DTW i embeddery tematów nie były mierzone; to hipotezy do pomiaru (pozycja 3).
- **tegaki:** wygląd ogonków w wygenerowanym bundlu Latin-Ext i zachowanie SMIL w `getAnimations()` nie były oglądane.
- **Biblioteki spoza klonów:** `@remotion/captions` (algorytm grupowania), `timeweb`/`timesnap` (zegar timecut), marp-core (auto-fit), `@paper-design/shaders` (licencja), `movielite` (licencja), roughjs (licencja), tekst Remotion License.
- **Rozmiary kafelka YouTube:** nie występują w żadnym przeczytanym repo; do zmierzenia Playwrightem.
- **Lottie:** odtwarzacze (lottie-web, dotlottie-web, thorvg, rlottie) przesiane, nieczytane. Przeczytany `diffusionstudio/lottie`: render przez canvaskit lub lottie-web w naszej pętli `render.mjs` jest tylko hipotezą z kodu, nic nie uruchomiono.
- **Niepełna lektura:** SeeCut (`references/01, 02, 04, 08, 10, 11`), JJKoubo `kbcut/SKILL.md` (624 linie, tylko grep), silniki `claude-animation-skills/skills/*/engine`. Brak licencji `video-editor-agent` stwierdzony tylko lokalnie (plik), nie na GitHubie.
- **Czy etap redakcji (Claude/ręczny) łapie powtórki zdań** — nie sprawdzałem; od tego zależy sens pozycji 4.
- **Przesiew metadanych** opiera się na API GitHuba z dnia 2026-11-05; liczba gwiazdek i data ostatniego commita starzeją się.
- **Pliki robocze:** w trakcie lektury jeden czytelnik rozpisał `data.pkl` trzech wag `.pth` przez `python3 -I -m pickletools` (bez wykonania) i zapisał pliki tymczasowe w `scratchpad`, poza repo.

