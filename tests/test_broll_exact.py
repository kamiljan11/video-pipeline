"""broll.py film times = build_edl's on frame-exact EDLs (seg_exact): pg-review T3 2026-11-09 data-1 — b-roll counted raw
piece lengths while overlays counted whole frames, so clips drifted from their anchor word piece by piece."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import broll
import timeline

SEGS = [{"in": 0.0, "out": 10.0 + 0.4 / timeline.FPS}, {"in": 12.0, "out": 25.0}]  # piece 1: 10.013 s raw, 10.0 s in frames
W = [(13.0, 13.4, " serwer")]


class BrollExactTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(prefix="broll-")
        self.addCleanup(self.dir.cleanup)
        self.clip = Path(self.dir.name) / "a.mp4"
        self.clip.write_bytes(b"x")

    def at(self, exact):
        items = [{"word": 0, "file": str(self.clip), "dur": 2.5, "lead": 0.0}]
        out, skipped = broll.place(items, W, SEGS, [], cache=self.dir.name, exact=exact)
        self.assertEqual(skipped, [])
        return out[0]["at"]

    def test_a_frame_exact_edl_places_the_clip_on_the_whole_frame_clock(self):
        self.assertEqual(self.at(True), round(timeline.src2out(13.0, SEGS, True), 3))
        self.assertEqual(self.at(True), 11.0)
        self.assertNotEqual(self.at(False), self.at(True))  # the raw clock is 0.013 s later: the drift the review found

    def test_exact_of_reads_the_edl_then_the_plan(self):
        self.assertTrue(broll.exact_of({"seg_exact": True}))
        self.assertTrue(broll.exact_of({}, {"seg_exact": True}))
        self.assertFalse(broll.exact_of({"seg_exact": False}, {"seg_exact": True}))
        self.assertFalse(broll.exact_of({}))


if __name__ == "__main__":
    unittest.main()
