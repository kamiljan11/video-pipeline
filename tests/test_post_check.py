"""post_check: the LinkedIn post graphic says alone what it should (OCR), the text keeps the measured habits
(style/REF-posts-top.md, Kamil 2026-11-05 "grafika sama musi nieść przekaz").

  python3 -m unittest tests.test_post_check
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import post_check as P  # after the path insert: the scripts are not a package

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"  # fonts-dejavu-extra (Ubuntu desktop, CI)
LINES = ["Każdy błąd zostawia bliznę", "Nowe sprawdzenie w systemie", "Ten sam błąd nie przejdzie drugi raz",
         "Jak nowy punkt w procedurze pilota", "Ponad sto blizn z prawdziwych projektów"]
TEXT = " ".join(["słowo"] * 80) + "\nRepo w pierwszym komentarzu."


def picture(d: Path, ink: str, lines=LINES) -> None:
    """a post graphic as gfx/post_gfx.mjs leaves it: grafika.png and its words in grafika.txt"""
    draw = ",".join(f"drawtext=fontfile={FONT}:text='{ln}':fontsize=56:fontcolor={ink}:x=80:y={120 + 140 * k}" for k, ln in enumerate(lines))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0A1430:s=1080x1350", "-frames:v", "1", "-vf", draw,
                    str(d / "grafika.png")], check=True)
    (d / "grafika.txt").write_text(" ".join(lines) + "\n")


class TextTest(unittest.TestCase):
    def test_hashtags_end_question_and_length_are_named(self):
        self.assertEqual(P.text_problems(TEXT, ["AI", "ClaudeCode", "kod"]), [])
        bad = P.text_problems("za krótko?", ["a", "b", "c", "d"])
        for want in ("4 hashtags", "ends on a question", "words of text"):
            self.assertTrue(any(want in b for b in bad), bad)


    def test_a_broken_post_folder_is_a_named_problem_not_a_traceback(self):
        # review 2026-11-05: empty text gave IndexError, bad JSON a JSONDecodeError, both without the post's name
        self.assertIn('no "text"', P.text_problems("  \n ", [])[0])
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            for body, want in (("{nie json", "not JSON"), ("[]", "needs"), ('{"hashtags": []}', "needs")):
                (d / "linkedin.json").write_text(body)
                self.assertTrue(any(want in b for b in P.problems(d)), (body, P.problems(d)))

    def test_a_graphic_older_than_its_spec_is_named(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            for f in ("grafika.png", "grafika.txt"): (d / f).write_text("x")
            (d / "grafika.json").write_text("{}")
            os.utime(d / "grafika.json", (2e9, 2e9))
            self.assertIn("newer than grafika.png", P.graphic_problems(d)[0])


@unittest.skipUnless(shutil.which("tesseract") and Path(FONT).exists(), "tesseract and DejaVu (CI installs both: .github/workflows/quality.yml)")
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
