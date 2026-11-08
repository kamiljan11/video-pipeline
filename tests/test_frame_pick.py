"""frame_pick.py: no blurred frame, shut eyes or mid-word mouth on a thumbnail (Kamil 2026-11-08 "glupie miny wybierasz")."""
import unittest
from unittest import mock

import numpy as np

import frame_pick as fp


def m(sharp=100.0, eyes=60.0, dark=0.0, smile=1.0, still=1.0, off=0.0):
    return {"sharp": sharp, "eyes": eyes, "dark": dark, "smile": smile, "still": still, "off": off, "face_h": 0.4, "gray": None}


class FramePickTest(unittest.TestCase):
    def run_pick(self, measures):
        img = np.zeros((4, 4, 3), np.uint8)
        with mock.patch.object(fp, "frames", return_value=[(i / 10, img) for i in range(len(measures))]), \
             mock.patch.object(fp, "detector", return_value=object()), \
             mock.patch.object(fp, "measure", side_effect=[None if x is None else dict(x) for x in measures]):
            return fp.pick("v.mp4", 0, 1)

    def test_shut_eyes_and_blur_are_dropped(self):
        got = self.run_pick([m(), m(eyes=30), m(sharp=40), None])
        self.assertEqual([c.t for c in got], [0.0])

    def test_open_mouth_loses_to_a_closed_one(self):
        got = self.run_pick([m(dark=0.3), m(dark=0.0)])
        self.assertEqual(got[0].t, 0.1)
        self.assertLess(got[1].mouth, got[0].mouth)

    def test_motion_and_a_turned_head_lose(self):
        got = self.run_pick([m(still=0.4), m(off=0.3), m()])
        self.assertEqual(got[0].t, 0.2)

    def test_no_face_no_candidates(self):
        self.assertEqual(self.run_pick([None, None]), [])

    def test_top_keeps_candidates_apart(self):
        cs = [fp.Cand(t, 1 - i / 10, 1, 1, 1, 1, 1, {}) for i, t in enumerate((1.0, 1.1, 1.2, 2.0, 2.3, 3.0))]
        self.assertEqual([c.t for c in fp.top(cs, 3)], [1.0, 2.0, 3.0])

    def test_eye_box_contrast_tells_open_from_shut(self):
        det = mock.Mock()
        face = np.array([[0, 0, 200, 200, 70, 80, 130, 80, 100, 110, 75, 150, 125, 150, 0.9]], np.float32)
        det.detect.return_value = (1, face)
        img = np.full((240, 240, 3), 150, np.uint8)
        shut = fp.measure(img, None, det)
        img[78:83, 66:75] = 20; img[78:83, 126:135] = 20  # dark irises inside both eye boxes
        opened = fp.measure(img, None, det)
        assert shut and opened
        self.assertGreater(opened["eyes"], shut["eyes"])
        img[148:153, 85:115] = 10  # a dark open mouth between the corners
        talking = fp.measure(img, None, det)
        assert talking
        self.assertGreater(talking["dark"], opened["dark"])


if __name__ == "__main__":
    unittest.main()
