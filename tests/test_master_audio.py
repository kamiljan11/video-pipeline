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
        finally:
            M.master = real
        self.assertEqual(self.film.stat().st_size, size)
        self.assertFalse(Path(film + ".master.mp4").exists())

    def test_usage_and_a_broken_file(self):
        self.assertEqual(M.main([]), 2)
        bad = self.d / "bad.mp4"; bad.write_text("x")
        self.assertEqual(M.main([str(bad), str(self.d / "o.mp4")]), 1)


if __name__ == "__main__":
    unittest.main()
