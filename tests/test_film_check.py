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

ROOT = Path(__file__).resolve().parent.parent
BRAND = json.loads((ROOT / "style" / "brand.json").read_text())["lower_sub"]


def words(n: int, step: float = 1.0) -> dict:
    return {"transcription": [{"offsets": {"from": round(i * step * 1000), "to": round((i * step + 0.5) * 1000)}, "text": f" w{i}"}
                              for i in range(n)]}


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
        (self.d / "edl_long.json").write_text(json.dumps({"segments": segs, "overlays": overlays}))
        (self.d / "specs.json").write_text(json.dumps(specs))
        (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json", "edl_out": "edl_long.json", "gfx_specs": "specs.json", **plan}))

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
            ovs.append({"id": f"s{k}", "at": 10 + 100 * k, "dur": 8}); specs.append({"id": f"s{k}", "type": "scene"})
        for k, at in enumerate(range(20, 600, 12)):
            ovs.append({"id": f"k{k}", "at": at, "dur": 4}); specs.append({"id": f"k{k}", "type": "kw"})
        for k, at in enumerate((2, 5)):
            ovs.append({"id": f"b{k}", "at": at, "dur": 2}); specs.append({"id": f"b{k}", "type": "float", "behind": {"edl": "edl_long.json"}})
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

    def test_out_folder(self):
        (self.d / "clips.json").write_text(json.dumps({"items": [{"id": "s1", "make": True}, {"id": "s9", "make": False}]}))
        (self.d / "posts.json").write_text(json.dumps({"items": [{"id": "p1", "make": True}]}))
        out = self.d / "out"
        r, rep = self.run_check("--out", str(out))
        self.assertEqual(r.returncode, 1)
        self.assertIn("s1", rep["out.shorts_all"]["detail"])
        for p, body in {"long/film.mp4": "", "shorts/s1.mp4": "", "thumbnails/long_A.jpg": "", "thumbnails/long_B.jpg": "",
                        "thumbnails/s1_cover.jpg": "", "posts/p1/post.md": "x", "posts/p1/slide.png": "",
                        "youtube/shorts/s1.md": "## Tytuł\n## Opis\n",
                        "youtube/long.md": "## Tytuły\n| A | t |\n| B | t |\n| C | t |\n## Opis\nx\n## Rozdziały\n0:00 a\n1:00 b\n2:00 c\n## Tagi\nx\n"}.items():
            (out / p).parent.mkdir(parents=True, exist_ok=True); (out / p).write_text(body)
        r, rep = self.run_check("--out", str(out))
        self.assertEqual(r.returncode, 0, json.dumps({k: v for k, v in rep.items() if v["status"] != "OK"}, ensure_ascii=False))

    def test_bad_inputs_are_named_with_exit_2(self):  # 1 means "items missing"; a broken file is another thing
        self.project(*self.full_long(), music_palette={"name": "lofi", "key": 2})
        (self.d / "story.json").write_text(json.dumps({"parts": [{"id": "p1", "start_word": 0}, {"id": "p9", "start_word": 999}]}))
        r, _ = self.run_check("long")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("p9", r.stderr); self.assertIn("start_word", r.stderr); self.assertNotIn("Traceback", r.stderr)
        (self.d / "story.json").write_text(json.dumps({"parts": [{"id": "p1", "start_word": 0}]}))
        self.ledger.write_text('{"a": ')  # a cut write of make_beds.py
        r, _ = self.run_check("long")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("music ledger", r.stderr); self.assertNotIn("Traceback", r.stderr)

    def test_out_thumbnails_one_variant_is_not_ab(self):
        # long_A.jpg + its 2560 copy is still one variant (thumbs.mjs stopped before B)
        (self.d / "clips.json").write_text(json.dumps({"items": []}))
        th = self.d / "out" / "thumbnails"; th.mkdir(parents=True)
        for f in ("long_A.jpg", "long_A_2560.png"): (th / f).write_text("")
        _, rep = self.run_check("--out", str(self.d / "out"))
        self.assertEqual(rep["out.thumbs"]["status"], "FAIL")
        self.assertIn("1 long thumbnail variants", rep["out.thumbs"]["detail"])


if __name__ == "__main__":
    unittest.main()
