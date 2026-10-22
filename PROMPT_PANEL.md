Zbuduj lokalny panel montażowy „Montażownia” dla mojego pipeline'u AI do montażu YouTube. Pracujemy pod PG: przed kodem przeczytaj ~/.claude/pg/design.md i dod.md, ustal tier z diffu, na końcu pg-review.

KONTEKST (przeczytaj najpierw, nic nie zgaduj):
- Pipeline już działa i jest źródłem prawdy: ~/video-pipeline (build_edl.py, face_track.py, critic.py, assemble.py, music/make_beds.py, gfx/render.mjs + gfx/template.html, run_v4.sh, verify_cut.py, spot_check.py, head_check.py, to_otio.py, stop_render.py).
- Spec panelu: ~/video-pipeline/PANEL_SPEC.md (przeczytaj w całości).
- Przykładowy projekt do testów: ~/Videos/Montaz/2026-10-20/work (plan_long.json, plan_short*.json, gfx_specs.json, edl_*.json, 2026-10-20_11-38-18.cw.json, *.sil, gfx/*.mov) i wyniki w ../out.
- Formaty (sprawdź w kodzie build_edl.py i assemble.py, zanim napiszesz parser):
  - plan_*.json: words, sil, src, keeps [[wStart,wEnd,{t0?,t1?}]], gfx [{id, word|find+near, lead}], emph [{word|find+near, amt, speed, auto?}], drift, zooms, tail, progress, verified_claims, vertical, hook_text, zoom_every_cut, edl_out, out_name, srt_out, ass_out
  - gfx_specs.json: [{id, type: kw|list|lower|chap|cta|slide|end, text, sub, icon, icons, items, delays, html, src, dur, canvas: "v" = 9:16 for shorts, compact: true = small kw above the face (only with canvas "v")}]
  - edl_*.json (generowany, tylko odczyt): segments [{src, in, out, zoom: liczba albo {a,b,t0,t1}, face [x,y], head [x0,y0,x1,y1], zmax, track [[t,cx],...]}], overlays [{file, at, dur, id, pip}], music, sfx, tail, w, h
  - *.cw.json: transcription [{offsets:{from,to} ms, text}]

CEL: przeglądarkowy panel na localhost, w którym widzę oś czasu wygenerowanego filmu i mogę ręcznie podciągnąć każdy element, a zmiany wracają do plan/gfx_specs, nie do kopii.

MUST HAVE (v1):
1. Wybór projektu (katalog work) i filmu (plan_*.json).
2. Oś czasu z ścieżkami: segmenty (kolor wg zoomu: statyczny / drift / najazd), grafiki, slajdy+PiP, waveform głosu, muzyka, SFX, znaczniki krytyka (C1–C10) w miejscach problemów. Zoom/przewijanie osi.
3. Transkrypcja obok osi: słowa wycięte przekreślone; klik = wytnij/przywróć (edycja keeps, łączenie zakresów), Alt+klik = najazd na słowie (emph), Shift+klik = zakotwicz zaznaczoną grafikę na tym słowie.
4. Inspektor zaznaczonego elementu:
   - grafika: tekst, podtytuł, ikona (lista z node_modules/lucide-static/icons z podglądem), typ, długość, przesunięcie (lead), usuń, duplikuj, nowa grafika;
   - segment: zoom a/b/t0/t1 z limitem zmax (nie pozwól przekroczyć), podgląd kadru (klatka + prostokąt kadru + ramka głowy z head);
   - najazd: siła (amt), szybkość, usuń;
   - globalnie: drift, zooms, tail, progress, hook_text, głośność muzyki (music_db), SFX (sfx_db), seed muzyki.
5. Podgląd: przycisk „Podgląd ±10 s” renderuje fragment w niskiej rozdzielczości (dodaj do assemble.py flagę --proxy: skala 640 px, -preset ultrafast, bez zmiany wyniku pełnego renderu) i odtwarza go w panelu.
6. Krytyk: przycisk „Sprawdź” (build_edl -> face_track -> critic.py), lista problemów z klikalnym przejściem na oś; „Popraw automatycznie” (critic --fix) z podglądem zmian przed zapisem; „Akceptuję” zapisuje wyjątek w planie z powodem.
7. Render pełny: kolejka (run_v4.sh dla wybranego filmu), log na żywo, ostrzeżenie gdy bateria < 40% i nie ładuje (/sys/class/power_supply/BAT0), przycisk Stop (stop_render.py).
8. Historia: każda zapisana zmiana robi kopię planu/specs z timestampem, Undo/Redo w sesji.

ZASADY:
- Lokalnie, offline, Linux. Backend Python (FastAPI) wołający istniejące skrypty przez subprocess; frontend lekki (bez ciężkiego frameworka wideo). Start jednym poleceniem, np. `montazownia ~/Videos/Montaz/2026-10-20/work`.
- NIE przepisuj logiki pipeline'u do panelu. Panel edytuje plan/gfx_specs i woła skrypty. Jeśli musisz zmienić skrypt (np. --proxy), zrób to minimalnie, z testem, i nie zmieniaj wyniku pełnego renderu.
- Nigdy nie ruszaj ~/Videos/Nagrania. Pliki robocze tylko w ~/video-pipeline/render. ~/Videos jest synchronizowany Syncthingiem, więc nie zapisuj tam plików tymczasowych.
- Żadnych zewnętrznych API ani CDN; wszystko lokalnie.
- UI po polsku, z polskimi znakami.

TESTY / DOD:
- Testy jednostkowe: round-trip plan (odczyt -> edycja keeps/emph/gfx -> zapis -> build_edl przechodzi), zmax nie do przekroczenia, kopia przed zapisem.
- Test integracyjny na projekcie 2026-10-20: otwórz short3, wytnij i przywróć słowo, dodaj najazd, zmień tekst grafiki, Podgląd ±10 s się renderuje, Sprawdź zwraca raport krytyka.
- Na koniec pokaż mi: zrzut ekranu panelu z osią short3 i long, wynik testów, listę zmienionych plików pipeline'u z diffem. Raport VERIFIED / UNVERIFIED.

Zanim zaczniesz kodować: przeczytaj PANEL_SPEC.md i wskazane skrypty, potem napisz mi krótki plan (moduły, endpointy, ekrany) i dopiero po nim buduj.
