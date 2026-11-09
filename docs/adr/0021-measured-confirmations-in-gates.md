# ADR-0021 — Bramki potwierdzają flagę pomiarem (words_check sound, short.punch)

Data: 2026-11-08 | Status: przyjęte (Kamil: „sam autonomicznie decyduj”, „nic nie naprawione ... szukaj metody”) | Drzwi: dwukierunkowe |
Przegląd: po obejrzeniu przez Kamila longa i 18 shortów filmu 2026-11-04 — czy któreś słowo z WARN było naprawdę niesłyszalne

**Kontekst:** dwie bramki blokowały render z powodów, które pomiar obalał:
1. `words_check sound`: whisper na gotowym filmie nie słyszał słowa, które słyszał na cięciu. s02 „no” było 20,3 dB nad muzyką,
   a s04 słowa angielskie 24,5 dB nad muzyką. Głos był wyraźny, whisper się pomylił (mishear). Ten sam test pokazał też prawdziwy problem:
   long miał 28 cichych słów pod muzyką (duck 0,05, muzyka −10 dB). Po remiksie (duck 0,01, muzyka −16 dB) zostało 0 problemów.
2. `short.punch`: liczył punch-iny na minutę całego filmu. s09 ma 34 z 46 s pod kartami, a pod kartą/b-rollem punch nie powstaje
   (build_edl pomija tam emph), a s17 ma każde ujęcie z zmax 1,0 (głowa wypełnia kadr, ADR-0012).

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| głos vs muzyka | stemy głosu i podkładu z grafu `assemble.audio.args.json`; min. różnica dB w oknach mowy ≥ `MASK_DB` 10 = WARN (whisper się pomylił) | `words_check.confirm_audible` |
| ponowne słuchanie | < 10 dB: whisper tego samego krótkiego okna cięcia i filmu; WARN tylko gdy słowa wokół luki (2+2) są w oknie filmu, a okna są równe albo słowo jest w filmie | `words_check.reheard` |
| budżet | max `REHEAR_MAX` 6 ponownych słuchań na check (2 przebiegi whisper każde, timeout 600 s); reszta zostaje FAIL z powodem | `words_check.confirm_audible` |
| brak pomiaru | brak stemów / miejsca na osi / ffmpeg padł = FAIL „not measured”, nigdy cichy WARN | `words_check` |
| short.punch | `punches_per_face_min`: punch-iny poza kartami / czas twarzy bez kart w ujęciach z zmax > `PUNCH_ROOM` 1,08; brak zmax = ujęcie liczy się | `film_check.Film.punches_per_face_min` |
| mało twarzy | < `FACE_MIN_S` 10 s takiej twarzy = 99 z opisem „not judged” w raporcie (oceniają reguły kart) | jw. |

**Progi:** `MASK_DB` 10 = połowa najniższego zmierzonego mishearu (20,3 dB) i ponad poziomem, przy którym 28 słów longa przed remiksem
było niesłyszalnych. `PUNCH_ROOM` 1,08 = najmniejszy zoom, który widać jako punch (ADR-0012).

**Dlaczego stałe w kodzie, nie w `style/*.json`:** to kalibracja narzędzia pomiarowego, nie wybór stylu, który Kamil zmienia per film.
Zmiana progu wymaga nowego pomiaru i testu (`tests/test_word_tools.py`, `tests/test_timeline.py`). Wartość progu checklisty
(`short.punch` ≥ ...) zostaje w `style/checklist.json`.

**Odrzucone:** `skip` z powodem w planie (ukrywa prawdziwe problemy, jak 28 słów longa); obniżenie progu whispera na całym filmie
(przepuszcza prawdziwe zgubione słowa); liczenie punch-inów na minutę filmu (kara za karty, w których punch nie powstaje).
**Ryzyko:** WARN zamiast FAIL dla słowa, które człowiek też by przeoczył przy 10-20 dB. Kontrola: Kamil ogląda przed publikacją
(out_v4 zostaje lokalnie); każde WARN jest wypisane z czasem i dB.
**Metryka:** słowa z WARN, które Kamil uzna za niesłyszalne (cel 0).
