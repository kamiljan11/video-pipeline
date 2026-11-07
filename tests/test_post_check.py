"""post_check: the LinkedIn post graphic says alone what it should (OCR), the text keeps the measured habits
(style/REF-posts-top.md, Kamil 2026-11-05 "grafika sama musi nieść przekaz").

  python3 -m unittest tests.test_post_check
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import post_check as P  # after the path insert: the scripts are not a package

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"  # fonts-dejavu-extra (Ubuntu desktop, CI)
LINES = ["Każdy błąd zostawia bliznę", "Nowe sprawdzenie w systemie", "Ten sam błąd nie przejdzie drugi raz",
         "Jak nowy punkt w procedurze pilota", "Ponad sto blizn z prawdziwych projektów"]
TEXT = "Pierwsza linia mówi wynik, nie wstęp.\n" + " ".join(["słowo"] * 80) + "\nRepo w pierwszym komentarzu.\nA Ty jak to robisz?"


def picture(d: Path, ink: str, lines=LINES) -> None:
    """a post graphic as gfx/post_gfx.mjs leaves it: grafika.png and its words in grafika.txt"""
    draw = ",".join(f"drawtext=fontfile={FONT}:text='{ln}':fontsize=56:fontcolor={ink}:x=80:y={120 + 140 * k}" for k, ln in enumerate(lines))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0A1430:s=1080x1350", "-frames:v", "1", "-vf", draw,
                    str(d / "grafika.png")], check=True)
    (d / "grafika.txt").write_text(" ".join(lines) + "\n")


class TextTest(unittest.TestCase):
    def test_hashtags_missing_question_and_length_are_named(self):
        self.assertEqual(P.text_problems(TEXT, ["AI", "ClaudeCode", "kod"]), [])
        bad = P.text_problems("za krótko.", ["a", "b", "c", "d"])
        for want in ("4 hashtags", "must end on a question", "words of text"):
            self.assertTrue(any(want in b for b in bad), bad)


    def test_round_2_links_word_range_hashtags_cta_variant(self):  # LI1-LI4
        self.assertTrue(any("2 links" in b for b in P.text_problems(TEXT + "\nhttps://a.pl https://b.pl\nA Ty?", [])))
        short30 = " ".join(["słowo"] * 29) + " koniec?"
        self.assertFalse([b for b in P.text_problems(short30, []) if "words" in b])  # 30 words: a WARN now, not a problem
        self.assertTrue(any("30 words" in w for w in P.text_warnings(short30, [])))
        self.assertTrue(any("at least" in b for b in P.text_problems("dziesięć słów tylko tutaj i nic więcej nie ma?", [])))
        w = P.text_warnings(TEXT, ["AI"])
        self.assertTrue(any("1 hashtags" in x for x in w) and any("cta_variant" in x for x in w), w)
        self.assertFalse([x for x in P.text_warnings(TEXT, [], "ps") if "hashtags" in x or "cta_variant" in x])
        self.assertEqual(P.text_problems(TEXT.rstrip() + "\nP.S. Jak to robisz u siebie?", []), [])  # "P.S. ...?" closes the post
        self.assertTrue(any("no utm_" in x for x in P.text_warnings(TEXT + "\nhttps://kamiljan.com/blog/x\nA Ty?", [], "ps")))

    def test_round_2_count_in_the_text_and_colon_without_list(self):  # LI5
        t = "5 rzeczy, które sprawdzam w kodzie z AI:\n- testy\n- typy\n- lint\n- recenzja\nA Ty?"
        self.assertEqual(P.text_count_problems(t, None), ["the hook promises 5 things, the text lists 4"])
        self.assertEqual(P.text_count_problems(t, {"type": "list", "items": []}), [])  # the graphic's list is count_problems
        self.assertTrue(any("ends on ':'" in x for x in P.text_warnings("Oto co robię:\nNic nie robię.\nA Ty?", [])))

    def test_line_1_is_a_hook_not_a_greeting_filler_long_or_a_question(self):  # PLAN 4.1
        def bad(first): return P.hook_problems(TEXT.replace(TEXT.splitlines()[0], first, 1))
        self.assertEqual([b for b in P.text_problems(TEXT.replace(TEXT.splitlines()[0], "Cześć, dziś pokażę coś o AI.", 1), []) if b.startswith("line 1")], [],
                         "line 1 rules are warnings (review 2026-11-07), never in problems()")
        self.assertEqual(bad("92% zmian wchodziło bez przeglądu, dziś 18%."), [])
        for first, want in (("Cześć, dziś pokażę coś o AI.", "greeting"), ("Dzisiaj opowiem o szlabanie.", "filler"),
                            ("5 rzeczy o AI w kodzie.", "title"), ("Jak ufać AI, które kłamie?", "question mark"),
                            ("AI kłamie w kodzie. " + "x" * 130, "characters")):
            self.assertTrue(any(want in b for b in bad(first)), (first, bad(first)))
        self.assertEqual(P.hook_problems("  \n"), [])

    def test_numbers_must_be_said_in_the_film(self):  # PLAN 4.2
        said = {"92", "18", "3"}
        self.assertEqual(P.number_problems("92% do 18%, trzy razy 3,5", "3 filary", said)[0].split(": ")[1].split(" (")[0], "3.5")
        bad = P.number_problems("W 2026 było 92 proc.", "Liczba 40 i 18", said)
        self.assertTrue("text" in bad[0] and "2026" in bad[0] and "92" not in bad[0].split(": ")[1], bad)
        self.assertTrue("graphic" in bad[1] and "40" in bad[1], bad)
        self.assertEqual(P.number_problems("2026", "40", None), [])  # no words file: skipped, never a failure

    def test_inflected_number_words_count_as_said_and_line_1_is_only_a_warning(self):  # review 2026-11-07: data-1, product-1
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "linkedin.json").write_text(json.dumps({"text": "Cześć, dziś o AI.\n" + TEXT.split("\n", 1)[1].replace("słowo", "3 i 5", 1), "hashtags": []}))
            w = d / "w.json"
            w.write_text(json.dumps({"transcription": [{"text": " trzech"}, {"text": " pięciu"}]}))
            self.assertFalse([p for p in P.problems(d, w) if "numbers" in p or p.startswith("line 1")], P.problems(d, w))
            self.assertTrue(any("greeting" in x for x in P.warnings(d)), P.warnings(d))
        self.assertEqual(P.hook_count("Trzech rzeczy nie robię."), 3)

    def test_problems_reads_the_words_file_and_spelled_numbers(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "linkedin.json").write_text(json.dumps({"text": TEXT.replace("słowo", "92 i 40", 1), "hashtags": []}))
            (d / "grafika.txt").write_text("trzy filary i 7")
            w = d / "w.json"
            w.write_text(json.dumps({"transcription": [{"text": " 92"}, {"text": " trzy"}, {"text": " 7"}]}))
            for f in ("grafika.png",): (d / f).write_text("x")
            bad = [b for b in P.problems(d, w) if "numbers" in b]
            self.assertEqual(len(bad), 1, bad)
            self.assertIn("40", bad[0]); self.assertNotIn("92,", bad[0])
            self.assertFalse(any("numbers" in b for b in P.problems(d)))  # no words file
            w.write_text("{}")
            self.assertTrue(any("not a whisper.cpp" in b for b in P.problems(d, w)))

    def test_a_count_in_the_hook_equals_the_list_items(self):  # PLAN 4.3
        spec = {"type": "list", "items": [{"h": "a"}] * 4}
        self.assertEqual(P.hook_count("5 rzeczy, które zmieniły kod"), 5)
        self.assertEqual(P.hook_count("Trzy drobne rzeczy w systemie"), 3)
        self.assertIsNone(P.hook_count("92% zmian bez przeglądu"))
        self.assertIn("promises 5", P.count_problems("5 rzeczy o AI", spec)[0])
        self.assertEqual(P.count_problems("4 rzeczy o AI", spec), [])
        self.assertEqual(P.count_problems("5 rzeczy o AI", {"type": "bars", "items": [1]}), [])  # no list to count
        self.assertEqual(P.count_problems("Jedno zdanie o AI", spec), [])

    def test_banned_phrases_from_the_voice_file_are_named(self):  # style/voice.md "## Zakazane"
        with tempfile.TemporaryDirectory() as t:
            v = Path(t) / "voice.md"
            v.write_text("# Głos\n## Zakazane\n- Game changer\n- długi myślnik\n## Przykłady\n- nie to\n")
            self.assertEqual(P.banned_phrases(v), ["game changer", "\u2014"])
            bad = P.text_problems(TEXT.replace("słowo", "To game changer \u2014 serio", 1), [], P.banned_phrases(v))
            self.assertTrue(any("'game changer'" in b and "'\u2014'" in b for b in bad), bad)
            self.assertEqual(P.text_problems(TEXT, [], P.banned_phrases(v)), [])
        self.assertIn("rewolucja", P.banned_phrases())  # the repo's own voice file is read
        with tempfile.TemporaryDirectory() as d:
            v = Path(d) / "voice.md"
            v.write_bytes(b"## Zakazane\r\n- Game Changer\r\n")
            self.assertEqual(P.banned_phrases(v), ["game changer"])  # CRLF
            v.write_text("## Banned\n- game changer\n", encoding="utf-8")
            with self.assertRaises(ValueError): P.banned_phrases(v)  # renamed heading

    def test_a_broken_post_folder_is_a_named_problem_not_a_traceback(self):
        # review 2026-11-05: empty text gave IndexError, bad JSON a JSONDecodeError, both without the post's name
        self.assertIn('no "text"', P.text_problems("  \n ", [])[0])
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            for body, want in (("{nie json", "not JSON"), ("[]", "needs"), ('{"hashtags": []}', "needs")):
                (d / "linkedin.json").write_text(body)
                self.assertTrue(any(want in b for b in P.problems(d)), (body, P.problems(d)))

    def test_an_ocr_that_hangs_is_a_named_problem(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(P.shutil, "which", return_value="/usr/bin/tesseract"), \
                mock.patch.object(P, "ocr", side_effect=subprocess.TimeoutExpired("tesseract", 120)):
            d = Path(t)
            for f in ("grafika.png", "grafika.txt"): (d / f).write_text("x")
            self.assertTrue(any("OCR failed" in b for b in P.graphic_problems(d)), P.graphic_problems(d))

    def test_a_graphic_older_than_its_spec_is_named(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            for f in ("grafika.png", "grafika.txt"): (d / f).write_text("x")
            (d / "grafika.json").write_text("{}")
            os.utime(d / "grafika.json", (2e9, 2e9))
            self.assertIn("newer than grafika.png", P.graphic_problems(d)[0])


# CI installs both (.github/workflows/quality.yml): there a missing one fails the run instead of skipping the OCR tests
@unittest.skipUnless((shutil.which("tesseract") and Path(FONT).exists()) or os.environ.get("CI"), "tesseract and DejaVu (local machine without them)")
class GraphicTest(unittest.TestCase):
    def test_readable_text_passes_and_dark_on_dark_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t); picture(d, "0xECF0F6")
            self.assertEqual(P.graphic_problems(d), [])
            picture(d, "0x162240")  # navy on navy: there, but nobody reads it in the feed
            self.assertTrue(any("low contrast" in b for b in P.graphic_problems(d)), P.graphic_problems(d))

    def test_no_graphic_or_too_few_words(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            self.assertIn("no grafika.png", P.graphic_problems(d)[0])
            picture(d, "0xECF0F6"); (d / "grafika.txt").write_text("Każdy błąd zostawia bliznę\n")
            self.assertTrue(any("4 words on the graphic" in b for b in P.graphic_problems(d)))


if __name__ == "__main__":
    unittest.main()
