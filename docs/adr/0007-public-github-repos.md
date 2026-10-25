# ADR-0007 — Kod i zasady stylu w publicznych repo na GitHubie; media na dysku Dane

Data: 2026-10-24 | Status: przyjęte (zastępuje decyzję B z ADR-0001 w części „bez remote”) | Drzwi: jednokierunkowe (publikacja) | Przegląd: 2027-01-24

**Kontekst:** ADR-0001 wybrał lokalny git bez remote i zostawił otwarte ryzyko: brak kopii poza dyskiem. 2026-10-23 inna sesja
założyła prywatne `kamiljan11/video-pipeline` (gałąź `wip/cetus-theme`, podzbiór dzisiejszego `main`). 2026-10-24 Kamil:
„wrzuć jako public repo na GitHub i opisz go ładnie (…) to nam pomoże nie zgubić naszego programu i stylu”, a do tego
„renderów nie ma co tam wrzucać”. Tego samego dnia dysk systemowy zapełnił się renderami (0 B wolnego, przerwany render), a Kamil
kazał przenieść pipeline, nagrania i pobrane filmy na nieużywany dysk Dane (196 GB, LUKS).

**Kryteria:** (1) program i zasady stylu przetrwają awarię laptopa; (2) nic z nagrań, transkrypcji, planów, renderów ani sekretów
nie wychodzi poza laptop; (3) zero kosztów; (4) ścieżki w skryptach, planach i panelu działają bez zmian.

| Kryterium (waga %) | A: jak ADR-0001 (bez remote) | B: prywatne repo | C: publiczne repo (kod + `style/`) | komentarz / ryzyko |
|---|---|---|---|---|
| Kopia poza dyskiem (35) | 1 | 5 | 5 | |
| Wyciek danych (35) | 5 | 4 | 4 | audyt całej historii obu repo 2026-10-24: 0 sekretów, 0 transkrypcji/planów, 0 cudzych danych; w historii jest klatka z twarzą autora (`gfx/test_kw.jpg`, ta sama co w jego filmach) |
| Koszt (10) | 5 | 5 | 5 | |
| Wartość wizerunkowa / „PG wie, jak to się robi” (20) | 1 | 2 | 5 | życzenie Kamila |
| **Suma** | 3,0 | 4,2 | 4,7 | |

**Decyzja:** C. `kamiljan11/video-pipeline` (to samo repo, `main` jako domyślna, widoczność public) + nowe
`kamiljan11/video-pipeline-panel` (panel). Licencja: „all rights reserved” (kod do wglądu i jako kopia; zmiana na MIT później jest
łatwa, odwrotnie nie — opublikowanej licencji otwartej nie da się odebrać). `.gitignore`: `render/`, media (`*.mp4/*.mov/*.wav/*.mkv/*.m4a/*.mp3/*.webm`), napisy (`*.srt/*.ass`),
dane projektu (`words*.json`, `plan_*.json`, `edl_*.json`, `gfx_specs.json`), `.env*`, modele, `node_modules/`, `.venv/`. CI (`.github/workflows/quality.yml`): ruff, testy node i Pythona bez modeli, gitleaks.

Media: `~/video-pipeline`, `~/Videos`, `~/Downloads`, `~/Desktop/Movies` przeniesione rsynciem na `~/Dane/...` i zastąpione
symlinkami o tej samej ścieżce (Syncthing `user-videos` widzi te same pliki: po zmianie `localDeleted` bez zmian). Panel kluczuje
`render/panel/<rodzaj>/<klucz>` po ścieżce rozwiązanej (`store.project_key`) i kopie odtwarzacza po `realpath` wejścia
(`livemedia.stamp`): katalogi i nazwy plików przepisane jednorazowo na nowe klucze (skrypt w transkrypcie sesji 2026-10-24).

**Rozważone alternatywy:** B (prywatne) spełnia kryterium kopii, ale nie życzenie Kamila. Zmiana ścieżek w skryptach na `~/Dane/...`
zamiast symlinków: kilkadziesiąt miejsc (`/home/kamil-jan/video-pipeline` w 21 plikach) i plany w `~/Videos` — więcej ryzyka, zero zysku.

**Konsekwencje:** historia commitów (autor, e-mail `mountainallservice@gmail.com`) jest publiczna. Każdy przyszły commit = publikacja:
skan sekretów pre-commit + gitleaks w CI; transkrypcje, plany i nagrania zostają poza gitem. Dysk Dane jest montowany przy starcie
(`/etc/crypttab` z plikiem klucza, `nofail`): gdy się nie zamontuje, symlinki prowadzą donikąd, a render i panel padną z „brak pliku”
(pierwszy krok diagnozy: `findmnt ~/Dane`). Stare kopie na dysku systemowym: `~/old-copies-2026-10-24/` (122 GB) do usunięcia
przez Kamila po sprawdzeniu.

**Koszt cykliczny:** 0 zł (GitHub Free; minuty Actions w publicznych repo bez limitu płatnego; obraz gitleaks pobierany przy każdym biegu).

**Wykonanie / rollback:** widoczność repo z powrotem na private w ustawieniach GitHuba (to, co już pobrano, zostaje u pobierających).
Dysk: `rm` symlinku + `mv ~/old-copies-2026-10-24/<katalog> ~/<katalog>` (dopóki kopie istnieją) albo `rsync` z `~/Dane` z powrotem.

**Zmiana 2026-10-25 (Kamil):** oba repo na licencji MIT, żeby inni mogli zainstalować i używać narzędzia (prompt instalacyjny w README). Zdjęcie autora, nazwisko i marka nie są objęte licencją.
