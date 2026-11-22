# RUNBOOK

## LinkedIn: kolejka i timer (`linkedin.py`, ADR-0009, ADR-0027)

Wszystko na laptopie (`kamil-jan`); token `~/.config/linkedin/token.json`, stan `~/.local/state/vp-linkedin/`.

| sytuacja | co zrobić |
|---|---|
| Włączyć timer (decyzja Kamila) | `systemctl --user link ~/Dane/video-pipeline/deploy/vp-linkedin-run-due.service ~/Dane/video-pipeline/deploy/vp-linkedin-run-due.timer ~/Dane/video-pipeline/deploy/vp-linkedin-failed.service` potem `systemctl --user enable --now vp-linkedin-run-due.timer` |
| Wyłączyć | `systemctl --user disable --now vp-linkedin-run-due.timer` |
| Czy timer chodzi | `systemctl --user list-timers vp-linkedin-run-due.timer`; bez sesji tylko z lingering (`loginctl show-user $USER -p Linger`) |
| Powiadomienie „LinkedIn: post nie wyszedł” | `OnFailure=` przebiegu z exit 1; przyczyna w logach, dalej wiersze niżej |
| Logi | `journalctl --user -u vp-linkedin-run-due.service -n 100`; nieudane przebiegi: `systemctl --user --failed` |
| Co jest w kolejce | `python3 linkedin.py queue list` (stan: `waiting`, `due`, `done`, `late`, `stuck <stan>`) |
| `late` (laptop był wyłączony > 3 h) | post nie wyszedł; `queue remove <spec>`, potem `queue add <spec> --at "<nowy czas>" --approve <ten sam kod>` |
| `stuck unknown`/`stuck pending` | post mógł wyjść: sprawdź profil (Aktywność > Posty). Jest: wpisz `"state": "published"` i URL do `<dir>/linkedin.published.json`. Nie ma: skasuj ten plik; następny tik opublikuje |
| `N failed publish attempts` | przyczyna w journalu (`FAILED ...`); napraw (token, plik, treść), potem `queue remove` + `queue add` (zeruje licznik prób) |
| `approval code is X now, Y when queued` | plik zmienił się po akceptacji (np. ponowny render shorta): nowy dry run, nowe OK Kamila, `queue remove` + `queue add` z nowym kodem |
| Token wygasa (stop 3 dni przed) | `python3 ~/infisical/infisical_bridge.py run --secrets LINKEDIN_CLIENT_ID,LINKEDIN_CLIENT_SECRET -- python3 linkedin_auth.py` (Kamil klika „Zezwól”) |
| Pierwszy komentarz nie wyszedł (exit 1, `FAILED`/`UNKNOWN`) | `python3 linkedin.py comment <spec>` (przy `UNKNOWN` najpierw sprawdź pod postem, potem `--checked`) |
| Repo przeniesione / po merge | popraw ścieżkę w `deploy/vp-linkedin-run-due.service` (`WorkingDirectory`, `ExecStart`), `systemctl --user daemon-reload` |

## Rodzaj materiału: solo albo rozmowa (`content_kind.py`, ADR-0032)

| sytuacja | co zrobić |
|---|---|
| `WARN content_kind: not clear ...` w `render.log` | film poszedł na regułach solo. Rozmowa dwóch osób -> `"podcast": true` w planie, jedna osoba -> `"podcast": false`, potem ponowny przebieg |
| `kind: ... was measured on another version of ...` | nagranie podmienione: `.venv/bin/python content_kind.py <work> <plan>` (nadpisze wpis) |
| `kind: ... is not valid JSON` | przenieś `<work>/content_kind.json` do `~/Dane/_to_delete/<data>/`, potem `content_kind.py` jak wyżej |
| `FAILED content_kind <film>` | przyczyna w `render.log` (ffmpeg bez klatki, zawieszony > 60 s, brak `src`); popraw plik albo wpisz `"podcast"` ręcznie (krok wtedy się pomija) |
| Co system uznał | `content_kind.json` -> `sources[<src>].kind`, `faces` (twarze na klatkę), `clear` |
