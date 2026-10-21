# Panel montażowy (spec dla Claude Code + PG)

Cel: lokalny panel (Linux, przeglądarka, localhost), w którym Kamil Jan widzi oś czasu filmu wygenerowanego przez pipeline i może podciągnąć każdy element bez dotykania kodu, a potem jednym klikiem przerenderować.

## Źródło prawdy
Panel NIE jest nowym edytorem wideo. Edytuje pliki, które pipeline już ma:
- `work/plan_<nazwa>.json`: keeps (zakresy słów), emph (najazdy), drift, zooms, hook_text, tail, progress, verified_claims
- `work/gfx_specs.json`: treść i czas grafik (kw, list, lower, chap, cta, slide, end), ikony
- `work/edl_<nazwa>.json`: wynik `build_edl.py` + `face_track.py` (segmenty, zoomy, overlaye, face, zmax). Tylko do odczytu w panelu
- `work/2026-…cw.json`: słowa z czasami (transkrypcja)
Zmiana w panelu → zapis planu/specs → `build_edl.py` → `face_track.py` → `critic.py` → podgląd.

## Widoki
1. **Oś czasu** (ścieżki): V1 segmenty z kolorem zoomu (statyczny / drift / najazd), V2 grafiki, V3 slajdy+PiP, A1 głos (waveform), A2 muzyka, A3 SFX, znaczniki krytyka (C1-C9) na osi.
2. **Transkrypcja** obok osi: tekst słowo po słowie, wycięte przekreślone. Klik słowa = przywróć/wytnij (edycja keeps), Alt+klik = najazd na tym słowie.
3. **Inspektor elementu**: dla grafiki tekst, podtytuł, ikona (wybór z Lucide), start (przesuń na słowo), długość, strona; dla segmentu zoom a/b, t0/t1, face x/y (z podglądem kadru i ramką głowy z `head`); dla muzyki głośność dB, seed/styl; dla SFX włącz/wyłącz per zdarzenie, głośność.
4. **Podgląd**: render proxy 640×360 tylko wybranego zakresu (±10 s) przez `assemble.py` z flagą proxy (do dodania: skala + `-preset ultrafast`), odtwarzacz HTML5.
5. **Raport krytyka**: lista problemów z linkiem do miejsca na osi, przycisk „Popraw automatycznie” (critic --fix) i „Akceptuję” (wyjątek zapisany w planie).
6. **Render pełny**: kolejka (`run_v4.sh`), log, postęp, ostrzeżenie o baterii.

## Wymagania
- Działa offline na laptopie; backend Python (FastAPI) lub Node, frontend prosty (bez ciężkiego frameworka wideo). Uruchamianie jednym poleceniem, port lokalny.
- Każda zmiana z historią (undo, kopia planu przed zapisem).
- Nie rusza oryginałów nagrań. Pliki robocze w `~/video-pipeline/render`.
- Testy: zapis/odczyt planu, round-trip edl, uruchomienie krytyka na przykładowym projekcie `2026-10-20`.

## Rozważone gotowe projekty (stan 2026-10-20)
- Kdenlive 26.08 (zainstalowany): pełny edytor, import OTIO z naszego `to_otio.py`, ale nie rozumie naszych zoomów, najazdów ani reguł; zmiany nie wracają do planu.
- OpenCut (MIT): klasyczny edytor w przeglądarce ma oś, keyframe’y i maski, ale brak API do wczytania projektu z JSON (Editor API dopiero w planach); przepisywany od zera.
- designcombo/react-video-editor (1,8k gwiazdek): oś czasu w React, eksport w przeglądarce; licencja darmowa do 3 pracowników, format JSON nieudokumentowany.
- Remotion Editor Starter: płatny szablon.
Wniosek: najmniej pracy i najlepsze dopasowanie daje własny panel nad naszym JSON. Ewentualnie komponent osi czasu z designcombo, jeśli licencja pasuje.
