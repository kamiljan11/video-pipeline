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
        self.assertFalse(ok); self.assertIn("block 5-10 min", detail); self.assertIn("pause 1.6 s", detail)  # 0.4 s words: end to start

    def test_l2_a_long_word_is_not_a_pause(self):  # "halucynowania" (1.4 s) + 0.4 s air: start to start 1.8 s, the pause 0.4 s
        ws = [{"offsets": {"from": int(t * 1000), "to": int(e * 1000)}, "text": w} for t, e, w in
              [(0.0, 0.3, " a"), (0.5, 1.9, " halucynowania"), (2.3, 2.6, " b"), (5.0, 5.3, " c")]]
        ws += [{"offsets": {"from": 5500 + 500 * k, "to": 5800 + 500 * k}, "text": " x"} for k in range(25)]  # >= 20 words
        f = self.film([], [], length=20)
        (self.d / "w.json").write_text(json.dumps({"transcription": ws}))
        f = film_check.Film(self.d, "long")
        bad = [b for b in f.pace_flat(block_s=600)[1].split("; ") if b.startswith("pause")]
        self.assertEqual(bad, ["pause 2.4 s at 3 s with nothing on screen"])

    def test_l3_roadmap_said_and_listed(self):
        ovs = [{"id": "map", "at": 20, "dur": 6}]
        specs = [{"id": "map", "type": "list", "text": "Plan", "items": ["Szlaban", "Blizna", "Dowód"]}]
        self.assertTrue(self.film(ovs, specs, said={15: "trzy"}, story=STORY).roadmap_in_opening()[0])
        ok, detail = self.film(ovs, specs, said={15: "dwa"}, story=STORY).roadmap_in_opening()
        self.assertFalse(ok); self.assertIn("number 3 is not said", detail)

    def test_a_retake_the_cut_kept_fails_and_a_named_repeat_passes(self):  # Kamil 2026-11-09: cut the worse take
        fill = {i: f"w{i}" for i in range(40)}  # every other second a different word (the default "słowo" repeats)
        take = ["to", "jest", "bardzo", "ważne", "zdanie"]
        said = {**fill, **dict(enumerate([*take, "no", *take]))}
        ok, detail = self.film([], [], said=said, length=40).retakes_left()
        self.assertFalse(ok); self.assertIn("'to jest bardzo ważne zdanie' at 0 s and 6 s", detail)  # the whole repeated run
        self.assertEqual(detail.count(" at "), 1)  # one retake = one line, not one per overlapping run
        far = {**fill, **dict(enumerate(take)), **{30 + i: w for i, w in enumerate(take)}}
        self.assertTrue(self.film([], [], said=far, length=40).retakes_left()[0])  # 30 s apart: a callback, not a retake
        named = self.film([], [], said=said, length=40, retakes_ok={"to jest bardzo ważne": "said twice on purpose for emphasis"})
        self.assertTrue(named.retakes_left()[0])
        ok, detail = self.film([], [], said=said, length=40, retakes_ok={"to jest bardzo ważne": "ok"}).retakes_left()
        self.assertFalse(ok); self.assertIn("the reason must say why", detail)
        for key in ("", "to", "jest bardzo"):  # review 2026-11-09: an empty or short key waived every run (substring match)
            ok, detail = self.film([], [], said=said, length=40, retakes_ok={key: "said twice on purpose for emphasis"}).retakes_left()
            self.assertFalse(ok, key); self.assertIn("name the 4+ words said twice", detail)
        kto = {**fill, **dict(enumerate(["kto", "jest", "bardzo", "ważne", "x", "kto", "jest", "bardzo", "ważne"]))}
        self.assertFalse(self.film([], [], said=kto, length=40, retakes_ok={"to jest bardzo ważne": "said twice on purpose for emphasis"}).retakes_left()[0])

    def test_l3_the_announced_parts_are_the_road_when_marked(self):  # Kamil 2026-11-09: "trzy pomysły" in 13 chapters, no skip
        parts = [{"id": "intro", "title": "Wstęp", "start_word": 0, "chap": False}, {"id": "pr", "title": "Problem", "start_word": 30}] + \
                [{"id": f"p{i}", "title": t, "start_word": 60 + 60 * i, "roadmap": True} for i, t in enumerate(("Szlaban", "Blizna", "Dowód"))] + \
                [{"id": "x", "title": "Narzędzia", "start_word": 300}]
        ovs = [{"id": "map", "at": 20, "dur": 6}]
        specs = [{"id": "map", "type": "list", "text": "Trzy pomysły", "items": ["Szlaban", "Blizna", "Dowód"]}]
        self.assertTrue(self.film(ovs, specs, said={15: "trzy"}, story={"parts": parts}).roadmap_in_opening()[0])
        ok, detail = self.film(ovs, specs, said={15: "pięć"}, story={"parts": [{**p, "roadmap": False} for p in parts]}).roadmap_in_opening()
        self.assertFalse(ok); self.assertIn("no list card with 5 items", detail)  # unmarked: all 5 content parts count
        ok, detail = self.film(ovs, specs, said={15: "trzy"}, story={"parts": [{**parts[0], "roadmap": True}] + parts[1:]}).roadmap_in_opening()
        self.assertFalse(ok); self.assertIn("on a part without a chapter: Wstęp", detail)

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


WORDS = ["92%", "zmian", "idzie", "bez", "przeglądu.", *["słowo"] * 30, "Dlatego", "te", "92%", "bolą."]


class ShortResearchTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="fc-r2s-"))
        self.addCleanup(shutil.rmtree, self.d, True)

    def short(self, sentence_words, ovs=(), specs=(), tail=0.0, **plan):
        """a 40 s short, one word a second: sentence_words = the words in order (with their . ? !)"""
        ws = [{"offsets": {"from": i * 1000, "to": i * 1000 + 400}, "text": f" {w}"} for i, w in enumerate(sentence_words)]
        n = len(sentence_words)
        (self.d / "w.json").write_text(json.dumps({"transcription": ws}))
        (self.d / "specs.json").write_text(json.dumps(list(specs)))
        (self.d / "edl_s1.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": float(n)}], "overlays": list(ovs), "tail": tail}))
        (self.d / "plan_s1.json").write_text(json.dumps({"words": "w.json", "gfx_specs": "specs.json", "vertical": True, **plan}))
        return film_check.Film(self.d, "s1")

    def test_s4_hook_that_repeats_the_first_sentence(self):
        ok, detail = self.short(WORDS, hook_text="92% zmian bez przeglądu").hook_echo()
        self.assertFalse(ok); self.assertIn("first sentence", detail)
        self.assertTrue(self.short(WORDS, hook_text="Kto to sprawdza?").hook_echo()[0])

    def test_s5_end_hold_only_on_a_scene_or_maxim(self):
        n = len(WORDS)
        ok, _ = self.short(WORDS, [{"id": "m", "at": n - 3, "dur": 4.2}], [{"id": "m", "type": "maxim"}], tail=1.2, end_hold=1.2).ends_on_the_last_word(0.6)
        self.assertTrue(ok)
        ok, detail = self.short(WORDS, [{"id": "c", "at": n - 3, "dur": 4.2}], [{"id": "c", "type": "cta"}], tail=1.2, end_hold=1.2).ends_on_the_last_word(0.6)
        self.assertFalse(ok); self.assertIn("want scene/maxim", detail)
        self.assertFalse(self.short(WORDS, tail=1.2).ends_on_the_last_word(0.6)[0])  # no end_hold: the old 0.6 s rule

    def test_s6_the_end_comes_back_to_the_hook(self):
        self.assertTrue(self.short(WORDS).callback_end()[0])
        self.assertFalse(self.short([*WORDS[:-4], "Tak", "to", "wygląda", "zawsze."]).callback_end()[0])

    def test_s7_changes_per_minute(self):
        ovs = [{"id": f"k{i}", "at": i * 5, "dur": 2} for i in range(8)]
        v, _ = self.short(WORDS, ovs, [{"id": f"k{i}", "type": "kw"} for i in range(8)]).changes_per_min()
        self.assertAlmostEqual(v, round(8 / (len(WORDS) / 60), 1))
        v, detail = self.short(WORDS, [{"id": "s", "at": 0, "dur": 30}], [{"id": "s", "type": "scene"}]).changes_per_min()
        self.assertEqual(v, 99.0); self.assertIn("not counted", detail)

    def test_s15_last_sentence_on_the_face(self):
        n = len(WORDS)
        self.assertTrue(self.short(WORDS).last_line_on_face()[0])
        ok, detail = self.short(WORDS, [{"id": "w", "at": n - 3, "dur": 3}], [{"id": "w", "type": "web"}]).last_line_on_face()
        self.assertFalse(ok); self.assertIn("w", detail)


class ShortTitlesTest(unittest.TestCase):  # plan 1 5.3
    def test_each_short_needs_ab_titles(self):
        d = Path(tempfile.mkdtemp(prefix="fc-st-")); self.addCleanup(shutil.rmtree, d, True)
        (d / "clips.json").write_text(json.dumps({"items": [{"id": "s1", "make": True}, {"id": "s2", "make": True}]}))
        sh = d / "out" / "youtube" / "shorts"; sh.mkdir(parents=True)
        (sh / "s1.md").write_text("## Tytuły\n| A | Kto sprawdza kod z AI? |\n| B | Claude Code + recenzent = 0 wpadek |\n")
        (sh / "s2.md").write_text("## Tytuły\n| A | Jeden tytuł |\n")
        o = film_check.Out(d, d / "out")
        ok, detail = o.short_titles()
        self.assertFalse(ok); self.assertIn("s2: 1 title variants", detail); self.assertNotIn("s1", detail)


class ThumbsResearchTest(unittest.TestCase):  # TH4 / TH6 / TH8 used in thumbs.json
    def test_variants_use_place_lift_and_object(self):
        d = Path(tempfile.mkdtemp(prefix="fc-th-")); self.addCleanup(shutil.rmtree, d, True)
        (d / "thumbs.json").write_text(json.dumps({"long": [{"id": "A", "frame": "a.png"}, {"id": "C", "no_face": True, "frame": "c.png"}]}))
        ok, detail = film_check.Out(d, d / "out").thumbs_research()
        self.assertFalse(ok)
        for want in ("long_A: not placed", "long_A: tone is not", "no variant with layout"):
            self.assertIn(want, detail)
        (d / "thumbs.json").write_text(json.dumps({"long": [{"id": "A", "frame": "a.png", "placed": {"cx": 0.72}, "tone": "lift"},
                                                            {"id": "C", "layout": "object", "object": [{"icon": "shield"}]}]}))
        self.assertTrue(film_check.Out(d, d / "out").thumbs_research()[0])


class AgentFieldsTest(unittest.TestCase):  # the EDL fields of the round 2 options (zooms, moves, framing, options_used)
    def test_canvas_zooms_are_punches_and_moves_fill_the_gap(self):
        edl = {"segments": [{"in": 0.0, "out": 60.0}], "overlays": [{"id": "s", "at": 0, "dur": 1, "zooms": [12.0]},
                                                                    {"id": "t", "at": 1, "dur": 1, "moves": [20.0, 40.0]}]}
        self.assertEqual(film_check.punches(edl), [12.0])
        self.assertEqual(film_check.max_gap(edl, 60.0), 20.0)
        self.assertEqual(film_check.max_gap({**edl, "overlays": edl["overlays"][:1]}, 60.0), 48.0)

    def test_framing_read_along_and_short_options(self):
        d = Path(tempfile.mkdtemp(prefix="fc-af-")); self.addCleanup(shutil.rmtree, d, True)
        (d / "w.json").write_text(json.dumps({"transcription": []}))
        (d / "specs.json").write_text(json.dumps([{"id": "c", "type": "scene", "els": [{"k": "term", "cmd": "ls"}]}]))
        def film(edl, **plan):
            (d / "edl_x.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": 100.0}], **edl}))
            (d / "plan_x.json").write_text(json.dumps({"words": "w.json", "gfx_specs": "specs.json", **plan}))
            return film_check.Film(d, "x")
        self.assertFalse(film({"overlays": []}).framing_changes()[0])
        self.assertTrue(film({"overlays": [], "options_used": {"zoom_every_s": 30}, "framing": {"changes": 4, "max_still": 30}}).framing_changes()[0])
        self.assertTrue(film({"overlays": [{"id": "c", "at": 1, "dur": 8}]}).read_along_used()[0])  # nothing of it is said
        (d / "specs.json").write_text(json.dumps([{"id": "c", "type": "scene", "els": [{"k": "win", "rows": ["~60", "Każdy raport kończ słowem"]}]}]))
        (d / "w.json").write_text(json.dumps({"transcription": [{"text": w, "offsets": {"from": 2000 + 300 * k, "to": 2200 + 300 * k}}
                                                               for k, w in enumerate(["każdy", "raport", "ma", "się"])]}))
        ok, detail = film({"overlays": [{"id": "c", "at": 1, "dur": 8}]}).read_along_used()
        self.assertFalse(ok); self.assertIn("Każdy raport", detail)
        self.assertTrue(film({"overlays": [{"id": "c", "at": 1, "dur": 8, "read_along": [3.0]}]}).read_along_used()[0])
        self.assertTrue(film({"overlays": [{"id": "c", "at": 20, "dur": 8}]}).read_along_used()[0])  # said before the card
        ok, detail = film({"overlays": []}, vertical=True, hook_show_report={"missing": ["Supabase"]}).short_options()
        self.assertFalse(ok)
        for want in ("hook_pos", "caption_emph", "Supabase"):
            self.assertIn(want, detail)
        self.assertTrue(film({"overlays": [], "options_used": {"hook_pos": "mid", "caption_emph": "key"}}, vertical=True).short_options()[0])


class FilmFixture(unittest.TestCase):  # a film from overlays, specs and (time, word) pairs; no tests of its own
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="fc-cu-")); self.addCleanup(shutil.rmtree, self.d, True)

    def film(self, ovs, specs, words=()):
        tr = [{"text": w, "offsets": {"from": int(t * 1000), "to": int(t * 1000) + 200}} for t, w in words]
        (self.d / "w.json").write_text(json.dumps({"transcription": tr}))
        (self.d / "specs.json").write_text(json.dumps(specs))
        (self.d / "edl_x.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": 300.0}], "overlays": ovs}))
        (self.d / "plan_x.json").write_text(json.dumps({"words": "w.json", "gfx_specs": "specs.json"}))
        return film_check.Film(self.d, "x")


class CardUseTest(FilmFixture):  # round 2 L8 L9 L12 L17 L21 S11 S14: the new cards are measured in the film, not only drawn
    def test_lists_on_their_words_and_stacked(self):
        sp = [{"id": "a", "type": "list", "items": ["x", "y", "z"]}, {"id": "b", "type": "list", "items": ["q"]}]
        ok, detail = self.film([{"id": "a", "at": 10, "dur": 8}, {"id": "b", "at": 50, "dur": 4}], sp).list_said()
        self.assertFalse(ok)
        self.assertIn("not timed", detail); self.assertIn("one stacked list", detail)
        self.assertTrue(self.film([{"id": "a", "at": 10, "dur": 8, "items_said": [10, 12, 14], "variant": "upto"}, {"id": "b", "at": 50, "dur": 4}], sp).list_said()[0])

    def test_chap_cards_drawn_as_the_map(self):
        sp = [{"id": "c1", "type": "chap", "text": "a"}, {"id": "c2", "type": "chap", "text": "b"}]
        self.assertFalse(self.film([{"id": "c1", "at": 5, "dur": 3, "variant": "roadmap"}, {"id": "c2", "at": 90, "dur": 3}], sp).chap_roadmap()[0])
        self.assertTrue(self.film([{"id": "c1", "at": 5, "dur": 3, "variant": "roadmap"}, {"id": "c2", "at": 90, "dur": 3, "variant": "part_tag"}], sp).chap_roadmap()[0])
        self.assertFalse(self.film([], []).chap_roadmap()[0])

    def test_define_and_note_follow_what_is_said(self):
        words = [(20.0, "czyli"), (100.0, "opisie.")]
        sp = [{"id": "d", "type": "lower", "define": True, "text": "RLS", "sub": "kto widzi wiersz"}, {"id": "n", "type": "note", "text": "link w opisie"}]
        f = self.film([], sp, words)
        self.assertFalse(f.define_used()[0]); self.assertFalse(f.note_used()[0])
        f = self.film([{"id": "d", "at": 21, "dur": 6, "variant": "define"}, {"id": "n", "at": 104, "dur": 4, "variant": "note"}], sp, words)
        self.assertTrue(f.define_used()[0]); self.assertTrue(f.note_used()[0])
        self.assertTrue(self.film([], sp).define_used()[0])  # no cue word: no define card needed

    def test_scene_zoom_items_and_panel_moves(self):
        sp = [{"id": "s", "type": "scene", "els": []}, {"id": "w", "type": "web"}]
        f = self.film([{"id": "s", "at": 0, "dur": 8}, {"id": "w", "at": 20, "dur": 9, "moves": [23.0]}], sp)
        self.assertFalse(f.scene_zoom()[0]); self.assertFalse(f.panel_moves()[0])
        f = self.film([{"id": "s", "at": 0, "dur": 8, "zooms": [3.0], "moves": [2.5, 5.0]}, {"id": "w", "at": 20, "dur": 9, "moves": [22.5, 25.0, 27.0]}], sp)
        self.assertTrue(f.scene_zoom()[0]); self.assertTrue(f.panel_moves()[0])
        self.assertFalse(self.film([{"id": "s", "at": 0, "dur": 8, "items": [[1, 3], [3, 8]]}], sp).list_items()[0])
        self.assertTrue(self.film([{"id": "s", "at": 0, "dur": 8, "items": [[1, 4.5], [4.5, 8]]}], sp).list_items()[0])


class WpmTest(FilmFixture):  # round 2 P0.6: wpm reported, no threshold
    def test_words_per_min_is_info(self):
        f = self.film([], [], [(i * 0.4, "słowo") for i in range(150)])
        ok, detail = f.words_per_min()
        self.assertTrue(ok); self.assertIn("wpm of the speech", detail)
        self.assertFalse(self.film([], []).words_per_min()[0])


class ActionWordTest(FilmFixture):  # round 2 L23: the prompt shown where it is said (a kw/slide card, or a scene's window)
    def test_a_scene_window_shows_the_prompt(self):
        story = {"parts": [{"id": "p0", "title": "a", "start_word": 0}, {"id": "p1", "title": "b", "start_word": 1, "action_word": 1}]}
        (self.d / "story.json").write_text(json.dumps(story))
        sp = [{"id": "s", "type": "scene", "els": [{"k": "win", "at": 1.0, "rows": ["Każdy raport kończ słowem"]}]}]
        words = [(0.0, "To"), (20.0, "dopisz")]
        self.assertFalse(self.film([{"id": "s", "at": 30, "dur": 8}], sp, words).action_words_shown()[0])
        self.assertTrue(self.film([{"id": "s", "at": 19.5, "dur": 8}], sp, words).action_words_shown()[0])


class MemeReviewTest(FilmFixture):  # Kamil note 19: a meme fits its sentence and is current
    def reviewed(self, review, sp=None, words=((10.0, "ręczny"), (10.4, "montaż"), (10.8, "odpada"))):
        self.film([{"id": "m", "at": 11, "dur": 3}], sp or [{"id": "m", "type": "sticker", "meme": "drake"}], words)
        (self.d / "plan_x.json").write_text(json.dumps({"words": "w.json", "gfx_specs": "specs.json", "meme_review": review}))
        return film_check.Film(self.d, "x").meme_review(max_age=8)

    def test_a_reviewed_current_meme_said_on_time_passes(self):
        now = film_check.datetime.datetime.now(film_check.datetime.UTC).year
        good = {"m": {"sentence": "ręczny montaż odpada", "why": "odrzucenie starego sposobu, Drake odpycha", "year": now - 3, "source": "https://knowyourmeme.com/x"}}
        self.assertTrue(self.reviewed(good)[0])
        self.assertTrue(self.film([], []).meme_review()[0])  # no meme on screen: nothing to review

    def test_missing_entry_old_meme_unsaid_sentence_each_named(self):
        self.assertIn("no plan meme_review entry", self.reviewed({})[1])
        ok, d = self.reviewed({"m": {"sentence": "zupełnie inne zdanie tutaj", "why": "krótko", "year": 2009, "source": ""}})
        self.assertFalse(ok)
        for part in ("not said while the card is up", '"why" = why', "more than 8 years old", '"source" = a URL'):
            self.assertIn(part, d)

    def test_a_plan_value_that_is_not_a_table_and_words_out_of_order_are_named(self):
        self.assertIn('plan "meme_review" = ', self.reviewed([{"m": {}}])[1])
        now = film_check.datetime.datetime.now(film_check.datetime.UTC).year
        jumbled = {"m": {"sentence": "odpada montaż ręczny", "why": "odrzucenie starego sposobu pracy", "year": now - 1, "source": "httpx"}}
        ok, d = self.reviewed(jumbled)
        self.assertFalse(ok)
        self.assertIn("1/3 words in order", d); self.assertIn('"source" = a URL', d)

    def test_a_toon_still_needs_its_sentence(self):
        ok, d = self.reviewed({"m": {"why": "kot przy klawiaturze = robota sama"}}, sp=[{"id": "m", "type": "sticker", "toon": "cat_typing"}])
        self.assertFalse(ok); self.assertIn('"sentence" = the line', d)

    def test_our_own_toon_needs_no_year_or_source(self):
        ok, d = self.reviewed({"m": {"sentence": "ręczny montaż odpada", "why": "kot przy klawiaturze = robota sama"}},
                              sp=[{"id": "m", "type": "sticker", "toon": "cat_typing"}])
        self.assertTrue(ok, d)
