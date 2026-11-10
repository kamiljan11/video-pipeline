"""ig_carousel: a post -> carousel.json + caption.json (5-10 slides, words from the post, one call), checked by ig_check"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import ig_carousel as C
import ig_check

POST = ("Najtrudniej było mi się nauczyć, kiedy przestać pilnować AI.\n\n"
        "Z pilnowaniem łatwo przesadzić. W takim systemie każdy błąd kusi, żeby dodać jeszcze jedną blokadę, na wszelki wypadek.\n\n"
        "Ale blokada, która częściej przeszkadza niż łapie błędy, jest jak alarm samochodowy. Po tygodniu nikt na niego nie patrzy.\n\n"
        "Dlatego mam prostą zasadę: nie ma prawdziwego problemu, nie ma nowej blokady. Decyzja jest moja.\n\n"
        "Cały system opisany krok po kroku: https://kamiljan.com/claude?utm_source=linkedin\n\n"
        "Którą blokadę u siebie obchodzisz?")


class SentencesTest(unittest.TestCase):
    def test_split_after_a_closing_quote_and_not_after_an_abbreviation(self):
        self.assertEqual(C.sentences("AI napisało „gotowe”. Sprawdzam i nic nie działa."), ["AI napisało „gotowe”.", "Sprawdzam i nic nie działa."])
        self.assertEqual(C.sentences("Np. taki przykład. Drugi."), ["Np. taki przykład.", "Drugi."])

    def test_group_pulls_the_count_into_range_or_fails_loudly(self):
        units = [f"To jest dość długie zdanie numer {w} o czymś ważnym dla czytelnika." for w in "abcdefghijk"]
        self.assertEqual(len(C.group(units, 3, 8)), 8)
        self.assertRaises(ValueError, C.group, ["Jedno krótkie."], 3, 8)

    def test_a_short_sentence_joins_a_neighbour_but_never_makes_three_sentences_a_slide(self):
        long1 = "To jest dość długie pierwsze zdanie, które mówi coś ważnego."
        g = C.group([long1, "Krótkie.", "Drugie krótkie.", long1, long1], 3, 8)
        self.assertTrue(all(len(C.sentences(u)) <= 2 for u in g), g)


class DeriveTest(unittest.TestCase):
    def test_spec_shape_and_words_from_the_post(self):
        s = C.derive(POST, "Kamil Jan · Higher Minds")
        sl = s["slides"]
        self.assertTrue(5 <= len(sl) <= 10)
        self.assertEqual((sl[0]["type"], sl[-1]["type"]), ("hook", "call"))
        self.assertEqual(sl[0]["title"], POST.split("\n")[0])
        self.assertEqual(sl[0]["kicker"], "Higher Minds")
        self.assertEqual(sl[-1]["title"], "Którą blokadę u siebie obchodzisz?")
        self.assertTrue(all(x["type"] == "idea" for x in sl[1:-1]))
        self.assertNotIn("http", json.dumps(s))
        self.assertIn("Decyzja jest moja.", " ".join(x["text"] for x in sl[1:-1]))

    def test_exactly_one_call_on_the_last_slide_and_none_before(self):
        s = C.derive(POST, "Kamil Jan · Higher Minds")
        last = " ".join(v for k, v in s["slides"][-1].items() if k != "type")
        self.assertEqual(len(ig_check.CTA.findall(last)), 1)
        self.assertIn("link w bio", last)
        with self.assertRaises(ValueError):
            C.derive(POST.replace("Decyzja jest moja.", "Zapisz to sobie."), "Kamil Jan")

    def test_hook_count_sets_the_number_of_idea_slides(self):
        post = POST.replace("Najtrudniej było mi się nauczyć, kiedy przestać pilnować AI.", "Pięć rzeczy, których nauczyłem się o blokadach.")
        s = C.derive(post, "Kamil Jan · Higher Minds")
        self.assertEqual(len(s["slides"]) - 2, 5)

    def test_a_post_with_too_few_paragraphs_is_refused(self):
        with self.assertRaises(ValueError):
            C.derive("Jedno zdanie.", "Kamil Jan")


class CaptionTest(unittest.TestCase):
    def test_link_becomes_link_w_bio(self):
        t = C.caption_text(POST)
        self.assertNotIn("http", t)
        self.assertIn("Cały system opisany krok po kroku: link w bio", t)

    def test_alt_one_per_slide_with_the_slide_words(self):
        s = C.derive(POST, "Kamil Jan · Higher Minds")
        alt = C.alt_texts(s)
        self.assertEqual(len(alt), len(s["slides"]))
        self.assertIn("okładka", alt[0])
        self.assertIn("wezwanie", alt[-1])

    def test_build_keeps_a_hand_edited_spec_unless_regen(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            spec = C.build("p1", POST, out, "Kamil Jan · Higher Minds", ["#ai"])
            spec["slides"][1]["text"] = "Moja poprawka."
            (out / "p1" / "carousel.json").write_text(json.dumps(spec, ensure_ascii=False))
            again = C.build("p1", POST, out, "Kamil Jan · Higher Minds", ["#ai"])
            self.assertEqual(again["slides"][1]["text"], "Moja poprawka.")
            fresh = C.build("p1", POST, out, "Kamil Jan · Higher Minds", ["#ai"], regen=True)
            self.assertNotEqual(fresh["slides"][1]["text"], "Moja poprawka.")
            cap = json.loads((out / "p1" / "caption.json").read_text())
            self.assertEqual((cap["hashtags"], len(cap["alt"])), (["#ai"], len(fresh["slides"])))


if __name__ == "__main__":
    unittest.main()
