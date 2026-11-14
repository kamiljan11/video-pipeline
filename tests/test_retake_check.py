"""retakes.py + retake_check.py: a retake the cut kept, heard utterance by utterance (2026-11-14 fragment at 1:00)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import retake_check
import retakes

# whisper per utterance on the fragment, 55.65-69.86 s of out/long.mp4 (measured 2026-11-14): both takes heard
SPANS = [(55.65, 58.85), (59.41, 61.50), (61.76, 62.84), (63.10, 66.30), (66.60, 69.86)]
TEXTS = ["Jakieś sprawdzenie zatrzyma to następnym razem. No i przykład.", "Z jednej aplikacji po usunięciu profilu",
         "program program", "No i przykład: w jednej aplikacji po usunięciu profilu",
         "Program po cichu stawiał na fakturę innego sprzedawcę."]


class RetakeTest(unittest.TestCase):
    def words(self):
        return retake_check.timed_words(SPANS, TEXTS)

    def test_the_fragment_retake_at_one_minute_is_found(self):
        bad, wrong = retakes.problems(self.words(), {})
        self.assertEqual(wrong, [])
        self.assertEqual(len(bad), 1)
        self.assertIn("jednej aplikacji po usunięciu profilu", bad[0])
        self.assertIn("at 60 s and 65 s", bad[0])

    def test_a_repeat_on_purpose_is_named_whole(self):
        ok = {"retakes_ok": {"jednej aplikacji po usunięciu profilu program": "said twice on purpose for the example"}}
        self.assertEqual(retakes.problems(self.words(), ok), ([], []))
        part = {"retakes_ok": {"jednej aplikacji po usunięciu": "said twice on purpose for the example"}}
        self.assertEqual(len(retakes.problems(self.words(), part)[0]), 1)  # 4 named words do not waive the longer run

    def test_a_named_phrase_without_a_reason_waives_nothing(self):
        bad, wrong = retakes.problems(self.words(), {"retakes_ok": {"jednej aplikacji po usunięciu profilu program": "ok"}})
        self.assertEqual(len(bad), 1); self.assertEqual(len(wrong), 1)

    def test_the_same_words_far_apart_are_not_a_retake(self):
        far = [(0.0, "no"), (0.5, "i"), (1.0, "to"), (1.5, "jest"), (40.0, "no"), (40.5, "i"), (41.0, "to"), (41.5, "jest")]
        self.assertEqual(retakes.runs(far), [])
        self.assertEqual(len(retakes.runs(far, window=60)), 1)

    def test_utterances_join_short_pieces_and_drop_blips(self):
        sil = [("start", 1.2), ("end", 1.6), ("start", 2.5), ("end", 3.8), ("start", 3.85), ("end", 9.0), ("start", 12.0), ("end", 12.3)]
        # speech 0-1.2 + 1.6-2.5 (joined: under 3 s together), 3.8-3.85 blip, 9-12, 12.3-15 (joined would be 6 s: apart)
        self.assertEqual(retake_check.utterances(sil, 15.0), [(0.0, 2.5), (9.0, 12.0), (12.3, 15.0)])

    def test_words_take_their_utterance_time(self):
        w = retake_check.timed_words([(10.0, 12.0)], ["a b"])
        self.assertEqual(w, [(10.0, "a"), (11.0, "b")])


if __name__ == "__main__":
    unittest.main()
