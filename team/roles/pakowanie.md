# 9 Pakowanie -> `out/youtube/*.md`, `thumbs.json`, `out/thumbnails/`

**Misja:** wszystko gotowe do wrzucenia ręką Kamila (nic nie publikujemy sami).

**Głos:** pisz według `style/voice.md` (rytm, jego frazy, `## Zakazane` sprawdza `post_check`) i słowami widzów z `style/audience-language.md`.

**YouTube long** `out/youtube/long.md`:
- `## Tytuły`: tabela `| wariant | kąt | tytuł | znaki | źródło |` A/B/C (do Test & Compare), <= 60 znaków, różne kąty:
  wynik / ciekawość / problem. WARN (`style/title_lint.json`, nie blokuje; dowód każdej listy w `_evidence`): < 35 znaków, brak markera
  obietnicy (cyfra + wynik / jak, od zera, kurs, od podstaw, krok po kroku, w N minut / adresat / ból), „Mój/Moje” bez wyniku i bez
  czasownika efektu (sprzedaje, zastąpił), tytuł-wydarzenie (vlog, Q&A, live, wywiad = temat na post/short), > 1 tytuł z `?`,
  prefiks serii („Odcinek 3:”, „Vlog:”; „Kurs:”/„Tutorial:” są OK), tag marki po `|`. Start = tytuł z niszy, który już działa (kolumna `źródło`: kanał + tytuł), potem nasz kąt.
- `## Fraza kluczowa`: jedna linia, co widz wpisuje w wyszukiwarkę; jej słowo w 3 pierwszych słowach każdego tytułu.
- Obietnica tytułu pada w pierwszych 30 s longa (>= 2 jego słowa treści słychać w otwarciu); nie pada -> zmień tytuł albo otwarcie.
- `## Opis` (`desc_check.py`, limity w `style/platform_limits.json`; 16 twórców, SYNTH2-yt-description): linia 1 = obietnica <= 110 znaków,
  linia 2 = 1 link z etykietą (artykuł lub oferta, KamilJan.com z `utm_`: `python3 utm.py <url> youtube long <film>`), potem 2-4 zdania,
  potem blok `Rozdziały:` W OPISIE (YouTube czyta rozdziały tylko z opisu): od `0:00`, z czasów EDL, >= 3, każdy >= 10 s, część 1
  najpóźniej w 90 s, <= 0,6 rozdz./min; potem zasoby i źródła; na końcu stopka z `style/brand.json` `description_footer`.
  Hashtagi: WARN > 3 (polscy twórcy 3-7), błąd > 7, nigdy w linii 1-2.
- `## Tagi` opcjonalne, <= 500 znaków.
- `## End screen`: który film / playlista (URL albo „playlista …”), ustawiane w Studio; ostatnie 5-20 s longa zostawia na to miejsce.
- `## Przypięty komentarz`: niepusty, <= 1 link, pytanie albo zasób.

**Shorty** `out/youtube/shorts/<id>.md`: `## Tytuł`, `## Opis`: 1-3 linie, <= 50 słów, teza shorta własnymi słowami (nie kopia tytułu),
potem `Pełny film: {{LONG_URL}}` (po publikacji longa: `python3 desc_check.py --fill-long <url longa> out`), 0-2 hashtagi, bez `#shorts`
(0/10 twórców), bez rozdziałów; `## Powiązany film` (long, ustawiany w Studio jako powiązany film).

**Miniatury** (`node gfx/thumbs.mjs thumbs.json out/thumbnails`): >= 2 warianty longa (A/B, najlepiej 3), `big` <= 18 znaków,
różne klatki/emocje i różne słowa; okładka każdego shorta. Bramki feedu: >= 1 wariant BEZ twarzy (liczba, schemat, ekran),
słowa miniatury dopowiadają tytuł (< 50 % wspólnych z każdym tytułem), `big` czytelne przy 320 px (OCR), żadna litera < 12 px
przy 320 (tag 48 px albo bez tagu), nic w prawym dolnym rogu (czas filmu), tekst okładki w y 220-1500.

**Gotowe gdy:** `film_check --out` out.youtube (`desc_check.py`), out.titles (`title_check.py`), out.thumbs i out.thumbs_read (`thumb_check.py`) OK.
