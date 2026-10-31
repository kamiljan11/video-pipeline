"""9:16 "meme" card: build_edl.py puts it in the split layout like a 9:16 "web" card and refuses it outside shorts;
memes.py takes only JPEG/PNG pictures from i.imgflip.com and writes the boxes of style/memes.json.

  python3 -m unittest tests.test_meme
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import memes  # after the path insert: the scripts are not a package


class BuildEdlMemeTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="meme-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        words = [(1.0, 1.5, " a"), (1.6, 2.9, " b")]
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round(a * 1000), "to": round(b * 1000)}, "text": t} for a, b, t in words]}))
        (self.d / "rec.sil").write_text("silence_start: 0\nsilence_end: 1.0\n")

    def build(self, spec: dict, **extra):
        (self.d / "specs.json").write_text(json.dumps([{"id": "m1", "type": "meme", "dur": 2.0, "meme": "drake", **spec}]))
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 1]], "edl_out": "edl.json", "vertical": True,
                "gfx": [{"id": "m1", "word": 1}], "gfx_specs": "specs.json", "gfx_dir": str(self.d), **extra}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def overlay(self, spec: dict) -> dict:
        r = self.build(spec)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads((self.d / "edl.json").read_text())["overlays"][0]

    def test_a_meme_is_split_by_default_and_full_on_request(self):
        o = self.overlay({"canvas": "v"})
        self.assertTrue(o["split"])
        self.assertFalse(o["pip"])
        self.assertNotIn("split", self.overlay({"canvas": "v", "layout": "full"}))

    def test_a_meme_outside_a_short_is_a_named_error(self):
        for spec, extra, why in (({}, {}, "canvas"), ({"canvas": "v"}, {"vertical": False}, "vertical"),
                                 ({"canvas": "v", "layout": "side"}, {}, "layout")):
            with self.subTest(spec=spec, extra=extra):
                r = self.build(spec, **extra)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(why, r.stderr)


class MemesToolTest(unittest.TestCase):
    TPL: ClassVar[dict] = {"id": "1", "name": "Drake Hotline Bling", "url": "https://i.imgflip.com/30b1gx.jpg", "width": 1200, "height": 1200}

    def test_only_jpeg_and_png(self):
        self.assertEqual(memes.kind(b"\xff\xd8\xff\xe0rest"), "jpg")
        self.assertEqual(memes.kind(b"\x89PNG\r\n\x1a\nrest"), "png")
        for bad in (b"<html>", b"GIF89a", b""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                memes.kind(bad)

    def test_entry_keeps_our_boxes_and_the_source(self):
        boxes = [[0.5, 0, 0.5, 0.5, "dark"]]
        e = memes.entry("drake", self.TPL, {"boxes": boxes}, "jpg", "2026-10-31")
        self.assertEqual((e["img"], e["width"], e["boxes"], e["source"]), ("drake.jpg", 1200, boxes, self.TPL["url"]))

    def test_a_picture_from_another_host_is_refused(self):
        with self.assertRaises(ValueError):
            memes.entry("drake", {**self.TPL, "url": "https://evil.example/x.jpg"}, {"boxes": []}, "jpg", "2026-10-31")

    def test_catalogue_boxes_are_well_formed(self):
        cat = json.loads((ROOT / "style" / "memes.json").read_text())
        for slug, e in cat.items():
            if slug.startswith("_"): continue
            with self.subTest(slug=slug):
                self.assertRegex(slug, r"^[a-z0-9_]+$")  # gfx/render.mjs accepts only these names
                self.assertTrue(e["imgflip"].isdigit())
                for x, y, w, h, style in e["boxes"]:
                    self.assertTrue(0 <= x < 1 and 0 <= y < 1 and 0 < w <= 1 - x + 1e-9 and 0 < h <= 1 - y + 1e-9, (x, y, w, h))
                    self.assertIn(style, ("dark", "light"))


if __name__ == "__main__":
    unittest.main()
