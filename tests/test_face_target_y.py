"""build_edl.py plan key "face_target_y" (vertical films): passed to the EDL for assemble.py / face_track.py, checked.

  python3 -m unittest tests.test_face_target_y
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


class FaceTargetYTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="face-target-y-"))
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

    def edl(self, **extra):
        r = self.build(**extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads((self.d / "edl.json").read_text())

    def test_vertical_plan_passes_it_to_the_edl(self):
        self.assertEqual(self.edl(vertical=True, face_target_y=0.47)["face_target_y"], 0.47)

    def test_without_the_key_the_edl_has_none(self):  # assemble.py / face_track.py keep their 0.40 default
        self.assertNotIn("face_target_y", self.edl(vertical=True))

    def test_a_16_9_film_ignores_it_and_says_so(self):
        self.assertNotIn("face_target_y", self.edl(face_target_y=0.47))
        self.assertIn("face_target_y: ignored", self.build(face_target_y=0.47).stderr)

    def test_plan_grade_reaches_the_edl_and_the_guard_takes_hqdn3d(self):
        sys.path.insert(0, str(ROOT))
        import edl_guard
        grade = "hqdn3d=3:2.5:8:6,eq=contrast=1.04,unsharp=5:5:0.25"
        edl = self.edl(vertical=True, grade=grade)
        self.assertEqual(edl["grade"], grade)
        self.assertTrue(edl_guard.chain_ok(grade, edl_guard.VIDEO))
        self.assertNotIn("grade", self.edl(vertical=True))  # no key: assemble.py's default grade

    def test_a_bad_value_is_a_named_error(self):
        for bad in (0.1, 0.9, "0.47", True, None):
            with self.subTest(bad=bad):
                r = self.build(vertical=True, face_target_y=bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("face_target_y: 0.3..0.6", r.stderr)


if __name__ == "__main__":
    unittest.main()
