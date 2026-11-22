import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stop_render


class MatchesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); t = self.tmp.name
        self.root = os.path.join(t, "vp"); os.makedirs(os.path.join(self.root, "render", "long"))
        self.other = os.path.join(t, "other"); os.makedirs(os.path.join(self.other, "render"))
        self.link = os.path.join(t, "vp-link"); os.symlink(self.root, self.link)

    def tearDown(self):
        self.tmp.cleanup()

    def m(self, argv, cwd=None):
        return stop_render.matches(argv, cwd or self.root, self.root)

    def test_this_checkouts_scripts_match_absolute_relative_or_through_a_symlink(self):
        self.assertTrue(self.m(["bash", f"{self.root}/run_v4.sh", "plan.json"], "/"))
        self.assertTrue(self.m(["bash", "run_v4.sh", "plan.json"]))
        self.assertTrue(self.m(["bash", f"{self.link}/run_v4.sh"], "/"))
        self.assertTrue(self.m(["/x/.venv/bin/python", "assemble.py", "edl_long.json"]))

    def test_another_checkouts_scripts_do_not_match(self):
        self.assertFalse(self.m(["bash", f"{self.other}/run_v4.sh"], "/"))
        self.assertFalse(self.m(["bash", "run_v4.sh"], self.other))
        self.assertFalse(self.m(["python3", "assemble.py", "edl_x.json"], self.other))

    def test_an_editor_or_tail_on_the_script_does_not_match(self):
        self.assertFalse(self.m(["vim", "run_v4.sh"]))
        self.assertFalse(self.m(["tail", "-f", "run_v4.sh"]))

    def test_ffmpeg_on_this_render_dir_matches_by_any_binary_or_argument_path(self):
        for argv0 in ("ffmpeg", "/home/someone/.local/bin/ffmpeg"):
            self.assertTrue(self.m([argv0, "-i", f"{self.root}/render/long/a.mp4", "out.mp4"], "/"), argv0)
        self.assertTrue(self.m(["ffmpeg", "-i", "render/long/a.mp4", "o.mp4"]))
        self.assertTrue(self.m(["ffmpeg", "-i", f"{self.link}/render/long/a.mp4"], "/"))

    def test_other_ffmpeg_or_ffprobe_does_not_match(self):
        self.assertFalse(self.m(["ffmpeg", "-i", f"{self.other}/render/a.mp4"], "/"))
        self.assertFalse(self.m(["ffmpeg", "-i", "/home/someone/Videos/x.mp4"], "/"))
        self.assertFalse(self.m(["ffprobe", f"{self.root}/render/a.mp4"], "/"))
        self.assertFalse(self.m([], "/"))

    def test_default_root_is_this_checkout(self):
        self.assertEqual(stop_render.ROOT, str(Path(stop_render.__file__).resolve().parent))


if __name__ == "__main__":
    unittest.main()
