# ADR-0008 — Memy w shortach: katalog w repo, obrazy poza nim

Data: 2026-10-31 | Status: przyjęte (2026-10-31, Kamil akceptuje ryzyko praw do obrazów) | Drzwi: dwukierunkowe | Przegląd: 2027-01-31

**Kontekst:** Kamil (2026-10-31): „korzystaj z wiekcej ilosci pro mozliwosci edycyjnych (…) lubie szczegolnie jak korzystaja z
znanych memow”. Rozbiór 7 shortów UFD Tech: 21 wstawek-obrazków (z tego ~12 to memy w ścisłym sensie), ~1 na 8–10 s, 0,5–5,8 s, zawsze pod konkretną frazę, bez dźwięku.
Memy to cudze obrazy (kadry z filmów, zdjęcia stockowe), a repo jest publiczne (ADR-0007).

**Kryteria:** (1) mem dobiera się w planie jak każdą kartę (dane, nie kod); (2) zero cudzych obrazów w publicznym repo;
(3) zero kosztów i kluczy; (4) pobieranie bez ryzyka dla laptopa.

| Kryterium (waga %) | A: obrazy w repo | B: katalog w repo, obrazy w `render/memes/` (pobiera `memes.py`) | C: Kamil wrzuca pliki ręcznie | komentarz |
|---|---|---|---|---|
| Dane, nie kod (30) | 4 | 5 | 3 | B i C: spec `{"meme": slug, "text": [...]}` |
| Nic cudzego w publicznym repo (35) | 1 | 5 | 5 | `render/` jest w `.gitignore` |
| Koszt (10) | 5 | 5 | 5 | API imgflip `get_memes` publiczne, bez klucza |
| Bezpieczeństwo pobierania (25) | 3 | 4 | 3 | B: tylko `https://i.imgflip.com`, tylko JPEG/PNG po bajtach, ≤ 5 MB; nic się nie wykonuje |
| **Suma** | 2,8 | 4,8 | 3,9 | |

**Decyzja:** B. `style/memes.json` = id szablonu imgflip + nasze pola tekstu; `memes.py add <slug>` zapisuje obraz i `<slug>.json`
(z URL-em źródła) do `render/memes/`. Karta `meme` tylko w 9:16, w układzie `split`/`full` kart `web` (ta sama ścieżka twarzy w boksie).

**Ryzyko (zaakceptowane przez Kamila 2026-10-31; regulaminu imgflip nie sprawdzano):** memy z kadrów filmowych mogą dostać roszczenie na YouTube (Content ID łapie głównie klipy z dźwiękiem; statyczny obraz
rzadziej, ale nie zero). Dlatego: tylko obrazy, bez dźwięku, krótko (2–3,5 s), z naszym tekstem (transformacja, komentarz). Klipy
wideo (np. reakcje z filmów) świadomie poza zakresem; wrócić, jeśli Kamil zaakceptuje ryzyko roszczeń.

**Konsekwencje:** szablon spoza top 100 imgflip nie da się pobrać `memes.py` (nazwany błąd); wtedy obraz można położyć ręcznie
w `render/memes/` z własnym `<slug>.json` (ten sam format).

**Koszt cykliczny:** 0 zł (API imgflip bez klucza, render lokalnie).

**Wykonanie / rollback:** klucze planu opt-in (`meme` w `gfx_specs`, `caption_pop`); bez nich short renderuje się jak przed zmianą.
Rollback = usunąć karty `meme` z planu (kod może zostać) albo revert commita; `render/memes/` można skasować bez skutków dla repo.

**Metryka:** brak automatycznej. Ręcznie: retencja v3 (z memami) vs poprzednia wersja tego samego shorta w YouTube Studio po 7 dniach,
jeśli Kamil wrzuci obie. Bez tego porównania decyzja opiera się na rozbiorze referencji, nie na danych z kanału.
