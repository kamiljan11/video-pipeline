# 9 Pakowanie -> `out/youtube/*.md`, `thumbs.json`, `out/thumbnails/`

**Misja:** wszystko gotowe do wrzucenia ręką Kamila (nic nie publikujemy sami).

**Głos:** pisz według `style/voice.md` (rytm, jego frazy, `## Zakazane` sprawdza `post_check`) i słowami widzów z `style/audience-language.md`.

**YouTube long** `out/youtube/long.md`:
- `## Tytuły`: tabela `| wariant | kąt | tytuł | znaki | źródło |` A/B/C (do Test & Compare), <= 60 znaków, różne kąty:
  wynik / ciekawość / problem. WARN (`style/title_lint.json`, nie blokuje): < 35 znaków, brak markera obietnicy (cyfra + wynik / jak, od zera,
  krok po kroku, w N minut / adresat / ból), „Mój/Moje” bez wyniku, liczba + newsy, prefiks serii („Tutorial:”), tag marki po `|`. Start = tytuł z niszy, który już działa (kolumna `źródło`: kanał + tytuł), potem nasz kąt.
- `## Fraza kluczowa`: jedna linia, co widz wpisuje w wyszukiwarkę; jej słowo w 3 pierwszych słowach każdego tytułu.
- Obietnica tytułu pada w pierwszych 30 s longa (>= 2 jego słowa treści słychać w otwarciu); nie pada -> zmień tytuł albo otwarcie.
- `## Opis`: 2 pierwsze linie = obietnica (widoczne przed „więcej”), potem linki, KamilJan.com.
- `## Rozdziały`: od `0:00`, z czasów EDL (nie ze źródła), >= 3, każdy >= 10 s.
- `## Tagi`, `## Przypięty komentarz`.

**Shorty** `out/youtube/shorts/<id>.md`: `## Tytuł`, `## Opis` (+ link do longa).

**Miniatury** (`node gfx/thumbs.mjs thumbs.json out/thumbnails`): >= 2 warianty longa (A/B, najlepiej 3), `big` <= 18 znaków,
różne klatki/emocje i różne słowa; okładka każdego shorta. Bramki feedu: >= 1 wariant BEZ twarzy (liczba, schemat, ekran),
słowa miniatury dopowiadają tytuł (< 50 % wspólnych z każdym tytułem), `big` czytelne przy 320 px (OCR), żadna litera < 12 px
przy 320 (tag 48 px albo bez tagu), nic w prawym dolnym rogu (czas filmu), tekst okładki w y 220-1500.

**Gotowe gdy:** `film_check --out` out.youtube, out.titles (`title_check.py`), out.thumbs i out.thumbs_read (`thumb_check.py`) OK.
