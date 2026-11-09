"""nothing the pipeline can do is left out unseen (Kamil 2026-11-09 "a da sie system enforcowac zeby nie pominal rzeczy").

Lock 2: style/capabilities.json covers every feature found in the code, each with a role card owner and a check.
Lock 3: every work item of a design reaches the research ledger (design_ledger), so research_gate blocks a render.
Lock 4: a film uses every required feature or skips it with a reason (film_check long/short.capabilities).
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import capabilities as C
import design_ledger as D


class MapTest(unittest.TestCase):
    def test_the_map_covers_the_code(self):
        self.assertEqual(C.problems(C.load(), C.discover()), [])

    def copy_root(self) -> Path:
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        for rel in ("gfx/render.mjs", "gfx/scene_lib.mjs", "build_edl.py", "style/checklist.json", "verify_cut.py",
                    "master_audio.py", "lip_check.py", "words_check.py", "edl_guard.py", "gfx/scene_check.mjs"):
            (d / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / rel, d / rel)
        shutil.copytree(ROOT / "team" / "roles", d / "team" / "roles")
        return d

    def test_a_new_card_type_without_an_entry_fails(self):
        d = self.copy_root()
        r = d / "gfx" / "render.mjs"
        r.write_text(r.read_text().replace("const html = sp => {", "const html = sp => {\n  if (sp.type === 'xray') return '';", 1))
        bad = C.problems(C.load(), C.discover(d), d)
        self.assertIn("card.xray: in the code, not in style/capabilities.json (add it with an owner, a check and a use)", bad)

    def test_a_new_plan_key_without_an_entry_fails(self):
        d = self.copy_root()
        b = d / "build_edl.py"; b.write_text(b.read_text() + '\n_x = P.get("glitter")\n')
        self.assertTrue(any(p.startswith("plan.glitter:") for p in C.problems(C.load(), C.discover(d), d)))

    def test_entries_need_a_real_owner_a_real_check_and_a_use(self):
        caps = [dict(c) for c in C.load()]
        caps[0] = {**caps[0], "owner": "nobody"}
        caps[1] = {**caps[1], "check": "long.nothing"}
        caps[2] = {**caps[2], "use": {"long": "maybe", "short": "report"}}
        caps.append({"id": "card.ghost", "kind": "card", "name": "ghost", "owner": "operator", "check": "long.punch",
                     "use": {"long": "never", "short": "report"}})
        bad = " | ".join(C.problems(caps, C.discover()))
        for want in ("is no role card", "is no style/checklist.json item", "not one of required", "'never' needs a why",
                     "card.ghost: in style/capabilities.json, no longer in the code"):
            self.assertIn(want, bad)

    def test_required_needs_evidence_of_its_own_form(self):
        caps = [dict(c) for c in C.load()]
        i = next(k for k, c in enumerate(caps) if c["id"] == "plan.grade")  # gate:edl_guard.py: the why is its only evidence
        caps[i] = {k: v for k, v in caps[i].items() if k != "why"}
        j = next(k for k, c in enumerate(caps) if c["id"] == "card.list")  # long.list_said is a long item: no evidence for a short
        caps[j] = {**caps[j], "use": {"long": "required", "short": "required"}}
        bad = C.problems(caps, C.discover())
        self.assertIn("plan.grade: required in the long without evidence (a why, or a long checklist item with a why as its check)", bad)
        self.assertIn("card.list: required in the short without evidence (a why, or a short checklist item with a why as its check)", bad)
        self.assertNotIn("card.list: required in the long without evidence (a why, or a long checklist item with a why as its check)", bad)

    def test_a_form_can_have_its_own_check(self):
        kw = next(c for c in C.load() if c["id"] == "card.kw")
        self.assertEqual((C.check_of(kw, "long"), C.check_of(kw, "short")), ("long.graphics", "short.max_gap"))

    def test_a_scan_that_finds_nothing_or_lost_its_marker_fails_loudly(self):
        found = {**C.discover(), "bg": set()}
        self.assertIn("bg: 0 found in the code (the scan in capabilities.discover no longer matches it)", C.problems(C.load(), found))
        d = self.copy_root()
        s = d / "gfx" / "scene_lib.mjs"; s.write_text(s.read_text().replace("export const BGS = [", "export const BACKGROUNDS = ["))
        with self.assertRaisesRegex(ValueError, "gfx/scene_lib.mjs: marker 'export const BGS = \\['"):
            C.discover(d)


CAPS = ({"id": "card.kw", "check": "long.graphics", "use": {"long": "required", "short": "required"}},
        {"id": "plan.broll", "check": "long.graphics", "use": {"long": "required", "short": "report"}},
        {"id": "piece.ring", "check": "gate:gfx/scene_check.mjs", "use": {"long": "report", "short": "report"}},
        {"id": "plan.sil", "check": "gate:build_edl.py", "use": {"long": "infra", "short": "infra"}})


class CoverageTest(unittest.TestCase):
    def test_required_must_be_used_or_skipped_with_a_reason(self):
        self.assertEqual(C.coverage(list(CAPS), "long", set(), {}), (["card.kw", "plan.broll"], ["piece.ring"]))
        self.assertEqual(C.coverage(list(CAPS), "long", {"card.kw"}, {"cap.plan.broll": "no concrete thing is named"}),
                         ([], ["piece.ring"]))
        self.assertEqual(C.coverage(list(CAPS), "long", {"card.kw"}, {"cap.plan.broll": "  "})[0], ["plan.broll"])  # no reason
        self.assertEqual(C.coverage(list(CAPS), "short", set(), {})[0], ["card.kw"])  # report in a short: WARN only

    def test_a_skipped_checklist_item_does_not_waive_its_features(self):  # one reason per feature (b-roll hid under graphics)
        self.assertEqual(C.coverage(list(CAPS), "long", set(), {"long.graphics": "a talk without graphics, Kamil asked"})[0],
                         ["card.kw", "plan.broll"])

    def test_used_reads_the_film_not_the_spec_file(self):
        specs = {"a": {"type": "scene", "bg": "dots", "els": [{"k": "ring", "anim": "pop"}]}, "b": {"type": "kw"}}
        edl = {"overlays": [{"id": "a", "at": 1, "dur": 3}]}  # "b" is specified but never on screen
        got = C.used({"broll": [{"q": "x"}], "grade": None, "zooms": [], "music_db": 0, "head_track": False, "audio": ""}, edl, specs)
        self.assertEqual(got, {"plan.broll", "plan.music_db", "card.scene", "bg.dots", "piece.ring", "anim.pop"})  # 0 dB is set

    def test_film_check_runs_it_for_both_forms(self):
        items = {i["id"]: i for i in json.loads((ROOT / "style" / "checklist.json").read_text())["items"]}
        for f in ("long", "short"):
            self.assertEqual(items[f"{f}.capabilities"]["metric"], "capabilities_missing")


class DesignLedgerTest(unittest.TestCase):
    def doc(self, text: str) -> Path:
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        (d / "2026-01-01-x.md").write_text(text)
        return d

    def test_each_item_and_form_gets_a_row(self):
        d = self.doc("<!-- ledger-forms: long, shorts -->\n## Order of work (one commit each)\n\n1. **Lines** drawn\n"
                     "2. **Stamps** pinned\n\n## Open\n3. **not work** outside the section\n")
        got = [i["id"] for i in D.missing(d, [])]
        self.assertEqual(got, ["design:2026-01-01-x:1:long", "design:2026-01-01-x:1:shorts",
                               "design:2026-01-01-x:2:long", "design:2026-01-01-x:2:shorts"])
        self.assertEqual(D.missing(d, [{"id": g} for g in got]), [])

    def test_a_plan_of_work_without_forms_is_refused(self):
        with self.assertRaises(ValueError):  # how 2026-11-05 got lost: a plan no gate knew about
            D.missing(self.doc("## Order of work\n1. **Lines**\n"), [])
        self.assertEqual(D.missing(self.doc("<!-- ledger-forms: none -->\n## Order of work\n1. **Lines**\n"), []), [])
        self.assertEqual(D.missing(self.doc("a design that mentions `## Order of work` in a sentence\n"), []), [])
        with self.assertRaises(ValueError):
            D.missing(self.doc("<!-- ledger-forms: posters -->\n## Order of work\n1. **Lines**\n"), [])

    def run_main(self, designs: Path, ledger: Path, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch.object(D, "DESIGNS", designs), mock.patch.object(D.research_gate, "LEDGER", ledger), \
                contextlib.redirect_stdout(out):
            rc = D.main(list(argv))
        return rc, out.getvalue()

    def test_sync_adds_each_row_once_and_check_then_passes(self):
        d = self.doc("<!-- ledger-forms: long -->\n## Order of work\n1. **Lines** drawn\n")
        led = d / "ledger.jsonl"; led.write_text(json.dumps({"id": "other", "status": "done"}) + "\n")
        self.assertEqual(self.run_main(d, led, "check")[0], 1)
        self.assertEqual(self.run_main(d, led, "sync")[0], 0)
        self.assertEqual(self.run_main(d, led, "sync")[0], 0)  # idempotent: nothing new the second time
        rows = [json.loads(x) for x in led.read_text().splitlines()]
        self.assertEqual([r["id"] for r in rows], ["other", "design:2026-01-01-x:1:long"])
        self.assertEqual(rows[1]["status"], "todo")
        self.assertEqual(self.run_main(d, led, "check")[0], 0)

    def test_a_missing_ledger_is_a_fail_line_not_a_traceback(self):
        d = self.doc("no plan here\n")
        rc, out = self.run_main(d, d / "nope.jsonl", "check")
        self.assertEqual(rc, 1)
        self.assertIn("FAIL research ledger", out)

    def test_the_repo_designs_all_have_rows(self):
        if not D.research_gate.LEDGER.exists(): self.skipTest("no research ledger on this machine")
        ledger = [json.loads(x) for x in D.research_gate.LEDGER.read_text().splitlines() if x.strip()]
        self.assertEqual(D.missing(D.DESIGNS, ledger), [])


if __name__ == "__main__":
    unittest.main()
