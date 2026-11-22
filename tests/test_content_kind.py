"""content_kind.py / kind.py: which rule set a film follows (one person vs two people), Kamil 2026-11-22, ADR-0032."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import content_kind as ck
import kind


class Classify(unittest.TestCase):
    def test_two_faces_in_most_frames_is_talk(self):
        self.assertEqual(ck.classify([2] * 20 + [1] * 4, 0.6), ("talk", True))

    def test_one_face_in_most_frames_is_solo(self):
        self.assertEqual(ck.classify([1] * 22 + [0, 2], 0.6), ("solo", True))

    def test_mixed_is_solo_but_not_clear(self):  # a night run must not stop: the rules films had before, with a WARN
        self.assertEqual(ck.classify([0] * 10 + [1] * 7 + [2] * 7, 0.6), ("solo", False))

    def test_no_frame_stops(self):
        with self.assertRaises(SystemExit): ck.classify([], 0.6)


class Cfg(unittest.TestCase):
    def test_the_repo_file_loads(self):
        c = ck.load_cfg()
        self.assertEqual(set(c), {"samples", "min_face", "share"}); self.assertGreater(c["samples"], 0)

    def test_a_bad_share_stops(self):
        f = Path(tempfile.mkdtemp()) / "c.json"; f.write_text(json.dumps({"samples": 24, "min_face": 0.08, "share": 0.3}))
        with self.assertRaises(SystemExit): ck.load_cfg(f)


class BigFacesAndTimes(unittest.TestCase):
    def test_small_faces_in_the_back_do_not_count(self):
        dets = [[0, 0, 50, 0.20 * ck.H], [0, 0, 50, 0.10 * ck.H], [0, 0, 10, 0.03 * ck.H]]
        self.assertEqual(ck.big_faces(dets, 0.08), 2)
        self.assertEqual(ck.big_faces(None, 0.08), 0)

    def test_times_spread_over_the_whole_recording(self):
        self.assertEqual(ck.times(100.0, 4), [12.5, 37.5, 62.5, 87.5])


class FromPlan(unittest.TestCase):
    def test_values(self):
        self.assertIsNone(kind.from_plan({}))
        self.assertTrue(kind.from_plan({"podcast": True})); self.assertTrue(kind.from_plan({"podcast": {"speakers": ["A", "B"]}}))
        self.assertFalse(kind.from_plan({"podcast": False})); self.assertFalse(kind.from_plan({"podcast": None}))
        with self.assertRaises(SystemExit): kind.from_plan({"podcast": "yes"})


class IsTalk(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); (self.d / "rec.mp4").write_bytes(b"x" * 10)
        self.plan = {"src": "rec.mp4"}

    def put(self, k, key=None):
        (self.d / "content_kind.json").write_text(json.dumps({"sources": {"rec.mp4": {"kind": k, "key": key or kind.key(self.d, self.plan)}}}))

    def test_plan_key_wins_over_the_measurement(self):
        self.put("talk")
        self.assertFalse(kind.is_talk({**self.plan, "podcast": False}, self.d))

    def test_measurement_without_plan_key(self):
        self.put("talk"); self.assertTrue(kind.is_talk(self.plan, self.d))
        self.put("solo"); self.assertFalse(kind.is_talk(self.plan, self.d))

    def test_nothing_is_solo(self):
        self.assertFalse(kind.is_talk(self.plan, self.d))

    def test_another_recording_in_the_file_is_not_this_one(self):
        (self.d / "content_kind.json").write_text(json.dumps({"sources": {"long.mp4": {"kind": "talk"}}}))
        self.assertFalse(kind.is_talk(self.plan, self.d))

    def test_a_stale_or_broken_file_stops(self):
        self.put("talk", key={"src": "rec.mp4", "size": 1, "mtime": 0, "version": kind.VERSION})
        with self.assertRaises(SystemExit): kind.is_talk(self.plan, self.d)
        (self.d / "content_kind.json").write_text("{\"sources\": ")
        with self.assertRaises(SystemExit): kind.is_talk(self.plan, self.d)


class Main(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); (self.d / "rec.mp4").write_bytes(b"x" * 10)
        (self.d / "plan.json").write_text(json.dumps({"src": "rec.mp4"}))

    def run_main(self, faces):
        det = mock.Mock(); det.detect.side_effect = [(None, np.array([[0, 0, 50, 0.2 * ck.H]] * n) if n else None) for n in faces]
        cv2 = mock.Mock(); cv2.FaceDetectorYN.create.return_value = det
        with mock.patch.dict(sys.modules, {"cv2": cv2}), mock.patch.object(ck, "duration", return_value=240.0), \
                mock.patch.object(ck, "frame", return_value=None), mock.patch.object(ck, "load_cfg", return_value={"samples": 4, "min_face": 0.08, "share": 0.6}):
            return ck.main([str(self.d), "plan.json"]), det.detect.call_count

    def test_measures_once_then_reads_the_cache(self):
        self.assertEqual(self.run_main([2, 2, 2, 1]), (0, 4))
        self.assertTrue(kind.is_talk({"src": "rec.mp4"}, self.d))
        self.assertEqual(self.run_main([]), (0, 0))  # cached: no frame read

    def test_a_changed_recording_is_measured_again(self):
        self.run_main([2, 2, 2, 2])
        os.utime(self.d / "rec.mp4", (1, 1))
        self.assertEqual(self.run_main([1, 1, 1, 1]), (0, 4))
        self.assertFalse(kind.is_talk({"src": "rec.mp4"}, self.d))

    def test_not_clear_writes_solo_with_clear_false(self):
        self.run_main([0, 1, 2, 0])
        e = json.loads((self.d / "content_kind.json").read_text())["sources"]["rec.mp4"]
        self.assertEqual((e["kind"], e["clear"]), ("solo", False))

    def test_skips_a_plan_that_says_podcast(self):
        (self.d / "plan.json").write_text(json.dumps({"podcast": True, "src": "missing.mp4"}))
        self.assertEqual(ck.main([str(self.d), "plan.json"]), 0)
        self.assertFalse((self.d / "content_kind.json").exists())


if __name__ == "__main__":
    unittest.main()
