# video-pipeline

Skrypty montażu nagrań (talking head -> long 16:9 + shorty 9:16). Lokalne repo gita bez remote (ADR: `docs/adr/0001-*`).

| Krok | Skrypt | Uruchamia |
|---|---|---|
| transkrypcja | `chunked_whisper.py` (whisper.cpp; `transcribe.py` = to samo na faster-whisper, zapasowo) | ręcznie / zadanie |
| momenty montażu | `beats.py`, `beatfx.py` (reguły: `style/grammar.json`, źródła: `style/RESEARCH.md`) | panel „Rozpoznaj momenty” |
| b-roll stock | `broll.py` (dobór), `stock.py` (Pexels, klucz `Pexels` z Infisicala) | panel „Dobierz b-roll” |
| EDL | `build_edl.py` -> `face_track.py` | panel / `run_v4.sh` |
| krytyk | `critic.py` (C1–C11), `head_check.py` | panel / `run_v4.sh` |
| muzyka | `music/make_beds.py` | `run_v4.sh` |
| render | `assemble.py` (`--proxy` = podgląd), grafiki `gfx/render.mjs` | `run_v4.sh <work> <out> <filmy…>` |

Panel montażowy i cała dokumentacja (README z obsługą błędów, kluczami planu i kontraktami skryptów, słownik, ADR gramatyki
montażu i b-rollu, testy tych skryptów): `panel/` — osobne repo gita (tu ignorowane), zob. `panel/README.md`,
`panel/docs/GLOSSARY.md`, `panel/docs/adr/`.

Logi (`render/`): `render.log` (każdy krok, `DONE <film>` / `FAILED <krok> <film>` / `FAILED_FILMS`), `critic_<film>.log`,
`beat_stats.log` (metryka po renderze), `gfx.log` w katalogu `work` projektu.

Jednorazowe skrypty projektu 2026-10-20 (sztywne ścieżki, nie do nowych projektów): `render_v3.sh`, `render_all.sh`,
`check_long.sh`, `final_check.sh`. Pomocnicze: `run_whisper.sh` (whisper.cpp bez dzielenia), `spot_check.py`, `verify_cut.py`,
`lines.py`, `to_otio.py` (eksport long do Kdenlive, woła go `run_v4.sh`), `stop_render.py`, `pdl.sh` (pobieranie równoległe),
`music/gen_music.py`. `PANEL_SPEC.md` / `PROMPT_PANEL.md` = historyczna specyfikacja panelu (aktualna: `panel/README.md`).

## Postawienie od zera (Ubuntu)
Ścieżka `/home/kamil-jan` jest wpisana w wielu skryptach (m.in. `run_v4.sh`, `assemble.py`, `face_track.py`, `head_check.py`,
`chunked_whisper.py`, `gfx/*.mjs`): na innym koncie/komputerze najpierw znajdź wszystkie (`grep -rl /home/kamil-jan --include=*.py
--include=*.sh --include=*.mjs . | grep -v -e node_modules -e whisper.cpp -e panel/`).
1. System: `ffmpeg`, `python3` (systemowy: build_edl, critic, assemble, beats, beatfx, broll, stock), Node 24, Google Chrome w
   `/usr/bin/google-chrome` (plansze renderuje `playwright-core` na tym Chrome). `.venv`: face_track, head_check, make_beds, to_otio.
2. `npm ci` (playwright-core, lucide-static z `package-lock.json`).
3. `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt` (wersje przypięte, stan 2026-10-21).
4. whisper.cpp: `git clone https://github.com/ggml-org/whisper.cpp && cmake -B whisper.cpp/build -S whisper.cpp &&
   git -C whisper.cpp checkout 231638a && cmake --build whisper.cpp/build -j` (231638a = wersja używana od 2026-10); model: `whisper.cpp/models/download-ggml-model.sh large-v3-q5_0`, plik do
   `models/ggml-large-v3-q5_0.bin`.
5. `models/face_detection_yunet_2023mar.onnx`: detektor twarzy YuNet z https://github.com/opencv/opencv_zoo
   (`models/face_detection_yunet/`, plik przez Git LFS); sha256 lokalnej kopii zaczyna się od `8f2383e4dd3cfbb4`.
6. B-roll: sekret `Pexels` w Infisicalu (most `~/infisical`); bez niego reszta pipeline'u działa.
7. Panel: `panel/` (własne repo bez remote, ta sama kopia dysku; `panel/README.md`).
8. Lint/typy (globalnie, nie w `.venv`): `pipx install ruff`, `npm i -g pyright`.

Przed publikacją shorta z b-rollem: linie autorów do opisu filmu (wytyczne API Pexels) = okno „Dobierz b-roll” w panelu albo
`python3 broll.py plan_<film>.json --credits` w katalogu `work`.

Bramki: pre-commit (ruff, pyright, skan sekretów) działa przez globalne `core.hooksPath=~/.claude/git-hooks` laptopa, nie z repo;
na innej maszynie uruchamiaj `ruff check . && pyright` ręcznie. Kopia: repo bez remote (ADR-0001), backup = kopia dysku laptopa.

Testy skryptów: `cd panel && .venv/bin/python -m unittest discover -s tests` (strażnik zgodności: bez nowych kluczy planu
wynik identyczny jak `panel/tests/pipeline_baseline/*.py.orig`). Lint: `ruff check .`, `pyright` (pre-commit).

Dodanie dostawcy stocku: funkcja wyszukiwania w `stock.PROVIDERS` + host plików w `stock.HOSTS` + klucz w Infisicalu
(most `~/infisical/infisical_bridge.py run --secrets <NAZWA> --`), potem `"provider"` w `style/grammar.json › broll`.
