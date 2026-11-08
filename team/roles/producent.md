# 1 Producent / story editor -> `work/story.json`

**Misja:** zanim ktokolwiek tnie, wiadomo z czego film się składa: części, ich pierwsze słowo, obietnica, główna myśl każdej części.

**Wejście:** `work/*.lines.txt` (L# [t0-t1] w#-# tekst), `work/*.cw.json`.

**Artefakt** `story.json`:
```json
{"promise": "co widz dostanie (1 zdanie, padnie w 8-20 s)",
 "hook": {"word": 12, "text": "zdanie otwierające, które zostaje w filmie"},
 "parts": [{"id": "p1", "title": "Pomysł 1: …", "start_word": 543, "question": "pytanie, które ta część zadaje",
            "idea": "1 zdanie myśli", "visual": "jak to narysować (metafora, przykład z życia)", "payoff_word": 599}],
 "skip": {}}
```

**Rubryka**
- `start_word` = PIERWSZE słowo części (pytanie / zapowiedź), nie słowo, które ją nazywa na końcu. Film 2: „pierwszy pomysł” padał
  na końcu myśli -> rozdziały wchodziły za późno. Szukaj zdań typu „ale zanim…”, „i teraz…”, „druga rzecz…”.
- 3-7 części na 10-15 min (rozbiory: rozdział co 1,5-3 min).
- Hook: najmocniejsze zdanie z pierwszych 20 s albo cold open z najlepszego momentu (long_editing §12).
- `visual` jest obowiązkowe: to brief dla motion designera (Kamil: „najbardziej mi zależy na graficznym pokazywaniu pomysłów”).

**Gotowe gdy:** `film_check long.story` OK, każda część ma `visual`.

**Round 2 (2026-11-08), pola story.json, które sprawdza film_check**
- Bramka tematu (plan 1 2.8): long = 1 szukane narzędzie albo wynik (`## Fraza kluczowa` w long.md, out.titles); newsy idą do shortów i postów.
- Intro kończy zdanie-most = `start_word` części 1, część 1 do 90 s (L4, long.first_part_by); w 50 s pada liczba części + karta `list` z tyloma pozycjami (L3, long.roadmap).
- `cta_after_part: k` = jedno CTA ofertowe po części k (L6, long.cta_place); recap jako część `"kind": "recap"`/`"combine"` albo karta `"recap": true` <= 10 s (L7, long.recap).
- `action_word` w części = słowo, gdzie pada komenda/prompt do wypróbowania; karta kw/slide <= 2 s od niego (L23, long.action_word).
- plan: `"end": "platform"` + `"next_video"` = koniec bez naszej karty, następny film nazwany w ostatnich 30 s (L5, long.end); `"sources": {id: url}` dla każdego `verified_claims` (L20, out.sources).
