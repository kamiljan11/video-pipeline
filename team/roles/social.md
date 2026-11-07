# 10 Social -> `work/posts.json`, `out/posts/<id>/`

**Misja:** z jednego filmu tyle dobrych postów, ile jest w nim samodzielnych myśli (nie stała liczba).

**Głos:** pisz według `style/voice.md` (rytm, jego frazy, `## Zakazane` sprawdza `post_check`) i słowami widzów z `style/audience-language.md`.

**Kandydaci:** każda część story, każda liczba/blizna, każdy kontrast (znak vs szlaban), każda lista kroków.
Ocena 0-3: samodzielność, konkret, kontrowersja/nowość, da się pokazać grafiką. `make: true` przy >= 8/12.

**Każdy post** (`style/REF-posts-top.md`; Kamil 2026-11-05: „grafika sama musi nieść przekaz”):
- grafika: `grafika.json` (szablon list / bars / split / table / quote, 15-230 słów) -> `node gfx/post_gfx.mjs <folder>`
  -> `grafika.png` 1080x1350 + `grafika.txt` (słowa na grafice). Karuzela PDF (`~/Dane/vp-linkedin`) tylko jako dodatek, gdy myśl ma kroki: `grafika.png` jest zawsze (`post_check` jej wymaga).
- tekst: `linkedin.json` `{"text", "hashtags"}` + `post.md`; 60-130 słów, hook 1-2 linie przed „zobacz więcej”, najwyżej 3
  hashtagi; zasób (film, repo) w przedostatniej linii, OSTATNIA linia = pytanie do komentarzy (Kamil 2026-11-07; przegląd po 4 tygodniach: komentarze na post vs 4 tygodnie przed, ADR-0015).
- sprawdzenie: `python3 post_check.py <folder>` (OCR tesseract pol: grafika czytelna sama, kontrast WCAG AA; tekst).

**Gotowe gdy:** `film_check --out` out.posts OK.
