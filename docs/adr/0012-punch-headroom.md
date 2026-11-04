# ADR-0012 — Punch-in może uciąć górę głowy (`punch_headroom`)

Data: 2026-11-04 | Status: proponowane (czeka na Kamila po obejrzeniu longa filmu 2 v2) | Drzwi: dwukierunkowe | Przegląd: 2026-12-31 (albo przy filmie 3, co pierwsze)

**Kontekst:** Kamil 4.11: „pominąłeś np. zoomy”; checklista `long.punch >= 2` na minutę. W filmie 2026-11-04 Kamil siedzi blisko
kamery: głowa z włosami zajmuje 73 % wysokości kadru. `face_track.py` trzymał w kadrze całą głowę z włosami (0,45 wysokości twarzy
nad nią), więc zoom mógł wynosić ~1,01 (mediana) i zostało 0,6 punch-inu na minutę.

**Opcje:**
| opcja | za | przeciw |
|---|---|---|
| A. bez zmian, `skip` `long.punch` z powodem | cała głowa zawsze w kadrze | Kamil prosił o zoomy; long stoi na twarzy |
| B. `punch_headroom: "face"`: zoom trzyma czoło-brodę (0,12 nad twarzą), może uciąć włosy | 2,06 punch-inu/min (pomiar niżej); tak tną profesjonalne kanały na zbliżeniach | ucięta góra głowy przy zbliżeniu |
| C. nagrywać dalej od kamery | najlepszy kadr | nie ratuje nagranego filmu |

**Decyzja (proponowana):** B jako klucz planu, domyślnie `"hair"` (stare filmy i shorty bez zmian), `"face"` tylko w planie, który go
ustawia (long filmu 2026-11-04). Na przyszłość C (uwaga do nagrań). Shorty: ZASADY-KAMILA-SHORTY (cała głowa z brodą w boksie) bez zmian.

**Konsekwencje:** Kamil ocenia zbliżenia w `out_v2/long`. TAK = status „przyjęte” z datą w nagłówku. NIE = klucz z planu wypada,
`long.punch` dostaje `skip` z powodem (A).

**Pomiar** (laptop, 2026-11-04, film `render/montaz/2026-11-04/work`): `face_track.py edl_long.json`, potem
`film_check.py . long` (`long.punch` liczy zoomy po przycięciu): `"hair"` 0,61/min (mediana `zmax` 1,01), `"face"` 2,06/min
(mediana `zmax` 1,48; 3 zoomy przycięte zamiast 53). Głowa z włosami = `head` y 0,04..0,77 (mediana) w `edl_long.json`.
