# 9 Pakowanie -> `out/youtube/*.md`, `thumbs.json`, `out/thumbnails/`

**Misja:** wszystko gotowe do wrzucenia ręką Kamila (nic nie publikujemy sami).

**Głos:** pisz według `style/voice.md` (rytm, jego frazy, `## Zakazane` sprawdza `post_check`) i słowami widzów z `style/audience-language.md`.

**YouTube long** `out/youtube/long.md`:
- `## Tytuły`: tabela `| wariant | kąt | tytuł | znaki | źródło |` A/B/C (do Test & Compare), <= 60 znaków, różne kąty:
  wynik / ciekawość / problem. Start = tytuł z niszy, który już działa (kolumna `źródło`: kanał + tytuł), potem nasz kąt.
- `## Fraza kluczowa`: jedna linia, co widz wpisuje w wyszukiwarkę; jej słowo w 3 pierwszych słowach każdego tytułu.
- Obietnica tytułu pada w pierwszych 30 s longa (>= 2 jego słowa treści słychać w otwarciu); nie pada -> zmień tytuł albo otwarcie.
- `## Opis`: 2 pierwsze linie = obietnica (widoczne przed „więcej”), potem linki, KamilJan.com.
- `## Rozdziały`: od `0:00`, z czasów EDL (nie ze źródła), >= 3, każdy >= 10 s.
- `## Tagi`, `## Przypięty komentarz`.

**Shorty** `out/youtube/shorts/<id>.md`: `## Tytuł`, `## Opis` (+ link do longa).

**Miniatury** (`node gfx/thumbs.mjs thumbs.json out/thumbnails`): >= 2 warianty longa (A/B, najlepiej 3), `big` <= 18 znaków,
różne klatki/emocje i różne słowa; okładka każdego shorta.

**Gotowe gdy:** `film_check --out` out.youtube, out.titles (`title_check.py`) i out.thumbs OK.
