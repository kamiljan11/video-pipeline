# ADR-0012 — Punch-in może uciąć górę głowy (`punch_headroom`)

Data: 2026-11-04 | Status: proponowane (czeka na Kamila po obejrzeniu longa filmu 2 v2) | Drzwi: dwukierunkowe | Przegląd: po filmie 3

**Kontekst:** Kamil 4.11: „pominąłeś np. zoomy”; checklista `long.punch >= 2` na minutę. W filmie 2026-11-04 Kamil siedzi blisko
kamery: głowa z włosami zajmuje 73 % wysokości kadru. `face_track.py` trzymał w kadrze całą głowę z włosami (0,45 wysokości twarzy
nad nią), więc zoom mógł wynosić ~1,01 (mediana) i zostało 0,6 punch-inu na minutę.

**Opcje:**
| opcja | za | przeciw |
|---|---|---|
| A. bez zmian, `skip` `long.punch` z powodem | cała głowa zawsze w kadrze | Kamil prosił o zoomy; long stoi na twarzy |
| B. `punch_headroom: "face"`: zoom trzyma czoło-brodę (0,12 nad twarzą), może uciąć włosy | 2,1 punch-inu/min; tak tną profesjonalne kanały na zbliżeniach | ucięta góra głowy przy zbliżeniu |
| C. nagrywać dalej od kamery | najlepszy kadr | nie ratuje nagranego filmu |

**Decyzja (proponowana):** B jako klucz planu, domyślnie `"hair"` (stare filmy i shorty bez zmian), `"face"` tylko w planie, który go
ustawia (long filmu 2026-11-04). Na przyszłość C (uwaga do nagrań). Shorty: ZASADY-KAMILA-SHORTY (cała głowa z brodą w boksie) bez zmian.

**Konsekwencje:** Kamil ocenia zbliżenia w `out_v2/long`. NIE = klucz z planu wypada, `long.punch` dostaje `skip` z powodem (A).
