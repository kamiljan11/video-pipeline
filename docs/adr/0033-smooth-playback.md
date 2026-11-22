# ADR-0033 — Płynność obrazu: mocniejsze kodowanie podglądu i bramka smooth_check, bez przekodowania źródła do CFR

Data: 2026-11-22 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: po pełnym renderze podcastu Dworak

**Kontekst:** Kamil (U12): „raz na zawsze naprawic problem klatkowania co pare sekund video”. Pomiary na podglądzie dry3
(`smooth_check.py`, różnica sąsiednich klatek w 40x22 szarości):
- źródło (S25 Ultra, VFR): 0–300 s = 60 fps z 48 pojedynczymi zgubionymi klatkami, od 300,1 s do końca = 30 fps (4 nierówności);
- podgląd (ultrafast crf 30): co 8,33 s (keyint 250) klatka kluczowa zmienia obraz 2,81x bardziej niż klatki obok;
- 71 podwojonych klatek, wszystkie wewnątrz kart-scen (animacja karty, nie wideo);
- zgubiona klatka źródła + `fps=30` = jedna klatka przesunięta o ±16 ms (np. 4,707 s), tylko w pierwszych 5 min.

**Decyzja:**
1. Podgląd: segmenty `ultrafast crf 20`, wyjście `ultrafast crf 18` (puls 1,60x; finał medium crf 18 1,36x), ta sama szybkość.
2. `smooth_check.py` po każdym renderze w `run_v4.sh` (po `av_check`): exit 1, gdy puls > 1,8x, podwojonych klatek > 1/min
   albo czasy klatek nierówne (> 1 ms od 1/fps). Film z błędem nie trafia do `out/`.
3. Bez przekodowania nagrania do CFR na wejściu: `fps=30` w `assemble.py` już daje CFR na wyjściu, a zgubionej przez
   telefon klatki nie odtworzy żadne przekodowanie (zostaje dziura albo duplikat). Koszt: ~1 h i ~30 GB na 28 GB pliku 4K
   przy zysku ±16 ms na 48 klatkach.

**Odrzucone:** interpolacja ruchu (`minterpolate`) w miejscach zgubionych klatek: artefakty na twarzy, wolne; krótszy GOP
(keyint 60): puls częstszy, nie mniejszy (zmierzone 2,91x).

**Rollback:** wartości `SEG_ENC`/`OUT_ENC` w `assemble.py`; krok `smooth_check` w `run_v4.sh` (jedna linia).
