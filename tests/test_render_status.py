"""render_status.py: stage and film from the unit's command lines, the stage-2 ffmpeg, the ETA of the whole set."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import render_status as R

FILMS = ["long", "s01", "s02", "s03"]


class Stage(unittest.TestCase):
    def test_assemble_wins_over_the_shell_and_names_the_film(self):
        cmds = [["bash", "run_v4.sh", "W", "O", "long"], ["python3", "/vp/assemble.py", "edl_long.json", "/vp/render/long"]]
        self.assertEqual(R.stage_of(cmds), ("assemble", "long"))

    def test_gfx_and_plan_film(self):
        self.assertEqual(R.stage_of([["node", "/vp/gfx/render.mjs", "gfx_specs.json", "gfx"]]), ("gfx", None))
        self.assertEqual(R.stage_of([["python3", "/vp/critic.py", "plan_s02_szlaban.json", "--fix"]]), ("critic", "s02_szlaban"))

    def test_nothing_known_is_start(self):
        self.assertEqual(R.stage_of([["bash", "-c", "x"]]), ("start", None))

    def test_stage2_ffmpeg_is_the_one_with_a_graph_on_rough(self):
        procs = {1: ["/usr/bin/ffmpeg", "-ss", "3", "-i", "rec.mp4", "seg.mkv"],
                 2: ["/usr/bin/ffmpeg", "-i", "/r/long/rough.mkv", "-i", "a.mov", "-filter_complex", "[0:v]..."]}
        self.assertEqual(R.stage2_pid(procs), 2)
        self.assertIsNone(R.stage2_pid({1: procs[1]}))


class Eta(unittest.TestCase):
    def test_current_film_from_its_rate_plus_the_rest(self):
        e = R.eta(FILMS, [], "long", 0.25, 600.0, [])
        self.assertAlmostEqual(e["current_left_s"], 1800.0)
        self.assertEqual(e["rest_films"], 3)
        self.assertAlmostEqual(e["total_left_s"], 1800 + 3 * R.SHORT_S + R.TAIL_S)

    def test_unknown_until_stage2_has_moved(self):
        self.assertIsNone(R.eta(FILMS, [], "long", 0.01, 30.0, [])["total_left_s"])
        self.assertIsNone(R.eta(FILMS, [], "long", None, None, [])["total_left_s"])

    def test_measured_shorts_replace_the_default(self):
        e = R.eta(FILMS, ["long", "s01"], "s02", 0.5, 60.0, [100.0, 140.0])
        self.assertEqual(e["per_short_s"], 120.0)
        self.assertAlmostEqual(e["total_left_s"], 60 + 120 + R.TAIL_S)

    def test_measured_rate_wins_over_process_age(self):
        e = R.eta(FILMS, [], "long", 0.5, 9999.0, [], rate=0.001)  # 0.1 % of the film per second
        self.assertAlmostEqual(e["current_left_s"], 500.0)

    def test_all_done_leaves_the_tail(self):
        self.assertAlmostEqual(R.eta(FILMS, FILMS, None, None, None, [])["total_left_s"], R.TAIL_S)


class Queue(unittest.TestCase):
    def test_rows_per_format(self):
        q = R.queue(FILMS, ["long", "s01"], "s02", False)
        self.assertEqual([(r["name"], r["done"], r["total"], r["now"]) for r in q[:2]], [("Long", 1, 1, False), ("Shorty", 1, 3, True)])
        self.assertFalse(q[2]["now"])

    def test_long_now_and_finishing(self):
        q = R.queue(FILMS, [], "long", False)
        self.assertTrue(q[0]["now"]); self.assertFalse(q[1]["now"])
        self.assertTrue(R.queue(FILMS, FILMS, None, True)[2]["now"])


class Shell(unittest.TestCase):
    def test_vars_expand_from_earlier_lines(self):
        text = 'VP=/home/k/vp\nO=$VP/render/out_v4\nS="s01 s02"\n'
        self.assertEqual(R.shell_var(text, "O"), "/home/k/vp/render/out_v4")
        self.assertEqual(R.shell_var(text, "S"), "s01 s02")
        self.assertEqual(R.shell_var(text, "X"), "")

    def test_fmt(self):
        self.assertEqual(R.fmt(None), "?")
        self.assertEqual(R.fmt(125), "2 min")
        self.assertEqual(R.fmt(3 * 3600 + 7 * 60), "3 h 07 min")


class Materials(unittest.TestCase):
    def test_counts_what_is_in_the_out_dir(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        for f in ("thumbnails/long_A.jpg", "thumbnails/long_B.jpg", "thumbnails/s01_cover.jpg", "posts/p01/post.md",
                  "posts/p02/grafika.png", "instagram/p01/1.png", "instagram/reels/s01.json", "youtube/long.md",
                  "youtube/shorts/s02.md", "blog/a/article.json"):
            (d / f).parent.mkdir(parents=True, exist_ok=True); (d / f).write_text("x")
        rows = {r["name"]: (r["done"], r["total"]) for r in R.materials(d, ["s01", "s02"])}
        self.assertEqual(rows["Miniatury longa (A/B…)"], (2, 2))
        self.assertEqual(rows["Okładki shortów"], (1, 2))
        self.assertEqual(rows["Posty LinkedIn"], (1, 2))  # p02 has no post.md yet
        self.assertEqual(rows["Karuzele Instagram"], (1, 1))
        self.assertEqual(rows["Opisy reels Instagram"], (1, 2))
        self.assertEqual(rows["Artykuł na bloga"], (1, 1))
        self.assertEqual(rows["Opisy YouTube"], (2, 3))

    def test_empty_out_dir_shows_missing_minimums(self):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d)
        rows = {r["name"]: (r["done"], r["total"]) for r in R.materials(d, ["s01"])}
        self.assertEqual(rows["Miniatury longa (A/B…)"], (0, 2))
        self.assertEqual(rows["Artykuł na bloga"], (0, 1))


if __name__ == "__main__":
    unittest.main()
