"""linkedin.py image and video posts, the queue and run-due, against a fake LinkedIn (no network, no timer).

python3 -m unittest tests.test_linkedin_media
"""
from __future__ import annotations

import datetime
import fcntl
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))

from test_linkedin import AVAIL, COMMENT, ME, POST, PROC, RULES, Fake

import linkedin  # after the path insert: the scripts are not a package

TEXT = ("Najtrudniej było mi się nauczyć, kiedy przestać pilnować AI.\n\nZ pilnowaniem łatwo przesadzić.\n\n"
        + "Blokada, która częściej przeszkadza niż łapie błędy, jest jak alarm samochodowy. " * 5
        + "\n\nCały system: https://kamiljan.com/claude")
IMG_SPEC = {"text": TEXT, "hashtags": [], "cta_variant": "question", "first_comment": "Cały film: https://youtu.be/VeM1WTRy8nA"}
VID_SPEC = {"text": "Trzy słowa, które zmieniły moją pracę z AI. Cały film jest w pierwszym komentarzu, a ten short poniżej.",
            "hashtags": ["AI"], "first_comment": "Cały film: https://youtu.be/VeM1WTRy8nA", "video": "../s01.mp4",
            "video_title": "Trzy słowa"}
PNG = b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + (1080).to_bytes(4, "big") + (1350).to_bytes(4, "big") + b"\x08\x02\0\0\0" + b"x" * 500
MP4 = b"\0\0\0\x18ftypmp42" + bytes(range(256)) * 400  # 102 412 bytes: above LinkedIn's 75 KB floor

IMG_INIT = (200, {}, {"value": {"uploadUrl": "https://www.linkedin.com/dms-uploads/img", "image": "urn:li:image:I1"}})
UP = (201, {}, None)
CUT = 50000
TWO_PARTS = ((0, CUT - 1), (CUT, len(MP4) - 1))


def vid_init(parts=TWO_PARTS, host="www.linkedin.com"):
    return (200, {}, {"value": {"video": "urn:li:video:V1", "uploadToken": "tok", "uploadInstructions": [
        {"uploadUrl": f"https://{host}/dms-uploads/v/{i}", "firstByte": a, "lastByte": b} for i, (a, b) in enumerate(parts)]}})


def part(etag):
    return (200, {"etag": f'"{etag}"'}, None)


FINAL = (200, {}, None)


def http(code):
    return urllib.error.HTTPError("u", code, "x", Message(), io.BytesIO(b'{"message":"no"}'))


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="li-media-")); self.addCleanup(shutil.rmtree, self.root, True)
        self.tok, self.seen, self.queue = self.root / "token.json", self.root / "seen", self.root / "state" / "queue.jsonl"
        for name, value in (("TOKEN", self.tok), ("SEEN", self.seen), ("QUEUE", self.queue)):
            p = mock.patch.object(linkedin, name, value); p.start(); self.addCleanup(p.stop)
        p = mock.patch.object(linkedin.time, "sleep"); self.sleep = p.start(); self.addCleanup(p.stop)
        self.tok.write_text(json.dumps({"access_token": "T", "obtained_at": time.time(), "expires_in": 40 * 86400,
                                        "scope": "openid,profile,w_member_social"}))

    def image_post(self, name="alarm", spec=None, alt: str | None = "Kiedy przestać dokładać blokady"):
        d = self.root / "posts" / name; d.mkdir(parents=True)
        (d / "linkedin.json").write_text(json.dumps(spec or IMG_SPEC), encoding="utf-8")
        (d / "grafika.png").write_bytes(PNG)
        if alt is not None: (d / "grafika.txt").write_text(alt, encoding="utf-8")
        return d / "linkedin.json"

    def video_post(self, name="s01", spec=None, blob=MP4):
        d = self.root / "shorts" / name; d.mkdir(parents=True)
        (d / "linkedin.json").write_text(json.dumps(spec or VID_SPEC), encoding="utf-8")
        (self.root / "shorts" / "s01.mp4").write_bytes(blob)
        return d / "linkedin.json"

    def code(self, spec_path):
        return linkedin.prepare(spec_path)[2]

    def run_with(self, spec_path, fake, really=True, approve: str | None = "dry run", **kw):
        if approve == "dry run": approve = self.code(spec_path)
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()) as out:
            rec = linkedin.publish(spec_path, really, approve, **kw)
        self.out = out.getvalue()
        return rec


class KindAndRulesTest(Base):
    def test_the_spec_decides_the_kind(self):
        self.assertEqual([linkedin.kind(s) for s in (IMG_SPEC, VID_SPEC, {"carousel": {}})], ["image", "video", "document"])

    def test_link_and_fold_only_warn_for_image_and_video_posts(self):
        long_fold = {**IMG_SPEC, "text": "a" * 140 + "\n" + "b" * 100 + "\n" + TEXT}
        self.assertEqual(linkedin.check(long_fold, RULES), [])
        got = linkedin.warnings(long_fold, RULES)
        self.assertTrue(any("has a link" in w for w in got) and any("first two lines" in w for w in got), got)
        self.assertEqual(linkedin.check(VID_SPEC, RULES), [])  # 100+ characters is enough for a short
        doc = {**IMG_SPEC, "carousel": {"title": "t", "slides": []}}  # a document post keeps them as hard rules
        self.assertTrue(any("has a link" in p for p in linkedin.check(doc, RULES)))

    def test_hard_rules_still_stop_image_and_video_posts(self):
        cases = {
            "en/em dash": {**IMG_SPEC, "first_comment": "Film – link"},
            "at least 300": {**IMG_SPEC, "text": "Krótko."},
            '"video": the path of an .mp4': {**VID_SPEC, "video": "s01.mov"},
            '"video_title" only goes with "video"': {**IMG_SPEC, "video_title": "x"},
            '"alt_text" only goes with an image': {**VID_SPEC, "alt_text": "x"},
            '"carousel" and "video" together': {**VID_SPEC, "carousel": {"title": "t", "slides": []}},
            '"video_title": a text of at most': {**VID_SPEC, "video_title": "x" * 101},
        }
        for want, s in cases.items():
            with self.subTest(want=want):
                got = linkedin.check(s, RULES)
                self.assertTrue(any(want in p for p in got), got)

    def test_render_is_only_for_document_posts(self):
        with self.assertRaisesRegex(ValueError, "render is for document posts"): linkedin.render(self.image_post())


class ImagePostTest(Base):
    def test_a_dry_run_shows_the_alt_text_and_the_warnings_and_sends_nothing(self):
        spec_path, fake = self.image_post(), Fake(ME)
        self.assertEqual(self.run_with(spec_path, fake, really=False), {"dry_run": True, "approve": self.code(spec_path)})
        self.assertEqual([r.get_method() for r in fake.calls], ["GET"])
        self.assertIn("--- image alt text ---\nKiedy przestać dokładać blokady", self.out)
        self.assertIn("WARNING (heuristic, Kamil decides): \"text\" has a link", self.out)
        self.assertFalse((spec_path.parent / "linkedin.published.json").exists())

    def test_publish_uploads_the_image_posts_it_with_alt_text_and_comments(self):
        spec_path = self.image_post()
        fake = Fake(ME, IMG_INIT, UP, POST, COMMENT)
        rec = self.run_with(spec_path, fake)
        self.assertEqual([(r.get_method(), r.full_url.split("?")[0].replace(linkedin.API, "")) for r in fake.calls], [
            ("GET", "/v2/userinfo"), ("POST", "/rest/images"), ("PUT", "https://www.linkedin.com/dms-uploads/img"),
            ("POST", "/rest/posts"), ("POST", "/v2/socialActions/urn%3Ali%3Ashare%3A42/comments")])
        self.assertEqual(fake.calls[2].data, PNG)
        post = json.loads(fake.calls[3].data)
        self.assertEqual(post["content"], {"media": {"id": "urn:li:image:I1", "altText": "Kiedy przestać dokładać blokady"}})
        self.assertNotIn("#", post["commentary"].replace("\\#", ""))  # no hashtags in this spec
        self.assertEqual(json.loads(fake.calls[4].data)["message"]["text"], IMG_SPEC["first_comment"])
        saved = json.loads((spec_path.parent / "linkedin.published.json").read_text())
        self.assertEqual((saved["state"], saved["kind"], saved["media"], saved["comment"]), ("published", "image", "urn:li:image:I1", 201))
        self.assertEqual(rec["url"], "https://www.linkedin.com/feed/update/urn:li:share:42/")

    def test_no_alt_text_file_posts_without_alt_text(self):
        spec_path, fake = self.image_post(alt=None), Fake(ME, IMG_INIT, UP, POST, COMMENT)
        self.run_with(spec_path, fake)
        self.assertEqual(json.loads(fake.calls[3].data)["content"], {"media": {"id": "urn:li:image:I1"}})

    def test_the_approval_covers_the_image_and_its_alt_text(self):
        for what, change in {"image": lambda d: (d / "grafika.png").write_bytes(PNG + b"!"),
                             "alt text": lambda d: (d / "grafika.txt").write_text("Inny opis", encoding="utf-8")}.items():
            with self.subTest(what=what):
                spec_path = self.image_post(name=what.replace(" ", "-"))
                code = self.code(spec_path)
                change(spec_path.parent)
                fake = Fake()
                with self.assertRaisesRegex(ValueError, "--approve"): self.run_with(spec_path, fake, approve=code)
                self.assertEqual(fake.calls, [])

    def test_a_bad_or_missing_image_stops_before_any_call(self):
        for want, setup in {"grafika.png missing": lambda d: (d / "grafika.png").unlink(),
                            "not a PNG, JPEG or GIF": lambda d: (d / "grafika.png").write_bytes(b"<html>"),
                            "pixels": lambda d: (d / "grafika.png").write_bytes(PNG[:16] + (9000).to_bytes(4, "big") * 2 + PNG[24:])}.items():
            with self.subTest(want=want):
                spec_path = self.image_post(name=want.split()[0].replace(",", ""))
                setup(spec_path.parent)
                fake = Fake()
                with self.assertRaisesRegex(ValueError, want): self.run_with(spec_path, fake, really=False, approve=None)
                self.assertEqual(fake.calls, [])

    def test_a_refused_upload_or_post_leaves_no_record(self):
        out_of_domain = (200, {}, {"value": {"uploadUrl": "https://evil.example/x", "image": "urn:li:image:I1"}})
        for want, fake in {"outside linkedin.com": Fake(ME, out_of_domain),
                           "HTTP 422": Fake(ME, IMG_INIT, UP, http(422))}.items():  # e.g. the image not ready yet: rerun is safe
            with self.subTest(want=want):
                spec_path = self.image_post(name=want.split()[0])
                with self.assertRaisesRegex(ValueError, want): self.run_with(spec_path, fake)
                self.assertFalse((spec_path.parent / "linkedin.published.json").exists())
                self.assertEqual(list(self.seen.glob("*")) if self.seen.exists() else [], [])


class VideoPostTest(Base):
    def test_publish_uploads_the_parts_finalizes_waits_and_posts(self):
        spec_path = self.video_post()
        fake = Fake(ME, vid_init(), part("e1"), part("e2"), FINAL, PROC, AVAIL, POST, COMMENT)
        self.run_with(spec_path, fake, wait_s=5, step_s=0)
        self.assertEqual([(r.get_method(), r.full_url.split("?")[0].replace(linkedin.API, "")) for r in fake.calls], [
            ("GET", "/v2/userinfo"), ("POST", "/rest/videos"),
            ("PUT", "https://www.linkedin.com/dms-uploads/v/0"), ("PUT", "https://www.linkedin.com/dms-uploads/v/1"),
            ("POST", "/rest/videos"), ("GET", "/rest/videos/urn%3Ali%3Avideo%3AV1"), ("GET", "/rest/videos/urn%3Ali%3Avideo%3AV1"),
            ("POST", "/rest/posts"), ("POST", "/v2/socialActions/urn%3Ali%3Ashare%3A42/comments")])
        init = json.loads(fake.calls[1].data)["initializeUploadRequest"]
        self.assertEqual((init["fileSizeBytes"], init["owner"]), (len(MP4), "urn:li:person:abc"))
        self.assertEqual(fake.calls[2].data + fake.calls[3].data, MP4)  # the parts are exactly the approved bytes
        self.assertEqual(json.loads(fake.calls[4].data), {"finalizeUploadRequest": {
            "video": "urn:li:video:V1", "uploadToken": "tok", "uploadedPartIds": ["e1", "e2"]}})
        post = json.loads(fake.calls[7].data)
        self.assertEqual(post["content"], {"media": {"id": "urn:li:video:V1", "title": "Trzy słowa"}})
        self.assertTrue(post["commentary"].endswith("#AI"))
        saved = json.loads((spec_path.parent / "linkedin.published.json").read_text())
        self.assertEqual((saved["kind"], saved["media"], saved["comment"]), ("video", "urn:li:video:V1", 201))

    def test_parts_that_do_not_cover_the_file_are_never_uploaded(self):
        for want, parts in {"gap or overlap": ((0, CUT - 1), (CUT + 1, len(MP4) - 1)),
                            f"cover {CUT} bytes": ((0, CUT - 1),)}.items():
            with self.subTest(want=want):
                spec_path = self.video_post(name=f"s{len(parts)}")
                fake = Fake(ME, vid_init(parts))
                with self.assertRaisesRegex(ValueError, want): self.run_with(spec_path, fake, wait_s=5, step_s=0)
                self.assertEqual([r.get_method() for r in fake.calls], ["GET", "POST"])
                self.assertFalse((spec_path.parent / "linkedin.published.json").exists())

    def test_upload_failures_before_the_post_release_the_claim(self):
        cases = {
            "without an ETag": Fake(ME, vid_init(), (200, {}, None)),
            "outside linkedin.com": Fake(ME, vid_init(host="evil.example")),
            "could not process the video .*codec": Fake(ME, vid_init(), part("e1"), part("e2"), FINAL,
                                                       (200, {}, {"status": "PROCESSING_FAILED", "processingFailureReason": "codec"})),
            "HTTP 500": Fake(ME, vid_init(), part("e1"), http(500)),
        }
        for i, (want, fake) in enumerate(cases.items()):
            with self.subTest(want=want):
                spec_path = self.video_post(name=f"f{i}")
                with self.assertRaisesRegex(ValueError, want): self.run_with(spec_path, fake, wait_s=5, step_s=0)
                self.assertNotIn(linkedin.API + "/rest/posts", [r.full_url for r in fake.calls])
                self.assertFalse((spec_path.parent / "linkedin.published.json").exists())

    def test_a_status_the_token_cannot_read_waits_then_posts(self):
        spec_path = self.video_post()
        fake = Fake(ME, vid_init(), part("e1"), part("e2"), FINAL, http(403), POST, COMMENT)
        self.run_with(spec_path, fake, wait_s=30, step_s=0)
        self.sleep.assert_called_once_with(30)
        self.assertEqual(json.loads((spec_path.parent / "linkedin.published.json").read_text())["state"], "published")

    def test_a_video_that_never_gets_ready_stops_before_the_post(self):
        spec_path = self.video_post()
        fake = Fake(ME, vid_init(), part("e1"), part("e2"), FINAL, *[PROC] * 20)
        with mock.patch.object(linkedin.time, "monotonic", side_effect=[0, 1, 99, 99]), self.assertRaisesRegex(ValueError, "still PROCESSING"):
            self.run_with(spec_path, fake, wait_s=5, step_s=0)
        self.assertNotIn(linkedin.API + "/rest/posts", [r.full_url for r in fake.calls])

    def test_a_file_outside_linkedins_limits_stops_before_any_call(self):
        for want, blob in {"bytes, LinkedIn takes": MP4[:1000], "not an MP4": b"RIFF" * 30000}.items():
            with self.subTest(want=want):
                spec_path = self.video_post(name=want.split()[0], blob=blob)
                fake = Fake()
                with self.assertRaisesRegex(ValueError, want): self.run_with(spec_path, fake, really=False, approve=None)
                self.assertEqual(fake.calls, [])

    def test_the_approval_covers_the_video_bytes_and_title(self):
        spec_path = self.video_post()
        code = self.code(spec_path)
        (self.root / "shorts" / "s01.mp4").write_bytes(MP4 + b"\0")  # the short was rendered again
        with self.assertRaisesRegex(ValueError, "--approve"): self.run_with(spec_path, Fake(), approve=code)
        spec_path.write_text(json.dumps({**VID_SPEC, "video_title": "Inny"}))
        (self.root / "shorts" / "s01.mp4").write_bytes(MP4)
        self.assertNotEqual(self.code(spec_path), code)


WARSAW = linkedin.WARSAW


def at(text):
    return datetime.datetime.fromisoformat(text).replace(tzinfo=WARSAW)


class QueueTest(Base):
    def run_due(self, fake, now, really=True, **kw):
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()) as out, \
                mock.patch("sys.stderr", io.StringIO()) as err:
            rc = linkedin.run_due(really, now=now, **kw)
        self.out, self.err = out.getvalue(), err.getvalue()
        return rc

    def add(self, spec_path, when, code=None, now="2026-11-15 12:00"):
        with mock.patch("sys.stdout", io.StringIO()):
            return linkedin.queue_add(spec_path, when, code or self.code(spec_path), now=at(now))

    def test_add_stores_warsaw_time_and_the_approval_code_after_checking_it_offline(self):
        spec_path = self.image_post()
        with mock.patch.object(linkedin, "_open", Fake()) as fake:
            item = self.add(spec_path, "2026-11-16 17:00")
        self.assertEqual(fake.calls, [])  # no token, no call
        self.assertEqual((item["when"], item["approve"]), ("2026-11-16T17:00+01:00", self.code(spec_path)))
        self.assertEqual([json.loads(x)["spec"] for x in self.queue.read_text().splitlines()], [str(spec_path.resolve())])

    def test_add_refuses_a_wrong_code_a_past_time_a_duplicate_and_a_bad_time(self):
        spec_path = self.image_post()
        with self.assertRaisesRegex(ValueError, "--approve"): self.add(spec_path, "2026-11-16 17:00", code="000000000000")
        with self.assertRaisesRegex(ValueError, "not in the future"): self.add(spec_path, "2026-11-15 11:59")
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD HH:MM"): self.add(spec_path, "jutro 17:00")
        self.add(spec_path, "2026-11-16 17:00")
        with self.assertRaisesRegex(ValueError, "already queued"): self.add(spec_path, "2026-11-17 17:00")

    def test_run_due_publishes_only_what_is_due_and_one_post_per_run(self):
        a, b, c = self.image_post("a"), self.image_post("b", spec={**IMG_SPEC, "text": TEXT + " B"}), \
            self.image_post("c", spec={**IMG_SPEC, "text": TEXT + " C"})
        self.add(a, "2026-11-16 17:00"); self.add(b, "2026-11-16 17:00"); self.add(c, "2026-11-17 17:00")
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 16:59")), 0)
        self.assertEqual(fake.calls, [])
        fake = Fake(ME, IMG_INIT, UP, POST, COMMENT)
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:05")), 0)
        self.assertEqual(len([r for r in fake.calls if r.full_url.endswith("/rest/posts")]), 1)
        self.assertEqual(json.loads((a.parent / "linkedin.published.json").read_text())["state"], "published")
        self.assertIn(f"next tick: {b.resolve()}", self.out)
        fake = Fake(ME, IMG_INIT, UP, POST, COMMENT)
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:20")), 0)  # the next tick takes b, a is done
        self.assertTrue((b.parent / "linkedin.published.json").exists())
        self.assertFalse((c.parent / "linkedin.published.json").exists())

    def test_without_publish_run_due_only_says_what_is_due(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:01"), really=False), 0)
        self.assertEqual(fake.calls, []); self.assertIn("DUE", self.out)

    def test_a_change_after_queueing_is_not_published(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        (spec_path.parent / "grafika.png").write_bytes(PNG + b"!")
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:01")), 1)
        self.assertEqual(fake.calls, []); self.assertIn("changed after Kamil's OK", self.err)
        self.assertFalse((spec_path.parent / "linkedin.published.json").exists())

    def test_a_late_item_is_reported_not_published(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 20:01")), 1)
        self.assertEqual(fake.calls, []); self.assertIn("late by more than 3 h", self.err)

    def test_a_stopped_publish_is_reported_each_run_and_never_retried(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        (spec_path.parent / "linkedin.published.json").write_text(json.dumps({"state": "unknown"}))
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:01")), 1)
        self.assertEqual(fake.calls, []); self.assertIn("stuck unknown", self.err)

    def test_a_failed_publish_fails_the_run_and_the_next_item_waits(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        self.tok.write_text("{}")  # the token is gone: named stop, nothing sent
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:01")), 1)
        self.assertEqual(fake.calls, []); self.assertIn("not a token", self.err)

    def test_a_second_run_while_one_is_running_does_nothing(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        with open(self.queue.with_name("run.lock"), "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            fake = Fake()
            self.assertEqual(self.run_due(fake, at("2026-11-16 17:01")), 0)
        self.assertEqual(fake.calls, []); self.assertIn("another linkedin.py run-due", self.out)

    def test_a_post_that_may_be_live_still_uses_the_runs_one_post(self):
        a, b = self.image_post("a"), self.image_post("b", spec={**IMG_SPEC, "text": TEXT + " B"})
        self.add(a, "2026-11-16 17:00"); self.add(b, "2026-11-16 17:00")
        fake = Fake(ME, IMG_INIT, UP, http(502))  # the post call of a: outcome unknown
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:01")), 1)
        self.assertEqual(len([r for r in fake.calls if r.full_url.endswith("/rest/posts")]), 1)  # b did not follow within seconds
        self.assertIn(f"next tick: {b.resolve()}", self.out)
        fake = Fake(ME, IMG_INIT, UP, POST, COMMENT)
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:16")), 1)  # a is reported stuck, b goes
        self.assertIn("stuck unknown", self.err)
        self.assertEqual(json.loads((b.parent / "linkedin.published.json").read_text())["state"], "published")

    def test_remove_is_refused_while_a_run_publishes_and_an_edited_queue_wins(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        real = linkedin.prepare
        def prepare(p):  # Kamil tries queue remove while this tick works, then edits the queue file by hand
            with self.assertRaisesRegex(ValueError, "publishing right now"): linkedin.queue_remove(spec_path)
            self.queue.write_text("")
            return real(p)
        fake = Fake()
        with mock.patch.object(linkedin, "prepare", prepare):
            self.assertEqual(self.run_due(fake, at("2026-11-16 17:01")), 0)
        self.assertEqual(fake.calls, []); self.assertIn("left the queue", self.out)

    def test_a_stop_between_the_post_and_its_record_waits_for_the_record(self):
        import signal
        old = signal.signal(signal.SIGTERM, linkedin._terminate); self.addCleanup(signal.signal, signal.SIGTERM, old)
        spec_path = self.image_post()
        def post(req):  # systemd stops the run while the post call is on its way
            os.kill(os.getpid(), signal.SIGTERM)
            return POST
        with self.assertRaises(SystemExit): self.run_with(spec_path, Fake(ME, IMG_INIT, UP, post, COMMENT))
        saved = json.loads((spec_path.parent / "linkedin.published.json").read_text())
        self.assertEqual((saved["state"], saved["post"]), ("published", "urn:li:share:42"))  # the id is on disk, not lost

    def test_a_video_outside_the_posts_tree_is_refused(self):
        spec_path = self.video_post(spec={**VID_SPEC, "video": "/etc/../tmp/private.mp4"})
        with self.assertRaisesRegex(ValueError, "outside"): self.run_with(spec_path, Fake(), really=False, approve=None)

    def test_times_are_warsaw_wall_clock_and_a_missing_hour_is_refused(self):
        self.assertEqual(linkedin.parse_when("2026-11-16 17:00").isoformat(), "2026-11-16T17:00:00+01:00")
        self.assertEqual(linkedin.parse_when("2026-07-01 17:00").isoformat(), "2026-07-01T17:00:00+02:00")
        self.assertEqual(linkedin.parse_when("2026-11-16T16:00+00:00").isoformat(), "2026-11-16T16:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "does not exist"): linkedin.parse_when("2027-03-28 02:30")

    def test_sigterm_during_the_upload_releases_the_claim(self):
        spec_path = self.image_post()
        with self.assertRaises(SystemExit): linkedin._terminate(15, None)
        def killed(req): raise SystemExit(143)  # what _terminate raises when systemd stops the run mid-upload
        with self.assertRaises(SystemExit): self.run_with(spec_path, Fake(ME, IMG_INIT, killed))
        self.assertFalse((spec_path.parent / "linkedin.published.json").exists())
        self.assertEqual(list(self.seen.glob("*")), [])

    def test_a_refusal_that_keeps_coming_stops_after_max_attempts(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        for i in range(linkedin.MAX_ATTEMPTS):
            fake = Fake(ME, IMG_INIT, UP, http(422))  # LinkedIn refuses the post: claim released, item still due
            self.assertEqual(self.run_due(fake, at(f"2026-11-16 17:{i * 15 + 1:02d}")), 1)
        fake = Fake()
        self.assertEqual(self.run_due(fake, at("2026-11-16 17:50")), 1)
        self.assertEqual(fake.calls, []); self.assertIn("3 failed publish attempts", self.err)
        with mock.patch("sys.stdout", io.StringIO()): linkedin.queue_remove(spec_path)
        self.assertEqual(linkedin._attempts(), {})  # remove + add starts again

    def test_no_network_after_a_wake_up_does_not_use_an_attempt(self):
        spec_path = self.image_post(); self.add(spec_path, "2026-11-16 17:00")
        for i in range(linkedin.MAX_ATTEMPTS + 1):
            fake = Fake(urllib.error.URLError("Temporary failure in name resolution"))  # the author call, before any upload
            self.assertEqual(self.run_due(fake, at(f"2026-11-16 17:{i * 15 + 1:02d}")), 1)
        self.assertEqual(linkedin._attempts(), {})
        self.assertFalse((spec_path.parent / "linkedin.published.json").exists())

    def test_main_turns_sigterm_into_systemexit(self):
        import signal
        old = signal.getsignal(signal.SIGTERM); self.addCleanup(signal.signal, signal.SIGTERM, old)
        with mock.patch("sys.stdout", io.StringIO()): linkedin.main(["queue", "list"])
        self.assertIs(signal.getsignal(signal.SIGTERM), linkedin._terminate)

    def test_list_and_remove(self):
        a, b = self.image_post("a"), self.image_post("b", spec={**IMG_SPEC, "text": TEXT + " B"})
        self.add(b, "2026-11-17 17:00"); self.add(a, "2026-11-16 17:00")
        with mock.patch("sys.stdout", io.StringIO()):
            rows = linkedin.queue_list(now=at("2026-11-16 18:00"))
            self.assertEqual([(Path(it["spec"]).parent.name, st) for it, st in rows], [("a", "due"), ("b", "waiting")])
            self.assertEqual(linkedin.queue_remove(a), 1)
            with self.assertRaisesRegex(ValueError, "not in"): linkedin.queue_remove(a)
        self.assertEqual([Path(it["spec"]).parent.name for it in linkedin.read_queue()], ["b"])

    def test_a_broken_queue_line_is_a_named_stop(self):
        self.queue.parent.mkdir(parents=True); self.queue.write_text('{"when": "2026-11-16 17:00"}\n')
        with self.assertRaisesRegex(ValueError, "queue.jsonl:1: not a queue item"): linkedin.read_queue()

    def test_cli(self):
        spec_path = self.image_post()
        with mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()) as err:
            self.assertEqual(linkedin.main(["queue"]), 2)
            self.assertEqual(linkedin.main(["queue", "add", str(spec_path)]), 1)
            self.assertIn("needs --at", err.getvalue())
            self.assertEqual(linkedin.main(["queue", "list"]), 0)
            self.assertEqual(linkedin.main(["check", str(spec_path)]), 0)


if __name__ == "__main__":
    unittest.main()
