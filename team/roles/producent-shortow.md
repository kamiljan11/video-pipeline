# 8 Producent shortów -> `plan_<clip>.json` dla każdego `make: true`

**Rubryka (ZASADY-KAMILA-SHORTY.md, REF-shorts-breakingbreach.md, shorts_sound.md)**
- `hook_text` na ekranie od 0 s (pierwsza zmiana obrazu <= 1 s); długość 30-55 s.
- Zmiana obrazu co 2-4 s (max 8 s bez zmiany): `layout` split / corner (`face_corner`, `face_box`), `web`, `meme`, sceny.
- `caption_pop: true`, `caption_case`, `caption_ahead`.
- Punch-in >= 3/min, ostatnie zdanie wraca do hooka (pętla).
- Upscale cropa: lanczos + lekkie wyostrzenie (`grade` unsharp), bez AI upscalera.
- `music_palette` ustawione.

**Gotowe gdy:** `film_check` short.* OK dla każdego klipu.
