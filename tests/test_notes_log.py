"""style/NOTES_LOG.md: every Kamil remark is one row that points at a rule; checklist ids it names must exist"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "style" / "NOTES_LOG.md"
STATUS = re.compile(r"^(zrobione|do zrobienia|scalone z \d+)$")
CHECK_ID = re.compile(r"`((?:long|short|out)\.[a-z_]+)`")


def rows() -> list[list[str]]:
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0].isdigit(): out.append(cells)
    return out


class NotesLogTest(unittest.TestCase):
    def test_rows_are_numbered_complete_and_have_a_status(self):
        rs = rows()
        self.assertGreaterEqual(len(rs), 23)
        self.assertEqual([int(r[0]) for r in rs], list(range(1, len(rs) + 1)))
        for r in rs:
            with self.subTest(row=r[0]):
                self.assertEqual(len(r), 7, r)
                self.assertTrue(all(r), r)
                self.assertRegex(r[1], r"^\d{4}-\d{2}-\d{2}$")
                self.assertRegex(r[6], STATUS)
                merged = re.match(r"scalone z (\d+)", r[6])
                if merged: self.assertLess(int(merged.group(1)), int(r[0]))

    def test_named_checklist_ids_exist(self):
        ids = {i["id"] for i in json.loads((ROOT / "style" / "checklist.json").read_text())["items"]}
        for r in rows():
            for cid in CHECK_ID.findall(r[4]):
                with self.subTest(row=r[0], id=cid):
                    self.assertIn(cid, ids)


if __name__ == "__main__":
    unittest.main()
