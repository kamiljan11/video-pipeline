# Post na LinkedIn z filmu: jak napisać `linkedin.json`

Decyzja i źródła: `docs/adr/0009-linkedin-document-posts.md`. Twarde limity sprawdza `python3 linkedin.py check` (`style/linkedin.json`);
ten plik mówi, co w nich napisać. Pisze sesja Claude Code z transkrypcji filmu (`*.cw.json` albo `out/youtube_metadata.md`).

## Źródło
- Tylko to, co Kamil mówi w filmie. Liczba, nazwa, cytat = musi paść w nagraniu albo w materiałach filmu. Zero dopisanych faktów.
- Jedna myśl na post: ta, która w filmie ma najmocniejszy dowód (liczba, własna porażka, konkretny przykład).

## Tekst posta (`text`)
- 1. linia = hak, sam w sobie zdanie (≤ 150 znaków): liczba, przyznanie się albo kontrast. Bez „W dzisiejszym poście…”.
- 2. linia dopowiada hak; obie razem ≤ 210 znaków (tyle widać przed „…więcej”).
- Krótkie akapity (1–3 zdania), pusta linia między nimi. Ton jak w filmie: pierwsza osoba, rzeczowo, bez przechwałek.
- Na końcu jedno pytanie do czytelnika (komentarze) i zdanie, że slajdy są w dokumencie, a cały film w pierwszym komentarzu.
- Bez linków w treści (link = `first_comment`), bez półpauz i myślników (przecinek, dwukropek, kropka), bez emoji na start.
- 600–3000 znaków; najlepiej 900–1500.
- `hashtags`: 3–5 słów bez `#` (np. `["AI", "automatyzacja", "MŚP"]`), skrypt dopisze je na końcu jako prawdziwe hashtagi.
- Znaki `( ) [ ] # * _ @ < > | { } ~ \` w tekście są OK: skrypt je escapuje (inaczej LinkedIn odrzuci albo zepsuje post).

## Pierwszy komentarz (`first_comment`)
- Link do filmu na YouTube + jedno zdanie, co tam jest więcej. Do 1250 znaków.

## Karuzela (`carousel`)
- `title`: nazwa dokumentu widoczna na LinkedIn (≤ 100 znaków), zwykle tytuł filmu.
- 5–12 slajdów: `cover` -> `point` × N -> `end`. Jeden slajd = jedna myśl, którą da się przeczytać w 3 sekundy.
- `cover`: `title` = hak (≤ 70 znaków), `sub` = obietnica (co czytelnik z tego weźmie). Opcjonalnie `photo` (kadr z filmu, .jpg/.png,
  ścieżka względem specu) = twarz w kółku.
- `point`: numer dokłada się sam; `title` = zasada w rozkazie albo stwierdzeniu, `body` ≤ 220 znaków = dowód lub przykład z filmu.
- `end`: wezwanie (film w komentarzu, pytanie). Tekst za długi na slajd = `render` stoi z nazwą slajdu: skróć, nie zmniejszaj fontu.
- Kolory: `theme.json` obok specu (jak w kartach), np. `{"theme": "cetus"}`.

## Kolejność
```bash
python3 linkedin.py check   <dir>/linkedin.json
python3 linkedin.py render  <dir>/linkedin.json      # obejrzyj PDF: pdftoppm -r 40 -png <dir>/linkedin.pdf <dir>/podglad
python3 linkedin.py publish <dir>/linkedin.json      # dry run: autor, token, tekst
python3 linkedin.py publish <dir>/linkedin.json --publish
```
