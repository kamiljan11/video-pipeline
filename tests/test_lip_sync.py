"""lips and voice of a finished film stay together (Kamil 2026-11-09 "dalej long ma opoznienie i to jeszcze wieksze").

Film 2026-11-04: the voice 40 ms late (afftdn + limiter look-ahead) and the picture up to 33 ms early (pieces cut off the
recording's frame grid, video start 0.033 s). The end-to-end test renders a recording made of flashes and beeps at the
same instants, laid out like the camera file, through assemble.py and measures it with lip_check.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import av_latency
import edl_guard
import lip_check
import timeline

PATTERN = "lt(mod({t},0.43),0.17)+0.6*lt(mod({t},0.31),0.09)"  # two periods: no lag repeats inside the search window


class SnapInTest(unittest.TestCase):
    def test_seek_lands_just_before_the_nearest_frame_of_the_recording(self):
        v0 = 0.033008
        for t in (5.333, 5.35, 5.37, 0.04):
            s = timeline.snap_in(t, v0)
            k = (s + 0.0005 - v0) * 30
            self.assertAlmostEqual(k, round(k), places=4)  # on the grid
            self.assertLessEqual(abs(s + 0.0005 - t), 1 / 60 + 1e-6)  # never more than half a frame away
        self.assertEqual(timeline.snap_in(0.0, 0.0), 0.0)
        self.assertAlmostEqual(timeline.snap_in(0.01, v0), v0 - 0.0005)  # before the first frame: the first frame


@unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
class ChainLatencyTest(unittest.TestCase):
    def test_measured_delay(self):
        self.assertEqual(av_latency.chain_ms("anull"), 0.0)
        self.assertAlmostEqual(av_latency.chain_ms("adelay=37"), 37.0, delta=1.0)
        self.assertAlmostEqual(av_latency.chain_ms("alimiter=limit=0.79:level=false"), 5.0, delta=1.0)
        self.assertEqual(av_latency.chain_ms("alimiter=limit=0.79:level=false:latency=1"), 0.0)
        with self.assertRaises(ValueError):  # longer than the search: never a silent 200 ms trim
            av_latency.chain_ms("adelay=300", max_ms=200)


class PiecesTest(unittest.TestCase):
    """2026-11-14: cards over 1073 of the long's 1086 s left lip_check 0 pieces, OK without a measurement"""

    def edl(self, overlays):
        segs = [{"src": 0, "in": 10.0 * k, "out": 10.0 * k + 3.0} for k in range(6)]  # 6 pieces of 3 s, film 0-18 s
        return {"segments": segs, "overlays": overlays}

    def test_free_pieces_come_first(self):
        e = self.edl([{"at": 0.0, "dur": 6.0}])  # cards over the first two pieces, four free
        self.assertEqual([i for i, _ in lip_check.pieces(e)], [2, 3, 4, 5])

    def test_a_film_all_under_cards_is_measured_under_them(self):
        e = self.edl([{"at": 0.0, "dur": 18.0}])
        self.assertEqual([i for i, _ in lip_check.pieces(e)], [0, 1, 2, 3, 4, 5])

    def test_too_few_free_pieces_take_the_covered_ones_too(self):
        e = self.edl([{"at": 0.0, "dur": 12.0}])  # two free pieces < MIN_PIECES
        self.assertEqual([i for i, _ in lip_check.pieces(e)], [0, 1, 2, 3, 4, 5])

    def test_min_pieces_free_ones_are_enough(self):
        e = self.edl([{"at": 0.0, "dur": 9.0}])  # three free pieces = MIN_PIECES
        self.assertEqual([i for i, _ in lip_check.pieces(e)], [3, 4, 5])

    def test_no_piece_long_enough_gives_nothing(self):
        e = {"segments": [{"src": 0, "in": 0.0, "out": 1.5}] * 4, "overlays": []}
        self.assertEqual(lip_check.pieces(e), [])

    def test_covered_pieces_that_do_not_match_fail(self):  # measured under cards, never matched = not measurable
        rows = [{"t": 1.0, "picture_ms": 0.0, "r_picture": 0.3, "sound_ms": 0.0, "r_sound": 0.95, "desync_ms": 0.0}] * 6
        self.assertIn("not measurable", lip_check.judge(rows, 45, 20)[0])


class JudgeTest(unittest.TestCase):
    def row(self, d, r=0.95):
        return {"t": 1.0, "picture_ms": 0.0, "r_picture": r, "sound_ms": d, "r_sound": r, "desync_ms": d}

    def test_late_voice_and_too_few_pieces_are_problems(self):
        self.assertEqual(lip_check.judge([self.row(5), self.row(-8), self.row(10)], 45, 20), [])
        self.assertTrue(any("median" in p for p in lip_check.judge([self.row(40)] * 3, 45, 20)))
        self.assertTrue(any("73 ms" in p for p in lip_check.judge([self.row(0), self.row(0), self.row(73)], 45, 20)))
        self.assertIn("not measurable", lip_check.judge([self.row(0, r=0.3)], 45, 20)[0])
        self.assertEqual(lip_check.judge([self.row(5), self.row(0, r=0.3)], 45, 20), [])  # a short: one piece decides
        self.assertTrue(lip_check.judge([self.row(47)], 45, 20))
        self.assertEqual(lip_check.judge([], 45, 20), [])  # an all-card short: nothing to compare, WARN in main, no FAIL


@unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
class EndToEndTest(unittest.TestCase):
    def test_finished_film_keeps_lips_and_voice_together(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        src = d / "rec.mp4"
        lum = "128+70*(" + PATTERN.format(t="T") + ")"
        snd = "0.3*sin(2*PI*300*t)*(" + PATTERN.format(t="t") + ")"
        # the picture of time T at pts T, the first frame dropped so the video starts at 1/30 s (as the camera file)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=30:d=9",
                        "-f", "lavfi", "-i", f"aevalsrc='{snd}':s=48000:d=9",
                        "-filter_complex", f"[0:v]geq=lum='{lum}':cb=128:cr=128,trim=start_frame=1[v]",
                        "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(src)], check=True)
        v0 = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=start_time",
                                   "-of", "csv=p=0", str(src)], capture_output=True, text=True, check=True).stdout)
        self.assertGreater(v0, 0.02)  # the layout under test: video after the sound
        edl = {"sources": {"A": str(src)}, "w": 320, "h": 180, "src_w": 320, "src_h": 180, "out_name": "final.mp4",
               "seg_exact": True, "segments": [{"src": "A", "in": 0.51, "out": 3.27}, {"src": "A", "in": 4.02, "out": 7.41}],
               "audio": "afftdn=nf=-25:tn=1,alimiter=limit=0.79:level=false"}
        self.assertEqual(edl_guard.problems(edl), [])
        (d / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(d / "edl.json"), str(d)],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        rows = lip_check.measure(edl, str(d / "final.mp4"))
        good = [x for x in rows if x["r_picture"] >= lip_check.R_MIN and x["r_sound"] >= lip_check.R_MIN]
        self.assertEqual(len(good), 2, rows)
        for x in good:
            self.assertLessEqual(abs(x["desync_ms"]), 12, rows)
        # the same film with the voice 40 ms late (the 2026-11-04 fault): the gate sees it
        late = d / "late.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(d / "final.mp4"), "-af", "adelay=40:all=1",
                        "-c:v", "copy", "-c:a", "aac", str(late)], check=True)
        rows = [x for x in lip_check.measure(edl, str(late)) if x["r_picture"] >= lip_check.R_MIN and x["r_sound"] >= lip_check.R_MIN]
        self.assertEqual(len(rows), 2, rows)
        for x in rows:
            self.assertAlmostEqual(x["desync_ms"], 40, delta=12, msg=rows)


if __name__ == "__main__":
    unittest.main()
