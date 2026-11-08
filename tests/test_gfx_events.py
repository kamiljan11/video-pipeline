"""gfx_events.py + build_edl.py: what happens inside a card lands on its EDL overlay in film seconds (research ledger L16b
read_along, L17 canvas_zoom "zooms", S11 list "items", S14 camera / in-panel "moves"); a plan gfx entry can hold the cues to
their spoken words.

  python3 -m unittest tests.test_gfx_events
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import gfx_events  # after the path insert: the scripts are not a package

SCENE = {"id": "s1", "type": "scene", "dur": 8, "els": [
    {"k": "term", "id": "t", "x": 0, "y": 0, "cmd": "ls", "out": ["a", "b"], "at": 0.5, "read_along": [[2.0, 0], [3.0, 1]]},
    {"k": "chip", "id": "i1", "x": 0, "y": 600, "text": "1. plan", "item": 1, "at": 1.0},
    {"k": "chip", "id": "i2", "x": 0, "y": 700, "text": "2. kod", "item": 2, "at": 4.0, "gone": 7.5},
    {"k": "cursor", "from": [0, 0], "to": [100, 100], "at": 5.0, "click_at": 6.0}],
    "cam": [{"t": 0, "on": "t"}, {"t": 0.5, "on": "t"}, {"t": 5.0, "on": "*"}],
    "canvas_zoom": [{"t": 2.5, "on": "t"}]}


class SceneTimesTest(unittest.TestCase):
    def test_every_inner_event_in_card_seconds(self):
        t = gfx_events.scene_times(SCENE)
        self.assertEqual(t["zooms"], [2.5])
        self.assertEqual(t["read_along"], [2.0, 3.0])
        self.assertEqual(t["items"], [[1.0, 8.0], [4.0, 7.5]])
        # camera: the same framing twice is no move; the move to "*" starts 0.9 s before its stop; cursor sets off 0.7 s
        # before its click; the terminal types from at + 0.5; zoom and read-along steps
        self.assertEqual(t["moves"], [1.0, 2.0, 2.5, 3.0, 4.1, 5.3])

    def test_film_seconds_on_the_overlay_only_what_is_there(self):
        f = gfx_events.overlay_fields(SCENE, 10.0)
        self.assertEqual(f["zooms"], [12.5])
        self.assertEqual(f["items"], [[11.0, 18.0], [14.0, 17.5]])
        self.assertEqual(f["moves"][0], 11.0)
        plain = {"id": "k", "type": "kw", "dur": 2, "text": "x"}
        self.assertEqual(gfx_events.overlay_fields(plain, 3.0), {})
        still = {"id": "s", "type": "scene", "dur": 4, "els": [{"k": "chip", "x": 0, "y": 0}]}  # default camera: nothing moves
        self.assertEqual(gfx_events.overlay_fields(still, 3.0), {})

    def test_a_web_card_lists_its_read_along_marks(self):
        f = gfx_events.overlay_fields({"id": "w", "type": "web", "dur": 9, "read_along": [4, 5.5]}, 2.0)
        self.assertEqual(f, {"read_along": [6.0, 7.5], "moves": [6.0, 7.5]})

    def test_junk_in_a_spec_is_skipped_not_raised(self):  # render.mjs refuses a bad spec by name; here nothing breaks
        bad = {"id": "b", "type": "scene", "dur": 5, "els": [None, {"k": "term", "read_along": "x", "item": True}],
               "cam": [{"t": "0"}, 3], "canvas_zoom": [{"t": None}]}
        self.assertEqual(gfx_events.overlay_fields(bad, 0.0), {})


class CueTest(unittest.TestCase):
    WORDS = (11.0, 12.0, 13.0, 14.05, 15.2)  # film seconds of words 0..4; the card comes in at 10.0

    def problems(self, g, sp=SCENE, at=10.0):
        return gfx_events.cue_problems(g, sp, at, lambda w: self.WORDS[w], len(self.WORDS))

    def test_cues_on_their_words_pass(self):
        self.assertEqual(self.problems({"read_along": [1, 2]}), [])  # card 2.0 / 3.0 = the words
        self.assertEqual(self.problems({"items": [0, 3]}), [])  # item 2 at 4.0, its numeral at 4.05: a hair early is fine
        self.assertEqual(self.problems({}), [])

    def test_an_item_late_or_early_against_its_numeral_is_named_with_the_card_time(self):
        p = self.problems({"items": [3, 4]})  # items at card 1.0 / 4.0, numerals at card 4.05 / 5.2
        self.assertEqual(len(p), 1)
        self.assertIn("items off its words", p[0])
        self.assertIn("[4.05, 5.2]", p[0])
        late = {**SCENE, "els": [{**SCENE["els"][1], "at": 4.4}, {**SCENE["els"][2], "at": 5.3}]}
        p = self.problems({"items": [3, 4]}, late)  # 0.35 s after its numeral: over 0.3 (S11); the second, 0.1 s, is fine
        self.assertIn("card has [4.4]", p[0])

    def test_the_window_ends_are_allowed(self):  # -0.15 s (a hair early, like gfx_lead) and +0.3 s (S11) pass, more does not
        sp = {**SCENE, "els": [{**SCENE["els"][1], "at": 1.0}, {**SCENE["els"][2], "at": 4.05}]}  # = card times of words 0 and 3 at 10.0
        for at, ok in ((10.3, True), (9.85, True), (10.32, False), (9.83, False)):
            with self.subTest(at=at):
                self.assertEqual(self.problems({"items": [0, 3]}, sp, at) == [], ok)

    def test_a_wrong_count_or_word_index_is_named(self):
        self.assertIn("names 1 words, the card has 2", self.problems({"read_along": [0]})[0])
        self.assertIn("word indexes", self.problems({"items": [0, 9]})[0])
        self.assertIn("word indexes", self.problems({"items": "x"})[0])


class BuildEdlTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="gfx-events-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        words = [(1.0, 1.5, " a"), (1.6, 2.9, " b"), (3.0, 3.5, " c"), (4.05, 4.5, " d")]
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round(a * 1000), "to": round(b * 1000)}, "text": t} for a, b, t in words]}))
        (self.d / "rec.sil").write_text("silence_start: 0\nsilence_end: 1.0\nsilence_start: 4.6\nsilence_end: 6\n")

    def build(self, spec: dict, gfx: dict):
        (self.d / "specs.json").write_text(json.dumps([spec]))
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 3]], "edl_out": "edl.json",
                "gfx": [{"id": spec["id"], "word": 0, **gfx}], "gfx_specs": "specs.json", "gfx_dir": str(self.d)}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def overlay(self, spec: dict, gfx: dict | None = None) -> dict:
        r = self.build(spec, gfx or {})
        self.assertEqual(r.returncode, 0, r.stderr)
        (o,) = json.loads((self.d / "edl.json").read_text())["overlays"]
        return o

    def test_a_card_without_the_keys_gets_no_new_field(self):
        o = self.overlay({"id": "k", "type": "kw", "dur": 1.5, "text": "x"})
        self.assertEqual(set(o) - {"file", "at", "dur", "id", "pip"}, set())

    def test_scene_events_are_film_times_from_the_card_start(self):
        o = self.overlay(SCENE)
        at = o["at"]  # word 0 at 1.0 s of the source, the keep starts 0.1 s before it
        self.assertEqual(o["zooms"], [round(at + 2.5, 3)])
        self.assertEqual(o["read_along"], [round(at + 2.0, 3), round(at + 3.0, 3)])
        self.assertEqual(o["items"][0], [round(at + 1.0, 3), round(at + 8.0, 3)])
        self.assertIn(round(at + 4.1, 3), o["moves"])

    def test_the_plan_holds_read_along_to_its_words(self):
        # words 1 and 2 start at 1.6 and 3.0 s of the source = card 0.6 / 2.0 s (the card comes in on word 0)
        sp = {**SCENE, "els": [{**SCENE["els"][0], "read_along": [[0.6, 0], [2.05, 1]]}], "canvas_zoom": [{"t": 2.5, "on": "t"}]}
        self.overlay(sp, {"read_along": [1, 2]})
        r = self.build({**sp, "els": [{**SCENE["els"][0], "read_along": [[0.6, 0], [2.6, 1]]}]}, {"read_along": [1, 2]})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("read_along off its words", r.stderr)
        self.assertIn("[2.0]", r.stderr)


if __name__ == "__main__":
    unittest.main()
