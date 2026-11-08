"""Research options of build_edl.py / beats.py (creator-study round 2 ledger): L10 zoom_every_s + part_framing, S8 hook_pos,
S9 caption_emph, S16 hook_show, S19 layout "split_full". Each is opt-in and leaves its trace in the EDL ("options_used"
and its own field), so film_check can prove it was used.

  python3 -m pytest -q tests/test_research_options.py   (no ffmpeg, no render)
"""
from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import beatfx  # after the path insert: the scripts are not a package
import beats
import framing
from gfx_types import CORNER, SPLIT_FULL


def monologue(n_sent: int, per: int = 8, step: float = 0.42, gap: float = 0.08):
    """one long talking stretch: n_sent sentences of `per` words, no pause long enough to cut"""
    W, t = [], 1.0
    for s in range(n_sent):
        for k in range(per):
            txt = f" słowo{s}x{k}" + ("." if k == per - 1 else "," if k == 3 else "")
            W.append((round(t, 3), round(t + step - gap, 3), txt)); t += step
    return W


class Plan:
    """a work dir with words, silences and specs; run(**keys) builds the EDL with build_edl.py"""

    def __init__(self, test: unittest.TestCase, W, sil=None, specs=None):
        self.d = Path(tempfile.mkdtemp(prefix="research-opts-"))
        test.addCleanup(shutil.rmtree, self.d, True)
        self.W = W
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": round(a * 1000), "to": round(b * 1000)}, "text": t} for a, b, t in W]}))
        end = W[-1][1]
        (self.d / "rec.sil").write_text(sil or f"silence_start: 0\nsilence_end: {W[0][0]}\nsilence_start: {end + 0.2}\nsilence_end: {end + 2}\n")
        (self.d / "specs.json").write_text(json.dumps(specs or []))

    def run(self, **keys):
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, len(self.W) - 1]], "edl_out": "edl.json",
                "drift": 0, **keys}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def edl(self, **keys) -> dict:
        r = self.run(**keys)
        if r.returncode:
            raise AssertionError(r.stderr)
        return json.loads((self.d / "edl.json").read_text())

    def dialogues(self, layer: int = 0) -> list[str]:
        return [ln.split(",", 9)[9] for ln in (self.d / "c.ass").read_text().splitlines() if ln.startswith(f"Dialogue: {layer},")]


def found(rx: str, text: str) -> tuple[str, ...]:
    """the groups of rx in text; no match fails the test with the pattern"""
    m = re.search(rx, text)
    if m is None:
        raise AssertionError(f"{rx!r} not in {text[:200]!r}")
    return m.groups()


def level(seg: dict) -> float:
    z = seg["zoom"]
    return z["a"] if isinstance(z, dict) else z


def runs(segs: list[dict]) -> list[tuple[float, float]]:
    """(level, seconds) of every framing: consecutive pieces at one level are one framing"""
    out: list[list[float]] = []
    for s in segs:
        d = s["out"] - s["in"]
        if out and abs(out[-1][0] - level(s)) < 1e-6: out[-1][1] += d
        else: out.append([level(s), d])
    return [(a, b) for a, b in out]


class ZoomEverySTest(unittest.TestCase):  # ledger L10
    def setUp(self):
        self.p = Plan(self, monologue(30))  # ~100 s without a jump cut

    def test_without_the_key_one_shot_and_no_trace(self):
        e = self.p.edl()
        self.assertEqual(len(e["segments"]), 1)
        self.assertNotIn("options_used", e)
        self.assertNotIn("framing", e)

    def test_a_framing_change_at_least_every_n_seconds_at_sentence_ends(self):
        e = self.p.edl(zoom_every_s=30)
        segs = e["segments"]
        self.assertGreaterEqual(len(segs), 4)
        self.assertTrue(all(d <= 30.01 for _, d in runs(segs)), runs(segs))
        ends = {round((a[1] + b[0]) / 2, 3) for a, b in pairwise(self.p.W) if a[2].endswith(".")}
        for a, b in pairwise(segs):
            self.assertEqual(a["out"], b["in"])  # contiguous: the same sound, a new framing
            self.assertIn(b["in"], ends)  # cut in the gap after a sentence
            self.assertEqual(b["framing"], "every_s")
        self.assertEqual([level(s) for s in segs[:4]], [1.0, 1.15, 1.0, 1.15])
        self.assertEqual(e["options_used"], {"zoom_every_s": 30})
        self.assertLessEqual(e["framing"]["max_still"], 30)
        self.assertEqual(e["framing"]["changes"], len(segs) - 1)

    def test_bad_values_are_named_errors(self):
        for bad in (2, 500, True, "30"):
            with self.subTest(bad=bad):
                r = self.p.run(zoom_every_s=bad)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("zoom_every_s:", r.stderr)


class PartFramingTest(unittest.TestCase):  # ledger L10
    def setUp(self):
        self.p = Plan(self, monologue(12))

    def check_parts(self, e: dict, starts: list[int]):
        segs = e["segments"]
        opened = {s["part"]: s for s in segs if s.get("framing") == "part"}
        self.assertEqual(sorted(opened), [0, 1, 2])
        self.assertIs(opened[0], segs[0])  # part 0 opens the film at A: its first piece, no cut needed
        for n in (1, 2):
            w = starts[n]
            self.assertTrue(self.p.W[w - 1][1] <= opened[n]["in"] <= self.p.W[w][0])  # in the gap before the part's first word
            self.assertEqual(level(opened[n]), 1.2 if n % 2 else 1.0)  # B on odd parts, A on even ones

    def test_a_list_of_part_starts(self):
        e = self.p.edl(part_framing=[0, 32, 64])
        self.check_parts(e, [0, 32, 64])
        self.assertEqual(e["options_used"], {"part_framing": [0, 32, 64]})
        self.assertEqual(e["framing"]["parts"], 3)

    def test_true_reads_story_json_beside_the_plan(self):
        (self.p.d / "story.json").write_text(json.dumps({"parts": [{"id": "a", "start_word": 0}, {"id": "b", "start_word": 40},
                                                                   {"id": "c", "start_word": 72}]}))
        self.check_parts(self.p.edl(part_framing=True), [0, 40, 72])

    def test_named_errors(self):
        r = self.p.run(part_framing=True)  # no story.json
        self.assertNotEqual(r.returncode, 0); self.assertIn("story.json", r.stderr)
        for bad in ([0, 9999], [], "yes", [True]):
            with self.subTest(bad=bad):
                r = self.p.run(part_framing=bad)
                self.assertNotEqual(r.returncode, 0); self.assertIn("part_framing:", r.stderr)


class FramingRulesTest(unittest.TestCase):  # framing.assign on made-up pieces
    def test_never_three_tight_framings_in_a_row(self):
        rnd = random.Random(7)
        for case in range(200):
            W, t, segs = [], 0.0, []
            for _ in range(rnd.randint(2, 12)):
                n = rnd.randint(2, 40); s0 = t
                for k in range(n):
                    W.append((t, t + 0.35, f" w{k}" + ("." if rnd.random() < 0.2 else ""))); t += 0.42
                segs.append([s0, t - 0.05, "end"]); t += rnd.choice((0.1, 1.2))
            parts = sorted(rnd.sample(range(len(W)), rnd.randint(0, 4)))
            opts = {"every": rnd.choice((None, 8.0, 15.0)), "parts": parts or None}
            out, _ = framing.assign(framing.part_pieces(segs, W, parts), W, [1.0, 1.15], opts, exact=rnd.random() < 0.5)
            tights = 0
            for lv, _ in runs(out):
                tights = tights + 1 if lv > 1.01 else 0
                self.assertLessEqual(tights, 2, (case, runs(out)))
            self.assertTrue(all(s["out"] > s["in"] for s in out))

    def test_cut_point_prefers_a_sentence_end_over_a_later_comma(self):
        W = [(0.0, 0.4, " a"), (0.5, 0.9, " b."), (1.0, 1.4, " c,"), (1.5, 1.9, " d")]
        self.assertEqual(framing.cut_point(W, 0.0, 1.9, 0.0, 1.9), 0.95)
        self.assertEqual(framing.cut_point(W, 0.0, 1.9, 1.0, 1.9), 1.45)
        self.assertIsNone(framing.cut_point(W, 0.0, 1.9, 1.95, 2.0))


class HookPosTest(unittest.TestCase):  # ledger S8
    def setUp(self):
        self.p = Plan(self, monologue(4, step=0.5))  # 16 s

    def keys(self, **extra):
        return {"vertical": True, "ass_out": "c.ass", "hook_text": "Trzy narzędzia", "hook_dur": 3.0, **extra}

    def test_default_keeps_the_top_band_and_no_punch(self):
        e = self.p.edl(**self.keys())
        (hook,) = self.p.dialogues(1)
        self.assertTrue(hook.startswith("{\\fad(0,250)\\bord14}"))
        self.assertNotIn("hook_punch", e); self.assertNotIn("options_used", e)

    def test_mid_puts_the_title_mid_screen_above_the_corner_circle_and_punches_when_it_leaves(self):
        e = self.p.edl(**self.keys(hook_pos="mid"))
        (hook,) = self.p.dialogues(1)
        y = int(found(r"\\pos\(540,(\d+)\)", hook)[0])
        self.assertTrue(0.40 * 1920 <= y <= 0.50 * 1920)
        self.assertLess(y + 120, CORNER["y"])  # 2 lines of 84 px in their box end above the face circle
        self.assertEqual(e["hook_pos"], "mid"); self.assertEqual(e["hook_y"], y)
        self.assertEqual(e["options_used"], {"hook_pos": "mid"})
        hp = e["hook_punch"]
        self.assertLessEqual(abs(hp["at"] - 3.0), 0.25)
        seg = e["segments"][hp["seg"]]
        self.assertTrue(seg["hook_punch"])
        self.assertGreater(seg["zoom"]["b"], seg["zoom"]["a"] + 0.1)

    def test_a_zoom_step_already_there_is_the_picture_change(self):
        out = [{"in": 0.0, "out": 2.9, "zoom": 1.0}, {"in": 4.0, "out": 9.0, "zoom": 1.15}]
        self.assertEqual(framing.hook_punch(out, set(), 3.0, False)["how"], "zoom_step")
        out = [{"in": 0.0, "out": 9.0, "zoom": 1.0}]
        self.assertEqual(framing.hook_punch(out, {0}, 3.0, False), {"at": None, "why": "a card covers the face then"})

    def test_named_errors(self):
        r = self.p.run(**self.keys(hook_pos="middle"))
        self.assertNotEqual(r.returncode, 0); self.assertIn("hook_pos:", r.stderr)
        r = self.p.run(vertical=True, ass_out="c.ass", hook_pos="mid")  # no hook_text
        self.assertNotEqual(r.returncode, 0); self.assertIn("hook_text", r.stderr)


class CaptionEmphTest(unittest.TestCase):  # ledger S9
    def setUp(self):
        words = ["Zbudowałem", "to", "w", "40", "godzin.", "Klient", "dostaje", "odpowiedź.", "Na", "to", "i", "tak."]
        self.p = Plan(self, [(1.0 + 0.5 * k, 1.4 + 0.5 * k, " " + w) for k, w in enumerate(words)])
        self.acc = "&HC4E22D&"

    def lines(self, **keys):
        self.e = self.p.edl(vertical=True, ass_out="c.ass", **keys)
        return self.p.dialogues()

    def test_default_is_the_karaoke_line(self):
        ls = self.lines()
        self.assertTrue(all(ln.count(self.acc) == 1 for ln in ls))
        self.assertNotIn("caption_emph", self.e)

    def test_key_colours_one_content_word_a_line_a_number_first(self):
        ls = self.lines(caption_emph="key")
        self.assertTrue(all(ln.count("\\c" + self.acc) <= 1 for ln in ls))
        accented = {found(r"\\c" + re.escape(self.acc) + r"\}([^{]+)\{", ln)[0] for ln in ls if self.acc in ln}
        self.assertIn("40", accented)  # "W 40 GODZIN": the number, not the noun
        self.assertIn("ODPOWIEDŹ", accented)  # caps stay: caption_case is the plan's choice
        self.assertFalse(accented & {"W", "NA", "TO", "I"})  # never a preposition or a filler
        self.assertTrue(any(self.acc not in ln for ln in ls))  # "na to i tak": no content word, no colour
        self.assertEqual(self.e["caption_emph"]["mode"], "key")
        self.assertGreater(self.e["caption_emph"]["lines"], self.e["caption_emph"]["keyed"])
        self.assertEqual(self.e["options_used"], {"caption_emph": "key"})

    def test_scale_grows_the_key_word_only(self):
        ls = self.lines(caption_emph="key", caption_emph_scale=1.6)
        keyed = [ln for ln in ls if self.acc in ln]
        self.assertTrue(all("\\fs147}" in ln and "\\fs92}" in ln for ln in keyed))  # 92 x 1.6, back to 92 after it
        self.assertEqual(self.e["caption_emph"]["scale"], 1.6)

    def test_named_errors(self):
        for keys in ({"caption_emph": "all"}, {"caption_emph_scale": 1.6}, {"caption_emph": "key", "caption_emph_scale": 3},
                     {"caption_emph": "key", "caption_ahead": "dim"}):
            with self.subTest(keys=keys):
                r = self.p.run(vertical=True, ass_out="c.ass", **keys)
                self.assertNotEqual(r.returncode, 0); self.assertIn("caption_emph", r.stderr)


GRAMMAR = {"detect": {"max_sentence": 30, "gfx_min_gap": 4.0}, "auto_gfx": {"short": []}, "icons": {"agent|bot": "bot", "": "hash"}}


class HookShowTest(unittest.TestCase):  # ledger S16
    def setUp(self):
        icons = Path(tempfile.mkdtemp(prefix="icons-")); self.addCleanup(shutil.rmtree, icons, True)
        for n in ("bot", "workflow", "database"): (icons / f"{n}.svg").write_text("<svg/>")
        self.addCleanup(setattr, beatfx, "ICONS", beatfx.ICONS); beatfx.ICONS = str(icons)
        text = "Claude, n8n i Supabase robią całą robotę za mnie. Reszta to detale."
        self.W = [(1.0 + 0.45 * k, 1.35 + 0.45 * k, " " + w) for k, w in enumerate(text.split())]
        self.plan = {"keeps": [[0, len(self.W) - 1]], "vertical": True, "name": "s1", "gfx_lead": -0.12,
                     "hook_assets": {"claude": "bot", "n8n": "workflow", "supabase": "database"}}

    def test_without_the_key_nothing_changes(self):
        self.plan.pop("hook_assets")
        self.assertEqual(beats.make_gfx(self.plan, [], self.W, GRAMMAR, []), [])
        self.assertNotIn("hook_show_report", self.plan)

    def test_three_items_three_cards_each_from_its_word(self):
        self.plan["hook_show"] = True
        specs = beats.make_gfx(self.plan, [], self.W, GRAMMAR, [])
        self.assertEqual([s["text"] for s in specs], ["Claude", "n8n", "Supabase"])
        self.assertEqual([s["icon"] for s in specs], ["bot", "workflow", "database"])
        self.assertTrue(all(s["type"] == "kw" and s["canvas"] == "v" and s["beat"] == "hook_show" for s in specs))
        self.assertTrue(all(0.5 <= s["dur"] <= 1.2 for s in specs))
        for g in self.plan["gfx"]:
            start = self.W[g["word"]][0] + g["lead"]
            self.assertTrue(self.W[g["word"]][0] - 0.2 <= start <= self.W[g["word"]][0])
        self.assertEqual(self.plan["hook_show_report"]["missing"], [])
        self.assertEqual(beats.make_gfx(self.plan, [], self.W, GRAMMAR, specs), [])  # idempotent

    def test_an_item_without_a_picture_is_reported_and_no_card_comes(self):
        self.plan["hook_show"] = True; del self.plan["hook_assets"]["supabase"]
        self.assertEqual(beats.make_gfx(self.plan, [], self.W, GRAMMAR, []), [])
        self.assertEqual(self.plan["hook_show_report"]["missing"], ["Supabase"])
        self.assertIn("rewrite the hook", self.plan["hook_show_report"]["why"])

    def test_a_top_band_hook_title_blocks_the_cards(self):
        self.plan.update(hook_show=True, hook_text="Trzy narzędzia")
        self.assertEqual(beats.make_gfx(self.plan, [], self.W, GRAMMAR, []), [])
        self.assertIn("hook_pos", self.plan["hook_show_report"]["why"])
        self.plan["hook_pos"] = "mid"
        self.assertEqual(len(beats.make_gfx(self.plan, [], self.W, GRAMMAR, [])), 3)

    def test_list_detection(self):
        def items(text):
            W = [(k * 0.5, k * 0.5 + 0.4, " " + w) for k, w in enumerate(text.split())]
            return [" ".join(W[i][2].strip(" ,.") for i in it) for it in beats.hook_items(list(range(len(W))), W)]
        self.assertEqual(items("Zbudowałem to na Claude, n8n i Supabase w tydzień."), ["Claude", "n8n", "Supabase"])
        self.assertEqual(items("Masz Google Sheets, Airtable, Notion oraz Excel."), ["Google Sheets", "Airtable", "Notion", "Excel"])
        self.assertEqual(items("Claude i n8n robią robotę."), [])  # two things are not a list

    def test_the_edl_names_the_hook_cards(self):
        self.plan["hook_show"] = True
        specs = beats.make_gfx(self.plan, [], self.W, GRAMMAR, [])
        p = Plan(self, self.W, specs=specs)
        e = p.edl(vertical=True, ass_out="c.ass", hook_show=True, gfx=self.plan["gfx"], gfx_specs="specs.json", gfx_dir="g",
                  hook_show_report=self.plan["hook_show_report"])
        self.assertEqual(e["hook_show"]["cards"], [s["id"] for s in specs])
        self.assertEqual(e["options_used"], {"hook_show": True})
        t0 = e["segments"][0]["in"]
        for o, g in zip(e["overlays"], self.plan["gfx"], strict=True):
            w = self.W[g["word"]][0] - t0  # film time of the word (one piece from t0)
            self.assertTrue(w - 0.2 <= o["at"] <= w + 1e-3, (o, w))


class SplitFullTest(unittest.TestCase):  # ledger S19
    def setUp(self):
        self.W = [(1.0, 1.5, " a"), (1.6, 2.9, " b"), (3.0, 3.5, " c"), (4.05, 4.5, " d")]

    def build(self, spec: dict, **extra):
        self.p = Plan(self, self.W, specs=[{"id": "w1", "type": "web", "dur": 2.5, "url": "https://example.com/", "canvas": "v", **spec}])
        return self.p.run(vertical=True, ass_out="c.ass", gfx=[{"id": "w1", "word": 1}], gfx_specs="specs.json", gfx_dir="g", **extra)

    def overlay(self, spec: dict) -> dict:
        r = self.build(spec)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.e = json.loads((self.p.d / "edl.json").read_text())
        (o,) = self.e["overlays"]
        return o

    def test_split_full_puts_the_face_in_the_bottom_half_and_the_captions_on_the_seam(self):
        o = self.overlay({"layout": "split_full"})
        self.assertTrue(o["split"]); self.assertFalse(o["pip"])
        self.assertEqual(o["layout"], "split_full")
        self.assertEqual(o["face_box"], [0, 960, 1080, 960])
        self.assertEqual(o["caption_y"], SPLIT_FULL["caption_y"])
        self.assertTrue(any("\\pos(540,960)" in ln for ln in self.p.dialogues()))
        self.assertEqual(self.e["options_used"], {"split_full": ["w1"]})
        self.assertEqual(self.e["segments"][0]["zoom"], 1.0)  # no punch-in under the box, as under a "split" card

    def test_default_split_is_unchanged(self):
        o = self.overlay({})
        self.assertNotIn("layout", o); self.assertNotIn("face_box", o)
        self.assertNotIn("options_used", self.e)

    def test_meme_and_float_take_it_a_scene_or_a_16_9_card_does_not(self):
        o = self.overlay({"type": "float", "layout": "split_full", "html": "<b>x</b>"})
        self.assertEqual(o["face_box"], [0, 960, 1080, 960])
        for spec in ({"type": "scene", "layout": "split_full", "els": []}, {"type": "kw", "layout": "split_full", "text": "x"}):
            with self.subTest(spec=spec):
                r = self.build(spec)
                self.assertNotEqual(r.returncode, 0); self.assertIn("split_full", r.stderr)

    def test_render_draws_the_card_in_the_top_half(self):  # gfx/render.mjs keeps a box for the layout build_edl accepts
        js = (ROOT / "gfx" / "render.mjs").read_text()
        _, y, _, view = map(int, found(r"WIN_V = \{.*split_full: \{ x: (\d+), y: (\d+), w: (\d+), view: (\d+) \}", js))
        self.assertLess(y + 122 + view + 18 + 34, SPLIT_FULL["caption_y"] - 46)  # chrome + view + source line above the captions
        box = found(r"MEME_BOX = \{.*split_full: \{ x: \d+, w: \d+, y: (\d+), h: (\d+) \}", js)
        self.assertLess(sum(map(int, box)) + 14 + 30, SPLIT_FULL["caption_y"] - 46)


if __name__ == "__main__":
    unittest.main()
