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


def copy_root(case: unittest.TestCase) -> Path:
    """the files capabilities.discover reads, in a temp dir the test may break"""
    d = Path(tempfile.mkdtemp()); case.addCleanup(shutil.rmtree, d)
    for f in [*ROOT.glob("*.py"), *ROOT.glob("gfx/*.mjs"), *ROOT.glob("music/*.py"), *ROOT.glob("gfx/toons/*.svg"),
              *ROOT.glob("style/themes/*.json"), ROOT / "style" / "checklist.json", ROOT / "style" / "memes.json", ROOT / "style" / "grammar.json"]:
        rel = f.relative_to(ROOT); (d / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, d / rel)
    shutil.copytree(ROOT / "team" / "roles", d / "team" / "roles")
    case.assertEqual(C.problems(C.load(), C.discover(d), d), [])  # the copy alone is a clean map
    return d


class MapTest(unittest.TestCase):
    def test_the_map_covers_the_code(self):
        self.assertEqual(C.problems(C.load(), C.discover()), [])

    def copy_root(self) -> Path:
        return copy_root(self)

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

    def test_a_new_spec_option_or_menu_value_without_an_entry_fails(self):  # round 3 (critic 2026-11-09): options inside a card
        d = self.copy_root()
        r = d / "gfx" / "render.mjs"; r.write_text(r.read_text() + "\nconst _x = sp => sp.glow;\n")
        self.assertIn("opt.glow: in the code, not in style/capabilities.json (add it with an owner, a check and a use)",
                      C.problems(C.load(), C.discover(d), d))
        m = d / "style" / "memes.json"; memes = json.loads(m.read_text()); memes["new_one"] = {}; m.write_text(json.dumps(memes))
        self.assertIn("new_one", C.menus(d)["meme"])  # a menu shows its values live from the code: no entry per value

    def test_the_brief_lists_a_menu(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out): C.main(["brief", "dzwiekowiec"])
        self.assertIn("menu.palette (pick from): bright, cinematic, drive, lofi, tech", out.getvalue())

    def test_plan_keys_read_as_P_outside_build_edl_are_found(self):
        self.assertIn("critic_accept", C.discover()["plan"])

    def test_entries_need_a_real_owner_a_real_check_and_a_use(self):
        caps = [dict(c) for c in C.load()]
        caps[0] = {**caps[0], "owner": "nobody"}
        caps[1] = {**caps[1], "check": "long.nothing"}
        caps[2] = {**caps[2], "use": {"long": "maybe", "short": "report"}}
        caps.append({"id": "card.ghost", "kind": "card", "name": "ghost", "owner": "operator", "check": "long.punch",
                     "use": {"long": "never", "short": "report"}})
        caps.append({"id": "card.ghost2", "kind": "card", "name": "ghost2", "owner": "operator", "check": "long.punch",
                     "use": {"long": "menu", "short": "menu"}, "why": "x"})
        bad = " | ".join(C.problems(caps, C.discover()))
        for want in ("is no role card", "is no style/checklist.json item", "not one of required", "'never' needs a why",
                     "card.ghost: in style/capabilities.json, no longer in the code", "card.ghost2: use 'menu' is for kind menu only"):
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
        self.assertEqual(got, {"plan.broll", "plan.music_db", "card.scene", "bg.dots", "piece.ring", "anim.pop",  # 0 dB is set
                               "opt.type", "opt.bg", "opt.els", "pfx.k", "pfx.anim"})

    def test_used_counts_spec_options_and_default_entrances(self):
        specs = {"a": {"type": "scene", "behind": {"ratio": 0.2}, "cam": None, "els": [{"k": "stamp"}, {"k": "text"}]}}
        got = C.used({}, {"overlays": [{"id": "a"}]}, specs, C.default_anims())
        self.assertTrue({"opt.behind", "anim.drop", "anim.up"} <= got)  # stamp enters with drop, text with 'up'
        self.assertNotIn("opt.cam", got)

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



class RoundFourTest(unittest.TestCase):  # completeness critic round 3 (2026-11-09)
    def test_spec_keys_read_in_other_ways_are_found(self):
        f = C.discover()
        for k in ("bookend", "cta", "caption_y", "face_anchor", "face_zoom", "behind.clean", "behind.ratio", "beat"):
            self.assertIn(k, f["opt"])
        self.assertTrue({"hl_at", "strike_at", "pulse_at", "packet_at", "on"} <= f["pfx"])
        self.assertTrue({"layout", "theme", "beat", "tone"} <= f["menu"])

    def test_blind_spots_of_the_scan_are_closed(self):
        d = copy_root(self)
        r = d / "gfx" / "render.mjs"
        r.write_text(r.read_text().replace("const html = sp => {", "const html = sp => {\n  const zz = sp.type === 'badge' ? 1 : 0;", 1)
                     + "\nconst _y = sp => sp?.gap;\nconst _z = sp => { const { zing, zong = 1 } = sp; return zing + zong; };\n")
        b = d / "build_edl.py"; b.write_text(b.read_text() + '\nif "newkey" in P: pass\n')
        f = C.discover(d)
        self.assertIn("badge", f["card"])
        self.assertTrue({"gap", "zing", "zong"} <= f["opt"])
        self.assertIn("newkey", f["plan"])

    def test_one_member_of_a_group_is_enough(self):
        caps = [{"id": "card.scene", "check": "x", "group": "explainer", "use": {"long": "required", "short": "report"}},
                {"id": "card.slide", "check": "x", "group": "explainer", "use": {"long": "required", "short": "report"}},
                {"id": "card.kw", "check": "x", "use": {"long": "required", "short": "report"}}]
        self.assertEqual(C.coverage(caps, "long", {"card.slide"}, {})[0], ["card.kw"])
        self.assertEqual(C.coverage(caps, "long", set(), {})[0], ["card.scene", "card.slide", "card.kw"])

    def test_a_skip_needs_a_real_reason_and_a_real_id(self):
        caps = list(CAPS)
        self.assertEqual(C.coverage(caps, "long", set(), {"cap.card.kw": "ok", "cap.plan.broll": "no thing is named"})[0], ["card.kw"])
        self.assertEqual(C.bad_skips(caps, {"cap.card.kww": "a long enough reason", "cap.card.kw": True, "long.x": "y"}),
                         ["cap.card.kww: no such capability in style/capabilities.json",
                          "cap.card.kw: the reason must say why (>= 10 characters), got True"])
        import film_check
        self.assertEqual(C.SKIP_MIN, film_check.SKIP_MIN)

    def test_used_reads_nested_options_and_piece_fields(self):
        specs = {"a": {"type": "float", "behind": {"ratio": 0.3, "clean": True}},
                 "b": {"type": "scene", "els": [{"k": "chip", "hl_at": 2.0, "x": 1, "y": 1}]}}
        got = C.used({}, {"overlays": [{"id": "a"}, {"id": "b"}]}, specs)
        self.assertTrue({"opt.behind", "opt.behind.ratio", "opt.behind.clean", "pfx.hl_at", "pfx.x"} <= got)

    def test_card_end_is_judged_by_the_item_of_its_form(self):
        end = next(c for c in C.load() if c["id"] == "card.end")
        self.assertEqual((C.check_of(end, "long"), C.check_of(end, "short"), end["use"]["short"]), ("long.end", "short.end", "never"))


class RoundFiveTest(unittest.TestCase):  # completeness critic round 4 (2026-11-09)
    def test_fields_the_anchors_write_are_not_choices(self):
        d = copy_root(self)
        s = d / "gfx" / "scene_lib.mjs"
        s.write_text(s.read_text() + "\nconst _q = e => e._from ?? e.shapeless;\n")
        f = C.discover(d)
        self.assertIn("shapeless", f["pfx"])
        self.assertFalse({k for k in f["pfx"] if k.startswith("_")}, "internal _fields are not in the scan")
        self.assertIn("shape", C.discover()["pfx"])

    def test_spec_keys_of_any_stage_and_fields_inside_pieces_are_found(self):
        f = C.discover()
        self.assertIn("quote", f["opt"])  # critic.py, outside the old fixed file list
        self.assertTrue({"rows.mark", "rows.hl", "msgs.who", "count.suf", "badge.tone"} <= f["pfx"])
        self.assertNotIn("long", C.menus()["layout"])  # MEME_BOX "long" = no layout, not a choice

    def test_a_row_mark_or_a_chat_side_counts_as_used(self):
        sp = {"type": "scene", "els": [{"k": "win", "rows": ["~", {"t": "Krok 2", "mark": "ok"}]},
                                       {"k": "chat", "msgs": [{"who": "me", "t": "hej"}]}, {"k": "stat", "count": {"to": 9, "suf": "%"}}]}
        have = C.used({}, {"overlays": [{"id": "s"}]}, {"s": sp})
        self.assertTrue({"pfx.rows.mark", "pfx.rows.t", "pfx.msgs.who", "pfx.count.suf", "pfx.count.to"} <= have)

    def test_one_way_to_end_and_one_way_to_reframe_is_enough(self):
        caps = C.load()
        missing = lambda have: C.coverage(caps, "long", have, {})[0]
        self.assertNotIn("plan.end", missing({"card.end"}))
        self.assertNotIn("card.end", missing({"plan.end", "plan.end=platform"}))  # round 6: only end "platform" replaces the card
        self.assertNotIn("plan.next_video", missing(set()))  # report: long.end reads it only with end "platform"
        self.assertNotIn("plan.part_framing", missing({"plan.zoom_every_s"}))
        self.assertIn("plan.part_framing", missing(set()))

    def test_features_a_form_refuses_are_never_asked_of_it(self):
        by = {c["id"]: c for c in C.load()}
        for i in ("card.note", "card.sticker", "opt.toon", "opt.define", "opt.upto", "opt.dim_done"):
            self.assertEqual(by[i]["use"]["short"], "never", i)
        for i in ("opt.compact", "opt.pill", "opt.face_box", "opt.face_corner"):
            self.assertEqual(by[i]["use"]["long"], "never", i)
        self.assertEqual(by["plan.verified_claims"]["use"]["short"], "report")
        self.assertEqual(C.check_of(by["plan.caption_emph"], "short"), "short.options")


class RoundSixTest(unittest.TestCase):  # completeness critic round 5 (2026-11-09)
    def test_a_default_value_does_not_count_where_the_gate_wants_another(self):
        caps = C.load()
        miss = lambda plan: C.coverage(caps, "short", C.used(plan, {"overlays": []}, {}), {})[0]
        self.assertIn("plan.caption_emph", miss({"caption_emph": "active"}))
        self.assertNotIn("plan.caption_emph", miss({"caption_emph": "key"}))
        self.assertIn("plan.hook_pos", miss({"hook_pos": "top"}))
        self.assertNotIn("plan.hook_pos", miss({"hook_pos": "mid"}))
        long_miss = lambda plan: C.coverage(caps, "long", C.used(plan, {"overlays": []}, {}), {})[0]
        self.assertIn("card.end", long_miss({"end": "card"}))  # only "platform" replaces the end card
        self.assertNotIn("card.end", long_miss({"end": "platform"}))

    def test_read_along_is_asked_of_the_scene_pieces_where_the_gate_looks(self):
        sp = {"type": "scene", "els": [{"k": "term", "out": ["ok"], "read_along": [[1, 0]]}]}
        miss = C.coverage(C.load(), "long", C.used({}, {"overlays": [{"id": "s"}]}, {"s": sp}), {})[0]
        self.assertNotIn("pfx.read_along", miss)
        self.assertNotIn("opt.read_along", miss)

    def test_fields_of_spec_lists_are_found_and_counted(self):
        f = C.discover()
        self.assertTrue({"cam.z", "cam.move", "canvas_zoom.k", "canvas_zoom.on", "behind.edl"} <= f["opt"])
        have = C.used({}, {"overlays": [{"id": "s"}]}, {"s": {"type": "scene", "canvas_zoom": [{"t": 1, "on": "a", "k": 1.2}]}})
        self.assertTrue({"opt.canvas_zoom", "opt.canvas_zoom.k", "opt.canvas_zoom.on"} <= have)

    def test_other_ways_of_naming_a_card_or_reading_a_spec_are_found(self):
        d = copy_root(self)
        r = d / "gfx" / "render.mjs"
        r.write_text(r.read_text().replace("const html = sp => {", "const html = sp => {\n  if (sp.type === 'quiz' || sp.type === 'poll') return '';", 1))
        p = d / "post_check.py"
        p.write_text(p.read_text() + '\nx = spec.get("zeta")\ny = self.specs[o["id"]].get("eta")\nz = spec["theta"]["iota"]\nw = spec.get("long")\n')
        f = C.discover(d)
        self.assertTrue({"quiz", "poll"} <= f["card"])
        self.assertTrue({"zeta", "eta", "theta.iota"} <= f["opt"])
        self.assertNotIn("long", f["opt"])  # thumbs.json's lists, outside the map

    def test_want_needs_a_list_of_strings_and_a_why(self):
        caps = [dict(c) for c in C.load()]
        c = next(x for x in caps if x["id"] == "plan.hook_pos"); c["want"] = "mid"
        self.assertIn('plan.hook_pos: "want" = a list of the values that count (strings) and a why', C.problems(caps, C.discover()))


if __name__ == "__main__":
    unittest.main()
