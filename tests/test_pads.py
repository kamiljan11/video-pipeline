"""build_edl.py plan key "pads": more air at cuts (pre/post/keep_l/keep_r/mingap), checked; absent = old cuts.

  python3 -m unittest tests.test_pads
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
DEFAULTS = {"pre": 0.10, "post": 0.16, "mingap": 0.45, "keep_l": 0.15, "keep_r": 0.12}


class PadsTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="pads-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        words = [(1.0, 1.5, " a"), (1.6, 2.9, " b"), (4.05, 4.5, " c")]
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round(a * 1000), "to": round(b * 1000)}, "text": t} for a, b, t in words]}))
        (self.d / "rec.sil").write_text("silence_start: 0\nsilence_end: 1.0\nsilence_start: 4.6\nsilence_end: 6\n")

    def build(self, **extra):
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 2]], "edl_out": "edl.json", **extra}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d,
                              capture_output=True, text=True, check=False)

    def segments(self, **extra):
        r = self.build(**extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [(s["in"], s["out"]) for s in json.loads((self.d / "edl.json").read_text())["segments"]]

    def test_without_the_key_cuts_match_the_explicit_defaults(self):  # old plans render exactly as before
        self.assertEqual(self.segments(), self.segments(pads=DEFAULTS))

    def test_more_post_keeps_more_sound_after_the_last_word(self):
        (_, out_default), = self.segments()
        (_, out_padded), = self.segments(pads={"post": 0.28})
        self.assertGreater(out_padded, out_default)

    def test_bad_pads_are_named_errors(self):
        for bad, msg in (([0.2], "pads: object"), ({"pre": 0.2, "gap": 1}, "pads: object"),
                         ({"pre": "0.2"}, "pads.pre"), ({"post": True}, "pads.post"), ({"mingap": 3}, "pads.mingap"),
                         ({"keep_l": -0.1}, "pads.keep_l")):
            with self.subTest(bad=bad):
                r = self.build(pads=bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(msg, r.stderr)


if __name__ == "__main__":
    unittest.main()
