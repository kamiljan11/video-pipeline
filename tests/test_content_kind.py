"""content_kind.py / kind.py: which rule set a film follows (one person vs two people), Kamil 2026-11-22."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import content_kind as ck
import kind


class Classify(unittest.TestCase):
    def test_two_faces_in_most_frames_is_talk(self):
        self.assertEqual(ck.classify([2] * 20 + [1] * 4), "talk")

    def test_one_face_in_most_frames_is_solo(self):
        self.assertEqual(ck.classify([1] * 22 + [0, 2]), "solo")

    def test_mixed_stops_with_the_counts(self):
        with self.assertRaises(SystemExit) as e: ck.classify([0] * 10 + [1] * 7 + [2] * 7)
        self.assertIn("not clear", str(e.exception)); self.assertIn("{0: 10, 1: 7, 2: 7}", str(e.exception))

    def test_no_frame_stops(self):
        with self.assertRaises(SystemExit): ck.classify([])


class BigFaces(unittest.TestCase):
    def test_small_faces_in_the_back_do_not_count(self):
        h = ck.H
        dets = [[0, 0, 50, 0.20 * h], [0, 0, 50, 0.10 * h], [0, 0, 10, 0.03 * h]]
        self.assertEqual(ck.big_faces(dets), 2)

    def test_none_is_zero(self):
        self.assertEqual(ck.big_faces(None), 0)


class Times(unittest.TestCase):
    def test_samples_spread_over_the_keeps_only(self):
        words = [(float(i), i + 1.0, "x") for i in range(100)]
        ts = ck.times({"keeps": [[0, 9], [50, 59]]}, words, n=4)  # keeps = 0..10 s and 50..60 s
        self.assertEqual(len(ts), 4)
        self.assertTrue(all(0 <= t <= 10 or 50 <= t <= 60 for t in ts), ts)
        self.assertEqual(sum(t < 10 for t in ts), 2)

    def test_without_keeps_all_words(self):
        words = [(0.0, 1.0, "a"), (9.0, 10.0, "b")]
        self.assertEqual(ck.times({}, words, n=2), [2.5, 7.5])


class IsTalk(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def test_plan_key_wins_over_the_measurement(self):
        (self.d / "content_kind.json").write_text(json.dumps({"kind": "talk"}))
        self.assertFalse(kind.is_talk({"podcast": False}, self.d))
        self.assertTrue(kind.is_talk({"podcast": {"names": ["A", "B"]}}, self.d))

    def test_measurement_without_plan_key(self):
        (self.d / "content_kind.json").write_text(json.dumps({"kind": "talk"}))
        self.assertTrue(kind.is_talk({}, self.d))
        (self.d / "content_kind.json").write_text(json.dumps({"kind": "solo"}))
        self.assertFalse(kind.is_talk({}, self.d))

    def test_nothing_is_solo(self):
        self.assertFalse(kind.is_talk({}, self.d))

    def test_main_skips_a_plan_that_says_podcast(self):
        (self.d / "plan.json").write_text(json.dumps({"podcast": True, "src": "missing.mp4"}))
        self.assertEqual(ck.main([str(self.d), "plan.json"]), 0)
        self.assertFalse((self.d / "content_kind.json").exists())


if __name__ == "__main__":
    unittest.main()
