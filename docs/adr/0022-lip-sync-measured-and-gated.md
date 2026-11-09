# ADR-0022 — Głos na ustach: opóźnienie filtrów mierzone i odcinane, cięcia na siatce klatek, bramka lip_check

Data: 2026-11-09 | Status: przyjęte (Kamil: „dalej long ma opoznienie i to jeszcze wieksze”) | Drzwi: dwukierunkowe |
Przegląd: po teście klaśnięcia (offset kamera vs mikrofon w nagrywarce) i po obejrzeniu przez Kamila nowego longa filmu 2026-11-04

**Kontekst:** long filmu 2026-11-04 miał głos 46 ms za ustami (mediana 7 kawałków, max 65 ms). Przyczyny zmierzone:
afftdn 25 ms + trzy alimitery po 5 ms look-ahead (głos, miks, master) = +40 ms dźwięku; kawałki cięte `-ss in`, a klatki
nagrania leżą na `0,033 + k/30` = obraz do 33 ms przesunięty. Żadna bramka nie porównywała obrazu z dźwiękiem
(sync_check: dźwięk cięcia vs plan, av_check: pakiety głosu).

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| opóźnienie filtrów | mierzone sygnałem testowym (paczki tonów 300/1100 Hz), odcinane `atrim` z początku głosu; łańcuch jest danymi planu, więc pomiar, nie tabela | `av_latency.chain_ms`, `assemble.py` |
| limitery | `latency=1` (kompensacja look-ahead) w miksie i masterze | `assemble.py`, `master_audio.py` |
| cięcia | `-ss` tuż przed najbliższą klatką nagrania; nazwa cache segmentu zmienia się (`_g<t>`) tylko gdy cięcie się przesunęło | `timeline.snap_in`, `assemble.seek` |
| bramka | `lip_check` po sync_check: mediana > 20 ms albo kawałek > 45 ms = FAIL; 0 dopasowanych z kilku = FAIL; mniej niż 3 policzone albo brak kawałka bez karty = WARN; `LIP_CHECK=off` z wpisem w logu | `lip_check.py`, `run_v4.sh` |

**Progi:** Kamil zauważył opóźnienie przy medianie +46 ms (max 65 ms), więc kawałek > 45 ms = FAIL; mediana 20 ms = poniżej
tego z zapasem i powyżej błędu pomiaru ruchu obrazu (1 klatka = 33 ms, z interpolacją ~10 ms). Normy branżowe (ITU-R BT.1359,
EBU R37) nie zostały sprawdzone w źródle [NIEPEWNE]: zmiana progu = nowy pomiar + `tests/test_lip_sync.py`. Po fixie short s01: +8,9 ms.

**Odrzucone:** stała tabela opóźnień filtrów (starzeje się przy każdej zmianie łańcucha); usunięcie afftdn (szum wraca);
przesuwanie obrazu zamiast dźwięku (cięcia na słowach liczą się w czasie dźwięku).
**Ryzyko:** lip_check mierzy względem NAGRANIA, więc offset samej nagrywarki (kamera v4l2 MJPEG vs mikrofon pulse, osobne zegary)
jest dla niej niewidoczny. Kontrola: test klaśnięcia (otwarte). Zoom/crop obniża dopasowanie ruchu, wtedy kawałek nie liczy się.
**Koszt:** pomiar łańcucha ~1 s na film, lip_check ~20 s na longu (ffmpeg). Koszt cykliczny: 0 zł.
**Metryka:** desync mediana longa w `render.log` (cel |x| <= 20 ms) i uwagi Kamila o opóźnieniu (cel 0).
