"""music_check.py: the music is heard under the voice (2026-11-14 fragment: the bed sat 48 dB under it)."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import music_check

SR = 16000


def tone(db: float, secs: float) -> np.ndarray:
    t = np.arange(int(secs * SR)) / SR
    return (10 ** (db / 20) * np.sqrt(2) * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


class MusicCheckTest(unittest.TestCase):
    def over(self, voice_db: float, bed_db: float) -> dict:
        return music_check.measure(tone(voice_db, 6), tone(bed_db, 6), SR)

    def test_a_bed_48_db_under_the_voice_is_not_heard(self):
        m = self.over(-16, -64)
        self.assertAlmostEqual(m["over"], 48, delta=0.5)
        self.assertIn("not heard", music_check.judge(m))

    def test_a_bed_20_db_under_the_voice_passes(self):
        self.assertEqual(music_check.judge(self.over(-16, -36)), "")

    def test_a_bed_close_to_the_voice_is_too_loud(self):
        self.assertIn("too loud", music_check.judge(self.over(-16, -24)))

    def test_pauses_are_measured_apart_and_no_speech_is_named(self):
        voice = np.concatenate([tone(-16, 3), np.zeros(3 * SR, np.float32)])
        m = music_check.measure(voice, tone(-30, 6), SR)
        self.assertAlmostEqual(m["bed_pause"], -30, delta=0.5)
        self.assertEqual(music_check.judge(music_check.measure(np.zeros(SR, np.float32), tone(-30, 1), SR)), "no speech measured")


if __name__ == "__main__":
    unittest.main()
