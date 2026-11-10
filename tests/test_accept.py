"""accept.py: nothing but the long is made until Kamil accepted the long he watched."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import accept

SAID = "Kamil 2026-11-15: long jest dobry, jedz dalej"


class AcceptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.film = self.work / "long.mp4"
        self.film.write_bytes(b"film v1")

    def test_no_acceptance_no_other_film(self):
        self.assertIn("not accepted yet", accept.check(self.work))

    def test_an_accepted_long_opens_the_rest(self):
        self.assertEqual(accept.write(self.work, self.film, SAID), "")
        self.assertEqual(accept.check(self.work), "")

    def test_a_long_rendered_again_needs_a_new_acceptance(self):
        accept.write(self.work, self.film, SAID)
        self.film.write_bytes(b"film v2")
        self.assertIn("changed after Kamil accepted it", accept.check(self.work))

    def test_a_deleted_long_is_named(self):
        accept.write(self.work, self.film, SAID)
        self.film.unlink()
        self.assertIn("gone", accept.check(self.work))

    def test_only_kamils_dated_sentence_accepts(self):
        for said in ("ok", "Claude 2026-11-15: all gates are green here", "Kamil: jedz dalej"):
            self.assertIn("whose words", accept.write(self.work, self.film, said), said)
        self.assertFalse((self.work / accept.NAME).exists())

    def test_the_command_exit_codes(self):
        self.assertEqual(accept.main(["check", str(self.work)]), 1)
        self.assertEqual(accept.main(["write", str(self.work), str(self.film), SAID]), 0)
        self.assertEqual(accept.main(["check", str(self.work)]), 0)
        self.assertEqual(accept.main(["write", str(self.work)]), 2)


if __name__ == "__main__":
    unittest.main()
