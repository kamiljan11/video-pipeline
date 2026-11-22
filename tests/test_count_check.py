"""count_check: the count he says matches the card (list items, scene element group, shown numbers)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import count_check as C

OV = [{"id": "g", "at": 10.0, "dur": 6.0}]


def tiles(n: int, k: str = "chip") -> dict:
    return {"id": "g", "type": "scene", "els": [{"k": k, "text": f"t{i}"} for i in range(n)] + [{"k": "line"}, {"k": "stamp"}]}


class CountTest(unittest.TestCase):
    def test_three_steps_over_six_tiles_fails(self):
        bad = C.problems(OV, {"g": tiles(6)}, [(9.0, "trzy"), (9.3, "kroki")])
        self.assertEqual(bad, ["g: 6 on the card, says [3]"])

    def test_the_right_count_in_any_case_passes(self):
        for w in ("sześć", "sześciu", "6"):
            with self.subTest(w=w):
                self.assertEqual(C.problems(OV, {"g": tiles(6)}, [(11.0, w)]), [])
        self.assertEqual(C.problems(OV, {"g": tiles(3, "node")}, [(10.5, "trzech")]), [])

    def test_a_seven_over_six_fails(self):
        card = {"id": "g", "type": "kw", "text": "7 zasad", "sub": "dla agenta"}
        self.assertEqual(C.problems(OV, {"g": card}, [(10.2, "sześć"), (10.5, "zasad")]), ["g: shows 7, says [6]"])

    def test_three_of_four_names_both_counts(self):  # "trzy z czterech zadań" over four task windows
        self.assertEqual(C.problems(OV, {"g": tiles(4, "file")}, [(9.5, "trzy"), (9.7, "z"), (9.9, "czterech")]), [])

    def test_no_count_said_or_said_far_away_is_no_claim(self):
        self.assertEqual(C.problems(OV, {"g": tiles(6)}, [(10.5, "kroki")]), [])
        self.assertEqual(C.problems(OV, {"g": tiles(6)}, [(5.0, "trzy"), (15.0, "dwa")]), [])  # before LEAD, after SPAN
        self.assertEqual(C.problems(OV, {"g": tiles(1)}, [(10.5, "trzy")]), [])  # one element: nothing to count

    def test_list_items_and_shown_values(self):
        lst = {"id": "g", "type": "list", "items": ["a", "b", "c", "d"]}
        self.assertEqual(C.problems(OV, {"g": lst}, [(10.0, "cztery")]), [])
        self.assertEqual(C.problems(OV, {"g": lst}, [(10.0, "pięć")]), ["g: 4 on the card, says [5]"])
        self.assertEqual(C.shown_numbers({"type": "kw", "text": "95% z 3 firm", "sub": "2,5 mln"}), {3})


if __name__ == "__main__":
    unittest.main()
