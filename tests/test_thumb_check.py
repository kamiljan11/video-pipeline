"""thumb_check: the long thumbnails at feed size (OCR at 320 px, one variant without a face, words that do not repeat a title)"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import thumb_check as T

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"


def thumb(f: Path, text: str, size: int) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0A1430:s=1280x720", "-frames:v", "1",
                    "-vf", f"drawtext=fontfile={FONT}:text='{text}':fontsize={size}:fontcolor=0xECF0F6:x=80:y=200", str(f)], check=True)


class ShareTest(unittest.TestCase):
    def test_ocr_noise_and_one_letter_words(self):
        self.assertEqual(T.read_share("3 z 4", "“324"), 1.0)  # the "z" between digits is not asked for
        self.assertEqual(T.read_share("18%", "18% ."), 1.0)
        self.assertAlmostEqual(T.read_share("Kod z AI", "Kod Ł. AI"), 1.0)
        self.assertLess(T.read_share("SZLABAN", "SZ"), T.OCR_MIN)

    def test_a_thumbnail_that_repeats_the_title(self):  # film 2: long_A "18% zmian bez przeglądu. Było 92%" over title A
        title = "92% zmian bez przeglądu. Dziś 18%. Mój system na AI"
        self.assertGreaterEqual(T.title_share("18% zmian bez przeglądu. Było 92% AI pisze mój kod", title), T.SHARE_MAX)
        self.assertLess(T.title_share("3 z 4 porażek AI to sukces", title), T.SHARE_MAX)
        self.assertEqual(T.title_share("", title), 0.0)


@unittest.skipUnless(shutil.which("tesseract"), "no tesseract")
class PictureTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.out = Path(self.t.name)
        (self.out / "thumbnails").mkdir()

    def tearDown(self):
        self.t.cleanup()

    def test_a_word_too_small_for_the_feed_fails_a_big_one_passes(self):
        thumb(self.out / "thumbnails/long_A.jpg", "SZLABAN", 200)
        thumb(self.out / "thumbnails/long_B.jpg", "BLIZNA ZOSTAJE NA ZAWSZE", 14)  # 3.5 px at 320 wide
        spec = {"long": [{"id": "A", "big": "SZLABAN"}, {"id": "B", "big": "BLIZNA ZOSTAJE NA ZAWSZE"}]}
        bad = T.problems(spec, self.out, [])
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("long_B: at 320 px only", bad[0])

    def test_every_variant_with_a_face_and_a_missing_file_are_named(self):
        thumb(self.out / "thumbnails/long_A.jpg", "SZLABAN", 200)
        spec = {"long": [{"id": "A", "big": "SZLABAN"}, {"id": "B", "big": "BLIZNA"}]}
        real = T.has_face
        try:
            T.has_face = lambda img: True
            bad = T.problems(spec, self.out, [])
        finally:
            T.has_face = real
        self.assertIn("long_B: no long_B.jpg", bad)
        self.assertTrue(any(b.startswith("all 1 long variants show a face") for b in bad), bad)
        self.assertFalse(T.has_face(self.out / "thumbnails/long_A.jpg"))  # YuNet on a picture of words: no face

    def test_cli(self):
        self.assertEqual(T.main([]), 2)


if __name__ == "__main__":
    unittest.main()
