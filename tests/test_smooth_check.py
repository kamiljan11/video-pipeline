"""smooth_check.py: keyframe pulse, doubled frames, uneven timestamps (U12, Kamil 2026-11-22 "klatkowanie co pare sekund")."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import smooth_check as sc

RNG = np.random.default_rng(1)


def moving(n: int, amp: float = 1.0) -> np.ndarray:
    """changes of a picture that moves a little every frame"""
    return np.abs(RNG.normal(0.6, 0.1, n)) * amp


class Pulse(unittest.TestCase):
    def test_a_keyframe_that_jumps_is_measured(self):
        d = moving(600); keys = [0, 250, 500]
        for k in keys[1:]: d[k - 1] = 0.6 * 2.5
        p, used = sc.pulse(d, keys)
        self.assertEqual(used, [250, 500]); self.assertGreater(p, 2.0)

    def test_a_cut_and_a_still_picture_are_not_pulses(self):
        d = moving(600); d[249] = 30.0  # a cut on the keyframe
        d[440:520] = 0.0; d[499] = 0.5  # still picture
        self.assertEqual(sc.pulse(d, [250, 500]), (0.0, []))

    def test_an_even_encode_passes(self):
        p, _ = sc.pulse(moving(600), [250, 500])
        self.assertLess(p, 1.8)


class Doubled(unittest.TestCase):
    def test_a_repeated_frame_in_motion_is_found(self):
        d = moving(300); d[100] = 0.0
        self.assertEqual(sc.doubled(d), [101])

    def test_a_still_shot_is_not_doubled_frames(self):
        d = np.zeros(300)
        self.assertEqual(sc.doubled(d), [])

    def test_a_move_that_starts_or_stops_is_not_doubled_frames(self):
        d = np.r_[np.zeros(50), moving(50) + 0.5, np.zeros(50)]  # hold, move, hold (dry3: 57 of 71)
        self.assertEqual(sc.doubled(d), [])

    def test_a_black_frame_between_two_fades_is_not_doubled(self):
        d = moving(100) + 0.5; d[50] = 0.0
        flat = np.zeros(101, bool); flat[51] = True  # frame 51 equals frame 50, both black
        self.assertEqual(sc.doubled(d, flat), [])
        self.assertEqual(sc.doubled(d), [51])


class Uneven(unittest.TestCase):
    def test_constant_rate_passes_and_a_gap_is_named(self):
        ts = [i / 30 for i in range(100)]
        self.assertEqual(sc.uneven(ts, 30), [])
        ts2 = ts[:50] + [t + 1 / 30 for t in ts[50:]]  # one frame shown twice as long
        self.assertEqual(sc.uneven(ts2, 30), [round(ts[49], 3)])


class Unmeasurable(unittest.TestCase):
    def test_a_still_film_warns_that_the_pulse_was_not_measured(self):
        f = Path(tempfile.mkdtemp()) / "still.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=gray:size=160x90:rate=30:duration=3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f)], check=True)
        from io import StringIO
        from unittest import mock
        with mock.patch("sys.stdout", new=StringIO()) as out:
            self.assertEqual(sc.main([str(f)]), 0)
        self.assertIn("WARN smooth: keyframe pulse not measurable", out.getvalue())


class OnAFile(unittest.TestCase):
    def test_a_smooth_cfr_clip_passes_and_a_vfr_one_fails(self):
        d = Path(tempfile.mkdtemp())
        ok, bad = d / "ok.mp4", d / "bad.mp4"
        src = ["-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=12"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(ok)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-vf", "setpts='PTS+if(gte(N,150),1/30/TB,0)'", "-fps_mode", "passthrough",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bad)], check=True)
        self.assertEqual(sc.main([str(ok)]), 0)
        self.assertEqual(sc.main([str(bad)]), 1)


if __name__ == "__main__":
    unittest.main()
