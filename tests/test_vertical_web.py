"""9:16 "web" card: build_edl.py marks a "split" card (face box under the card, captions in the gap, no corner PiP),
checks "layout"; assemble.py draws the face box over the card with rounded top corners, only while the card is on.

  python3 -m unittest tests.test_vertical_web   (needs ffmpeg; about 15 s)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import edl_guard  # after the path insert: the scripts are not a package
from gfx_types import SPLIT

DUR = 2.0


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class BuildEdlSplitTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="vertical-web-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        words = [(1.0, 1.5, " a"), (1.6, 2.9, " b"), (4.05, 4.5, " c")]
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round(a * 1000), "to": round(b * 1000)}, "text": t} for a, b, t in words]}))
        (self.d / "rec.sil").write_text("silence_start: 0\nsilence_end: 1.0\nsilence_start: 4.6\nsilence_end: 6\n")

    def build(self, spec: dict, **extra):
        (self.d / "specs.json").write_text(json.dumps([{"id": "w1", "type": "web", "dur": 1.5, "url": "https://example.com/", **spec}]))
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 2]], "edl_out": "edl.json", "vertical": True,
                "gfx": [{"id": "w1", "word": 1}], "gfx_specs": "specs.json", "gfx_dir": str(self.d), "ass_out": "c.ass", **extra}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def overlay(self, spec: dict) -> dict:
        r = self.build(spec)
        self.assertEqual(r.returncode, 0, r.stderr)
        (o,) = json.loads((self.d / "edl.json").read_text())["overlays"]
        return o

    def test_a_9_16_web_card_is_split_by_default_without_the_corner_pip(self):
        o = self.overlay({"canvas": "v"})
        self.assertTrue(o["split"])
        self.assertFalse(o["pip"])

    def test_layout_full_has_no_face_box(self):
        self.assertNotIn("split", self.overlay({"canvas": "v", "layout": "full"}))

    def test_a_16_9_web_card_keeps_its_pip(self):  # as before this change
        o = self.overlay({})
        self.assertTrue(o["pip"])
        self.assertNotIn("split", o)

    def test_captions_under_a_split_card_move_into_the_gap(self):
        self.overlay({"canvas": "v"})
        lines = [ln for ln in (self.d / "c.ass").read_text().splitlines() if ln.startswith("Dialogue: 0,")]
        moved = [ln for ln in lines if f"\\pos(540,{SPLIT['caption_y']})" in ln]
        self.assertTrue(moved)  # words b, c are said while the card is on (it starts on word b)
        self.assertLess(len(moved), len(lines))  # word a is said before it: stays where captions always are

    def test_bad_layout_is_a_named_error(self):
        for spec in ({"canvas": "v", "layout": "side"}, {"layout": "full"}, {"canvas": "v", "layout": True}):
            with self.subTest(spec=spec):
                r = self.build(spec)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("layout", r.stderr)


class AssembleSplitTest(unittest.TestCase):
    """red speaker, an opaque blue card from 0.5 s to 1.5 s: inside the face box red, around it blue, before the card red"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vertical-web-mix-"))
        cls.src = cls.tmp / "src.mp4"
        ffmpeg("-f", "lavfi", "-i", f"color=c=red:s=640x360:r=30:d={DUR}", "-f", "lavfi", "-i", f"sine=f=220:d={DUR}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src))
        cls.card = cls.tmp / "card.mov"
        ffmpeg("-f", "lavfi", "-i", "color=c=blue:s=1080x1920:r=30:d=1", "-c:v", "prores_ks", "-profile:v", "4444",
               "-pix_fmt", "yuva444p10le", str(cls.card))
        edl = {"sources": {"A": str(cls.src)}, "segments": [{"src": "A", "in": 0.0, "out": DUR}], "w": 1080, "h": 1920,
               "src_w": 640, "src_h": 360, "vertical": True, "out_name": "final.mp4", "seg_exact": True,
               "overlays": [{"file": str(cls.card), "at": 0.5, "dur": 1.0, "id": "w1", "pip": False, "split": True}]}
        assert edl_guard.problems(edl) == []
        (cls.tmp / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(cls.tmp / "edl.json"), str(cls.tmp), "--proxy"],
                           capture_output=True, text=True, check=False)
        assert r.returncode == 0, r.stderr[-2000:]
        cls.video = cls.tmp / "final.mp4"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    def rgb(self, t: float, x: int, y: int) -> tuple[int, int, int]:
        """colour at (x, y) of the 1080x1920 frame; the proxy is 360x640, so a 3x3 px patch there"""
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(self.video), "-frames:v", "1",
                              "-vf", f"crop=3:3:{x // 3 - 1}:{y // 3 - 1},format=rgb24", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        return tuple(sum(raw[i::3]) // 9 for i in range(3))  # type: ignore[return-value]

    def red(self, c):
        return c[0] > 150 and c[2] < 100

    def blue(self, c):
        return c[2] > 150 and c[0] < 100

    def test_face_box_shows_the_speaker_inside_the_card(self):
        bx, by, bw, bh = SPLIT["face_box"]
        self.assertTrue(self.red(self.rgb(1.0, bx + bw // 2, by + bh // 2)))  # in the box: the speaker
        self.assertTrue(self.blue(self.rgb(1.0, 540, 600)))  # above it: the card
        self.assertTrue(self.blue(self.rgb(1.0, bx + 6, by + 6)))  # the rounded top-left corner: card, not speaker

    def test_without_the_card_the_frame_is_the_speaker(self):
        self.assertTrue(self.red(self.rgb(0.2, 540, 600)))
        self.assertTrue(self.red(self.rgb(1.8, 540, 600)))


if __name__ == "__main__":
    unittest.main()
