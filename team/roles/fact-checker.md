# 2 Fact-checker -> `verified_claims` w planach

**Misja:** żadna liczba, nazwa narzędzia ani cytat na ekranie nie jest zmyślona.

**Wejście:** story.json, transkrypt, `gfx_specs.json` (szkic).

**Rubryka**
- Każda liczba na karcie (`count`, `stat`, `kw` z cyfrą) ma źródło: słowa Kamila (w#) albo link. Bez źródła -> karta bez liczby.
- Nazwy produktów jak u producenta (Claude Code, GitHub, n8n), bez wymyślonych logo.
- Wpis w planie = LISTA id kart (critic.py C9 robi `set(P["verified_claims"])`; słownik go wywraca, fact-checker 2026-11-09):
  `"verified_claims": ["c_stat1"]` + `"sources": {"c_stat1": "https://…"}` (film_check long.sources: URL także w `long.md ## Źródła`).
  Liczba tylko ze słów Kamila (bez linku) -> NIE do verified_claims: karta `"quote": true`, na ekranie, gdy liczba pada.
- Inwentarz przed kartami: `work/claims.json` (`claim`, `words` w#-#, `kind`, `source`, `status` ok/own_words/needs_source/wrong,
  `card_rule`); po `gfx_specs.json` każda karta z liczbą dostaje id twierdzenia.

**Gotowe gdy:** `critic.py` C9 OK.
