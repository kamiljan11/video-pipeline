# ADR-0020 — MediaPipe Face Landmarker w wyborze klatek (wzrok, mina, pozycja głowy)

Data: 2026-11-08 | Status: przyjęte (Kamil 8.11: „glupie miny wybierasz”, „brzydkie czasami rozmazane”) | Drzwi: dwukierunkowe |
Przegląd: po pierwszym pakiecie miniatur zrobionym tą logiką — ile klatek Kamil odrzuci przy oglądaniu

**Kontekst:** `frame_pick.py` liczył tylko miary z 5 punktów YuNet. Na 20 okładkach i miniaturach filmu 2026-11-04,
obejrzanych z bliska: kontrast w okolicy oka dał 0,94 prawie zamkniętym oczom (rzęsy i brwi też mają kontrast), a spojrzenie
w bok i głowa odwrócona o 20° przeszły każdą miarę (okładki s03, s05, s06, s14, s18). Trzy heurystyki pikselowe (ciemny punkt
w oku, białko po obu stronach tęczówki, odblask) nie odróżniły dobrych klatek od złych.

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| model | MediaPipe Face Landmarker (Google, PyPI `mediapipe==1.2.2`, model `face_landmarker.task` float16/1, 3,7 MB) | `frame_pick.expression_reader` |
| miary | blendshapes: wzrok poziomo/pionowo, mrugnięcie, dziubek, wciągnięte usta, otwarta szczęka; pozycja głowy z macierzy (yaw, pitch, roll) | `frame_pick.expression` |
| bramka | wzrok w bok > 0,25, w dół < −0,3, w górę > 0,35, mrugnięcie > 0,35, dziubek > 0,3, wciągnięte usta > 0,5, głowa > 12° / 12° / 9° = nie kandydat | `frame_pick.odd_face` |
| progi | z 20 klatek obejrzanych z bliska (patrzy w kamerę: wzrok ≤ 0,16, głowa ≤ 9°; w bok 0,36-0,44; odwrócona 15-20°) | stałe na górze `frame_pick.py` |
| środowisko | osobny venv `~/.local/share/vp-face-venv` (`--system-site-packages`), bo pip w systemowym Pythonie jest zablokowany (PEP 668); import tylko w funkcji, reszta repo go nie potrzebuje | README › Frame pick |
| bez mediapipe | `frame_pick` staje z komendą do uruchomienia, bez cichego powrotu do starych miar | `expression_reader` |

**Odrzucone:** heurystyki pikselowe (sprawdzone, nie rozdzielają); model punktów LBF z opencv-contrib (plik modelu spoza
oficjalnego źródła, brak kierunku wzroku); ręczny wybór klatek bez miary (to było źródłem uwag Kamila).
**Koszt:** zależność ok. 120 MB w venv (mediapipe, opencv-contrib, matplotlib); ok. 15 ms na klatkę; skrypt pakietu musi
iść pod pythonem z venv. Koszt cykliczny: 0 zł (lokalnie).
**Metryka:** klatki odrzucone przez Kamila po obejrzeniu pakietu (przed: uwagi „glupie miny” do v2; 5 z 20 klatek v3 złych
przy oglądaniu z bliska).
