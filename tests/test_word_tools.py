"""words_check (lost words) and word_times (word starts on the voice): the pure parts, no whisper run.
Film 2026-11-04: "Przez" and "I" lost in the long; whisper word starts up to 1.07 s off the voice."""
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import word_times as T
import words_check as C


def w(text: str, s: int, e: int) -> dict:
    return {"offsets": {"from": s, "to": e}, "text": f" {text}"}


class WordsCheckTest(unittest.TestCase):
    EXP = C.norm("Dzisiaj muszę się przyznać. Przez długi czas wstydziłem się. I wtedy zmieniłem pytanie, już nie czy wypada")

    def test_sound_mode_fails_on_any_lost_word_inside_the_film(self):
        heard = [x for x in self.EXP if x not in ("przez", "i")]
        bad, _ = C.judge("sound", self.EXP, heard)
        self.assertEqual(len(bad), 2, bad)
        self.assertTrue(any("[[przez]]" in b for b in bad) and any("[[i]]" in b for b in bad), bad)

    def test_sound_mode_only_warns_at_the_film_edges(self):
        bad, warn = C.judge("sound", self.EXP, self.EXP[1:])
        self.assertEqual(bad, [])
        self.assertTrue(warn and "film edge" in warn[0])

    def test_cut_mode_tolerates_short_single_mishearings(self):
        heard = [x for x in self.EXP if x != "i"]
        self.assertEqual(C.judge("cut", self.EXP, heard)[0], [])  # "i" alone: WARN, whisper drops it by itself
        heard = [x for x in self.EXP if x != "przez"]
        self.assertTrue(C.judge("cut", self.EXP, heard)[0])  # a 5-letter word gone: FAIL
        heard = [x for x in self.EXP if x not in ("już", "nie")]
        self.assertTrue(C.judge("cut", self.EXP, heard)[0])  # 2 in a row: FAIL

    def test_identical_text_passes(self):
        self.assertEqual(C.judge("sound", self.EXP, list(self.EXP)), ([], []))


class WordTimesTest(unittest.TestCase):
    def test_dtw_start_reads_the_first_real_token(self):
        item = {"tokens": [{"text": "[_BEG_]", "t_dtw": 0}, {"text": " Pr", "t_dtw": 932}, {"text": "ze", "t_dtw": 940}]}
        self.assertEqual(T.dtw_start_ms(item), 9320)
        self.assertIsNone(T.dtw_start_ms({"tokens": [{"text": " Pr", "t_dtw": -1}]}))

    def test_transfer_keeps_hand_fixed_text_and_takes_matching_starts(self):
        words = [w("Dzisiaj", 1000, 1400), w("Halloweenowo", 1600, 6480), w("muszę", 6500, 6800)]
        dtw = [w("dzisiaj", 1050, 1400), w("Halloween", 1700, 2300), w("owo", 2300, 2700), w("muszę", 2900, 3200)]
        moved = T.transfer(words, dtw)
        self.assertEqual([x["text"] for x in words], [" Dzisiaj", " Halloweenowo", " muszę"])  # text untouched
        self.assertEqual(words[0]["offsets"]["from"], 1050)
        self.assertEqual(words[1]["offsets"]["from"], 1600)  # no match: kept
        self.assertEqual(words[2]["offsets"]["from"], 6500)  # matched but 3.6 s away: another occurrence, kept
        self.assertEqual(moved, 1)

    def test_snap_moves_a_start_after_a_pause_onto_the_onset_only(self):
        words = [w("a", 1000, 1500), w("b", 2200, 2600), w("c", 2620, 2900)]
        n = T.snap(words, np.array([1.98, 2.64]))
        self.assertEqual(words[1]["offsets"]["from"], 1980)  # after a 0.7 s pause, onset 0.22 s earlier: snapped
        self.assertEqual(words[2]["offsets"]["from"], 2620)  # inside the phrase: left alone
        self.assertEqual(n, 1)

    def test_onsets_and_error_on_a_synthetic_voice(self):
        sr = 16000
        a = np.zeros(sr * 3, np.int16)
        for t0 in (0.5, 1.6):
            a[int(t0 * sr):int((t0 + 0.4) * sr)] = (8000 * np.sin(np.arange(int(0.4 * sr)) * 2 * np.pi * 200 / sr)).astype(np.int16)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "v.wav"
            with wave.open(str(f), "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(a.tobytes())
            on = T.onsets(str(f))
            self.assertEqual([round(x, 2) for x in on], [0.5, 1.6])
            e = T.error([w("x", 700, 900), w("y", 1600, 1900)], on)
            self.assertEqual((e["n"], e["over_150ms_pct"]), (2, 50.0))


if __name__ == "__main__":
    unittest.main()
