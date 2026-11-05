"""gfx_types.is_full / has_pip: which cards are a separate screen and which put the face cam in the corner.

  python3 -m unittest tests.test_gfx_types
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gfx_types  # after the path insert: the scripts are not a package


class ScreenKindTest(unittest.TestCase):
    def test_a_side_scene_is_beside_the_speaker(self):  # Kamil 2026-11-05: "rzeczy latające dookoła mnie"
        self.assertTrue(gfx_types.is_full({"type": "scene"}))
        self.assertTrue(gfx_types.has_pip({"type": "scene"}))
        side = {"type": "scene", "layout": "side"}
        self.assertFalse(gfx_types.is_full(side))
        self.assertFalse(gfx_types.has_pip(side))
        self.assertTrue(gfx_types.is_full({"type": "scene", "layout": "side", "canvas": "v"}))  # 9:16 has no "side"
        self.assertTrue(gfx_types.beside(side) and gfx_types.beside({"type": "sticker"}))
        self.assertFalse(gfx_types.beside({"type": "float"}) or gfx_types.beside({"type": "kw"}))  # these still stop a punch-in

    def test_stickers_and_floats_are_not_screens(self):
        for t in ("sticker", "float", "kw"):
            self.assertFalse(gfx_types.is_full({"type": t}), t)
            self.assertFalse(gfx_types.has_pip({"type": t}), t)
        self.assertFalse(gfx_types.has_pip({"type": "scene", "pip": False}))
        self.assertFalse(gfx_types.has_pip({"type": "meme", "canvas": "v"}))


if __name__ == "__main__":
    unittest.main()
