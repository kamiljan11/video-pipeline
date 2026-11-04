"""run_v4.sh gates owned by this repo (the panel repo tests the rest of the script): scene_check before the graphics,
film_check before the music beds, and their logged off switches. run_v4.sh runs as a copy with VP pointed at stub scripts.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = """import os, sys
name = os.path.basename(sys.argv[0])
log = os.environ["RUNV4_LOG"]
open(log, "a").write(name + "\\n")
if os.environ.get("FAIL_" + name.split(".")[0]):
    sys.exit(1)
if name == "assemble.py":
    os.makedirs(sys.argv[2], exist_ok=True)
    open(os.path.join(sys.argv[2], "film.mp4"), "w").write("x")
"""
SCENE = [{"id": "s", "type": "scene", "dur": 3, "els": []}]


@unittest.skipUnless(shutil.which("node"), "node not installed")
class RunV4GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="runv4-gates-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        vp = self.tmp / "vp"
        for rel in ("build_edl.py", "face_track.py", "critic.py", "assemble.py", "music/make_beds.py", "to_otio.py",
                    "beatfx.py", "behind.py", "edl_guard.py", "film_check.py"):
            (vp / rel).parent.mkdir(parents=True, exist_ok=True)
            (vp / rel).write_text(STUB)
        (vp / "gfx").mkdir()
        # node stubs: scene_check fails when FAIL_scene_check is set, render.mjs logs its call
        log_js = "require('fs').appendFileSync(process.env.RUNV4_LOG, '{n}\\n');"
        (vp / "gfx" / "scene_check.mjs").write_text(
            "import fs from 'fs'; fs.appendFileSync(process.env.RUNV4_LOG, 'scene_check.mjs\\n');"
            " if (process.env.FAIL_scene_check) process.exit(1);")
        (vp / "gfx" / "render.mjs").write_text(log_js.format(n="render.mjs").replace("require('fs')", "(await import('fs'))"))
        for venv in (".venv", "matte/.venv"):
            (vp / venv / "bin").mkdir(parents=True)
            (vp / venv / "bin" / "python").symlink_to(shutil.which("python3") or "/usr/bin/python3")
        (vp / "render").mkdir()
        src = (ROOT / "run_v4.sh").read_text()
        self.assertIn("VP=/home/kamil-jan/video-pipeline;", src)
        (vp / "run_v4.sh").write_text(src.replace("VP=/home/kamil-jan/video-pipeline;", f"VP={vp};"))
        self.vp, self.work, self.out = vp, self.tmp / "work", self.tmp / "out"
        self.work.mkdir()
        self.out.mkdir()
        (self.work / "edl_x.json").write_text(json.dumps({"out_name": "film.mp4"}))

    def run_v4(self, rc: int = 0, **env: str) -> tuple[str, list[str]]:
        log = self.tmp / "calls.log"
        r = subprocess.run(["bash", str(self.vp / "run_v4.sh"), str(self.work), str(self.out), "x"], check=False, timeout=60,
                           env={**os.environ, "RUNV4_LOG": str(log), **env}, capture_output=True, text=True)
        self.assertEqual(r.returncode, rc, r.stderr)
        return (self.vp / "render" / "render.log").read_text(), log.read_text().split() if log.exists() else []

    def test_scene_clash_stops_every_film_before_the_graphics(self):
        (self.work / "gfx_specs.json").write_text(json.dumps(SCENE))
        render, calls = self.run_v4(rc=1, FAIL_scene_check="1")
        self.assertIn("FAILED scene_check", render)
        self.assertIn("FAILED_FILMS x", render)
        self.assertEqual(calls, ["scene_check.mjs"])  # no graphics, no film step

    def test_clean_scenes_go_on_to_the_render(self):
        (self.work / "gfx_specs.json").write_text(json.dumps(SCENE))
        render, calls = self.run_v4()
        self.assertEqual(calls[:2], ["scene_check.mjs", "render.mjs"])
        self.assertIn("DONE x", render)

    def test_no_scene_card_no_scene_check(self):
        (self.work / "gfx_specs.json").write_text(json.dumps([{"id": "c", "type": "chap"}]))
        _, calls = self.run_v4()
        self.assertNotIn("scene_check.mjs", calls)

    def test_scene_check_off_is_logged_and_skipped(self):
        (self.work / "gfx_specs.json").write_text(json.dumps(SCENE))
        render, calls = self.run_v4(SCENE_CHECK="off", FAIL_scene_check="1")
        self.assertIn("WARN scene_check off", render)
        self.assertNotIn("scene_check.mjs", calls)
        self.assertIn("DONE x", render)

    def test_failed_film_check_renders_nothing(self):
        render, calls = self.run_v4(rc=1, FAIL_film_check="1")
        self.assertIn("FAILED film_check x", render)
        self.assertNotIn("make_beds.py", calls)
        self.assertNotIn("assemble.py", calls)

    def test_film_check_off_is_logged_and_skipped(self):
        render, calls = self.run_v4(FILM_CHECK="off", FAIL_film_check="1")
        self.assertIn("WARN film_check off x", render)
        self.assertNotIn("film_check.py", calls)
        self.assertIn("DONE x", render)


if __name__ == "__main__":
    unittest.main()
