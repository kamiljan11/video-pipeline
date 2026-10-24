# ADR-0006 — EDL nie niesie tekstu do ffmpeg: `edl_guard.py` przed `assemble.py`

Data: 2026-10-24 | Status: przyjęte | Drzwi: dwukierunkowe (jedno wywołanie w `assemble.py`) | Przegląd: 2027-01-31

**Kontekst:** recenzja `behind.py` (r15–r16, potwierdzone przez weryfikatora) pokazała, że `assemble.py` wkleja wartości EDL
do tekstu `-vf` / `-filter_complex` (`face`, `face_target_y`, `w/h`, `src_w/src_h`, `zoom/face/track` segmentu, `tail`,
`music_db`, `sfx_db`, `pip_size`, łańcuchy `audio` i `grade`, plik `subs`, kolor motywu) i podaje nazwy plików do `-i`.
Plany i EDL leżą w folderach Syncthing. `face=[0.5, "0.45)),vidstabdetect=result=<plik>,..."]` kazało ffmpeg zapisać plik;
`movie=` / `amovie=` czytają pliki i URL-e mimo `-protocol_whitelist`.

**Decyzja:** `edl_guard.check(edl)` na starcie `assemble.py` (przed każdym ffmpeg tego skryptu); błąd = `EDL refused (<pola>)`, rc 1.
Liczby skończone, |v| < 1e9; łańcuchy `audio`/`grade` tylko z filtrów z listy (`AUDIO`, `VIDEO`) z opcjami `k=wartość` bez
`/`, cudzysłowów i nawiasów; pliki wejściowe lokalne (przed pierwszym `:` musi stać `/`, więc ani `protokół:`, ani forma
`subfile,,opcje,,:`); `out_name` = sama nazwa pliku (ffmpeg pisze ją z `-y`); segment `in < out`, `src` = nazwa z `sources`,
zoom > 0; `tail` 0-60 s; klucz liczbowy obecny = liczba (null = odmowa); `subs` i `sub_style` bez cudzysłowu,
`\` i separatorów filtergraphu; motyw `name` [A-Za-z0-9_-], `acc` #RRGGBB. `behind.py` używa tych samych reguł kadrowania.
Poprawne EDL dają identyczne komendy ffmpeg (test zgodności z `assemble.py.orig`).

**Odrzucone:** escapowanie wartości (łatwo o pominięte miejsce, a liczba i tak ma być liczbą); walidacja tylko w
`build_edl.py` (EDL też leży w zsynchronizowanym folderze); `-protocol_whitelist` dla każdego `-i` (zmienia komendy, nie
zamyka filtrów).

**Zakres i ryzyko resztkowe (pg-review 2026-10-24):**
- Guard działa w `assemble.py`, czyli po `make_beds`, `face_track` i `behind.py` w `run_v4.sh`. `behind.py` sprawdza te same
  reguły kadrowania; zły łańcuch `audio` wychodzi dopiero na końcu (wywołanie zaraz po `build_edl` w `run_v4.sh` = następny krok).
- Wejścia mogą wskazywać dowolny lokalny plik (np. inne nagranie z `~/Videos`); ograniczenie do katalogu projektu = decyzja Kamila.
- Odrzucone przez recenzję ścieżki (playlista HLS jako źródło, `subfile` -> http) są bezpieczne dzięki zagnieżdżonym
  whitelistom protokołów ffmpeg 8.0.1; starszy ffmpeg = sprawdzić ponownie.

**Konsekwencje:** nowy filtr w `audio`/`grade` planu = dopisanie go do listy w `edl_guard.py` (świadoma decyzja, nie
przypadek). Koszt cykliczny: 0 zł.
