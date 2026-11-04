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
