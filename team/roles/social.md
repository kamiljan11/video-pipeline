# 10 Social -> `work/posts.json`, `out/posts/<id>/`

**Misja:** z jednego filmu tyle dobrych postów, ile jest w nim samodzielnych myśli (nie stała liczba).

**Głos:** pisz według `style/voice.md` (rytm, jego frazy, `## Zakazane` sprawdza `post_check`) i słowami widzów z `style/audience-language.md`.

**Kandydaci:** każda część story, każda liczba/blizna, każdy kontrast (znak vs szlaban), każda lista kroków.
Ocena 0-3: samodzielność, konkret, kontrowersja/nowość, da się pokazać grafiką. `make: true` przy >= 8/12.

**Każdy post** (`style/REF-posts-top.md`; Kamil 2026-11-05: „grafika sama musi nieść przekaz”):
- grafika: `grafika.json` (szablon list / bars / split / table / quote, 15-230 słów) -> `node gfx/post_gfx.mjs <folder>`
  -> `grafika.png` 1080x1350 + `grafika.txt` (słowa na grafice). Karuzela PDF (`~/Dane/vp-linkedin`) tylko jako dodatek, gdy myśl ma kroki: `grafika.png` jest zawsze (`post_check` jej wymaga).
- tekst: `linkedin.json` `{"text", "hashtags", "cta_variant"}` + `post.md`; hook 1-2 linie przed „zobacz więcej” (linia 1 <= 140 znaków,
  bez powitania i `?`); 60-130 słów (WARN poza; < 20 = błąd); hashtagi domyślnie 0 (WARN > 0, błąd > 3, `style/platform_limits.json`);
  w treści najwyżej 1 link (reszta w pierwszym komentarzu, pole `first_comment` gdy jest); link KamilJan.com z `utm_` (`python3 utm.py <url> linkedin post <film>`);
  zasób (film, repo) w przedostatniej linii, OSTATNIA linia = pytanie do komentarzy, także jako „P.S. …?” (Kamil 2026-11-07; ADR-0015).
  `cta_variant`: `question` albo `ps` (przegląd ADR-0015 porówna komentarze per wariant). „5 rzeczy” w haku = 5 pozycji listy (w grafice `list` albo w tekście).
- `posts.json`: każdy post z `make: true` ma `publish_day` (dzień po premierze longa, 0 = ten dzień), jeden post dziennie, film rozłożony na >= 5 dni.
- sprawdzenie: `python3 post_check.py <folder>` (OCR tesseract pol: grafika czytelna sama, kontrast WCAG AA; tekst).

**Gotowe gdy:** `film_check --out` out.posts OK.
