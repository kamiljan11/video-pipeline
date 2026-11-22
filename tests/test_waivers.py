"""waivers.py: a gate that is off needs Kamil's words in the plan; no code may write them."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import waivers

OK = "Kamil 2026-11-10: tego shorta nie da sie zmierzyc, pusc bez ust"


class WaiversTest(unittest.TestCase):
    def test_an_off_gate_without_a_waiver_is_named(self):
        self.assertEqual(waivers.missing({}, ["lip_check"]), ["lip_check is off and the plan has no waivers.lip_check"])

    def test_kamils_words_let_the_gate_stay_off(self):
        self.assertEqual(waivers.missing({"waivers": {"lip_check": OK}}, ["lip_check"]), [])

    def test_a_waiver_for_one_gate_does_not_cover_another(self):
        self.assertEqual(len(waivers.missing({"waivers": {"lip_check": OK}}, ["lip_check", "words_check"])), 1)

    def test_a_reason_that_is_not_kamils_sentence_is_refused(self):
        for said in ("too slow", "Kamil: ok", "Claude 2026-11-10: the gate is wrong here", "Kamil 2026-11-10: ok", 5):
            self.assertEqual(len(waivers.missing({"waivers": {"lip_check": said}}, ["lip_check"])), 1, said)

    def test_an_unknown_gate_is_refused(self):
        self.assertEqual(len(waivers.missing({"waivers": {"lips": OK}}, [])), 1)
        self.assertEqual(len(waivers.missing({}, ["everything"])), 1)

    def test_the_command_fails_on_a_missing_plan_and_passes_with_a_waiver(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "plan_x.json"
            run = lambda: subprocess.run([sys.executable, str(ROOT / "waivers.py"), str(p), "lip_check"], check=False, capture_output=True, text=True)
            self.assertEqual(run().returncode, 1)
            p.write_text(json.dumps({"waivers": {"lip_check": OK}}), encoding="utf-8")
            r = run()
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("lip_check", r.stdout)

    def test_no_code_writes_a_waiver(self):  # the key is typed into a plan after Kamil said it, never produced by a tool
        key = re.compile(r"""["']waivers["']""")
        hits = [str(f.relative_to(ROOT)) for pat in ("*.py", "*.sh", "gfx/*.mjs", "music/*.py") for f in ROOT.glob(pat)
                if f.name != "waivers.py" and key.search(f.read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
