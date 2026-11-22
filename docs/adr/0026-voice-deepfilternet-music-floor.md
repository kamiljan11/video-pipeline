# ADR-0026 — Głos przez DeepFilterNet, muzyka z podłogą pod głosem

Data: 2026-11-14 | Status: przyjęte (Kamil po fragmencie testowym: „muzyka tech chyba w tle nie gra”, „audio mikrofon … żeby był dźwięk jak studyjny”, „wybierz se najlepszy”) |
Przegląd: po pierwszym filmie z inną muzyką i po odsłuchu Kamila — czy zakres 14–28 dB i głos bez kompresora zostają (wynik do `style/NOTES_LOG.md`)

**Kontekst:** fragment longa 2026-11-04 (`fragment.py`, 245 s). Muzyka siedziała 48 dB pod głosem (ducking 0.004 / 8), czyli była
niesłyszalna; po podgłośnieniu (0.04 / 2.5) wracała w górę przy cichych słowach i zakryła jedno w 201 s (`words_check sound`).
Tor głosu to były same filtry ffmpeg: `highpass, afftdn, acompressor, loudnorm`.

**Decyzje:**
| # | decyzja | gdzie |
|---|---|---|
| 1 | Głos surowego cięcia przechodzi przez DeepFilterNet przed łańcuchem `audio`; łańcuch nie ma wtedy `afftdn` ani `acompressor` | `voice_clean.py`, klucz planu / EDL `"voice_clean": "dfn"`, `assemble.py`, `edl_guard.py` |
| 2 | Brak binarki = render staje z nazwaną ścieżką; nie ma cichego powrotu do nieoczyszczonego głosu | `voice_clean.clean` (`SystemExit`), `tests/test_voice_clean.py` |
| 3 | Ducking muzyki i SFX ma `mix` (0–1): podłoga, muzyka trzyma jeden poziom pod głośnym i cichym słowem | `assemble.py` (`sidechaincompress … mix=`), `edl_guard.duck_ok` |
| 4 | Bramka longa: mediana „głos minus podkład” pod mową w 14–28 dB | `music_check.py`, `run_v4.sh music_ok` |

**Pomiary (dowód wyboru):** dwie próbki 30 s nagrania 2026-11-04 (466–496 s i 900–930 s), ocena bez wzorca TorchAudio-SQUIM, PESQ:
surowy mikrofon 3,80 / 3,74; stary łańcuch 3,02 / 3,02; DeepFilterNet + kompresor ratio 3: 3,52 / 3,37; ratio 1,5: 3,69 / 3,63;
**DeepFilterNet bez kompresora 3,77 / 3,72**. Rozpiętość głośności (LRA) bez kompresora 2,4 / 3,5 LU wobec 2,2 / 3,4 LU, więc
kompresor niczego nie wyrównywał. Czas: 4,1 s na 30 s na CPU. Muzyka na ścieżkach fragmentu: 0.04 / 2.5 → mediana 22,7 dB,
3,3 % okien mowy z muzyką bliżej niż 10 dB; 0.004 / 8 / mix 0.8 → 25,5 dB, 0,8 %, w pauzach −29,9 dBFS. Całość:
`~/Dane/voice-test-2026-11-14/DECYZJA.md` (poza repo), skrót w nagłówku `voice_clean.py`.

**Odrzucone:** Resemble Enhance (PESQ 2,43, SI-SDR 12,9 dB: zmienia głos; ~28 min na 4 min filmu na CPU; venv 1,4 GB z przypiętym
torch 2.1.1); Resemble denoise (wynik jak DeepFilterNet, 3× wolniej, ten sam ciężki venv); bramka szumu po DeepFilterNet (PESQ bez
zmiany, SI-SDR niżej); zostawienie `afftdn` (sam obniżał wynik z 3,31 do 3,02); samo podgłośnienie muzyki bez podłogi (zakrywa ciche słowa).

**Zależność zewnętrzna:** `deep-filter` 0.5.6, statyczna binarka z wydania autora
(`github.com/Rikorose/DeepFilterNet/releases/tag/v0.5.6`, plik `deep-filter-0.5.6-x86_64-unknown-linux-musl`, MIT / Apache-2.0,
sha256 `70775e251eee44c0f2451a1e833326cf8bcbbe304d3e7cd12851e6fce72ef7da`). Miejsce: `~/.local/share/vp-voice/dfn/deep-filter`
albo `VP_DEEP_FILTER`. Instalacja na nowej maszynie: pobrać plik, `chmod +x`, porównać sha256. Bez sieci w czasie renderu.

**Koszt cykliczny:** 0 zł (lokalnie, bez API i subskrypcji); ~35 s CPU na 4 min filmu; 36 MB na dysku. Utrzymanie: wersja
przypięta, aktualizacja tylko po nowym pomiarze na tych samych próbkach.

**Ryzyka:** ocena SQUIM to estymata modelu, nie ucho — ostatecznie rozstrzyga odsłuch Kamila; zakres 14–28 dB ustawiony na jednym
filmie i jednym gatunku muzyki; binarka bez sumy kontrolnej od wydawcy (sha256 powyżej zapisane po pobraniu).

**Rollback:** usunąć `"voice_clean"` z planu i przywrócić stary łańcuch w `"audio"`; `music_duck` bez `mix` działa jak przed zmianą.
Kod bez klucza `voice_clean` zachowuje się jak przed ADR (testy `test_assemble_mix`).
