"""behind.py (text behind the speaker), run with matte/.venv/bin/python -m unittest matte/test_behind.py from ~/video-pipeline
(the panel suite runs it: panel/tests/test_behind.py). A fake matting model on a synthetic film whose every frame has its
own grey level, so the test sees WHICH film frame the model got for each card frame."""
import contextlib
import hashlib
import io
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

import numpy as np

PIPE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPE))
import behind

W, H = 64, 36


class FakeMatter:
    """the left half is "the person"; records the grey level of every frame it is given"""
    seen: ClassVar[list[int]] = []

    def __init__(self, ratio):
        FakeMatter.seen = []

    def __call__(self, rgb):
        FakeMatter.seen.append(round(float(rgb.mean())))
        p = np.zeros(rgb.shape[:2], np.float32)
        p[:, : rgb.shape[1] // 2] = 1
        return p


class GreyMatter(FakeMatter):
    """the whole frame is "person" as much as the frame is bright: card frame k's alpha tells which film frame it got"""

    def __call__(self, rgb):
        super().__call__(rgb)
        return np.full(rgb.shape[:2], float(rgb.mean()) / 255, np.float32)


class Crash(FakeMatter):
    def __call__(self, rgb):
        if len(FakeMatter.seen) == 12:
            raise RuntimeError("killed mid-way")
        return super().__call__(rgb)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
class BehindTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="behind-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        self.src = self.d / "src.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"nullsrc=s={W}x{H}:r=30:d=2,geq=lum='16+N*3':cb=128:cr=128",
                        "-c:v", "ffv1", str(self.src)], check=True)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.src), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        self.grey = [round(float(f.mean())) for f in np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)]  # source frame n
        (self.d / "gfx").mkdir()
        self.mov = self.d / "gfx" / "b.mov"
        self.front = self.d / "gfx" / "b.front.mov"
        self.card(1.0)
        self.edl = {"sources": {"A": str(self.src)}, "w": W, "h": H, "src_w": W, "src_h": H, "face": [0.5, 0.5], "seg_exact": True,
                    "segments": [{"src": "A", "in": 0.0, "out": 0.5, "zoom": 1.0}, {"src": "A", "in": 1.0, "out": 2.0, "zoom": 1.0}],
                    "overlays": [{"id": "b", "at": 0.3, "dur": 20 / 30}]}
        self.write_edl()
        self.spec = {"id": "b", "type": "float", "behind": {"edl": "edl.json"}}

    def card(self, a: float, frames: int = 20):  # what render.mjs writes
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=white@{a}:s={W}x{H}:r=30,format=rgba",
                        "-frames:v", str(frames), "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(self.mov)],
                       check=True)

    def write_edl(self):
        (self.d / "edl.json").write_text(json.dumps(self.edl))

    def run_once(self, matter=FakeMatter):
        return behind.process(self.spec, self.d / "gfx", self.d, matter_for=matter)

    def alpha(self) -> np.ndarray:
        return behind.card_frames(self.mov, (W, H))[..., 3]

    def test_the_person_is_cut_out_and_the_rest_of_the_card_stays(self):
        self.assertIn("cut out of 20 frames", self.run_once())
        a = self.alpha()
        self.assertEqual(len(a), 20)
        self.assertLessEqual(int(a[:, :, : W // 2].max()), 1)    # the speaker's side: see-through
        self.assertGreaterEqual(int(a[:, :, W // 2 :].min()), 254)  # elsewhere: the card as rendered
        self.assertTrue(self.front.exists())
        self.assertEqual(list((self.d / "gfx").glob("*.part*")), [])

    def test_each_card_frame_is_matched_with_the_film_frame_under_it(self):
        self.run_once()
        # card at 0.3 s = film frame 9; warm-up from frame 0 (1 s before, clipped); film frames 0..14 = source 0..14,
        # 15.. = source 30.. (second segment starts at 1.0 s); the model saw film frames 0..28 in order
        film = [*range(15), *range(30, 44)]
        self.assertEqual(len(FakeMatter.seen), 29)
        for got, n in zip(FakeMatter.seen, film, strict=True):
            self.assertAlmostEqual(got, self.grey[n], delta=1, msg=n)

    def test_each_card_frame_gets_the_matte_of_its_own_film_frame(self):
        self.run_once(GreyMatter)
        film = [*range(15), *range(30, 44)]
        for k, a in enumerate(self.alpha().mean(axis=(1, 2))):
            self.assertAlmostEqual(float(a), 255 - self.grey[film[9 + k]], delta=2, msg=k)

    def test_nothing_changed_nothing_redone(self):
        self.run_once()
        with mock.patch.object(FakeMatter, "__call__", side_effect=AssertionError("matted again")):
            self.assertIn("up to date", self.run_once())

    def test_a_changed_edl_window_or_setting_cuts_out_again_from_the_rendered_card(self):
        self.run_once()
        front = sha(self.front)
        self.edl["segments"][1]["in"] = 1.2
        self.write_edl()
        self.assertIn("cut out", self.run_once())
        self.assertEqual(sha(self.front), front)  # never the masked card
        self.assertAlmostEqual(FakeMatter.seen[15], self.grey[36], delta=1)
        self.spec["behind"]["ratio"] = 0.3
        self.assertIn("cut out", self.run_once())

    def test_a_newly_rendered_card_becomes_the_new_front(self):
        self.run_once()
        self.card(0.5)  # render.mjs wrote a new b.mov (spec changed, the old one moved aside)
        new = sha(self.mov)
        self.assertIn("cut out", self.run_once())
        self.assertEqual(sha(self.front), new)
        self.assertAlmostEqual(int(self.alpha()[0, 0, -1]), 128, delta=2)

    def test_a_run_killed_mid_way_leaves_the_card_whole_and_the_next_run_finishes(self):
        before = sha(self.mov)
        with self.assertRaises(RuntimeError):
            self.run_once(Crash)
        self.assertEqual(sha(self.mov), before)  # still the card as rendered: assemble / the player can use it
        self.assertEqual(list((self.d / "gfx").glob("*.part*")), [])
        self.assertIn("cut out", self.run_once())
        self.assertLessEqual(int(self.alpha()[:, :, : W // 2].max()), 1)

    def test_a_lost_card_is_rebuilt_from_its_front(self):
        self.run_once()
        self.mov.unlink()
        self.assertIn("cut out", self.run_once())
        self.assertLessEqual(int(self.alpha()[:, :, : W // 2].max()), 1)

    def test_a_masked_card_without_its_front_stops_with_what_to_do(self):
        self.run_once()
        self.front.unlink()
        self.edl["segments"][1]["in"] = 1.2
        self.write_edl()
        with self.assertRaisesRegex(behind.BehindError, "aside"):
            self.run_once()

    def test_a_card_longer_than_the_film_keeps_the_last_matte(self):
        self.edl["overlays"][0]["at"] = 1.3  # 39 film frames (15 + 30... ends at frame 45): the card's last 14 frames have no film
        self.write_edl()
        self.run_once(GreyMatter)
        a = self.alpha().mean(axis=(1, 2))
        last = 255 - self.grey[30 + 29]  # film frame 44 = source 59
        for k in range(6, 20):
            self.assertAlmostEqual(float(a[k]), last, delta=2, msg=k)

    def test_an_edl_not_built_yet_is_left_for_later(self):
        (self.d / "edl.json").unlink()
        self.assertIn("not built yet", self.run_once())
        self.assertFalse(self.front.exists())

    def test_a_card_not_in_the_edl_is_left_alone(self):
        self.edl["overlays"] = []
        self.write_edl()
        self.assertIn("not in", self.run_once())
        self.assertFalse(self.front.exists())

    def test_without_exact_segments_it_refuses(self):
        del self.edl["seg_exact"]
        self.write_edl()
        with self.assertRaisesRegex(behind.BehindError, "seg_exact"):
            self.run_once()

    def test_names_from_the_spec_never_leave_the_work_folder(self):
        for spec in ({"id": "../../x/victim", "behind": {"edl": "edl.json"}}, {"id": "b", "behind": {"edl": "../edl.json"}},
                     {"id": "b", "behind": {"edl": "/etc/passwd"}}):
            with self.subTest(spec=spec), self.assertRaises(behind.BehindError):
                behind.process(spec, self.d / "gfx", self.d, matter_for=FakeMatter)

    def cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(behind, "Matter", FakeMatter), mock.patch.object(behind, "MODEL", self.d / "none.onnx"), \
                mock.patch.object(behind, "low_priority"), mock.patch.object(behind.signal, "signal"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = behind.main(["behind.py", *args])
        return rc, out.getvalue(), err.getvalue()

    def test_cli_only_the_named_films_cards_and_a_failure_is_exit_1(self):
        specs = self.d / "gfx_specs.json"
        specs.write_text(json.dumps([self.spec, {"id": "other", "behind": {"edl": "edl_other.json"}}]))
        rc, out, _ = self.cli(str(specs), str(self.d / "gfx"), "--edl", "edl.json")  # no model file: only the fake can run
        self.assertEqual(rc, 0)
        self.assertTrue(self.front.exists())
        self.assertIn("other: for edl_other.json, not edl.json", out)  # a card skipped by --edl shows in render.log
        specs.write_text(json.dumps([{"id": "../x", "behind": {"edl": "edl.json"}}]))
        self.assertEqual(self.cli(str(specs), str(self.d / "gfx"))[0], 1)

    def test_cli_bad_specs_json_is_exit_1_with_the_reason(self):
        specs = self.d / "gfx_specs.json"
        specs.write_text("[{")
        rc, _, err = self.cli(str(specs), str(self.d / "gfx"))
        self.assertEqual(rc, 1)
        self.assertIn("FAILED behind", err)

    def test_before_the_final_edl_a_card_without_seg_exact_waits_for_run_v4(self):
        del self.edl["seg_exact"]
        self.write_edl()
        specs = self.d / "gfx_specs.json"
        specs.write_text(json.dumps([self.spec]))
        rc, out, _ = self.cli(str(specs), str(self.d / "gfx"))  # render.mjs: no --edl
        self.assertEqual((rc, "seg_exact yet" in out), (0, True))
        rc, _, err = self.cli(str(specs), str(self.d / "gfx"), "--edl", "edl.json")  # run_v4.sh: the final EDL must have it
        self.assertEqual((rc, "seg_exact" in err), (1, True))

    def test_a_symlinked_card_is_refused(self):
        victim = self.d / "victim.mov"
        self.mov.rename(victim)
        self.mov.symlink_to(victim)
        with self.assertRaisesRegex(behind.BehindError, "symlink"):
            self.run_once()

    def test_temp_files_get_fresh_names_so_a_planted_link_is_never_written_through(self):
        victim = self.d / "victim.txt"
        victim.write_text("keep")
        for name in ("b.front.part.mov", "b.behind.part.mov", ".b.part.mov"):
            (self.d / "gfx" / name).symlink_to(victim)
        self.assertIn("cut out", self.run_once())
        self.assertEqual(victim.read_text(), "keep")

    def test_a_card_not_the_films_size_is_refused(self):
        self.edl["w"] = W * 2
        self.write_edl()
        with self.assertRaisesRegex(behind.BehindError, "is not"):
            self.run_once()

    def test_before_the_final_edl_a_card_or_setup_fault_still_fails(self):
        self.spec["behind"]["ratio"] = 5  # a spec fault, not an EDL that run_v4.sh will rebuild
        specs = self.d / "gfx_specs.json"
        specs.write_text(json.dumps([self.spec]))
        rc, _, err = self.cli(str(specs), str(self.d / "gfx"))
        self.assertEqual((rc, "FAILED behind b" in err), (1, True))

    def test_a_card_longer_than_max_dur_is_refused(self):
        with mock.patch.object(behind, "MAX_DUR", 0.5), self.assertRaisesRegex(behind.BehindError, "at most"):
            self.run_once()

    def test_ratio_out_of_range_is_refused(self):
        for r in (0, 1.5, "0.2", True):
            self.spec["behind"]["ratio"] = r
            with self.subTest(ratio=r), self.assertRaisesRegex(behind.BehindError, "ratio"):
                self.run_once()

    def test_zoom_face_track_must_be_numbers(self):
        for k, v in (("zoom", "1,movie=x"), ("face", ["0.5", 0.5]), ("track", [[0, "x"]]), ("zoom", {"a": 1, "b": "2", "t0": 0, "t1": 1})):
            seg = dict(self.edl["segments"][1], **{k: v})
            self.edl["segments"] = [self.edl["segments"][0], seg]
            self.write_edl()
            with self.subTest(**{k: str(v)}), self.assertRaisesRegex(behind.BehindError, "numbers"):
                self.run_once()

    def test_a_change_in_assembles_framing_cuts_out_again(self):
        self.run_once()
        src = behind.framing_src() + "\n# vf_for changed"
        with mock.patch.object(behind, "framing_src", lambda: src):
            self.assertIn("cut out", self.run_once())

    def test_sigterm_mid_run_leaves_the_card_whole_and_no_temp_file(self):
        self.run_once()
        before = sha(self.mov)
        self.edl["segments"][1]["in"] = 1.2  # a new window: the next run cuts out again
        self.write_edl()
        specs = self.d / "gfx_specs.json"
        specs.write_text(json.dumps([self.spec]))
        runner = self.d / "runner.py"
        runner.write_text(f"""import sys, time
import numpy as np
sys.path.insert(0, {str(PIPE)!r})
import behind
class Slow:
    def __init__(self, ratio): pass
    def __call__(self, rgb):
        time.sleep(0.2)
        return np.zeros(rgb.shape[:2], np.float32)
behind.Matter = Slow
behind.MODEL = behind.Path("none.onnx")
behind.low_priority = lambda: None
sys.exit(behind.main(["behind.py", {str(specs)!r}, {str(self.d / "gfx")!r}, "--edl", "edl.json"]))
""")
        with subprocess.Popen([sys.executable, "-I", str(runner)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as pr:
            for _ in range(300):
                if list((self.d / "gfx").glob(".b.*.part.mov")):
                    break
                time.sleep(0.05)
            else:
                self.fail("no temp file appeared")
            time.sleep(0.5)
            pr.send_signal(signal.SIGTERM)
            _, err = pr.communicate(timeout=60)
        self.assertNotEqual(pr.returncode, 0)
        self.assertIn("SIGTERM", err)
        self.assertEqual(list((self.d / "gfx").glob(".*.part*")), [])
        self.assertEqual(sha(self.mov), before)

    def test_edl_wide_framing_values_must_be_numbers(self):
        for k, v in (("face", [0.5, "0.45)),drawbox=c=white"]), ("face_target_y", "0.4,movie=x"), ("src_w", "2560"),
                     ("vertical", "yes"), ("face", None), ("src_h", None), ("face_target_y", float("nan"))):
            with self.subTest(**{k: str(v)}):
                self.edl[k] = v
                self.write_edl()
                with self.assertRaisesRegex(behind.BehindError, "EDL"):
                    self.run_once()
                self.setUp()

    def test_before_the_final_edl_an_edl_that_does_not_fit_waits_for_run_v4(self):
        self.edl["w"] = W * 2
        self.write_edl()
        specs = self.d / "gfx_specs.json"
        specs.write_text(json.dumps([self.spec]))
        rc, out, _ = self.cli(str(specs), str(self.d / "gfx"))  # render.mjs: other films' graphics go on
        self.assertEqual((rc, "left for run_v4.sh" in out), (0, True))
        self.assertEqual(self.cli(str(specs), str(self.d / "gfx"), "--edl", "edl.json")[0], 1)

    def test_an_edl_of_the_wrong_shape_is_named_not_a_traceback(self):
        base = json.dumps(self.edl)
        for change in ({"segments": [{"src": "A", "in": "0", "out": 0.5}]}, {"segments": [{"src": "B", "in": 0, "out": 0.5}]},
                       {"overlays": [{"id": "b", "at": "0.3"}]}, {"overlays": ["b"]}, {"sources": {"A": 1}}, {"segments": None}):
            with self.subTest(change=change):
                self.edl = dict(json.loads(base), **change)
                self.write_edl()
                with self.assertRaisesRegex(behind.NotReady, "EDL"):
                    self.run_once()

    def test_any_other_fault_in_one_card_is_a_line_and_the_next_card_still_runs(self):
        specs = self.d / "gfx_specs.json"
        specs.write_text(json.dumps(["x", {"id": "x", "behind": "edl.json"}, {"id": "y", "behind": {"edl": 5}}, self.spec]))
        rc, out, err = self.cli(str(specs), str(self.d / "gfx"))
        self.assertEqual((rc, "cut out" in out, "Traceback" in err), (1, True, False))
        self.assertEqual(self.cli(str(specs), str(self.d / "gfx"), "--edl", "edl.json")[0], 0)  # not its film's cards: skipped
        real = behind.process
        with mock.patch.object(behind, "process", side_effect=[TypeError("a bug"), real(self.spec, self.d / "gfx", self.d)]):
            specs.write_text(json.dumps([self.spec, self.spec]))
            self.assertEqual(self.cli(str(specs), str(self.d / "gfx"))[0], 1)

    def test_the_front_copy_never_writes_through_a_link(self):
        victim = self.d / "victim.txt"
        victim.write_text("keep")
        link = self.d / "gfx" / ".b.link.part.mov"
        link.symlink_to(victim)
        with mock.patch.object(behind, "temp_in", return_value=link), self.assertRaises(OSError):
            self.run_once()
        self.assertEqual(victim.read_text(), "keep")

    def test_cut_out_cards_keep_the_usual_file_mode(self):
        self.run_once()
        umask = os.umask(0); os.umask(umask)
        for f in (self.mov, self.front):
            self.assertEqual(stat.S_IMODE(f.stat().st_mode), 0o666 & ~umask, f.name)

    def test_a_failed_front_copy_leaves_no_temp_file(self):
        with mock.patch.object(behind.shutil, "copyfileobj", side_effect=OSError("disk full")), self.assertRaises(OSError):
            self.run_once()
        self.assertEqual(list((self.d / "gfx").glob(".*.part*")), [])

    def test_temp_files_of_a_killed_run_are_swept_young_ones_kept(self):
        old, young = self.d / "gfx" / ".gone_card.old.part.mov", self.d / "gfx" / ".b.young.part.mov"  # any card's
        old.write_bytes(b"x"); young.write_bytes(b"x")
        t = time.time() - behind.STALE_PART - 60
        os.utime(old, (t, t))
        self.run_once()
        self.assertEqual((old.exists(), young.exists()), (False, True))

    def test_a_link_swapped_in_after_the_check_is_not_read(self):
        secret = self.d / "secret.txt"
        secret.write_text("private")
        real_open = behind.open_nofollow

        def swap_then_open(p):  # the peer wins the race: the card turns into a link between the check and the copy
            if p == self.mov:
                self.mov.unlink(); self.mov.symlink_to(secret)
            return real_open(p)
        with mock.patch.object(behind, "open_nofollow", swap_then_open), self.assertRaises(OSError):
            self.run_once()
        self.assertFalse(self.front.exists())
        with self.assertRaises(OSError):
            behind.sha(self.mov)

    def test_only_the_verified_model_file_is_loaded(self):
        bad = self.d / "model.onnx"
        bad.write_bytes(b"not the model")
        with mock.patch.object(behind, "MODEL", bad), self.assertRaisesRegex(behind.BehindError, "sha256"):
            behind.Matter(0.2)
        with mock.patch.object(behind, "MODEL", self.d / "none.onnx"), self.assertRaises(behind.BehindError):
            behind.Matter(0.2)



@unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
class FramingMatchesAssembleTest(unittest.TestCase):
    """film_frames == the frames assemble.py itself cuts (its rough.mkv), with a dynamic zoom, keyframes and a face"""

    def test_film_frames_are_assembles_frames(self):
        d = Path(tempfile.mkdtemp(prefix="behind-asm-"))
        self.addCleanup(shutil.rmtree, d, True)
        src = d / "src.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=3", "-f", "lavfi", "-i",
                        "sine=d=3", "-c:v", "ffv1", "-c:a", "pcm_s16le", str(src)], check=True)
        edl = {"sources": {"A": str(src)}, "w": 320, "h": 180, "src_w": 320, "src_h": 180, "face": [0.4, 0.45], "seg_exact": True,
               "out_name": "f.mp4", "overlays": [], "grade": "null", "audio": "anull",
               "segments": [{"src": "A", "in": 0.2, "out": 1.0, "zoom": {"a": 1.0, "b": 1.3, "t0": 0.1, "t1": 0.6}},
                            {"src": "A", "in": 1.5, "out": 2.4, "zoom": 1.2, "face": [0.6, 0.5]},
                            {"src": "A", "in": 2.4, "out": 2.9, "zoom": {"a": 1.1, "b": 1.1, "t0": 0, "t1": 0.5,
                                                                          "keys": [[0.0, 1.1], [0.3, 1.4]]}}]}
        (d / "edl.json").write_text(json.dumps(edl))
        subprocess.run([sys.executable, str(PIPE / "assemble.py"), str(d / "edl.json"), str(d / "out")], check=True,
                       capture_output=True, timeout=300)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(d / "out" / "rough.mkv"), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        ref = np.frombuffer(raw, np.uint8).reshape(-1, 180, 320, 3).astype(np.int16)
        n = sum(behind.seg_frames(edl))
        self.assertEqual(len(ref), n)
        got = np.stack(list(behind.film_frames(edl, 0, n, behind.framing(edl), (320, 180)))).astype(np.int16)
        err = np.abs(got - ref).mean(axis=(1, 2, 3))
        self.assertLess(float(err.max()), 4.0, err.round(1).tolist())  # x264 crf 12 in rough.mkv; a 1-frame or crop shift is > 10


class CutOutTest(unittest.TestCase):
    def test_alpha_times_not_person(self):
        rgba = np.full((1, 4, 4), 200, np.uint8)
        out = behind.cut_out(rgba, np.array([[0.0, 0.5, 1.0, 1.5]], np.float32))
        self.assertEqual(out[0, :, 3].tolist(), [200, 100, 0, 0])
        self.assertEqual(out[0, :, :3].tolist(), rgba[0, :, :3].tolist())
        self.assertEqual(behind.cut_out(rgba, None).tolist(), rgba.tolist())


if __name__ == "__main__":
    unittest.main()
