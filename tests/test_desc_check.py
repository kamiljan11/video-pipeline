"""desc_check + utm: YouTube descriptions (round 2 Y0-Y5, S2, S3, S10, M1, M2) and the one link tagger (X1)"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import desc_check as D
import utm

FOOT = utm.URL.sub(lambda m: utm.tag(m.group(0), "youtube", "long", "t"), D.footer())  # the footer as the pack writes it
LONG = f"""## Opis
Kod z AI, który sam się sprawdza.
Artykuł: https://kamiljan.com/blog/x?utm_source=youtube&utm_medium=long&utm_campaign=t

Rozdziały:
0:00 Wstęp
1:05 Część 1
3:00 Część 2

{FOOT}

## Tagi
AI, kod

## End screen
następny film: playlista Claude Code

## Przypięty komentarz
A Ty? Jaki błąd AI zrobiło Ci dwa razy?
"""
SHORT = """## Tytuł
x
## Opis
AI mówi „gotowe”, a nic nie działa.
Pełny film: {{LONG_URL}}
## Powiązany film
long
"""


class UtmTest(unittest.TestCase):
    def test_only_our_links_get_tags_and_old_tags_are_replaced(self):
        self.assertEqual(utm.tag("https://github.com/x", "youtube", "long", "f"), "https://github.com/x")
        t = utm.tag("https://KamilJan.com/blog/a?x=1&utm_source=old", "youtube", "short", "2026-11-04")
        self.assertEqual(t, "https://KamilJan.com/blog/a?x=1&utm_source=youtube&utm_medium=short&utm_campaign=2026-11-04")
        self.assertEqual(utm.untagged(f"a {t} b https://kamiljan.com c https://www.kamiljan.com/x."), ["https://kamiljan.com", "https://www.kamiljan.com/x"])  # the sentence's dot is not the link


class LongTest(unittest.TestCase):
    def test_a_good_description_passes_clean(self):
        self.assertEqual(D.long_check(LONG, 20 * 60), ([], []))

    def test_chapters_outside_the_description_fail(self):  # film 2 out_v3: chapters only under `## Rozdziały`
        md = LONG.replace("Rozdziały:\n0:00 Wstęp\n1:05 Część 1\n3:00 Część 2\n", "") + "## Rozdziały\n0:00 a\n1:00 b\n2:00 c\n"
        bad, _ = D.long_check(md)
        self.assertTrue(any("Rozdziały:" in b for b in bad), bad)
        bad, _ = D.long_check(LONG.replace("1:05 Część 1", "4:05 Część 1"))
        self.assertIn("long: chapter times do not grow", bad)

    def test_hashtags_tags_and_fold(self):
        bad, warn = D.long_check(LONG.replace("Kod z AI, który", "#AI Kod z AI, który"))
        self.assertFalse(bad); self.assertTrue(any("line 1-2" in w for w in warn), warn)
        bad, warn = D.long_check(LONG.replace(FOOT, FOOT + " #a #b #c #d"))
        self.assertFalse(bad); self.assertTrue(any("4 hashtags" in w for w in warn), warn)
        bad, _ = D.long_check(LONG.replace(FOOT, FOOT + " #a #b #c #d #e #f #g #h"))
        self.assertTrue(any("8 hashtags" in b for b in bad), bad)
        bad, _ = D.long_check(LONG.replace("AI, kod", "x" * 501))
        self.assertTrue(any("501 characters" in b for b in bad), bad)
        _, warn = D.long_check(LONG.replace("Kod z AI, który sam się sprawdza.", "a" * 111))
        self.assertTrue(any("line 1 is 111" in w for w in warn), warn)
        _, warn = D.long_check(LONG.replace("Artykuł: https://kamiljan.com/blog/x?utm_source=youtube&utm_medium=long&utm_campaign=t", "Bez linku."))
        self.assertTrue(any("first link is in line" in w for w in warn), warn)
        _, warn = D.long_check(LONG.replace("?utm_source=youtube&utm_medium=long&utm_campaign=t", ""))
        self.assertTrue(any("no utm_" in w for w in warn), warn)

    def test_first_part_chapter_density_end_screen_pinned(self):
        _, warn = D.long_check(LONG.replace("1:05 Część 1", "1:42 Część 1"))
        self.assertTrue(any("first part starts at 1:42" in w for w in warn), warn)
        _, warn = D.long_check(LONG, 4 * 60)  # 3 chapters in 4 min = 0.75/min
        self.assertTrue(any("/min" in w for w in warn), warn)
        _, warn = D.long_check(LONG.replace("## End screen\nnastępny film: playlista Claude Code\n", ""))
        self.assertTrue(any("End screen" in w for w in warn), warn)
        _, warn = D.long_check(LONG.replace("następny film: playlista Claude Code", "x"))
        self.assertTrue(any("names no video" in w for w in warn), warn)
        _, warn = D.long_check(LONG.replace("A Ty? Jaki błąd AI zrobiło Ci dwa razy?", "Dzięki."))
        self.assertTrue(any("neither a question nor a link" in w for w in warn), warn)
        _, warn = D.long_check(LONG.replace("A Ty? Jaki błąd AI zrobiło Ci dwa razy?", "https://a.pl https://b.pl"))
        self.assertTrue(any("2 links" in w for w in warn), warn)

    def test_tags_are_optional(self):  # 13/16 set them: the section is no longer required
        self.assertEqual(D.long_check(LONG.replace("## Tagi\nAI, kod\n", ""), 20 * 60), ([], []))


class ShortTest(unittest.TestCase):
    def test_a_good_short_passes_with_one_note_until_the_long_is_out(self):
        self.assertEqual(D.short_check("s1", SHORT.replace("{{LONG_URL}}", "https://youtu.be/abc")), ([], []))
        bad, warn = D.short_check("s1", SHORT)
        self.assertEqual((bad, [w for w in warn if "LONG_URL" not in w]), ([], []))

    def test_leftovers_and_no_long_link_fail(self):  # film 2 out_v3: "link do longa po jego publikacji"
        bad, _ = D.short_check("s1", SHORT.replace("Pełny film: {{LONG_URL}}", "Cały odcinek: link do longa po jego publikacji."))
        self.assertTrue(any("leftover" in b for b in bad) and any("no link to the long" in b for b in bad), bad)
        self.assertEqual(D.short_check("s1", SHORT.replace("{{LONG_URL}}", "https://youtu.be/abc"))[0], [])

    def test_hashtags_shorts_lines_related(self):
        bad, warn = D.short_check("s1", SHORT.replace("Pełny film:", "#shorts #AI #kod Pełny film:"))
        self.assertFalse(bad); self.assertTrue(any("#shorts" in w for w in warn) and any("3 hashtags" in w for w in warn), warn)
        bad, _ = D.short_check("s1", SHORT.replace("Pełny film:", "#a #b #c #d Pełny film:"))
        self.assertTrue(any("4 hashtags" in b for b in bad), bad)
        _, warn = D.short_check("s1", SHORT.replace("## Powiązany film\nlong\n", "") + "")
        self.assertTrue(any("Powiązany film" in w for w in warn), warn)
        _, warn = D.short_check("s1", SHORT.replace("Pełny film:", "a\nb\nc\nPełny film:"))
        self.assertTrue(any("4 description lines before" in w for w in warn), warn)

    def test_thesis_counted_before_the_link_and_not_a_copy_of_the_title(self):  # round 2 S2, S3
        three = SHORT.replace("AI mówi „gotowe”, a nic nie działa.", " ".join(["słowo"] * 13) + "\n" + " ".join(["inne"] * 13) + "\n" + " ".join(["trzy"] * 13))
        self.assertEqual(D.short_check("s1", three.replace("{{LONG_URL}}", "https://youtu.be/a") + "\n#AI #kod\n"), ([], []))  # 39 words in 3 lines: fine, the link and tags do not count
        _, warn = D.short_check("s1", SHORT.replace("AI mówi „gotowe”, a nic nie działa.", " ".join(["słowo"] * 51)))
        self.assertTrue(any("51 words" in w for w in warn), warn)
        copy = SHORT.replace("## Tytuł\nx", "## Tytuł\nAI mówi gotowe, a nic nie działa")
        self.assertTrue(any("repeats the title" in w for w in D.short_check("s1", copy)[1]))

    def test_fill_long_replaces_the_placeholder_and_a_left_one_warns(self):  # review 2026-11-07: code-1, ops-1
        self.assertTrue(any("still in the description" in w for w in D.short_check("s1", SHORT.replace("## Powiązany film", "## X"))[1]))
        with tempfile.TemporaryDirectory() as t:
            out = Path(t); (out / "youtube/shorts").mkdir(parents=True)
            (out / "youtube/shorts/s1.md").write_text(SHORT)
            with self.assertRaises(ValueError): D.fill_long(out, "https://evil.example/x")
            self.assertEqual(D.main(["--fill-long", "https://youtu.be/abc123", str(out)]), 0)
            self.assertIn("https://youtu.be/abc123", (out / "youtube/shorts/s1.md").read_text())
            self.assertEqual(D.short_check("s1", (out / "youtube/shorts/s1.md").read_text()), ([], []))


class FolderTest(unittest.TestCase):
    def test_the_same_line_in_two_shorts_and_a_missing_file(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t); (out / "youtube/shorts").mkdir(parents=True)
            (out / "youtube/long.md").write_text(LONG)
            for s in ("s1", "s2"): (out / f"youtube/shorts/{s}.md").write_text(SHORT)
            bad, warn = D.check(out, 20 * 60, ["s1", "s2", "s3"])
            self.assertEqual(bad, ["no youtube/shorts/s3.md"])
            self.assertTrue(any(w.startswith("s1, s2: the same description line") for w in warn), warn)
            self.assertEqual(D.main([str(out)]), 0)


if __name__ == "__main__":
    unittest.main()
