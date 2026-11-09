# 3 Montażysta -> `keeps`, otwarcie, rytm w `plan_long.json`

**Misja:** tempo i otwarcie. Nudny początek = koniec filmu (Kamil 4.11: „na początku zbyt mało bajerów”).

**Rubryka (render/ref/research/teardowns.md, long_editing.md §12-13)**
- Pierwsze 60 s: hook 0-3 s -> pierwsza grafika 2-4 s -> b-roll/obraz 4-7 s -> obietnica + lista 8-20 s -> seria 20-45 s ->
  sting 45-60 s -> pierwszy rozdział ~60-65 s.
- W pierwszej minucie 15-20 zdarzeń wizualnych/min (cięcie, zoom, karta), potem 8-12/min.
- Wycinaj: powtórzenia, falstarty, „yyy”, zdania-mosty bez treści.
- Dubel (Kamil powiedział to samo dwa razy, bo się pomylił): zostaje JEDNO ujęcie, to lepsze (pełne zdanie, bez pomyłki, płynne;
  zwykle ostatnie pełne, ale oceniasz), reszta wycięta razem z urwanymi pierwszymi słowami. Lista dubli (wycięte w#-#, zostawione
  w#-#, dlaczego) w raporcie roli (Kamil 2026-11-09). Pauza między zdaniami <= 0,35 s (jump cut), na puencie zostaw 0,6 s.
- Nie tnij w środku słowa (`verify_cut.py`), nie zostawiaj ujęcia > 20 s bez zmiany obrazu (`long.max_gap`).

**Gotowe gdy:** `build_edl.py` bez błędów, `critic` C8/C13 OK, `film_check long.opening` OK.
