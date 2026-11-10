"""dry_run.py: the full render needs a passed small render of the same film on the same code."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import dry_run


class DryRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        (self.work / "edl_long.json").write_text('{"segments": [1]}', encoding="utf-8")
        (self.work / "gfx_specs.json").write_text("[]", encoding="utf-8")
        self.git = {"dirty": False, "changed": None}
        for name, fn in (("dirty", lambda: self.git["dirty"]), ("head", lambda: "abc1234"),
                         ("code_changed", lambda commit, film=False: self.git["changed"])):
            p = mock.patch.object(dry_run.manifest, name, fn)
            p.start()
            self.addCleanup(p.stop)

    def test_no_dry_run_no_render(self):
        self.assertIn("DRY=1 first", dry_run.needed(self.work, "long"))

    def test_a_passed_dry_run_lets_the_same_film_render(self):
        self.assertEqual("", dry_run.passed(self.work, "long"))
        self.assertEqual("", dry_run.needed(self.work, "long"))

    def test_another_cut_asks_for_a_new_dry_run(self):
        dry_run.passed(self.work, "long")
        (self.work / "edl_long.json").write_text('{"segments": [2]}', encoding="utf-8")
        self.assertIn("edl_long.json changed", dry_run.needed(self.work, "long"))

    def test_other_cards_ask_for_a_new_dry_run(self):
        dry_run.passed(self.work, "long")
        (self.work / "gfx_specs.json").unlink()
        self.assertIn("gfx_specs.json changed", dry_run.needed(self.work, "long"))

    def test_code_changed_after_the_dry_run_stops_the_render(self):  # the film's code freeze
        dry_run.passed(self.work, "long")
        self.git["changed"] = "code changed since abc1234: assemble.py"
        self.assertIn("assemble.py", dry_run.needed(self.work, "long"))

    def test_uncommitted_code_gives_no_record_and_no_render(self):
        self.git["dirty"] = True
        self.assertIn("uncommitted", dry_run.passed(self.work, "long"))
        self.assertFalse(dry_run.record(self.work, "long").exists())
        self.git["dirty"] = False
        dry_run.passed(self.work, "long")
        self.git["dirty"] = True
        self.assertIn("uncommitted", dry_run.needed(self.work, "long"))

    def test_a_dry_run_of_one_film_does_not_cover_another(self):
        dry_run.passed(self.work, "long")
        self.assertIn("no dry run of s01", dry_run.needed(self.work, "s01"))

    def test_a_broken_record_is_named(self):
        dry_run.record(self.work, "long").write_text("{", encoding="utf-8")
        self.assertIn("not JSON", dry_run.needed(self.work, "long"))

    def test_the_command_exit_codes(self):
        self.assertEqual(dry_run.main(["need", str(self.work), "long"]), 1)
        self.assertEqual(dry_run.main(["pass", str(self.work), "long"]), 0)
        self.assertEqual(dry_run.main(["need", str(self.work), "long"]), 0)
        self.assertEqual(dry_run.main(["what"]), 2)


if __name__ == "__main__":
    unittest.main()
