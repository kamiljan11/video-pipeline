"""av_check + sync_check: a dropped piece of voice and a piece played off its planned time are caught (film 2026-11-04,
Kamil 2026-11-08: 0.65 s of voice lost at 3.09 s of the long and in 4 shorts; cards placed off the words).

  python3 -m unittest tests.test_av_check   (needs ffmpeg; a few seconds)
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import av_check
import sync_check

VOICE = "aevalsrc='0.5*sin(2*PI*300*t)*gt(sin(2*PI*1.3*t)+0.3*sin(2*PI*3.1*t),0)':d=12"  # on/off bursts: a shape to find


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class AvCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="av-check-"))
        cls.ref = cls.tmp / "ref.mkv"
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=160x90:r=30:d=12", "-f", "lavfi", "-i", VOICE, "-c:v", "libx264",
               "-c:a", "pcm_s16le", str(cls.ref))
        cls.good = cls.tmp / "good.mp4"
        ffmpeg("-i", str(cls.ref), "-c:v", "copy", "-c:a", "aac", str(cls.good))
        cls.hole = cls.tmp / "hole.mp4"  # 0.5 s of sound gone at 1.5 s, the picture runs on: what stage 2 did to the long
        ffmpeg("-i", str(cls.ref), "-filter_complex", "[0:a]atrim=0:1.5,asetpts=PTS-STARTPTS[a1];[0:a]atrim=2.0,asetpts=PTS-STARTPTS+1.5/TB[a2];"
               "[a1][a2]concat=n=2:v=0:a=1[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", str(cls.hole))

    def test_a_clean_film_passes(self):
        self.assertEqual(av_check.check(str(self.good), str(self.ref)), [])

    def test_a_hole_in_the_sound_fails_by_name(self):
        bad = av_check.check(str(self.hole))
        self.assertTrue(any("ms audio packet at 1.4" in b or "ms audio packet at 1.5" in b for b in bad), bad)
        self.assertTrue(any("samples missing or extra" in b for b in bad), bad)

    def test_sound_off_the_reference_fails(self):
        bad = av_check.against_ref(sync_check.envelope(str(self.hole)), sync_check.envelope(str(self.ref)), 60, points=4)
        after = [b for b in bad if float(b.split()[1]) >= 2.0]  # a window across the hole itself reads garbage, still a FAIL
        self.assertGreaterEqual(len(after), 2, bad)
        self.assertTrue(all("-500 ms" in b for b in after), bad)

    def test_main_exit_codes(self):
        self.assertEqual(av_check.main([str(self.good)]), 0)
        self.assertEqual(av_check.main([str(self.hole)]), 1)
        self.assertEqual(av_check.main([]), 2)


class SyncCheckTest(unittest.TestCase):
    def test_find_locates_a_shifted_piece_and_refuses_the_edge(self):
        rng = np.random.default_rng(1)
        film = rng.normal(0, 1, 20000)  # white noise: a piece matches only at its own place
        piece = film[8000:10000]
        got, r = sync_check.find(piece, film, 8.2)
        self.assertIsNotNone(got)
        self.assertAlmostEqual(got or 0.0, 8.0, places=2)
        self.assertGreater(r, 0.99)
        got, r = sync_check.find(piece, film, 9.0)  # the true place is 1.0 s away, outside the 0.6 s search
        self.assertTrue(got is None or r < 0.6, (got, r))

    def test_planned_starts_are_the_sums_of_the_piece_lengths(self):
        edl = {"segments": [{"in": 1.0, "out": 2.5}, {"in": 4.0, "out": 4.5}, {"in": 9.0, "out": 10.0}]}
        self.assertEqual(sync_check.planned_starts(edl), [0.0, 1.5, 2.0])


if __name__ == "__main__":
    unittest.main()
