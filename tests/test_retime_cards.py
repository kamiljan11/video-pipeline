"""retime_cards.py: card pieces follow the cut (2026-11-15: sentences put back and air between sentences)."""
import json
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

    def test_a_new_cut_built_without_cards_starts_each_card_where_its_old_start_lands(self):
        bare = {"segments": NEW["segments"]}
        sp = {"id": "s", "type": "scene", "dur": 8.0, "els": [{"k": "chip", "at": 1.0}, {"k": "file", "at": 3.0}]}
        self.assertEqual(rc.retime(OLD, bare, [sp]), ["s: 1 timings, dur 8.0 -> 14.0"])
        self.assertEqual([e["at"] for e in sp["els"]], [1.0, 9.0])
        sp2 = {"id": "s", "type": "scene", "dur": 1.0, "els": [{"at": 0.5}]}
        self.assertEqual(rc.retime({"segments": OLD["segments"], "overlays": [{"id": "s", "at": 4.5}]},
                                   {"segments": [{"in": 10.0, "out": 14.0}]}, [sp2]), [])  # its start is cut: left alone


    def test_a_card_over_a_moved_piece_is_left_alone_and_named(self):  # 2026-11-15 f_nie_wierzy: 3.65 s -> 51 s
        moved = {"segments": [{"in": 20.0, "out": 24.0}, {"in": 10.0, "out": 14.0}], "overlays": [{"id": "f", "at": 1.0}]}
        sp = {"id": "f", "type": "float", "dur": 5.0, "html": '<div style="animation:a 0.5s ease 2.00s both"></div>'}
        self.assertEqual(rc.retime(moved, {"segments": [{"in": 10.0, "out": 24.0}]}, [sp]),
                         ["f: LEFT ALONE, the old cut plays its words out of recording order: time it by hand"])
        self.assertEqual(sp["dur"], 5.0)


    def test_a_card_starting_just_before_a_cut_belongs_to_the_piece_after_it(self):  # 2026-11-15 f_nie_wierzy
        old = {"segments": [{"in": 10.0, "out": 14.0}, {"in": 40.0, "out": 50.0}], "overlays": [{"id": "f", "at": 3.6}]}
        bare = {"segments": [{"in": 10.0, "out": 20.0}, {"in": 40.0, "out": 50.0}]}
        sp = {"id": "f", "type": "float", "dur": 3.0, "html": '<div style="animation:a 0.5s ease 1.60s both"></div>'}
        rc.retime(old, bare, [sp])
        self.assertAlmostEqual(sp["dur"], 3.0, delta=0.5)


    def test_the_card_start_stays_at_zero_and_nothing_goes_negative(self):  # 2026-11-15 s_szlaban cam[0].t
        old = {"segments": [{"in": 10.0, "out": 14.0}, {"in": 40.0, "out": 50.0}], "overlays": [{"id": "s", "at": 3.6}]}
        bare = {"segments": [{"in": 10.0, "out": 20.0}, {"in": 40.0, "out": 50.0}]}
        sp = {"id": "s", "type": "scene", "dur": 3.0, "cam": [{"t": 0}, {"t": 0.2}], "els": [{"at": 2.0}]}
        rc.retime(old, bare, [sp])
        self.assertEqual(sp["cam"][0]["t"], 0)
        self.assertGreaterEqual(sp["cam"][1]["t"], 0.0)



class MainTest(unittest.TestCase):
    def test_a_second_run_keeps_the_first_backup(self):  # pg-review 2026-11-15: .bak was overwritten
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "old.json").write_text(json.dumps(OLD)); (d / "new.json").write_text(json.dumps(NEW))
        sp = d / "specs.json"; sp.write_text(json.dumps([{"id": "s", "type": "scene", "dur": 8.0, "els": [{"at": 3.0}]}]))
        for _ in range(2): rc.main([str(d / "old.json"), str(d / "new.json"), str(sp)])
        self.assertEqual(json.loads((d / "specs.json.bak").read_text())[0]["els"][0]["at"], 3.0)
        self.assertTrue((d / "specs.json.bak1").exists())


if __name__ == "__main__":
    unittest.main()
