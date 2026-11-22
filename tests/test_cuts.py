"""cuts.py: a long cuts only named mistakes and keeps air between sentences (Kamil 2026-11-15)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cuts


class CutsTest(unittest.TestCase):
    def setUp(self):
        self.PLAN = {"keeps": [[0, 10], [21, 30], [12, 15], [41, 50]], "pads": {"mingap": 0.7, "keep_l": 0.28, "keep_r": 0.22}}

    def test_every_run_left_out_is_found_in_word_order(self):
        self.assertEqual(cuts.dropped(self.PLAN["keeps"], 51), [(11, 11), (16, 20), (31, 40)])

    def test_an_unnamed_cut_is_a_problem(self):  # the 2026-11-09 edit: 23 spans of digressions out with the retakes
        bad = cuts.problems(self.PLAN, 51)
        self.assertEqual(len(bad), 3); self.assertIn("w16-20 is cut and plan \"cuts\" does not name it", bad[1])

    def test_named_mistakes_pass_and_content_does_not(self):
        ok = {**self.PLAN, "cuts": {"w11-11": "slip: 'te te'", "w16-20": "retake: take 1 of 2", "w31-40": "Kamil 2026-11-09: 92 % not proven"}}
        self.assertEqual(cuts.problems(ok, 51), [])
        bad = {**ok, "cuts": {**ok["cuts"], "w31-40": "ramble: a digression"}}
        self.assertIn("kind one of", cuts.problems(bad, 51)[0])
        self.assertIn("name a run", cuts.problems({**ok, "cuts": {**ok["cuts"], "31-40": "retake: x"}}, 51)[0])
        self.assertEqual(cuts.problems({**ok, "cuts": {"w10-45": "retake: one range over all three"}}, 51), [])

    def test_a_tight_pause_is_a_problem_and_the_default_breathes(self):
        tight = {"keeps": [[0, 10]], "pads": {"mingap": 0.36}}
        self.assertIn("pads.mingap 0.36", cuts.problems(tight, 11)[0])
        self.assertEqual(cuts.problems({"keeps": [[0, 10]]}, 11), [])  # no pads: build_edl uses LONG_PADS
        self.assertIn("pads.mingap 0.45", cuts.problems({"keeps": [[0, 10]], "pads": {"pre": 0.1}}, 11)[0])



class NamedRunsTest(unittest.TestCase):
    def test_one_word_and_neighbouring_ranges_cover_a_run(self):  # 2026-11-04 long: w1366, and two retakes side by side
        plan = {"keeps": [[0, 9], [11, 20], [41, 50]],
                "cuts": {"w10": "slip: doubled 'te te'", "w21-30": "retake: take 1 of it", "w31-40": "Kamil 2026-11-09: stays out"}}
        self.assertEqual(cuts.problems(plan, 51), [])

    def test_a_run_half_named_is_still_a_problem(self):
        plan = {"keeps": [[0, 9], [41, 50]], "cuts": {"w10-30": "retake: take 1 of it"}}
        self.assertEqual(len(cuts.problems(plan, 51)), 1)


class EdgesTest(unittest.TestCase):
    def test_talk_before_the_first_keep_and_after_the_last_is_named_too(self):
        plan = {"keeps": [[5, 20]], "cuts": {"w0-4": "off take: 'nagrywamy?' before the take"}}
        self.assertEqual(len(cuts.problems(plan, 30)), 1)  # w21-29 after the last keep is not named
        plan["cuts"]["w21-29"] = "off take: 'dobra, stop' after the take"
        self.assertEqual(cuts.problems(plan, 30), [])


class OrderTest(unittest.TestCase):
    def test_a_keep_moved_back_in_the_recording_is_named(self):  # the 2026-11-04 long: w187-232 before w69-166
        why = cuts.order([[0, 50], [187, 232], [69, 166]])
        self.assertEqual(len(why), 1)
        self.assertIn("w69-166 comes after w187-232", why[0])

    def test_keeps_in_word_order_pass(self):
        self.assertEqual(cuts.order([[0, 50, {"t1": 3.0}], [51, 68], [70, 90]]), [])


if __name__ == "__main__":
    unittest.main()
