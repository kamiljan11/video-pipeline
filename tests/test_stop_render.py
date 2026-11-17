import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stop_render


class MatchesTest(unittest.TestCase):
    R = "/home/someone/video-pipeline/render/"

    def test_pipeline_scripts_match(self):
        self.assertTrue(stop_render.matches("bash /x/run_v4.sh plan.json", self.R))
        self.assertTrue(stop_render.matches("/x/.venv/bin/python assemble.py edl_long.json", self.R))

    def test_ffmpeg_on_this_render_dir_matches_by_any_binary_path(self):
        for argv0 in ("ffmpeg", "/home/someone/.local/bin/ffmpeg", "/usr/bin/ffmpeg"):
            self.assertTrue(stop_render.matches(f"{argv0} -i {self.R}long/a.mp4 out.mp4", self.R), argv0)

    def test_other_processes_do_not_match(self):
        self.assertFalse(stop_render.matches("ffmpeg -i /home/someone/Videos/x.mp4 y.mp4", self.R))
        self.assertFalse(stop_render.matches("ffprobe " + self.R + "a.mp4", self.R))
        self.assertFalse(stop_render.matches("vim notes-about-ffmpeg " + self.R, self.R))

    def test_default_render_dir_is_this_checkout(self):
        self.assertEqual(stop_render.RENDER, str(Path(stop_render.__file__).resolve().parent / "render") + "/")


if __name__ == "__main__":
    unittest.main()
