"""themes.py: work/theme.json -> accent and ink colors for captions, progress bar and PiP frame.

Run: cd ~/video-pipeline && python3 -m pytest -q tests/test_themes.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import themes  # after the repo root is on the path


class ThemesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work, self.dir = Path(tmp.name) / "work", Path(tmp.name) / "themes"
        self.work.mkdir(); self.dir.mkdir()

    def pick(self, name, css=None):
        (self.work / "theme.json").write_text(json.dumps({"theme": name}))
        if css is not None: (self.dir / f"{name}.json").write_text(json.dumps({"css": css}))

    def test_no_theme_json_is_none(self):
        self.assertIsNone(themes.load(self.work, self.dir))

    def test_theme_gives_upper_case_accent_and_ink(self):
        self.pick("navy", {"--acc": "#6fa7ec", "--ink": "#0A1430", "--soft": "#E6EDF7"})
        self.assertEqual(themes.load(self.work, self.dir), {"name": "navy", "acc": "#6FA7EC", "ink": "#0A1430"})

    def test_the_real_cetus_theme_loads(self):
        self.pick("cetus")
        self.assertEqual(themes.load(self.work), {"name": "cetus", "acc": "#6FA7EC", "ink": "#0A1430"})

    def test_bad_files_stop_with_a_named_error(self):
        for name, css, msg in [
            ("../x", None, "must be a name"), ("Navy", None, "must be a name"), ("none", None, "no theme 'none'"),
            ("t", {"--ink": "#000000"}, "--acc must be #RRGGBB"),
            ("t", {"--acc": "rgb(1,2,3)", "--ink": "#000000"}, "--acc must be #RRGGBB"),
            ("t", {"--acc": "#000000", "--ink": "#000"}, "--ink must be #RRGGBB"),
        ]:
            with self.subTest(name=name, css=css):
                self.pick(name, css)
                with self.assertRaises(SystemExit) as e: themes.load(self.work, self.dir)
                self.assertIn(msg, str(e.exception.code))

    def test_not_json_or_not_an_object_is_a_named_error(self):
        for raw in ("[]", "null", '{"theme": "cetus"', '"cetus"'):
            with self.subTest(raw=raw):
                (self.work / "theme.json").write_text(raw)
                with self.assertRaises(SystemExit) as e: themes.load(self.work, self.dir)
                self.assertRegex(str(e.exception.code), r"theme\.json: (not valid JSON|expected a JSON object)")
        self.pick("t"); (self.dir / "t.json").write_text("[1]")
        with self.assertRaises(SystemExit) as e: themes.load(self.work, self.dir)
        self.assertIn("t.json: expected a JSON object", str(e.exception.code))

    def test_progress_bar_and_pip_frame_follow_the_theme(self):
        cetus = {"name": "cetus", "acc": "#6FA7EC", "ink": "#0A1430"}
        self.assertEqual(themes.bar_hex(None), "2de2c4")  # the color assemble.py had before themes
        self.assertEqual(themes.bar_hex(cetus), "6FA7EC")
        self.assertEqual(themes.pip_frame(None), str(themes.GFX / "pip_frame.png"))
        self.assertEqual(themes.pip_frame(cetus), str(themes.GFX / "pip_frame_cetus_6FA7EC.png"))  # in the repo
        with self.assertRaises(SystemExit) as e:  # --acc edited, no frame in the new accent yet
            themes.pip_frame({**cetus, "acc": "#086AD8"})
        self.assertIn("node gfx/pip_assets.mjs 600 #086AD8 cetus", str(e.exception.code))

    def test_ass_color_is_bgr_with_optional_alpha(self):
        self.assertEqual(themes.ass_color("#6FA7EC"), "&HECA76F")
        self.assertEqual(themes.ass_color("#2de2c4"), "&HC4E22D")  # the template's own accent, as hardcoded before
        self.assertEqual(themes.ass_color("#0d0f12", 0xD8), "&HD8120F0D")


if __name__ == "__main__":
    unittest.main()
