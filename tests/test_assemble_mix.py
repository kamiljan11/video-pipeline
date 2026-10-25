"""assemble.py: the progress bar fills with the film time, music_duck reaches sidechaincompress, edl_guard checks it.

  python3 -m unittest tests.test_assemble_mix   (needs ffmpeg; about 10 s)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import edl_guard  # after the path insert: the scripts are not a package

W, H, DUR = 320, 180, 2.0


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class AssembleMixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="assemble-mix-"))
        cls.src = cls.tmp / "src.mp4"
        ffmpeg("-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30:d={DUR}", "-f", "lavfi", "-i", f"sine=f=220:d={DUR}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src))
        for name in ("music", "sfx"):
            ffmpeg("-f", "lavfi", "-i", f"sine=f=440:d={DUR + 1}", "-ac", "2", str(cls.tmp / f"{name}.wav"))

    def render(self, **keys) -> Path:
        out = Path(tempfile.mkdtemp(dir=self.tmp))
        edl = {"sources": {"A": str(self.src)}, "segments": [{"src": "A", "in": 0.0, "out": DUR}], "w": W, "h": H,
               "src_w": W, "src_h": H, "out_name": "final.mp4", "seg_exact": True, **keys}
        self.assertEqual(edl_guard.problems(edl), [])
        (out / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(out / "edl.json"), str(out)],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return out / "final.mp4"

    def bar_px(self, video: Path, t: float) -> int:
        """lit pixels in the middle row of the bottom 8 px at time t"""
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(video), "-frames:v", "1",
                              "-vf", f"crop={W}:1:0:{H - 4},format=gray", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        return sum(1 for b in raw if b > 60)

    def test_progress_fill_grows_with_time(self):
        v = self.render(progress="fill")
        widths = [self.bar_px(v, t) for t in (0.5, 1.0, 1.5)]
        for got, want in zip(widths, (W * 0.25, W * 0.5, W * 0.75)):
            self.assertAlmostEqual(got, want, delta=W * 0.06, msg=widths)

    def test_progress_true_is_the_old_full_bar(self):  # kept for old EDLs (test_pipeline_compat)
        v = self.render(progress=True)
        self.assertEqual([self.bar_px(v, t) for t in (0.5, 1.5)], [W, W])

    def test_no_progress_key_no_bar(self):
        self.assertEqual(self.bar_px(self.render(), 1.5), 0)

    def test_music_duck_renders(self):
        mix = {"music": str(self.tmp / "music.wav"), "sfx": str(self.tmp / "sfx.wav"), "music_db": -12}
        for duck in ({}, {"threshold": 0.05, "ratio": 2.5}, {"ratio": 3}):
            with self.subTest(duck=duck):
                self.assertTrue(self.render(**mix, **({"music_duck": duck} if duck else {})).stat().st_size > 0)

    def test_guard_refuses_bad_music_duck(self):
        base = {"sources": {"A": "a.mp4"}, "segments": [{"src": "A", "in": 0.0, "out": 1.0}]}
        for bad in ({"threshold": 0}, {"threshold": 0.0001}, {"threshold": 2}, {"ratio": 0.5}, {"ratio": 30}, {"ratio": "6"}, {"knee": 2},
                    {"ratio": True}, [0.05, 2.5], "0.05", None):
            with self.subTest(bad=bad):
                self.assertTrue(any("music_duck" in p for p in edl_guard.problems({**base, "music_duck": bad})))
        for ok in ({"threshold": 0.05, "ratio": 2.5}, {"threshold": edl_guard.DUCK_MIN_THRESHOLD}, {}):
            self.assertEqual(edl_guard.problems({**base, "music_duck": ok}), [], ok)

    def test_guard_progress_values(self):
        base = {"sources": {"A": "a.mp4"}, "segments": [{"src": "A", "in": 0.0, "out": 1.0}]}
        for ok in (True, False, "fill"):
            self.assertEqual(edl_guard.problems({**base, "progress": ok}), [], ok)
        for bad in ("Fill", "true", 1.5, None):
            with self.subTest(bad=bad):
                self.assertTrue(any("progress" in p for p in edl_guard.problems({**base, "progress": bad})))


if __name__ == "__main__":
    unittest.main()
