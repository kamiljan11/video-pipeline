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
        ffmpeg("-f", "lavfi", "-i", f"sine=f=440:d={DUR + 1}", "-ac", "2", str(cls.tmp / "music.wav"))
        ffmpeg("-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={DUR + 1}", str(cls.tmp / "sfx.wav"))

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

    def music_db_under_voice(self, **duck) -> float:
        """level of the 440 Hz music under the 220 Hz voice in the final mix (dBFS RMS)"""
        v = self.render(music=str(self.tmp / "music.wav"), sfx=str(self.tmp / "sfx.wav"), music_db=-12, **duck)
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-ss", "0.5", "-t", "1", "-i", str(v), "-af",
                            "bandpass=f=440:width_type=q:w=8,bandpass=f=440:width_type=q:w=8,astats=measure_overall=RMS_level:measure_perchannel=none",
                            "-f", "null", "-"], capture_output=True, text=True, check=True)
        return float(r.stderr.rsplit("RMS level dB:", 1)[1].split()[0])

    def test_music_duck_reaches_the_sidechain(self):
        none = self.music_db_under_voice(music_duck={"ratio": 1})  # ratio 1 = no ducking
        hard = self.music_db_under_voice(music_duck={"threshold": 0.001, "ratio": 20})
        default = self.music_db_under_voice()  # 0.015 / 6
        self.assertGreater(none - hard, 10, (none, default, hard))
        self.assertGreater(none - default, 3, (none, default, hard))
        self.assertGreater(default - hard, 1, (none, default, hard))

    def test_segment_cache_follows_face_target_y(self):
        """a re-render into the same folder after a face_target_y change cuts the segments again (not the old head line)"""
        out = Path(tempfile.mkdtemp(dir=self.tmp))
        names = []
        for ty in (0.35, 0.55, 0.35):
            edl = {"sources": {"A": str(self.src)}, "segments": [{"src": "A", "in": 0.0, "out": DUR, "zoom": 1.3, "face": [0.5, 0.5]}],
                   "w": 180, "h": 320, "src_w": W, "src_h": H, "vertical": True, "face_target_y": ty, "out_name": "final.mp4"}
            self.assertEqual(edl_guard.problems(edl), [])
            (out / "edl.json").write_text(json.dumps(edl))
            r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(out / "edl.json"), str(out)],
                               capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            names.append((out / "concat.txt").read_text())
        self.assertNotEqual(names[0], names[1])
        self.assertEqual(names[0], names[2])  # same value: the cache still works
        self.assertEqual(len(list((out / "segs").glob("*.mkv"))), 2)

    def test_without_face_target_y_segment_names_stay_as_before(self):  # old EDLs keep their cached segments
        names = [p.name for p in (self.render().parent / "segs").glob("*.mkv")]
        self.assertEqual(names, ["0000_0.000_2.000_1.0__x.mkv"])

    def test_guard_refuses_bad_music_duck(self):
        base = {"sources": {"A": "a.mp4"}, "segments": [{"src": "A", "in": 0.0, "out": 1.0}]}
        for bad in ({"threshold": 0}, {"threshold": 0.0001}, {"threshold": 2}, {"ratio": 0.5}, {"ratio": 30}, {"ratio": "6"}, {"knee": 2},
                    {"ratio": True}, [0.05, 2.5], "0.05", None):
            with self.subTest(bad=bad):
                self.assertTrue(any("music_duck" in p for p in edl_guard.problems({**base, "music_duck": bad})))
        for ok in ({"threshold": 0.05, "ratio": 2.5}, {"threshold": edl_guard.DUCK_MIN_THRESHOLD}, {}):
            self.assertEqual(edl_guard.problems({**base, "music_duck": ok}), [], ok)

    def test_build_edl_refuses_them_at_plan_time(self):
        for key, bad in (("progress", "Fill"), ("music_duck", {"threshold": 0})):
            with self.subTest(key=key):
                d = Path(tempfile.mkdtemp(dir=self.tmp))
                (d / "rec.cw.json").write_text(json.dumps({"transcription": [{"offsets": {"from": 1000, "to": 1500}, "text": " a"}]}))
                (d / "rec.sil").write_text("")
                (d / "plan.json").write_text(json.dumps({"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4",
                                                         "keeps": [[0, 0]], "edl_out": "edl.json", key: bad}))
                r = subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=d, capture_output=True,
                                   text=True, check=False)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(f"{key}:", r.stderr)

    def test_guard_progress_values(self):
        base = {"sources": {"A": "a.mp4"}, "segments": [{"src": "A", "in": 0.0, "out": 1.0}]}
        for ok in (True, False, "fill"):
            self.assertEqual(edl_guard.problems({**base, "progress": ok}), [], ok)
        for bad in ("Fill", "true", 1.5, None):
            with self.subTest(bad=bad):
                self.assertTrue(any("progress" in p for p in edl_guard.problems({**base, "progress": bad})))


if __name__ == "__main__":
    unittest.main()
