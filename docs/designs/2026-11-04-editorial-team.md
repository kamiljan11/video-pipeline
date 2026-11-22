# Design: zespół montażowy (role, artefakty, bramka kompletności)

Tier: T2 · Data: 2026-11-04 · Autor: Claude (sesja e121fa47) · Status: wdrożony na gałęzi `feat/film-v2-motion` (ADR-0011)

## 1. Problem
Film 2026-11-04 („Coding Higher Mind”) wyszedł płaski. Kamil (4.11): „w ciul pominąłeś”, „najbardziej mi zależy na graficznym
animowanym pokazywaniu moich pomysłów”, „pod shorty zero nowych logik”, „nie widzę plików z tytułami, opisami per platforma”,
„miałeś zawsze robić A/B thumbnaile”. Dowody (`render/montaz/2026-11-04/work/AUDYT_ZASAD.md`):
- 32 karty w longu vs 70 w filmie 1; 0 kart `float`/`slide`/`scene`/`behind`; najdłuższa przerwa bez karty 166 s.
- Muzyka: `gen_music.py` = ten sam utwór w każdym filmie (seed 7, korelacja podkładów 0,986-0,999).
- Rozdziały 1 i 2 zakotwiczone na zdaniu kończącym myśl („I to jest pierwszy pomysł”), nie na wejściu części.
- Render szedł z checkoutu bez `main` (#6 memy, napisy pop) i bez gałęzi `feat/scene-cards`.
- Brak metadanych YouTube, miniatur A/B, okładek shortów; film 1 miał je robione ręcznie w sesji.
Przyczyna wspólna: plan pisany ręcznie (`build_plan.py`) bez listy kontrolnej; nic nie sprawdza, czy funkcja została użyta.

## 2. Cele i kryteria akceptacji
- **G1 Nic nie ginie:** przed renderem `film_check.py <work>` sprawdza każdą pozycję z `style/checklist.json` (long, short,
  pakiet publikacji) i kończy się kodem 1, jeśli pozycja nie jest spełniona ani pominięta z powodem (`"skip": {"id": "powód"}`
  w planie). Sprawdzenie: test jednostkowy na planie filmu 2 sprzed zmian = wypisuje te luki, które wskazał Kamil (rozdziały,
  behind, sceny, muzyka, podpis, miniatury).
- **G2 Pomysły pokazane animacją:** każda część (rozdział) longa ma ≥1 kartę `scene` lub `float`, a karty mają ruch: rysowane
  linie, wskaźnik, ptaszek z rozbłyskiem, kamera. Sprawdzenie: `film_check` (pozycja `long.explainers`) + arkusz klatek.
- **G3 Muzyka inna w każdym filmie:** `music_palette` w planie; `film_check` odrzuca paletę+tonację użytą w poprzednim filmie
  (rejestr `render/music_ledger.json`). Sprawdzenie: korelacja podkładów 2 palet < 0,5 (test).
- **G4 Ilość z jakości, nie z przyzwyczajenia:** shorty i posty powstają ze wszystkich kandydatów, którzy przejdą próg
  oceny w `clips.json`/`posts.json` (kryteria w roli `shorts-scout`/`social`), a nie stała liczba. Sprawdzenie: `film_check`
  porównuje liczbę zrenderowanych shortów z liczbą kandydatów ≥ progu.
- **G5 Pakiet publikacji:** w `out/` są: long, wszystkie shorty, `youtube/` (3 tytuły A/B/C, opis z rozdziałami, tagi,
  przypięty komentarz; dla każdego shorta tytuł i opis), `thumbnails/` (≥2 warianty dla longa, okładka na short), `posts/`
  (LinkedIn: tekst + grafika/PDF dla każdego posta). Sprawdzenie: `film_check --out`.

Metryka sukcesu: ocena Kamila po obejrzeniu + po publikacji retencja YouTube Studio w miejscach scen vs gadającej głowy
(ręcznie; event w kodzie: brak, bo publikacja jest poza pipeline'em).

## 3. Non-goals
- Publikacja i upload (YouTube, LinkedIn) — zostaje ręczna decyzja Kamila (memory „watch locally”).
- Generacja muzyki modelem AI (MusicGen = licencja NC; ACE-Step niezmierzony na CPU) — palety syntezy teraz, AI później.
- Własna maskotka — rolę postaci gra Kamil w kółku (`face_corner`).
- Przepisywanie panelu (`panel/`) — role pracują na plikach, panel czyta te same plany.

## 4. Ścieżka użytkownika (CUJ)
1. Kamil wrzuca nagranie do `~/Videos/Nagrania/` i pisze „montuj”.
2. Sesja Claude Code prowadzi zespół wg `team/RUNBOOK.md`: każda rola czyta artefakty poprzedniej i zapisuje swój.
3. `run_v4.sh` woła `film_check.py` przed renderem; luka = `FAILED film_check` z listą (co, dlaczego, jak naprawić).
4. Po renderze: recenzja widza (`viewer_pack.py` + agent), `film_check --out` na folderze `out/`.
5. Kamil ogląda folder `out/` (jeden folder: long, shorty, posty, miniatury, metadane, `RAPORT.md`).

## 5. Plan per plik
| Plik | Zmiana |
|---|---|
| `team/RUNBOOK.md` (nowy) | Kolejność ról, wejścia/wyjścia, bramki między etapami, mapa procesu (mermaid) |
| `team/roles/*.md` (nowe) | Karta roli: misja, wejście, artefakt, rubryka, „gotowe gdy” (producent, fact-checker, montażysta, motion designer, operator zoomów, dźwiękowiec, scout shortów, producent shortów, grafik miniatur, copywriter/social, QA-widz) |
| `style/checklist.json` (nowy) | Lista pozycji kontrolnych (dane, edytowalne): id, format, opis, cytat Kamila, próg |
| `film_check.py` (nowy) | Bramka: liczy metryki z planu/EDL/specs/out, porównuje z checklistą, obsługuje `skip` z powodem |
| `run_v4.sh` | Woła `film_check.py` po `edl_guard`, przed renderem; `FAILED film_check <film>` |
| `music/gen_music.py` | Palety (`--palette`, `--key`): tempo, tonacja, akordy, groove, barwa; bez flag = stary podkład bit w bit |
| `music/make_beds.py`, `build_edl.py` | Przekazanie `music_palette` z planu do EDL i do `gen_music.py` |
| `gfx/scene_lib.mjs` | Nowe ruchy: rysowana linia SVG, ptaszek z rozbłyskiem, kursor z falą kliknięcia, przekreślenie, licznik, plamy tła |
| `gfx/thumbs.mjs` (nowy, z `render/montaz/2026-10-22/work/thumbs.mjs`) | Miniatury A/B longa i okładki shortów z danych (`thumbs.json`) |
| `assemble.py` | Pion 9:16: skalowanie lanczos + lekkie wyostrzenie (Kamil: „możesz upscalować”) |
| `docs/adr/0011-editorial-team.md` | Decyzja: role = karty + bramka 0-tokenowa, nie nowy orkiestrator |

## 6. Alternatywy (odrzucone)
- **Nic nie zmieniamy, tylko lepszy ręczny plan:** tak było w filmie 2 i zgubiło połowę funkcji; pamięć sesji nie jest bramką.
- **Workflow wieloagentowy uruchamiany co film:** drogi w limicie tygodniowym i wymaga hasła Kamila; role jako karty +
  sesja główna + bramka skryptowa daje to samo sprawdzenie za 0 tokenów.
- **Gotowy produkt (Opus Clip, Submagic):** płatny, chmurowy, nie zna marki ani zasad Kamila; bierzemy logikę, nie produkt.

## 7. Założenia, które ta zmiana unieważnia
| Założenie | `rg` | Trafienia do zmiany |
|---|---|---|
| muzyka = jeden podkład 92 BPM Am-F-C-G | `rg -n "92 BPM" music/` | 1 (docstring; zostaje dla trybu bez palety) |
| podpis „Automatyzacje i wdrożenia AI” | `rg -n "Automatyzacje i wdrożenia AI" --hidden -g '!render'` | 0 w kodzie (tylko dane projektów) |
| shorty = stała lista w planie | `rg -n "short1\|s1_" run_v4.sh` | 0 (lista filmów z argumentów) |

## 8. Ryzyka
- Bramka za ostra -> zatrzymuje render o rzecz zbędną: każda pozycja ma `skip` z powodem w planie. Poziomu `warn` nie ma
  (zmiana wobec szkicu): każda pozycja blokuje od pierwszego dnia, bo luki filmu 2 v1 były właśnie rzeczami „na później”.
- Render 60 fps i więcej scen = dłuższy render (karty 2x): akceptowane; `--proxy` do podglądu.
- Sceny z „tekstem z terminala” muszą być prawdziwe (wynik polecenia przepisany), inaczej film kłamie: rola fact-checker.
- Bezpieczeństwo: brak nowych zależności sieciowych; GSAP lokalny (licencja „no charge” od 30.04.2025), brak pobierania kodu.

## 9. Niezmienniki
- Bez nowych kluczy planu obraz i dźwięk identyczne jak dotąd: palety i upscale są opt-in (`film_check` nie zmienia renderu,
  tylko go zatrzymuje). Bramka `film_check` jest domyślnie WŁĄCZONA także dla starych planów (zmiana wobec szkicu): projekt
  sprzed listy kontrolnej (np. film 1, plany z panelu) renderuje się tylko z `FILM_CHECK=off` (w `render.log` zostaje
  `WARN film_check off <film>`). Decyzja do potwierdzenia przez Kamila przy merge; alternatywa = domyślnie off dla planów bez
  `story.json`.
- EDL do ffmpeg tylko przez `edl_guard.py` (ADR-0006).

## 10. Weryfikacja
- `.venv/bin/python -m unittest discover -s tests` (nowe: `test_film_check.py`, `test_music_palette.py`), `npm test` (nowe
  testy scen), `ruff check .`, `pyright`.
- `python3 film_check.py render/montaz/2026-11-04/work --plans-dir _plans_bak` = lista luk z §1 (kryterium G1).
- Pełny render filmu 2 do `render/montaz/2026-11-04/out_v2/`, `film_check --out` zielony, arkusze klatek obejrzane.

## 11. Wdrożenie i rollback
Gałąź `feat/film-v2-motion`, PR do `kamiljan11/video-pipeline`, merge dopiero po obejrzeniu przez Kamila i jego komendzie.
Rollback = revert PR. Stare plany bez revertu: `FILM_CHECK=off` (obraz jak wcześniej; karty bez `.key` renderują się raz od nowa).

## Status recenzji
| Kiedy | Kto (dział / rubryka) | Werdykt | Otwarte punkty |
|---|---|---|---|
| 2026-11-04 | pg-review T3: code, security, data, ops, product + weryfikator (`~/.cache/pg-review-20261104-192841`) | REQUEST CHANGES (1 blocker, 9 must_fix), poprawki w tej samej gałęzi | domyślne `FILM_CHECK` dla starych planów (Kamil) |
