# ADR-0032 — Rodzaj materiału: system sam rozpoznaje jedną osobę albo rozmowę dwóch osób

Data: 2026-11-22 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: po pierwszym filmie solo i pierwszym podcaście z pomiarem

**Kontekst:** ADR-0031 włączał tryb podcastu ręcznym kluczem planu `"podcast"`. Kamil (2026-11-22): „nasz system ...
powinien sam rozpoznawac czy to bedziemy stosowac logiki ... jednej osoby ... czy ... 2 osob bo wtedy inne logiki
powinny wejsc”. Reguły różnią się w każdym kroku: kadr (`podcast.py`), punch-iny (`build_edl`), progi grafik
(`film_check`, klucz `"podcast"` w `style/checklist.json`).

**Decyzja:**
1. `content_kind.py <work> <plan>` (krok `run_v4.sh` przed `build_edl`, python z venv, bo potrzebuje cv2) bierze
   `samples` klatek równo z całego nagrania. Szuka twarzy YuNet, tym samym modelem co `face_track.py`. Twarz liczy się
   od `min_face` wysokości kadru. `talk`, gdy 2+ twarze są w >= `share` klatek; `solo`, gdy 1. Liczby: `style/content_kind.json`.
2. Wynik trafia do `<work>/content_kind.json` pod `sources[src]`, z rozmiarem i mtime nagrania (`kind.key`). Long i shorty
   z tego samego nagrania dzielą jedną odpowiedź; inne `src` (np. gotowy long) dostaje własny wpis.
3. `kind.is_talk(plan, work)` = jedno miejsce odpowiedzi dla `build_edl` i `film_check`. Kolejność: klucz `"podcast"`
   planu (`true`/obiekt = rozmowa, `false`/`null` = solo), potem pomiar, a bez pomiaru solo (jedna linia na stderr).
   Plik zepsuty albo z innej wersji nagrania = stop z poleceniem ponownego pomiaru, nie cicha zgadywanka.
4. Pomiar niejasny (ktoś wychodzi z kadru, nagranie ekranu, ciemno) = reguły solo, czyli te, które miał każdy film
   przed 2026-11-22. W `render.log` idzie linia `WARN content_kind: not clear`, w pliku `"clear": false`. Decyzję podejmuje
   człowiek kluczem w planie.

**Odrzucone:**
- Stop przy niejasnym pomiarze: nocny run dawałby 0 filmów (2026-11-10), a reguły solo to dotychczasowe zachowanie.
- Próbki z keeps planu: wynik zależałby od planu, a long i shorty z jednego folderu nadpisywałyby sobie pomiar.
- Diaryzacja głosu (pyannote): model z licencją HF i instalacja to decyzja Kamila. Twarze w kadrze wystarczą do
  rozróżnienia jednej kamery na jedną osobę od jednej kamery na dwie.

**Ryzyko:** druga twarz >= 8 % wysokości w >= 60 % klatek (osoba w tle, ekran z twarzą) da fałszywe `talk`. Trzy osoby
też dadzą `talk`. Na to jest ręczny klucz `"podcast": false`. Sprawdzone: podcast Dworak 2026-11-19 = 24/24 klatki z 2 twarzami.
Walidacji na nagraniu solo jeszcze nie było (nagrania solo są w chmurze); zrobić przy pierwszym filmie solo.

**Rollback:** `"podcast": false` w planie (jeden film) albo usunięcie kroku z `run_v4.sh` (wszystkie: wraca ADR-0031).
