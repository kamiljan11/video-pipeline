# Wzorzec: memy i „pro” montaż shortów (rozbiór 2026-10-31)

Pełne rozbiory: `style/refs/2026-10-31-ufd-tech.md` (memy), `style/refs/2026-10-31-norbert-bodziony-taher-shabaan.md` (dowody, split,
skecze POV). Poprzedni wzorzec (karty-dowody, split): `style/REF-shorts-proof-cards.md`.

## Co mówią dane

| kanał | memy | co robi najlepiej |
|---|---|---|
| UFD Tech (0,3–1,5 mln wyśw.) | 21 pozycji w 7 filmach (~12 to memy sensu stricto), ~1 na 8–10 s, 0,5–5,8 s (mediana 1,7 s), bez dźwięku, zawsze pod konkretną frazę („or else” -> Arthur, „sunk cost” -> Teddy KGB, „Swiss” -> „I'm Switzerland”, „always watching” -> Roz) | co 5–12 s zmiana trybu: twarz <-> rozmyta twarz + karta; nigdy > 12 s bez nowego obrazu |
| Norbert Bodziony | brak klasycznych memów; znane symbole jako naklejki (logo, flaga) za głową | split dowód/twarz 80–90 % czasu, flash light-leak 0,25 s przy wejściu dowodu, licznik, marker na frazie |
| Taher Shabaan (FB) | brak | animowany panel u góry, twarz na dole, napis na szwie |

Skecze POV Norberta (2 osoby, shot/reverse-shot, napis „POV: …”) mają najwięcej wyświetleń w jego zestawie przy najprostszym montażu.

## Co już mamy (2026-10-31)

| mechanika | klucz / typ |
|---|---|
| mem pod frazę, karta u góry + twarz w boksie albo pełny kadr | `"type": "meme"` (`style/memes.json`, `memes.py add`) |
| dowód ze strony w szerokości telefonu, marker na cytacie | `"type": "web"`, `"canvas": "v"` |
| napisy jak mówione, słowo przed wypowiedzeniem szare, pop wejścia | `caption_case`, `caption_ahead`, `caption_pop` |
| punch-in na cięciu, licznik, whoosh na karcie, podkład pod głosem | `zoom_every_cut`, `count`, `CARD_WHOOSH`, `music_duck` |

## Kolejka (wpływ × łatwość, z rozbioru)

1. **Tryb „blur”**: rozmyta twarz pod wyśrodkowaną kartą (UFD, 6/7 filmów) jako trzeci `layout` karty 9:16.
2. **Flash light-leak 0,2–0,27 s** przy wejściu/wyjściu dowodu (Norbert: 2–6 na 30 s, nie na każde cięcie).
3. **Zoom-out na starcie** 1,20 -> 1,00 w 0,4 s (Norbert 2/3 explainerów).
4. **Naklejka marki za głową** (logo, flaga) na nazwie własnej; mamy maskę mówcy (`behind.py`).
5. **Klipy-memy wideo** (Teddy KGB, Dr. Evil): poza zakresem do decyzji Kamila (ryzyko roszczeń Content ID, ADR-0008).
6. **Mem nad tułowiem przy pełnej twarzy** (slot UFD y 840–1440): u nas twarz stoi niżej (`face_target_y` 0,52), slot zasłoniłby
   usta; wymaga innego kadru.
7. **Koniec bez planszy** (UFD 7/7, Norbert: mówione CTA): do porównania z naszą `end`.
