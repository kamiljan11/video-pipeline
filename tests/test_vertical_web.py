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
from gfx_types import CORNER, SPLIT

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

    def build(self, spec: dict, lead: float = 0.0, **extra):
        (self.d / "specs.json").write_text(json.dumps([{"id": "w1", "type": "web", "dur": 1.5, "url": "https://example.com/", **spec}]))
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 2]], "edl_out": "edl.json", "vertical": True,
                "gfx": [{"id": "w1", "word": 1, "lead": lead}], "gfx_specs": "specs.json", "gfx_dir": str(self.d), "ass_out": "c.ass", **extra}
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

    def test_a_9_16_scene_takes_the_float_layouts(self):  # the long's animated explainer drawn for a short (scene_lib canvas "v")
        o = self.overlay({"type": "scene", "canvas": "v", "layout": "split", "els": []})
        self.assertTrue(o["split"]); self.assertFalse(o["pip"])
        o = self.overlay({"type": "scene", "canvas": "v", "layout": "corner", "els": []})
        self.assertTrue(o["corner"]); self.assertNotIn("split", o)
        for spec in ({"type": "scene", "canvas": "v"}, {"type": "scene", "canvas": "v", "layout": "full"}):
            with self.subTest(spec=spec):
                r = self.build(spec)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("layout", r.stderr)

    def test_layout_full_has_no_face_box(self):
        self.assertNotIn("split", self.overlay({"canvas": "v", "layout": "full"}))

    def test_a_16_9_web_card_keeps_its_pip(self):  # as before this change
        r = self.build({}, vertical=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        (o,) = json.loads((self.d / "edl.json").read_text())["overlays"]
        self.assertTrue(o["pip"])
        self.assertNotIn("split", o)

    def test_captions_under_a_split_card_move_into_the_gap(self):
        self.overlay({"canvas": "v"})
        lines = [ln for ln in (self.d / "c.ass").read_text().splitlines() if ln.startswith("Dialogue: 0,")]
        moved = [ln for ln in lines if f"\\pos(540,{SPLIT['caption_y']})" in ln]
        self.assertTrue(moved)  # words b, c are said while the card is on (it starts on word b)
        self.assertLess(len(moved), len(lines))  # word a is said before it: stays where captions always are

    def test_a_line_said_before_the_card_ends_where_the_card_comes_in(self):  # not at the old spot over the face box
        r = self.build({"canvas": "v"}, lead=-0.3)
        self.assertEqual(r.returncode, 0, r.stderr)
        at = json.loads((self.d / "edl.json").read_text())["overlays"][0]["at"]
        first = next(ln for ln in (self.d / "c.ass").read_text().splitlines() if ln.startswith("Dialogue: 0,"))
        h, m, sec = first.split(",")[2].split(":")
        self.assertLessEqual(int(h) * 3600 + int(m) * 60 + float(sec), at + 0.01)

    def test_a_9_16_web_card_in_a_16_9_film_is_a_named_error(self):  # no box and no PiP there: the face would vanish
        r = self.build({"canvas": "v"}, vertical=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("vertical", r.stderr)

    def test_bad_layout_is_a_named_error(self):
        for spec in ({"canvas": "v", "layout": "side"}, {"canvas": "v", "layout": True}):
            with self.subTest(spec=spec):
                r = self.build(spec)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("layout", r.stderr)
        r = self.build({"layout": "full"}, vertical=False)  # layout on a 16:9 card
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("layout", r.stderr)

    def test_box_keys_reach_the_edl_with_or_without_an_own_box(self):
        keys = {"face_zoom": 0.62, "face_anchor": 0.4, "caption_y": 1100}
        for extra in ({}, {"face_box": [80, 1100, 920, 820]}):
            with self.subTest(extra=extra):
                o = self.overlay({"canvas": "v", **keys, **extra})
                self.assertEqual({k: o[k] for k in keys}, keys)

    def test_a_box_value_ffmpeg_cannot_use_is_a_named_error(self):  # face_zoom 0 divided by zero in assemble.py
        for k, bad in (("face_zoom", 0), ("face_zoom", 1.5), ("face_anchor", 2), ("caption_y", "x"), ("caption_y", True)):
            with self.subTest(**{k: bad}):
                r = self.build({"canvas": "v", k: bad})
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(k, r.stderr)

    def test_a_bad_gfx_lead_is_a_named_error(self):  # plan "gfx_lead": refused at plan time, like "tail"
        for bad in ("x", True, 0.5, -3):
            with self.subTest(gfx_lead=bad):
                r = self.build({"canvas": "v"}, gfx_lead=bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("gfx_lead", r.stderr)
        self.assertEqual(self.build({"canvas": "v"}, gfx_lead=-0.12).returncode, 0)

    def test_master_key_reaches_the_edl_and_bad_values_are_named(self):  # plan "master": master_audio.py from assemble.py
        self.assertEqual(self.build({"canvas": "v"}, master={"lufs": -14, "tp": -1.5}).returncode, 0)
        self.assertEqual(json.loads((self.d / "edl.json").read_text())["master"], {"lufs": -14, "tp": -1.5})
        self.assertEqual(self.build({"canvas": "v"}).returncode, 0)
        self.assertNotIn("master", json.loads((self.d / "edl.json").read_text()))  # absent: assemble.py as before
        for bad in ({"lufs": 0}, {"tp": 1}, {"lufs": "x"}, {"loud": -14}, "yes", {"tp": True}):
            with self.subTest(master=bad):
                r = self.build({"canvas": "v"}, master=bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("master", r.stderr)

    def test_face_corner_and_no_fade_out_flags(self):
        o = self.overlay({"canvas": "v", "layout": "full", "face_corner": True, "no_fade_out": True})
        self.assertTrue(o["corner"]); self.assertTrue(o["no_fade_out"]); self.assertNotIn("split", o)

    def test_captions_under_a_corner_card_sit_above_the_circle(self):
        self.overlay({"type": "scene", "canvas": "v", "layout": "corner", "els": []})
        self.assertIn(f"\\pos(540,{CORNER['caption_y']})", (self.d / "c.ass").read_text())


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


class AssembleCornerZoomTest(unittest.TestCase):
    """the two other 9:16 face layouts: a box with face_zoom < 1 (smaller picture on its blurred copy) from 0.2 s to 0.9 s,
    then a full card with the face in the corner circle from 1.1 s to 1.9 s"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vertical-corner-"))
        src = cls.tmp / "src.mp4"
        ffmpeg("-f", "lavfi", "-i", f"color=c=red:s=640x360:r=30:d={DUR}", "-f", "lavfi", "-i", f"sine=f=220:d={DUR}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src))
        card = cls.tmp / "card.mov"
        ffmpeg("-f", "lavfi", "-i", "color=c=blue:s=1080x1920:r=30:d=1", "-c:v", "prores_ks", "-profile:v", "4444",
               "-pix_fmt", "yuva444p10le", str(card))
        cls.box = [80, 1100, 920, 820]
        edl = {"sources": {"A": str(src)}, "segments": [{"src": "A", "in": 0.0, "out": DUR}], "w": 1080, "h": 1920,
               "src_w": 640, "src_h": 360, "vertical": True, "out_name": "final.mp4", "seg_exact": True,
               "overlays": [{"file": str(card), "at": 0.2, "dur": 0.7, "id": "z", "pip": False, "split": True,
                             "face_box": cls.box, "face_zoom": 0.6, "face_anchor": 0.4},
                            {"file": str(card), "at": 1.1, "dur": 0.8, "id": "c", "pip": False, "corner": True, "no_fade_out": True}]}
        assert edl_guard.problems(edl) == []
        (cls.tmp / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(cls.tmp / "edl.json"), str(cls.tmp), "--proxy"],
                           capture_output=True, text=True, check=False)
        assert r.returncode == 0, r.stderr[-2000:]
        cls.video = cls.tmp / "final.mp4"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    rgb, red, blue = AssembleSplitTest.rgb, AssembleSplitTest.red, AssembleSplitTest.blue

    def test_zoomed_out_box_shows_the_speaker_on_the_card(self):
        bx, by, bw, bh = self.box
        self.assertTrue(self.red(self.rgb(0.6, bx + bw // 2, by + bh // 2)))
        self.assertTrue(self.red(self.rgb(0.6, bx + 20, by + bh // 2)))  # the blurred copy fills the box to its side edge
        self.assertTrue(self.blue(self.rgb(0.6, 540, 600)))

    def test_corner_circle_holds_the_face_and_the_card_fills_the_rest(self):
        x, y, d = CORNER["x"], CORNER["y"], CORNER["size"]
        self.assertTrue(self.red(self.rgb(1.5, x + d // 2, y + d // 2)))
        self.assertTrue(self.blue(self.rgb(1.5, 540, 600)))
        self.assertFalse(self.red(self.rgb(1.5, x + 4, y + 4)))  # the square's corner is outside the circle


if __name__ == "__main__":
    unittest.main()
