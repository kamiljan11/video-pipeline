# ADR-0005 — Tekst za postacią: maska mówcy z modelu RVM wycinana z karty (`behind.py`)

Data: 2026-10-24 | Status: przyjęte | Drzwi: dwukierunkowe (karta bez `"behind"` = zwykła karta; `matte/` można usunąć) | Przegląd: 2027-01-31

**Kontekst:** Kamil (poprawka #11 do filmu 2026-10-22) chce dużych słów „za mną”, za głową, gdy tłumaczy. Potrzebna maska
postaci na klatkach filmu. W pipeline nie było nic do segmentacji osoby (YuNet w `face_track.py` daje tylko prostokąt twarzy).

**Decyzja:**
- Maska z modelu **Robust Video Matting** (PeterL1n, praca ByteDance, WACV 2022), plik `rvm_resnet50_fp32.onnx` z release v1.0.0,
  uruchamiany przez **onnxruntime** (Microsoft) na CPU w osobnym venv `matte/.venv` (wersje: `matte/requirements.txt`).
  Sha256 pliku jest w `behind.py` i sprawdzany przy każdym uruchomieniu. ONNX to graf + wagi, bez wykonywania kodu przy wczytaniu.
- Maska jest **wypalana w kartę** (alfa karty × (1 − postać)), a nie składana w `assemble.py`. `assemble.py` i odtwarzacz panelu
  bez zmian nakładają `<id>.mov`. Klatki pod kartą `behind.py` liczy sam, z `vf_for` czytanego z `assemble.py`
  (jedno źródło kadrowania), więc wymaga `seg_exact` (bez niego klatki filmu rozjeżdżają się z czasem).
- Uruchamiają go `gfx/render.mjs` (zaraz po renderze, żeby panel od razu pokazał efekt) i `run_v4.sh` (przed `assemble.py`
  na EDL po poprawkach krytyka, tylko karty tego filmu). Przetworzony `.mov` niesie klucz w metadanych (`comment=behind:<klucz>`);
  plik bez niego = świeży render. Nie ma osobnego pliku stanu, a jedyny zapis to atomowe `replace`.

**Odrzucone alternatywy:**
- **MediaPipe Selfie Segmentation:** lżejszy, ale słabsze krawędzie włosów; RVM ma stan rekurencyjny (stabilna maska w czasie).
- **Model `.pth` + PyTorch:** ~1 GB zależności i pickle (wykonanie kodu przy wczytaniu); ONNX + onnxruntime ~50 MB.
- **Składanie maski w `assemble.py` (overlay karty, potem postać z maski na wierzch):** zmiana chronionego skryptu i drugi
  kod w odtwarzaczu panelu; wypalenie w kartę nie zmienia żadnego z nich.
- **Maska z gotowego filmu (po renderze):** wymaga pełnego renderu, a karty i napisy byłyby już w kadrze.

**Konsekwencje (koszt):**
- Licencja: kod repo RVM jest GPL-3.0; bierzemy tylko plik wag i własny kod. Filmy (wynik) nie podlegają licencji kodu.
- Ok. 0,1 s na klatkę 2560x1440 (CPU, wątki z `cpu_budget.heavy_threads()`, nice 10): karta 3 s ≈ 15 s. Pierwszy bieg
  `render.mjs` może liczyć na EDL sprzed poprawek krytyka; `run_v4.sh` liczy wtedy jeszcze raz (tylko gdy okno się zmieniło).
- Maska myli się na dłoni przed głową i na rzeczach w kadrze podobnych do postaci; wtedy karta bez `"behind"` albo inne miejsce.
- `matte/.venv` i model są poza gitem (jak whisper.cpp i YuNet); instrukcja w README › „Postawienie od zera”.

**Koszt cykliczny:** 0 zł (lokalnie, CPU).

**Kryterium przeglądu (2027-01-31):** zostaje, gdy co najmniej jeden opublikowany film ma kartę `"behind"`. Gdy żaden: usunąć
`behind.py`, `matte/` i oba wywołania.
