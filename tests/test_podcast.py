"""podcast mode (two people, one wide camera, ADR-0031): podcast_faces.py, podcast.py reframe, build_edl/edl_guard keys and
the 9:16 "stack" render in assemble.py.

  python3 -m unittest tests.test_podcast
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from itertools import pairwise
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import edl_guard
import podcast
import podcast_faces as pf
import podcast_shots
import timeline

CFG = podcast_shots.load_cfg()
FACES = {"0.000-60.000": {"L": [0.20, 0.30, 0.08, 0.15], "R": [0.70, 0.32, 0.08, 0.15]}}


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def words_of(spec):
    w, s, t = [], [], 0.0
    for spk, dur in spec:
        for _ in range(round(dur / 0.5)):
            w.append((t, t + 0.5, "x")); s.append(spk); t += 0.5
    return w, s


class TwoFaces(unittest.TestCase):
    def test_sorted_left_right_by_centre(self):
        dets = np.array([[600, 100, 60, 80, 0.9], [100, 120, 70, 90, 0.9]], dtype=float)
        got = pf.two_faces(dets)
        self.assertLess(got["L"][0], got["R"][0])

    def test_only_the_two_largest_count(self):
        dets = np.array([[600, 100, 60, 80], [100, 120, 70, 90], [400, 400, 10, 10]], dtype=float)
        self.assertEqual(sorted(pf.two_faces(dets)), ["L", "R"])
        self.assertGreater(pf.two_faces(dets)["R"][0], 0.5)

    def test_one_face_goes_to_the_nearer_side(self):
        last = {"L": [0.2, 0.3, 0.1, 0.1], "R": [0.6, 0.3, 0.1, 0.1]}
        self.assertEqual(list(pf.two_faces(np.array([[560, 100, 60, 80]], float), last)), ["R"])
        self.assertEqual(list(pf.two_faces(np.array([[100, 100, 60, 80]], float))), ["L"])
        self.assertEqual(pf.two_faces(None), {})

    def test_mouth_motion_sees_the_moving_mouth(self):
        a = np.zeros((pf.H, pf.W), np.uint8); b = a.copy()
        box = [0.2, 0.3, 0.1, 0.2]; mx, my, mw, mh = pf.mouth_box(box)
        b[int(my * pf.H) + 1:int((my + mh) * pf.H), int(mx * pf.W) + 1:int((mx + mw) * pf.W)] = 200
        m = pf.motion(a, b, box)
        self.assertIsNotNone(m); self.assertGreater(m or 0.0, 20)
        self.assertEqual(pf.motion(a, b, [0.6, 0.3, 0.1, 0.2]), 0.0)


class WordSpeakers(unittest.TestCase):
    def test_louder_mouth_wins_after_normalising(self):
        # R's mouth always moves a little more (beard, closer seat): only a real difference counts
        samples = [[t / 10, 1.0 if t < 20 else 6.0, 2.0 if t >= 20 else 12.0] for t in range(40)]
        spk = pf.word_speakers([(0.0, 1.9, "a"), (2.0, 3.9, "b")], samples, 1.25)
        self.assertEqual(spk, ["R", "L"])

    def test_no_clear_winner_is_unknown(self):
        samples = [[t / 10, 1.0, 1.0] for t in range(20)]
        self.assertEqual(pf.word_speakers([(0.0, 1.9, "a")], samples, 1.25), ["?"])
        self.assertEqual(pf.word_speakers([(5.0, 6.0, "a")], samples, 1.25), ["?"])  # no sample inside the word

    def test_fix_overrides_a_stretch(self):
        w = [(0, 1, "a"), (1, 2, "b"), (2, 3, "c")]
        self.assertEqual(pf.apply_fix(w, ["L", "L", "L"], [[0.9, 2.2, "R"]]), ["L", "R", "L"])
        with self.assertRaises(SystemExit): pf.apply_fix(w, ["L"] * 3, [[0, 1, "X"]])


def edl(vertical=False, segs=((0.0, 30.0),), overlays=(), specs=None, tmp=None):
    E = {"sources": {"A": "rec.mp4"}, "segments": [{"src": "A", "in": a, "out": b, "zoom": {"a": 1.0, "b": 1.1, "t0": 0, "t1": 1},
                                                    "track": [[0, 0.5]]} for a, b in segs],
         "overlays": list(overlays), "vertical": vertical, "w": 1080 if vertical else 2560, "h": 1920 if vertical else 1440}
    if specs is not None:
        f = Path(str(tmp)) / "specs.json"; f.write_text(json.dumps(specs)); E["gfx_specs"] = str(f)
    return E


class Reframe(unittest.TestCase):
    def test_long_pieces_follow_the_speaker(self):
        w, s = words_of([("L", 10), ("R", 10), ("L", 10)])
        E, _, _ = podcast.reframe(edl(), s, w, FACES, CFG)
        shots = [p["shot"] for p in E["segments"]]
        self.assertEqual(shots, ["wide", "L", "R", "L"])
        first_l = E["segments"][1]
        self.assertEqual(first_l["zoom"]["a"], CFG["single_zoom"]); self.assertNotIn("track", first_l)
        self.assertAlmostEqual(first_l["face"][0], 0.24, places=3)
        wide = E["segments"][0]
        self.assertAlmostEqual(wide["face"][0], 0.49, places=3); self.assertEqual(wide["zoom"], CFG["wide_zoom"])
        self.assertTrue(all(edl_guard.segment_ok(p) for p in E["segments"]))

    def test_single_shots_drift_in_and_out_by_turns(self):  # Kamil 2026-11-22: play with the zooms on the speaker, gently
        w, s = words_of([("L", 10), ("R", 10), ("L", 10)])
        E, _, _ = podcast.reframe(edl(), s, w, FACES, CFG)
        singles = [p for p in E["segments"] if p["shot"] in ("L", "R")]
        z0 = CFG["single_zoom"]
        self.assertLess(singles[0]["zoom"]["a"], singles[0]["zoom"]["b"])  # push in
        self.assertGreater(singles[1]["zoom"]["a"], singles[1]["zoom"]["b"])  # pull out
        for p in singles:
            z = p["zoom"]; d = timeline.piece_len(p, False)
            self.assertEqual(min(z["a"], z["b"]), z0)  # never wider than the still single shot
            self.assertLessEqual(abs(z["b"] - z["a"]), CFG["single_drift"] + 1e-9)
            self.assertEqual((z["t0"], z["t1"]), (0.0, round(d, 3)))
        wide = [p for p in E["segments"] if p["shot"] == "wide"]
        self.assertTrue(all(p["zoom"] == CFG["wide_zoom"] for p in wide))
        self.assertTrue(all(edl_guard.segment_ok(p) for p in E["segments"]))

    def test_short_single_stays_still_and_move_grows_with_length(self):
        c = dict(CFG)
        self.assertEqual(podcast.single_drift(1.8, c["drift_min_s"] - 0.01, c, 0), 1.8)
        short = podcast.single_drift(1.8, 3.0, c, 0); long_ = podcast.single_drift(1.8, 60.0, c, 0)
        assert isinstance(short, dict) and isinstance(long_, dict)
        self.assertAlmostEqual(short["b"] - short["a"], round(c["drift_per_s"] * 3.0, 3), places=6)
        self.assertAlmostEqual(long_["b"] - long_["a"], c["single_drift"], places=6)

    def test_vertical_singles_keep_the_build_edl_zoom(self):  # short.punch: the punch-ins of the words stay in 9:16
        w, s = words_of([("L", 10), ("R", 10)])
        E0 = edl(vertical=True, segs=((0.0, 20.0),))
        E0["segments"][0]["zoom"] = {"a": 1.0, "b": 1.12, "t0": 12.0, "t1": 12.3}  # a punch in R's part
        E, _, _ = podcast.reframe(E0, s, w, FACES, CFG)
        singles = [p for p in E["segments"] if p["shot"] in ("L", "R")]
        self.assertEqual(singles[0]["zoom"], 1.0)  # the punch starts after L's piece ends: its start level
        z = singles[-1]["zoom"]; off = singles[-1]["in"]
        self.assertEqual((z["t0"], z["t1"]), (round(12.0 - off, 3), round(12.3 - off, 3)))
        self.assertTrue(all(not isinstance(p.get("zoom"), dict) or p["zoom"]["a"] >= 1 for p in E["segments"]))
        self.assertTrue(all(edl_guard.segment_ok(p) for p in E["segments"]))

    def test_long_single_keeps_a_word_punch_on_its_own_level(self):  # long.punch: emph punches survive the reframe
        w, s = words_of([("L", 10), ("R", 10), ("L", 10)])
        E0 = edl()
        E0["segments"][0]["zoom"] = {"a": 1.0, "b": 1.12, "t0": 14.0, "t1": 14.3}  # build_edl emph in R's part
        E, _, _ = podcast.reframe(E0, s, w, FACES, CFG)
        r = next(p for p in E["segments"] if p["shot"] == "R")
        z0 = CFG["single_zoom"]
        self.assertEqual((r["zoom"]["a"], r["zoom"]["b"]), (round(z0, 4), round(z0 * 1.12, 4)))
        self.assertEqual((r["zoom"]["t0"], r["zoom"]["t1"]), (round(14.0 - r["in"], 3), round(14.3 - r["in"], 3)))
        l1 = next(p for p in E["segments"] if p["shot"] == "L")
        self.assertEqual(l1["zoom"]["a"], z0)  # no punch there: the slow drift
        self.assertFalse(podcast.is_punch({"a": 1.0, "b": 1.05, "t0": 0.0, "t1": 9.0}))
        self.assertTrue(podcast.is_punch({"a": 1.0, "b": 1.0, "t0": 0.0, "t1": 9.0, "keys": [[0, 1.0], [2, 1.2]]}))

    def test_word_punches_go_on_their_piece_and_never_under_a_card(self):  # long.punch in podcast mode
        w, s = words_of([("L", 10), ("R", 10), ("L", 10)])
        E0 = edl()
        # build_edl podcast: film times; 13 s and 16 s in R's piece, 25 s in L's piece but a side card covers 24-30 s
        E0["word_punches"] = [{"t": 13.0, "amt": 0.11, "speed": 0.3}, {"t": 16.0, "amt": 0.2, "speed": 0.3},
                              {"t": 25.0, "amt": 0.11, "speed": 0.3}]
        E0["punch_off"] = [[24.0, 30.0]]
        E, _, rep = podcast.reframe(E0, s, w, FACES, CFG)
        r = next(p for p in E["segments"] if p["shot"] == "R")
        z0, t13 = CFG["single_zoom"], round(13.0 - r["in"], 3)
        self.assertEqual(r["zoom"]["keys"][:3], [[0.0, z0], [t13, z0], [round(t13 + 0.3, 3), round(z0 * 1.11, 4)]])
        self.assertEqual(r["zoom"]["keys"][-1], [round(16.0 - r["in"] + 0.3, 3), round(z0 * 1.2, 4)])
        self.assertEqual((rep["punches"], rep["punch_under_card"]), (2, 1))
        last = E["segments"][-1]
        self.assertFalse(isinstance(last["zoom"], dict) and last["zoom"].get("keys"))  # under the card: the slow drift only
        self.assertTrue(all(edl_guard.segment_ok(p) for p in E["segments"]))
        import film_check
        self.assertEqual(len([t for t in film_check.punches({"segments": [r]})]), 2)  # every keyed push in counts

    def test_a_card_later_in_the_piece_brings_the_shot_back_to_its_level(self):
        w, s = words_of([("L", 10), ("R", 10), ("L", 10)])
        E0 = edl()
        E0["word_punches"] = [{"t": 12.0, "amt": 0.2, "speed": 0.3}]
        E0["punch_off"] = [[16.0, 19.0]]  # a side card 4 s after the word, inside R's piece
        E, _, rep = podcast.reframe(E0, s, w, FACES, CFG)
        r = next(p for p in E["segments"] if p["shot"] == "R")
        z0, c = CFG["single_zoom"], round(16.0 - r["in"], 3)
        self.assertEqual(r["zoom"]["keys"][-2:], [[round(c - 0.034, 3), round(z0 * 1.2, 4)], [c, z0]])
        self.assertEqual(rep["punches"], 1)
        self.assertTrue(edl_guard.segment_ok(r))

    def test_one_word_punch_is_a_plain_move_and_none_keeps_the_level(self):
        self.assertEqual(podcast.word_punches(1.8, []), 1.8)
        self.assertEqual(podcast.word_punches(1.0, [{"t": 2.0, "amt": 0.2, "speed": 0.3}]), {"a": 1.0, "b": 1.2, "t0": 2.0, "t1": 2.3})
        cap = podcast.word_punches(1.8, [{"t": 2.0, "amt": 0.9, "speed": 0.3}])
        assert isinstance(cap, dict)
        self.assertEqual(cap["b"], round(1.8 * podcast.PUNCH_MAX, 4))

    def test_shift_zoom_moves_times_or_settles_on_a_level(self):
        z = {"a": 1.0, "b": 1.2, "t0": 5.0, "t1": 5.3}
        self.assertEqual(podcast.shift_zoom(z, 0.0, 10.0), z)
        self.assertEqual(podcast.shift_zoom(z, 6.0, 4.0), 1.2)  # over before the piece: its end level
        self.assertEqual(podcast.shift_zoom(z, 1.0, 3.0), 1.0)  # starts after the piece ends: its start level
        self.assertEqual(podcast.shift_zoom(z, 2.0, 8.0), {"a": 1.0, "b": 1.2, "t0": 3.0, "t1": 3.3})
        k = podcast.shift_zoom({"a": 1.0, "b": 1.2, "t0": 0.0, "t1": 1.0, "keys": [[0.0, 1.0], [4.0, 1.2]]}, 1.5, 5.0)
        assert isinstance(k, dict)
        self.assertEqual(k["keys"], [[-1.5, 1.0], [2.5, 1.2]])
        self.assertEqual(podcast.shift_zoom(1.1, 3.0, 2.0), 1.1)

    def test_no_stack_under_a_vertical_card(self):
        w, s = words_of([("L", 5), ("R", 1.5), ("L", 1.5), ("R", 1.5), ("L", 6)])
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        E, _, rep = podcast.reframe(edl(vertical=True, segs=((0.0, 15.5),), overlays=[{"at": 4.0, "dur": 8.0, "id": "k"}],
                                        specs={"k": {"type": "scene", "canvas": "v", "layout": "split"}}, tmp=tmp), s, w, FACES, CFG)
        self.assertFalse([p for p in E["segments"] if p["shot"] == "stack"])
        self.assertGreater(rep["stack_under_card"], 0)
        E2, _, _ = podcast.reframe(edl(vertical=True, segs=((0.0, 15.5),), overlays=[{"at": 4.0, "dur": 8.0, "id": "e"}],
                                       specs={"e": {"type": "end", "canvas": "v"}}, tmp=tmp), s, w, FACES, CFG)
        self.assertTrue([p for p in E2["segments"] if p["shot"] == "stack"])  # an end board does not count

    def test_split_keeps_the_frame_count(self):
        w, s = words_of([("L", 7.3), ("R", 9.1), ("L", 13.6)])
        E0 = edl(segs=((0.0, 12.345), (14.0, 30.0)))
        E, _, _ = podcast.reframe(E0, s, w, FACES, CFG)
        frames = lambda segs: sum(round((g["out"] - g["in"]) * 30) for g in segs)
        self.assertEqual(frames(E["segments"]), frames(E0["segments"]))
        for a, b in zip(E["segments"], E["segments"][1:]):
            if a["out"] < 12.345: self.assertEqual(a["out"], b["in"])  # inside the first piece: no gap, no overlap

    def test_side_card_over_wide_takes_the_speaker(self):
        w, s = words_of([("L", 10), ("R", 10)])
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        E, _, _ = podcast.reframe(edl(overlays=[{"at": 1.0, "dur": 2.0, "id": "k"}], specs={"k": {"type": "kw"}}, tmp=tmp), s, w, FACES, CFG)
        self.assertEqual(E["segments"][0]["shot"], "L")  # the opening wide would have the card over person R

    def test_vertical_fast_exchange_is_stacked(self):
        w, s = words_of([("L", 5), ("R", 1.5), ("L", 1.5), ("R", 1.5), ("L", 6)])
        E, _, _ = podcast.reframe(edl(vertical=True, segs=((0.0, 15.5),)), s, w, FACES, CFG)
        st = [p for p in E["segments"] if p["shot"] == "stack"]
        self.assertTrue(st)
        self.assertEqual(st[0]["stack"], [[0.24, 0.375], [0.74, 0.395]])
        self.assertTrue(all(p["zoom"] == 1.0 for p in st))  # a stack has its own panel zoom (stack_zoom)
        self.assertTrue(all(edl_guard.segment_ok(p) for p in E["segments"]))

    def test_no_faces_leaves_the_piece(self):
        w, s = words_of([("L", 10)])
        E, _, _ = podcast.reframe(edl(segs=((0.0, 10.0),)), s, w, {}, CFG)
        self.assertNotIn("shot", E["segments"][0])

    def test_no_speaker_stops(self):
        with self.assertRaises(SystemExit): podcast.reframe(edl(), ["?"], [(0, 1, "a")], FACES, CFG)


class ReviewFixes(unittest.TestCase):
    """pg-review 2026-11-22 (RUN pg-review-20261122-133203): film clock, pauses, frame grid, stale fields, one face"""
    def test_shots_run_on_film_time(self):
        # the film keeps only 600-640 s of the recording: it still opens wide
        w, s = words_of([("L", 640)])
        E, sh, _ = podcast.reframe(edl(segs=((600.0, 640.0),)), s, w, {"0.000-700.000": FACES["0.000-60.000"]}, CFG)
        self.assertEqual(sh[0][2], "wide"); self.assertEqual(sh[0][0], 0.0)
        self.assertEqual(E["segments"][0]["shot"], "wide")

    def test_shot_change_moves_to_a_pause(self):
        w = [(0.0, 3.0, "a"), (3.0, 6.0, "b"), (6.4, 9.0, "c"), (9.0, 12.0, "d"), (12.0, 15.0, "e")]
        tn = [[0.0, 6.2, "L"], [6.2, 15.0, "R"]]
        self.assertEqual(podcast.snap([[0.0, 6.0, "L"], [6.0, 15.0, "R"]], w, [])[0][1], 6.2)
        self.assertTrue(tn)

    def test_split_never_changes_the_frame_count(self):
        import random
        rnd = random.Random(7)
        for _ in range(3000):
            a = round(rnd.uniform(0, 100), 3); b = a + rnd.uniform(1, 40)
            seg = {"in": a, "out": b}
            shots = [[0, 1, "L"]] + [[rnd.uniform(0, b - a), 0, "R"] for _ in range(rnd.randint(1, 4))]
            shots = [shots[0]] + sorted(shots[1:])
            pts = podcast.split_points(seg, 0.0, shots)
            bounds = [a, *pts, b]
            total = sum(podcast.timeline.piece_frames({"in": x, "out": y}) for x, y in pairwise(bounds))
            self.assertEqual(total, podcast.timeline.piece_frames(seg), (seg, pts))

    def test_rerun_drops_an_old_stack(self):
        p = podcast.frame_piece({"in": 0, "out": 1, "stack": [[0.2, 0.4], [0.7, 0.4]], "shot": "stack"}, "L", "L",
                                {"L": [0.2, 0.3, 0.1, 0.1], "R": [0.7, 0.3, 0.1, 0.1]}, CFG, True)
        self.assertNotIn("stack", p); self.assertEqual(p["shot"], "L")

    def test_one_face_never_stacks_the_same_person_twice(self):
        p = podcast.frame_piece({"in": 0, "out": 1}, "stack", "L", {"R": [0.7, 0.3, 0.1, 0.1]}, CFG, True)
        self.assertEqual(p["shot"], "R"); self.assertNotIn("stack", p)

    def test_no_face_is_counted(self):
        w, s = words_of([("L", 10)])
        E, _, rep = podcast.reframe(edl(segs=((0.0, 10.0),)), s, w, {}, CFG)
        self.assertGreater(rep["no_face"], 0)
        self.assertEqual(rep["no_face"], len(E["segments"]))  # every piece kept as it was

    def test_last_switch_of_an_exchange_is_stacked(self):
        sh = podcast_shots.short_shots([[0, 5, "L"], [5, 6, "R"], [6, 7, "L"], [7, 20, "R"]], CFG)
        st = [x for x in sh if x[2] == "stack"]
        self.assertEqual(st[0][0], 5); self.assertGreater(st[0][1], 7)  # the stack holds hold_s into R's answer
        self.assertEqual(sh[-1][2], "R")

    def test_cross_key_rules(self):
        with self.assertRaises(SystemExit): podcast_shots.load_cfg({"single_max_s": 3, "cutaway_s": 2.5})
        with self.assertRaises(SystemExit): podcast_shots.load_cfg({"stack_zoom": 0.5})

    def test_fix_rows_are_checked_with_their_number(self):
        w = [(0, 1, "a")]
        for bad in ([["0", 1, "L"]], [[2, 1, "L"]]):
            with self.assertRaises(SystemExit) as cm: pf.apply_fix(w, ["L"], bad)
            self.assertIn("row 1", str(cm.exception))

    def test_still_mouth_side_is_not_taken_for_unseen(self):
        samples = [[t / 10, 0.0 if t != 5 else 4.0, 3.0] for t in range(30)]  # L mouth still (median 0), R talking
        self.assertEqual(pf.word_speakers([(1.0, 2.0, "a")], samples, 1.25), ["R"])

    def test_failed_ffmpeg_stops_instead_of_half_samples(self):
        with self.assertRaises(SystemExit) as cm: list(pf.frames("/nonexistent/x.mp4", 0, 1.0, 10))
        self.assertIn("ffmpeg failed", str(cm.exception))

    def test_hung_ffmpeg_is_killed_with_a_named_error(self):
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp, True)
        fake = tmp / "ffmpeg"; fake.write_text("#!/bin/sh\nexec sleep 30\n"); fake.chmod(0o755)
        old_path, old_stall = os.environ["PATH"], pf.STALL_S
        os.environ["PATH"] = f"{tmp}:{old_path}"; pf.STALL_S = 0.5
        try:
            with self.assertRaises(SystemExit) as cm: list(pf.frames("x.mp4", 0, 1.0, 10))
        finally:
            os.environ["PATH"], pf.STALL_S = old_path, old_stall
        self.assertIn("gave no frame", str(cm.exception))

    def test_cache_key_follows_word_times(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, True)
        f = Path(tmp) / "r.mp4"; f.write_bytes(b"x")
        k1 = podcast.cache_key(str(f), [[0, 1]], [(0.0, 0.5, "a")], CFG)
        self.assertNotEqual(k1, podcast.cache_key(str(f), [[0, 1]], [(0.1, 0.5, "a")], CFG))

    def test_guard_runs_before_the_source_is_opened(self):
        tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "edl.json").write_text(json.dumps({"podcast": True, "sources": {"A": "http://127.0.0.1:9/x.m3u8"},
                                                  "segments": [{"src": "A", "in": 0, "out": 1}]}))
        r = subprocess.run([sys.executable, str(ROOT / "podcast.py"), str(tmp / "edl.json")], capture_output=True, text=True, check=False)
        self.assertNotEqual(r.returncode, 0); self.assertIn("EDL refused", r.stderr)

    def test_empty_podcast_object_still_means_podcast(self):
        src = (ROOT / "face_track.py").read_text()
        self.assertIn('"podcast" in E and E["podcast"] is not False', src)


class Guard(unittest.TestCase):
    def test_stack_must_be_two_number_pairs(self):
        self.assertTrue(edl_guard.segment_ok({"stack": [[0.2, 0.4], [0.7, 0.4]]}))
        for bad in ([[0.2, 0.4]], [["0.2;x", 0.4], [0.7, 0.4]], "L"):
            self.assertFalse(edl_guard.segment_ok({"stack": bad}), bad)

    def test_stack_zoom_number(self):
        base = {"sources": {"A": "/x.mp4"}, "segments": [{"src": "A", "in": 0, "out": 1}]}
        self.assertTrue(edl_guard.framing_ok({**base, "stack_zoom": 1.8}))
        self.assertFalse(edl_guard.framing_ok({**base, "stack_zoom": "2,crop=1"}))
        self.assertFalse(edl_guard.framing_ok({**base, "stack_zoom": 0.5}))


class BuildEdl(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="podcast-edl-")); self.addCleanup(shutil.rmtree, self.d, True)
        (self.d / "rec.cw.json").write_text(json.dumps({"transcription": [
            {"offsets": {"from": 1000, "to": 1500}, "text": " a"}, {"offsets": {"from": 1600, "to": 2900}, "text": " b"}]}))
        (self.d / "rec.sil").write_text("silence_start: 0\nsilence_end: 1.0\nsilence_start: 3.0\nsilence_end: 6\n")

    def build(self, **extra):
        plan = {"words": "rec.cw.json", "sil": "rec.sil", "src": "rec.mp4", "keeps": [[0, 1]], "edl_out": "edl.json", **extra}
        (self.d / "plan.json").write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(ROOT / "build_edl.py"), "plan.json"], cwd=self.d, capture_output=True, text=True, check=False)

    def test_podcast_key_and_words_reach_the_edl(self):
        r = self.build(podcast={"hold_s": 3, "stack_zoom": 2.0})
        self.assertEqual(r.returncode, 0, r.stderr)
        E = json.loads((self.d / "edl.json").read_text())
        self.assertEqual(E["podcast"], {"hold_s": 3, "stack_zoom": 2.0}); self.assertEqual(E["words"], "rec.cw.json")
        self.assertEqual(E["stack_zoom"], 2.0)

    def test_without_the_key_nothing_changes(self):
        self.assertEqual(self.build().returncode, 0)
        E = json.loads((self.d / "edl.json").read_text())
        self.assertNotIn("podcast", E); self.assertNotIn("words", E)

    def test_vertical_captions_sit_on_the_seam(self):
        r = self.build(podcast=True, vertical=True, ass_out="subs.ass")
        self.assertEqual(r.returncode, 0, r.stderr)
        cap = next(x for x in (self.d / "subs.ass").read_text().splitlines() if x.startswith("Style: Cap,"))
        self.assertEqual(cap.split(",")[21], "900")
        r = self.build(podcast=True, vertical=True, ass_out="subs.ass", caption_v=700)  # the plan's own value wins
        cap = next(x for x in (self.d / "subs.ass").read_text().splitlines() if x.startswith("Style: Cap,"))
        self.assertEqual(cap.split(",")[21], "700")

    def test_false_means_off_like_face_track(self):
        r = self.build(podcast=False, vertical=True, ass_out="subs.ass")
        self.assertEqual(r.returncode, 0, r.stderr)
        E = json.loads((self.d / "edl.json").read_text())
        self.assertNotIn("words", E)
        cap = next(x for x in (self.d / "subs.ass").read_text().splitlines() if x.startswith("Style: Cap,"))
        self.assertNotEqual(cap.split(",")[21], "900")

    def test_bad_value_is_a_named_error(self):
        r = self.build(podcast="yes")
        self.assertNotEqual(r.returncode, 0); self.assertIn("podcast:", r.stderr)


class StackRender(unittest.TestCase):
    """a red person on the left, a green one on the right: the stack shows red on top and green below"""
    def test_stack_puts_left_on_top(self):
        tmp = Path(tempfile.mkdtemp(prefix="stack-")); self.addCleanup(shutil.rmtree, tmp, True)
        src = tmp / "src.mp4"
        run("-f", "lavfi", "-i", "color=c=0x202020:s=1280x720:r=30:d=1", "-f", "lavfi", "-i", "sine=f=220:d=1",
            "-vf", "drawbox=x=230:y=250:w=100:h=200:color=red:t=fill,drawbox=x=900:y=250:w=100:h=200:color=green:t=fill",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src))
        E = {"sources": {"A": str(src)}, "w": 360, "h": 640, "src_w": 1280, "src_h": 720, "vertical": True, "seg_exact": True,
             "stack_zoom": 1.5, "out_name": "final.mp4", "face": [0.5, 0.45],
             "segments": [{"src": "A", "in": 0.0, "out": 1.0, "zoom": 1.0, "face": [0.22, 0.48], "stack": [[0.22, 0.48], [0.74, 0.48]]}]}
        (tmp / "edl.json").write_text(json.dumps(E))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(tmp / "edl.json"), str(tmp)], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        out = tmp / "final.mp4"
        wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(out)],
                            capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(wh, "360,640")
        def px(y):
            return subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(out), "-frames:v", "1", "-vf", f"format=rgb24,crop=1:1:180:{y}",
                                   "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
        top, bottom = px(160), px(480)
        self.assertGreater(top[0], 150, list(top)); self.assertLess(top[1], 90, list(top))
        self.assertGreater(bottom[1], 90, list(bottom)); self.assertLess(bottom[0], 90, list(bottom))


if __name__ == "__main__":
    unittest.main()
