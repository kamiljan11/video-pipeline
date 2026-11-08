# 2 Fact-checker -> `verified_claims` w planach

**Misja:** żadna liczba, nazwa narzędzia ani cytat na ekranie nie jest zmyślona.

**Wejście:** story.json, transkrypt, `gfx_specs.json` (szkic).

**Rubryka**
- Każda liczba na karcie (`count`, `stat`, `kw` z cyfrą) ma źródło: słowa Kamila (w#) albo link. Bez źródła -> karta bez liczby.
- Nazwy produktów jak u producenta (Claude Code, GitHub, n8n), bez wymyślonych logo.
- Wpis: `"verified_claims": [{"card": "id", "claim": "100+ blizn", "source": "w1130-1134"}]`.

**Gotowe gdy:** `critic.py` C9 OK.
