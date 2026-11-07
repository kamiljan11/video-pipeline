"""stills.py: film time -> source frame, what is said while a card is up, compositing, the sheet and accept"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stills as S

EDL = {"sources": {"A": "a.mp4", "B": "b.mp4"}, "segments": [{"src": "A", "in": 10.0, "out": 12.0}, {"src": "B", "in": 5.0, "out": 6.0}]}


class TimeTest(unittest.TestCase):
    def test_film_time_maps_through_the_segments(self):
        self.assertEqual(S.source_at(EDL, 0.5), ("a.mp4", 10.5))
        self.assertEqual(S.source_at(EDL, 2.25), ("b.mp4", 5.25))
        self.assertIsNone(S.source_at(EDL, 3.0))

    def test_said_while_the_card_is_up(self):
        words = [(0.1, "raz"), (1.0, "dwa"), (2.0, "trzy")]
        self.assertEqual(S.said(words, 0.5, 2.0), "dwa")
        self.assertEqual(S.said(words, 5, 6), "")


class PictureTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.d = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def test_a_see_through_card_shows_the_frame_an_opaque_one_covers_it(self):
        base = np.full((54, 96, 3), 200, np.uint8)
        rgba = np.zeros((108, 192, 4), np.uint8); rgba[:54, :, :] = (0, 0, 255, 255)  # top half red, bottom see-through
        cv2.imwrite(str(self.d / "a.png"), rgba)
        out = S.over(base, self.d / "a.png")
        self.assertEqual(out.shape, base.shape)
        self.assertEqual(tuple(out[5, 5]), (0, 0, 255)); self.assertEqual(tuple(out[50, 5]), (200, 200, 200))
        cv2.imwrite(str(self.d / "b.png"), np.full((108, 192, 3), 30, np.uint8))  # a full-screen scene: no alpha in the PNG
        self.assertEqual(int(S.over(base, self.d / "b.png")[50, 5, 0]), 30)
        (self.d / "c.png").write_text("not a picture")
        with self.assertRaises(RuntimeError): S.over(base, self.d / "c.png")

    def test_cells_make_a_two_column_sheet_and_polish_letters_do_not_break_it(self):
        c = S.cell(np.zeros((540, 304, 3), np.uint8), "s1  0:03.2", "Zażółć gęślą jaźń " * 12)
        self.assertEqual(c.shape, (S.CELL[1] + S.CAPTION, S.CELL[0], 3))
        self.assertEqual(S.sheet([c, c, c]).shape, (2 * c.shape[0], 2 * c.shape[1], 3))
        self.assertEqual(S.wrap("a b c", 3), ["a b", "c"])

    def test_a_card_past_the_film_end_says_so_on_its_still(self):
        work = self.d / "w"; gfx = work / "gfx"; sd = gfx / "stills"; sd.mkdir(parents=True)
        cv2.imwrite(str(sd / "k.png"), np.zeros((1440, 2560, 4), np.uint8)); (sd / "k.t").write_text("1.0"); (sd / "k.key").write_text("x")
        (work / "edl.json").write_text(json.dumps({"segments": [{"src": "A", "in": 0, "out": 2}], "sources": {"A": "a.mp4"},
                                                   "overlays": [{"file": str(gfx / "k.mov"), "id": "k", "at": 5, "dur": 2}]}))
        (work / "w.json").write_text(json.dumps({"transcription": []}))
        (work / "specs.json").write_text(json.dumps([{"id": "k", "type": "kw", "dur": 2}]))
        plan = work / "plan.json"; plan.write_text(json.dumps({"edl_out": "edl.json", "words": "w.json", "gfx_specs": "specs.json"}))
        real = S.subprocess.run
        S.subprocess.run = lambda *a, **k: None  # render.mjs --stills: the PNG is already there
        try:
            S.make(plan)
        finally:
            S.subprocess.run = real
        self.assertIn("[no source frame]", (sd / "sheet.md").read_text())
        self.assertEqual(json.loads((sd / "scope.json").read_text()), ["k"])
        self.assertEqual(json.loads((sd / "accepted.json").read_text()), {})

    def test_accept_copies_the_render_keys_and_names_a_card_without_a_still(self):
        work = self.d / "work"; sd = work / "gfx" / "stills"; sd.mkdir(parents=True)
        (sd / "s1.key").write_text("k1"); (sd / "s2.key").write_text("k2")
        (work / "edl.json").write_text(json.dumps({"segments": [], "sources": {}, "overlays": [{"file": str(work / "gfx" / "s1.mov"), "id": "s1"}]}))
        (work / "w.json").write_text(json.dumps({"transcription": []}))
        plan = work / "plan.json"; plan.write_text(json.dumps({"edl_out": "edl.json", "words": "w.json"}))
        self.assertEqual(S.accept(plan, ["s1"]), ["s1"])
        self.assertEqual(json.loads((sd / "accepted.json").read_text()), {"s1": "k1"})
        self.assertEqual(S.accept(plan, ["--all"]), ["s1", "s2"])
        self.assertEqual(json.loads((sd / "accepted.json").read_text()), {"s1": "k1", "s2": "k2"})
        with self.assertRaises(ValueError): S.accept(plan, ["s9"])
        self.assertEqual(S.main(["accept", str(plan), "s9"]), 1)
        self.assertEqual(S.main([]), 2)


if __name__ == "__main__":
    unittest.main()
