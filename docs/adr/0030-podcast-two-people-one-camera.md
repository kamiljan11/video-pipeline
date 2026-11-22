# ADR-0030 — Tryb podcast: dwie osoby, jedna kamera szeroka

Data: 2026-11-22 | Status: proponowane | Drzwi: dwukierunkowe | Przegląd: po pierwszym renderze nagrania 2026-11-19

**Kontekst:** Kamil (2026-11-22): nowy format, „2 osoby gadające ze sobą, podcast”, na kanał ArkadiuszDworak.pl;
„nie możemy tak samo edytować jak kiedy jest jedna osoba, bo zasłonimy ludzi”, shorty też trzeba przemyśleć.
Nagranie: jeden plik z telefonu (S25 Ultra, `20261119_121337.mp4`, 28,5 GB). Pipeline zakładał jedną osobę wszędzie:
`face_track.py` bierze największą twarz, kadr 9:16 i karty boczne stoją pod jedną głowę w środku
(mapa: `research/podcast/PIPELINE-MAP.md`).

**Badania:** `research/podcast/RESEARCH-LONGFORM.md` (~58 źródeł, saturacja od ~25) i `RESEARCH-SHORTS.md` (~45 stron,
saturacja układów i napisów przy ~8-9). Zgodne reguły: domyślnie mówiący, szeroki plan na otwarcie i jako przerywnik;
nie przełączać na każde „mhm”; z jednej kamery 4K = „wirtualny multicam” (szeroki + wycinek na osobę); w shortach kadr
na mówiącego, układ jedna-nad-drugą tylko przy szybkiej wymianie zdań, napisy na styku paneli. Liczby (2 s trzymania,
18 s maks. ujęcia) to domyślne wartości narzędzi, nie zmierzona retencja: są danymi w `style/podcast.json`.

**Decyzja:**
1. Klucz planu `"podcast": true` albo obiekt z kluczami `style/podcast.json` (nadpisanie na jeden film). Bez klucza
   nic się nie zmienia (stare plany renderują się jak dotąd).
2. `face_track.py` przy `podcast` oddaje EDL do `podcast.py`. Ten tnie kawałki EDL w miejscach zmiany ujęcia (na siatce
   klatek: suma klatek bez zmian, `timeline.piece_len`) i wpisuje pola, które `assemble.py` już czyta: `face` + stały `zoom`.
   Ujęcia 16:9: `wide` (obie osoby), `L` / `R` (wycinek na osobę, `single_zoom`). Ujęcia 9:16: `L` / `R` (pełna wysokość
   na jedną twarz) i `stack` (L na górze, R na dole; nowa gałąź `assemble.stack_vf`).
3. Kto mówi: `podcast_faces.py`, ruch ust (różnica klatek w dolnej części ramki twarzy, każda strona dzielona przez swoją
   medianę), YuNet jak w `face_track.py` na klatkach 960x540. Wynik w `podcast_spk.json` (pamięć podręczna), ręczna
   poprawka w `podcast_fix.json` (`[[t0, t1, "L"|"R"], ...]`). Raport liczy słowa bez pewnego mówcy.
4. Karta boczna 16:9 (`gfx_types.SIDE_BOX`) nad planem szerokim zasłoniłaby osobę: pod kartą idzie ujęcie mówiącego.
5. Napisy 9:16 w trybie podcast domyślnie `caption_v` 900 (styk paneli `stack`, pod brodą w ujęciu pojedynczym);
   domyślne 540 wypadało na twarzy dolnej osoby.
6. Kolorystyka kanału: motyw `style/themes/dworak.json` (kolory z CSS arkadiuszdworak.pl, wariant ciemny), wybór przez
   `work/theme.json`. Motyw `cetus` i domyślny zostają bez zmian.

**Rozważone:** (a) pyannote / WhisperX do rozpoznania mówców: licencje OK (MIT/BSD), ale ciężkie na CPU (szacunek 20-50+ min
na godzinę audio, bez pomiaru) i trzeba jeszcze przypisać mówcę do strony kadru; zostaje jako kolejny backend, jeśli ruch ust
zawiedzie. (b) Model ASD (TalkNet, Light-ASD, MIT): brak zmierzonej prędkości na CPU, wagi AVA słabo się przenoszą.
(c) Gotowe narzędzia (OpusClip, Vizard): płatne, poza pipeline'em, padają przy osobach siedzących blisko.
(d) Osobna ścieżka renderu dla podcastu: odrzucone, ten sam `vf_for` dostaje inne `face`/`zoom`, mniej kodu do utrzymania.
(e) Licencje AGPL/niekomercyjne (podcli, SupoClip, modele InsightFace): odrzucone, sprzedajemy oprogramowanie.

**Kryterium sukcesu (sprawdzane na pierwszym nagraniu, przed renderem longa w `review_player.py`):** raport `podcast.py`
pokazuje ≤ 10 % słów bez pewnego mówcy (`?`) i ≤ 3 uwagi Kamila „zła osoba w kadrze” na 10 min filmu. Gorzej = ręczne
`podcast_fix.json` na ten film i backend pyannote (Rozważone a) jako kolejny krok. Progi to założenie, nie pomiar.

**Ryzyka i zabezpieczenia:**
- Heurystyka ruchu ust nie była sprawdzona na prawdziwym nagraniu (plik jeszcze się kopiuje). Zabezpieczenia: `?` zamiast
  zgadywania, ostrzeżenie przy >20 % słów bez mówcy, `podcast_fix.json`. Pierwszy render = przegląd wzrokowy.
- Jedna ścieżka dźwięku (mikrofon telefonu): nie da się ściszyć jednej osoby przy przegadywaniu; tylko zostawić albo wyciąć.
- Wycinek `single_zoom` 1,8 z 4K do 2560x1440 to powiększenie ~1,33x (3840/1,8 = 2133 px szerokości): lekka utrata ostrości.
- 4K: `assemble.py` liczył kadr dla 2560x1440, gdy EDL nie miał `src_w`/`src_h`; `podcast.py` wpisuje prawdziwy rozmiar.

**Nie robimy teraz (puste sloty):** kolor napisów wg mówcy i podpisy z imionami (klucz `podcast.speakers` jest przepuszczany
przez `podcast_shots.load_cfg`, nic go jeszcze nie czyta), wybór klipów do shortów z parą pytanie-odpowiedź w `shorts.py`, backend pyannote, J/L-cięcia dźwięku.

**Koszt cykliczny:** jedno przejście ffmpeg po zakresach filmu (10 kl./s, 960x540) na pierwszy przebieg każdego nagrania;
potem pamięć podręczna `podcast_spk.json` (klucz: wersja algorytmu, rozmiar i mtime pliku, czasy słów, reguły).
Czas na prawdziwym 4K niezmierzony. Utrzymanie: `style/podcast.json` + trzy moduły `podcast*.py`, testy
`tests/test_podcast*.py`.

**Wycofanie:** usunąć `"podcast"` z planu: `face_track.py` wraca do starej ścieżki, EDL bez pól `shot`/`stack`/`spk`.
Całkowite: revert commitu tej zmiany; stare plany nie używają żadnego nowego pola.
