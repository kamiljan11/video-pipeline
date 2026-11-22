"""watch_render.py: one line when a run ends, fails or stops moving."""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import watch_render


class WatchRenderTest(unittest.TestCase):
    def test_a_run_still_going_has_no_verdict(self):
        self.assertIsNone(watch_render.verdict(["DONE s01", "FAILED film_check s02"]))

    def test_a_finished_run_names_its_films(self):
        self.assertEqual(watch_render.verdict(["DRY_OK long", "ALL_DONE"]), (0, "DONE long"))

    def test_a_failed_film_fails_the_run(self):
        code, line = watch_render.verdict(["DONE s01", "FAILED lip_check s02", "ALL_DONE", "FAILED_FILMS s02"]) or (0, "")
        self.assertEqual(code, 1)
        self.assertIn("FAILED lip_check s02", line)

    def run_watch(self, log: Path, *more: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(ROOT / "watch_render.py"), str(log), "--poll", "0.1", *more],
                              check=False, capture_output=True, text=True, timeout=30)

    def test_an_old_all_done_in_the_log_is_not_this_run(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "render.log"
            log.write_text("ALL_DONE\n", encoding="utf-8")
            r = self.run_watch(log, "--stall", "0.5")
            self.assertEqual(r.returncode, 3, r.stdout)
            self.assertIn("STALL", r.stdout)

    def test_a_folder_that_keeps_changing_is_not_a_stall(self):
        with tempfile.TemporaryDirectory() as d:
            log, film = Path(d) / "render.log", Path(d) / "long"
            film.mkdir()
            log.write_text("", encoding="utf-8")
            p = subprocess.Popen([sys.executable, str(ROOT / "watch_render.py"), str(log), "--poll", "0.1", "--stall", "1", str(film)],
                                 stdout=subprocess.PIPE, text=True)
            for i in range(15):  # 1.5 s of work in the film's folder, longer than the stall limit
                (film / f"w{i}.mp4").write_text("x", encoding="utf-8")
                time.sleep(0.1)
            self.assertIsNone(p.poll())
            with log.open("a", encoding="utf-8") as f: f.write("DONE long\nALL_DONE\n")
            out, _ = p.communicate(timeout=10)
            self.assertEqual(p.returncode, 0, out)
            self.assertEqual(out.strip(), "DONE long")

    def test_newest_sees_one_level_below_a_folder(self):
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d) / "chunks"
            sub.mkdir()
            f = sub / "w0.mp4"
            f.write_text("x", encoding="utf-8")
            os.utime(f, (time.time() + 100, time.time() + 100))
            self.assertGreater(watch_render.newest([d]), time.time() + 50)
            self.assertEqual(watch_render.newest([str(Path(d) / "missing")]), 0.0)


if __name__ == "__main__":
    unittest.main()
