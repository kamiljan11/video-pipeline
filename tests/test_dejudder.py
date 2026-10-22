"""dejudder.py on synthetic frames (no ffmpeg, no camera): a square moving 8 px per frame, some frames repeated.

Run: cd ~/video-pipeline && .venv/bin/python -m unittest tests.test_dejudder
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dejudder  # after the path: the script directory is not a package

W, H = 320, 180


def frame(x: int) -> bytes:
    y = np.full((H, W), 40, np.uint8)
    y[60:120, x:x + 40] = 220
    return y.tobytes() + np.full(W * H // 2, 128, np.uint8).tobytes()


def square_x(buf: bytes) -> float:
    y = dejudder.planes(buf, W, H)[0][60:120].astype(float) - 40
    cols = y.sum(axis=0)
    return float((cols * np.arange(W)).sum() / cols.sum()) - 19.5  # left edge of the square


def run(xs: list[int]) -> tuple[list[bytes], dict[str, int]]:
    stats = {"fixed": 0, "stalls": 0}
    return list(dejudder.repaired(iter([frame(x) for x in xs]), W, H, stats)), stats


class RepairTest(unittest.TestCase):
    def test_a_repeated_frame_becomes_the_in_between_position(self):
        out, stats = run([0, 8, 16, 16, 32, 40])  # the camera skipped x=24, ffmpeg repeated x=16
        self.assertEqual(len(out), 6)  # timing kept: same frame count
        self.assertEqual(stats["fixed"], 1)
        self.assertAlmostEqual(square_x(out[3]), 24, delta=2)
        self.assertEqual(out[2], frame(16))  # real frames pass through untouched
        self.assertEqual(out[4], frame(32))

    def test_two_repeats_are_spread_evenly(self):
        out, stats = run([0, 8, 8, 8, 32, 40])
        self.assertEqual(stats["fixed"], 2)
        self.assertAlmostEqual(square_x(out[2]), 16, delta=2)
        self.assertAlmostEqual(square_x(out[3]), 24, delta=2)

    def test_a_stall_longer_than_max_run_is_left_alone(self):
        xs = [0, 8] + [8] * (dejudder.MAX_RUN + 1) + [48]
        out, stats = run(xs)
        self.assertEqual(stats, {"fixed": 0, "stalls": 1})
        self.assertEqual(out, [frame(x) for x in xs])

    def test_a_frozen_camera_is_streamed_not_buffered(self):
        def frozen():  # endless repeats after two real frames
            yield frame(0)
            while True:
                yield frame(8)
        stats = {"fixed": 0, "stalls": 0}
        out = dejudder.repaired(frozen(), W, H, stats)
        first = [next(out) for _ in range(dejudder.MAX_RUN + 10)]  # would never return if repeats were held
        self.assertEqual(first[1:], [frame(8)] * (dejudder.MAX_RUN + 9))
        self.assertEqual(stats["stalls"], 1)

    def test_repeats_at_the_end_and_a_still_picture_stay(self):
        out, stats = run([0, 8, 8])
        self.assertEqual(out, [frame(0), frame(8), frame(8)])  # no next frame to move towards
        self.assertEqual(stats["fixed"], 0)

    def test_real_motion_is_not_taken_for_a_repeat(self):
        small = [dejudder.small_luma(frame(x), W, H) for x in (0, 1)]
        self.assertFalse(dejudder.is_repeat(small[0], small[1]))  # even 1 px of motion is far above the threshold
        self.assertTrue(dejudder.is_repeat(small[0], small[0]))


def clip(path: Path, seconds: int = 1) -> None:
    """A tiny test recording: moving picture at 30 fps with every 5th frame repeated, plus a tone."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=24:d={seconds}",
                    "-f", "lavfi", "-i", f"sine=d={seconds}", "-r", "30", "-c:v", "libx264", "-qp", "0",
                    "-c:a", "aac", "-shortest", str(path)], check=True)


def run_main(args: list[str]) -> tuple[int, str]:
    err = io.StringIO()
    with redirect_stderr(err), redirect_stdout(io.StringIO()):
        rc = dejudder.main(args)
    return rc, err.getvalue()


class MainTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_usage_and_missing_input_are_named_errors(self):
        self.assertEqual(run_main([])[0], 2)
        self.assertEqual(run_main(["--scan"])[0], 2)
        rc, err = run_main(["--scan", str(self.tmp / "nope.mp4")])  # flag first works too
        self.assertEqual(rc, 1)
        self.assertIn("no such recording", err)

    def test_never_writes_over_the_recording(self):
        src = self.tmp / "take.part.mp4"
        clip(src)
        before = src.read_bytes()
        rc, err = run_main([str(src), str(self.tmp / "take.mp4")])  # its .part.mp4 would be the source itself
        self.assertEqual(rc, 1)
        self.assertIn("would overwrite", err)
        self.assertEqual(src.read_bytes(), before)

    def test_a_dying_encoder_leaves_no_partial_file(self):
        src, out = self.tmp / "take.mp4", self.tmp / "fixed.mp4"
        clip(src)
        part = out.with_suffix(".part.mp4")
        with mock.patch.object(dejudder, "encode_cmd", return_value=["sh", "-c", f"echo x > {part}; exit 3"]):
            rc, err = run_main([str(src), str(out)])
        self.assertEqual(rc, 1)
        self.assertIn("partial output removed", err)
        self.assertFalse(part.exists())
        self.assertFalse(out.exists())

    def test_any_failure_in_the_loop_ends_cleanly(self):
        src, out = self.tmp / "take.mp4", self.tmp / "fixed.mp4"
        clip(src)

        def broken(*_args):
            raise RuntimeError("cv2 says no")
            yield b""  # a generator, like repaired()
        with mock.patch.object(dejudder, "repaired", broken), \
                mock.patch.object(dejudder, "encode_cmd", return_value=["sh", "-c", "cat > /dev/null"]):
            err = io.StringIO()
            with redirect_stderr(err), self.assertRaisesRegex(RuntimeError, "cv2 says no"):
                dejudder.main([str(src), str(out)])  # used to hang on a decoder blocked on a full pipe
        self.assertIn("FAILED dejudder", err.getvalue())
        self.assertFalse(out.with_suffix(".part.mp4").exists())

    @unittest.skipUnless(os.path.exists(dejudder.RENDER_NODE), "no VAAPI device")
    def test_a_recording_without_sound_works(self):
        src, out = self.tmp / "mute.mp4", self.tmp / "fixed.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=30:d=1",
                        "-c:v", "libx264", str(src)], check=True)
        rc, err = run_main([str(src), str(out)])
        self.assertEqual(rc, 0, err)
        self.assertEqual(dejudder.packets(out), {"video": 30})

    @unittest.skipUnless(os.path.exists(dejudder.RENDER_NODE), "no VAAPI device")
    def test_output_keeps_frames_time_and_sound(self):
        src, out = self.tmp / "take.mp4", self.tmp / "fixed.mp4"
        clip(self.tmp / "plain.mp4", 2)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-itsoffset", "0.033", "-i", str(self.tmp / "plain.mp4"),
                        "-i", str(self.tmp / "plain.mp4"), "-map", "0:v", "-map", "1:a", "-c", "copy", str(src)], check=True)
        self.assertGreater(dejudder.av_offset(src), 0.02)  # video later than sound, like the recorder's takes
        rc, err = run_main([str(src), str(out)])
        self.assertEqual(rc, 0, err)

        def streams(f: Path) -> list[str]:
            return subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries",
                                   "stream=codec_type,nb_read_frames", "-of", "csv=p=0", str(f)],
                                  capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(streams(out)[0], streams(src)[0])  # same number of video frames
        self.assertIn("audio", " ".join(streams(out)))
        rc, _ = run_main(["--scan", str(out)])
        self.assertEqual(rc, 0)
        self.assertAlmostEqual(dejudder.av_offset(out), dejudder.av_offset(src), delta=0.002)  # sync kept


if __name__ == "__main__":
    unittest.main()
