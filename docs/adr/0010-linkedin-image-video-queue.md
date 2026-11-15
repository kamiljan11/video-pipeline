# ADR-0010 — LinkedIn: posty z obrazem i z wideo oraz kolejka publikacji

Data: 2026-11-15 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: 2027-02-15

**Kontekst:** Kamil (2026-11-15): „jak planujesz shorty na yt to planuj je na linkedin” i „lecisz upload wszystkiego po
kolei poprawione”. Film 2 ma 12 postów z grafiką (`out/posts/*/linkedin.json` + `grafika.png`) i 18 shortów publikowanych na
YouTube codziennie o 17:00. `linkedin.py` (ADR-0009) umiał tylko post-dokument (PDF). LinkedIn API nie ma postów planowanych.

**Decyzja:**
1. Rodzaj posta wynika ze specu: `carousel` = dokument (bez zmian), `video: "<ścieżka>.mp4"` = wideo (Videos API:
   initializeUpload, PUT części w zakresach bajtów od LinkedIn, finalizeUpload z ETagami, czekanie na `AVAILABLE`), brak
   obu = obraz `grafika.png` obok specu (Images API; alt text z `alt_text` albo `grafika.txt`). Ten sam projekt bezpieczeństwa:
   kod akceptacji = skrót tekstu, tytułu/alt textu, komentarza i bajtów pliku; rekord przed pierwszym zapisem; `SEEN`; dry run domyślnie.
2. Kolejka = plik `~/.local/state/vp-linkedin/queue.jsonl` (czas Europe/Warsaw, ścieżka specu, kod akceptacji).
   `queue add` sprawdza kod offline; `run-due --publish` publikuje tylko pozycje, których czas minął, a kod wciąż pasuje do plików.
   Uruchamia go timer systemd użytkownika co 15 min (`deploy/`), który włącza Kamil.
3. Heurystyki tekstu `fold` i `link` są dla obrazu i wideo ostrzeżeniem w dry runie (Kamil decyduje), dla dokumentu zostają
   regułą. Powód: 12 gotowych postów ma celowy link z UTM w tekście, a 7 z nich ma pierwsze dwie linie dłuższe niż 210 znaków;
   to decyzja treści, nie błąd do zatrzymania automatu.

**Rozważone:** (a) zaplanowane zadanie Claude (Cowork/scheduled task) zamiast timera: odrzucone, klasyfikator uprawnień blokuje
wysyłki z zadań zaplanowanych i zadanie zużywa limit subskrypcji; timer to zero tokenów. (b) Planowanie natywne w UI LinkedIn:
ręczne, 18+12 pozycji. (c) cron: systemd daje `journalctl`, `Persistent` i blokadę czasu wykonania bez dodatkowych narzędzi.

**Ryzyka i zabezpieczenia:**
- Laptop wyłączony albo uśpiony (znany problem: sloty przepadają albo odpalają hurtem): jeden post na przebieg i pozycja spóźniona
  o więcej niż 3 h (`MAX_LATE_H`) nie wychodzi, tylko jest zgłaszana (exit 1, `systemctl --user --failed`). Lepiej pominąć niż wysłać
  serię starych postów rano.
- Zmiana pliku po akceptacji (np. ponowny render shorta): kod się zmienia, `run-due` nie publikuje i to zgłasza.
- Token `w_member_social` nie czyta `GET /rest/images` (dokumentacja Images API): obraz idzie bez sprawdzania statusu; zbyt wczesny
  post = odmowa 4xx, rekord zwolniony, ponowienie bezpieczne. Dla wideo 403 na odczycie statusu = czekanie 180 s (`BLIND_S`) i próba
  posta; wideo jeszcze w obróbce = odmowa 4xx, rekord zwolniony, kolejny tik timera ponawia. Nieznane: czy LinkedIn przyjmie post z wideo,
  którego obróbka później padnie (wtedy zostaje zepsuty post do ręcznego usunięcia). Sonda 2026-11-04 potwierdziła tylko initializeUpload.
- Przebieg przerwany (SIGTERM od systemd, `TimeoutStartSec=30min`): handler zamienia go w SystemExit, więc upload bez posta zwalnia rekord.
- `queue remove` w trakcie przebiegu: kolejka jest czytana ponownie tuż przed publikacją; usunięcie w trakcie samego uploadu już nie zatrzyma posta.
- Pozycja `late`/`stuck`/ze zmienionym kodem daje exit 1 w każdym tiku, dopóki Kamil nie zrobi `queue remove` (celowo widoczne w
  `systemctl --user --failed`); pozycje `done` zostają w pliku jako historia.
- Token wygasa ok. połowy grudnia 2026: `run-due` zatrzymuje się 3 dni przed z komendą odnowienia (jak `publish`).

**Konsekwencje:** pozycja w kolejce = zgoda Kamila na konkretny kod; usunięcie: `queue remove`. Rollback = revert commita,
`systemctl --user disable --now vp-linkedin-run-due.timer`; opublikowane posty usuwa się ręcznie na LinkedIn.

**Metryka:** jak ADR-0009 (`stats_7d` w `linkedin.published.json`), osobno per rodzaj (`kind`): dokument vs obraz vs wideo.
