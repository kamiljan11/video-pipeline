"""review_player.py: Kamil watches the dry film and leaves notes at the pause (2026-11-15)."""
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import review_player as rp

WORDS = [{"offsets": {"from": 10000, "to": 10400}, "text": " szlaban"}, {"offsets": {"from": 10500, "to": 10900}, "text": " blokuje"},
         {"offsets": {"from": 30000, "to": 30400}, "text": " daleko"}]
EDL = {"segments": [{"in": 8.0, "out": 12.0}, {"in": 29.0, "out": 31.0}]}


class PartsTest(unittest.TestCase):
    def test_a_note_keeps_the_recording_second_and_the_words_said_there(self):
        n = rp.note(EDL, WORDS, 2.3, "karta za wcześnie")
        self.assertEqual(n, {"t": 2.3, "src": 10.3, "words": "szlaban blokuje", "text": "karta za wcześnie"})
        self.assertEqual(rp.note(EDL, WORDS, 5.0, "x")["src"], 30.0)  # after the cut: the second piece

    def test_byte_ranges_a_video_element_asks_for(self):
        self.assertEqual(rp.byte_range("bytes=0-", 100), (0, 99))
        self.assertEqual(rp.byte_range("bytes=10-19", 100), (10, 19))
        self.assertEqual(rp.byte_range("bytes=-30", 100), (70, 99))
        self.assertEqual(rp.byte_range("bytes=90-500", 100), (90, 99))
        self.assertIsNone(rp.byte_range(None, 100))
        self.assertIsNone(rp.byte_range("bytes=200-", 100))


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "w.json").write_text(json.dumps({"transcription": WORDS}))
        (self.d / "plan_long.json").write_text(json.dumps({"words": "w.json"}))
        (self.d / "edl_long.json").write_text(json.dumps(EDL))
        self.video = self.d / "long.mp4"; self.video.write_bytes(bytes(range(256)) * 4)
        self.rv = rp.Review(self.d, "long", self.video)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), rp.handler(self.rv))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close()

    def post(self, path, body):
        r = urllib.request.urlopen(urllib.request.Request(self.url + path, data=json.dumps(body).encode(), method="POST"))
        return json.loads(r.read())

    def test_notes_are_saved_in_film_order_deleted_and_marked_done(self):
        self.post("/note", {"t": 5.0, "text": "drugi"})
        st = self.post("/note", {"t": 2.3, "text": "pierwszy"})
        self.assertEqual([n["text"] for n in st["notes"]], ["pierwszy", "drugi"])
        self.post("/delete", {"i": 1})
        self.post("/done", {})
        saved = json.loads((self.d / "review_notes_long.json").read_text())
        self.assertEqual([n["text"] for n in saved["notes"]], ["pierwszy"])
        self.assertTrue(saved["done"])
        self.assertEqual(rp.Review(self.d, "long", self.video).state["notes"][0]["words"], "szlaban blokuje")  # reopened

    def test_a_bad_note_is_400_and_another_page_may_not_write(self):  # pg-review 2026-11-15
        with self.assertRaises(urllib.error.HTTPError) as e: self.post("/note", {"text": "bez czasu"})
        self.assertEqual(e.exception.code, 400)
        req = urllib.request.Request(self.url + "/note", data=b'{"t": 1, "text": "x"}', method="POST",
                                     headers={"Origin": "http://evil.example"})
        with self.assertRaises(urllib.error.HTTPError) as e: urllib.request.urlopen(req)
        self.assertEqual(e.exception.code, 403)
        self.assertEqual(self.rv.state["notes"], [])

    def test_the_video_is_served_in_ranges_so_the_player_can_seek(self):
        req = urllib.request.Request(self.url + "/video", headers={"Range": "bytes=256-259"})
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 206)
            self.assertEqual(r.headers["Content-Range"], "bytes 256-259/1024")
            self.assertEqual(r.read(), bytes([0, 1, 2, 3]))
        with urllib.request.urlopen(self.url + "/") as r:
            self.assertIn("Spacja = pauza", r.read().decode())


if __name__ == "__main__":
    unittest.main()
