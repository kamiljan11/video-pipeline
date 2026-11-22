import sys
import unittest
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import podcast_shots as ps

CFG = ps.load_cfg()


def words_of(spec):
    """spec: [(speaker, seconds), ...] -> words of 0.5 s each, back to back"""
    w, s, t = [], [], 0.0
    for spk, dur in spec:
        for _ in range(max(1, round(dur / 0.5))):
            w.append((t, t + 0.5, "x")); s.append(spk); t += 0.5
    return w, s


class Turns(unittest.TestCase):
    def test_backchannel_does_not_take_the_floor(self):
        w, s = words_of([("L", 6), ("R", 0.5), ("L", 6)])
        self.assertEqual(ps.turns(w, s, CFG), [[0.0, 12.5, "L"]])

    def test_real_turn_switches(self):
        w, s = words_of([("L", 6), ("R", 5), ("L", 3)])
        self.assertEqual([t[2] for t in ps.turns(w, s, CFG)], ["L", "R", "L"])

    def test_turns_are_contiguous(self):
        w = [(0, 1, "a"), (2, 3, "b"), (5, 6, "c")]
        tn = ps.turns(w, ["L", "R", "R"], CFG)
        self.assertEqual(tn, [[0, 2, "L"], [2, 6, "R"]])

    def test_unknown_words_stay_with_the_speaker(self):
        w, s = words_of([("L", 2), ("?", 2), ("R", 3)])
        self.assertEqual([t[2] for t in ps.turns(w, s, CFG)], ["L", "R"])
        self.assertEqual(ps.turns(w, s, CFG)[0][1], 4.0)

    def test_no_speaker_at_all(self):
        self.assertEqual(ps.turns([(0, 1, "a")], ["?"], CFG), [])

    def test_label_count_mismatch_stops(self):
        with self.assertRaises(SystemExit): ps.turns([(0, 1, "a")], [], CFG)


class LongShots(unittest.TestCase):
    def test_opens_wide_then_speaker(self):
        w, s = words_of([("L", 10), ("R", 6)])
        sh = ps.long_shots(ps.turns(w, s, CFG), CFG)
        self.assertEqual(sh[0], [0.0, 4.0, "wide"])
        self.assertEqual([x[2] for x in sh], ["wide", "L", "R"])

    def test_short_turn_keeps_previous_shot(self):
        w, s = words_of([("L", 8), ("R", 1.5), ("L", 6)])  # 1.5 s answer: above backchannel, below hold
        sh = ps.long_shots(ps.turns(w, s, CFG), CFG)
        self.assertEqual([x[2] for x in sh], ["wide", "L"])

    def test_long_monologue_gets_wide_cutaway(self):
        w, s = words_of([("L", 50)])
        sh = ps.long_shots(ps.turns(w, s, CFG), CFG)
        self.assertIn("wide", [x[2] for x in sh[1:]])
        self.assertTrue(all(b - a <= CFG["single_max_s"] + 1e-6 for a, b, x in sh if x == "L"))

    def test_pieces_cover_the_turns_without_gaps(self):
        w, s = words_of([("L", 7), ("R", 4), ("L", 30), ("R", 3)])
        tn = ps.turns(w, s, CFG); sh = ps.long_shots(tn, CFG)
        self.assertEqual(sh[0][0], tn[0][0]); self.assertEqual(sh[-1][1], tn[-1][1])
        for (a, b, _), (c, d, _) in pairwise(sh): self.assertAlmostEqual(b, c)
        self.assertTrue(all(b - a >= CFG["min_piece_s"] for a, b, _ in sh))


class ShortShots(unittest.TestCase):
    def test_fast_exchange_is_stacked(self):
        w, s = words_of([("L", 5), ("R", 1.5), ("L", 1.5), ("R", 1.5), ("L", 6)])
        sh = ps.short_shots(ps.turns(w, s, CFG), CFG)
        self.assertIn("stack", [x[2] for x in sh])
        self.assertEqual(sh[0][2], "L"); self.assertEqual(sh[-1][2], "L")

    def test_monologue_after_exchange_leaves_stack(self):
        w, s = words_of([("R", 3), ("L", 1.5), ("R", 1.5), ("L", 20)])
        sh = ps.short_shots(ps.turns(w, s, CFG), CFG)
        stack = [b - a for a, b, x in sh if x == "stack"]
        self.assertTrue(stack and max(stack) < 8)
        self.assertEqual(sh[-1][2], "L")

    def test_slow_exchange_is_not_stacked(self):
        w, s = words_of([("L", 8), ("R", 8), ("L", 8)])
        self.assertEqual([x[2] for x in ps.short_shots(ps.turns(w, s, CFG), CFG)], ["L", "R", "L"])


class Cfg(unittest.TestCase):
    def test_plan_override(self):
        self.assertEqual(ps.load_cfg({"hold_s": 3})["hold_s"], 3)

    def test_unknown_key_and_bad_value_stop(self):
        with self.assertRaises(SystemExit): ps.load_cfg({"hodl_s": 3})
        with self.assertRaises(SystemExit): ps.load_cfg({"hold_s": 0})
        with self.assertRaises(SystemExit): ps.load_cfg({"hold_s": True})

    def test_speaker_names_are_not_rules(self):
        self.assertNotIn("speakers", ps.load_cfg({"speakers": {"L": "A", "R": "B"}}))


if __name__ == "__main__":
    unittest.main()
