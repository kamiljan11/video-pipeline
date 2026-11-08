"""out_gate: the out folder passes film_check --out and every done research item is met in that report"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import out_gate
import research_gate


def fake_run(report, rc=0):
    return mock.Mock(return_value=subprocess.CompletedProcess([], rc, stdout=json.dumps(report), stderr=""))


class OutGateTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="outgate-"))
        self.ledger = self.d / "l.jsonl"
        self.ledger.write_text(json.dumps({"id": "L1", "status": "done", "ref": "check:out.chapters", "form": "Long", "rule": "r"}) + "\n")
        p = mock.patch.object(research_gate, "LEDGER", self.ledger); p.start(); self.addCleanup(p.stop)

    def gate(self, report, rc=0):
        with mock.patch.object(out_gate.subprocess, "run", fake_run(report, rc)):
            return out_gate.main([str(self.d), str(self.d / "out")])

    def test_ok_when_every_item_is_met(self):
        self.assertEqual(self.gate([{"film": "out", "id": "out.chapters", "status": "OK", "detail": ""}]), 0)
        self.assertTrue((self.d / "fc_out.json").exists())

    def test_a_research_warn_or_a_fail_stops_it(self):
        self.assertEqual(self.gate([{"film": "out", "id": "out.chapters", "status": "WARN", "detail": "3 vs 0"}]), 1)
        self.assertEqual(self.gate([{"film": "out", "id": "out.chapters", "status": "OK", "detail": ""},
                                    {"film": "out", "id": "out.manifest", "status": "FAIL", "detail": "no stamp"}], rc=1), 1)

    def test_no_report_is_a_usage_error(self):
        with mock.patch.object(out_gate.subprocess, "run", mock.Mock(return_value=subprocess.CompletedProcess([], 2, stdout="", stderr="boom"))):
            self.assertEqual(out_gate.main([str(self.d), str(self.d)]), 2)
        self.assertEqual(out_gate.main([]), 2)
        self.assertEqual(self.gate([]), 2)  # an empty report measured nothing: not a pass

    def test_a_missing_out_row_is_not_met(self):  # pg-review 2026-11-08: a renamed check passed silently
        self.assertEqual(self.gate([{"film": "out", "id": "out.manifest", "status": "OK", "detail": ""}]), 1)

    def test_a_timeout_is_a_usage_error(self):
        with mock.patch.object(out_gate.subprocess, "run", mock.Mock(side_effect=subprocess.TimeoutExpired("film_check", 1))):
            self.assertEqual(out_gate.main([str(self.d), str(self.d)]), 2)


if __name__ == "__main__":
    unittest.main()
