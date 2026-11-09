# 8 Producent shortów -> `plan_<clip>.json` dla każdego `make: true`

**Rubryka (ZASADY-KAMILA-SHORTY.md, REF-shorts-breakingbreach.md, shorts_sound.md)**
- `hook_text` na ekranie od 0 s (pierwsza zmiana obrazu <= 1 s); długość 30-55 s.
- Zmiana obrazu co 2-4 s (max 8 s bez zmiany): `layout` split / corner (`face_corner`, `face_box`), `web`, `meme`, sceny.
- `caption_pop: true`, `caption_case`, `caption_ahead`.
- Punch-in >= 3/min, ostatnie zdanie wraca do hooka (liczba albo rzeczownik z 1. zdania, `shorts.py` callback +1,5) LUB odpowiada na obietnicę tytułu (round 2 S6, Sinek 3/3).
- Upscale cropa: lanczos + lekkie wyostrzenie (`grade` unsharp), bez AI upscalera.
- `music_palette` ustawione.

- Sceny shorta rysuje motion designer (karta `motion-designer.md`): wyjście od sceny longa na tych samych słowach, przerysowanej na
  9:16 nad ramką twarzy, kawałki wchodzą na swoich słowach. Szablon „2-3 chipy na pustym płótnie” to nie scena (2026-11-09:
  36 takich scen w 18 shortach przeszło bramki; przerysowane od nowa). Zobacz stillsy (`stills.py plan_<clip>.json`) przed oddaniem.

**Gotowe gdy:** `film_check` short.* OK dla każdego klipu (w tym short.scenes = `gfx/scene_check.mjs` na scenach shorta).
Plan generowany skryptem po raz drugi zachowuje klucze innych ról (dźwięk: audio, master, music_*, sfx_*): przeczytaj stary plan i
nadpisz tylko swoje pola (2026-11-09: regeneracja 18 planów skasowała klucze dźwiękowca).
