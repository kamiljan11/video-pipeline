# Wzorzec: animowany short-checklista bez twarzy (rozbiór 2026-11-04)

Źródło: kanał @BreakingBreach (439 subskrypcji 04.11.2026), YouTube Shorts:
- `Ek4VNGaih9s` „Pre-Launch Checklist for Vibe-Coded Apps” (02.11.2026, 92,5 s, 1080x1920, **60 fps**, -20,1 LUFS, 3,5 tys. wyświetleń)
- `8JsFi_ZOvio` „Vibe-Coded App Too Slow? 31 Ways to Speed It Up” (82,2 s, 1080x1920, 60 fps, -23,1 LUFS, 45 tys. wyświetleń; najpopularniejszy na kanale)

Rozbiór: arkusze klatek co 1 s (`render/ref/shorts/<id>/sheet_*.png`), pasek 12 klatek/s na 1 s (`motion_12s.png`, `caption_20s.png`), `select=gt(scene,0.2)`, `ebur128`.
Pobrane za zgodą Kamila (04.11.2026), tylko lokalnie. Bierzemy mechanikę ruchu, nie treść, grafiki ani maskotkę autora (pikselowy krab, najpewniej postać z Claude Code, czyli marka Anthropic: nie kopiujemy).

Kamil (04.11.2026): „fajne, płynne, żywe animacje”.

## Co tam jest (oba shorty mają ten sam szablon)

| element | jak działa | czas |
|---|---|---|
| **Brak cięć** | 0 zmian sceny powyżej progu 0,2 w obu filmach. Cały short to jedna ciągła scena, a zmieniają się tylko **stany** elementów. To daje wrażenie płynności. | cały film |
| **60 fps** | Ruch tekstu i kart jest renderowany w 60 klatkach. Przy 30 fps te same animacje wyglądają mniej miękko. | cały film |
| **Nagłówek kinetyczny u góry** (y ok. 140-230 na 1920) | Narracja pojawia się słowo po słowie w chwili, gdy słowo pada. Każde słowo wjeżdża z rozmyciem, przezroczystością i lekkim przesunięciem z prawej (ok. 3-4 klatki przy 12 fps, czyli ok. 0,3 s). Poprzednia fraza znika rozmyciem, zanim pojawi się nowa. | 1 fraza = 1 punkt listy |
| **Słowo kluczowe** | Jeden z czterech zabiegów: (1) szeryfowa kursywa w kolorze akcentu („privacy”, „retention”), (2) pigułka podświetlenia, która rozwija się w prawo pod słowem („keyboard navigation”), (3) czerwień dla zła („legal trouble”, „N+1”), (4) przekreślenie rysowane linią przy „Remove …” („fake countdown timers”). | przy słowie |
| **Licznik postępu** | Pigułka „Checklist N / 35” z paskiem, zawsze pod nagłówkiem. Rośnie o 1, gdy zaczyna się kolejny punkt. W drugim filmie to sam licznik „04 / 31” w rogu karty. | stała |
| **Karta-makieta UI w środku** | Mała aplikacja (okno przeglądarki, telefon, formularz, tabela) zawsze w tym samym miejscu. Każdy punkt listy zmienia jej **stan**: elementy dochodzą po kolei (stagger ok. 80 ms), linia limitu się rysuje, ikona kosza wyskakuje, checkbox dostaje ptaszek z rozbłyskiem, kursor klika z falą. Przejście między punktami: przenikanie z lekkim rozmyciem, karta się nie przesuwa. | 2-4 s na punkt |
| **Postać w prawym dolnym rogu karty** | Maskotka z delikatnym kołysaniem; reaguje (wykrzyknik, uśmiech, rogi diabła przy „złym” kodzie). Pełni rolę twarzy narratora. | stała |
| **Tło** | Jasne: biel z miękkimi pastelowymi plamami gradientu, które powoli pływają, plus delikatna siatka kropek. Ciemne (drugi film): granat z tymi samymi plamami. | stała |
| **Dźwięk** | Narracja i podkład, -20 do -23 LUFS, czyli ciszej niż nasz cel -14. | |

Tempo: 35 punktów w 92 s (2,6 s na punkt) i 31 punktów w 82 s. To format „lista N rzeczy”, a długa lista sama trzyma widza (licznik obiecuje, że będzie więcej).

## Co z tego mamy, czego nie mamy (pipeline 2026-11-04)

| element | u nas | luka |
|---|---|---|
| 60 fps | nie: `gfx/render.mjs` `FPS = 30`, `assemble.py` `fps=30` | klucz planu `fps: 60` dla shortów; karty renderowane w 60 klatkach. Koszt: renderu kart 2x dłużej. Źródło z kamery ma 30 fps, więc twarz zostaje w 30 (klatki zdublowane), a płynniej ruszają się tylko karty i tekst. |
| nagłówek słowo po słowie z rozmyciem | nie: napisy ASS (grupa słów, CAPS Montserrat, mówione słowo w akcencie) | nowy typ karty `headline` (HTML, czasy słów z `cw.json`): blur-in na słowo, poprzednia fraza blur-out; ewentualnie zamiast napisów ASS w shorcie |
| słowo kluczowe: kursywa szeryfowa / pigułka / przekreślenie | częściowo: `*słowo*` w kartach maxim = akcent kolorem | w `headline`: `*kursywa*`, `[pigułka]`, `~przekreślenie~`, `!czerwień!` |
| licznik „N / total” | nie (mamy pasek postępu filmu `progress: fill`) | klucz planu `counter` z punktami listy: pigułka rośnie na słowach-kotwicach |
| karta-makieta ze zmianą stanu | częściowo: karty `web` (zrzut strony z markerem), `list` (pozycje po kolei) | typ `scene`: jedna karta HTML na cały short, kroki stanu przypięte do słów (stagger, ptaszek, kursor z falą); najwięcej pracy |
| bez cięć, jedna ciągła scena | nie: shorty to cięcia twarzy + karty | układ „pełna scena” + twarz w kółku (`face_corner`, jest od 31.10) zamiast maskotki |
| pływające plamy tła | nie (tło kart: motyw, statyczny gradient) | CSS: 2-3 rozmyte koła z wolnym ruchem; tanie |
| maskotka | — | u nas rolę postaci gra Kamil w kółku w rogu; własnej maskotki nie robimy bez decyzji Kamila |

## Jak to pasuje do filmów Kamila

Format jest bez twarzy, a filmy Kamila są gadane. Najbliższy przeszczep bez zmiany sposobu nagrywania:
short „lista N rzeczy” z fragmentu filmu, w którym Kamil wylicza (np. „3 pomysły”, „Sprawdzone / Niesprawdzone / Nie wyszło”).
Cały czas jedna karta-scena na górze, Kamil w kółku w rogu, nagłówek słowo po słowie, licznik punktów.
Kolejność wdrożenia od najtańszego: (1) tło z plamami + 60 fps kart, (2) `headline`, (3) `counter`, (4) `scene`.
