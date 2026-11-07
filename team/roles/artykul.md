# 11 Artykuł -> `out/blog/<slug>/article.json` (+ obrazki obok)

**Misja:** z filmu szczegółowy artykuł na blog kamiljan.com, który linkuje film na YouTube i daje to, czego film nie mówi
(Kamil 2026-11-07: "raczej szczegółowy, może jakieś dodatkowe rzeczy, których film nie zawiera").

**Głos:** `style/voice.md` (artykuł pisany, więc bez wypełniaczy mowy) i słowa widzów z `style/audience-language.md`.

**Wejście:** `story.json` (części, liczby, blizny), transkrypcja longa (`plan_long.json` -> `words`), grafiki postów
(`out/posts/*/grafika.png`), klatki z filmu, repo z filmu.

**Jak:**
- H2 = część story; pod każdą: to, co film mówi, głębiej (kroki, kod, konfiguracja, liczby z pomiaru) + 1 rzecz spoza filmu
  (źródło, kontrprzykład, instrukcja krok po kroku). Każde źródło w `sources` i podlinkowane w tekście `[etykieta](https://...)`.
- Liczba w tekście PL = padła w filmie albo stoi w akapicie z linkiem do źródła (`article_check` to liczy).
- Film: akapit z `[obejrzyj na YouTube](<url>)` na początku i na końcu; do publikacji filmu `"youtube": null`.
- PL + EN (strona jest dwujęzyczna; EN >= 60 % długości PL, nie streszczenie). Bez długich myślników i słów "hype".
- Format = typ `Post` strony (comfy-container `src/data/posts.ts`): bloki `p`, `h2` (unikalne `id`), `list`, `code`, `img`
  (plik w folderze artykułu, alt > 20 znaków). Okładka: miniatura longa A albo grafika posta.

**Sprawdzenie:** `python3 article_check.py out/blog/<slug> --words work/<film>.json` (zasady testów strony + >= 1200 słów PL,
>= 3 H2, źródła, liczby).

**Publikacja (dopiero po filmie na YouTube i po obejrzeniu przez Kamila):**
`python3 ~/infisical/infisical_bridge.py run --secrets GITHUB_Token -- python3 publish_post.py out/blog/<slug> --confirm`
-> gałąź `blog/<slug>` + PR na kamiljan11/comfy-container. Merge = publikacja (klik Kamila), Vercel wdraża main.

**Gotowe gdy:** `film_check --out` out.article OK.
