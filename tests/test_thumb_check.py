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


class WordsTest(unittest.TestCase):
    def test_what_counts_as_a_word(self):
        self.assertEqual(T.content_words("3 z 4"), ["3", "4"])  # one-letter words go, digits stay
        self.assertEqual(T.content_words("92% → 18%: czy to zadziałało?"), ["92%", "18%", "czy", "to", "zadziałało"])
        self.assertEqual(T.content_words(""), [])

    def test_film_2_long_a_is_ten_words(self):  # 18% | zmian bez przeglądu. Było 92% | AI pisze mój kod
        self.assertEqual(len(T.content_words("18% zmian bez przeglądu. Było 92% AI pisze mój kod")), 10)


class TopicLabelTest(unittest.TestCase):
    def test_labels_warn(self):
        for big in ("Kod z AI", "Blizna", "Szlaban", "Jedno zdanie", "Nowy pracownik"):
            self.assertTrue(T.is_topic_label(big), big)

    def test_a_promise_is_not_a_label(self):
        for big in ("18%", "3 z 4", "Kto sprawdza?", "„Gotowe”?", "Katar vs rezonans", "92% → 18%", "A -> B", "Psuję kod", "Kiedy przestać", "Stop dla AI", ""):
            self.assertFalse(T.is_topic_label(big), big)


class RoundTwoTextTest(unittest.TestCase):  # round 2 TH1, TH10
    def test_phrase_words_are_not_counted_against_the_title(self):  # was a false FAIL: 0.67
        self.assertGreaterEqual(T.title_share("Claude Code: 18%", "Claude Code od podstaw"), T.SHARE_MAX)
        self.assertEqual(T.title_share("Claude Code: 18%", "Claude Code od podstaw", "Claude Code"), 0.0)

    def test_a_tool_name_is_not_a_topic_label(self):
        for big in ("Claude Code", "MCP", "n8n"):
            self.assertFalse(T.is_topic_label(big), big)
        self.assertTrue(T.is_topic_label("Kod z AI"))  # "kod" is a word, not a tool

    def test_small_letter_and_money_warn(self):
        w = T.text_warns("x", {"big": "leci na ślepo.", "sub": "10 000 zł"})
        self.assertTrue(any("small letter" in x for x in w) and any("money" in x for x in w), w)
        self.assertFalse(T.text_warns("x", {"big": "92% → 18%"}))
        self.assertFalse([x for x in T.text_warns("x", {"big": "3 z 4"}) if "small letter" in x])  # film 2: a digit first is not a small letter


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.out = Path(self.t.name)
        (self.out / "thumbnails").mkdir()
        for i in "AB": thumb(self.out / f"thumbnails/long_{i}.jpg", "SZLABAN", 200)
        self.real = T.face_info, T.FACE_MODEL
        T.FACE_MODEL = Path(__file__)  # any file: the model is "there"

    def tearDown(self):
        T.face_info, T.FACE_MODEL = self.real
        self.t.cleanup()

    def run_check(self, spec, height=0.0, cx=0.75, n=1, titles=(), phrase=""):
        T.face_info = lambda img: (height, cx if height else 0.0, n if height else 0)
        return T.check(spec, self.out, list(titles), phrase)

    @unittest.skipUnless(shutil.which("tesseract"), "no tesseract")
    def test_word_limit_fail_warn_pass(self):
        ten = {"id": "A", "big": "SZLABAN", "sub": "zmian bez przeglądu. Było 92%", "tag": "AI pisze mój kod"}  # 1 + 5 + 4 = 10
        six = {"id": "B", "big": "SZLABAN", "sub": "bez przeglądu zmian", "tag": "AI pisze"}  # 1 + 3 + 2
        bad, _ = self.run_check({"long": [ten]})
        self.assertTrue(any("long_A: 10 words" in b for b in bad), bad)
        bad, _ = self.run_check({"long": [six]})
        self.assertTrue(any("long_B: 6 words" in b for b in bad), bad)
        five = dict(six, sub="bez przeglądu", tag="AI pisze")  # 1 + 2 + 2 = 5: WARN, not FAIL
        bad, warn = self.run_check({"long": [five]})
        self.assertFalse([b for b in bad if "words" in b], bad)
        self.assertTrue(any("long_B: 5 words" in w for w in warn), warn)
        four = dict(six, sub="bez przeglądu", tag="")  # 1 + 2 = 3
        bad, warn = self.run_check({"long": [four]})
        self.assertFalse([x for x in bad + warn if "words" in x], (bad, warn))

    @unittest.skipUnless(shutil.which("tesseract"), "no tesseract")
    def test_face_height_warns_only_between_zero_and_the_minimum(self):
        spec = {"long": [{"id": "A", "big": "SZLABAN"}]}
        for h, warns in ((0.0, False), (0.39, True), (0.40, False), (0.6, False)):
            _, warn = self.run_check(spec, h)
            self.assertEqual(any("face is" in w for w in warn), warns, (h, warn))
        self.assertIn("39%", next(w for w in self.run_check(spec, 0.39)[1] if "face is" in w))

    @unittest.skipUnless(shutil.which("tesseract"), "no tesseract")
    def test_centred_face_two_faces_and_flat_tone_warn(self):
        spec = {"long": [{"id": "A", "big": "SZLABAN"}]}
        _, warn = self.run_check(spec, 0.6, cx=0.5, n=2)
        self.assertTrue(any("centred" in w for w in warn) and any("2 faces" in w for w in warn), warn)
        _, warn = self.run_check(spec, 0.6, cx=0.75, n=1)
        self.assertFalse([w for w in warn if "centred" in w or "faces" in w], warn)
        self.assertTrue(any("colour groups" in w for w in warn), warn)  # black on white: 0 colour groups

    @unittest.skipUnless(shutil.which("tesseract"), "no tesseract")
    def test_the_phrase_reaches_the_share_check(self):
        spec = {"long": [{"id": "A", "big": "Claude Code", "sub": "18%"}]}
        bad, _ = self.run_check(spec, titles=["Claude Code od podstaw"])
        self.assertTrue(any("of its words are in the title" in b for b in bad), bad)
        bad, _ = self.run_check(spec, titles=["Claude Code od podstaw"], phrase="Claude Code")
        self.assertFalse([b for b in bad if "in the title" in b], bad)

    @unittest.skipUnless(shutil.which("tesseract"), "no tesseract")
    def test_topic_label_is_checked_on_long_and_shorts(self):
        spec = {"long": [{"id": "A", "big": "Kod z AI"}, {"id": "B", "big": "18%"}],
                "shorts": [{"id": "s02", "big": "Szlaban"}, {"id": "s07", "big": "Katar vs rezonans"}]}
        _, warn = self.run_check(spec)
        self.assertEqual(sorted(w.split(":")[0] for w in warn if "topic label" in w), ["long_A", "s02"], warn)

    def test_warnings_do_not_fail_the_cli(self):
        (self.out / "youtube").mkdir()
        spec = self.out / "thumbs.json"
        spec.write_text('{"shorts": [{"id": "s02", "big": "Szlaban"}]}')
        T.face_info = lambda img: (0.0, 0.0, 0)
        self.assertEqual(T.main([str(spec), str(self.out)]), 0 if shutil.which("tesseract") else 1)


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
        bad = [b for b in T.problems(spec, self.out, []) if not b.startswith("no face model")]  # CI: models/ is not in git
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("long_B: at 320 px only", bad[0])

    def test_every_variant_with_a_face_and_a_missing_file_are_named(self):
        thumb(self.out / "thumbnails/long_A.jpg", "SZLABAN", 200)
        spec = {"long": [{"id": "A", "big": "SZLABAN"}, {"id": "B", "big": "BLIZNA"}]}
        real, model = T.face_info, T.FACE_MODEL
        try:
            T.face_info, T.FACE_MODEL = (lambda img: (0.5, 0.75, 1)), Path(__file__)  # any file: the model is "there"
            bad = T.problems(spec, self.out, [])
            T.FACE_MODEL = self.out / "none.onnx"
            gone = T.problems(spec, self.out, [])
        finally:
            T.face_info, T.FACE_MODEL = real, model
        self.assertIn("long_B: no long_B.jpg", bad)
        self.assertTrue(any(b.startswith("all 1 long variants show a face") for b in bad), bad)
        self.assertTrue(any(b.startswith("no face model") for b in gone), gone)  # named, never a pass

    @unittest.skipUnless(T.FACE_MODEL.is_file(), "no face model (models/ is not in git; CI has none)")
    def test_yunet_sees_no_face_in_a_picture_of_words(self):
        thumb(self.out / "thumbnails/long_A.jpg", "SZLABAN", 200)
        self.assertFalse(T.has_face(self.out / "thumbnails/long_A.jpg"))

    def test_a_broken_model_file_is_a_named_error(self):  # cv2.error is not a RuntimeError
        thumb(self.out / "thumbnails/long_A.jpg", "SZLABAN", 200)
        model = T.FACE_MODEL
        try:
            T.FACE_MODEL = self.out / "lfs.onnx"; T.FACE_MODEL.write_text("version https://git-lfs.github.com/spec/v1\n")
            with self.assertRaises(RuntimeError) as e: T.has_face(self.out / "thumbnails/long_A.jpg")
        finally:
            T.FACE_MODEL = model
        self.assertIn("face detector on long_A.jpg", str(e.exception))

    def test_cli(self):
        self.assertEqual(T.main([]), 2)


if __name__ == "__main__":
    unittest.main()
