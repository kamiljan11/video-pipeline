"""plan2 cards (research ledger plan2:L8, L9, L12, L21) on the Python side: build_edl.py timing and guards, count_check,
gfx_types, the opt-in grammar beats. gfx/test/cards.test.mjs covers their HTML. A plan without the new fields is unchanged.

  python3 -m unittest tests.test_plan2_cards
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import beatfx  # after the path insert: the scripts are not a package
import beats
import count_check
import gfx_types

N_WORDS = 1300  # word i is said from 1.0 + 0.5 i s; one keep from 0.9 s, so film time = source time - 0.9


def said(i: int) -> float:
    return round(1.0 + 0.5 * i - 0.9, 3)


class BuildEdlTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="plan2-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round((1.0 + 0.5 * i) * 1000), "to": round((1.4 + 0.5 * i) * 1000)}, "text": f" w{i}"}
            for i in range(N_WORDS)]}))
        (self.d / "rec.sil").write_text("")

    def build(self, specs, gfx, **extra):
        (self.d / "gfx_specs.json").write_text(json.dumps(specs))
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, N_WORDS - 1]], "edl_out": "edl.json",
                "gfx_specs": "gfx_specs.json", "gfx_dir": "gfx", **extra, "gfx": gfx}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def overlays(self, specs, gfx, **extra):
        r = self.build(specs, gfx, **extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return {o["id"]: o for o in json.loads((self.d / "edl.json").read_text())["overlays"]}, r.stdout

    def refused(self, specs, gfx, msg, **extra):
        r = self.build(specs, gfx, **extra)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(msg, r.stderr)

    def test_legacy_cards_keep_their_overlay(self):  # no new key in the EDL of an old plan
        specs = [{"id": "l", "type": "list", "text": "x", "items": ["a", "b"], "dur": 4}, {"id": "c", "type": "chap", "text": "T", "sub": "1", "dur": 3},
                 {"id": "w", "type": "lower", "text": "Kamil", "sub": "MAS", "dur": 4}]
        ovs, _ = self.overlays(specs, [{"id": "l", "word": 10}, {"id": "c", "word": 30}, {"id": "w", "word": 50}])
        for o in ovs.values(): self.assertEqual(set(o), {"file", "at", "dur", "id", "pip"})

    # ---- L8
    def test_item_words_time_a_stacked_list(self):
        sp = {"id": "l", "type": "list", "text": "x", "items": ["a", "b", "c"], "dim_done": True, "delays": [0.0, 5.0, 10.0], "dur": 12}
        ovs, out = self.overlays([sp], [{"id": "l", "word": 10, "item_words": [10, 20, 30]}])
        o = ovs["l"]
        self.assertEqual(o["variant"], "stack")
        self.assertEqual(o["items_said"], [said(10), said(20), said(30)])
        self.assertEqual(o["delays"], [0.0, 5.0, 10.0])
        self.assertEqual(o["item_lead"], 0.0)
        self.assertNotIn("WARN", out)
        self.assertEqual(count_check.early_items(o), [])

    def test_an_item_shown_before_its_word_stops_the_build_with_the_delays(self):
        sp = {"id": "l", "type": "list", "text": "x", "items": ["a", "b", "c"], "dur": 12}  # default delays 0, 1, 2 s: items 2, 3 early
        r = self.build([sp], [{"id": "l", "word": 10, "item_words": [10, 20, 30]}])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("item(s) [2, 3] on screen before they are said", r.stderr)
        self.assertIn('"delays": [0.02, 5.02, 10.02]', r.stderr)

    def test_lead_moves_the_said_time_and_a_late_item_only_warns(self):
        sp = {"id": "l", "type": "list", "text": "x", "items": ["a", "b"], "delays": [0.0, 6.0], "dur": 9}
        ovs, out = self.overlays([sp], [{"id": "l", "word": 10, "item_words": [10, 20]}], gfx_lead=-0.12)
        self.assertIn("WARN l: item(s) [2] come in more than 0.3 s after their word", out)
        self.assertEqual(ovs["l"]["item_lead"], -0.12)
        self.assertNotIn("variant", ovs["l"])  # a plain list with item_words: timed, no new look

    def test_upto_shows_the_earlier_items_from_the_start(self):
        sp = {"id": "u", "type": "list", "text": "x", "items": ["a", "b", "c"], "upto": 3, "dim_done": True, "delays": [None, None, 0.1], "dur": 4}
        ovs, _ = self.overlays([sp], [{"id": "u", "word": 40, "item_words": [10, 20, 40]}])
        self.assertEqual(ovs["u"]["variant"], "upto")
        self.assertEqual(ovs["u"]["delays"], [None, None, 0.1])
        self.refused([sp], [{"id": "u", "word": 40, "item_words": [10, 45, 50]}], "items 1..2 are on the card from its start")

    def test_bad_item_words_and_a_short_hold_are_named(self):
        sp = {"id": "l", "type": "list", "text": "x", "items": ["a", "b"], "delays": [0.0, 5.0], "dur": 6}
        self.refused([sp], [{"id": "l", "word": 10, "item_words": [10]}], "item_words = 2 kept word indexes in order")
        self.refused([sp], [{"id": "l", "word": 10, "item_words": [20, 10]}], "item_words = 2 kept word indexes in order")
        self.refused([sp], [{"id": "l", "word": 10, "item_words": [10, 20]}], "the last item needs 1.5 s on screen")
        self.refused([{"id": "k", "type": "kw", "text": "x", "dur": 3}], [{"id": "k", "word": 10, "item_words": [10]}], 'item_words is for a "list" card')
        # a spec the renderer would refuse is a named stop here too (build_edl may run before a render)
        for patch, msg in (({"items": []}, 'needs "items"'), ({"upto": 0}, "upto = a whole number 1..2"), ({"upto": "2"}, "upto = a whole number"),
                           ({"delays": [0.0, "5"]}, "delays = seconds >= 0 or null"), ({"delays": [-1, 5]}, "delays = seconds")):
            with self.subTest(patch=patch):
                self.refused([{**sp, "dur": 9, **patch}], [{"id": "l", "word": 10, "item_words": [10, 20]}], msg)


    # ---- L9
    def test_roadmap_and_part_tag_share_one_drawing(self):
        parts = ["Pamięć", "Narzędzia", "Agenci"]
        specs = [{"id": "m0", "type": "chap", "chap_style": "roadmap", "parts": parts, "current": 0, "dur": 6},
                 {"id": "c2", "type": "chap", "chap_style": "roadmap", "parts": parts, "current": 2, "dur": 4},
                 {"id": "t3", "type": "chap", "chap_style": "part_tag", "parts": parts, "current": 3, "dur": 5}]
        gfx = [{"id": "m0", "word": 20}, {"id": "c2", "word": 200}, {"id": "t3", "word": 400}]
        ovs, _ = self.overlays(specs, gfx)
        self.assertEqual([ovs[k]["variant"] for k in ("m0", "c2", "t3")], ["roadmap", "roadmap", "part_tag"])
        specs[2]["parts"] = [*parts, "Koszty"]
        self.refused(specs, gfx, 'roadmap / part_tag cards with different "parts" in one film')

    def test_a_part_tag_is_not_a_separate_screen(self):
        tag = {"type": "chap", "chap_style": "part_tag"}
        self.assertTrue(gfx_types.is_part_tag(tag))
        self.assertFalse(gfx_types.is_full(tag))
        self.assertTrue(gfx_types.is_full({"type": "chap"}))
        self.assertTrue(gfx_types.is_full({"type": "chap", "chap_style": "roadmap"}))

    # ---- L12
    def test_define_holds_its_reading_time_and_six_seconds(self):
        sp = {"id": "d", "type": "lower", "define": True, "text": "RAG", "sub": "model szuka w dokumentach", "dur": 6}
        ovs, _ = self.overlays([sp], [{"id": "d", "word": 10}])
        self.assertEqual(ovs["d"]["variant"], "define")
        long_def = {**sp, "sub": " ".join(["słowo"] * 19), "dur": 7}  # 20 words: 1.2 x 4 + 0.35 x 16 = 10.4 s
        self.refused([long_def], [{"id": "d", "word": 10}], "a define card needs 10.4 s on screen")

    # ---- L21
    def test_note_rules(self):
        note = {"id": "n", "type": "note", "text": "Link w opisie", "dur": 4}
        ovs, _ = self.overlays([note], [{"id": "n", "word": 10}])
        self.assertEqual(ovs["n"]["variant"], "note")
        self.assertEqual(ovs["n"]["pip"], False)
        self.refused([{**note, "text": " ".join(["raz"] * 14)}], [{"id": "n", "word": 10}], "a note card needs 8.3 s")
        two = [note, {**note, "id": "n2"}]
        self.refused(two, [{"id": "n", "word": 10}, {"id": "n2", "word": 500}], "at most one note per 300 s")  # 245 s apart
        ovs, _ = self.overlays(two, [{"id": "n", "word": 10}, {"id": "n2", "word": 700}])  # 345 s apart
        lower = {"id": "w", "type": "lower", "text": "Kamil", "sub": "MAS", "dur": 4}
        self.refused([note, lower], [{"id": "n", "word": 10}, {"id": "w", "word": 12}], "share the bottom-left corner at once")

    def test_plan2_cards_are_long_only(self):
        note = {"id": "n", "type": "note", "text": "Link w opisie", "dur": 4}
        self.refused([note], [{"id": "n", "word": 10}], "a note card is 16:9 only", vertical=True)


class PartTagSoundTest(unittest.TestCase):
    """music/make_beds.py: a part_tag (corner tag over the speaker) pops like a lower third; a full chapter card keeps its
    whoosh (v1) / riser + impact (v2) before it comes in"""

    def sfx_before(self, chap: dict, style: str | None) -> float:
        d = Path(tempfile.mkdtemp(prefix="beds-"))
        self.addCleanup(shutil.rmtree, d, True)
        specs = [{"id": "w", "type": "lower", "text": "Kamil", "sub": "MAS", "dur": 3}, {"id": "c", "type": "chap", "dur": 3, **chap}]
        (d / "gfx_specs.json").write_text(json.dumps(specs))
        edl = {"segments": [{"src": "A", "in": 0.0, "out": 8.0, "zoom": 1.0}], "overlays": [{"id": "w", "at": 1.0, "dur": 3}, {"id": "c", "at": 5.0, "dur": 3}],
               "gfx_specs": str(d / "gfx_specs.json"), **({"sfx_style": style} if style else {})}
        (d / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "music" / "make_beds.py"), str(d / "edl.json"), str(d / "beds")], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        with wave.open(str(d / "beds" / "sfx.wav")) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2)[:, 0].astype(float)
        sr = 44100
        return float(np.abs(x[int(4.3 * sr):int(4.98 * sr)]).max())  # the 0.7 s before the card at 5.0 s

    def test_part_tag_has_no_chapter_sweep(self):
        for style in (None, "v2"):
            with self.subTest(style=style):
                self.assertGreater(self.sfx_before({"text": "T", "sub": "1"}, style), 1000)
                self.assertLess(self.sfx_before({"chap_style": "part_tag", "parts": ["a", "b"], "current": 2}, style), 50)


class CountCheckTest(unittest.TestCase):
    def test_an_item_before_its_word_is_named(self):
        o = {"id": "l", "at": 10.0, "dur": 8, "delays": [0.0, 1.0, 4.0], "items_said": [10.0, 13.0, 14.0], "item_lead": -0.12}
        self.assertEqual(count_check.early_items(o), ["l: item 2 on screen at 11.00 s, said at 13.00 s"])
        self.assertEqual(count_check.problems([o], {"l": {"id": "l", "type": "list", "items": ["a", "b", "c"]}}, []),
                         ["l: item 2 on screen at 11.00 s, said at 13.00 s"])
        self.assertEqual(count_check.early_items({"id": "x", "at": 1.0, "dur": 3}), [])  # a card without item_words

    def test_roadmap_and_upto_counts(self):
        ov = [{"id": "g", "at": 10.0, "dur": 6.0}]
        road = {"id": "g", "type": "chap", "chap_style": "roadmap", "parts": ["a", "b", "c"], "current": 0}
        self.assertEqual(count_check.problems(ov, {"g": road}, [(9.0, "trzy")]), [])
        self.assertEqual(count_check.problems(ov, {"g": road}, [(9.0, "cztery")]), ["g: 3 on the card, says [4]"])
        upto = {"id": "g", "type": "list", "items": ["a", "b", "c", "d"], "upto": 2}
        for w in ("dwa", "cztery"):
            self.assertEqual(count_check.problems(ov, {"g": upto}, [(10.0, w)]), [], w)
        self.assertEqual(count_check.problems(ov, {"g": upto}, [(10.0, "pięć")]), ["g: 4 on the card, says [5]"])


def words(text: str):
    return [(1.0 + 0.4 * i, 1.3 + 0.4 * i, f" {w}") for i, w in enumerate(text.split())]


class OptInBeatTest(unittest.TestCase):
    TEXT = "Dzisiaj pokażę wam coś dużego. RAG czyli wyszukiwanie w dokumentach firmy. Link w opisie filmu."

    def setUp(self):
        self.g = beats.load_grammar()
        self.W = words(self.TEXT)
        self.plan = {"keeps": [[0, len(self.W) - 1]]}

    def types(self, plan, grammar=None):
        return [b["type"] for b in beats.detect(plan, self.W, grammar or self.g)]

    def test_without_beat_opt_in_the_moments_are_as_before(self):
        before = copy.deepcopy(self.g)
        for k in ("define", "note"): before["beats"].pop(k)  # the grammar before plan2:L12 / L21
        self.assertEqual(self.types(self.plan), self.types(self.plan, before))
        self.assertNotIn("define", self.types(self.plan))
        self.assertIn("cta", self.types(self.plan))  # "link w opisie" stays a cta

    def test_beat_opt_in_detects_define_and_note(self):
        got = self.types({**self.plan, "beat_opt_in": ["define", "note"]})
        self.assertIn("define", got)
        self.assertIn("note", got)
        self.assertNotIn("cta", got)  # the note (priority 86) takes "link w opisie"
        self.assertEqual(self.g["effects"]["long"]["define"]["gfx"], "define")
        self.assertEqual(self.g["effects"]["long"]["note"]["gfx"], "note")

    def test_bad_beat_opt_in_and_opt_in_values_are_named(self):
        for bad in (["stat"], "define", [1]):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "beat_opt_in"):
                beats.detect({**self.plan, "beat_opt_in": bad}, self.W, self.g)
        raw = json.loads((ROOT / "style" / "grammar.json").read_text(encoding="utf-8"))
        raw["beats"]["define"]["opt_in"] = "yes"
        with self.assertRaisesRegex(ValueError, "beats.define.opt_in"):
            beatfx._validate(raw, "grammar.json")


if __name__ == "__main__":
    unittest.main()
