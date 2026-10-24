"""behind.py (text behind the speaker), run with matte/.venv/bin/python -m unittest matte/test_behind.py from ~/video-pipeline
(the panel suite runs it: panel/tests/test_behind.py). A fake matting model on a synthetic film whose every frame has its
own grey level, so the test sees WHICH film frame the model got for each card frame."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import behind

W, H = 64, 36




class FakeMatter:
    """the left half is "the person"; records the grey level of every frame it is given"""
    seen: ClassVar[list[int]] = []

    def __init__(self, ratio):
        FakeMatter.seen = []

    def __call__(self, rgb):
        FakeMatter.seen.append(round(float(rgb.mean())))
        p = np.zeros(rgb.shape[:2], np.float32)
        p[:, : rgb.shape[1] // 2] = 1
        return p


class GreyMatter(FakeMatter):
    """the whole frame is "person" as much as the frame is bright: card frame k's alpha tells which film frame it got"""

    def __call__(self, rgb):
        super().__call__(rgb)
        return np.full(rgb.shape[:2], float(rgb.mean()) / 255, np.float32)


@unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
class BehindTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="behind-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        self.src = self.d / "src.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"nullsrc=s={W}x{H}:r=30:d=2,geq=lum='16+N*3':cb=128:cr=128",
                        "-c:v", "ffv1", str(self.src)], check=True)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.src), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        self.grey = [round(float(f.mean())) for f in np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)]  # source frame n
        (self.d / "gfx").mkdir()
        self.card(1.0)
        self.edl = {"sources": {"A": str(self.src)}, "w": W, "h": H, "src_w": W, "src_h": H, "face": [0.5, 0.5], "seg_exact": True,
                    "segments": [{"src": "A", "in": 0.0, "out": 0.5, "zoom": 1.0}, {"src": "A", "in": 1.0, "out": 2.0, "zoom": 1.0}],
                    "overlays": [{"id": "b", "at": 0.3, "dur": 20 / 30}]}
        self.write_edl()
        self.spec = {"id": "b", "type": "float", "behind": {"edl": "edl.json"}}

    def card(self, a: float):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=white@{a}:s={W}x{H}:r=30:d={20 / 30},format=rgba",
                        "-frames:v", "20", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(self.d / "gfx" / "b.mov")],
                       check=True)

    def write_edl(self):
        (self.d / "edl.json").write_text(json.dumps(self.edl))

    def run_once(self):
        return behind.process(self.spec, self.d / "gfx", self.d, matter_for=FakeMatter)

    def test_the_person_is_cut_out_and_the_rest_of_the_card_stays(self):
        self.assertIn("cut out of 20 frames", self.run_once())
        rgba = behind.card_frames(self.d / "gfx" / "b.mov", (W, H))
        self.assertEqual(len(rgba), 20)
        self.assertLessEqual(int(rgba[:, :, : W // 2, 3].max()), 1)    # the speaker's side: see-through
        self.assertGreaterEqual(int(rgba[:, :, W // 2 :, 3].min()), 254)  # elsewhere: the card as rendered
        self.assertTrue((self.d / "gfx" / "b.front.mov").exists())

    def test_each_card_frame_is_matched_with_the_film_frame_under_it(self):
        self.run_once()
        # card at 0.3 s = film frame 9; warm-up from frame 0 (1 s before, clipped); film frames 0..14 = source 0..14,
        # 15.. = source 30.. (second segment starts at 1.0 s); the model saw film frames 0..28 in order
        film = [*range(15), *range(30, 44)]
        self.assertEqual(len(FakeMatter.seen), 29)
        for got, n in zip(FakeMatter.seen, film, strict=True):
            self.assertAlmostEqual(got, self.grey[n], delta=1, msg=n)

    def test_each_card_frame_gets_the_matte_of_its_own_film_frame(self):
        behind.process(self.spec, self.d / "gfx", self.d, matter_for=GreyMatter)
        film = [*range(15), *range(30, 44)]
        alpha = behind.card_frames(self.d / "gfx" / "b.mov", (W, H))[..., 3].mean(axis=(1, 2))
        for k, a in enumerate(alpha):
            self.assertAlmostEqual(float(a), 255 - self.grey[film[9 + k]], delta=2, msg=k)

    def test_nothing_changed_nothing_redone(self):
        self.run_once()
        with mock.patch.object(FakeMatter, "__call__", side_effect=AssertionError("matted again")):
            self.assertIn("up to date", self.run_once())

    def test_a_changed_edl_window_cuts_out_again_from_the_rendered_card(self):
        self.run_once()
        front = hashlib.sha256((self.d / "gfx" / "b.front.mov").read_bytes()).hexdigest()
        self.edl["segments"][1]["in"] = 1.2
        self.write_edl()
        self.assertIn("cut out", self.run_once())
        self.assertEqual(hashlib.sha256((self.d / "gfx" / "b.front.mov").read_bytes()).hexdigest(), front)
        self.assertAlmostEqual(FakeMatter.seen[15], self.grey[36], delta=1)

    def test_a_newly_rendered_card_becomes_the_new_front(self):
        self.run_once()
        self.card(0.5)  # render.mjs wrote a new b.mov (spec changed)
        new = hashlib.sha256((self.d / "gfx" / "b.mov").read_bytes()).hexdigest()
        self.assertIn("cut out", self.run_once())
        self.assertEqual(hashlib.sha256((self.d / "gfx" / "b.front.mov").read_bytes()).hexdigest(), new)
        rgba = behind.card_frames(self.d / "gfx" / "b.mov", (W, H))
        self.assertAlmostEqual(int(rgba[0, 0, -1, 3]), 128, delta=2)

    def test_a_card_not_in_the_edl_is_left_alone(self):
        self.edl["overlays"] = []
        self.write_edl()
        self.assertIn("not in", self.run_once())
        self.assertFalse((self.d / "gfx" / "b.front.mov").exists())

    def test_only_the_verified_model_file_is_loaded(self):
        bad = self.d / "model.onnx"
        bad.write_bytes(b"not the model")
        with mock.patch.object(behind, "MODEL", bad), self.assertRaises(SystemExit) as e:
            behind.Matter(0.2)
        self.assertIn("sha256", str(e.exception))
        with mock.patch.object(behind, "MODEL", self.d / "none.onnx"), self.assertRaises(SystemExit):
            behind.Matter(0.2)


class CutOutTest(unittest.TestCase):
    def test_alpha_times_not_person(self):
        rgba = np.full((1, 4, 4), 200, np.uint8)
        out = behind.cut_out(rgba, np.array([[0.0, 0.5, 1.0, 1.5]], np.float32))
        self.assertEqual(out[0, :, 3].tolist(), [200, 100, 0, 0])
        self.assertEqual(out[0, :, :3].tolist(), rgba[0, :, :3].tolist())


if __name__ == "__main__":
    unittest.main()
