"""title_check: the long's A/B/C titles (length, the phrase first, a source, the promise said in the opening)"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


def warn(title: str) -> list[str]:
    return T.warnings(f"## Tytuły\n\n| wariant | kąt | tytuł | znaki | źródło |\n|---|---|---|---|---|\n| A | x | {title} | 0 | s |\n")


class TitleWarnTest(unittest.TestCase):
    def test_good_titles_get_no_warning(self):
        for t in ["Jak pisać kod z AI krok po kroku, bez wstydu", "92% zmian bez przeglądu. Dziś 18%, jak to zrobiłem",
                  "Claude Code dla firm: wdrożenie w 20 minut", "Dlaczego AI mówi „gotowe”, a nic nie działa",
                  "Mój system na AI skrócił przegląd kodu o 74%"]:
            self.assertEqual(warn(t), [], t)

    def test_no_promise_marker_warns_only_for_a_long_title(self):
        self.assertTrue(any("no promise marker" in w for w in warn("Moje przemyślenia o świecie sztucznej inteligencji")))
        self.assertTrue(any("no promise marker" in w for w in warn("Ciekawy eksperyment z agentami i kodem w repo")))
        self.assertFalse(any("no promise marker" in w for w in warn("Szybki start")))  # short: only the length warns

    def test_film_2_titles_starting_with_moj_system_warn(self):
        w = warn("Mój system na AI do pisania i przeglądu kodu")
        self.assertTrue(any("Mój/Moje/Moja" in x for x in w), w)
        w = warn("AI mówi „gotowe”, a nic nie działa. Mój system mu nie wierzy")
        self.assertTrue(any("Mój/Moje/Moja" in x for x in w), w)
        self.assertFalse(any("Mój/Moje/Moja" in x for x in warn("92% zmian bez przeglądu. Dziś 18%. Mój system na AI")))

    def test_number_with_news_warns(self):
        self.assertTrue(any("news word" in w for w in warn("14 nowości w Claude Code, jak ich używać od zera")))
        self.assertTrue(any("news word" in w for w in warn("5 aktualizacji AI, które zmieniły kod w tym tygodniu")))

    def test_soft_minimum_length(self):
        w = warn("Jak pisać kod z AI")
        self.assertTrue(any("soft min 35" in x for x in w), w)
        self.assertEqual(warn("Jak pisać kod z AI krok po kroku w 20 minut"), [])

    def test_series_prefix_and_brand_tag(self):
        self.assertTrue(any("series prefix" in w for w in warn("Tutorial: jak pisać kod z AI krok po kroku")))
        self.assertTrue(any("series prefix" in w for w in warn("Nowości: Claude Code dla firm i programistów")))
        self.assertTrue(any("brand tag" in w for w in warn("Jak pisać kod z AI krok po kroku \\| Kamil Jan")))

    def test_warnings_never_change_the_exit_code(self):
        with tempfile.TemporaryDirectory() as t:
            md = Path(t) / "md"
            md.write_text("## Tytuły\n\n| wariant | tytuł | źródło |\n|---|---|---|\n| A | Tutorial: kod z AI | kanał X |\n\n## Fraza kluczowa\nkod z AI\n")
            r = subprocess.run([sys.executable, str(ROOT / "title_check.py"), str(md)], capture_output=True, text=True, check=False, cwd=ROOT)
            self.assertIn("WARN A:", r.stdout)
            self.assertEqual(r.returncode, 1)  # only the "no opening" problem, not the WARN lines
            self.assertNotIn("series prefix", "\n".join(T.problems(md.read_text(), [])))


if __name__ == "__main__":
    unittest.main()


class TitleLintFileTest(unittest.TestCase):
    def test_a_broken_lint_file_is_one_warning_not_a_traceback(self):  # review 2026-11-07: ops-3
        with mock.patch.object(T, "lint_lists", side_effect=ValueError("bad json")):
            got = T.warnings("## Tytuły\n| A | Jakiś tytuł o AI | x |\n")
        self.assertTrue(len(got) == 1 and "cannot be read" in got[0], got)
