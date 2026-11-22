"""cutout.py: a meme's character without its background for the "sticker" card with "cut": true (visual upgrade item 6)."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import cutout

MATTE_PY = ROOT / "matte" / ".venv" / "bin" / "python"


def picture(d: Path, slug: str, rgb: np.ndarray, crops: list) -> None:
    """a picture placed by hand (its own json carries the crops; no catalogue entry for this slug)"""
    h, w = rgb.shape[:2]
    rgba = np.dstack([rgb, np.full((h, w), 255, np.uint8)])
    cutout.write_png(rgba, d / f"{slug}.png")
    (d / f"{slug}.json").write_text(json.dumps({"name": slug, "img": f"{slug}.png", "width": w, "height": h, "boxes": [], "sticker": crops}))


class CutoutTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="cutout-")); self.addCleanup(shutil.rmtree, self.d)
        self.cat = self.d / "memes.json"; self.cat.write_text("{}")

    def test_a_plain_background_goes_and_the_character_stays(self):
        rgb = np.full((200, 400, 3), 250, np.uint8)
        rgb[50:150, 60:140] = (220, 30, 30)    # left crop: a red figure
        rgb[40:160, 250:350] = (30, 30, 220)   # right crop: a blue one
        picture(self.d, "two", rgb, [[0, 0, 0.5, 1], [0.5, 0, 0.5, 1]])
        c = cutout.cut("two", "flat", self.d, self.cat)
        out = cutout.read_rgba(self.d / "two.cut.png")
        self.assertEqual(int(out[100, 100, 3]), 255)  # the figure
        self.assertEqual(int(out[5, 5, 3]), 0)        # the background
        self.assertEqual(c["src_sha256"], hashlib.sha256((self.d / "two.png").read_bytes()).hexdigest())
        self.assertEqual(json.loads((self.d / "two.json").read_text())["cut"]["file"], "two.cut.png")
        self.assertAlmostEqual(c["cover"][0], 100 * 80 / (200 * 200), places=2)

    def test_a_busy_background_or_an_empty_crop_fails_by_name(self):
        rng = np.random.default_rng(1)
        picture(self.d, "busy", rng.integers(0, 255, (100, 100, 3), dtype=np.uint8), [[0, 0, 1, 1]])
        with self.assertRaisesRegex(cutout.CutError, r"crop 0: the border is not one plain colour"):
            cutout.cut("busy", "flat", self.d, self.cat)
        picture(self.d, "empty", np.full((100, 100, 3), 250, np.uint8), [[0, 0, 1, 1]])
        with self.assertRaisesRegex(cutout.CutError, r"crop 0: the cut keeps 0% of it .* nobody found with method flat"):
            cutout.cut("empty", "flat", self.d, self.cat)
        self.assertFalse((self.d / "empty.cut.png").exists())

    def test_alpha_needs_transparency_and_a_picture_needs_its_json(self):
        picture(self.d, "opaque", np.full((50, 50, 3), 9, np.uint8), [[0, 0, 1, 1]])
        with self.assertRaisesRegex(cutout.CutError, r"has no transparency"):
            cutout.cut("opaque", "alpha", self.d, self.cat)
        with self.assertRaisesRegex(cutout.CutError, r"ghost.json missing: python3 memes.py add ghost"):
            cutout.cut("ghost", "flat", self.d, self.cat)

    def test_a_panel_border_inside_the_picture_is_cleared(self):
        rgba = np.zeros((200, 200, 4), np.uint8)
        rgba[60:140, 60:140] = (200, 40, 40, 255)  # one figure across the border between the top and the bottom panel
        cutout.write_png(rgba, self.d / "panels.png")
        (self.d / "panels.json").write_text(json.dumps({"name": "p", "img": "panels.png", "width": 200, "height": 200, "boxes": [],
                                                        "sticker": [[0, 0, 1, 0.5], [0, 0.5, 1, 0.5]]}))
        cutout.cut("panels", "alpha", self.d, self.cat)
        out = cutout.read_rgba(self.d / "panels.cut.png")
        self.assertEqual([int(out[y, 100, 3]) for y in (90, 97, 100, 102, 110)], [255, 0, 0, 0, 255])

    def test_unsafe_names_and_a_transparent_picture_for_the_wrong_method_are_refused(self):
        with self.assertRaisesRegex(cutout.CutError, r"slug '\.\./x' = \[a-z0-9_\]\+"):
            cutout.cut("../x", "flat", self.d, self.cat)
        rgba = np.zeros((100, 100, 4), np.uint8); rgba[30:70, 30:70] = (9, 9, 9, 255)
        cutout.write_png(rgba, self.d / "clear.png")
        (self.d / "clear.json").write_text(json.dumps({"img": "clear.png", "sticker": [[0, 0, 1, 1]]}))
        with self.assertRaisesRegex(cutout.CutError, r"already has transparency: use --method alpha"):
            cutout.cut("clear", "flat", self.d, self.cat)
        (self.d / "clear.json").write_text(json.dumps({"img": "../clear.png", "sticker": [[0, 0, 1, 1]]}))
        with self.assertRaisesRegex(cutout.CutError, r'"img" = <slug>.jpg\|png'):
            cutout.cut("clear", "alpha", self.d, self.cat)

    def test_a_winding_background_on_a_large_crop_is_quick(self):
        rgb = np.full((1000, 1000, 3), 250, np.uint8)
        for x in range(50, 950, 100): rgb[50:950, x:x + 40] = (30, 30, 200)  # comb teeth: the background winds between them
        picture(self.d, "comb", rgb, [[0, 0, 1, 1]])
        import time
        t = time.monotonic(); c = cutout.cut("comb", "flat", self.d, self.cat)
        self.assertLess(time.monotonic() - t, 20)
        self.assertAlmostEqual(c["cover"][0], 9 * 40 * 900 / 1e6, places=2)

    def test_cli_names_the_failure_in_one_line(self):
        r = subprocess.run([sys.executable, str(ROOT / "cutout.py"), "ghost", "--method", "flat"], capture_output=True, text=True,
                           env={"VP_MEMES": str(self.d), "PATH": "/usr/bin:/bin:" + str(Path.home() / ".local/bin")}, check=False)
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"^FAILED cutout ghost: .*ghost.json missing")

    @unittest.skipUnless(MATTE_PY.exists() and (ROOT / "render" / "memes" / "drake.jpg").exists(), "needs matte/.venv and render/memes/drake.jpg")
    def test_people_of_a_real_meme_are_cut_out_by_the_matting_model(self):
        for f in ("drake.jpg", "drake.json"): shutil.copy(ROOT / "render" / "memes" / f, self.d / f)
        r = subprocess.run([str(MATTE_PY), str(ROOT / "cutout.py"), "drake"], capture_output=True, text=True, timeout=600,
                           env={"VP_MEMES": str(self.d), "PATH": "/usr/bin:/bin:" + str(Path.home() / ".local/bin")}, check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cover = json.loads((self.d / "drake.json").read_text())["cut"]["cover"]
        self.assertTrue(all(0.3 < k < 0.9 for k in cover), cover)


if __name__ == "__main__":
    unittest.main()
