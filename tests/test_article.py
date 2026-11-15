"""article_check.py (the blog article made from a film) and publish_post.py; no network (git against a local bare remote, a fake gh)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import article_check as A
import publish_post as P

YT = "https://www.youtube.com/watch?v=abcdefghijk"
SRC = "https://example.org/raport"
PARA = " ".join(["słowo"] * 60)


def article(d: Path, **over) -> dict:
    """a complete article folder: cover + one picture, 1700 Polish words, the film and a source linked in both languages, a 5 step how-to"""
    for f in ("cover.png", "schemat.png"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=navy:s=64x36", "-frames:v", "1", str(d / f)], check=True)
    def body(lang: str, n: int) -> dict:
        blocks: list[dict] = []
        for k in range(1, 6):  # five "Krok N" sections, a picture under every other one, n paragraphs spread over them
            blocks += [{"t": "h2", "id": f"krok-{k}", "text": f"Krok {k}: zrób część {k}"}] + [{"t": "p", "text": PARA} for _ in range(n // 5 + 1)]
            if k % 2: blocks.append({"t": "img", "src": "schemat.png", "alt": "Schemat bramki, która zatrzymuje agenta", "caption": "Bramka", "width": 64, "height": 36})
        blocks += [{"t": "p", "text": "**Uwaga:** bramka nie zastąpi przeglądu. **Zasób:** gotowy plik z regułami jest w repo."},
                   {"t": "h2", "id": "podsumowanie", "text": "Podsumowanie"},
                   {"t": "list", "items": ["Bramka zatrzymuje agenta", "Test czerwony blokuje koniec", "Raport pokazuje powód"]},
                   {"t": "p", "text": f"Cały film: [obejrzyj na YouTube]({YT}). Dane: [raport]({SRC}) mówi 95 procent."},
                   {"t": "p", "text": "Którą bramkę postawisz pierwszą u siebie?"}]
        lead = f"W 5 krokach stawiam bramkę, która zatrzymuje agenta, a 95 procent złych zmian staje przed testem. [Obejrzyj film na YouTube]({YT})."
        return {"title": f"Tytuł artykułu {lang} o bramkach", "description": "Opis artykułu, który ma ponad pięćdziesiąt znaków, ale mniej niż trzysta.",
                "lead": lead, "blocks": blocks}
    a = {"slug": "bramki-dla-agenta", "date": "2026-11-07", "youtube": YT,
         "cover": {"src": "cover.png", "width": 64, "height": 36, "alt": {"pl": "Okładka: bramka i agent na tle kodu", "en": "Cover: a gate and an agent over code"}},
         "sources": [{"label": "raport", "url": SRC}], "body": {"pl": body("pl", 28), "en": body("en", 20)}}
    a.update(over)
    (d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
    return a


def pick(a: dict, lang: str, t: str, n: int = 0) -> dict:
    """the n-th block of type t in the article body"""
    return [x for x in a["body"][lang]["blocks"] if x["t"] == t][n]


def block_has(x: dict, s: str) -> bool:
    return s in str(x.get("text", ""))


def save(d: Path, a: dict) -> None:
    (d / "article.json").write_text(json.dumps(a, ensure_ascii=False))


class ArticleCheckTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.d = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def test_a_complete_article_passes(self):
        article(self.d)
        self.assertEqual(A.problems(self.d), [])

    # PLAN 3.1-3.8 (creator-study 2026-11-07)
    def test_film_link_must_come_before_the_first_h2(self):  # 3.1
        a = article(self.d)
        a["body"]["pl"]["lead"] = "W 5 krokach stawiam bramkę, a 95 procent złych zmian staje przed testem."
        save(self.d, a)
        bad = " | ".join(A.problems(self.d))
        self.assertIn("not linked in the lead or before the first h2", bad)
        self.assertNotIn("(en): the film", bad)
        a["body"]["pl"]["blocks"].insert(0, {"t": "p", "text": f"Film: [obejrzyj]({YT})."})  # a paragraph before the first h2 counts too
        save(self.d, a)
        self.assertEqual(A.problems(self.d), [])

    def test_lead_is_short_and_carries_a_digit(self):  # 3.2
        a = article(self.d)
        a["body"]["pl"]["lead"] = f"Krótki wstęp bez liczby, [film]({YT})"
        a["body"]["en"]["lead"] = "In 5 steps " + " ".join(["word"] * 80) + f" [film]({YT})"
        save(self.d, a)
        bad = A.problems(self.d)
        self.assertIn("lead (pl): no digit (the promise carries a number: parts, minutes or a measured result)", bad)
        self.assertTrue(any(p.startswith("lead (en): 8") and "at most 80" in p for p in bad), bad)

    def test_a_how_to_needs_five_sections_and_the_promised_step_count(self):  # 3.3
        a = article(self.d)
        a["body"]["pl"]["lead"] = a["body"]["pl"]["lead"].replace("5 krokach", "4 krokach")
        a["body"]["en"]["lead"] = a["body"]["en"]["lead"].replace("5 krokach", "5 steps")
        a["body"]["en"]["blocks"] = [x for x in a["body"]["en"]["blocks"] if not (x["t"] == "h2" and x["id"] in ("krok-2", "krok-3"))]
        save(self.d, a)
        bad = " | ".join(A.problems(self.d))
        self.assertIn("steps (pl): the lead promises 4 steps, the text has 5", bad)
        self.assertIn("steps (en): the lead promises 5 steps, the text has 3", bad)
        self.assertIn("sections (en): at least 5 h2 (a how-to: one per step), got 4", bad)

    def test_a_lead_without_a_step_promise_does_not_count_steps(self):  # 3.3: only a promise is checked
        a = article(self.d)
        a["body"]["pl"]["lead"] = f"Bramka zatrzymuje agenta w 20 minut. [Film]({YT})"
        save(self.d, a)
        self.assertEqual(A.problems(self.d), [])

    def test_an_article_that_is_not_a_how_to_needs_1200_words_and_3_sections(self):  # review 2026-11-07: product-4
        a = article(self.d)
        a["body"]["pl"]["lead"] = f"Bramka zatrzymuje agenta w 20 minut. [Film]({YT})"
        a["body"]["en"]["lead"] = f"A gate stops the agent in 20 minutes. [Film]({YT})"
        for lang in ("pl", "en"):
            h2 = [x["id"] for x in a["body"][lang]["blocks"] if x["t"] == "h2"]
            a["body"][lang]["blocks"] = [x for x in a["body"][lang]["blocks"] if not (x["t"] == "h2" and x["id"] in h2[:2])]
        save(self.d, a)
        self.assertFalse([p for p in A.problems(self.d) if p.startswith("sections")], A.problems(self.d))
        self.assertTrue(A.is_howto({"lead": "Pokażę to w 5 krokach."}))
        self.assertEqual(A.said_numbers(self._words(" trzech jednym")), {"3", "1"})

    def _words(self, text: str) -> Path:
        w = self.d / "w.json"
        w.write_text(json.dumps({"transcription": [{"text": t} for t in text.split()]}))
        return w

    def test_shape_warnings_never_fail(self):  # round 2 A1, A3, A4, A8
        a = article(self.d)
        pl = a["body"]["pl"]
        pl["blocks"] = [x for x in pl["blocks"] if not block_has(x, "**Uwaga:**")]
        pick(a, "pl", "h2", 0)["text"] = "1. Zrób część"
        pick(a, "pl", "h2", 1)["text"] = "2. Druga część"
        pick(a, "pl", "h2", 5)["text"] = "6. Podsumowanie"
        pick(a, "pl", "list")["items"] = ["jedno", "dwa"]
        pick(a, "pl", "p")["text"] = " ".join(["słowo"] * 81)
        pl["title"] = "Tytuł z liczbą 7 o bramkach"
        save(self.d, a)
        self.assertNotIn("WARN", " ".join(A.problems(self.d)))
        w = " | ".join(A.warnings(self.d))
        for part in ("callouts (pl): no **Uwaga:** / **Zasób:**", "recap (pl): 2 points", "over 80 words", "number 7 from the title",
                     "promise (pl): the lead promises 5, the text has 6 numbered sections"):
            self.assertIn(part, w)

    def test_a_clean_article_has_no_shape_warnings(self):  # review 2026-11-08: the negative path, en skips callouts, recap 3..N
        a = article(self.d)
        self.assertEqual(A.shape_warnings(a["body"]["pl"], "(pl)"), [])
        self.assertEqual(A.shape_warnings({"lead": "", "blocks": [{"t": "p", "text": "x"}]}, "(en)"), [])
        few = {"lead": "", "blocks": [{"t": "h2", "text": "A"}, {"t": "p", "text": "x"}, {"t": "list", "items": list("abc")}]}
        self.assertEqual(A.shape_warnings(few, "(en)"), [])  # one section: a 3 point recap is fine, never "want 3 to 1"

    def test_picture_density_warns_but_never_fails(self):  # 3.4
        a = article(self.d)
        a["body"]["pl"]["blocks"] = [x for x in a["body"]["pl"]["blocks"] if x["t"] != "img"]
        save(self.d, a)
        self.assertEqual(A.problems(self.d), [])
        w = A.warnings(self.d)
        self.assertEqual(len(w), 1, w)
        self.assertIn("pictures (pl): 0 for 6 sections", w[0])
        article(self.d)
        self.assertEqual(A.warnings(self.d), [])
        r = subprocess.run([sys.executable, str(ROOT / "article_check.py"), str(self.d)], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_ending_is_a_recap_list_the_film_link_and_a_closing_question(self):  # 3.5
        a = article(self.d)
        a["body"]["pl"]["blocks"][-1]["text"] = "To wszystko."  # no question
        a["body"]["en"]["blocks"] = [x for x in a["body"]["en"]["blocks"] if x["t"] != "list"]  # no recap
        save(self.d, a)
        bad = " | ".join(A.problems(self.d))
        self.assertIn("ending (pl): the last block must be a paragraph ending with '?'", bad)
        self.assertIn("ending (en): no recap list", bad)
        a = article(self.d)
        next(b for b in a["body"]["pl"]["blocks"] if YT in b.get("text", "") and b["t"] == "p")["text"] = f"Dane: [raport]({SRC}) mówi 95 procent."  # the film is linked up front, not in the ending
        save(self.d, a)
        bad = " | ".join(A.problems(self.d))
        self.assertIn("ending (pl): the film", bad)
        self.assertNotIn("recap", bad)

    def test_a_number_in_the_title_must_be_said_in_the_film(self):  # 3.7
        a = article(self.d)
        a["body"]["pl"]["title"] = "Bramka agenta w 12 minut i 5 kroków"
        save(self.d, a)
        words = self.d / "w.json"
        words.write_text(json.dumps({"transcription": [{"text": " 5"}, {"text": " kroków"}, {"text": " 95"}]}))
        bad = A.problems(self.d, words)
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("title (pl): numbers not said in the film: 12", bad[0])
        words.write_text(json.dumps({"transcription": [{"text": " 12"}, {"text": " 5"}, {"text": " 95"}]}))
        self.assertEqual(A.problems(self.d, words), [])
        self.assertEqual(A.problems(self.d), [])  # no transcript given: skipped

    def test_one_thousand_two_hundred_words_is_no_longer_enough(self):  # 3.8
        a = article(self.d)
        a["body"]["pl"]["blocks"] = [x for i, x in enumerate(a["body"]["pl"]["blocks"]) if not (x["t"] == "p" and len(x["text"]) > 300 and i % 3 == 0)]
        save(self.d, a)
        words = len(" ".join(A.block_text(x) for x in a["body"]["pl"]["blocks"]).split())
        self.assertTrue(1200 <= words < 1500, words)
        self.assertIn("words, want at least 1500", " | ".join(A.problems(self.d)))

    def test_the_sites_own_rules_are_named(self):
        a = article(self.d)
        a["body"]["pl"]["description"] = "za krótki"
        a["body"]["pl"]["blocks"][1]["text"] = "To jest rewolucyjne — serio"
        pick(a, "pl", "h2", 1)["id"] = "krok-1"
        pick(a, "en", "img")["alt"] = "krótki"
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        bad = " | ".join(A.problems(self.d))
        for want in ("description (pl)", "em or en dash", "hype word", "heading ids (pl)", "alt more than 20"):
            self.assertIn(want, bad)

    def test_ours_detailed_sourced_and_the_film_linked(self):
        a = article(self.d, sources=[])
        a["body"]["pl"]["blocks"] = a["body"]["pl"]["blocks"][:4] + a["body"]["pl"]["blocks"][-1:]
        a["body"]["en"]["blocks"][-2]["text"] = "no links here"
        a["body"]["en"]["lead"] = "In 5 steps the gate stops the agent."
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        bad = " | ".join(A.problems(self.d))
        for want in ('"sources"', "(pl) ", "words, want at least 1500", "(en): the film", "is not linked"):
            self.assertIn(want, bad)

    def test_numbers_must_be_said_in_the_film_or_carry_a_source(self):
        a = article(self.d)
        a["body"]["pl"]["blocks"].insert(3, {"t": "p", "text": "Agent zrobił 4321 kroków w 17 minut."})
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        words = self.d / "w.json"
        words.write_text(json.dumps({"transcription": [{"text": " 17"}, {"text": " minut"}]}))
        bad = A.problems(self.d, words)
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("4321", bad[0])
        self.assertNotIn("17,", bad[0])  # said in the film; "95" sits in a block with a source link

    def test_the_film_link_does_not_back_an_invented_number(self):
        a = article(self.d)
        a["body"]["pl"]["blocks"].insert(3, {"t": "p", "text": f"Wymyślone 4321 kroków, film: [obejrzyj]({YT})."})
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        words = self.d / "w.json"
        words.write_text(json.dumps({"transcription": [{"text": " 17"}]}))
        bad = A.problems(self.d, words)
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("4321", bad[0])

    def test_a_thumbnail_copied_as_the_blog_cover_fails(self):
        # Kamil 2026-11-08: out_v3 blog cover = long thumbnail A ("18% LECI NA ŚLEPO ... musisz zmienic logiki")
        art = self.d / "out" / "blog" / "bramki-dla-agenta"; art.mkdir(parents=True); (self.d / "out" / "thumbnails").mkdir()
        article(art)
        twin = self.d / "out" / "thumbnails" / "long_A.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(art / "cover.png"), "-vf", "scale=128:72", str(twin)], check=True)
        self.assertTrue(any("is the thumbnail long_A.jpg" in b for b in A.problems(art)))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=orange:s=128x72", "-frames:v", "1", str(twin)], check=True)
        self.assertFalse(any("is the thumbnail" in b for b in A.problems(art)))

    def test_pictures_must_sit_inside_the_article_folder(self):
        (self.d / "a").mkdir()
        outside = self.d / "outside.png"
        a = article(self.d / "a")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=8x8", "-frames:v", "1", str(outside)], check=True)
        a["cover"]["src"] = "../outside.png"
        pick(a, "pl", "img")["src"] = str(outside)
        (self.d / "a" / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        bad = " | ".join(A.problems(self.d / "a"))
        self.assertIn("cover '../outside.png'", bad)
        self.assertIn(f"picture {str(outside)!r}", bad)

    def test_banned_title_bad_words_file_and_a_youtube_tail_are_named(self):
        a = article(self.d, youtube=YT + '"><script>')
        a["body"]["pl"]["title"] = "Game changer w bramkach agenta"
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        bad = " | ".join(A.problems(self.d))
        self.assertIn("'game changer'", bad)
        self.assertIn("youtube ", bad)
        article(self.d)
        broken = self.d / "w.json"; broken.write_text('{"segments": []}')
        self.assertIn('not a whisper.cpp words json', " | ".join(A.problems(self.d, broken)))

    def test_no_youtube_yet_is_allowed_but_publish_refuses(self):
        article(self.d, youtube=None)
        self.assertEqual(A.problems(self.d), [])
        r = subprocess.run([sys.executable, str(ROOT / "publish_post.py"), str(self.d)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('"youtube" is null', r.stderr)

    def test_dry_run_writes_nothing(self):
        article(self.d)
        r = subprocess.run([sys.executable, str(ROOT / "publish_post.py"), str(self.d), "--repo", str(self.d / "nope")], cwd=ROOT,
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("dry run: branch blog/bramki-dla-agenta", r.stdout)


class PublishEditsTest(unittest.TestCase):
    def test_post_goes_first_with_web_paths(self):
        with tempfile.TemporaryDirectory() as t:
            a = article(Path(t))
        entry = P.ts_post(a, a["slug"])
        self.assertIn('"/blog/bramki-dla-agenta/cover.webp"', entry)
        self.assertIn('"/blog/bramki-dla-agenta/schemat.webp"', entry)
        self.assertNotIn('"youtube": "http', entry)  # the site's Post type has no URL field; the film is a block + a link in the text
        src = 'const X = 1;\nexport const POSTS: Post[] = [\n  {\n    slug: "old",\n  },\n];\n'
        new = P.add_post(src, entry, a["slug"])
        self.assertLess(new.index("bramki-dla-agenta"), new.index('slug: "old"'))
        with self.assertRaises(SystemExit): P.add_post(new, entry, a["slug"])  # the same slug twice
        with self.assertRaises(SystemExit): P.add_post("no anchor", entry, a["slug"])

    def test_the_film_player_follows_the_first_paragraph_in_both_languages(self):
        with tempfile.TemporaryDirectory() as t:
            a = article(Path(t))
        for k, x in enumerate(a["body"]["pl"]["blocks"]): x["t"] = "h2" if k == 0 else x["t"]  # pl: a heading before the first p
        post = json.loads(P.ts_post(a, a["slug"]).strip().rstrip(","))
        for lang, b in post["body"].items():
            vids = [x for x in b["blocks"] if x["t"] == "youtube"]
            self.assertEqual(vids, [{"t": "youtube", "id": "abcdefghijk", "title": a["body"][lang]["title"],
                                     "poster": "/blog/bramki-dla-agenta/cover.webp"}], lang)
            i = b["blocks"].index(vids[0])
            self.assertEqual(b["blocks"][i - 1]["t"], "p", lang)
            self.assertNotIn("p", [x["t"] for x in b["blocks"][:i - 1]], lang)  # right after the FIRST paragraph
        self.assertEqual(P.with_video([{"t": "h2"}], {"t": "youtube"}), [{"t": "youtube"}, {"t": "h2"}])  # no paragraph: opens the body

    def test_youtube_id_from_both_url_shapes(self):
        self.assertEqual(P.youtube_id("https://youtu.be/VeM1WTRy8nA"), "VeM1WTRy8nA")
        self.assertEqual(P.youtube_id("https://www.youtube.com/watch?v=VeM1WTRy8nA&t=30s"), "VeM1WTRy8nA")
        self.assertEqual(P.youtube_id("https://youtu.be/VeM1WTRy8nA?si=abc"), "VeM1WTRy8nA")
        for bad in ("https://youtu.be/short", "https://evil.example/watch?v=VeM1WTRy8nA", "https://youtu.be/VeM1WTRy8nA\"><x>", ""):
            with self.assertRaises(SystemExit, msg=bad): P.youtube_id(bad)

    def test_sitemap_and_og_page_once(self):
        sm = '<urlset>\n  <url>\n    <loc>https://kamiljan.com/blog/old</loc>\n  </url>\n</urlset>\n'
        once = P.add_sitemap(sm, "nowy", "2026-11-07")
        self.assertIn("<loc>https://kamiljan.com/blog/nowy</loc>", once)
        self.assertEqual(P.add_sitemap(once, "nowy", "2026-11-07"), once)
        og = 'const PAGES = [\n  "/blog",\n  "/blog/old",\n  "/uslugi",\n];\n'
        added = P.add_og_page(og, "nowy")
        self.assertIn('  "/blog/old",\n  "/blog/nowy",\n  "/uslugi"', added)
        self.assertEqual(P.add_og_page(added, "nowy"), added)



def git(*a: str, cwd: Path) -> str:
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


class ConfirmTest(unittest.TestCase):
    """--confirm end to end: a bare 'origin' with the site's three files, a fake gh on PATH, the token never in argv"""
    POSTS_TS = 'export const POSTS: Post[] = [\n  {\n    slug: "old",\n  },\n];\n'

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.art = Path(self.t.name) / "art"; self.art.mkdir(); article(self.art)

    def site(self, posts: str = POSTS_TS, more: tuple[tuple[str, str], ...] = ()) -> None:
        d = Path(self.t.name)
        seed, self.bare, self.repo = d / "seed", d / "origin.git", d / "site"
        for f, text in ((P.POSTS, posts),
                        (P.SITEMAP, "<urlset>\n</urlset>\n"), (P.OG_SPEC, 'const PAGES = [\n  "/blog/old",\n];\n'), *more):
            (seed / f).parent.mkdir(parents=True, exist_ok=True); (seed / f).write_text(text)
        git("init", "-q", "-b", "main", cwd=seed); git("add", "-A", cwd=seed)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "chore: seed the site", cwd=seed)
        git("clone", "-q", "--bare", str(seed), str(self.bare), cwd=d)
        git("clone", "-q", str(self.bare), str(self.repo), cwd=d)
        git("config", "user.name", "t", cwd=self.repo); git("config", "user.email", "t@t", cwd=self.repo)
        self.bin = d / "bin"; self.bin.mkdir()
        self.calls = d / "gh.args"

    def tearDown(self):
        self.t.cleanup()

    def publish(self, gh_rc: int = 0, gh_sleep: int = 0, timeout: int = 300, env_more: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        gh = self.bin / "gh"
        gh.write_text(f'#!/bin/sh\nsleep {gh_sleep}\necho "$@" > {self.calls}\necho https://github.com/x/y/pull/1\nexit {gh_rc}\n'); gh.chmod(0o755)
        # git config from the caller's environment (the stop gate runs tests with a hooks path override) would replace
        # the hooks these tests set in the repo
        base = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG")}
        env = {**base, "PATH": f"{self.bin}:{os.environ['PATH']}", "GITHUB_Token": "tok-SECRET-123", "PUBLISH_TIMEOUT": str(timeout), **(env_more or {})}
        return subprocess.run([sys.executable, str(ROOT / "publish_post.py"), str(self.art), "--repo", str(self.repo), "--remote", str(self.bare), "--confirm"],
                              cwd=ROOT, env=env, capture_output=True, text=True, check=False)

    def test_branch_pushed_and_pr_opened(self):
        self.site()
        r = self.publish()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PR: https://github.com/x/y/pull/1", r.stdout)
        posts = git("show", "blog/bramki-dla-agenta:src/data/posts.ts", cwd=self.bare)
        self.assertLess(posts.index("bramki-dla-agenta"), posts.index('slug: "old"'))
        self.assertIn("public/blog/bramki-dla-agenta/cover.webp", git("ls-tree", "-r", "--name-only", "blog/bramki-dla-agenta", cwd=self.bare))
        self.assertIn("--head blog/bramki-dla-agenta", self.calls.read_text())
        self.assertNotIn("tok-SECRET-123", self.calls.read_text() + r.stdout + r.stderr)

    def test_a_failure_before_the_push_leaves_nothing_behind(self):
        self.site(posts="no anchor\n")  # the site changed: add_post refuses after the worktree exists
        r = self.publish()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found; the site changed", r.stderr)
        self.assertFalse((self.repo.parent / "comfy-blog-bramki-dla-agenta").exists())
        self.assertEqual(git("branch", "--list", "blog/*", cwd=self.repo), "")
        self.assertEqual(git("branch", "--list", "blog/*", cwd=self.bare), "")

    def test_the_sites_hooks_never_see_the_token(self):
        self.site()
        hooks = self.repo / "site-hooks"; hooks.mkdir()
        spy = hooks / "pre-commit"
        spy.write_text(f'#!/bin/sh\nenv > {self.bin}/hook.env\n'); spy.chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)  # the site's own hooks dir, as comfy-container has
        r = self.publish()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("tok-SECRET-123", (self.bin / "hook.env").read_text())

    def test_the_sites_pre_commit_finds_the_sites_node_modules(self):  # 2026-11-15: check-encoding.mjs imports esbuild
        self.site(more=((".gitignore", "node_modules\n"),))
        (self.repo / "node_modules" / "esbuild").mkdir(parents=True)
        hooks = self.repo / "site-hooks"; hooks.mkdir()
        hook = hooks / "pre-commit"
        hook.write_text("#!/bin/sh\ntest -d node_modules/esbuild || { echo no esbuild >&2; exit 1; }\n"); hook.chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)
        r = self.publish()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("node_modules", git("ls-tree", "-r", "--name-only", "blog/bramki-dla-agenta", cwd=self.bare))

    def test_a_site_pre_push_hook_stops_before_the_push(self):
        self.site()
        hooks = self.repo / "site-hooks"; hooks.mkdir()
        (hooks / "pre-push").write_text("#!/bin/sh\nexit 0\n"); (hooks / "pre-push").chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)
        r = self.publish()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("push hook would run with the token", r.stderr)
        self.assertEqual(git("branch", "--list", "blog/*", cwd=self.bare), "")

    def test_a_hooks_dir_elsewhere_under_the_pg_folder_is_not_trusted(self):  # stop gate 2026-11-07: TMPDIR there let the push through
        self.site()
        home = Path(self.t.name) / "home"; hooks = home / ".claude" / "tmp" / "site-hooks"; hooks.mkdir(parents=True)
        (hooks / "pre-push").write_text("#!/bin/sh\nexit 0\n"); (hooks / "pre-push").chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)
        r = self.publish(env_more={"HOME": str(home)})
        self.assertNotEqual(r.returncode, 0, r.stderr)
        self.assertIn("push hook would run with the token", r.stderr)

    def test_a_site_reference_transaction_hook_stops_before_the_push(self):  # git push runs it locally too
        self.site()
        hooks = self.repo / "site-hooks"; hooks.mkdir()
        (hooks / "reference-transaction").write_text("#!/bin/sh\nexit 0\n"); (hooks / "reference-transaction").chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)
        r = self.publish()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("reference-transaction", r.stderr)
        self.assertEqual(git("branch", "--list", "blog/*", cwd=self.bare), "")

    def test_our_own_quality_hooks_folder_is_trusted(self):  # the only exception: core.hooksPath = publish_post.PG_HOOKS
        self.site()
        home = Path(self.t.name) / "home"; hooks = home / ".claude" / "git-hooks"; hooks.mkdir(parents=True)
        (hooks / "pre-push").write_text("#!/bin/sh\nexit 0\n"); (hooks / "pre-push").chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)
        r = self.publish(env_more={"HOME": str(home)})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_hung_gh_ends_with_a_message(self):
        self.site()
        r = self.publish(gh_sleep=10, timeout=4)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no answer in 4 s", r.stderr)

    def test_a_failed_pr_says_the_branch_is_pushed(self):
        self.site()
        r = self.publish(gh_rc=1)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("branch blog/bramki-dla-agenta is pushed", r.stderr)
        self.assertNotIn("tok-SECRET-123", r.stderr)

if __name__ == "__main__":
    unittest.main()
