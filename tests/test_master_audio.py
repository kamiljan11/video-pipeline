"""master_audio.py: a too loud, clipping mix comes out at -14 LUFS with true peak <= -1.5 dBTP, the video untouched"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import master_audio as M


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.d = Path(self.t.name)
        self.film = self.d / "loud.mp4"  # 20 s: pink noise with hot peaks over a test picture
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=160x90:r=25:d=20",
                        "-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.9:d=20,volume=6dB", "-shortest",
                        "-c:v", "libx264", "-c:a", "aac", "-b:a", "256k", str(self.film)], check=True)

    def tearDown(self):
        self.t.cleanup()

    def test_a_hot_mix_lands_on_target_and_the_video_is_copied(self):
        before = M.measure(str(self.film))
        self.assertGreater(before["tp"], -1.0)  # the fixture clips, as film 2 did
        out = self.d / "mastered.mp4"
        r = subprocess.run([sys.executable, str(ROOT / "master_audio.py"), str(self.film), str(out)], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rep = json.loads(out.with_suffix(".master.json").read_text())
        self.assertLessEqual(abs(rep["after"]["lufs"] + 14), 0.5, rep)
        self.assertLessEqual(rep["after"]["tp"], -1.5, rep)
        probe = lambda f: subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=size",
                                          "-of", "csv=p=0", str(f)], capture_output=True, text=True, check=True).stdout
        self.assertEqual(probe(self.film), probe(out))  # same video packets: copied, not re-encoded

    def test_in_place_replaces_the_film_or_keeps_it_and_leaves_no_temp(self):  # assemble.py's EDL "master" step
        film = str(self.film)
        rep = M.master_in_place(film, {})  # {} = the defaults
        self.assertTrue(rep["ok"])
        self.assertLessEqual(M.measure(film)["tp"], -1.5)
        self.assertTrue(self.film.with_suffix(".master.json").exists())
        self.assertFalse(Path(film + ".master.mp4").exists())
        size = self.film.stat().st_size
        real = M.master
        try:
            M.master = lambda f, o, lufs, tp: {**real(f, o, lufs, tp), "ok": False}  # off target
            with self.assertRaises(SystemExit) as e: M.master_in_place(film, {"lufs": -14})
            self.assertIn("unmastered file kept", str(e.exception))
            def broken(f, o, lufs, tp):
                Path(o).write_text("half"); raise RuntimeError("ffmpeg died")
            M.master = broken
            with self.assertRaises(SystemExit) as e: M.master_in_place(film, {})
            self.assertIn("ffmpeg died", str(e.exception))
            def no_json(f, o, lufs, tp):
                Path(o).write_text("half"); raise ValueError("substring not found")  # loudnorm printed no JSON block
            M.master = no_json
            with self.assertRaises(SystemExit) as e: M.master_in_place(film, {})
            self.assertIn("FAILED master", str(e.exception))
        finally:
            M.master = real
        self.assertEqual(self.film.stat().st_size, size)
        self.assertFalse(Path(film + ".master.mp4").exists())

    def test_a_limiter_that_takes_loudness_gets_one_correction_pass(self):
        calls, real = [], (M.measure, M._apply)
        try:
            M.measure = lambda f: {"lufs": -10.0, "tp": 2.0}
            M._apply = lambda f, o, gain, tp: calls.append(gain) or {"lufs": -14.8 if len(calls) == 1 else -14.1, "tp": -2.0}
            rep = M.master("in.mp4", "out.mp4")
        finally:
            M.measure, M._apply = real
        self.assertEqual([round(g, 2) for g in calls], [-4.0, -3.2])  # the 0.8 LU the limiter took is added once
        self.assertTrue(rep["ok"]); self.assertEqual(rep["gain_db"], -3.2)

    def test_aac_overshoot_tries_the_next_margin(self):  # film 2026-11-04 long: limiter -2.0 gave -0.2 dBTP after AAC
        calls, real = [], (M.measure, M._apply)
        aac = {-2.0: -0.2, -3.0: -2.3}  # measured, AAC is not linear in the ceiling
        try:
            M.measure = lambda f: {"lufs": -14.6, "tp": -1.3}
            M._apply = lambda f, o, gain, ceiling: calls.append(ceiling) or {"lufs": -14.1, "tp": aac[round(ceiling, 1)]}
            rep = M.master("in.mp4", "out.mp4")
        finally:
            M.measure, M._apply = real
        self.assertEqual([round(c, 2) for c in calls], [-2.0, -3.0])
        self.assertTrue(rep["ok"], rep); self.assertEqual(rep["ceiling_db"], -3.0); self.assertEqual(len(rep["tried"]), 2)

    def test_a_peak_that_never_fits_fails_after_every_margin(self):
        calls, real = [], (M.measure, M._apply)
        try:
            M.measure = lambda f: {"lufs": -14.0, "tp": 0.0}
            M._apply = lambda f, o, gain, ceiling: calls.append(ceiling) or {"lufs": -14.0, "tp": 0.5}  # a broken limiter
            rep = M.master("in.mp4", "out.mp4")
        finally:
            M.measure, M._apply = real
        self.assertEqual(len(calls), len(M.MARGINS))
        self.assertFalse(rep["ok"])

    def test_usage_and_a_broken_file(self):
        self.assertEqual(M.main([]), 2)
        bad = self.d / "bad.mp4"; bad.write_text("x")
        self.assertEqual(M.main([str(bad), str(self.d / "o.mp4")]), 1)


if __name__ == "__main__":
    unittest.main()
