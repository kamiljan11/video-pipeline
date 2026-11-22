"""run_v4.sh gates owned by this repo (the panel repo tests the rest of the script): scene_check before the graphics,
film_check before the music beds, and their logged off switches. run_v4.sh runs as a copy with VP pointed at stub scripts.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = """import os, sys
name = os.path.basename(sys.argv[0])
log = os.environ["RUNV4_LOG"]
open(log, "a").write(name + "\\n")
plan = name == "words_check.py" and sys.argv[1:2] == ["plan"]  # the preflight before assemble fails on its own switch
if os.environ.get("FAIL_" + name.split(".")[0]) and not plan:
    sys.exit(1)
if os.environ.get("FAIL_words_plan") and plan:
    sys.exit(1)
if os.environ.get("FAIL_phase") and "--phase" in sys.argv:  # film_check's "behind" phase only
    sys.exit(1)
if os.environ.get("FAIL_report") and "--report" in sys.argv:  # research_gate on the film_check report only
    sys.exit(1)
if name == "dry_run.py":
    open(log, "a").write("dry_run:" + sys.argv[1] + "\\n")
    if os.environ.get("FAIL_dry_" + sys.argv[1]):
        sys.exit(1)
if name == "sound_seen.py":
    open(log, "a").write("sound_seen:" + sys.argv[1] + "\\n")
    if sys.argv[1] == "key": print("k")
    if sys.argv[1] == "same" and not os.environ.get("SOUND_SAME"): sys.exit(1)
if name == "assemble.py":
    if "--dry" in sys.argv:
        open(log, "a").write("assemble:--dry\\n")
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
                    "beatfx.py", "behind.py", "edl_guard.py", "film_check.py", "av_check.py", "sync_check.py", "lip_check.py", "words_check.py",
                    "research_gate.py", "retake_check.py", "music_check.py", "manifest.py", "capabilities.py", "design_ledger.py", "waivers.py", "dry_run.py", "accept.py", "sound_seen.py",
                    "review_player.py", "content_kind.py"):
            (vp / rel).parent.mkdir(parents=True, exist_ok=True)
            (vp / rel).write_text(STUB)
        (vp / "gfx").mkdir()
        # node stubs: scene_check fails when FAIL_scene_check is set, render.mjs logs its call
        log_js = "require('fs').appendFileSync(process.env.RUNV4_LOG, '{n}\\n');"
        (vp / "gfx" / "scene_check.mjs").write_text(
            "import fs from 'fs'; fs.appendFileSync(process.env.RUNV4_LOG, 'scene_check.mjs\\n');"
            " if (process.env.FAIL_scene_check) process.exit(1);"
            " if (process.env.HANG_scene_check) await new Promise(r => setTimeout(r, 30000));")
        (vp / "gfx" / "render.mjs").write_text(log_js.format(n="render.mjs").replace("require('fs')", "(await import('fs'))"))
        for venv in (".venv", "matte/.venv"):
            (vp / venv / "bin").mkdir(parents=True)
            (vp / venv / "bin" / "python").symlink_to(shutil.which("python3") or "/usr/bin/python3")
        (vp / "render").mkdir()
        src = (ROOT / "run_v4.sh").read_text()
        self.assertNotIn("/home/kamil-jan", src)  # VP is the directory the script is in, so the copy runs on vp
        (vp / "run_v4.sh").write_text(src)
        self.vp, self.work, self.out = vp, self.tmp / "work", self.tmp / "out"
        self.work.mkdir()
        self.out.mkdir()
        (self.work / "edl_x.json").write_text(json.dumps({"out_name": "film.mp4"}))

    def run_v4(self, rc: int = 0, film: str = "x", **env: str) -> tuple[str, list[str]]:
        log = self.tmp / "calls.log"
        r = subprocess.run(["bash", str(self.vp / "run_v4.sh"), str(self.work), str(self.out), film], check=False, timeout=60,
                           env={**os.environ, "RUNV4_LOG": str(log), **env}, capture_output=True, text=True)
        self.assertEqual(r.returncode, rc, r.stderr)
        return (self.vp / "render" / "render.log").read_text(), log.read_text().split() if log.exists() else []

    def test_scene_clash_stops_every_film_before_the_graphics(self):
        (self.work / "gfx_specs.json").write_text(json.dumps(SCENE))
        render, calls = self.run_v4(rc=1, FAIL_scene_check="1")
        self.assertIn("FAILED scene_check", render)
        self.assertIn("FAILED_FILMS x", render)
        self.assertEqual(calls, ["accept.py", "scene_check.mjs"])  # no graphics, no film step

    def test_clean_scenes_go_on_to_the_render(self):
        (self.work / "gfx_specs.json").write_text(json.dumps(SCENE))
        render, calls = self.run_v4()
        self.assertEqual(calls[:3], ["accept.py", "scene_check.mjs", "render.mjs"])
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

    def test_hung_scene_check_is_stopped_and_named(self):
        (self.work / "gfx_specs.json").write_text(json.dumps(SCENE))
        render, calls = self.run_v4(rc=1, HANG_scene_check="1", SCENE_CHECK_TIMEOUT="1")
        self.assertIn("FAILED scene_check rc=124 (timeout 1 s", render)
        self.assertNotIn("render.mjs", calls)

    def test_missing_out_folder_stops_before_any_step(self):
        self.out.rmdir()
        render, calls = self.run_v4(rc=2)
        self.assertIn(f"FAILED out: no writable folder {self.out}", render)
        self.assertIn("FAILED_FILMS x", render)
        self.assertEqual(calls, [])

    def run_from(self, cwd: Path, out: str, rc: int) -> str:
        r = subprocess.run(["bash", str(self.vp / "run_v4.sh"), str(self.work), out, "x"], cwd=cwd, check=False, timeout=60,
                           env={**os.environ, "RUNV4_LOG": str(self.tmp / "calls.log")}, capture_output=True, text=True)
        self.assertEqual(r.returncode, rc, r.stderr)
        return (self.vp / "render" / "render.log").read_text()

    def test_a_relative_out_counts_from_the_work_folder(self):
        """the 2026-11-05 incident: OUT relative to the caller's folder is not there after the cd into WORK"""
        render = self.run_from(self.tmp, "out", rc=2)  # tmp/out exists, but work/out does not
        self.assertIn("FAILED out: no writable folder out seen from", render)
        self.assertIn("a relative OUT counts from the work folder", render)
        self.assertIn("DONE x", self.run_from(self.tmp, "../out", rc=0))  # relative to WORK: found

    def test_read_only_out_folder_stops_too(self):
        self.out.chmod(0o555)
        self.addCleanup(self.out.chmod, 0o755)
        render, calls = self.run_v4(rc=2)
        self.assertIn("FAILED out: no writable folder", render)
        self.assertEqual(calls, [])

    def test_cards_behind_the_speaker_are_checked_after_the_cut_out(self):
        (self.work / "gfx_specs.json").write_text(json.dumps([{"id": "b", "type": "float", "behind": {"edl": "edl_x.json"}}]))
        render, calls = self.run_v4()
        i = calls.index("behind.py")
        self.assertEqual(calls[i + 1], "film_check.py")  # the "behind" phase, before assemble.py
        self.assertLess(i + 1, calls.index("assemble.py"))
        self.assertIn("DONE x", render)

    def test_a_hidden_card_behind_the_speaker_renders_nothing(self):
        (self.work / "gfx_specs.json").write_text(json.dumps([{"id": "b", "type": "float", "behind": {"edl": "edl_x.json"}}]))
        render, calls = self.run_v4(rc=1, FAIL_phase="1")
        self.assertIn("FAILED film_check behind x", render)
        self.assertIn("behind.py", calls)
        self.assertNotIn("assemble.py", calls)

    def test_failed_film_check_renders_nothing(self):
        render, calls = self.run_v4(rc=1, FAIL_film_check="1")
        self.assertIn("FAILED film_check x", render)
        self.assertNotIn("make_beds.py", calls)
        self.assertNotIn("assemble.py", calls)

    def test_dropped_voice_keeps_the_film_out_of_out(self):  # av_check after assemble (film 2026-11-04: 0.65 s of voice lost)
        render, calls = self.run_v4(rc=1, FAIL_av_check="1")
        self.assertEqual(calls[calls.index("assemble.py") + 1], "av_check.py")
        self.assertIn("FAILED av_check x", render)
        self.assertNotIn("DONE x", render)
        self.assertFalse((self.out / "film.mp4").exists())

    def test_cards_off_the_words_keep_the_film_out_of_out(self):  # sync_check after av_check
        render, calls = self.run_v4(rc=1, FAIL_sync_check="1")
        self.assertEqual(calls[calls.index("av_check.py") + 1:][:5], ["sound_seen.py", "sound_seen:key", "sound_seen.py", "sound_seen:same", "sync_check.py"])
        self.assertIn("FAILED sync_check x", render)
        self.assertFalse((self.out / "film.mp4").exists())

    def test_the_same_sound_and_cut_are_not_checked_twice(self):  # 2026-11-15 long: 78 of 123 min in checks
        render, calls = self.run_v4(SOUND_SAME="1")
        for gone in ("sync_check.py", "words_check.py", "music_check.py", "retake_check.py", "sound_seen:pass"):
            self.assertNotIn(gone, calls[calls.index("assemble.py"):], gone)
        self.assertIn("av_check.py", calls); self.assertIn("lip_check.py", calls)  # the picture is always checked
        self.assertIn("DONE x", render)

    def test_only_a_dry_run_records_the_sound_checks(self):  # the full render does not run retake_check
        _, calls = self.run_v4()
        self.assertIn("sync_check.py", calls); self.assertNotIn("sound_seen:pass", calls)
        _, calls = self.run_v4(DRY="1")
        self.assertIn("sound_seen:pass", calls[calls.index("retake_check.py"):])
        _, calls = self.run_v4(rc=1, DRY="1", FAIL_retake_check="1")
        self.assertNotIn("sound_seen:pass", calls[-6:])

    def test_a_stale_feature_map_or_a_design_without_rows_stops_the_film(self):  # Kamil 2026-11-09: nothing skipped unseen
        for name, line in (("capabilities", "FAILED capabilities map x"), ("design_ledger", "FAILED design_ledger x")):
            render, calls = self.run_v4(rc=1, **{f"FAIL_{name}": "1"})
            self.assertIn(line, render)
            self.assertNotIn("assemble.py", calls)
            self.assertFalse((self.out / "film.mp4").exists())

    def test_lips_off_the_voice_keep_the_film_out_of_out(self):  # lip_check after sync_check (2026-11-04: voice 46 ms late)
        render, calls = self.run_v4(rc=1, FAIL_lip_check="1")
        self.assertEqual(calls[calls.index("sync_check.py") + 1], "lip_check.py")
        self.assertIn("FAILED lip_check x", render)
        self.assertFalse((self.out / "film.mp4").exists())

    def test_lip_check_off_is_logged_and_skipped(self):
        render, calls = self.run_v4(rc=0, LIP_CHECK="off")
        self.assertIn("LIP_CHECK=off: lip_check skipped for x", render)
        self.assertNotIn("lip_check.py", calls)

    def test_lost_words_keep_the_film_out_of_out(self):  # words_check cut + sound after lip_check
        render, calls = self.run_v4(rc=1, FAIL_words_check="1")
        self.assertEqual(calls[calls.index("lip_check.py") + 1], "words_check.py")
        self.assertIn("FAILED words_check cut x", render)
        self.assertFalse((self.out / "film.mp4").exists())
        render, calls = self.run_v4(rc=0, WORDS_CHECK="off")
        self.assertIn("WORDS_CHECK=off: words_check skipped for x", render)
        self.assertIn("DONE x", render)

    def test_a_plan_the_checks_cannot_read_renders_nothing(self):  # 2026-11-10: the long's words_check crashed after 50 min
        render, calls = self.run_v4(rc=1, FAIL_words_plan="1")
        self.assertIn("FAILED words_check plan x", render)
        self.assertNotIn("assemble.py", calls)
        render, calls = self.run_v4(rc=0, WORDS_CHECK="off", FAIL_words_plan="1")
        self.assertIn("DONE x", render)

    def test_the_kind_is_measured_before_build_edl_and_a_failure_stops_the_film(self):  # ADR-0032
        render, calls = self.run_v4(DRY="1")
        self.assertLess(calls.index("content_kind.py"), calls.index("build_edl.py"))
        (self.tmp / "calls.log").unlink(); (self.vp / "render" / "render.log").unlink()
        render, calls = self.run_v4(rc=1, FAIL_content_kind="1")
        self.assertIn("FAILED content_kind x", render)
        self.assertNotIn("build_edl.py", calls)

    def test_open_research_renders_nothing(self):  # research_gate before build_edl (2026-11-08: 0/24 Long items in the long)
        render, calls = self.run_v4(rc=1, FAIL_research_gate="1")
        self.assertIn("FAILED research_gate long x", render)
        self.assertNotIn("build_edl.py", calls)
        self.assertNotIn("assemble.py", calls)

    def test_a_vertical_plan_is_gated_as_shorts(self):
        (self.work / "plan_x.json").write_text(json.dumps({"vertical": True}))
        render, _ = self.run_v4(rc=1, FAIL_research_gate="1")
        self.assertIn("FAILED research_gate shorts x", render)

    def test_research_missed_in_the_film_renders_nothing(self):  # a done item whose warn-level check is not OK in this film
        render, calls = self.run_v4(rc=1, FAIL_report="1")
        self.assertIn("FAILED research_used long x", render)
        self.assertNotIn("assemble.py", calls)
        self.assertFalse((self.out / "film.mp4").exists())

    def test_research_gate_off_is_logged_and_skipped(self):
        render, calls = self.run_v4(rc=1, RESEARCH_GATE="off", FAIL_research_gate="1", FAIL_build_edl="1")
        self.assertIn("RESEARCH_GATE=off: research_gate skipped for x (long)", render)
        self.assertNotIn("research_gate.py", calls)
        # the capability locks have no off switch: RESEARCH_GATE=off must not reach them (pg-review 2026-11-09)
        self.assertIn("capabilities.py", calls)
        self.assertIn("design_ledger.py", calls)

    def test_a_finished_film_is_stamped_with_the_pipeline_commit(self):  # manifest.py (out.manifest in film_check --out)
        render, calls = self.run_v4(rc=0)
        self.assertIn("DONE x", render)
        self.assertLess(calls.index("assemble.py"), calls.index("manifest.py"))

    def test_the_dry_run_hears_the_cut_for_retakes_and_a_retake_stops_it(self):  # 2026-11-14 fragment at 1:00
        render, calls = self.run_v4(DRY="1")
        self.assertLess(calls.index("words_check.py"), calls.index("retake_check.py"))
        self.assertIn("DRY_OK x", render)
        render, calls = self.run_v4(rc=1, DRY="1", FAIL_retake_check="1")
        self.assertIn("FAILED retake_check x", render)
        self.assertNotIn("DRY_OK x", render.split("FAILED retake_check x")[-1])

    def test_a_long_whose_music_is_not_heard_is_not_done(self):  # 2026-11-14 fragment: bed 48 dB under the voice
        (self.work / "edl_long.json").write_text(json.dumps({"out_name": "film.mp4"}))
        render, calls = self.run_v4(rc=1, film="long", FAIL_music_check="1")
        self.assertIn("FAILED music_check long", render)
        self.assertNotIn("DONE long", render)
        (self.work / "plan_x.json").write_text(json.dumps({"vertical": True}))
        _, calls = self.run_v4(film="x")  # a short (plan "vertical") is not judged by the long's range
        self.assertEqual(calls.count("music_check.py"), 1)  # the call log keeps both runs: only the long's

    def test_the_final_render_does_not_hear_the_cut_again(self):  # same cut as the dry run (dry_run.py digest)
        _, calls = self.run_v4()
        self.assertNotIn("retake_check.py", calls)

    def test_the_kdenlive_project_of_the_long_is_stamped_too(self):  # out.manifest: every part of out/ has a stamp
        (self.work / "edl_long.json").write_text(json.dumps({"out_name": "film.mp4"}))  # the stub assemble writes film.mp4
        _, calls = self.run_v4(film="long")
        self.assertEqual(calls[-2:], ["to_otio.py", "manifest.py"])

    def test_a_failed_stamp_fails_the_film(self):
        render, _ = self.run_v4(rc=1, FAIL_manifest="1")
        self.assertIn("FAILED manifest x", render)

    def test_a_gate_off_without_kamils_waiver_renders_nothing(self):  # 2026-11-04 v5: LIP_CHECK=off on 5 shorts, a log line only
        render, calls = self.run_v4(rc=1, LIP_CHECK="off", FAIL_waivers="1")
        self.assertIn("SKIPPED_GATES: lip_check", render)
        self.assertIn("FAILED waivers x (gates off: lip_check)", render)
        self.assertEqual(calls, ["accept.py", "waivers.py"])

    def test_every_run_names_the_gates_that_are_off(self):
        render, calls = self.run_v4()
        self.assertIn("SKIPPED_GATES: none", render)
        self.assertNotIn("waivers.py", calls)

    def test_gates_off_with_a_waiver_are_named_and_the_film_renders(self):
        render, calls = self.run_v4(LIP_CHECK="off", WORDS_CHECK="off")
        self.assertIn("SKIPPED_GATES: lip_check words_check", render)
        self.assertEqual(calls[:2], ["accept.py", "waivers.py"])
        self.assertIn("DONE x", render)

    def test_no_passed_dry_run_no_full_render(self):  # 2026-11-04 long: 5 full renders, the checks ran after each
        render, calls = self.run_v4(rc=1, FAIL_dry_need="1")
        self.assertIn("FAILED dry_run x", render)
        self.assertNotIn("assemble.py", calls)
        self.assertNotIn("make_beds.py", calls)

    def test_a_dry_run_runs_every_check_and_leaves_no_film(self):
        render, calls = self.run_v4(DRY="1")
        self.assertIn("DRY_OK x", render)
        self.assertNotIn("DONE x", render)
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertIn("assemble:--dry", calls)
        self.assertIn("dry_run:pass", calls)
        self.assertNotIn("dry_run:need", calls)
        for gate in ("av_check.py", "sync_check.py", "lip_check.py", "words_check.py"):
            self.assertIn(gate, calls)
        self.assertNotIn("manifest.py", calls)

    def test_a_dry_run_with_preview_pops_the_film_up_before_the_checks(self):  # Kamil 2026-11-15: watch, note, then render
        render, calls = self.run_v4(DRY="1", PREVIEW="1", PREVIEW_RUN="")
        self.assertRegex(render, r"PREVIEW x http://127\.0\.0\.1:88\d\d/|PREVIEW x http://127\.0\.0\.1:879\d/")  # own port per film
        time.sleep(0.5)  # the player starts in the background; the script puts it right after the assemble
        self.assertIn("review_player.py", (self.tmp / "calls.log").read_text().split())
        _, calls = self.run_v4(DRY="1")  # the call log keeps both runs: still the one player of the first
        self.assertEqual(calls.count("review_player.py"), 1)

    def test_a_dry_run_with_a_failed_check_opens_nothing(self):
        render, calls = self.run_v4(rc=1, DRY="1", FAIL_av_check="1")
        self.assertNotIn("DRY_OK x", render)
        self.assertNotIn("dry_run:pass", calls)

    def test_a_dry_run_that_cannot_be_recorded_fails(self):
        render, _ = self.run_v4(rc=1, DRY="1", FAIL_dry_pass="1")
        self.assertIn("FAILED dry_run pass x", render)

    def test_the_stages_of_a_run_are_timed_in_the_work_folder(self):  # Kamil 2026-11-10: a film's hours measured, not guessed
        self.run_v4(DRY="1")
        marks = [ln.split(" ", 1) for ln in (self.work / "timeline.log").read_text().splitlines()]
        self.assertEqual([m[1] for m in marks], ["run dry x", "gfx", "plan x", "beds x", "assemble x", "checks x",  # each check timed apart (2026-11-15: where the hours go)
                                                  "check av x", "check sync x", "check lips x", "check words_cut x", "check retake x",
                                                  "check words_sound x", "check music x", "end "])
        for when, _ in marks:
            self.assertRegex(when, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d")

    def test_no_other_film_before_the_long_is_accepted(self):  # Kamil 2026-11-10: the rest only after "jedz dalej"
        render, calls = self.run_v4(rc=1, FAIL_accept="1")
        self.assertIn("FAILED accept: x waits for the accepted long", render)
        self.assertEqual(calls, ["accept.py"])

    def test_the_long_itself_needs_no_acceptance(self):
        (self.work / "edl_long.json").write_text(json.dumps({"out_name": "film.mp4"}))
        render, calls = self.run_v4(film="long", FAIL_accept="1")
        self.assertIn("DONE long", render)
        self.assertNotIn("accept.py", calls)

    def test_film_check_off_is_logged_and_skipped(self):
        render, calls = self.run_v4(FILM_CHECK="off", FAIL_film_check="1")
        self.assertIn("WARN film_check off x", render)
        self.assertNotIn("film_check.py", calls)
        self.assertIn("DONE x", render)

    def test_film_check_off_skips_the_behind_phase_too(self):
        # review 2026-11-05 ops-1: the behind cut-out runs, its check (film_check --phase behind) does not
        (self.work / "gfx_specs.json").write_text(json.dumps([{"id": "b", "type": "behind", "dur": 3, "text": "x"}]))
        render, calls = self.run_v4(FILM_CHECK="off", FAIL_film_check="1")
        self.assertIn("behind.py", calls)
        self.assertNotIn("film_check.py", calls)
        self.assertIn("DONE x", render)


if __name__ == "__main__":
    unittest.main()
