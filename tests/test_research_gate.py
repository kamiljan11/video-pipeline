"""research_gate.py: a film form renders only when its research is in the film (Kamil 2026-11-08 "dlaczego nic nie weszlo")."""
import json
import tempfile
import unittest
from pathlib import Path

import research_gate as rg

IDS = {"long.opening", "short.hook", "out.thumbs_read"}


def item(i: str, status: str, ref: str = "", form: str = "Long") -> dict:
    return {"id": i, "form": form, "status": status, "ref": ref, "rule": f"rule {i}"}


class ResearchGateTest(unittest.TestCase):
    def bad(self, items, form="long"):
        return rg.problems(items, form, IDS)

    def test_todo_blocks(self):
        b = self.bad([item("L1", "todo")])
        self.assertEqual(len(b), 1)
        self.assertIn("L1 open (todo)", b[0])

    def test_done_needs_a_film_check_item(self):
        self.assertIn("without a film_check item", self.bad([item("L1", "done", "commit abc123")])[0])
        self.assertEqual(self.bad([item("L1", "done", "abc123 check:long.opening")]), [])

    def test_done_with_an_unknown_check_id_fails(self):
        self.assertIn("unknown film_check items ['long.nothing']", self.bad([item("L1", "done", "check:long.nothing")])[0])

    def test_merged_into_an_open_carrier_is_open_and_counted_on_it(self):
        b = self.bad([item("L1", "todo"), item("w:1", "merged", "L1", form="long"), item("w:2", "merged", "L1", form="long")])
        self.assertEqual(b, ["L1 open (todo): rule L1 [+2 merged]"])

    def test_merged_into_a_done_carrier_is_closed(self):
        self.assertEqual(self.bad([item("L1", "done", "check:long.opening"), item("w:1", "merged", "L1", form="long")]), [])

    def test_carrier_in_another_form_is_named(self):
        b = self.bad([item("P0.6", "todo", form="P0 — badanie"), item("w:1", "merged", "P0.6", form="long")])
        self.assertEqual(len(b), 1)
        self.assertIn("P0.6 open (todo, carries 1 item(s) of this form)", b[0])

    def test_merged_into_an_unknown_id_is_open(self):
        self.assertIn("unknown id", self.bad([item("w:1", "merged", "nope", form="long")])[0])

    def test_merged_cycle_does_not_loop(self):
        b = self.bad([item("a", "merged", "b"), item("b", "merged", "a")])
        self.assertEqual(len(b), 2)

    def test_deferred_needs_kamil_or_data(self):
        self.assertTrue(self.bad([item("L13", "deferred", "later")]))
        self.assertEqual(self.bad([item("L13", "deferred", "Kamil: A/B napisy, decyzja po filmie 2")]), [])
        self.assertEqual(self.bad([item("L24", "deferred", "data: wpm PL po 3 filmach")]), [])

    def test_rejected_needs_a_reason(self):
        self.assertTrue(self.bad([item("x", "rejected", "no")]))
        self.assertEqual(self.bad([item("x", "rejected", "sprzeczne z regula Kamila 5.11")]), [])

    def test_meta_done_passes_and_is_listed(self):
        items = [item("L14", "done", "meta: rewizja L1-L13")]
        self.assertEqual(self.bad(items), [])
        self.assertEqual(rg.meta_items(items, "long"), ["INFO L14 done as plan work (meta: rewizja L1-L13)"])

    def test_forms_are_kept_apart(self):
        items = [item("S1", "todo", form="Shorts"), item("TH4", "todo", form="Thumbs (miniatury longa)"),
                 item("p", "todo", form="P2 — shorty"), item("t", "todo", form="P1 — miniatury i tytuły longa")]
        self.assertEqual(self.bad(items, "long"), [])
        self.assertEqual([b.split()[0] for b in self.bad(items, "shorts")], ["S1", "p"])
        self.assertEqual([b.split()[0] for b in self.bad(items, "thumbs")], ["TH4", "t"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "l.jsonl"
            f.write_text(json.dumps(item("L1", "todo")) + "\n" + json.dumps(item("S1", "done", "check:short.hook", "Shorts")) + "\n")
            self.assertEqual(rg.main(["long", "--ledger", str(f)]), 1)
            self.assertEqual(rg.main(["shorts", "--ledger", str(f)]), 0)
            self.assertEqual(rg.main(["nope", "--ledger", str(f)]), 2)
            self.assertEqual(rg.main(["long", "--ledger", str(Path(d) / "missing")]), 2)

    def test_report_needs_ok_for_every_done_check(self):  # a warn-level research check missed in the film = not used
        items = [item("L8", "done", "check:long.list_said"), item("L16", "done", "check:long.web_marked check:long.read_along"),
                 item("L1", "done", "check:out.chapters"), item("S4", "done", "check:short.hook_echo", "Shorts")]
        rep = [{"film": "long", "id": "long.list_said", "status": "WARN", "detail": "a: 3 items not timed"},
               {"film": "long", "id": "long.web_marked", "status": "OK", "detail": ""},
               {"film": "long", "id": "long.read_along", "status": "SKIP", "detail": "no code in this film"}]
        bad, info = rg.report_problems(items, "long", rep)
        self.assertEqual([b.split()[0] for b in bad], ["L8"])  # out.chapters not in a film report: checked in the out report
        self.assertIn("WARN", bad[0])
        self.assertEqual(len(info), 1); self.assertIn("no code in this film", info[0])
        self.assertEqual(rg.report_problems(items, "shorts", rep), ([], []))
        with tempfile.TemporaryDirectory() as d:
            f, r = Path(d) / "l.jsonl", Path(d) / "fc.json"
            f.write_text("".join(json.dumps(i) + "\n" for i in items)); r.write_text(json.dumps(rep))
            self.assertEqual(rg.main(["long", "--ledger", str(f), "--report", str(r)]), 1)
            r.write_text(json.dumps([{**x, "status": "OK"} for x in rep]))
            self.assertEqual(rg.main(["long", "--report", str(r), "--ledger", str(f)]), 0)

    def test_a_check_without_a_row_for_a_film_is_not_met(self):  # pg-review 2026-11-08 data-1 / code-1
        items = [item("S4", "done", "check:short.hook_echo", "Shorts"), item("L1", "done", "check:out.chapters", "Shorts")]
        rep = [{"film": "s01", "id": "short.hook_echo", "status": "OK", "detail": ""},
               {"film": "s02", "id": "short.end", "status": "OK", "detail": ""}]
        bad, _ = rg.report_problems(items, "shorts", rep)
        self.assertEqual(len(bad), 1); self.assertIn("no row for s02", bad[0])  # out.chapters: another format, not here

    def test_a_whole_film_check_of_a_fragment_test_is_info_not_a_miss(self):  # film_check FRAGMENT_TAG row
        items = [item("L7", "done", "check:long.recap"), item("L8", "done", "check:long.list_said")]
        rep = [{"film": "long", "id": "long.recap", "status": "WARN", "detail": "fragment test, whole-film item: no recap", "fragment": True},
               {"film": "long", "id": "long.list_said", "status": "WARN", "detail": "fragment test, whole-film item: x", "fragment": "yes"}]
        bad, info = rg.report_problems(items, "long", rep)
        self.assertEqual([b.split()[0] for b in bad], ["L8"])  # only a real true marks it
        self.assertTrue(any("L7" in i and "fragment" in i for i in info))

    def test_an_empty_or_malformed_report_is_refused(self):
        items = [item("L8", "done", "check:long.list_said")]
        for rep in ([], {}, [{"id": "long.list_said"}], ["x"]):
            with self.assertRaises(ValueError): rg.report_problems(items, "long", rep)
        with tempfile.TemporaryDirectory() as d:
            f, r = Path(d) / "l.jsonl", Path(d) / "fc.json"
            f.write_text(json.dumps(items[0]) + "\n")
            for text in ("[]", "{", '[{"id": "x"}]'):
                r.write_text(text)
                self.assertEqual(rg.main(["long", "--ledger", str(f), "--report", str(r)]), 2)
            self.assertEqual(rg.main(["long", "--ledger", str(f), "--report", str(Path(d) / "missing.json")]), 2)

    def test_the_real_checklist_ids_load(self):
        self.assertIn("long.opening", rg.checklist_ids())


if __name__ == "__main__":
    unittest.main()
