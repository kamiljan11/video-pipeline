"""linkedin.py: the rules of style/linkedin.json, little-text escaping, and publish against a fake LinkedIn (no network).

python3 -m unittest tests.test_linkedin
"""
from __future__ import annotations

import copy
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
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import linkedin  # after the path insert: the scripts are not a package

RULES = json.loads((ROOT / "style" / "linkedin.json").read_text(encoding="utf-8"))
HOOK = "95% firm nie widzi zysku z AI. Byłem w tych 95%."
SPEC = {
    "text": HOOK + "\n\nPrzez dwa lata budowałem narzędzia, które nie zarobiły ani złotówki.\n\n" + "Trzy zasady zmieniły to u mnie. " * 20,
    "hashtags": ["AI", "automatyzacja", "biznes"],
    "first_comment": "Cały film: https://youtu.be/xyz",
    "carousel": {"title": "95% firm nie widzi zysku z AI", "slides": [
        {"type": "cover", "title": "95% firm nie widzi zysku z AI", "sub": "Trzy zasady"},
        {"type": "point", "title": "Proces przed narzędziem", "body": "Policz koszt ręcznej pracy."},
        {"type": "point", "title": "Jeden mierzalny cel", "body": "Godziny albo złotówki."},
        {"type": "point", "title": "Pilotaż na 2 tygodnie", "body": "Mały zakres, prawdziwe dane."},
        {"type": "end", "title": "Cały film na YouTube", "body": "Link w pierwszym komentarzu."}]},
}


def spec(**change):
    s = copy.deepcopy(SPEC); s.update(change); return s


class CheckTest(unittest.TestCase):
    def test_a_good_spec_passes(self):
        self.assertEqual(linkedin.check(spec(), RULES), [])

    def test_every_broken_rule_is_named(self):
        slides = SPEC["carousel"]["slides"]
        cases = {
            "first line": spec(text="x" * 200 + "\n" + SPEC["text"]),
            "first two lines": spec(text="a" * 140 + "\n" + "b" * 100 + "\n" + SPEC["text"]),
            "has a link": spec(text=SPEC["text"] + " https://example.com"),
            "en/em dash": spec(text=SPEC["text"] + " a – b"),
            "hashtags\": 2": spec(hashtags=["AI", "biznes"]),
            "single words": spec(hashtags=["#AI", "biznes", "x y"]),
            "at least": spec(text=HOOK),
            "first_comment": spec(first_comment="x" * 2000),
            '"carousel" must': spec(carousel=None),
            "slides": spec(carousel={"title": "t", "slides": slides[:2]}),
            '"type" must be "end"': spec(carousel={"title": "t", "slides": slides[:4] + [slides[1]]}),
            '"title" of 1-': spec(carousel={"title": "t", "slides": [slides[0], {**slides[1], "title": "x" * 99}, *slides[2:]]}),
            "carousel.title": spec(carousel={"title": "", "slides": slides}),
        }
        for want, s in cases.items():
            with self.subTest(want=want):
                got = linkedin.check(s, RULES)
                self.assertTrue(any(want in p for p in got), got)

    def test_reserved_characters_are_escaped_and_hashtags_stay_hashtags(self):
        got = linkedin.commentary(spec(text="a (b) #c *d* @e [f] <g> |h| {i} ~j_ \\k zażółć", hashtags=["AI", "Łódź"]))
        self.assertEqual(got, "a \\(b\\) \\#c \\*d\\* \\@e \\[f\\] \\<g\\> \\|h\\| \\{i\\} \\~j\\_ \\\\k zażółć\n\n#AI #Łódź")


class Fake:
    """urlopen stand-in: answers in order, records every request"""
    def __init__(self, *answers):
        self.answers: list = list(answers)
        self.calls: list = []

    def __call__(self, req, timeout):
        self.calls.append(req)
        a: Any = self.answers.pop(0)
        if callable(a): a = a(req)  # an answer that looks at the world when the call happens
        if isinstance(a, BaseException): raise a
        status, headers, body = a
        return Reply(status, headers, body)


class Reply:
    def __init__(self, status, headers, body):
        self.status, self.headers, self.body = status, headers, body
    def __enter__(self): return self
    def __exit__(self, *exc): return False
    def read(self): return json.dumps(self.body).encode() if self.body is not None else b""


ME = (200, {}, {"sub": "abc", "name": "Kamil Jan"})
INIT = (200, {}, {"value": {"uploadUrl": "https://www.linkedin.com/dms-uploads/x", "document": "urn:li:document:D1"}})
UP = (201, {}, None)
PROC, AVAIL = (200, {}, {"status": "PROCESSING"}), (200, {}, {"status": "AVAILABLE"})
POST = (201, {"x-restli-id": "urn:li:share:42"}, None)
COMMENT = (201, {}, None)


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="li-")); self.addCleanup(shutil.rmtree, self.dir, True)
        self.spec = self.dir / "linkedin.json"; self.spec.write_text(json.dumps(SPEC), encoding="utf-8")
        self.pdf = self.dir / "linkedin.pdf"; self.pdf.write_bytes(b"%PDF " + b"/Type /Page " * 5 + b"/Type /Pages")
        now = time.time(); os.utime(self.spec, (now - 10, now - 10))
        self.tok = self.dir / "token.json"
        self.token(days=40)
        p = mock.patch.object(linkedin, "TOKEN", self.tok); p.start(); self.addCleanup(p.stop)

    def token(self, days, scope="openid,profile,w_member_social"):
        self.tok.write_text(json.dumps({"access_token": "T", "obtained_at": time.time(), "expires_in": days * 86400, "scope": scope}))

    def run_with(self, fake, really=True):
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()):
            return linkedin.publish(self.spec, really, wait_s=5, step_s=0)

    def test_a_dry_run_only_asks_who_the_author_is(self):
        fake = Fake(ME)
        self.assertEqual(self.run_with(fake, really=False), {"dry_run": True})
        self.assertEqual([r.get_method() for r in fake.calls], ["GET"])
        self.assertFalse((self.dir / "linkedin.published.json").exists())

    def test_publish_uploads_waits_posts_comments_and_records(self):
        fake = Fake(ME, INIT, UP, PROC, AVAIL, POST, COMMENT)
        rec = self.run_with(fake)
        self.assertEqual([(r.get_method(), r.full_url.split("?")[0].replace(linkedin.API, "")) for r in fake.calls], [
            ("GET", "/v2/userinfo"), ("POST", "/rest/documents"), ("PUT", "https://www.linkedin.com/dms-uploads/x"),
            ("GET", "/rest/documents/urn%3Ali%3Adocument%3AD1"), ("GET", "/rest/documents/urn%3Ali%3Adocument%3AD1"),
            ("POST", "/rest/posts"), ("POST", "/v2/socialActions/urn%3Ali%3Ashare%3A42/comments")])
        post = json.loads(fake.calls[5].data)
        self.assertEqual((post["author"], post["content"]["media"]["id"]), ("urn:li:person:abc", "urn:li:document:D1"))
        self.assertTrue(post["commentary"].endswith("#AI #automatyzacja #biznes"))
        self.assertEqual(fake.calls[5].get_header("Linkedin-version"), linkedin.VERSION)
        self.assertEqual(fake.calls[2].data, self.pdf.read_bytes())
        saved = json.loads((self.dir / "linkedin.published.json").read_text())
        self.assertEqual((saved["post"], saved["comment"], rec["url"]), ("urn:li:share:42", 201, "https://www.linkedin.com/feed/update/urn:li:share:42/"))

    def test_a_second_publish_is_refused(self):
        self.run_with(Fake(ME, INIT, UP, AVAIL, POST, COMMENT))
        with self.assertRaisesRegex(ValueError, "already published"): self.run_with(Fake())

    def test_a_failed_comment_keeps_the_record_and_fails_the_exit_code(self):
        def comment(req):  # the post is recorded before the comment is even tried: a crash here must not allow a second post
            self.assertTrue((self.dir / "linkedin.published.json").exists())
            return urllib.error.HTTPError("u", 403, "Forbidden", Message(), io.BytesIO(b'{"message":"no"}'))
        with mock.patch.object(linkedin, "_open", Fake(ME, INIT, UP, AVAIL, POST, comment)), mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(linkedin.main(["publish", str(self.spec), "--publish"]), 1)
        saved = json.loads((self.dir / "linkedin.published.json").read_text())
        self.assertEqual(saved["post"], "urn:li:share:42"); self.assertIn("HTTP 403", saved["comment"])

    def test_failures_before_the_post_are_named_and_leave_no_record(self):
        err = urllib.error.HTTPError("u", 422, "Unprocessable", Message(), io.BytesIO(b'{"message":"bad commentary"}'))
        cases = {
            "HTTP 422 .*bad commentary": Fake(ME, INIT, UP, AVAIL, err),
            "upload URL outside linkedin.com": Fake(ME, (200, {}, {"value": {"uploadUrl": "https://evil.example/x", "document": "urn:li:document:D1"}})),
            "could not process": Fake(ME, INIT, UP, (200, {}, {"status": "PROCESSING_FAILED"})),
            "no post id": Fake(ME, INIT, UP, AVAIL, (201, {}, None)),
        }
        for want, fake in cases.items():
            with self.subTest(want=want):
                with self.assertRaisesRegex(ValueError, want): self.run_with(fake)
                self.assertFalse((self.dir / "linkedin.published.json").exists())
                if want == "upload URL outside linkedin.com": self.assertEqual(len(fake.calls), 2)  # nothing sent there

    def test_a_document_that_never_gets_ready_stops_before_the_post(self):
        fake = Fake(ME, INIT, UP, *[PROC] * 50)
        with mock.patch.object(linkedin.time, "monotonic", side_effect=[0, 1, 99, 99]), self.assertRaisesRegex(ValueError, "still PROCESSING"):
            self.run_with(fake)
        self.assertNotIn("/rest/posts", [r.full_url for r in fake.calls])

    def test_the_token_and_the_pdf_are_checked_before_any_call(self):
        for want, setup in {
            "expires in": lambda: self.token(days=1),
            "no w_member_social": lambda: self.token(days=40, scope="openid,profile"),
            "older than the spec": lambda: os.utime(self.pdf, (time.time() - 100, time.time() - 100)),
            "2 pages": lambda: self.pdf.write_bytes(b"/Type /Page /Type /Page"),
        }.items():
            with self.subTest(want=want):
                self.setUp(); setup()
                fake = Fake()
                with self.assertRaisesRegex(ValueError, want): self.run_with(fake, really=False)
                self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()
