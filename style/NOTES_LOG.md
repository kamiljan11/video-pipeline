# NOTES_LOG: każda uwaga Kamila -> jedna reguła

Pętla (Skool CCC A7/E18, P1 task 6): uwaga przychodzi -> wpis tutaj i w pliku POPRAWKI rundy -> **przepisz JEDNĄ istniejącą
regułę** (punkt `style/checklist.json`, bramka, dane stylu) tak, żeby uwaga nie wróciła; nową regułę dopisz tylko, gdy żadna
istniejąca nie dotyczy tematu. Kolumna "reguła" wskazuje, gdzie reguła żyje (id z checklisty w backtickach, plik, test).
Status: `zrobione` (reguła działa), `do zrobienia` (zapisane, bramki jeszcze nie ma), `scalone z N` (ta sama reguła co N).
`tests/test_notes_log.py` pilnuje formatu i tego, że każde id z checklisty istnieje.

| # | data | film | uwaga Kamila | reguła | brzmienie reguły | status |
|---|---|---|---|---|---|---|
| 1 | 2026-11-05 | 2026-11-04 long | okienko PiP nie jest wycentrowane | `long.head_track`, gfx_types.pip_window, tests/test_pip_window.py | PiP wycinany z nagrania wokół głowy danego fragmentu (plan `head_track`) | zrobione |
| 2 | 2026-11-05 | 2026-11-04 long | za dużo skoków na osobny ekran | `long.screen_share`, `long.screen_switches`, `long.screen_block`, `long.speaker_back` | pełny ekran tylko gdy treść go potrzebuje; udział, częstotliwość i przerwy mierzone | zrobione |
| 3 | 2026-11-05 | 2026-11-04 long | napis za nim nieczytelny (WYZNANIE na wysokości głowy) | `long.behind_readable` | tekst za postacią zasłonięty najwyżej w 15 % (cover.json), inaczej nad linię głowy | zrobione |
| 4 | 2026-11-05 | 2026-11-04 long | elementy znikają, zanim da się je przeczytać | `long.reading`, render_audit.py `short` | karta na ekranie co najmniej czas czytania (film_check.reading_need) i >= 1,5 s w gotowym renderze | zrobione |
| 5 | 2026-11-05 | 2026-11-04 long | memy GIF mile widziane, kotki na wszystko | `long.memes`, style/memes.json | mem jako naklejka z Pexels/Pixabay; Giphy/Tenor tylko za zgodą (Content ID, ADR-0008) | zrobione |
| 6 | 2026-11-05 | 2026-11-04 long | narysuj zamiast pisać (szlaban) | docs/designs/2026-11-05-visual-upgrade.md | słowo-obiekt w zdaniu dostaje rysunek obok/za postacią, nie napis | do zrobienia |
| 7 | 2026-11-05 | 2026-11-04 long | więcej ruchu, nic nie stoi | docs/designs/2026-11-05-visual-upgrade.md | animowane grafiki i memy, nie tylko animowany tekst | do zrobienia |
| 8 | 2026-11-05 | 2026-11-04 posty | grafika posta LinkedIn sama musi nieść przekaz | `out.posts`, post_check.py | grafika bez tekstu posta daje pełną myśl; OCR >= 85 % słów, kontrast WCAG | zrobione |
| 9 | 2026-11-05 | 2026-11-04 shorty | kółko w shorcie to ultra zbliżenie twarzy | `short.head_track`, tests/test_pip_window.py CornerRenderTest | kółko wycinane z nagrania wokół głowy, widać głowę i ramiona | zrobione |
| 10 | 2026-11-05 | 2026-11-04 long | (pomiar uwag 2 i 4) | `long.screen_share`, `long.reading` | progi z pomiaru v2 | scalone z 2 |
| 11 | 2026-11-05 | 2026-11-04 posty | (bramka grafiki posta) | `out.posts` | jak 8; "bez pytania na końcu" zastąpione przez 24 | scalone z 8 |
| 12 | 2026-11-05 | pipeline | zmiana domyślna w assemble/build_edl psuje test zgodności panelu | panel/CLAUDE.md, panel tests/test_pipeline_compat.py | nowe zachowanie tylko pod kluczem planu/EDL; bez klucza render jak dawniej | zrobione |
| 13 | 2026-11-05 | 2026-11-04 shorty | memy w shortach nieczytelne, plansza końcowa 3 s | `short.meme`, `short.end` | mem dostaje czas czytania albo wypada; bez planszy, ogon <= 0,6 s | zrobione |
| 14 | 2026-11-05 | 2026-11-04 posty | (recenzja) wartość ze speca wstrzyknięta do HTML grafiki posta | gfx/post_gfx.mjs, gfx/test/post_gfx.test.mjs | wartości ze speca: lista dozwolonych albo escape, CSP default-src 'none', JS wyłączony | zrobione |
| 15 | 2026-11-05 | 2026-11-04 long v2 | tablice boczne za małe na telefon | docs/designs/2026-11-05-visual-upgrade.md | tekst po skali kamery czytelny na telefonie (min wysokość tekstu na klatce 1440), inaczej mniej elementów albo pełny ekran | do zrobienia |
| 16 | 2026-11-05 | 2026-11-04 long v2 | stempel musi siedzieć na rzeczy, którą ocenia | scene check (commit 96640c1) | stempel zawsze na swojej karcie, nigdy sam w pustym miejscu | zrobione |
| 17 | 2026-11-05 | 2026-11-04 long v2 | animuj akcję zamiast pisać werdykt (ODMOWA) | docs/designs/2026-11-05-visual-upgrade.md | przełącznik odskakuje / miga na czerwono zamiast słowa | do zrobienia |
| 18 | 2026-11-05 | 2026-11-04 long v2 | obwódki i strzałki muszą trafiać w cel | docs/designs/2026-11-05-visual-upgrade.md | linia przypinana do id węzła albo bramka "linia przecina pudełko" | do zrobienia |
| 19 | 2026-11-05 | 2026-11-04 long v2 | memy muszą pasować do zdania i być aktualne | style/memes.json | każdy mem: zdanie, dlaczego pasuje, wiek; stare wymienić | do zrobienia |
| 20 | 2026-11-05 | 2026-11-04 long v2 | dubel ujęcia schowany przez dryf transkrypcji (5:30) | render_audit.py `repeat` | podejrzane miejsca transkrybowane ponownie (whisper -ml 1) przed cięciem; podwójne słowo na cięciu łapie render_audit | do zrobienia |
| 21 | 2026-11-05 | 2026-11-04 long v2 | muzyka za cicha | plan `music_db` -10, ADR-0015 | podkład -10 dB; przy zmianie poziomu podgląd audio przed renderem | zrobione |
| 22 | 2026-11-05 | 2026-11-04 long v2 | research ma zmienić wygląd, nie tylko czasy | docs/designs/2026-11-05-visual-upgrade.md | z REF brać też mechanikę wizualną | do zrobienia |
| 23 | 2026-11-05 | proces | każdą uwagę zapisuj i organizuj, żeby była przestrzegana | style/NOTES_LOG.md, team/RUNBOOK.md | uwaga -> wpis tutaj + POPRAWKI -> przepisanie jednej reguły | zrobione |
| 24 | 2026-11-07 | proces | post kończy się pytaniem ("dawaj yes") | `out.posts`, post_check.text_problems, ADR-0015 | ostatnia linia posta = pytanie do komentarzy; przegląd po 4 tygodniach | zrobione |
| 25 | 2026-11-08 | 2026-11-04 miniatury | „głupie miny”, „rozmazane”: metryka klatki nie widziała wzroku w bok ani obrotu głowy | frame_pick.py (MediaPipe), ADR-0020, test progów | wzrok w bok > 0,2, głowa > 10° = nie kandydat; arkusz klatek oglądany przed miniaturą | zrobione |
| 26 | 2026-11-08 | proces | bramki gfx (scene_check, thumbs, post_gfx) przez symlink kończyły exit 0 i nic nie robiły | gfx/cli.mjs isMain, gfx/test/cli.test.mjs | skrypt wołany przez dowiązanie działa albo mówi, czemu nie; nigdy cichy exit 0 | zrobione |
| 27 | 2026-11-08 | 2026-11-04 okładki | „18% LECI NA ŚLEPO”: liczba bez podmiotu na okładce | content_review.py thumbs (stranger test), thumb_check | każda miniatura/okładka: kto/co + liczba; werdykt z „dlaczego” przed renderem | zrobione |
| 28 | 2026-11-08 | grafiki | sieroty „w”, „z”, „bez”, „nie” na końcu linii (okładka bloga, posty) | gfx/html_lib.mjs prose(), testy | jedna reguła typografii dla miniatur, postów i kart filmu | zrobione |
| 29 | 2026-11-08 | posty, opis | liczby w postach niesprawdzane z filmem; opis longa bez ## Źródła / ## Zasoby | build_posts_v3 --words, plan sources, film_check out.sources/out.resources | każda liczba z filmu, każde twierdzenie z publicznym źródłem; brak źródła = pytanie do Kamila | zrobione (92→18 czeka na Kamila) |
