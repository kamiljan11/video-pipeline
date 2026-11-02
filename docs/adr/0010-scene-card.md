# ADR-0010: karta `scene`, schemat w stylu aplikacji z kamerą, twarz w kółku

Data: 2026-11-02 · Status: przyjęta (do oceny po pierwszym longu z nią)

## Kontekst
Long o Higher Mind w wersji 20-minutowej nagrywał się prawie 40 minut i był za długi do oglądania. Kamil wskazał wzór: film
AI LABS „EGM: Google's New Way To Use Claude Code Is Insane” (2026-10-25, 16 min, ok. 210 tys. wyświetleń w dniu rozbioru).
Rozbiór klatek co 6 s: brak twarzy, dwa tryby obrazu. (1) Schematy: prawie czarne tło, płaskie ciemne karty (okno, plik, czat,
lista z ptaszkami), szare kreski zamiast tekstu, którego nie trzeba czytać, dwa kolory marki, kamera przesuwa się i przybliża
między grupami. (2) Prawdziwe nagranie terminala i edytora z zaznaczonym fragmentem. Nowy obraz co kilka sekund.
Nasze karty `slide` i `float` umiały pokazać hasło albo kilka elementów obok mówcy, ale nie mechanizm krok po kroku.

## Decyzja
Nowy typ `scene` (gfx/scene_lib.mjs): biblioteka małych elementów (okno, plik, terminal, pigułka, ikona, osoba, czat, pieczątka,
napis, pasek, liczba, linia) na płótnie, każdy z czasem wejścia, plus kamera. Twarz zostaje: scena jest w `PIP`, więc
`assemble.py` kładzie kółko z twarzą w prawym dolnym rogu, tak jak przy `slide` i `web`. Kamera kadruje elementy po `id`;
rozmiary mierzy przeglądarka po ułożeniu (`sceneFit` w render.mjs), więc spec nie musi znać szerokości tekstu. Wszystko na
CSS i opóźnieniach, więc istniejące przewijanie klatek (`document.getAnimations()`) działa bez zmian.

## Konsekwencje
- Terminal pokazuje prawdziwy wynik polecenia, przepisany do speca. To nie jest nagranie ekranu: zmiana treści = zmiana speca.
  Prawdziwe nagranie ekranu (Kooha) jako tło karty to osobna decyzja (dekodowanie wideo klatka po klatce w Chrome).
- `"pip": false` na karcie z `PIP` wyłącza kółko z twarzą pod nią (build_edl.py); bez klucza wszystko jak dotąd.
- Panel trzyma własną kopię `CARD_WHOOSH`; do czasu zmiany w panelu podgląd w panelu nie da whoosha pod sceną.
- Brak metryki: ocena po pierwszym longu ze scenami (retencja w YouTube Studio w miejscach scen vs gadającej głowy).
