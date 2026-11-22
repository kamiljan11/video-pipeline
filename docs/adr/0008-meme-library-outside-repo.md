# ADR-0008 — Memy w filmach: katalog w repo, obrazy poza nim

Data: 2026-10-31 | Status: przyjęte dla shortów (2026-10-31, Kamil akceptuje ryzyko praw do obrazów); mem w longu: otwarte (niżej) | Drzwi: dwukierunkowe | Przegląd: 2027-01-31

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
Uzupełnienie 2026-11-04 (Kamil: „memów nie ma”): karta działa też w 16:9 (obraz na lewo od PiP z twarzą) i w 9:16 w układzie
`corner` (Kamil w kółku w rogu). Źródło obrazów i zasady (bez dźwięku, krótko, nasz tekst) bez zmian.
**Otwarte, decyzja Kamila:** akceptacja ryzyka z 2026-10-31 dotyczyła shortów. Mem w longu (kanał główny, monetyzacja) to szersze
ryzyko roszczenia; checklista wymaga `long.memes >= 3`. Do jego decyzji po obejrzeniu filmu 2 v2 (lokalnie, nic nie wysłane):
TAK = wpis tutaj ze statusem i datą; NIE = w planie longa `"skip": {"long.memes": "<powód>"}` i bez kart `meme` w jego `gfx`
(skrypt planu filmu w `render/montaz/<data>/work/`), tak samo jak NIE w ADR-0012.

**Ryzyko (zaakceptowane przez Kamila 2026-10-31; regulaminu imgflip nie sprawdzano):** memy z kadrów filmowych mogą dostać roszczenie na YouTube (Content ID łapie głównie klipy z dźwiękiem; statyczny obraz
rzadziej, ale nie zero). Dlatego: tylko obrazy, bez dźwięku, krótko (2–3,5 s), z naszym tekstem (transformacja, komentarz). Klipy
wideo (np. reakcje z filmów) świadomie poza zakresem; wrócić, jeśli Kamil zaakceptuje ryzyko roszczeń.

**Uzupełnienie 2026-11-05, gify zwierząt (Kamil: „moje OK daje ci”):** dozwolone krótkie gify kotów i innych zwierząt jako
naklejka obok mówiącego: do 2 s, bez dźwięku, bez napisu. Nie wolno brać wycinków z telewizji ani filmów: tam jest realne ryzyko
roszczeń. Najpierw Pexels/Pixabay (licencja do użytku komercyjnego, klucz Pexels już jest), dopiero potem gif amatorski. Każdy gif
ma zapisane źródło, żeby przy roszczeniu dało się podmienić jeden klip i zrenderować film od nowa. Ryzyko, które Kamil przyjął:
popularne filmiki zwierząt bywają w Content ID agencji licencyjnych (np. Jukin Media). Skutek to roszczenie (przychód albo blokada
w części krajów), a nie ban kanału. Narzędzie do gifów: do zbudowania (runda poprawek filmu 2).

**Uzupełnienie 2026-11-07, gify od zera (Kamil: „możesz tworzyć gify od zera, dodaj to do logiki”):** domyślne źródło
animowanej naklejki to nasz własny rysunek: `gfx/toons/<nazwa>.svg` (wektor + same keyframes CSS), karta `sticker` z polem
`"toon"` zamiast `"meme"` (`gfx/render.mjs` toonSticker). Zero licencji i zero dopasowania w Content ID, styl spójny z
planowanymi scenami rysowanymi (`docs/designs/2026-11-05-visual-upgrade.md`), koszt 0 zł. Plik toona to tylko rysunek i CSS:
skrypt, obsługa zdarzeń, foreignObject i link na zewnątrz = nazwany błąd. Rozważone: (a) klip z fal.ai (obraz -> wideo, ok.
0,015-0,07 USD/s wg porównań z 2026-11, ceny niezweryfikowane na fal.ai) + wycięcie tła, dla realistycznych memów, płatne,
do decyzji Kamila; (b) Wan-Alpha (wideo z kanałem alfa, otwarte wagi 14B) za ciężkie na laptop; (c) Lottie pisane przez
model (diffusionstudio/lottie) to nowa zależność, a SVG + CSS w Chrome już mamy. Kolejność: toon, potem Pexels/Pixabay, potem gif
amatorski z zapisanym źródłem.

**Konsekwencje:** szablon spoza top 100 imgflip nie da się pobrać `memes.py` (nazwany błąd); wtedy obraz można położyć ręcznie
w `render/memes/` z własnym `<slug>.json` (ten sam format).

**Koszt cykliczny:** 0 zł (API imgflip bez klucza, render lokalnie).

**Wykonanie / rollback:** klucze planu opt-in (`meme` w `gfx_specs`, `caption_pop`); bez nich short renderuje się jak przed zmianą.
Rollback = usunąć karty `meme` z planu (kod może zostać) albo revert commita; `render/memes/` można skasować bez skutków dla repo.

**Metryka:** brak automatycznej. Ręcznie: retencja v3 (z memami) vs poprzednia wersja tego samego shorta w YouTube Studio po 7 dniach,
jeśli Kamil wrzuci obie. Bez tego porównania decyzja opiera się na rozbiorze referencji, nie na danych z kanału.
