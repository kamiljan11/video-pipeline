# Zasady Kamila Jana do shortów i rolek 9:16 (uwagi zebrane 2026-10-31)

Czytać przed każdym montażem shortów. Każdy punkt to błąd, który już raz został zgłoszony. Uzupełnia `REF-shorts-proof-cards.md` (wzorzec układów A/B/C).

## Cięcia
- Materiał tylko z właściwego nagrania (sprawdzić datę i projekt, zanim zacznie się montaż).
- Granice cięć stawiać na ciszy: profil energii co 40 ms z `.wav` plus whisper na krótkim oknie. Czasy słów z transkrypcji bywają przesunięte o około 0,5 s. W planie jawne `t0`/`t1`, gdy granica auto wypada w mowie.
- Nie ucinać głosek, zostawić oddech między zdaniami.
- Przejęzyczenia i powtórzone ujęcia wycinać w całości, zostawić lepsze ujęcie (np. „na tym kroku najczęściej przerywają…” wypada, zostaje „na jakim kroku ludzie najczęściej przerywają”).
- Każde cięcie sprawdzić 3 razy: ponowna transkrypcja gotowej rolki (verify_cuts), energia na krawędzi (cisza poniżej ok. -45 dB), whisper na oknie wokół cięcia.

## Układ kadru
- Układy A (split: karta u góry, twarz w boksie pod nią), B (pełna karta), C (sama twarz). Zmiana układu co kilka sekund, nie jedna karta na pół minuty.
- Przy dużej karcie nigdy połowa twarzy. W boksie cała głowa z brodą (`face_target_y` 0.48).
- Krótka karta: boks z twarzą zaraz pod kartą i napisem, do dolnej krawędzi ekranu (`face_box` w specu karty). Bez pustej przestrzeni między kartą a twarzą.
- Twarz w boksie nie może być za blisko. Pod kartą żadnych zoomów ani punch-inów (dotyczy też kart `web`). Pod oknem strony boks węższy niż karta (820 px), bo szeroki boks za bardzo powiększa twarz.
- Pełna karta B: Kamil w kółku w prawym dolnym rogu (`face_corner`), duże kółko (460 px) z rozmytą poświatą obrazu dookoła. Kiedy tłumaczy, ma być widoczny.
- Karty idące jedna po drugiej stykają się bez zanikania (`no_fade_out` plus jedna klatka zakładki; karta `web` po karcie dostaje `no_fade_in`). Zero pojedynczych klatek gołej twarzy między kartami (sprawdzać klatka po klatce).
- Jeden przykład pokazany jednym sposobem. Zaczęło się na kartce, to kończy się na kartce (bez wtrącania osobnej ciemnej planszy w środku).
- Karty ze stron internetowych: to samo okno (ten sam rozmiar) dla wszystkich kart w rolce, marker na cytowanym zdaniu, minimum ok. 3,5 s na kartę.
- Żadna karta nie startuje pusta i nie ma pustego ekranu dłużej niż sekundę. Animacja w karcie zsynchronizowana ze słowem.

## Treść i marka
- Każde twierdzenie w 100% prawdziwe i sprawdzone ze źródłem. Wymyślone liczby i nazwy w makietach podpisane „przykład” / „dane przykładowe”.
- Logo Cetus Automation to wieloryb z zębatką ze strony automation.cetuspro.com, nigdy gwiazda z zipa `cetus-automation-logo.zip`.
- Bez długich myślników (—) nigdzie, także w tekstach na kartach i hookach.
- Napisy zawsze wtopione.
- Rolki dla marki robić pod przypadkowego widza profilu firmy, bez historii o własnych porażkach. TÜV NORD nie pojawia się nigdzie.

## Technika (żeby nie wracały te same błędy)
- Po zmianie specu karty nic nie kasować: klucz cache (`gfx/<id>.mov.key`) to motyw + spec karty (scena: także `gfx/scene_lib.mjs`), karta renderuje się sama (do 2026-11-04 klucz był tylko z motywu i trzeba było usuwać `.mov`).
- `run_v4.sh` przebudowuje EDL (krytyk `--fix`), więc czasy kart liczyć po ustabilizowaniu EDL.
- `render.mjs` z względnym katalogiem gfx: obraz zrzutu przez `pathToFileURL(path.resolve(...))` (naprawione 2026-10-31).
