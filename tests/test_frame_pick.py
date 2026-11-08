"""frame_pick.py: no blurred frame, shut eyes or mid-word mouth on a thumbnail (Kamil 2026-11-08 "glupie miny wybierasz")."""
import importlib.util
import unittest
from unittest import mock

import numpy as np

import frame_pick as fp


def m(sharp=100.0, eyes=60.0, dark=0.0, smile=1.0, still=1.0, off=0.0):
    return {"sharp": sharp, "eyes": eyes, "dark": dark, "smile": smile, "still": still, "off": off, "face_h": 0.4, "gray": None}


def e(gaze_h=0.0, gaze_v=0.0, blink=0.15, pucker=0.0, jaw=0.0, lips_in=0.0, yaw=0.0, pitch=0.0, roll=0.0):
    return {"gaze_h": gaze_h, "gaze_v": gaze_v, "blink": blink, "pucker": pucker, "jaw": jaw, "lips_in": lips_in,
            "yaw": yaw, "pitch": pitch, "roll": roll}


class FramePickTest(unittest.TestCase):
    def run_pick(self, measures, exprs=None):
        img = np.zeros((4, 4, 3), np.uint8)
        exprs = list(exprs or [e() for _ in measures])
        with mock.patch.object(fp, "frames", return_value=[(i / 10, img) for i in range(len(measures))]), \
             mock.patch.object(fp, "detector", return_value=object()), \
             mock.patch.object(fp, "measure", side_effect=[None if x is None else dict(x) for x in measures]):
            return fp.pick("v.mp4", 0, 1, expr=lambda _img: exprs.pop(0))

    def test_shut_eyes_and_blur_are_dropped(self):
        got = self.run_pick([m(), m(eyes=30), m(sharp=40), None])
        self.assertEqual([c.t for c in got], [0.0])

    def test_open_mouth_loses_to_a_closed_one(self):
        got = self.run_pick([m(dark=0.3), m(dark=0.0)])
        self.assertEqual(got[0].t, 0.1)
        self.assertLess(got[1].mouth, got[0].mouth)

    def test_motion_and_a_turned_head_lose(self):
        got = self.run_pick([m(still=0.4), m(), m()], [e(), e(yaw=8), e()])
        self.assertEqual(got[0].t, 0.2)

    def test_a_turned_or_tilted_head_or_rolled_in_lips_is_no_candidate(self):  # s03 cover: 427.0 s 20 deg, 415.0 s lips in
        got = self.run_pick([m() for _ in range(5)], [e(yaw=20.2), e(pitch=-14), e(roll=-10), e(lips_in=0.93), e(yaw=8.7)])
        self.assertEqual([c.t for c in got], [0.4])

    def test_one_blurred_outlier_does_not_drop_every_sharp_frame(self):
        # s03 cover 2026-11-08: a frame in motion had the highest eye-box contrast; scaled to it no sharp frame was kept
        got = self.run_pick([m(eyes=200, sharp=40)] + [m() for _ in range(10)])
        self.assertTrue(got)
        self.assertNotIn(0.0, [c.t for c in got])

    def test_a_glance_aside_down_half_shut_eyes_or_a_pursed_mouth_is_no_candidate(self):
        # covers of film 2026-11-04 checked by eye: s03/s05/s14/s18 glance aside (gaze_h ~0.4), s06 eyes down and half shut,
        # s12 a pursed "o"; every one passed the YuNet measures (Kamil 2026-11-08 "glupie miny wybierasz")
        got = self.run_pick([m() for _ in range(6)], [e(gaze_h=0.44), e(gaze_h=-0.4), e(gaze_v=-0.77, blink=0.51),
                                                      e(blink=0.5), e(pucker=0.61), e()])
        self.assertEqual([c.t for c in got], [0.5])
        self.assertEqual([fp.odd_face(x) for x in (e(gaze_h=0.44), e(gaze_v=-0.5), e(gaze_v=0.5), e(blink=0.5), e(pucker=0.6),
                                                    e(lips_in=0.9), e(yaw=-15), e(roll=10), e())],
                         ["looks to the side", "looks down", "looks up", "half-shut eyes", "pursed mouth", "lips rolled in",
                          "head turned", "head tilted", ""])

    def test_straighter_gaze_and_a_closed_jaw_win(self):
        got = self.run_pick([m(), m(), m()], [e(gaze_h=0.2), e(jaw=0.35), e()])
        self.assertEqual(got[0].t, 0.2)
        by_t = {c.t: c for c in got}
        self.assertLess(by_t[0.0].look, by_t[0.2].look)  # a glance of 0.2 counts against "look"
        self.assertLess(by_t[0.1].mouth, by_t[0.2].mouth)  # an open jaw against "mouth"

    def test_a_face_mediapipe_does_not_find_is_skipped(self):
        self.assertEqual(self.run_pick([m()], [None]), [])

    def test_blendshapes_map_to_gaze_and_expression(self):
        names = ("eyeLookOutLeft", "eyeLookInLeft", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpLeft", "eyeLookUpRight",
                 "eyeLookDownLeft", "eyeLookDownRight", "eyeBlinkLeft", "eyeBlinkRight", "mouthPucker", "jawOpen")
        b = dict.fromkeys(names, 0.0) | {"eyeLookOutLeft": 0.46, "eyeLookInRight": 0.4, "eyeLookDownLeft": 0.8, "eyeLookDownRight": 0.76,
                                          "eyeBlinkLeft": 0.52, "eyeBlinkRight": 0.5, "mouthPucker": 0.61}
        x = fp.expression(b)
        self.assertAlmostEqual(x["gaze_h"], 0.43); self.assertAlmostEqual(x["gaze_v"], -0.78); self.assertAlmostEqual(x["blink"], 0.51)
        self.assertEqual(x["pucker"], 0.61); self.assertEqual(x["yaw"], 0.0)
        turned = np.array([[np.cos(0.35), 0, np.sin(0.35)], [0, 1, 0], [-np.sin(0.35), 0, np.cos(0.35)]])  # 20 deg about y
        self.assertAlmostEqual(abs(fp.expression(b, turned)["yaw"]), 20.05, places=1)

    def test_without_mediapipe_it_names_the_python_to_use(self):
        with mock.patch.dict("sys.modules", {"mediapipe": None}), self.assertRaisesRegex(RuntimeError, "vp-face-venv"):
            fp.expression_reader()

    @unittest.skipUnless(importlib.util.find_spec("mediapipe") and fp.LANDMARK_MODEL.is_file(), "run with the vp-face-venv python")
    def test_real_mediapipe_reads_a_frame(self):  # the real API (model sha, task options, detect) under VENV_PY
        read = fp.expression_reader()
        self.assertIsNone(read(np.full((480, 360, 3), 128, np.uint8)))  # no face: None, not a crash

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
