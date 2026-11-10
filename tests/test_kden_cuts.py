"""cut_fix.py, kden_export.py, kden_import.py: a cut edge dragged in Kdenlive reaches the plan and the EDL."""
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cut_fix
import kden_export
import kden_import

EDL = {"name": "long", "sources": {"A": "/rec/a.crop.mp4"}, "music_db": -10,
       "segments": [{"src": "A", "in": 5.3, "out": 6.788}, {"src": "A", "in": 7.062, "out": 8.96}, {"src": "A", "in": 40.0, "out": 42.5},
                    {"src": "A", "in": 20.0, "out": 22.0}],
       "overlays": [{"file": "gfx/a.mov", "at": 1.0, "dur": 3.0}, {"file": "gfx/b.mov", "at": 2.0, "dur": 2.0}, {"file": "gfx/c.mov", "at": 5.0, "dur": 1.0}]}


class CutFixTest(unittest.TestCase):
    def segs(self):
        return [[5.3, 6.788, "pause"], [7.062, 8.96, "end"], [40.0, 42.5, "end"], [20.0, 22.0, "end"]]

    def test_an_edge_dragged_out_gets_back_what_was_cut(self):
        s = self.segs()
        self.assertEqual(cut_fix.apply(s, [[6.788, 7.0], [40.0, 39.2]]), 2)
        self.assertEqual([s[0][1], s[2][0]], [7.0, 39.2])

    def test_an_edge_that_is_gone_stops_the_build(self):
        with self.assertRaisesRegex(cut_fix.CutFixError, "no cut edge at 6.100"):
            cut_fix.apply(self.segs(), [[6.1, 6.5]])

    def test_the_same_words_twice_are_refused(self):
        with self.assertRaisesRegex(cut_fix.CutFixError, "overlap"):
            cut_fix.apply(self.segs(), [[6.788, 7.5]])

    def test_pieces_from_another_place_in_the_recording_may_cross(self):  # keeps are reordered: 40-42.5 plays before 20-22
        s = self.segs()
        cut_fix.apply(s, [[20.0, 19.0]])
        self.assertEqual(s[3][0], 19.0)

    def test_a_piece_dragged_to_nothing_is_refused(self):
        with self.assertRaisesRegex(cut_fix.CutFixError, "under 0.2 s"):
            cut_fix.apply(self.segs(), [[8.96, 7.1]])

    def test_a_bad_value_is_named(self):
        for bad in ("x", [[1]], [[1, "2"]], [[True, 2]], [[-1, 2]]):
            with self.assertRaises(cut_fix.CutFixError, msg=bad): cut_fix.check(bad)


class KdenliveRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = Path(self.tmp.name)
        self.edl, self.proj, self.plan = d / "edl_long.json", d / "long.kdenlive", d / "plan_long.json"
        self.edl.write_text(json.dumps(EDL), encoding="utf-8")
        self.plan.write_text(json.dumps({"keeps": [[0, 5]]}), encoding="utf-8")
        self.assertEqual(kden_export.main([str(self.edl), str(self.proj)]), 0)

    def test_the_project_is_one_kdenlive_opens(self):  # 2026-11-10: "Version of the project file cannot be read", "Clip with invalid Id"
        root = ET.fromstring(self.proj.read_text(encoding="utf-8"))
        bin_ = next(p for p in root.iter("playlist") if p.get("id") == "main_bin")
        self.assertEqual(next(p.text for p in bin_.findall("property") if p.get("name") == "kdenlive:docproperties.version"), "1.04")
        clips = [el for el in root if el.tag in ("producer", "chain")]
        ids = [next(p.text for p in el.findall("property") if p.get("name") == "kdenlive:id") for el in clips]
        self.assertEqual(len(set(ids)), len(clips))
        self.assertEqual({e.get("producer") for e in bin_.findall("entry")}, {el.get("id") for el in clips})

    def test_the_recording_is_one_track_with_picture_and_voice(self):  # a ripple trim must move both
        root = ET.fromstring(self.proj.read_text(encoding="utf-8"))
        cam = next(t for t in root.iter("track") if t.get("producer") == "v_cam")
        self.assertIsNone(cam.get("hide"))
        ents = next(p for p in root.iter("playlist") if p.get("id") == "v_cam").findall("entry")
        self.assertEqual([(e.get("in"), e.get("out")) for e in ents][:2], [("159", "203"), ("212", "268")])

    def test_cards_that_overlap_go_to_separate_tracks(self):
        self.assertEqual([[c[0] for c in ln] for ln in kden_export.lanes(EDL["overlays"])], [[0, 2], [1]])

    def test_an_untouched_project_changes_nothing(self):
        self.assertEqual(kden_import.main([str(self.proj), str(self.plan)]), 0)
        self.assertNotIn("cut_fix", json.loads(self.plan.read_text(encoding="utf-8")))

    def drag(self, old: str, new: str) -> None:
        s = self.proj.read_text(encoding="utf-8")
        self.assertEqual(s.count(old), 1)
        self.proj.write_text(s.replace(old, new), encoding="utf-8")

    def test_a_dragged_edge_lands_in_the_plan_and_moves_the_cut(self):
        self.drag('in="159" out="203"', 'in="159" out="209"')  # the first piece ends 6 frames later
        self.assertEqual(kden_import.main([str(self.proj), str(self.plan)]), 0)
        fixes = json.loads(self.plan.read_text(encoding="utf-8"))["cut_fix"]
        self.assertEqual(fixes, [[6.788, 7.0]])
        segs = [[s["in"], s["out"], "end"] for s in EDL["segments"]]
        cut_fix.apply(segs, fixes)
        self.assertEqual(segs[0], [5.3, 7.0, "end"])
        self.assertTrue(Path(str(self.plan) + ".before_kden").exists())

    def test_check_writes_nothing(self):
        self.drag('in="159" out="203"', 'in="150" out="203"')
        self.assertEqual(kden_import.main([str(self.proj), str(self.plan), "--check"]), 0)
        self.assertNotIn("cut_fix", json.loads(self.plan.read_text(encoding="utf-8")))

    def test_a_project_saved_with_clock_times_reads_the_same(self):  # Kdenlive writes 00:00:05.300, not frames
        s = self.proj.read_text(encoding="utf-8")
        clock = lambda f: f"00:{int(f) // 30 // 60:02d}:{int(f) / 30 % 60:06.3f}"
        s = re.sub(r'(<entry producer="src_A" in=")(\d+)(" out=")(\d+)"', lambda m: f'{m[1]}{clock(m[2])}{m[3]}{clock(m[4])}"', s)
        self.proj.write_text(s, encoding="utf-8")
        self.assertIn('in="00:00:05.300"', s)
        self.assertEqual(kden_import.main([str(self.proj), str(self.plan)]), 0)
        self.assertNotIn("cut_fix", json.loads(self.plan.read_text(encoding="utf-8")))

    def test_an_edge_moved_twice_keeps_its_first_place(self):  # build_edl looks for the edge it computes itself
        self.assertEqual(kden_import.merged([[6.788, 7.0]], [[7.0, 7.2], [40.0, 39.0]]), [[6.788, 7.2], [40.0, 39.0]])
        self.assertEqual(kden_import.merged([[6.788, 7.0]], [[7.0, 6.788]]), [])  # dragged back

    def test_a_removed_piece_is_named_and_nothing_is_written(self):
        self.drag('<entry producer="src_A" in="159" out="203"/>', "")
        self.assertEqual(kden_import.main([str(self.proj), str(self.plan)]), 1)
        self.assertNotIn("cut_fix", json.loads(self.plan.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
