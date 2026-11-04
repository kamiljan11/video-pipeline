# ADR-0009 — Posty na LinkedIn: dokument (karuzela PDF) przez oficjalne API

Data: 2026-11-04 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: 2027-02-04

**Kontekst:** Kamil (2026-11-04): system obok shortów i longów ma robić posty na LinkedIn; „decyduj to co najpopularniejsze i
publikuj przez api”. Na profilu kamiljan11 działa już publikacja przez API (toRzeszów, od 16.10.2026): aplikacja LinkedIn
265006181, produkt Share on LinkedIn, token `~/.config/linkedin/token.json` (scope `w_member_social`, 60 dni) z
`~/Documents/toRzeszow/skrypty/linkedin_auth.py`. Sonda 2026-11-04 na tym tokenie: `POST /rest/{documents,images,videos}?action=initializeUpload`
z autorem `urn:li:person:…` = 200 dla wszystkich trzech (LinkedIn-Version 202609), więc format nie jest ograniczony dostępem.

**Kryteria:** (1) format o najwyższym zaangażowaniu; (2) materiał z tego, co pipeline już ma (nagranie, transkrypcja, motyw);
(3) zero kosztów i płatnego API (tekst pisze sesja Claude Code z subskrypcji, jak opisy YouTube); (4) publikacja bez klikania,
ale bez ryzyka podwójnego posta.

| Kryterium (waga %) | A: tekst + obraz | B: wideo 4:5 | C: dokument (karuzela PDF) | komentarz |
|---|---|---|---|---|
| Zaangażowanie (40) | 2 | 3 | 5 | Socialinsider 2026: dokument 7,0 %, multi-image 6,45–6,9 %, wideo 5,6 %, obraz 4,85 %, tekst 4,0 % |
| Z istniejącego materiału (25) | 5 | 3 | 4 | C: slajdy z myśli z nagrania, render tym samym Chrome i motywem co karty |
| Koszt budowy (15) | 5 | 3 | 3 | B: nowy kadr i render całego klipu |
| Przejmowalność (20) | 5 | 3 | 4 | C: jeden szablon HTML, jedna komenda |
| **Suma** | 3,8 | 3,0 | 4,25 | |

**Decyzja:** C. `<dir>/linkedin.json` (tekst, hashtagi, pierwszy komentarz, slajdy) -> `linkedin.py check` (reguły z
`style/linkedin.json`) -> `linkedin.py render` (`gfx/carousel.mjs`, strona 1080x1350 na slajd) -> `linkedin.py publish`
(dry run) -> `--publish` (Documents API + Posts API + pierwszy komentarz z linkiem do filmu). Tekst po polsku (ten sam
odbiorca co kanał; dotychczasowe posty na profilu też są po polsku); zasady pisania: `style/LINKEDIN.md`.

**Dlaczego nie A/B:** A ma najmniejsze zaangażowanie w każdym zestawieniu; B dubluje short (9:16 można wrzucić ręcznie już dziś).
Ordinal (215 tys. postów) stawia multi-image przed PDF; dokument wybrany, bo wygrywa w 3 z 4 zestawień (Socialinsider, Buffer,
AuthoredUp) i nie wymaga cięcia obrazów. Do sprawdzenia metryką niżej.
Źródła (2026-11-04): socialinsider.io/social-media-benchmarks/linkedin, socialmediatoday.com (raport o postach-dokumentach),
tryordinal.com/blog/carousel-posts. Liczby to dane stron firmowych i różne metryki: kierunek, nie prognoza dla tego profilu.

**Ryzyko:** posty z API na tym profilu miały 15 i 23 wyświetlenia vs 52 dla ręcznego (toRzeszów, 16 vs 01.10; inny temat i dzień,
więc to sygnał, nie dowód kary za API). Token wygasa co 60 dni: `linkedin.py` zatrzymuje się 3 dni przed i podaje komendę odnowienia.
`LinkedIn-Version` jest wycofywana po ok. roku: stała `VERSION` w `linkedin.py`.

**Konsekwencje:** `linkedin.published.json` obok specu blokuje drugą publikację (świadome ponowienie = usunąć plik). Pierwszy
komentarz jest po poście; jego błąd nie cofa posta (zapis + exit 1). Token i `linkedin_auth.py` dzielimy z zadaniem toRzeszów
(jeden token na profil; odnowienie dotyczy obu).

**Koszt cykliczny:** 0 zł (API LinkedIn bez opłat, render lokalnie).

**Wykonanie / rollback:** nowe pliki (`linkedin.py`, `gfx/carousel*.{mjs,html}`, `style/linkedin.json`, `style/LINKEDIN.md`), nic w
istniejącym pipeline się nie zmienia. Rollback = revert commita; opublikowany post usuwa się na LinkedIn ręcznie.

**Metryka:** wyświetlenia i reakcje posta-dokumentu po 7 dniach vs mediana ostatnich 5 postów profilu (karta „Analytics” posta).
Gorzej 2 razy z rzędu = wrócić do tej decyzji (multi-image albo ręczna publikacja).
