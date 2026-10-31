"""build_edl.py caption keys: "caption_case" (CAPS or words as said) and "caption_ahead" (a word not said yet in grey).

  python3 -m unittest tests.test_caption_style
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CaptionStyleTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="caption-style-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        words = [(1.0, 1.4, " Ten"), (1.5, 1.9, " model"), (2.0, 2.4, " działa.")]
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round(a * 1000), "to": round(b * 1000)}, "text": t} for a, b, t in words]}))
        (self.d / "rec.sil").write_text("silence_start: 0\nsilence_end: 1.0\nsilence_start: 2.5\nsilence_end: 4\n")

    def lines(self, **keys) -> list[str]:
        r = self.run_plan(**keys)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [ln.split(",", 9)[9] for ln in (self.d / "c.ass").read_text().splitlines() if ln.startswith("Dialogue: 0,")]

    def run_plan(self, **keys):
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 2]], "edl_out": "edl.json",
                "vertical": True, "ass_out": "c.ass", **keys}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def test_default_is_the_old_caps_line(self):  # plans without the keys render as before
        first = self.lines()[0]
        self.assertIn("TEN", first)
        self.assertIn("{\\c&HFFFFFF&} MODEL DZIAŁA", first)

    def test_as_said_keeps_the_words_as_transcribed(self):
        first = self.lines(caption_case="as_said")[0]
        self.assertIn("Ten", first)
        self.assertIn("model działa", first)
        self.assertNotIn("MODEL", first)

    def test_dim_greys_only_the_words_not_said_yet(self):
        first, second, third = self.lines(caption_ahead="dim", caption_case="as_said")
        self.assertEqual(first.count("&H8C8C8C&"), 2)  # "model", "działa" not said yet
        self.assertEqual(second.count("&H8C8C8C&"), 1)  # "działa"
        self.assertNotIn("&H8C8C8C&", third)  # the last word: nothing ahead
        self.assertTrue(third.startswith("Ten model "))  # said words are plain white

    def test_pop_only_where_a_line_comes_in(self):
        first, second, third = self.lines(caption_pop=True)
        self.assertTrue(first.startswith("{\\fscx60\\fscy60\\t(0,70,"))
        self.assertNotIn("fscx", second + third)  # same line, next word: colour only
        self.assertNotIn("fscx", "".join(self.lines()))  # no key: as before

    def test_bad_values_are_named_errors(self):
        for key, bad in (("caption_case", "lower"), ("caption_case", True), ("caption_ahead", "grey"), ("caption_ahead", None),
                         ("caption_pop", "yes")):
            with self.subTest(key=key, bad=bad):
                r = self.run_plan(**{key: bad})
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(f"{key}:", r.stderr)


if __name__ == "__main__":
    unittest.main()
