"""music/gen_music.py palettes (--palette, --key): another piece of music per film; without them the old bed, unchanged.

  .venv/bin/python -m unittest tests.test_music_palette
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "music" / "gen_music.py"


def mono(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).mean(1)


class PaletteTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="pal-"))
        self.addCleanup(shutil.rmtree, self.d, True)

    def gen(self, name, *args):
        out = self.d / name
        r = subprocess.run([sys.executable, str(GEN), str(out), "12", *args], capture_output=True, text=True, check=False)
        return r, out

    def test_palettes_are_different_music(self):
        tracks = {}
        for pal in ("lofi", "drive", "cinematic", "tech", "bright"):
            r, out = self.gen(f"{pal}.wav", "5", "--palette", pal)
            self.assertEqual(r.returncode, 0, r.stderr)
            tracks[pal] = mono(out)
        r, out = self.gen("classic.wav", "5")
        tracks["classic"] = mono(out)
        names = list(tracks)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                x, y = tracks[a], tracks[b]; n = min(len(x), len(y))
                self.assertLess(abs(np.corrcoef(x[:n], y[:n])[0, 1]), 0.5, f"{a} vs {b} sound alike")

    def test_key_moves_the_music(self):
        _, a = self.gen("k0.wav", "5", "--palette", "lofi", "--key", "0")
        _, b = self.gen("k3.wav", "5", "--palette", "lofi", "--key", "3")
        x, y = mono(a), mono(b)
        self.assertLess(abs(np.corrcoef(x, y)[0, 1]), 0.5)

    def test_flags_work_with_moods_and_bad_values_stop_by_name(self):
        r, _ = self.gen("m.wav", "5", '[[0, "story"], [6, "upbeat"]]', "--palette", "drive", "--key", "-3")
        self.assertEqual(r.returncode, 0, r.stderr)
        r, _ = self.gen("x.wav", "5", "--palette", "nosuch")
        self.assertNotEqual(r.returncode, 0); self.assertIn("--palette", r.stderr)
        r, _ = self.gen("y.wav", "5", "--palette", "lofi", "--key", "9")
        self.assertNotEqual(r.returncode, 0); self.assertIn("--key", r.stderr)

    def test_without_a_palette_the_old_bed_is_unchanged(self):
        # the generator before palettes (commit 40ffa83), kept as a file: CI checks out without history
        old = ROOT / "tests" / "fixtures" / "gen_music_40ffa83.py"
        a, b = self.d / "old.wav", self.d / "new.wav"
        subprocess.run([sys.executable, str(old), str(a), "12", "7"], capture_output=True, check=True)
        subprocess.run([sys.executable, str(GEN), str(b), "12", "7"], capture_output=True, check=True)
        self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()
