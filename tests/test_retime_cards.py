"""retime_cards.py: card pieces follow the cut (2026-11-15: sentences put back and air between sentences)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import retime_cards as rc

OLD = {"segments": [{"in": 10.0, "out": 14.0}, {"in": 20.0, "out": 30.0}], "overlays": [{"id": "s", "at": 2.0}, {"id": "f", "at": 3.0}]}
# the sentence 14-20 s put back, a 0.5 s pause before 25 s kept: the words after 14 s come 6 s later, after 25 s 6.5 s later
NEW = {"segments": [{"in": 10.0, "out": 24.5}, {"in": 24.5, "out": 25.0}, {"in": 25.0, "out": 30.0}],
       "overlays": [{"id": "s", "at": 2.0}, {"id": "f", "at": 3.0}]}


class RetimeTest(unittest.TestCase):
    def test_source_and_film_seconds_both_ways(self):
        self.assertEqual(rc.film_to_source(OLD["segments"], 5.0), 21.0)
        self.assertEqual(rc.source_to_film(OLD["segments"], 21.0), 5.0)
        self.assertEqual(rc.source_to_film(OLD["segments"], 16.0), 4.0)  # left out: the next piece kept
        self.assertEqual(rc.source_to_film([{"in": 50.0, "out": 60.0}, {"in": 0.0, "out": 10.0}], 5.0), 15.0)  # out of source order

    def test_a_scene_follows_the_words_and_text_stays_text(self):
        sp = {"id": "s", "type": "scene", "dur": 8.0, "els": [{"k": "chip", "t": "jak kompilator", "at": 1.0},
              {"k": "file", "at": 3.0, "rows": [{"t": "x", "mark_at": 4.0}]}], "cam": [{"t": 0}, {"t": 3.0}]}
        self.assertEqual(rc.retime(OLD, NEW, [sp]), ["s: 3 timings, dur 8.0 -> 14.0"])
        self.assertEqual(sp["els"][0], {"k": "chip", "t": "jak kompilator", "at": 1.0})  # said before the put-back sentence
        self.assertEqual(sp["els"][1]["at"], 9.0); self.assertEqual(sp["els"][1]["rows"][0]["mark_at"], 10.0)
        self.assertEqual(sp["cam"][1]["t"], 9.0)

    def test_a_float_keeps_its_easing_and_its_loops(self):
        h = ('<div style="animation:flinr 0.5s cubic-bezier(.2,1.2,.4,1) 0.30s both"></div>'
             '<div style="animation:fldrop 0.5s cubic-bezier(.2,1.2,.4,1) 3.00s both, flbob 1.4s ease-in-out infinite"></div>')
        sp = {"id": "f", "type": "float", "dur": 5.0, "html": h}
        rc.retime(OLD, NEW, [sp])
        self.assertIn("cubic-bezier(.2,1.2,.4,1) 0.30s both", sp["html"])
        self.assertIn("cubic-bezier(.2,1.2,.4,1) 9.00s both, flbob 1.4s ease-in-out infinite", sp["html"])
        self.assertEqual(sp["dur"], 11.0)  # its end at source 24 s, before the kept pause

    def test_other_cards_and_cards_of_one_cut_only_are_left_alone(self):
        kw = {"id": "s", "type": "kw", "dur": 2.0}
        gone = {"id": "x", "type": "scene", "dur": 3.0, "els": [{"at": 2.0}]}
        self.assertEqual(rc.retime(OLD, NEW, [kw, gone]), [])
        self.assertEqual(gone["els"][0]["at"], 2.0)


if __name__ == "__main__":
    unittest.main()
