# RUNBOOK

## LinkedIn: kolejka i timer (`linkedin.py`, ADR-0009, ADR-0010)

Wszystko na laptopie (`kamil-jan`); token `~/.config/linkedin/token.json`, stan `~/.local/state/vp-linkedin/`.

| sytuacja | co zrobić |
|---|---|
| Włączyć timer (decyzja Kamila) | `systemctl --user link ~/Dane/vp-linkedin/deploy/vp-linkedin-run-due.service ~/Dane/vp-linkedin/deploy/vp-linkedin-run-due.timer` potem `systemctl --user enable --now vp-linkedin-run-due.timer` |
| Wyłączyć | `systemctl --user disable --now vp-linkedin-run-due.timer` |
| Czy timer chodzi | `systemctl --user list-timers vp-linkedin-run-due.timer`; bez sesji tylko z lingering (`loginctl show-user $USER -p Linger`) |
| Logi | `journalctl --user -u vp-linkedin-run-due.service -n 100`; nieudane przebiegi: `systemctl --user --failed` |
| Co jest w kolejce | `python3 linkedin.py queue list` (stan: `waiting`, `due`, `done`, `late`, `stuck <stan>`) |
| `late` (laptop był wyłączony > 3 h) | post nie wyszedł; `queue remove <spec>`, potem `queue add <spec> --at "<nowy czas>" --approve <ten sam kod>` |
| `stuck unknown`/`stuck pending` | post mógł wyjść: sprawdź profil (Aktywność > Posty). Jest: wpisz `"state": "published"` i URL do `<dir>/linkedin.published.json`. Nie ma: skasuj ten plik; następny tik opublikuje |
| `N failed publish attempts` | przyczyna w journalu (`FAILED ...`); napraw (token, plik, treść), potem `queue remove` + `queue add` (zeruje licznik prób) |
| `approval code is X now, Y when queued` | plik zmienił się po akceptacji (np. ponowny render shorta): nowy dry run, nowe OK Kamila, `queue remove` + `queue add` z nowym kodem |
| Token wygasa (stop 3 dni przed) | `python3 ~/infisical/infisical_bridge.py run --secrets LINKEDIN_CLIENT_ID,LINKEDIN_CLIENT_SECRET -- python3 linkedin_auth.py` (Kamil klika „Zezwól”) |
| Pierwszy komentarz nie wyszedł (exit 1, `FAILED`/`UNKNOWN`) | `python3 linkedin.py comment <spec>` (przy `UNKNOWN` najpierw sprawdź pod postem, potem `--checked`) |
| Repo przeniesione / po merge | popraw ścieżkę w `deploy/vp-linkedin-run-due.service` (`WorkingDirectory`, `ExecStart`), `systemctl --user daemon-reload` |
