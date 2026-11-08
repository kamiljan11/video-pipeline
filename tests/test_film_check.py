"""film_check.py: the checklist gate (style/checklist.json) before the render and on the out folder after it.

  python3 -m unittest tests.test_film_check
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_article  # an article folder that passes article_check
import test_ig_check  # an Instagram carousel that passes ig_check

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
FACE_MODEL = ROOT / "models" / "face_detection_yunet_2023mar.onnx"
BRAND = json.loads((ROOT / "style" / "brand.json").read_text())["lower_sub"]


def words(n: int, step: float = 1.0) -> dict:
    return {"transcription": [{"offsets": {"from": round(i * step * 1000), "to": round((i * step + 0.5) * 1000)}, "text": f" w{i}"}
                              for i in range(n)]}



LONG_MD = """## Tytuły

| wariant | kąt | tytuł | źródło |
|---|---|---|---|
| A | wynik | Kod z AI, który sam się sprawdza | kanał X: Kod z AI bez błędów |
| B | ciekawość | AI agent mówi gotowe | kanał Y: Agent mówi done |
| C | problem | Agent AI kłamie, że kod działa | kanał X: Agent AI kłamie |

## Fraza kluczowa

kod z AI, agent AI

## Opis
Kod z AI, który sam się sprawdza.
Artykuł: https://kamiljan.com/blog/x?utm_source=youtube&utm_medium=long&utm_campaign=t

Rozdziały:
0:00 a
1:00 b
2:00 c

Strona: https://KamilJan.com
## Tagi
x
"""


HOOKS = ["AI mówi „gotowe”. A nic nie działa.", "92% zmian bez przeglądu. A dziś?", "Na katar nikt nie robi rezonansu"]


def thumb(f: Path, text: str) -> None:
    """a long thumbnail with one big readable word and no face (thumb_check reads it at 320 px)"""
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
    f.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0A1430:s=1280x720", "-frames:v", "1",
                    "-vf", f"drawtext=fontfile={font}:text='{text}':fontsize=200:fontcolor=0xECF0F6:x=80:y=200", str(f)], check=True)


def opening(d: Path) -> None:
    """the long's words (with "siedemnaście" for the article's numbers) and an EDL: what the titles promise is said in the first 30 s"""
    said = ["siedemnaście", "agent", "AI", "mówi", "gotowe", "kod", "działa", "sprawdza"]
    (d / "w.json").write_text(json.dumps({"transcription": [{"offsets": {"from": i * 1000, "to": i * 1000 + 500}, "text": f" {w}"}
                                                            for i, w in enumerate(said)]}))
    (d / "edl_long.json").write_text(json.dumps({"segments": [{"src": "A", "in": 0.0, "out": 20.0, "zoom": 1.0}]}))


POST_LINES = ["Każdy błąd zostawia bliznę", "Nowe sprawdzenie w systemie", "Ten sam błąd nie przejdzie drugi raz",
              "Jak nowy punkt w procedurze pilota"]


def post_graphic(d: Path) -> None:
    """a readable post graphic and its words (what gfx/post_gfx.mjs writes), for post_check.py"""
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
    draw = ",".join(f"drawtext=fontfile={font}:text='{ln}':fontsize=56:fontcolor=0xECF0F6:x=80:y={120 + 140 * k}" for k, ln in enumerate(POST_LINES))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0A1430:s=1080x1350", "-frames:v", "1", "-vf", draw,
                    str(d / "grafika.png")], check=True)
    (d / "grafika.txt").write_text(" ".join(POST_LINES) + "\n")


class FilmCheckTest(unittest.TestCase):
    """a 10-minute long with three parts (words 0, 200, 400 = 0 s, 200 s, 400 s; no cuts, so source time = film time)"""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="fcheck-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        (self.d / "w.json").write_text(json.dumps(words(600)))
        (self.d / "story.json").write_text(json.dumps({"parts": [
            {"id": "p1", "title": "Wstęp", "start_word": 0}, {"id": "p2", "title": "Szlaban", "start_word": 200},
            {"id": "p3", "title": "Blizna", "start_word": 400}]}))
        self.ledger = self.d / "ledger.json"

    def project(self, overlays, specs, segments=None, **plan):
        segs = segments or [{"src": "A", "in": 0.0, "out": 600.0, "zoom": 1.0}]
        (self.d / "edl_long.json").write_text(json.dumps({"segments": segs, "overlays": overlays, "gfx_lead": -0.12}))  # build_edl copies plan gfx_lead
        (self.d / "specs.json").write_text(json.dumps(specs))
        (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json", "edl_out": "edl_long.json", "gfx_specs": "specs.json", **plan}))
        self.accept_stills([o["id"] for o in overlays])
        self.review_meaning(specs)

    def review_meaning(self, specs):  # every card read for meaning (content_review.py, film_check long/short.meaning)
        import film_check
        (self.d / "content_review_long.json").write_text(json.dumps(
            {s["id"]: {"verdict": "ok", "why": "adds the step the viewer needs", "hash": film_check.card_text_hash(s)} for s in specs}))

    def accept_stills(self, ids):  # Kamil accepted a still of every card (stills.py accept, film_check long/short.stills)
        sd = self.d / "gfx" / "stills"; sd.mkdir(parents=True, exist_ok=True)
        (sd / "accepted.json").write_text(json.dumps({i: "key" for i in ids}))

    def run_check(self, *args):
        env_code = (f"import sys, film_check; film_check.LEDGER = __import__('pathlib').Path({str(self.ledger)!r}); "
                    f"sys.exit(film_check.main(sys.argv[1:]))")
        r = subprocess.run([sys.executable, "-c", env_code, str(self.d), *args, "--json"], cwd=ROOT, capture_output=True, text=True, check=False)
        rep = json.loads(r.stdout) if r.stdout.strip().startswith("[") else []
        return r, {x["id"]: x for x in rep}

    def full_long(self):
        """a long that meets every item: chapters at each part start, an explainer in each part, dense cards and punches"""
        ovs, specs = [], []
        for k, at in enumerate((0.5, 200.5, 400.5)):
            ovs.append({"id": f"c{k}", "at": at, "dur": 3}); specs.append({"id": f"c{k}", "type": "chap"})
        for k in range(6):  # an animated explanation every 100 s
            ovs.append({"id": f"s{k}", "at": 10 + 100 * k, "dur": 12}); specs.append({"id": f"s{k}", "type": "scene"})
        for k, at in enumerate(range(20, 600, 6)):  # cards beside him cover most of the film: face_full <= 0.35
            ovs.append({"id": f"k{k}", "at": at, "dur": 4}); specs.append({"id": f"k{k}", "type": "kw", "title": f"{k + 2} kroki"})
        for k, at in enumerate((2, 5)):
            ovs.append({"id": f"b{k}", "at": at, "dur": 2.5}); specs.append({"id": f"b{k}", "type": "float", "behind": {"edl": "edl_long.json"}})
        for k, at in enumerate((150, 350, 550)):
            ovs.append({"id": f"m{k}", "at": at, "dur": 3}); specs.append({"id": f"m{k}", "type": "sticker", "meme": "drake"})  # beside him, not a screen
        ovs.append({"id": "low", "at": 6, "dur": 4}); specs.append({"id": "low", "type": "lower", "text": "Kamil Jan", "sub": BRAND})
        ovs.append({"id": "end", "at": 590, "dur": 8}); specs.append({"id": "end", "type": "end"})
        segs = [{"src": "A", "in": i * 3.0, "out": i * 3.0 + 3.0, "zoom": {"a": 1.0, "b": 1.2, "t0": 0.5, "t1": 0.8}} for i in range(200)]
        return ovs, specs, segs

    def test_film_two_gaps_are_named(self):
        """the plan of film 2026-11-04: no story, chapters at the end of thoughts, no scenes, no text behind, old bed"""
        ovs = [{"id": "c1", "at": 275, "dur": 3}, {"id": "k1", "at": 100, "dur": 5}]
        specs = [{"id": "c1", "type": "chap"}, {"id": "k1", "type": "kw"},
                 {"id": "low", "type": "lower", "sub": "Automatyzacje i wdrożenia AI · KamilJan.com"}]
        self.project(ovs, specs, sfx_style="v2")
        r, rep = self.run_check("long")
        self.assertEqual(r.returncode, 1, r.stderr)
        for item in ("long.chapters", "long.explainers", "long.behind", "long.punch", "long.music_palette", "long.lower", "long.max_gap"):
            self.assertEqual(rep[item]["status"], "FAIL", item)
        self.assertIn("Szlaban", rep["long.chapters"]["detail"])  # the part whose chapter card is missing at its start

    def test_complete_long_passes(self):
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segs, sfx_style="v2", music_palette={"name": "lofi", "key": 2},
                     music_moods=[[0, "story"], [200, "tension"], [400, "upbeat"]])
        r, rep = self.run_check("long")
        self.assertEqual(r.returncode, 0, json.dumps({k: v for k, v in rep.items() if v["status"] != "OK"}, ensure_ascii=False))

    def test_a_one_word_card_that_says_nothing_fails(self):  # Kamil 2026-11-08 on "Najwięcej"
        import film_check
        ovs, specs, segs = self.full_long()
        ovs.append({"id": "nw", "at": 23, "dur": 3}); specs.append({"id": "nw", "type": "kw", "title": "Najwięcej", "icon": "sparkles"})
        self.project(ovs, specs, segs)
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.filler"]["status"], "FAIL")
        self.assertIn('nw "Najwięcej"', rep["long.filler"]["detail"])
        for title, sub in (("GitHub", ""), ("kamiljan.com", ""), ("92%", ""), ("Najwięcej", "z jednego promptu"), ("Dwa słowa", "")):
            self.assertFalse(film_check.says_nothing(title, sub), title)
        self.assertTrue(film_check.says_nothing("", ""))

    def test_every_card_is_read_for_meaning_before_the_render(self):
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segs)
        f = self.d / "content_review_long.json"
        rev = json.loads(f.read_text())
        rev.pop("k0"); rev["k1"]["hash"] = "old"; rev["k2"]["verdict"] = "cut"; rev["k3"]["why"] = "ok"
        f.write_text(json.dumps(rev))
        _, rep = self.run_check("long")
        d = rep["long.meaning"]["detail"]
        self.assertEqual(rep["long.meaning"]["status"], "FAIL")
        for want in ("k0 not reviewed", "k1 changed after the review", "k2 judged 'cut'", "k3 ok without a reason"):
            self.assertIn(want, d)
        f.unlink()
        _, rep = self.run_check("long")
        self.assertIn("no content_review_long.json", rep["long.meaning"]["detail"])

    def test_content_review_lists_new_and_changed_cards_and_keeps_the_rest(self):
        import content_review
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segs)
        specs[0] = {**specs[0], "title": "Nowy tytuł"}  # c0 changed after its review
        ovs.append({"id": "nw", "at": 23, "dur": 3}); specs.append({"id": "nw", "type": "kw", "title": "Najwięcej"})
        (self.d / "specs.json").write_text(json.dumps(specs))
        edl = json.loads((self.d / "edl_long.json").read_text()); edl["overlays"] = ovs
        (self.d / "edl_long.json").write_text(json.dumps(edl))
        self.assertEqual(content_review.main([str(self.d), "long"]), 0)
        rev = json.loads((self.d / "content_review_long.json").read_text())
        self.assertEqual(rev["nw"]["verdict"], "todo")
        self.assertEqual(rev["c0"]["verdict"], "todo")
        self.assertEqual(rev["k5"]["verdict"], "ok")
        md = (self.d / "content_review_long.md").read_text()
        self.assertIn("### nw (kw, 0:23.0, 3.0 s) **FILLER?**", md)
        self.assertIn("- said: w23", md)

    def test_face_windows_must_be_cut_around_the_head(self):  # Kamil 5.11: PiP "scentruj", corner "nie ultra zoomed twarz"
        ovs, specs, segs = self.full_long()
        self.project([*ovs, {"id": "w1", "at": 300, "dur": 6, "pip": True}], specs, segs)
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.head_track"]["status"], "FAIL")
        edl = json.loads((self.d / "edl_long.json").read_text())
        (self.d / "edl_long.json").write_text(json.dumps({**edl, "head_track": True}))
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.head_track"]["status"], "OK")

    def test_the_count_he_says_must_be_the_count_on_the_card(self):  # count_check.py, long.counts
        ovs, specs, segs = self.full_long()
        ovs.append({"id": "tiles", "at": 300.5, "dur": 8}); specs.append({"id": "tiles", "type": "scene", "els": [{"k": "chip"}] * 6})
        w = words(600)
        w["transcription"][299]["text"] = " trzy"  # said at 299 s, 1.5 s before the card
        (self.d / "w.json").write_text(json.dumps(w))
        self.project(ovs, specs, segs)
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.counts"]["status"], "FAIL")
        self.assertIn("tiles: 6 on the card, says [3]", rep["long.counts"]["detail"])
        w["transcription"][299]["text"] = " sześć"
        (self.d / "w.json").write_text(json.dumps(w))
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.counts"]["status"], "OK")

    def test_graphics_must_enter_before_their_word(self):  # Skool CCC A19: entrance ~0.12 s before the word
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segs)
        edl = json.loads((self.d / "edl_long.json").read_text())
        for lead, want in ((None, "FAIL"), (0.0, "FAIL"), (-0.12, "OK"), (-1.0, "FAIL")):
            (self.d / "edl_long.json").write_text(json.dumps({**{k: v for k, v in edl.items() if k != "gfx_lead"},
                                                               **({} if lead is None else {"gfx_lead": lead})}))
            _, rep = self.run_check("long")
            self.assertEqual(rep["long.gfx_lead"]["status"], want, lead)

    def test_text_behind_the_head_must_stay_readable(self):
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segs, music_palette={"name": "lofi", "key": 0})
        _, rep = self.run_check("long")
        self.assertNotIn("long.behind_readable", rep)  # phase "behind": not in the check before the render
        (self.d / "gfx").mkdir(exist_ok=True)
        (self.d / "gfx" / "b0.cover.json").write_text(json.dumps({"covered": 0.08}))
        r, rep = self.run_check("long", "--phase", "behind")
        self.assertEqual(rep["long.behind_readable"]["status"], "FAIL")  # b1 has no measure: counted as hidden
        self.assertIn("b1 100%", rep["long.behind_readable"]["detail"])
        self.assertEqual(r.returncode, 1)
        (self.d / "gfx" / "b1.cover.json").write_text(json.dumps({"covered": 0.31}))
        _, rep = self.run_check("long", "--phase", "behind")
        self.assertEqual(rep["long.behind_readable"]["status"], "FAIL")
        self.assertIn("b1 31%", rep["long.behind_readable"]["detail"])
        (self.d / "gfx" / "b1.cover.json").write_text(json.dumps({"covered": 0.12}))
        r, rep = self.run_check("long", "--phase", "behind")
        self.assertEqual(rep["long.behind_readable"]["status"], "OK")
        self.assertEqual(list(rep), ["long.behind_readable"])  # only the items of that phase
        self.assertEqual(r.returncode, 0)
        self.assertIn("b0 8%", rep["long.behind_readable"]["detail"])
        r, _ = self.run_check("long", "--phase", "behnd")  # a typo is refused, not an empty pass
        self.assertEqual(r.returncode, 2)
        self.assertIn("known: behind", r.stderr)

    def test_a_drawing_behind_the_head_is_not_held_to_the_text_limit(self):  # Kamil 5.11: "narysuj szlaban" za mną
        ovs, specs, segs = self.full_long()
        b = next(sp for sp in specs if "behind" in sp)
        specs.append({**b, "id": "d1", "behind": {**b["behind"], "drawing": True}})
        ovs.append({**next(o for o in ovs if o["id"] == b["id"]), "id": "d1"})
        self.project(ovs, specs, segs, music_palette={"name": "lofi", "key": 0})
        (self.d / "gfx").mkdir(exist_ok=True)
        for sp in specs:
            if "behind" in sp: (self.d / "gfx" / f"{sp['id']}.cover.json").write_text(json.dumps({"covered": 0.05}))
        (self.d / "gfx" / "d1.cover.json").write_text(json.dumps({"covered": 0.6}))  # the barrier's arm passes behind the head
        r, rep = self.run_check("long", "--phase", "behind")
        self.assertEqual(r.returncode, 0, rep["long.behind_readable"]["detail"])
        self.assertNotIn("d1", rep["long.behind_readable"]["detail"])

    def test_separate_screens_and_reading_time_are_measured(self):  # Kamil 5.11: "zbyt często osobny ekran", "nie zdąży się przeczytać"
        sys.path.insert(0, str(ROOT))
        import film_check
        specs = {"a": {"type": "scene", "els": [{"k": "node", "text": "AI pisze kod"}] * 5}, "b": {"type": "slide"},
                 "c": {"type": "kw", "text": "jedno dwa trzy cztery"},
                 "f": {"type": "float", "html": '<style>.x{a:b}</style><div><span>W</span><span>Y</span><b>Z</b></div><p>dwa słowa</p>'}}
        edl = {"overlays": [{"id": "a", "at": 0, "dur": 3}, {"id": "b", "at": 3.02, "dur": 4}, {"id": "c", "at": 8, "dur": 1},
                            {"id": "b", "at": 7.5, "dur": 2}, {"id": "f", "at": 20, "dur": 3}]}
        self.assertEqual(film_check.full_spans(edl, specs), [(0, 7.02), (7.5, 9.5)])  # back to back = one screen; kw and float are not
        self.assertEqual(film_check.read_words(specs["f"]), 3)  # css out, a word drawn letter by letter is one word
        self.assertEqual(film_check.read_words(specs["a"]), 15)  # "node" is a piece kind, not text
        ovs, sp, segs = self.full_long()
        self.project(ovs, sp, segs)
        f = film_check.Film(self.d, "long")
        share, detail = f.full_screen_share()
        self.assertAlmostEqual(share, (6 * 12 + 3 * 3 + 8) / 600, places=2)  # scenes, chapters, end card; stickers are beside him
        self.assertIn("separate screens", detail)
        f.ovs.append({"id": "kx", "at": 1, "dur": 1.0}); f.specs["kx"] = {"type": "kw", "text": "jedno dwa trzy cztery pięć sześć"}
        f.ovs.append({"id": "s9", "at": 30, "dur": 3.0}); f.specs["s9"] = {"type": "scene", "els": []}
        n, detail = f.cards_shorter_than_reading()
        self.assertIn("kx 1.0 s < 5.5 s", detail)  # 4 words x 1.2 s + 2 more x 0.35 s
        self.assertIn("s9 3.0 s < 6.0 s", detail)  # a scene: 6 s at least, whatever its words
        self.assertNotIn("k1 ", detail)  # "kw" cards of the fixture: no words, 4 s >= 2.5 s
        self.assertEqual(n, 2)
        self.assertEqual(f.screen_switches_per_min()[0], round(len(film_check.full_spans(f.edl, f.specs)) / 10, 2))

    def test_face_full_counts_only_the_bare_face(self):  # PLAN 1.1: nothing of the EDL on the face (course author study, n=1)
        sys.path.insert(0, str(ROOT))
        import film_check
        ovs = [{"id": "a", "at": 0, "dur": 100}, {"id": "b", "at": 50, "dur": 100}, {"id": "k", "at": 580, "dur": 50}]  # overlap, past the end
        self.project(ovs, [{"id": "a", "type": "scene"}, {"id": "b", "type": "kw"}, {"id": "k", "type": "sticker"}])
        f = film_check.Film(self.d, "long")
        f.edl["broll"] = [{"at": 200, "dur": 100}, {"at": 250, "dur": 100}, {"dur": 5}]  # overlapping b-roll; one without "at" is ignored
        share, detail = f.face_full()
        self.assertEqual(share, round((600 - 150 - 150 - 20) / 600, 3))  # 0-150 cards, 200-350 b-roll, 580-600 sticker
        self.assertIn("280 s of 600 s", detail)
        f.edl["overlays"] = []; f.ovs = []; f.edl["broll"] = []
        self.assertEqual(f.face_full()[0], 1.0)

    def test_a_long_without_memes_is_named(self):  # Kamil 4.11: "miały być też memy, memów nie ma"
        ovs, specs, segs = self.full_long()
        ovs = [o for o in ovs if not o["id"].startswith("m")]
        self.project(ovs, specs, segs, sfx_style="v2", music_palette={"name": "lofi", "key": 2},
                     music_moods=[[0, "story"], [200, "tension"], [400, "upbeat"]])
        r, rep = self.run_check("long")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(rep["long.memes"]["status"], "FAIL")
        self.assertEqual([k for k, v in rep.items() if v["status"] == "FAIL"], ["long.memes"])

    def test_a_short_needs_a_meme_or_a_reason(self):
        def short(ovs, specs, **plan):
            (self.d / "edl_s1.json").write_text(json.dumps({"segments": [{"src": "A", "in": 0.0, "out": 40.0, "zoom": 1.0}], "overlays": ovs}))
            (self.d / "specs.json").write_text(json.dumps(specs))
            (self.d / "plan_s1.json").write_text(json.dumps({"words": "w.json", "edl_out": "edl_s1.json", "gfx_specs": "specs.json",
                                                             "vertical": True, **plan}))
            return self.run_check("s1")[1]["short.meme"]
        meme = ([{"id": "m", "at": 5, "dur": 3}], [{"id": "m", "type": "meme", "canvas": "v", "meme": "drake"}])
        self.assertEqual(short(*meme)["status"], "OK")
        self.assertEqual(short([], [])["status"], "FAIL")
        self.assertEqual(short([], [], skip={"short.meme": "no face gap of 3.5 s"})["status"], "SKIP")

    def test_a_short_hook_is_checked_against_the_six_killers(self):  # hook_check.py, short.hook_lint
        def lint(**plan):
            (self.d / "edl_s1.json").write_text(json.dumps({"segments": [{"src": "A", "in": 0.0, "out": 40.0, "zoom": 1.0}], "overlays": []}))
            (self.d / "specs.json").write_text("[]")
            (self.d / "plan_s1.json").write_text(json.dumps({"words": "w.json", "edl_out": "edl_s1.json", "gfx_specs": "specs.json",
                                                             "vertical": True, **plan}))
            return self.run_check("s1")[1]["short.hook_lint"]
        self.assertEqual(lint(hook_text=HOOKS[0])["status"], "OK")
        bad = lint(hook_text="Cześć, dzisiaj o moim systemie")
        self.assertEqual(bad["status"], "FAIL"); self.assertIn("greeting", bad["detail"]); self.assertIn("no stake", bad["detail"])
        self.assertIn("no text", lint()["detail"])  # nothing on screen in the first frame

    def test_opening_part_without_chapter(self):
        """the first part may say "chap": false (the hook stands there); it still needs its explainer"""
        ovs, specs, segs = self.full_long()
        ovs = [o for o in ovs if o["id"] != "c0"]
        self.project(ovs, specs, segs, sfx_style="v2", music_palette={"name": "lofi", "key": 2},
                     music_moods=[[0, "story"], [200, "tension"], [400, "upbeat"]])
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.chapters"]["status"], "FAIL")
        self.assertIn("Wstęp", rep["long.chapters"]["detail"])
        story = json.loads((self.d / "story.json").read_text()); story["parts"][0]["chap"] = False
        (self.d / "story.json").write_text(json.dumps(story))
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.chapters"]["status"], "OK")

    def test_skip_needs_a_reason(self):
        ovs, specs, segs = self.full_long()
        ovs = [o for o in ovs if not o["id"].startswith("b")]
        self.project(ovs, specs, segs, sfx_style="v2", music_palette={"name": "lofi", "key": 2},
                     music_moods=[[0, "story"], [200, "tension"], [400, "upbeat"]], skip={"long.behind": "ok"})
        r, rep = self.run_check("long")
        self.assertEqual(rep["long.behind"]["status"], "FAIL")  # "ok" is not a reason
        self.project(ovs, specs, segs, sfx_style="v2", music_palette={"name": "lofi", "key": 2},
                     music_moods=[[0, "story"], [200, "tension"], [400, "upbeat"]], skip={"long.behind": "plain wall, nothing to hide text behind"})
        r, rep = self.run_check("long")
        self.assertEqual(rep["long.behind"]["status"], "SKIP")
        self.assertEqual(r.returncode, 0, json.dumps({k: v for k, v in rep.items() if v["status"] == "FAIL"}, ensure_ascii=False))

    def test_same_music_as_the_last_film_is_refused(self):
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segs, sfx_style="v2", music_palette={"name": "lofi", "key": 2},
                     music_moods=[[0, "story"], [200, "tension"], [400, "upbeat"]])
        self.ledger.write_text(json.dumps({"x::long": {"work": "/elsewhere", "film": "long", "name": "lofi", "key": 2, "at": "2026-11-01T10:00:00"}}))
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.music_palette"]["status"], "FAIL")
        self.ledger.write_text(json.dumps({"x::long": {"work": "/elsewhere", "film": "long", "name": "lofi", "key": 0, "at": "2026-11-01T10:00:00"}}))
        _, rep = self.run_check("long")
        self.assertEqual(rep["long.music_palette"]["status"], "OK")  # another key is another piece

    def test_a_broken_hook_lint_file_is_named_not_a_traceback(self):  # review 2026-11-07: KeyError came from the loop
        import film_check
        import hook_check
        (self.d / "clips.json").write_text(json.dumps({"items": [{"id": "s1", "make": True, "hook": HOOKS[0], "hooks": HOOKS, "hook_from": "mech-contrarian"}]}))
        real = hook_check.lists
        try:
            hook_check.lists = lambda path=None: {"max_words": 12}  # "greeting" and the rest gone
            ok, detail = film_check.Out(self.d, self.d / "out").out_hooks()
        finally:
            hook_check.lists = real
        self.assertFalse(ok)
        self.assertIn("cannot be read", detail)

    def test_stills_item_names_a_missing_sheet_and_a_card_without_acceptance(self):  # film_check long.stills (ADR-0018)
        import film_check
        ovs, specs, segs = self.full_long()
        self.project(ovs, specs, segments=segs)
        f = film_check.Film(self.d, "long")
        self.assertTrue(f.stills_accepted()[0])
        self.accept_stills([o["id"] for o in ovs[1:]])
        ok, detail = f.stills_accepted()
        self.assertFalse(ok); self.assertIn(ovs[0]["id"], detail)
        self.accept_stills([o["id"] for o in ovs])
        (self.d / "gfx" / "stills" / f"{ovs[2]['id']}.key").write_text("newer")  # a still drawn after the acceptance
        ok, detail = f.stills_accepted()
        self.assertFalse(ok); self.assertIn(ovs[2]["id"], detail)
        (self.d / "gfx" / "stills" / "accepted.json").unlink()
        self.assertIn("no stills sheet yet", f.stills_accepted()[1])
        f.ovs = []
        self.assertEqual(f.stills_accepted(), (True, "no cards"))  # nothing to look at: never a check that cannot pass

    def test_out_folder(self):
        (self.d / "clips.json").write_text(json.dumps({"items": [{"id": "s1", "make": True, "hook": HOOKS[0], "hooks": HOOKS, "hook_from": "mech-contrarian"},
                                                              {"id": "s9", "make": False}]}))
        (self.d / "posts.json").write_text(json.dumps({"items": [{"id": "p1", "make": True}]}))
        out = self.d / "out"
        r, rep = self.run_check("--out", str(out))
        self.assertEqual(r.returncode, 1)
        self.assertIn("s1", rep["out.shorts_all"]["detail"])
        for p, body in {"long/film.mp4": "", "shorts/s1.mp4": "", 
                        "thumbnails/s1_cover.jpg": "", "posts/p1/post.md": "x", "posts/p1/slide.png": "",
                        "posts/p1/linkedin.json": json.dumps({"text": "Recenzent znalazł błąd w wydaniu.\n" + " ".join(["słowo"] * 80) + "\nRepo w komentarzu.\nA jak to wygląda u Ciebie?", "hashtags": ["AI"]}),
                        "youtube/shorts/s1.md": "## Tytuł\n## Opis\nJedno zdanie.\nPełny film: {{LONG_URL}}\n## Powiązany film\nlong\n",
                        "youtube/long.md": LONG_MD}.items():
            (out / p).parent.mkdir(parents=True, exist_ok=True); (out / p).write_text(body)
        (self.d / "thumbs.json").write_text(json.dumps({"long": [{"id": "A", "big": "BLIZNA"}, {"id": "B", "big": "SZLABAN"}]}))
        thumb(out / "thumbnails/long_A.jpg", "BLIZNA"); thumb(out / "thumbnails/long_B.jpg", "SZLABAN")
        r, rep = self.run_check("--out", str(out))
        self.assertIn("numbers in the posts cannot be checked", rep["out.posts"]["detail"])  # no words of the long: never a silent skip
        self.assertIn("no grafika.png", rep["out.posts"]["detail"])  # a picture alone is not enough: the graphic that says it (post_check)
        post_graphic(out / "posts/p1")
        self.assertIn("no out/blog", rep["out.article"]["detail"])
        (out / "blog/bramki-dla-agenta").mkdir(parents=True)
        test_article.article(out / "blog/bramki-dla-agenta")  # the blog article for kamiljan.com (article_check)
        r, rep = self.run_check("--out", str(out))
        self.assertIn("cannot be checked", rep["out.article"]["detail"])  # no words of the long: the numbers check must not pass quietly
        self.assertIn("opening cannot be checked", rep["out.titles"]["detail"])  # nor the titles' promise
        self.assertIn("Instagram captions cannot be checked", rep["out.instagram"]["detail"])
        self.assertIn("numbers in the descriptions cannot be checked", rep["out.youtube"]["detail"])  # review 2026-11-08: X3 never skips quietly
        test_ig_check.make(out)  # out/instagram/p01: one carousel that passes ig_check
        opening(self.d)
        if not (self.d / "plan_long.json").exists(): (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json"}))
        r, rep = self.run_check("--out", str(out))
        bad = {k: v for k, v in rep.items() if v["status"] != "OK" and (k not in ("out.posts", "out.thumbs_read") or shutil.which("tesseract"))
               and (k != "out.thumbs_read" or FACE_MODEL.is_file())}
        self.assertEqual(bad, {}, json.dumps(bad, ensure_ascii=False))  # out.posts and out.thumbs_read read by OCR (tesseract: local and CI); the face model is not in git (models/), CI has none

    def test_posts_need_their_own_publish_day(self):  # round 2 LI6
        import film_check
        (self.d / "posts.json").write_text(json.dumps({"items": [{"id": "p1", "make": True, "publish_day": 1}, {"id": "p2", "make": True, "publish_day": 1},
                                                               {"id": "p3", "make": True}]}))
        o = film_check.Out(self.d, self.d / "out")
        self.assertEqual(o.publish_days(["p1", "p2", "p3"]), ["publish_day 1: p1, p2 (one post a day)"])
        self.assertTrue(any("p3: no publish_day" in w for _, w in o.warns), o.warns)
        (self.d / "posts.json").write_text(json.dumps({"items": ["junk", {"id": "p1", "publish_day": [1]}, {"id": "p2", "publish_day": "1"}]}))
        o = film_check.Out(self.d, self.d / "out")  # review 2026-11-07: code-3, data-2 (no TypeError, "1" is not 1)
        self.assertEqual(o.publish_days(["p1", "p2"]), ["p1: publish_day [1] is not a whole number of days >= 0", "p2: publish_day '1' is not a whole number of days >= 0"])

    def test_titles_are_checked_against_length_phrase_source_and_opening(self):  # title_check.py, out.titles
        opening(self.d)
        (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json"}))
        yt = self.d / "out" / "youtube"; yt.mkdir(parents=True)
        cases = {"too long": (LONG_MD.replace("AI agent mówi gotowe", "AI agent mówi gotowe, a potem przez cały tydzień naprawiam to, co zepsuł"), "B: 72 characters"),
                 "phrase late": (LONG_MD.replace("Agent AI kłamie, że kod działa", "Dlaczego mój program kłamie o kodzie z AI"), "C: no word of the phrase"),
                 "no source": (LONG_MD.replace("| kanał X: Agent AI kłamie |", "|  |"), "C: empty źródło"),
                 "promise not said": (LONG_MD.replace("Kod z AI, który sam się sprawdza", "Kod: 92% mniej przeglądów w miesiąc"), "A: the first 30 s say")}
        for name, (md, want) in cases.items():
            with self.subTest(name):
                (yt / "long.md").write_text(md)
                _, rep = self.run_check("--out", str(self.d / "out"))
                self.assertEqual(rep["out.titles"]["status"], "FAIL")
                self.assertIn(want, rep["out.titles"]["detail"])
        (yt / "long.md").write_text(LONG_MD)
        _, rep = self.run_check("--out", str(self.d / "out"))
        self.assertEqual(rep["out.titles"]["status"], "OK", rep["out.titles"])

    def test_bad_inputs_are_named_with_exit_2(self):  # 1 means "items missing"; a broken file is another thing
        self.project(*self.full_long(), music_palette={"name": "lofi", "key": 2})
        (self.d / "story.json").write_text(json.dumps({"parts": [{"id": "p1", "start_word": 0}, {"id": "p9", "start_word": 999}]}))
        r, _ = self.run_check("long")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("p9", r.stderr); self.assertIn("start_word", r.stderr); self.assertNotIn("Traceback", r.stderr)
        (self.d / "story.json").write_text(json.dumps({"parts": [{"id": "p1", "start_word": 0}]}))
        for broken in ('{"a": ', "[]"):  # a cut write of make_beds.py; valid JSON of the wrong shape
            self.ledger.write_text(broken)
            r, _ = self.run_check("long")
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("music ledger", r.stderr); self.assertNotIn("Traceback", r.stderr)
        self.ledger.unlink()
        (self.d / "story.json").write_text(json.dumps({"parts": 5}))
        r, _ = self.run_check("long")
        self.assertEqual(r.returncode, 2, r.stderr); self.assertNotIn("Traceback", r.stderr)

    def test_out_thumbnails_one_variant_is_not_ab(self):
        # long_A.jpg + its 2560 copy is still one variant (thumbs.mjs stopped before B)
        (self.d / "clips.json").write_text(json.dumps({"items": []}))
        th = self.d / "out" / "thumbnails"; th.mkdir(parents=True)
        for f in ("long_A.jpg", "long_A_2560.png"): (th / f).write_text("")
        _, rep = self.run_check("--out", str(self.d / "out"))
        self.assertEqual(rep["out.thumbs"]["status"], "FAIL")
        self.assertIn("1 long thumbnail variants", rep["out.thumbs"]["detail"])


    def test_checklist_args_that_do_not_fit_the_metric_name_the_item(self):
        sys.path.insert(0, str(ROOT))
        import film_check  # review 2026-11-05: a typo in "args" gave a bare TypeError traceback

        class Obj:
            def __init__(self): self.plan = {}
            def metric(self, scene_min=3.0): return True
        item = {"id": "short.reading", "metric": "metric", "op": "true"}
        self.assertEqual(film_check.judge(Obj(), item)[0], "OK")
        for args in ({"scene_mni": 2}, [1]):
            with self.assertRaises(SystemExit) as e: film_check.judge(Obj(), {**item, "args": args})
            self.assertIn("short.reading", str(e.exception))


    def test_separate_screen_metrics_measure_switches_blocks_and_the_gap_between(self):
        # review 2026-11-05 r2: long.screen_switches, long.screen_block and long.speaker_back had no test of their values
        sys.path.insert(0, str(ROOT))
        import film_check
        f = film_check.Film.__new__(film_check.Film)
        f.specs = {"a": {"type": "web"}, "b": {"type": "web"}, "c": {"type": "web"}, "k": {"type": "kw"}}
        f.edl = {"overlays": [{"id": "a", "at": 10.0, "dur": 8.0}, {"id": "b", "at": 18.02, "dur": 4.0},  # back to back: one block
                              {"id": "c", "at": 24.0, "dur": 6.0}, {"id": "k", "at": 40.0, "dur": 3.0}]}  # a kw is not a separate screen
        f.len = 120.0
        self.assertEqual(film_check.full_spans(f.edl, f.specs), [(10.0, 22.02), (24.0, 30.0)])
        self.assertEqual(f.screen_switches_per_min()[0], 1.0)  # 2 screens in 2 min
        self.assertEqual(f.screen_block_median()[0], 12.0)  # blocks 6 and 12 s: the upper middle
        self.assertEqual(f.full_screen_min_gap()[0], 2.0)  # 22.02 -> 24.0: under long.speaker_back (3 s)
        f.edl = {"overlays": [{"id": "k", "at": 1.0, "dur": 2.0}]}
        self.assertEqual((f.screen_block_median()[0], f.full_screen_min_gap()[0]), (999.0, 999.0))  # none: nothing to fail

    def test_a_type_error_inside_a_metric_is_not_blamed_on_args(self):
        sys.path.insert(0, str(ROOT))
        import film_check

        class Obj:
            def __init__(self): self.plan = {}
            def metric(self): raise TypeError("a bug inside the metric")
        with self.assertRaises(TypeError): film_check.judge(Obj(), {"id": "x.y", "metric": "metric", "op": "true"})


    def test_a_short_ends_on_its_last_word(self):
        sys.path.insert(0, str(ROOT))
        import film_check
        f = film_check.Film.__new__(film_check.Film)
        f.specs, f.ovs, f.edl = {"e": {"type": "end"}}, [], {"tail": 0}
        self.assertTrue(f.ends_on_the_last_word(tail_max=0.6)[0])
        f.edl = {"tail": 0.6}
        self.assertTrue(f.ends_on_the_last_word(tail_max=0.6)[0])  # the bound itself passes
        f.edl = {"tail": 3}
        self.assertFalse(f.ends_on_the_last_word(tail_max=0.6)[0])  # a 3 s end screen
        f.edl, f.ovs = {"tail": 0}, [{"id": "e", "at": 40.0, "dur": 3.5}]
        self.assertFalse(f.ends_on_the_last_word(tail_max=0.6)[0])  # an end card


if __name__ == "__main__":
    unittest.main()


class JudgeLevelTest(unittest.TestCase):
    def test_a_warn_level_item_prints_warn_and_never_fails(self):  # review 2026-11-07: product-2 (face_full n=1)
        import film_check as F

        class Obj:
            def __init__(self): self.plan: dict = {}
            def face_full(self): return 0.58, "750 s bare"
        item = {"id": "long.face_full", "metric": "face_full", "op": "<=", "value": 0.35, "why": ""}
        self.assertEqual(F.judge(Obj(), item)[0], "FAIL")
        st, detail = F.judge(Obj(), {**item, "level": "warn"})
        self.assertEqual(st, "WARN"); self.assertIn("0.58 <= 0.35", detail)

