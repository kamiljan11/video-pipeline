"""title_check: the long's A/B/C titles (length, the phrase first, a source, the promise said in the opening)"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import title_check as T

MD = """## Tytuły

| wariant | kąt | tytuł | znaki | źródło |
|---|---|---|---|---|
| A | wynik | Kod pisze AI, a ja się wstydziłem | 33 | kanał X |
| B | problem | AI mówi „gotowe”, a nic nie działa | 34 | kanał Y |

## Fraza kluczowa
kod z AI

## Opis
"""


class TitleTest(unittest.TestCase):
    def test_the_table_is_read_by_its_header(self):
        rows = T.titles(MD)
        self.assertEqual([r["variant"] for r in rows], ["A", "B"])
        self.assertEqual(rows[1]["title"], "AI mówi „gotowe”, a nic nie działa")
        self.assertEqual(rows[0]["source"], "kanał X")
        self.assertIsNone(T.titles("## Tytuły\n| A | t |\n")[0]["source"])  # no header: no źródło column at all

    def test_polish_endings_match_and_stop_words_do_not_count(self):
        self.assertTrue(T.same("wstydziłem", "wstydziłam"))
        self.assertTrue(T.same("kod", "kodu"))
        self.assertFalse(T.same("ai", "aim"))
        self.assertEqual(T.content("Mój system na AI, dziś 18%"), ["system", "ai", "18%"])

    def test_the_opening_must_say_what_the_title_promises(self):
        said = ["muszę", "się", "przyznać", "wstydziłam", "się", "że", "kod", "pisze", "AI", "ale", "nic", "nie", "działało"]
        self.assertEqual(T.problems(MD, said), [])
        bad = T.problems(MD, ["dzień", "dobry", "dziś", "o", "pogodzie"])
        self.assertTrue(any(b.startswith("A: the first 30 s say none") for b in bad), bad)
        self.assertIn("the opening cannot be checked: no words and EDL of the long", T.problems(MD, None))
        self.assertIn("no `## Fraza kluczowa`", T.problems(MD.replace("kod z AI\n", ""), said)[0])

    def test_the_opening_is_read_through_the_edl_cut(self):  # what is HEARD in the film, not the recording's first 30 s
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            said = ["dzień", "dobry"] * 20 + ["kod", "pisze", "AI", "nic", "działa"]  # 45 words, one a second
            (d / "w.json").write_text(json.dumps({"transcription": [{"offsets": {"from": i * 1000, "to": i * 1000 + 500}, "text": f" {w}"}
                                                                    for i, w in enumerate(said)]}))
            (d / "plan_long.json").write_text(json.dumps({"words": "w.json", "edl_out": "e.json"}))
            (d / "md").write_text(MD)
            run = lambda: subprocess.run([sys.executable, str(ROOT / "title_check.py"), str(d / "md"), str(d / "plan_long.json")],
                                         capture_output=True, text=True, check=False, cwd=ROOT)
            (d / "e.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": 45.0}]}))  # no cut: the promise comes at 40 s
            r = run()
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("A: the first 30 s say", r.stdout)
            (d / "e.json").write_text(json.dumps({"segments": [{"in": 38.0, "out": 45.0}]}))  # the greeting cut away
            r = run()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(T.main([]), 2)


if __name__ == "__main__":
    unittest.main()
