# ADR-0015 — Artykuł na kamiljan.com z filmu, głos postów, pytanie na końcu

Data: 2026-11-07 | Status: przyjęte (Kamil 7.11: „kamiljan.com tam jest blog chcemy z filmiku go też móc generować i wrzucać
automatycznie i linkować filmik na yt”, „dawaj yes”, „music -10db jest okej”) | Drzwi: dwukierunkowe |
Przegląd: po 4 tygodniach postów z pytaniem (komentarze na post vs 4 tygodnie przed)

**Kontekst:** pipeline robi long, shorty, posty i miniatury; brakowało artykułu na blog. Strona (`kamiljan11/comfy-container`,
Lovable + Vercel) trzyma posty jako dane w `src/data/posts.ts` i ma własne testy (`posts.test.ts`). Kurs Skool CCC (A19)
pokazał wejście grafiki chwilę przed słowem. Nasza próbka top postów (`style/REF-posts-top.md`) miała pytanie na końcu w 4/68.

**Decyzje:**
| co | decyzja | gdzie |
|---|---|---|
| artykuł | `out/blog/<slug>/article.json` (PL + EN, >= 1200 słów PL, >= 3 sekcje, źródła spoza filmu, film podlinkowany); `article_check.py` sprawdza reguły strony i nasze, liczby muszą paść w filmie albo stać przy linku ze `sources` | `team/roles/artykul.md`, `film_check --out` (`out.article`) |
| publikacja | `publish_post.py --confirm` = osobny worktree, gałąź `blog/<slug>`, push, PR. Merge = klik Kamila (Vercel wdraża `main`). Token tylko z mostu, w nagłówku git przez zmienne środowiska, nigdy w argv | `publish_post.py` |
| głos | `style/voice.md` (z tekstów Kamila) + `style/audience-language.md`; lista `## Zakazane` blokuje posty i artykuły, brak listy = błąd, nie cisza | `post_check.banned_phrases` |
| pytanie | ostatnia linia posta = pytanie do komentarzy (decyzja Kamila wbrew próbce 4/68) | `post_check.text_problems`, `team/roles/social.md` |
| `gfx_lead` | klucz planu, grafika wchodzi przed słowem (-0,5..-0,1 s); bez klucza `build_edl` tnie jak dawniej, a `film_check` daje FAIL `gfx_lead` (jak każdy punkt listy: `skip` z powodem albo `FILM_CHECK=off` dla starego projektu) | `build_edl.py`, bramki `long/short.gfx_lead` |
| muzyka | -10 dB zostaje | bez zmiany |

**Odrzucone:** pisanie wprost do `main` strony (brak przeglądu przed publikacją); osobny CMS (strona ma posty jako dane w repo,
Lovable synchronizuje z GitHubem); token w URL remote (widoczny w `ps`).

**Konsekwencje / cofnięcie:** zmiana struktury strony (nazwa repo, `posts.ts`, kotwica `POSTS`, sitemap, `og-meta.spec.ts`)
wymaga edycji stałych w `publish_post.py`. Token: skrypt zdejmuje `GITHUB_Token` ze środowiska na starcie (hook pre-commit strony, `scripts/git-hooks`, to kod z obcego repo), push dostaje nagłówek tylko w swoim env i odmawia, gdy strona ma własny hook pre-push. Pytanie na końcu: daty i komentarze postów zapisuje Kamil/rola social w `render/post_log.json` (do zbudowania razem z NOTES_LOG, Taski #6); bez tego przegląd się nie odbędzie (świadomie w kodzie: zmienia się rzadko, a skrypt odmawia głośno, gdy kotwicy brak).
Pytanie na końcu: cofnięcie, gdy po 4 tygodniach komentarze na post nie wzrosły vs 4 tygodnie przed; wtedy usunąć warunek z
`post_check.text_problems` i linię w `social.md`. Stare posty filmu 2 (`out_v2`) nie przechodzą `out.posts` do poprawki.
**Koszt cykliczny:** 0 zł.
