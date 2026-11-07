# 9 Pakowanie -> `out/youtube/*.md`, `thumbs.json`, `out/thumbnails/`

**Misja:** wszystko gotowe do wrzucenia ręką Kamila (nic nie publikujemy sami).

**Głos:** pisz według `style/voice.md` (rytm, jego frazy, `## Zakazane` sprawdza `post_check`) i słowami widzów z `style/audience-language.md`.

**YouTube long** `out/youtube/long.md`:
- `## Tytuły`: tabela A/B/C (do Test & Compare), <= 60 znaków, różne kąty: wynik / ciekawość / problem.
- `## Opis`: 2 pierwsze linie = obietnica (widoczne przed „więcej”), potem linki, KamilJan.com.
- `## Rozdziały`: od `0:00`, z czasów EDL (nie ze źródła), >= 3, każdy >= 10 s.
- `## Tagi`, `## Przypięty komentarz`.

**Shorty** `out/youtube/shorts/<id>.md`: `## Tytuł`, `## Opis` (+ link do longa).

**Miniatury** (`node gfx/thumbs.mjs thumbs.json out/thumbnails`): >= 2 warianty longa (A/B, najlepiej 3), `big` <= 18 znaków,
różne klatki/emocje i różne słowa; okładka każdego shorta.

**Gotowe gdy:** `film_check --out` out.youtube i out.thumbs OK.
