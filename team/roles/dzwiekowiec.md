# 6 Dźwiękowiec -> `music_palette`, `music_moods`, `sfx_style`, `sfx`

**Misja:** każdy film ma własną muzykę, a ta zmienia się z częściami (Kamil 4.11: „co filmik nowa muzyczka”).

**Rubryka (shorts_sound.md, long_editing.md)**
- `music_palette: {name, key}` z `music/gen_music.py` PALETTES; para (name, key) inna niż w ostatnim filmie
  (`render/music_ledger.json`; film_check odrzuca powtórkę).
- `music_moods` >= 3, zmiana na każdym rozdziale (tension / story / upbeat / resolve / drop).
- Muzyka 18-24 dB pod głosem; cisza 0,5-1 s przed puentą.
- `sfx_style: "v2"`: dźwięk wg typu ruchu (whoosh przy rozdziale, klik przy kursorze, pop przy słowie); max 1 SFX na 2 s.
- Shorty: własna paleta (inna niż longa albo inna tonacja), mocniejsza perkusja.

**Gotowe gdy:** `film_check` long.music_palette, long.music_moods, long.sfx, short.music_palette OK.
