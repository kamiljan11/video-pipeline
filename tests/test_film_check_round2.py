"""film_check metrics for the round 2 long research (creator-study/round2/PLAN2.md L2-L24): each must pass a film that
follows the rule and name what a film that breaks it misses."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import film_check

STORY = {"parts": [{"id": "intro", "title": "Wstęp", "start_word": 0, "chap": False}, {"id": "p1", "title": "Szlaban", "start_word": 60},
                   {"id": "p2", "title": "Blizna", "start_word": 250}, {"id": "p3", "title": "Dowód", "start_word": 420}]}


class LongResearchTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="fc-r2-"))
        self.addCleanup(shutil.rmtree, self.d, True)

    def film(self, ovs, specs, said=None, story=None, length=600.0, **plan):
        """a long of `length` s with no cuts (source time = film time); said = {second: word}, else one word a second"""
        said = said or {}
        ws = [{"offsets": {"from": i * 1000, "to": i * 1000 + 400}, "text": f" {said.get(i, 'słowo')}"} for i in range(int(length))]
        (self.d / "w.json").write_text(json.dumps({"transcription": ws}))
        (self.d / "specs.json").write_text(json.dumps(specs))
        (self.d / "edl_long.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": length, "zoom": 1.0}], "overlays": ovs, **plan.pop("edl", {})}))
        (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json", "gfx_specs": "specs.json", **plan}))
        if story: (self.d / "story.json").write_text(json.dumps(story))
        return film_check.Film(self.d, "long")

    def test_l2_pace_names_a_slow_block_and_an_empty_pause(self):
        f = self.film([], [], length=600)
        ok, _ = f.pace_flat()
        self.assertTrue(ok)
        ws = [i for i in range(600) if not (300 <= i < 600 and i % 2)]  # the second block at half the pace
        (self.d / "w.json").write_text(json.dumps({"transcription": [{"offsets": {"from": i * 1000, "to": i * 1000 + 400}, "text": " a"} for i in ws]}))
        f = film_check.Film(self.d, "long")
        ok, detail = f.pace_flat()
        self.assertFalse(ok); self.assertIn("block 5-10 min", detail); self.assertIn("pause 2.0 s", detail)

    def test_l3_roadmap_said_and_listed(self):
        ovs = [{"id": "map", "at": 20, "dur": 6}]
        specs = [{"id": "map", "type": "list", "text": "Plan", "items": ["Szlaban", "Blizna", "Dowód"]}]
        self.assertTrue(self.film(ovs, specs, said={15: "trzy"}, story=STORY).roadmap_in_opening()[0])
        ok, detail = self.film(ovs, specs, said={15: "dwa"}, story=STORY).roadmap_in_opening()
        self.assertFalse(ok); self.assertIn("number 3 is not said", detail)

    def test_l4_first_part_start(self):
        self.assertEqual(self.film([], [], story=STORY).first_part_at(), 60.0)

    def test_l5_platform_end(self):
        self.assertFalse(self.film([], [], end="platform").end_ok()[0])
        f = self.film([], [], said={590: "następny", 591: "film"}, end="platform", next_video="Szlaban dla agenta")
        self.assertTrue(f.end_ok()[0], f.end_ok())
        f = self.film([{"id": "e", "at": 592, "dur": 8}], [{"id": "e", "type": "end"}], said={590: "następny", 591: "film"},
                      end="platform", next_video="x")
        ok, detail = f.end_ok()
        self.assertFalse(ok); self.assertIn("full cards in the last 20 s: e", detail)
        self.assertTrue(self.film([{"id": "e", "at": 592, "dur": 8}], [{"id": "e", "type": "end"}]).end_ok()[0])  # default: end card

    def test_l6_one_mid_cta_with_a_url_before_the_next_chapter(self):
        cta = {"id": "o", "type": "cta", "text": "Szablon", "sub": "kamiljan.com/szablon"}
        self.assertTrue(self.film([{"id": "o", "at": 200, "dur": 20}], [cta]).mid_cta()[0])
        ok, detail = self.film([{"id": "o", "at": 200, "dur": 50}, {"id": "o2", "at": 300, "dur": 10}, {"id": "c", "at": 222, "dur": 3}],
                               [cta, {**cta, "id": "o2", "sub": "bez linku"}, {"id": "c", "type": "chap"}]).mid_cta()
        self.assertFalse(ok)
        for want in ("2 offer CTAs", "o 50 s > 45", "o2 has no URL"):
            self.assertIn(want, detail)
        ok, detail = self.film([], [], story={**STORY, "cta_after_part": 0}).mid_cta()
        self.assertFalse(ok); self.assertIn("cta_after_part 0: no CTA", detail)

    def test_l7_recap(self):
        self.assertFalse(self.film([], []).recap()[0])
        self.assertTrue(self.film([{"id": "r", "at": 560, "dur": 8}], [{"id": "r", "type": "list", "recap": True, "items": []}]).recap()[0])
        self.assertFalse(self.film([{"id": "r", "at": 560, "dur": 14}], [{"id": "r", "type": "list", "recap": True}]).recap()[0])
        self.assertTrue(self.film([], [], story={"parts": [*STORY["parts"], {"id": "r", "kind": "recap", "start_word": 540}]}).recap()[0])

    def test_l15_proof_early(self):
        self.assertTrue(self.film([{"id": "w", "at": 9, "dur": 6}], [{"id": "w", "type": "web"}]).proof_early()[0])
        self.assertFalse(self.film([{"id": "w", "at": 40, "dur": 6}], [{"id": "w", "type": "web"}]).proof_early()[0])

    def test_l16a_long_web_cards_are_marked(self):
        ok, detail = self.film([{"id": "w", "at": 9, "dur": 8}, {"id": "v", "at": 30, "dur": 8}],
                               [{"id": "w", "type": "web", "find": "92%"}, {"id": "v", "type": "web"}]).web_marked()
        self.assertFalse(ok); self.assertIn("v", detail); self.assertNotIn("w,", detail)

    def test_l18_end_bookend(self):
        specs = [{"id": "a", "type": "web", "src": "shot.png"}, {"id": "z", "type": "web", "src": "shot.png"}]
        self.assertTrue(self.film([{"id": "a", "at": 5, "dur": 5}, {"id": "z", "at": 580, "dur": 5}], specs).end_bookend()[0])
        self.assertFalse(self.film([{"id": "a", "at": 5, "dur": 5}], specs).end_bookend()[0])
        specs2 = [{"id": "a", "type": "kw"}, {"id": "z", "type": "kw", "bookend": "a"}]
        self.assertTrue(self.film([{"id": "a", "at": 5, "dur": 5}, {"id": "z", "at": 580, "dur": 5}], specs2).end_bookend()[0])

    def test_l23_action_word_gets_a_card(self):
        story = {"parts": [{"id": "p1", "start_word": 0, "action_word": 100}]}
        self.assertFalse(self.film([], [], story=story).action_words_shown()[0])
        self.assertTrue(self.film([{"id": "k", "at": 101, "dur": 3}], [{"id": "k", "type": "kw", "title": "/review"}], story=story).action_words_shown()[0])

    def test_l24_opening_pace_is_info(self):
        ok, detail = self.film([], []).opening_pace()
        self.assertTrue(ok); self.assertIn("30 words in the first 30 s", detail)


if __name__ == "__main__":
    unittest.main()


class OutResearchTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="fc-r2o-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        (self.d / "out" / "youtube").mkdir(parents=True)

    def out(self, md, said=None, ovs=(), specs=(), **plan):
        said = said or {}
        ws = [{"offsets": {"from": i * 1000, "to": i * 1000 + 400}, "text": f" {said.get(i, 'słowo')}"} for i in range(300)]
        (self.d / "w.json").write_text(json.dumps({"transcription": ws}))
        (self.d / "specs.json").write_text(json.dumps(list(specs)))
        (self.d / "edl_long.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": 300.0}], "overlays": list(ovs)}))
        (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json", "gfx_specs": "specs.json", **plan}))
        (self.d / "out" / "youtube" / "long.md").write_text(md)
        return film_check.Out(self.d, self.d / "out")

    def test_l1_chapters_are_the_chap_cards(self):
        ovs, specs = [{"id": "c1", "at": 60, "dur": 3}], [{"id": "c1", "type": "chap", "text": "Szlaban zamiast tabliczki"}]
        ok = self.out("## Opis\nRozdziały:\n0:00 Wstęp\n1:01 Szlaban zamiast tabliczki\n", ovs=ovs, specs=specs).chapters_match()
        self.assertTrue(ok[0], ok)
        o = self.out("## Opis\nRozdziały:\n0:00 Wstęp\n1:30 Subskrybuj kanał teraz\n", ovs=ovs, specs=specs)
        ok, detail = o.chapters_match()
        self.assertFalse(ok); self.assertIn("at 90 s, its card at 60 s", detail); self.assertIn("is not the card text", detail)
        self.assertIn("call to action", o.warns[0][1])

    def test_l19_said_in_the_description_needs_resources(self):
        said = {100: "link", 101: "w", 102: "opisie"}
        self.assertTrue(self.out("## Opis\nx\n").resources_given()[0])
        self.assertFalse(self.out("## Opis\nx\n", said=said).resources_given()[0])
        self.assertTrue(self.out("## Zasoby\nhttps://github.com/x/y\n", said=said).resources_given()[0])

    def test_l20_verified_claims_have_sources(self):
        ovs, specs = [{"id": "s92", "at": 10, "dur": 4}], [{"id": "s92", "type": "kw", "title": "92%"}]
        o = self.out("## Źródła\n- https://example.org/raport\n", ovs=ovs, specs=specs, verified_claims=["s92"])
        self.assertFalse(o.sources_listed()[0])
        o = self.out("## Źródła\n- 92%: https://example.org/raport\n", ovs=ovs, specs=specs, verified_claims=["s92"],
                     sources={"s92": "https://example.org/raport"})
        self.assertTrue(o.sources_listed()[0])
