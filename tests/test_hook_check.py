"""hook_check: the 6 hook killers (Polish), the variants per short and the hook bank"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import hook_check as H
import shorts

BAD = {"Cześć, tu Kamil i AI w moim kodzie": "greeting",
       "5 porad jak pisać kod z AI": "title, not a hook",
       "Dzisiaj o tym, jak AI psuje mój kod": "filler",
       "Sekret produktywności, który zmienia wszystko": "vague",
       "Niesamowity, genialny system dla agenta": "vague: hype",
       "Zbudowałem system dla agenta": "no stake"}
GOOD = ["AI mówi „gotowe”. A nic nie działa.", "92% zmian bez przeglądu. A dziś?", "Na katar nikt nie robi rezonansu"]


class KillerTest(unittest.TestCase):
    def test_six_bad_hooks_fail_on_their_killer(self):
        for hook, killer in BAD.items():
            with self.subTest(hook):
                bad = H.problems(hook)
                self.assertTrue(any(b.startswith(killer) for b in bad), bad)

    def test_three_good_hooks_pass(self):
        for hook in GOOD:
            with self.subTest(hook):
                self.assertEqual(H.problems(hook), [])

    def test_length_and_the_first_frame(self):
        self.assertIn("14 words (max 12)", H.problems("Jak przez rok traciłem czas na pisanie kodu, który AI pisze za mnie dziś"))
        self.assertTrue(any(b.startswith("no text") for b in H.problems(GOOD[0], on_screen=False)))
        self.assertEqual(H.problems("   "), ["empty hook"])

    def test_a_vague_word_with_an_anchor_is_not_vague(self):  # "trik" next to a number or an acronym says something concrete
        self.assertFalse(any(b.startswith("vague") for b in H.problems("Jeden trik w CLAUDE.md zamiast 40 zasad")))


IDS = frozenset({"mech-contrarian"})


class ClipTest(unittest.TestCase):
    def test_three_clean_variants_the_chosen_one_and_its_source(self):
        ok = {"id": "s1", "hooks": GOOD, "hook": GOOD[0], "hook_from": "mech-contrarian"}
        self.assertEqual(H.clip_problems(ok, IDS), [])
        bad = H.clip_problems({"id": "s1", "hooks": GOOD[:1] + ["Cześć wszystkim"], "hook": "inny", "hook_from": "x"}, IDS)
        for want in ("2 hook variants", "'Cześć wszystkim': greeting", '"hook" is not one of', '"hook_from" \'x\''):
            self.assertTrue(any(want in b for b in bad), (want, bad))


class BankTest(unittest.TestCase):
    def test_rows_are_whole_typed_unique_and_our_own_are_clean(self):
        rows = H.bank()
        self.assertGreaterEqual(len(rows), 20)
        for r in rows.values():
            with self.subTest(r["id"]):
                self.assertIn(r["type"], shorts.HOOKS)
                self.assertTrue(r["text"] and r["source"] and r["why"])
                self.assertIn("result", r)  # null until measured: never a made-up number
                if r["id"].startswith("own-"): self.assertEqual(H.problems(r["text"]), [])

    def test_cli(self):
        self.assertEqual(H.main([]), 2)
        self.assertEqual(H.main(GOOD), 0)
        self.assertEqual(H.main(list(BAD)), 1)


if __name__ == "__main__":
    unittest.main()
