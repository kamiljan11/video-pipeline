"""dejudder.py on synthetic frames (no ffmpeg, no camera): a square moving 8 px per frame, some frames repeated.

Run: cd ~/video-pipeline && .venv/bin/python -m unittest tests.test_dejudder
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dejudder  # after the path: the script directory is not a package

W, H = 320, 180


def frame(x: int) -> bytes:
    y = np.full((H, W), 40, np.uint8)
    y[60:120, x:x + 40] = 220
    return y.tobytes() + np.full(W * H // 2, 128, np.uint8).tobytes()


def square_x(buf: bytes) -> float:
    y = dejudder.planes(buf, W, H)[0][60:120].astype(float) - 40
    cols = y.sum(axis=0)
    return float((cols * np.arange(W)).sum() / cols.sum()) - 19.5  # left edge of the square


def run(xs: list[int]) -> tuple[list[bytes], dict[str, int]]:
    stats = {"fixed": 0, "stalls": 0}
    return list(dejudder.repaired(iter([frame(x) for x in xs]), W, H, stats)), stats


class RepairTest(unittest.TestCase):
    def test_a_repeated_frame_becomes_the_in_between_position(self):
        out, stats = run([0, 8, 16, 16, 32, 40])  # the camera skipped x=24, ffmpeg repeated x=16
        self.assertEqual(len(out), 6)  # timing kept: same frame count
        self.assertEqual(stats["fixed"], 1)
        self.assertAlmostEqual(square_x(out[3]), 24, delta=2)
        self.assertEqual(out[2], frame(16))  # real frames pass through untouched
        self.assertEqual(out[4], frame(32))

    def test_two_repeats_are_spread_evenly(self):
        out, stats = run([0, 8, 8, 8, 32, 40])
        self.assertEqual(stats["fixed"], 2)
        self.assertAlmostEqual(square_x(out[2]), 16, delta=2)
        self.assertAlmostEqual(square_x(out[3]), 24, delta=2)

    def test_a_stall_longer_than_max_run_is_left_alone(self):
        xs = [0, 8] + [8] * (dejudder.MAX_RUN + 1) + [48]
        out, stats = run(xs)
        self.assertEqual(stats, {"fixed": 0, "stalls": 1})
        self.assertEqual(out, [frame(x) for x in xs])

    def test_repeats_at_the_end_and_a_still_picture_stay(self):
        out, stats = run([0, 8, 8])
        self.assertEqual(out, [frame(0), frame(8), frame(8)])  # no next frame to move towards
        self.assertEqual(stats["fixed"], 0)

    def test_real_motion_is_not_taken_for_a_repeat(self):
        small = [dejudder.small_luma(frame(x), W, H) for x in (0, 1)]
        self.assertFalse(dejudder.is_repeat(small[0], small[1]))  # even 1 px of motion is far above the threshold
        self.assertTrue(dejudder.is_repeat(small[0], small[0]))


if __name__ == "__main__":
    unittest.main()
