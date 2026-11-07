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
    """a complete article folder: cover + one picture, 1300 Polish words, the film and a source linked in both languages"""
    for f in ("cover.png", "schemat.png"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=navy:s=64x36", "-frames:v", "1", str(d / f)], check=True)
    def body(lang: str, n: int) -> dict:
        blocks = [{"t": "h2", "id": f"czesc-{k}", "text": f"Część {k}"} for k in range(3)]
        blocks += [{"t": "p", "text": PARA} for _ in range(n)]
        blocks += [{"t": "p", "text": f"Cały film: [obejrzyj na YouTube]({YT}). Dane: [raport]({SRC}) mówi 95 procent."},
                   {"t": "img", "src": "schemat.png", "alt": "Schemat bramki, która zatrzymuje agenta", "caption": "Bramka", "width": 64, "height": 36}]
        return {"title": f"Tytuł artykułu {lang} o bramkach", "description": "Opis artykułu, który ma ponad pięćdziesiąt znaków, ale mniej niż trzysta.",
                "lead": "Krótki wstęp.", "blocks": blocks}
    a = {"slug": "bramki-dla-agenta", "date": "2026-11-07", "youtube": YT,
         "cover": {"src": "cover.png", "width": 64, "height": 36, "alt": {"pl": "Okładka: bramka i agent na tle kodu", "en": "Cover: a gate and an agent over code"}},
         "sources": [{"label": "raport", "url": SRC}], "body": {"pl": body("pl", 22), "en": body("en", 18)}}
    a.update(over)
    (d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
    return a


class ArticleCheckTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.d = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def test_a_complete_article_passes(self):
        article(self.d)
        self.assertEqual(A.problems(self.d), [])

    def test_the_sites_own_rules_are_named(self):
        a = article(self.d)
        a["body"]["pl"]["description"] = "za krótki"
        a["body"]["pl"]["blocks"][0]["text"] = "To jest rewolucyjne — serio"
        a["body"]["pl"]["blocks"][1]["id"] = "czesc-0"
        a["body"]["en"]["blocks"][-1]["alt"] = "krótki"
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        bad = " | ".join(A.problems(self.d))
        for want in ("description (pl)", "em or en dash", "hype word", "heading ids (pl)", "alt more than 20"):
            self.assertIn(want, bad)

    def test_ours_detailed_sourced_and_the_film_linked(self):
        a = article(self.d, sources=[])
        a["body"]["pl"]["blocks"] = a["body"]["pl"]["blocks"][:4] + a["body"]["pl"]["blocks"][-1:]
        a["body"]["en"]["blocks"][-2]["text"] = "no links here"
        (self.d / "article.json").write_text(json.dumps(a, ensure_ascii=False))
        bad = " | ".join(A.problems(self.d))
        for want in ('"sources"', "(pl) ", "words, want at least 1200", "(en): the film", "is not linked"):
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

    def test_pictures_must_sit_inside_the_article_folder(self):
        (self.d / "a").mkdir()
        outside = self.d / "outside.png"
        a = article(self.d / "a")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=8x8", "-frames:v", "1", str(outside)], check=True)
        a["cover"]["src"] = "../outside.png"
        a["body"]["pl"]["blocks"][-1]["src"] = str(outside)
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
        self.assertNotIn('"youtube"', entry)  # the site's Post type has no such field; the film is a link in the text
        src = 'const X = 1;\nexport const POSTS: Post[] = [\n  {\n    slug: "old",\n  },\n];\n'
        new = P.add_post(src, entry, a["slug"])
        self.assertLess(new.index("bramki-dla-agenta"), new.index('slug: "old"'))
        with self.assertRaises(SystemExit): P.add_post(new, entry, a["slug"])  # the same slug twice
        with self.assertRaises(SystemExit): P.add_post("no anchor", entry, a["slug"])

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

    def site(self, posts: str = POSTS_TS) -> None:
        d = Path(self.t.name)
        seed, self.bare, self.repo = d / "seed", d / "origin.git", d / "site"
        for f, text in ((P.POSTS, posts),
                        (P.SITEMAP, "<urlset>\n</urlset>\n"), (P.OG_SPEC, 'const PAGES = [\n  "/blog/old",\n];\n')):
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

    def publish(self, gh_rc: int = 0, gh_sleep: int = 0, timeout: int = 300) -> subprocess.CompletedProcess:
        gh = self.bin / "gh"
        gh.write_text(f'#!/bin/sh\nsleep {gh_sleep}\necho "$@" > {self.calls}\necho https://github.com/x/y/pull/1\nexit {gh_rc}\n'); gh.chmod(0o755)
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "GITHUB_Token": "tok-SECRET-123", "PUBLISH_TIMEOUT": str(timeout)}
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

    def test_a_site_pre_push_hook_stops_before_the_push(self):
        self.site()
        hooks = self.repo / "site-hooks"; hooks.mkdir()
        (hooks / "pre-push").write_text("#!/bin/sh\nexit 0\n"); (hooks / "pre-push").chmod(0o755)
        git("config", "core.hooksPath", str(hooks), cwd=self.repo)
        r = self.publish()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pre-push hook would run with the token", r.stderr)
        self.assertEqual(git("branch", "--list", "blog/*", cwd=self.bare), "")

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
