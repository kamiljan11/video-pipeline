"""ig_check: carousel + Reel captions (round 2 IG1, IG2, IG4, IG6; SYNTH2-instagram R1-R6, R12)"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import ig_check as I

TEXT = "Trzy rzeczy, które sprawdzam w kodzie z AI przed wysłaniem.\n\nOpis karuzeli.\n\nLink w bio."


def make(root: Path, n: int = 5, text: str = TEXT, tags: list | None = None, alt: list | None = None, last: str = "Zapisz na później.") -> Path:
    d = root / "instagram" / "p01"
    d.mkdir(parents=True)
    for i in range(1, n + 1): (d / f"slide_{i:02d}.png").write_bytes(b"png")
    (d / f"slide_{n:02d}.txt").write_text(last)
    cap = {"text": text, "hashtags": ["AI", "kod"] if tags is None else tags, "alt": [f"slajd {i}" for i in range(n)] if alt is None else alt}
    (d / "caption.json").write_text(json.dumps(cap, ensure_ascii=False))
    return root / "instagram"


class CarouselTest(unittest.TestCase):
    def test_a_good_carousel_passes_clean(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(I.check(make(Path(t))), ([], []))

    def test_platform_limits_fail(self):
        with tempfile.TemporaryDirectory() as t:
            bad, _ = I.check(make(Path(t), tags=["a", "b", "c", "d", "e", "f"]))
            self.assertTrue(any("6 hashtags, Instagram allows 5" in b for b in bad), bad)
        with tempfile.TemporaryDirectory() as t:
            bad, _ = I.check(make(Path(t), text=TEXT + "x" * 2200))
            self.assertTrue(any("Instagram allows 2200" in b for b in bad), bad)
        with tempfile.TemporaryDirectory() as t:
            bad, _ = I.check(make(Path(t), n=21, text="Opis.\n\nLink w bio."))
            self.assertTrue(any("21 slides, Instagram allows 20" in b for b in bad), bad)

    def test_alt_one_per_slide(self):  # R12
        with tempfile.TemporaryDirectory() as t:
            bad, _ = I.check(make(Path(t), alt=["a", "b"]))
            self.assertTrue(any(b.startswith("p01: alt: want one non-empty text per slide (5), got 2") for b in bad), bad)
        with tempfile.TemporaryDirectory() as t:
            bad, _ = I.check(make(Path(t), alt=["a", "", "c", "d", "e"]))
            self.assertTrue(any("alt" in b for b in bad), bad)

    def test_hook_count_matches_content_slides(self):  # IG1 / R4: cover + 3 + call = 5
        with tempfile.TemporaryDirectory() as t:
            bad, _ = I.check(make(Path(t), n=6))
            self.assertTrue(any("promises 3 things, the carousel has 4 content slides" in b for b in bad), bad)

    def test_numbers_the_film_never_says_fail(self):  # IG1 / R3
        with tempfile.TemporaryDirectory() as t:
            ig = make(Path(t), text="AI kłamało w 75% porażek.\n\nLink w bio.")
            words = Path(t) / "words.json"
            words.write_text(json.dumps({"transcription": [{"text": " 92"}, {"text": " trzy"}]}))
            bad, _ = I.check(ig, words)
            self.assertTrue(any("numbers in the text that the film does not say: 75" in b for b in bad), bad)

    def test_warnings_slides_tags_link_call(self):
        with tempfile.TemporaryDirectory() as t:
            _, warn = I.check(make(Path(t), n=4, text="Opis bez listy.\n\nLink w bio.", tags=["a", "b", "c", "d"]))
            self.assertTrue(any("4 slides, want 5-10" in w for w in warn) and any("4 hashtags, want at most 3" in w for w in warn), warn)
        with tempfile.TemporaryDirectory() as t:
            _, warn = I.check(make(Path(t), text=TEXT + "\nhttps://kamiljan.com/blog"))
            self.assertTrue(any("not make it clickable" in w for w in warn), warn)
        with tempfile.TemporaryDirectory() as t:
            _, warn = I.check(make(Path(t), last="Zapisz i wyślij znajomemu."))
            self.assertTrue(any("2 calls" in w for w in warn), warn)
        with tempfile.TemporaryDirectory() as t:
            _, warn = I.check(make(Path(t), text="a" * 130 + "\n\nLink w bio."))
            self.assertTrue(any("line 1: 130 characters" in w for w in warn), warn)

    def test_missing_files_are_named(self):
        with tempfile.TemporaryDirectory() as t:
            ig = make(Path(t))
            (ig / "p01" / "caption.json").unlink()
            self.assertEqual(I.check(ig)[0], ["p01: no caption.json"])
            (ig / "p01" / "caption.json").write_text("{")
            self.assertTrue(I.check(ig)[0][0].startswith("p01: caption.json is not JSON"))
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(I.check(Path(t) / "instagram")[0][0].startswith("no "))
            (Path(t) / "instagram").mkdir()
            self.assertTrue(any("no carousel folder" in b for b in I.check(Path(t) / "instagram")[0]))


    def test_bad_bytes_and_a_broken_table_are_named(self):  # review 2026-11-07 code: no traceback, no silent default
        with tempfile.TemporaryDirectory() as t:
            ig = make(Path(t))
            (ig / "p01" / "slide_05.txt").write_bytes(b"\xff")
            self.assertEqual(I.check(ig)[0], [])
        old = I.LIMITS_ERROR
        try:
            I.LIMITS_ERROR = "table broken"
            self.assertEqual(I.check(Path("/nope")), (["table broken"], []))
        finally:
            I.LIMITS_ERROR = old


class ReelTest(unittest.TestCase):  # IG6: Reels = the shorts
    def test_reel_caption(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t) / "instagram" / "reels"; r.mkdir(parents=True)
            (r / "s01.json").write_text(json.dumps({"text": "AI mówi gotowe, a nic nie działa.\n\nCały film: link w bio.", "hashtags": ["AI"]}))
            self.assertEqual(I.check(Path(t) / "instagram"), ([], []))
            (r / "s02.json").write_text(json.dumps({"text": " ", "hashtags": []}))
            (r / "s03.json").write_text(json.dumps({"text": "Hook.\nhttps://youtu.be/x", "hashtags": ["a", "b", "c", "d"]}))
            bad, warn = I.check(Path(t) / "instagram")
            self.assertEqual(bad, ["reels/s02.json: the caption has no line 1"])
            self.assertTrue(any(w.startswith("reels/s03.json: 4 hashtags") for w in warn) and any("clickable" in w for w in warn), warn)

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(I.main([str(make(Path(t)))]), 0)
            self.assertEqual(I.main([]), 2)
            self.assertEqual(I.main([str(Path(t) / "nope")]), 1)


if __name__ == "__main__":
    unittest.main()
