"""chunks.py: stage 2 in time windows. Pure command building plus one real ffmpeg check that the windows joined give
the same frames as the single pass (lavfi sources, no recording needed)."""
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import chunks as C

CARD_IN = ["-threads", "2", "-thread_queue_size", "4"]


def card(at, f):
    return [*CARD_IN, "-itsoffset", f"{at:.3f}", "-i", f]


class Windows(unittest.TestCase):
    def test_short_film_is_one_window(self):
        self.assertEqual(C.windows(1800, 120), [(0, None)])

    def test_windows_cover_every_frame_once_and_the_last_runs_open(self):
        w = C.windows(30 * 1270, 120)  # 21 min 10 s
        self.assertEqual(w[0][0], 0)
        self.assertIsNone(w[-1][1])
        for (_a0, a1), (b0, _) in itertools.pairwise(w):
            self.assertEqual(a1, b0)

    def test_no_stub_window_at_the_end(self):
        w = C.windows(30 * 245, 120)  # 4 min 5 s: the 5 s rest joins the last window
        self.assertEqual(w, [(0, 3600), (3600, None)])


class OnScreen(unittest.TestCase):
    def test_overlap_rules(self):
        self.assertTrue(C.on_screen(100, 10, 105, 220))   # started before, still on
        self.assertTrue(C.on_screen(219, 5, 100, 220))    # starts inside
        self.assertFalse(C.on_screen(50, 10, 100, 220))   # over before the window
        self.assertFalse(C.on_screen(221, 5, 100, 220))   # starts after it
        self.assertTrue(C.on_screen(5000, 1, 100, None))  # last window runs to the end


class WindowArgs(unittest.TestCase):
    def setUp(self):
        self.inputs = ["-i", "rough.mkv", *card(10, "a.mov"), *card(300, "b.mov"), "-i", "pip.mkv"]
        b = 2 + len(card(10, "a.mov"))
        self.cards = [(2, 10.0, 5.0), (b, 300.0, 5.0)]
        self.aligned = [0, len(self.inputs) - 2]
        self.fc = ["[0:v]eq,tpad=stop_mode=clone:stop_duration=2[v0]", "[v0][1:v]overlay[v1]", "[v1][2:v]overlay[v2]"]

    def args(self, win):
        return C.window_args(self.inputs, self.cards, self.aligned, self.fc, win, "v2", ",tpad=stop_mode=clone:stop_duration=2",
                             ["-c:v", "libx264"], "out.mkv")

    def test_first_window_keeps_its_card_and_stands_in_the_other(self):
        a = self.args((0, 3600))
        self.assertIn("a.mov", a)
        self.assertNotIn("b.mov", a)
        self.assertEqual(a.count("-i"), 4)  # input numbers unchanged
        self.assertEqual(a[a.index("rough.mkv") - 5:a.index("rough.mkv")], ["-ss", "0.000000", "-t", "121.000000", "-i"])
        self.assertIn("-copyts", a)
        self.assertEqual(a[a.index("-frames:v") + 1], "3600")
        self.assertNotIn("tpad", a[a.index("-filter_complex") + 1])  # only the last window pads the tail

    def test_last_window_seeks_both_aligned_inputs_and_keeps_the_tail(self):
        a = self.args((7200, None))
        self.assertNotIn("a.mov", a)
        self.assertIn("b.mov", a)
        for f in ("rough.mkv", "pip.mkv"):
            self.assertEqual(a[a.index(f) - 3:a.index(f)], ["-ss", "240.000000", "-i"])
        self.assertIn("tpad", a[a.index("-filter_complex") + 1])
        self.assertNotIn("-frames:v", a)
        self.assertTrue(a[a.index("-filter_complex") + 1].endswith("[v2]setpts=PTS-STARTPTS[vwin]"))

    def test_aligned_index_must_point_at_an_input(self):
        with self.assertRaises(ValueError):
            C.window_args(self.inputs, [], [1], self.fc, (0, None), "v2", "", [], "o.mkv")

    def test_key_changes_when_an_input_file_is_made_again(self):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d)
        f = os.path.join(d, "card.mov"); Path(f).write_bytes(b"old")
        k = C.key(["-i", f, "o.mkv"])
        os.utime(f, ns=(1, 1)); Path(f).write_bytes(b"new!")  # same path, other picture (a correction round)
        self.assertNotEqual(C.key(["-i", f, "o.mkv"]), k)

    def test_key_ignores_the_output_path_only(self):
        self.assertEqual(C.key(["a", "b", "x.mkv"]), C.key(["a", "b", "y.mkv"]))
        self.assertNotEqual(C.key(["a", "c", "x.mkv"]), C.key(["a", "b", "x.mkv"]))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "no ffmpeg")
class SameFramesAsOnePass(unittest.TestCase):
    """8 s film, 3 cards (one across the window join), progress bar on t, windows of 3 s: the joined windows have the
    single pass's frame count and the same picture at sampled frames."""

    def test_windows_match_single_pass(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        run = lambda a: subprocess.run(a, check=True, capture_output=True)
        rough = os.path.join(d, "rough.mkv")
        run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=8", "-c:v", "libx264", "-preset",
             "ultrafast", "-g", "15", "-pix_fmt", "yuv420p", rough])
        cards = []
        for k, (at, dur, col) in enumerate([(1.0, 1.5, "red"), (2.6, 1.0, "blue"), (6.0, 1.0, "green")]):
            f = os.path.join(d, f"c{k}.mov")
            run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c={col}@0.6:s=320x180:r=30:d={dur}", "-vf", "format=yuva444p10le",
                 "-c:v", "prores_ks", "-profile:v", "4444", f])
            cards.append((at, dur, f))
        inputs, slots, fc, last = ["-i", rough], [], ["[0:v]eq=contrast=1.04,tpad=stop_mode=clone:stop_duration=0.5[v0]"], "v0"
        fc.append("color=c=white:s=320x8:r=30,format=rgba[pbar]")
        fc.append("[v0][pbar]overlay=x='-w+w*min(t/8,1)':y=H-8:shortest=1[vbar]"); last = "vbar"
        for k, (at, dur, f) in enumerate(cards):
            slots.append((len(inputs), at, dur)); inputs += card(at, f)
            fc.append(f"[{k + 1}:v]format=yuva444p10le[g{k}]"); fc.append(f"[{last}][g{k}]overlay=eof_action=pass:format=auto[o{k}]"); last = f"o{k}"
        enc = ["-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "yuv444p"]
        one = os.path.join(d, "one.mkv")
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-an", *enc, one])
        parts = []
        for i, w in enumerate(C.windows(240, 3.0)):
            p = os.path.join(d, f"w{i}.mkv")
            run(C.window_args(inputs, slots, [0], fc, w, last, ",tpad=stop_mode=clone:stop_duration=0.5", enc, p)); parts.append(p)
        lst = os.path.join(d, "l.txt"); Path(lst).write_text("".join(f"file '{p}'\n" for p in parts))
        joined = os.path.join(d, "joined.mkv")
        run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

        def frames(f):
            r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                "stream=nb_read_frames", "-of", "json", f], capture_output=True, text=True, check=True)
            return int(json.loads(r.stdout)["streams"][0]["nb_read_frames"])

        def pix(f, n):
            return subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout

        def diff(a, b):
            d = [abs(x - y) for x, y in zip(a, b, strict=True)]
            return max(d), sum(d) / len(d)

        self.assertEqual(frames(joined), frames(one))
        # the same picture up to colour-conversion rounding (measured: max 3, mean < 0.25 of 255)
        for n in (0, 40, 85, 89, 90, 91, 100, 185, 200, 239, frames(one) - 1):  # cards, the joins at 90 / 180, the tail
            mx, mean = diff(pix(joined, n), pix(one, n))
            self.assertLessEqual(mx, 4, f"frame {n} differs")
            self.assertLess(mean, 0.5, f"frame {n} differs")
        # control: testsrc2 moves every frame, so a window one frame late would fail the check above
        self.assertGreater(diff(pix(joined, 125), pix(one, 126))[1], 2.0)  # 4.2 s: no card over the moving source


if __name__ == "__main__":
    unittest.main()
