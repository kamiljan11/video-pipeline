"""timeline: film times of seg_exact pieces are whole frames (film 2026-11-04: cards up to 287 ms off the words)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import timeline as T

SEGS = [{"in": 0.0, "out": 1.01}, {"in": 5.0, "out": 6.02}, {"in": 9.0, "out": 9.5}]


class TimelineTest(unittest.TestCase):
    def test_exact_pieces_last_whole_frames(self):
        self.assertEqual([T.piece_frames(s) for s in SEGS], [30, 31, 15])
        self.assertAlmostEqual(T.piece_len(SEGS[1], True), 31 / 30)
        self.assertAlmostEqual(T.piece_len(SEGS[1], False), 1.02)

    def test_starts_and_total_add_the_film_lengths(self):
        self.assertEqual([round(x, 4) for x in T.starts(SEGS, True)], [0.0, 1.0, round(61 / 30, 4)])
        self.assertAlmostEqual(T.total(SEGS, True), 76 / 30)
        self.assertAlmostEqual(T.total(SEGS, False), 2.53)

    def test_src2out_maps_inside_between_and_after_pieces(self):
        self.assertAlmostEqual(T.src2out(5.5, SEGS, True), 1.0 + 0.5)  # inside piece 2
        self.assertAlmostEqual(T.src2out(3.0, SEGS, True), 1.0)  # in a cut gap: the next piece start
        self.assertAlmostEqual(T.src2out(1.01, SEGS, True), 1.0)  # past the frame-rounded end: clamped to the piece
        self.assertAlmostEqual(T.src2out(99, SEGS, True), 76 / 30)
        self.assertAlmostEqual(T.src2out(5.5, SEGS, False), 1.01 + 0.5)


if __name__ == "__main__":
    unittest.main()


class FilmCheckUsesTimelineTest(unittest.TestCase):  # film_check measured with raw piece lengths (up to 287 ms off on 2026-11-04)
    def test_film_times_follow_whole_frame_pieces(self):
        import film_check
        segs = [{"in": 0.0, "out": 1.016, "zoom": 1.0}, {"in": 2.0, "out": 3.016, "zoom": {"a": 1.0, "b": 1.2, "t0": 0.5}},
                {"in": 4.0, "out": 5.0, "zoom": 1.3}]
        edl = {"segments": segs, "seg_exact": True}
        self.assertAlmostEqual(film_check.body_len(edl), T.total(segs, True))
        self.assertAlmostEqual(film_check.punches(edl)[0], 1.5)  # 1.016 s = 30 frames
        self.assertAlmostEqual(film_check.zoom_steps(edl)[0], 2.0)
        self.assertAlmostEqual(film_check.src2out(segs, 4.5, True), 2.5)
        self.assertAlmostEqual(film_check.body_len({"segments": segs}), 3.032)
