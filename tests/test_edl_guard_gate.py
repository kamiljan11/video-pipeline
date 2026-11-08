"""edl_guard: a hard noise gate in the voice chain is refused (film 2026-11-04: agate threshold 0.035 / range 0.1 ate
"I" of "I wtedy" and other quiet word starts; 0.008 / 0.4 kept them in a whisper A/B)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import edl_guard

BASE = {"sources": {"A": "a.mp4"}, "segments": [{"src": "A", "in": 0.0, "out": 1.0}]}
CHAIN = "highpass=f=80,afftdn=nf=-25:tn=1,{gate}acompressor=threshold=-24dB:ratio=2"


def probs(gate: str) -> list[str]:
    return [p for p in edl_guard.problems({**BASE, "audio": CHAIN.format(gate=gate)}) if "agate" in p]


class GateTest(unittest.TestCase):
    def test_the_film_2_gate_is_refused(self):
        self.assertTrue(probs("agate=threshold=0.035:ratio=3:range=0.1:attack=3:release=120,"))

    def test_ffmpeg_default_gate_is_refused(self):
        self.assertTrue(probs("agate,"))
        self.assertTrue(probs("agate=ratio=2,"))

    def test_gentle_gate_and_no_gate_pass(self):
        self.assertEqual(probs("agate=threshold=0.008:ratio=2:range=0.4:attack=1:release=200,"), [])
        self.assertEqual(probs(""), [])

    def test_unreadable_numbers_are_refused(self):
        self.assertTrue(probs("agate=threshold=x:range=0.4,"))


if __name__ == "__main__":
    unittest.main()
