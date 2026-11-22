# ADR-0029 — gitleaks: przejrzane fałszywe alarmy jako dokładne odciski commitów

Data: 2026-11-17 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: 2027-02-17

**Kontekst:** PR #11 (synchronizacja `main` z pracą z 31.10–15.11) ma czerwony check `secrets`. Gitleaks skanuje całą historię
i zgłasza 5 trafień w 5 commitach. Wszystkie są fałszywe: nazwy kroków Videos API LinkedIn w ADR o kolejce LinkedIn (wtedy `0010`, dziś ADR-0027; `linkedin-client-id`),
wiersz tabeli „sound/picture effects” w dokumencie projektowym oraz syntetyczny token `tok-SECRET-123` w `tests/test_article.py`
(`generic-api-key`). Bramka zakazywała `.gitleaksignore` w ogóle, a poprawka pliku w HEAD nie usuwa trafień ze starszych commitów.

**Decyzja:** `.gitleaksignore` jest dozwolony wyłącznie jako lista pełnych odcisków `sha:ścieżka:reguła:linia`. CI odrzuca
każdą inną linię (poza komentarzem i pustą) oraz SHA, którego nie ma w repo, i wypisuje ignorowane pozycje w logu.
`.gitleaks.toml` pozostaje zakazany (mógłby wyłączyć reguły albo zrobić allowlistę po ścieżce lub wzorcu).

**Rozważone:** (a) przepisanie historii (`git filter-repo --replace-text`): zmienia SHA ok. 270 commitów i 9 gałęzi, wymaga
force-push i rozjeżdża worktree; odrzucone, koszt nieproporcjonalny do fałszywego alarmu. (b) Skan tylko drzewa HEAD
(`gitleaks dir`): przestaje łapać sekret dodany i usunięty w tym samym PR; odrzucone. (c) Odcisk bez commita (`ścieżka:reguła:linia`):
ukrywa trafienie we wszystkich przyszłych commitach; zakazany przez CI.

**Ryzyka i zabezpieczenia:** ktoś (albo agent) może w jednym PR dodać prawdziwy klucz i jego odcisk; sprawdzenie formatu tego
nie odróżni (recenzja security 2026-11-17). Dlatego PR, który zmienia `.gitleaksignore`, przechodzi `secrets` dopiero z etykietą
`gl-ok-<pełny sha bloba .gitleaksignore, 40 hex>` (`git rev-parse HEAD:.gitleaksignore`; 46 znaków, limit GitHuba 50; skrót 8 hex dał się podrobić dopisaniem komentarza w 32 s), nakładaną przez Kamila po sprawdzeniu każdego wpisu (workflow słucha też `labeled`/`unlabeled`). Etykieta nazywa treść, którą Kamil przeczytał: każda późniejsza zmiana pliku daje inny blob, więc żadne zdarzenie PR (push, pusty push, inna etykieta, reopen) nie zazieleni `secrets` bez nowej etykiety; bezpośredni push na `main` omija ten krok (zostaje sprawdzenie formatu), dlatego `main` przyjmuje zmiany tylko przez PR (pg-review 2026-11-22: etykieta bez treści dała się obejść drugim pushem). Granica: etykietę może nałożyć każdy z prawem do etykiet; agenci jej nie nakładają (blokada auto-mode). **Koszt cykliczny:** każda zmiana `.gitleaksignore` = Kamil czyta wpisy i nakłada nową etykietę (zwykle 0-1 razy na kwartał).
Lista jest wypisywana w logu CI. Odcisk dotyczy jednego commita i jednej linii: nowy sekret w innym commicie i tak zostanie
zgłoszony. Gitleaks pomija też linie z jego komentarzem wyłączającym w treści; CI odrzuca taki komentarz w całej historii
(dotąd 0 wystąpień). Nowe dane testowe nie powinny wyglądać jak klucze (np. `fake-token`), żeby lista nie rosła.
