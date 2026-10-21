# ADR-0001 — Pipeline w lokalnym gicie; zależności zewnętrzne (Node, ffmpeg, Pexels)

Data: 2026-10-21 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: 2026-12-01

**Kontekst:** `~/video-pipeline` (skrypty montażu: transkrypcja, `build_edl.py`, `assemble.py`, grafiki `gfx/render.mjs`) działał
bez kontroli wersji; jedyną historią były tary `render/pipeline-snapshot-*.tar.gz` i kopie `.orig` w repo panelu. Kamil
(2026-10-21, pytanie 1 z ADR-0002 panelu): „yes” = repo gita. Przy okazji pierwszy raz trafia do wersjonowania `package.json`
z zależnościami, które były używane od początku (`playwright-core`: Chrome renderuje plansze HTML do `.mov`;
`lucide-static`: ikony SVG kart), a b-roll (ADR-0003 panelu) dokłada pierwszą zależność sieciową: Pexels API.
Decyzje montażowe (gramatyka, b-roll) są opisane w `panel/docs/adr/` (0002, 0003); tu tylko repo i zależności.

**Kryteria:** (1) każda zmiana skryptu i `style/grammar.json` ma historię i da się cofnąć jedną komendą; (2) nic z nagrań,
renderów ani sekretów nie trafia do repo (`~/Videos` jest w Syncthingu, plany są niezaufane); (3) zero kosztów i kont.

Profil wag: własny — jedna osoba, lokalne narzędzie, priorytet = nie stracić działającej wersji i nie wypuścić danych.

| Kryterium (waga %) | A: bez gita, tary (stan) | B: lokalny git, bez remote | C: git + prywatne repo na GitHubie | komentarz / ryzyko |
|---|---|---|---|---|
| Historia i cofanie (40) | 2: tar ręcznie, bez diffu | 5: `git log -p`, revert | 5: jak B | |
| Ryzyko wycieku (35) | 5: nic nie wychodzi | 5: nic nie wychodzi | 3: transkrypcje i ścieżki w historii poza laptopem | `.gitignore`: render/, node_modules, modele, *.mp4/*.wav/*.mov, panel/ |
| Kopia poza dyskiem (15) | 2: tar na tym samym dysku | 2: jak A | 5 | ryzyko B: awaria dysku = utrata historii (kopie dysku Kamila) |
| Koszt / konta (10) | 5 | 5 | 4: PAT przez most Infisical | |
| **Suma** | 3,3 | 4,6 | 4,2 | |

**Decyzja:** B. Repo lokalne, bez remote; panel ma własne repo w `panel/` (ignorowany tutaj). Zależności:
- Node (`package.json`): `playwright-core` (render plansz; używa zainstalowanego Chrome, nie pobiera przeglądarki),
  `lucide-static` (ikony; nazwa ikony to tylko nazwa pliku — sprawdza panel). Wersje z `^` jak dotąd; lockfile w repo.
- System: ffmpeg/ffprobe, whisper.cpp + model (poza repo), `.venv` (Python 3.12: opencv-python-headless + YuNet dla
  `face_track.py`/`head_check.py`, numpy, opentimelineio, faster-whisper dla zapasowego `transcribe.py`); kroki: `README.md`.
- Sieć: tylko `stock.py` (Pexels API + pliki z `videos.pexels.com`), tylko na żądanie („Dobierz b-roll”), klucz z Infisicala
  (`infisical_bridge.py run --secrets Pexels`), nigdy w plikach. Render, krytyk i reszta działają offline; bez sieci dobór
  b-rollu przerywa się z komunikatem, a film renderuje się z klipami już pobranymi do `render/broll/`.

**Rozważone alternatywy:** A odpada, bo zmiana progu w gramatyce albo skryptu nie miała diffu ani cofnięcia (kryterium 1).
C odpada na dziś: wyciek transkrypcji/ścieżek do historii poza laptopem nie jest wart kopii zapasowej, którą daje backup dysku;
wraca, gdy Kamil będzie chciał pracować na drugim komputerze. Pixabay jako drugi dostawca stocku: pusty slot w `stock.PROVIDERS`
(potrzebny klucz = konto Kamila).

**Konsekwencje:** zysk = historia reguł (`git log -p style/grammar.json`) i bramki pre-commit (ruff, pyright, skan sekretów)
na skryptach. Koszt = commit 652914d musiał najpierw naprawić błędy ruff i pyright w starych skryptach (wynik
identyczny: testy zgodności panelu), jedna regresja wyszła później (`head_check.py`: `gfx_specs: null` -> TypeError; naprawiona,
sprawdzona ręcznie na renderze, bez testu automatycznego — head_check potrzebuje modelu i wideo). Zależność od Pexels: zmiana API/limitu (200 zapytań/h) psuje tylko dobór nowych klipów.

**Koszt cykliczny:** 0 zł (Pexels bez opłat: 200 zapytań/h, 20 000/mies.; wytyczne API proszą o link do Pexels i autorów =
linie `credits` do opisu filmu). Ryzyko: brak kopii poza dyskiem (B) — kopia = backup dysku laptopa; inaczej wraca opcja C.

**Wykonanie / rollback:** repo istnieje od 652914d; cofnięcie decyzji = usunąć `.git` (pliki zostają). Zależność Pexels
cofa się usunięciem `broll` z `style/grammar.json` (pipeline bez klucza planu `broll` działa jak wcześniej).
