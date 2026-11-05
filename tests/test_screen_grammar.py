"""screen_grammar.screen_pass: memes and simple scenes go beside the speaker, cards hold their reading time, close
separate screens join (Kamil 2026-11-05, style/REF-long-negacz.md).

  python3 -m unittest tests.test_screen_grammar
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import screen_grammar as G  # after the path insert: the scripts are not a package


def scene(i, n, dur, **more):
    return {"id": i, "type": "scene", "dur": dur, "els": [{"k": "chip", "text": "x"}] * n, **more}


class ScreenPassTest(unittest.TestCase):
    def run_pass(self, cards, drop=None):
        logs = []
        specs, shift = G.screen_pass(cards, drop, log=logs.append)
        return {sp["id"]: sp for sp in specs}, shift, logs

    def test_memes_and_simple_scenes_go_beside_him(self):
        cards = [(0.0, {"id": "m1", "type": "meme", "dur": 4, "meme": "drake", "text": ["a"]}), (10.0, scene("s1", 3, 8, bg="blobs")),
                 (30.0, scene("s2", 9, 8)), (50.0, scene("s3", 2, 8, pip=False))]
        out, _, _ = self.run_pass(cards)
        self.assertEqual(out["m1"]["type"], "sticker")
        self.assertEqual(out["s1"].get("layout"), "side")
        self.assertNotIn("bg", out["s1"])  # the board, not the full-screen background
        self.assertNotIn("layout", out["s2"])  # 9 pieces: too much beside him, a separate screen
        self.assertNotIn("layout", out["s3"])  # "pip": false asked for the whole frame
        self.assertEqual(cards[0][1]["type"], "meme")  # the plan's own cards are untouched (the shorts use them)

    def test_a_meme_without_sticker_crops_stays_a_meme(self):
        # review 2026-11-05: render.mjs stops a "sticker" whose template has no crops (always_has_been has none)
        self.assertFalse(G.has_sticker("always_has_been"))
        self.assertFalse(G.has_sticker("no_such_template"))
        out, _, _ = self.run_pass([(0.0, {"id": "m2", "type": "meme", "dur": 4, "meme": "always_has_been", "text": ["a"]})])
        self.assertEqual(out["m2"]["type"], "meme")
        out, _, _ = self.run_pass([(0.0, scene("s4", 3, 8, cam="none"))])
        self.assertNotIn("layout", out["s4"])  # scene_lib refuses layout "side" with cam "none"
        tied = {"id": "s5", "type": "scene", "dur": 8, "els": [{"k": "chip", "text": "a"}, {"k": "line", "from": [0, 0], "to": [9, 9]}]}
        out, _, _ = self.run_pass([(0.0, tied)])
        self.assertNotIn("layout", out["s5"])  # a line ties two pieces: it cannot stack into the column beside him

    def test_a_card_is_held_to_its_reading_time_and_starts_earlier_when_it_must(self):
        kw = {"id": "k1", "type": "kw", "dur": 2.0, "text": "jedno dwa trzy cztery pięć sześć"}  # needs 1.2 x 4 + 0.35 x 2 = 5.5
        out, shift, _ = self.run_pass([(0.0, scene("s0", 9, 12)), (12.05, kw), (16.1, scene("s9", 9, 8))])
        self.assertAlmostEqual(out["k1"]["dur"], 5.5, places=2)
        self.assertAlmostEqual(shift["k1"], -1.5)  # 4.0 s of room after it: SHIFT_MAX (1.5 s) more before it
        self.assertLessEqual(out["s0"]["dur"], 12 - 0.5)  # taken from the 12 s scene, which keeps its own 6 s
        self.assertGreaterEqual(out["s0"]["dur"], 6.0)

    def test_a_map_with_no_room_is_dropped_and_close_screens_join(self):
        cards = [(0.0, scene("s1", 9, 10)), (10.5, scene("m1_mapa", 9, 2.0)), (12.5, scene("s2", 9, 10)), (24.0, scene("s3", 9, 6))]
        out, _, logs = self.run_pass(cards, drop={"s3": "said twice"})
        self.assertNotIn("m1_mapa", out)  # 2 s of room, a map needs 6
        self.assertTrue(any("m1_mapa dropped" in m for m in logs) and any("s3 left out" in m for m in logs))
        self.assertAlmostEqual(out["s1"]["dur"], 12.5)  # then 2.5 s of face between s1 and s2 (< 3 s): one block
        out2, _, _ = self.run_pass([(0.0, scene("a", 9, 10)), (13.0, scene("b", 9, 10))])
        self.assertAlmostEqual(out2["a"]["dur"], 10.0)  # 3 s of face: the speaker is back, two blocks

    def test_a_lower_third_does_not_cut_a_side_card_short(self):
        out, _, _ = self.run_pass([(0.0, scene("s1", 3, 3.0)), (4.0, {"id": "low", "type": "lower", "dur": 5, "text": "Kamil"})])
        self.assertAlmostEqual(out["s1"]["dur"], 6.0)  # beside him, right; the lower third sits bottom left


if __name__ == "__main__":
    unittest.main()
