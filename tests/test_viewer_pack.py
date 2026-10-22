"""viewer_pack.py: what the viewer reviewer gets (time mapping, windows, on-screen list, a real tiny pack).

Run: cd ~/video-pipeline && .venv/bin/python -m unittest tests.test_viewer_pack
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import viewer_pack as vp  # after the path: the script directory is not a package


def word(text: str, a: float, b: float) -> dict:
    return {"text": f" {text}", "offsets": {"from": int(a * 1000), "to": int(b * 1000)}}


class MappingTest(unittest.TestCase):
    def test_words_land_at_film_time_and_cut_words_vanish(self):
        words = [word("raz", 1.0, 1.4), word("wycięte", 3.0, 3.5), word("dwa", 5.0, 5.4)]
        segs = [{"in": 0.9, "out": 2.0}, {"in": 4.9, "out": 6.0}]
        self.assertEqual([(round(t, 2), w) for t, w in vp.film_words(words, segs)], [(0.1, "raz"), (1.2, "dwa")])

    def test_a_word_started_just_before_the_cut_is_still_heard(self):
        words = [word("95%", 3.60, 4.10)]
        segs = [{"in": 3.654, "out": 9.0}]
        self.assertEqual([w for _, w in vp.film_words(words, segs)], ["95%"])

    def test_the_next_word_grazed_by_the_cut_is_not_heard(self):
        words = [word("firmę.", 73.2, 73.815), word("A", 73.815, 74.0)]
        segs = [{"in": 70.0, "out": 73.865}]  # the film ends 50 ms into "A": nobody hears it (checked by ASR)
        self.assertEqual([w for _, w in vp.film_words(words, segs)], ["firmę."])

    def test_a_word_across_two_segments_counts_once(self):
        words = [word("długie", 1.8, 2.4)]
        segs = [{"in": 0.0, "out": 2.0}, {"in": 2.0, "out": 3.0}]
        self.assertEqual(len(vp.film_words(words, segs)), 1)

    def test_stamps_never_show_sixty_seconds(self):
        self.assertEqual([vp.stamp(t) for t in (0.0, 59.96, 119.97, 61.25)], ["0:00.0", "1:00.0", "2:00.0", "1:01.2"])

    def test_windows_cover_the_film_without_gaps(self):
        self.assertEqual(vp.windows(65.0, 30.0), [(0.0, 30.0), (30.0, 60.0), (60.0, 65.0)])
        self.assertEqual(vp.windows(60.0, 30.0), [(0.0, 30.0), (30.0, 60.0)])

    def test_on_screen_lists_cards_overlapping_the_window(self):
        specs = {"g1": {"type": "kw", "text": "95% firm", "sub": "bez zwrotu"}}
        shown = [{"id": "g1", "at": 25.0, "dur": 10.0}, {"id": "b1", "at": 70.0, "dur": 3.0, "kind": "broll"}]
        self.assertEqual(vp.on_screen(shown, specs, 30.0, 60.0), ["g1 (kw) 25.0-35.0 s: 95% firm / bez zwrotu"])
        self.assertEqual(vp.on_screen(shown, specs, 60.0, 90.0), ["b1 (broll) 70.0-73.0 s"])

    def test_a_card_without_spec_is_named_not_guessed(self):
        shown = [{"id": "literowka", "at": 1.0, "dur": 2.0}]
        self.assertEqual(vp.on_screen(shown, {}, 0.0, 5.0), ["literowka (BRAK SPECA) 1.0-3.0 s"])

    def test_card_text_keeps_its_colon(self):
        specs = {"g": {"type": "kw", "text": "Koszt:"}}
        self.assertEqual(vp.on_screen([{"id": "g", "at": 0.0, "dur": 1.0}], specs, 0.0, 5.0), ["g (kw) 0.0-1.0 s: Koszt:"])


def project(work: Path, size: str = "320x180", **edl) -> Path:
    """A tiny finished film (8 s) with its plan, transcript, EDL and card specs."""
    film = work / "film.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=30:d=8",
                    "-c:v", "libx264", str(film)], check=True)
    (work / "w.json").write_text(json.dumps({"transcription": [word("cześć", 0.5, 0.9), word("koniec", 6.0, 6.5)]}))
    (work / "edl.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": 8.0}],
                                               "overlays": [{"id": "g1", "at": 1.0, "dur": 2.0}], **edl}))
    (work / "specs.json").write_text(json.dumps([{"id": "g1", "type": "kw", "text": "Tytuł"}]))
    (work / "plan.json").write_text(json.dumps({"words": "w.json", "edl_out": "edl.json", "gfx_specs": "specs.json"}))
    return film


class PackTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.work = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_a_tiny_film_gives_sheets_and_a_readable_pack(self):
        work = self.work
        film = project(work)
        r = vp.pack(work / "plan.json", str(film), work / "out", every=1.0, size=5.0)
        self.assertEqual([w["sheet"] for w in r["windows"]], ["w000.jpg", "w001.jpg"])
        self.assertEqual(r["windows"][0]["said"], "cześć")
        self.assertEqual(r["windows"][1]["said"], "koniec")
        img = cv2.imread(str(work / "out" / "w000.jpg"))
        assert img is not None
        self.assertEqual(img.shape[1], 4 * 400)  # 4 frames side by side, 225 px high -> 400 px wide
        md = (work / "out" / "pack.md").read_text()
        self.assertIn("g1 (kw) 1.0-3.0 s: Tytuł", md)
        self.assertIn("Na ekranie: tylko kamera", md)
        self.assertEqual(sorted(p.name for p in (work / "out").iterdir()), ["pack.json", "pack.md", "w000.jpg", "w001.jpg"])

    def test_a_vertical_short_with_broll_through_the_command_line(self):
        film = project(self.work, "180x320", vertical=True, broll=[{"id": "b1", "at": 4.0, "dur": 2.0}])
        rc, _ = run_main([str(self.work / "plan.json"), str(film), str(self.work / "out"), "--window", "4"])
        self.assertEqual(rc, 0)
        r = json.loads((self.work / "out" / "pack.json").read_text())
        self.assertTrue(r["vertical"])
        self.assertEqual(r["every"], 1.5)
        self.assertEqual([w["start"] for w in r["windows"]], [0.0, 4.0])
        self.assertEqual(r["windows"][1]["on_screen"], ["b1 (broll) 4.0-6.0 s"])
        img = cv2.imread(str(self.work / "out" / "w000.jpg"))
        assert img is not None
        self.assertEqual(img.shape[0], 400)  # one row of 400 px high vertical frames

    def test_a_new_pack_replaces_the_old_one(self):
        film = project(self.work)
        out = self.work / "out"
        vp.pack(self.work / "plan.json", str(film), out, every=1.0, size=2.0)
        self.assertTrue((out / "w003.jpg").exists())
        vp.pack(self.work / "plan.json", str(film), out, every=1.0, size=5.0)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["pack.json", "pack.md", "w000.jpg", "w001.jpg"])

    def test_a_window_without_frames_is_reported_not_dropped(self):
        film = project(self.work)
        real = vp.grab_frames
        with mock.patch.object(vp, "grab_frames", lambda *a: real(*a)[:3]):  # a render cut short after 3 s
            err = io.StringIO()
            with redirect_stderr(err):
                r = vp.pack(self.work / "plan.json", str(film), self.work / "out", every=1.0, size=4.0)
        self.assertEqual(r["missing"], [1])
        self.assertIn("no frames for window 1", err.getvalue())
        self.assertIn("UWAGA: okna bez klatek (nieobejrzane): [1]", (self.work / "out" / "pack.md").read_text())

    def test_a_broken_plan_is_a_named_failure(self):
        film = project(self.work)
        (self.work / "plan.json").write_text("{}")
        rc, err = run_main([str(self.work / "plan.json"), str(film), str(self.work / "out")])
        self.assertEqual(rc, 1)
        self.assertIn("FAILED viewer_pack", err)
        self.assertIn("KeyError", err)

    def test_a_broken_film_says_what_ffprobe_said(self):
        project(self.work)
        bad = self.work / "bad.mp4"
        bad.write_text("garbage")
        rc, err = run_main([str(self.work / "plan.json"), str(bad), str(self.work / "out")])
        self.assertEqual(rc, 1)
        self.assertIn("FAILED viewer_pack", err)
        self.assertIn("ffprobe: ", err)
        self.assertIn("Invalid data", err)

    def test_frames_left_by_a_killed_run_are_cleared(self):
        film = project(self.work)
        left = self.work / "out" / ".frames-abc"
        left.mkdir(parents=True)
        (left / "f00001.jpg").write_bytes(b"x")
        vp.pack(self.work / "plan.json", str(film), self.work / "out", every=1.0, size=5.0)
        self.assertFalse(left.exists())

    def test_usage_and_missing_files(self):
        self.assertEqual(run_main([])[0], 2)
        self.assertEqual(run_main(["a", "b", "c", "--every", "0"])[0], 2)
        self.assertEqual(run_main(["a", "b", "c", "--every", "abc"])[0], 2)
        self.assertEqual(run_main(["/nope/plan.json", "/nope/film.mp4", "/tmp/x"])[0], 1)


def run_main(args: list[str]) -> tuple[int, str]:
    err = io.StringIO()
    with redirect_stderr(err), redirect_stdout(io.StringIO()):
        rc = vp.main(args)
    return rc, err.getvalue()


if __name__ == "__main__":
    unittest.main()
