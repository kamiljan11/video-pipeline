"""fragment.py: a window of a long's plan as its own work folder (Phase 7, long-lite)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fragment

WORDS = [(i * 1.0, i * 1.0 + 0.8) for i in range(40)]  # word i at i s of the recording
# the long plays words 0-9, then 20-29, then 10-14 (out of source order)
KEEPS = [[0, 9, {"t0": 0.0}], [20, 29, {"t0": 19.9, "t1": 29.9}], [10, 14]]
EDL = {"seg_exact": False, "segments": [{"src": "A", "in": 0.0, "out": 10.0}, {"src": "A", "in": 19.9, "out": 29.9},
                                        {"src": "A", "in": 9.9, "out": 14.9}]}
PLAN = {"words": "r.cw.json", "keeps": KEEPS, "gfx_specs": "gfx_specs.json",
        "gfx": [{"id": "a", "word": 3}, {"id": "b", "word": 22}, {"id": "l", "word": 21, "item_words": [23, 27]},
                {"id": "l2", "word": 24, "item_words": [25, 33]}, {"id": "e", "word": "END"}],
        "emph": [{"word": 5}, {"word": 25}], "beats": [{"word": 1}, {"word": 26}],
        "music_moods": [[0, "tension"], [8, "story"], [15, "upbeat"], [25, "drop"]],
        "meme_review": {"b": {}, "a": {}}, "sources": {"a": "x", "b": "y"}, "verified_claims": ["a", "b"]}
SPECS = [{"id": "a"}, {"id": "b", "extends": "z"}, {"id": "z"}, {"id": "l"}, {"id": "l2"}, {"id": "e"}, {"id": "q"}]
STORY = {"parts": [{"id": "p0", "start_word": 0}, {"id": "p1", "start_word": 21}], "beats": [{"word": 2}, {"word": 22}]}


class CutKeepsTest(unittest.TestCase):
    def test_window_follows_play_order_and_clips_the_edges(self):
        self.assertEqual(fragment.cut_keeps(KEEPS, 5, 12), [[5, 9], [20, 29, {"t0": 19.9, "t1": 29.9}], [10, 12]])

    def test_a_clipped_edge_loses_its_measured_time_an_unclipped_one_keeps_it(self):
        self.assertEqual(fragment.cut_keeps(KEEPS, 21, 29), [[21, 29, {"t1": 29.9}]])
        self.assertEqual(fragment.cut_keeps(KEEPS, 20, 25), [[20, 25, {"t0": 19.9}]])

    def test_a_word_outside_the_keeps_or_a_backwards_window_is_refused(self):
        for a, b in ((16, 20), (0, 17), (12, 5)):
            with self.assertRaises(SystemExit): fragment.cut_keeps(KEEPS, a, b)


class CutPlanTest(unittest.TestCase):
    def setUp(self):
        self.p, self.sp, self.st = fragment.cut_plan(PLAN, SPECS, STORY, EDL, WORDS, 20, 29)

    def test_only_what_is_said_in_the_window_stays(self):
        self.assertEqual([g["id"] for g in self.p["gfx"]], ["b", "l", "e"])  # l2: item word 33 is not kept; END stays
        self.assertEqual(self.p["emph"], [{"word": 25}]); self.assertEqual(self.p["beats"], [{"word": 26}])
        self.assertEqual(self.p["meme_review"], {"b": {}}); self.assertEqual(self.p["sources"], {"b": "y"})
        self.assertEqual(self.p["verified_claims"], ["b"])

    def test_specs_of_the_kept_cards_and_what_they_extend(self):
        self.assertEqual([s["id"] for s in self.sp], ["b", "z", "l", "e"])

    def test_story_parts_and_beats_inside_the_window(self):
        st = self.st or {}
        self.assertEqual(st["parts"], [{"id": "p1", "start_word": 21}]); self.assertEqual(st["beats"], [{"word": 22}])

    def test_moods_shift_to_the_window_start_with_the_mood_playing_there(self):
        # word 20 (20.0 s) is 0.1 s into the 2nd piece (film 10.0) -> the window starts at film 10.1
        self.assertEqual(self.p["music_moods"], [[0, "story"], [4.9, "upbeat"]])

    def test_the_long_plan_is_not_changed(self):
        self.assertEqual(len(PLAN["gfx"]), 5); self.assertEqual(PLAN["keeps"][1], [20, 29, {"t0": 19.9, "t1": 29.9}])


class MainTest(unittest.TestCase):
    def test_writes_the_folder_and_refuses_a_used_one(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "src", Path(d) / "dst"; src.mkdir()
            words = {"transcription": [{"offsets": {"from": int(a * 1000), "to": int(b * 1000)}, "text": "w"} for a, b in WORDS]}
            (src / "r.cw.json").write_text(json.dumps(words)); (src / "r.sil").write_text("")
            (src / "plan_long.json").write_text(json.dumps(PLAN)); (src / "edl_long.json").write_text(json.dumps(EDL))
            (src / "gfx_specs.json").write_text(json.dumps(SPECS)); (src / "story.json").write_text(json.dumps(STORY))
            (src / "gfx" / "stills").mkdir(parents=True)
            (src / "gfx" / "stills" / "accepted.json").write_text(json.dumps({"b": "k1", "a": "k2", "q": "k3"}))
            self.assertEqual(fragment.main([str(src), str(dst), "--from-word", "20", "--to-word", "29"]), 0)
            self.assertTrue((dst / "r.cw.json").is_symlink()); self.assertTrue((dst / "r.sil").is_symlink())
            rec = json.loads((dst / "FRAGMENT.json").read_text())
            self.assertEqual((rec["from_word"], rec["to_word"], rec["gfx"]), (20, 29, ["b", "l", "e"]))
            self.assertEqual(json.loads((dst / "plan_long.json").read_text())["keeps"], [[20, 29, {"t0": 19.9, "t1": 29.9}]])
            self.assertEqual(json.loads((dst / "gfx" / "stills" / "accepted.json").read_text()), {"b": "k1"})  # window cards only
            with self.assertRaises(SystemExit): fragment.main([str(src), str(dst), "--from-word", "20", "--to-word", "29"])


if __name__ == "__main__":
    unittest.main()


class FragmentProfileTest(unittest.TestCase):
    """film_check: a whole-film item is WARN only in a fragment folder; accept.py never accepts a fragment"""
    def judge(self, work, item):
        import film_check
        obj = type("F", (), {"work": Path(work), "plan": {}, "m": lambda self: 1})()
        return film_check.judge(obj, {"id": "x", "metric": "m", "op": ">=", "value": 3, **item})[0]

    def test_whole_film_item_warns_in_a_fragment_and_fails_in_a_film(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.judge(d, {"whole_film": True}), "FAIL")
            (Path(d) / "FRAGMENT.json").write_text(json.dumps({"src_work": "/w", "from_word": 1, "to_word": 9}))
            self.assertEqual(self.judge(d, {"whole_film": True}), "WARN")
            self.assertEqual(self.judge(d, {}), "FAIL")  # every other item still fails in a fragment

    def test_a_whole_film_warn_level_item_is_tagged_in_a_fragment(self):  # research_gate reads the tag, not level warn
        import film_check
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "FRAGMENT.json").write_text(json.dumps({"src_work": "/w", "from_word": 1, "to_word": 9}))
            obj = type("F", (), {"work": Path(d), "plan": {}, "m": lambda self: 1})()
            st, detail = film_check.judge(obj, {"id": "x", "metric": "m", "op": ">=", "value": 3, "level": "warn", "whole_film": True})
            self.assertEqual(st, "WARN"); self.assertTrue(detail.startswith(film_check.FRAGMENT_TAG))
            st, detail = film_check.judge(obj, {"id": "x", "metric": "m", "op": ">=", "value": 3, "level": "warn"})
            self.assertFalse(detail.startswith(film_check.FRAGMENT_TAG))

    def test_a_broken_fragment_record_is_no_fragment(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ("{", "[]", json.dumps({"src_work": "/w", "from_word": True, "to_word": 9})):
                (Path(d) / "FRAGMENT.json").write_text(bad)
                self.assertEqual(self.judge(d, {"whole_film": True}), "FAIL", bad)

    def test_accept_refuses_a_fragment(self):
        import accept
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "FRAGMENT.json").write_text("{}"); film = Path(d) / "long.mp4"; film.write_bytes(b"x")
            self.assertIn("fragment", accept.write(Path(d), film, "Kamil 2026-11-14: dobry long, jedz dalej"))
            self.assertIn("fragment", accept.check(Path(d)))
