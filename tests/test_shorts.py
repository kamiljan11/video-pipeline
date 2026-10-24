"""shorts.py on a made-up transcript: what makes a good short start and end, no overlap, the length window.

Run: cd ~/video-pipeline && python3 -m pytest -q tests/test_shorts.py
"""
import sys
import unittest
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shorts  # after the repo root is on the path
from beats import load_grammar

G = load_grammar()


def words(*sents, step=0.5):
    """Sentences -> whisper-like words (one every step s) and a plan keeping all of them."""
    W, t = [], 0.0
    for s in sents:
        for w in s.split():
            W.append((t, t + step - 0.05, " " + w)); t += step
    return W, {"keeps": [[0, len(W) - 1]]}


def best(*sents, lo=5.0, hi=60.0):
    """The candidate made of all the sentences given."""
    W, plan = words(*sents)
    return next(c for c in shorts.candidates(plan, W, G, lo, hi) if c["sent"] == [0, len(sents) - 1]), W


class ShortsTest(unittest.TestCase):
    def test_a_stat_hook_beats_a_start_that_leans_on_the_long(self):
        body = ["Sprawdziłem to na trzech firmach i wynik był zawsze ten sam.", "Nie chodzi o narzędzie, tylko o proces."]
        good, _ = best("95% firm nie widzi zwrotu z AI.", *body)
        bad, _ = best("Czyli jak mówiłem, firmy nie widzą zwrotu z AI.", *body)
        self.assertGreater(good["score"], bad["score"] + 3)
        self.assertIn("hak: stat", good["why"])
        self.assertTrue(any(w.startswith("start nawiązuje") for w in bad["why"]))

    def test_mid_list_and_mid_sentence_starts_are_marked(self):
        for opener, reason in (("Po drugie, liczymy godziny.", "start nawiązuje"), ("4. Kto tego użyje?", "start nawiązuje"),
                               ("godzin w miesiącu to dużo.", "start w pół zdania")):
            with self.subTest(opener=opener):
                W, _ = words(opener, "Nie chodzi o narzędzie.")
                _, why = shorts.score([list(range(len(opener.split()))), list(range(len(opener.split()), len(W)))],
                                      [[], [("maxim", len(W) - 1)]], W)
                self.assertTrue(any(w.startswith(reason) for w in why), why)

    def test_an_end_that_announces_the_next_part_is_marked(self):
        c, _ = best("95% firm nie widzi zwrotu z AI.", "No dobrze, zaczniemy od najważniejszego.")
        self.assertIn("koniec zapowiada dalszą część longa", c["why"])

    def test_picks_never_overlap_and_keep_the_length_window(self):
        sents = [f"Zdanie numer {k} ma sześć słów." for k in range(40)]  # 3 s each
        W, plan = words(*sents)
        got = shorts.pick(shorts.candidates(plan, W, G, 10.0, 20.0), 5)
        self.assertEqual(len(got), 5)
        for a, b in pairwise(got):
            self.assertLess(a["sent"][1], b["sent"][0])
        for c in got:
            self.assertTrue(10.0 <= c["dur"] <= 20.0, c["dur"])

    def test_keeps_are_word_ranges_of_the_chosen_sentences(self):
        self.assertEqual(shorts.runs([3, 4, 5, 9, 10, 14]), [[3, 5], [9, 10], [14, 14]])
        c, W = best("95% firm nie widzi zwrotu.", "Nie chodzi o narzędzie.", lo=1, hi=60)
        self.assertEqual(c["keeps"], [[0, len(W) - 1]])


if __name__ == "__main__":
    unittest.main()
