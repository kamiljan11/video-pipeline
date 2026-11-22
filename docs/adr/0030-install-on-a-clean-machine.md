# ADR-0030 — instalacja na czystej maszynie: przypięte pobrania z sha256, font w repo

Data: 2026-11-22 | Status: przyjęte | Drzwi: dwukierunkowe | Przegląd: 2027-02-22

**Kontekst:** repo ma być publiczne (ADR-0007), a obcy ma je postawić na czystym Ubuntu 24.04 z README. Kod zakładał
checkout w `/home/kamil-jan/video-pipeline`, font kart w `~/.local/share/fonts` autora i ręcznie ściągnięte modele.
apt w Ubuntu 24.04 ma ffmpeg 6.1, a render używa filtrów z 8.x.

**Decyzja:**
- Ścieżki liczone od pliku (`Path(__file__)`, `BASH_SOURCE`, `import.meta.url`); `run_v4.sh`/`run_whisper.sh` odmawiają ścieżki ze spacją.
- `install/ffmpeg.sh`: statyczny build GPL z FFmpeg-Builds, przypięty do buildu z końca miesiąca (dzienne są kasowane po ~2 tyg.),
  sha256 z `checksums.sha256` wydania, instalacja do `~/.local/bin` bez sudo, idempotentna i atomowa (kopia obok + `mv`).
- `install/fetch_models.sh`: whisper (Hugging Face), YuNet (opencv_zoo), face landmarker (MediaPipe); plik zostaje tylko z sha256
  z `install/models.sha256` (= sumy publikowane przez wydawców); `--check-urls` w CI łapie przeniesione pliki.
- Montserrat VF w `fonts/` (OFL, `fonts/OFL.txt`, blob = google/fonts); karty ładują go względną ścieżką, nie z systemu.
- `install/check.sh` mówi, czego brakuje, z komendą naprawy (także sandbox Chrome i `/dev/shm` w Dockerze).

**Odrzucone:**
- **PPA z ffmpeg 8:** prywatne PPA = czerwona flaga bezpieczeństwa; wersja zależy od opiekuna.
- **Dockerfile jako jedyna droga:** Chrome z sandboxem wymaga w Dockerze `seccomp=unconfined`; użytkownik desktopowy go nie potrzebuje.
- **Modele w repo (Git LFS):** ~1 GB, limity LFS na darmowym koncie.

**Konsekwencje:** wynik sprawdzony w kontenerze ubuntu:24.04 (użytkownik `tester`): `check.sh` = ready, testy zielone.
Upstream może zdjąć przypięty build albo przenieść model: wtedy CI (`--check-urls`, pobranie ffmpeg) robi się czerwone,
a naprawa = nowy pin + suma w jednym pliku.

**Koszt cykliczny:** ~0; przy czerwonym CI z powodu 404 jedna zmiana pinu (FFMPEG_RELEASE/TAR/SHA256 albo URL modelu).
