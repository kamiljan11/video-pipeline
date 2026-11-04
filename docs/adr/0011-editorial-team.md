# ADR-0011: montaż jako praca zespołu ról z bramkami, nie jeden przebieg

Data: 2026-11-04 · Status: przyjęta (do oceny po filmie 2, wersja v2)

## Kontekst
Film 2 (2026-11-04, Coding Higher Mind) w pierwszej wersji pominął rzeczy, które Kamil już zamawiał: karty rozdziałów na
starcie każdej części (była tylko jedna), zoomy, napisy za plecami, nowa muzyka na każdy film, animowane pokazanie pomysłów
(„najbardziej mi zależy”), posty z grafiką, pliki z tytułami i opisami na platformy, miniatury A/B. Shortów było 5, bez
sprawdzenia, czy dobrych fragmentów nie jest więcej. Wspólna przyczyna: jeden przebieg „zrób film” bez listy, kto za co odpowiada
i co musi istnieć, zanim film wyjdzie.

## Decyzja
Montaż prowadzi `team/RUNBOOK.md`: 12 etapów, każdy z kartą roli w `team/roles/` (technik, producent, fact-checker, montażysta,
motion designer, operator, dźwiękowiec, scout shortów, producent shortów, pakowanie, social, QA widza). Karta mówi: misję,
wejście, wyjście (plik), liczby z researchu (`render/ref/research/`) i kiedy etap jest skończony.
Bramki są danymi i kodem, nie pamięcią:
- `style/checklist.json` + `film_check.py`: co każdy long, short i folder wyjściowy musi mieć; pozycję można pominąć tylko z
  powodem w planie (`"skip"`), wypisanym w raporcie.
- Ilość shortów i postów wynika z oceny kandydatów (`clips.json`, `posts.json`, skala 0-3 na kryteria z kart scouta i social),
  nie ze stałej liczby; `out.shorts_all` i `out.posts` sprawdzają, że każdy kandydat z `"make": true` jest w folderze.
- `gfx/scene_check.mjs` przed renderem (kolizje elementów scen), `thumbs.mjs` (tekst miniatury mieści się w kadrze).
Plany filmu generuje skrypt projektu (`build_plan_v2.py`, `build_shorts_v2.py`, `build_pack_v2.py`, `build_posts_v2.py`):
każda karta jest przypięta do słowa z transkryptu (szukanego po tekście, nie wpisanego ręcznie), czasy w filmie liczy EDL.

## Konsekwencje
- Więcej kroków i dłuższy render (sceny, wiele shortów). Koszt przyjęty: Kamil ogląda gotowy folder, zamiast wyliczać braki.
- Shorty w stylu sceny (BreakingBreach): `short.punch` pomijany z powodem, gdy sceny zajmują >= 60 % shorta (zoom twarzy pod
  sceną nie istnieje; kamera sceny prowadzi oko). Do oceny po pierwszych publikacjach.
- Nic nie jest publikowane automatycznie: `out_v2/` to paczka do obejrzenia; publikacja na LinkedIn tylko przez
  `linkedin.py publish` z kodem zatwierdzenia Kamila (ADR-0009).
- Metryka: liczba rzeczy, które Kamil wskazuje jako pominięte po obejrzeniu (film 2 v1: 9 punktów; cel v2: 0 z tej listy).

## Gdzie co leży (dla następcy)
| Co | Gdzie | Dlaczego tam |
|---|---|---|
| Bramki i ich progi (z `why`: skąd liczba, cytat Kamila albo rozbiór) | `style/checklist.json`, `film_check.py`, `gfx/scene_check.mjs`, `gfx/thumbs.mjs` | repo: ogólne dla każdego filmu |
| Role i kolejność | `team/RUNBOOK.md`, `team/roles/*.md` | repo |
| Generatory planów filmu (`build_plan_v2.py`, `build_shorts_v2.py`, `build_pack_v2.py`, `build_posts_v2.py`) | `render/montaz/<data>/work/` (gitignored) | dane projektu jak `plan_*.json`: przypinają karty do słów TEGO nagrania; nowy film = kopia skryptów poprzedniego i nowa treść |
| Notatki z researchu (rozbiory, tutoriale, przegląd repo OSS) | `render/ref/research/*.md` (gitignored) | zawierają opisy i cytaty cudzych materiałów; liczby, których używa bramka, są przepisane do `why` w `checklist.json` |
| Rejestr muzyki (paleta i tonacja każdego projektu) | `render/music_ledger.json` (gitignored) | stan jednej maszyny renderującej (laptop); zapis atomowy (`make_beds.py`), zepsuty plik = `film_check` exit 2 z nazwą, nie cichy przepust. Inna maszyna = pusty rejestr, bramka palety przepuszcza pierwszy film |
| Posty LinkedIn (`linkedin.py`, ADR-0009) | gałąź `feat/linkedin-carousel` (osobny PR) | luka 0008 -> 0010 w `docs/adr/` do czasu merge tamtego PR |

**Koszt cykliczny:** 0 zł (wszystko lokalnie; brak nowych kont, kluczy i zależności sieciowych). Czas: dłuższy render (sceny,
wiele shortów) i ok. 30 min pracy sesji na przygotowanie planów przez generatory.
