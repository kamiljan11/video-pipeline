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


def spec_on_disk(path):
    return json.loads(path.read_text(encoding="utf-8"))


def spec(**change):
    s = copy.deepcopy(SPEC); s.update(change); return s


class CheckTest(unittest.TestCase):
    def test_a_good_spec_passes(self):
        self.assertEqual(linkedin.check(spec(), RULES), [])
        self.assertEqual(linkedin.check(spec(hashtags=[], cta_variant="question"), RULES), [])  # round 2: 0 hashtags, A/B label of the closing call

    def test_every_broken_rule_is_named(self):
        slides = SPEC["carousel"]["slides"]
        cases = {
            "first line": spec(text="x" * 200 + "\n" + SPEC["text"]),
            "first two lines": spec(text="a" * 140 + "\n" + "b" * 100 + "\n" + SPEC["text"]),
            "has a link": spec(text=SPEC["text"] + " https://example.com"),
            "en/em dash": spec(text=SPEC["text"] + " a – b"),
            "hashtags\": 4": spec(hashtags=["AI", "biznes", "kod", "praca"]),
            '"cta_variant": \'pytanie\'': spec(cta_variant="pytanie"),
            "single words": spec(hashtags=["#AI", "biznes", "x y"]),
            "at least": spec(text=HOOK),
            "first_comment": spec(first_comment="x" * 2000),
            '"first_comment": required': spec(first_comment=" "),
            'unknown key "first_coment"': spec(first_coment="x"),
            'slide 2: unknown key "bdy"': spec(carousel={"title": "t", "slides": [slides[0], {**slides[1], "bdy": "x"}, *slides[2:]]}),
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
        self.spec, self.pdf, self.tok = self.dir / "linkedin.json", self.dir / "linkedin.pdf", self.dir / "token.json"
        self.done = self.dir / "linkedin.published.json"
        p = mock.patch.object(linkedin, "TOKEN", self.tok); p.start(); self.addCleanup(p.stop)
        self.seen = self.dir / "seen"
        p = mock.patch.object(linkedin, "SEEN", self.seen); p.start(); self.addCleanup(p.stop)
        self.fresh()

    def fresh(self):
        """a good spec, its PDF, a 40-day token and no record: every test (and subtest) starts here"""
        self.spec.write_text(json.dumps(SPEC), encoding="utf-8")
        self.pdf.write_bytes(b"%PDF " + b"/Type /Page " * 5 + b"/Type /Pages")
        now = time.time(); os.utime(self.spec, (now - 10, now - 10))
        self.token(days=40)
        self.done.unlink(missing_ok=True)
        shutil.rmtree(self.seen, ignore_errors=True)

    def token(self, days, scope="openid,profile,w_member_social"):
        self.tok.write_text(json.dumps({"access_token": "T", "obtained_at": time.time(), "expires_in": days * 86400, "scope": scope}))

    def run_with(self, fake, really=True, approve: str | None = "dry run"):
        """approve="dry run" = the code the dry run printed for the current spec and PDF (what Kamil saw)"""
        if approve == "dry run": approve = linkedin.approval(spec_on_disk(self.spec), self.pdf.read_bytes())
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()):
            return linkedin.publish(self.spec, really, approve, wait_s=5, step_s=0)

    def test_a_dry_run_only_asks_who_the_author_is(self):
        fake = Fake(ME)
        self.assertEqual(self.run_with(fake, really=False), {"dry_run": True, "approve": linkedin.approval(SPEC, self.pdf.read_bytes())})
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

    def test_an_unknown_post_outcome_keeps_the_record_so_a_rerun_cannot_post_twice(self):
        for want, answer in {"timed out": TimeoutError("timed out"), "no post id": (201, {}, None),
                             "HTTP 502": urllib.error.HTTPError("u", 502, "x", Message(), io.BytesIO(b"{}"))}.items():
            with self.subTest(want=want):
                self.fresh()
                with self.assertRaisesRegex(ValueError, f"{want}.*may be live"): self.run_with(Fake(ME, INIT, UP, AVAIL, answer))
                saved = json.loads(self.done.read_text())
                self.assertEqual((saved["state"], saved["document"]), ("unknown", "urn:li:document:D1"))
                fake = Fake()
                with self.assertRaisesRegex(ValueError, "exists"): self.run_with(fake)
                self.assertEqual(fake.calls, [])

    def test_the_record_is_claimed_before_the_first_write_and_only_once(self):
        def init(req):  # a second run arriving now finds the claim and stops
            self.assertEqual(json.loads(self.done.read_text())["state"], "pending")
            with self.assertRaisesRegex(ValueError, "state pending"): linkedin._claim(self.done, linkedin.commentary(SPEC))
            return INIT
        self.run_with(Fake(ME, init, UP, AVAIL, POST, COMMENT))
        self.assertEqual(json.loads(self.done.read_text())["state"], "published")

    def test_comment_retries_only_the_comment_of_a_published_post(self):
        def comment():
            with mock.patch("sys.stdout", io.StringIO()): return linkedin.comment(self.spec)
        with mock.patch.object(linkedin, "_open", Fake()), self.assertRaisesRegex(ValueError, "no published post"): comment()
        self.done.write_text(json.dumps({"state": "published", "post": "urn:li:share:42", "url": "u", "comment": "FAILED x",
                                         "first_comment": SPEC["first_comment"]}))
        fake = Fake(ME, COMMENT)
        with mock.patch.object(linkedin, "_open", fake): self.assertEqual(comment()["comment"], 201)
        self.assertEqual(fake.calls[1].full_url, linkedin.API + "/v2/socialActions/urn%3Ali%3Ashare%3A42/comments")
        self.assertEqual(json.loads(fake.calls[1].data)["message"]["text"], SPEC["first_comment"])
        self.assertEqual(json.loads(self.done.read_text())["comment"], 201)
        with mock.patch.object(linkedin, "_open", Fake()), self.assertRaisesRegex(ValueError, "already has"): comment()

    def test_a_comment_that_may_have_gone_through_is_not_sent_again_unchecked(self):
        for why, answer in {"timeout": TimeoutError("timed out"),
                            "HTTP 502": urllib.error.HTTPError("u", 502, "x", Message(), io.BytesIO(b"{}"))}.items():
            with self.subTest(why=why):
                self.fresh()
                self.run_with(Fake(ME, INIT, UP, AVAIL, POST, answer))
                self.assertTrue(json.loads(self.done.read_text())["comment"].startswith("UNKNOWN"))
                with mock.patch("sys.stdout", io.StringIO()):
                    with mock.patch.object(linkedin, "_open", Fake()), self.assertRaisesRegex(ValueError, "--checked"):
                        linkedin.comment(self.spec)
                    fake = Fake(ME, COMMENT)
                    with mock.patch.object(linkedin, "_open", fake):
                        self.assertEqual(linkedin.comment(self.spec, checked=True)["comment"], 201)
                self.assertEqual(len(fake.calls), 2)

    def test_a_run_killed_while_commenting_leaves_unknown_not_a_resendable_state(self):
        with self.assertRaises(KeyboardInterrupt): self.run_with(Fake(ME, INIT, UP, AVAIL, POST, KeyboardInterrupt()))
        self.assertTrue(json.loads(self.done.read_text())["comment"].startswith("UNKNOWN"))
        with mock.patch.object(linkedin, "_open", Fake()), self.assertRaisesRegex(ValueError, "--checked"): linkedin.comment(self.spec)

    def test_comment_sends_only_the_approved_text(self):
        self.run_with(Fake(ME, INIT, UP, AVAIL, POST, urllib.error.HTTPError("u", 403, "x", Message(), io.BytesIO(b"{}"))))
        self.spec.write_text(json.dumps(spec(first_comment="Podmieniony link: https://evil.example")))
        with mock.patch.object(linkedin, "_open", Fake()), mock.patch("sys.stdout", io.StringIO()), \
                self.assertRaisesRegex(ValueError, "differs from the one approved"):
            linkedin.comment(self.spec)
        self.spec.write_text(json.dumps(SPEC))
        fake = Fake(ME, COMMENT)
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()): linkedin.comment(self.spec)
        self.assertEqual(json.loads(fake.calls[1].data)["message"]["text"], SPEC["first_comment"])

    def test_a_stopped_publish_points_at_the_profile_not_at_comment(self):
        self.done.write_text(json.dumps({"state": "pending"}))
        fake = Fake()
        with self.assertRaisesRegex(ValueError, "state pending.*may be live.*Activity > Posts.*delete that file only if"): self.run_with(fake)
        self.assertEqual(fake.calls, [])

    def test_a_record_that_cannot_be_written_after_the_post_names_the_live_post(self):
        real = linkedin._save
        def save(done, rec):
            if rec.get("state") == "published": raise OSError(28, "No space left on device")
            real(done, rec)
        with mock.patch.object(linkedin, "_save", save), self.assertRaisesRegex(ValueError, "LIVE at .*urn:li:share:42"):
            self.run_with(Fake(ME, INIT, UP, AVAIL, POST))
        self.assertEqual(json.loads(self.done.read_text())["state"], "pending")  # the claim stays: no second post
        with self.assertRaisesRegex(ValueError, "may be live"): self.run_with(Fake())

    def test_any_2xx_comment_counts_as_sent(self):
        self.done.write_text(json.dumps({"state": "published", "post": "urn:li:share:42", "url": "u", "comment": 200,
                                         "first_comment": SPEC["first_comment"]}))
        with mock.patch.object(linkedin, "_open", Fake()), self.assertRaisesRegex(ValueError, "already has"): linkedin.comment(self.spec)

    def test_two_comment_retries_at_once_send_one_comment(self):
        import fcntl
        self.done.write_text(json.dumps({"state": "published", "post": "urn:li:share:42", "url": "u", "comment": "FAILED x",
                                         "first_comment": SPEC["first_comment"]}))
        with open(self.dir / "linkedin.comment.lock", "w") as held:
            fcntl.flock(held, fcntl.LOCK_SH)  # even a shared hold must stop a retry
            fake = Fake()
            with mock.patch.object(linkedin, "_open", fake), self.assertRaisesRegex(ValueError, "another linkedin.py comment"):
                linkedin.comment(self.spec)
            self.assertEqual(fake.calls, [])

    def test_the_same_text_from_another_folder_is_a_duplicate(self):
        self.run_with(Fake(ME, INIT, UP, AVAIL, POST, COMMENT))
        other = self.dir / "copy"; other.mkdir()
        shutil.copy(self.spec, other / "linkedin.json"); shutil.copy(self.pdf, other / "linkedin.pdf")
        os.utime(other / "linkedin.json", (time.time() - 10, time.time() - 10))
        fake = Fake()
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()), \
                self.assertRaisesRegex(ValueError, f"already published from {self.done}"):
            linkedin.publish(other / "linkedin.json", True, linkedin.approval(SPEC, self.pdf.read_bytes()))
        self.assertEqual(fake.calls, []); self.assertFalse((other / "linkedin.published.json").exists())

    def test_two_folders_racing_with_the_same_text_post_once(self):
        def init(req):  # the other folder claims the text while this run is uploading
            other = self.dir / "copy"; other.mkdir()
            with self.assertRaisesRegex(ValueError, "already published or is being published"):
                linkedin._claim(other / "linkedin.published.json", linkedin.commentary(SPEC))
            self.assertFalse((other / "linkedin.published.json").exists())
            return INIT
        self.run_with(Fake(ME, init, UP, AVAIL, POST, COMMENT))

    def test_a_record_written_by_hand_from_the_message_lets_the_comment_go(self):
        real = linkedin._save
        def save(done, rec):
            if rec.get("state") == "published": raise OSError(28, "No space left on device")
            real(done, rec)
        with mock.patch.object(linkedin, "_save", save), self.assertRaises(ValueError) as ctx:
            self.run_with(Fake(ME, INIT, UP, AVAIL, POST))
        self.done.write_text(str(ctx.exception).split("by hand: ", 1)[1])  # exactly what the message says to write
        fake = Fake(ME, COMMENT)
        with mock.patch.object(linkedin, "_open", fake), mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(linkedin.comment(self.spec, checked=True)["comment"], 201)

    def test_the_record_is_replaced_whole_or_not_at_all(self):
        self.done.write_text(json.dumps({"state": "pending"}))
        with mock.patch.object(linkedin.os, "replace", side_effect=OSError("disk full")), self.assertRaises(OSError):
            linkedin._save(self.done, {"state": "published", "post": "urn:li:share:42"})
        self.assertEqual(json.loads(self.done.read_text()), {"state": "pending"})  # the old record, readable

    def test_an_api_error_names_linkedins_request_id(self):
        hdrs = Message(); hdrs["x-li-uuid"] = "abc123"
        err = urllib.error.HTTPError("u", 500, "x", hdrs, io.BytesIO(b"{}"))
        with mock.patch.object(linkedin, "_open", Fake(err)), self.assertRaisesRegex(ValueError, r"HTTP 500.*x-li-uuid=abc123"):
            linkedin.api("T", "GET", linkedin.API + "/v2/userinfo")

    def test_a_failed_comment_keeps_the_record_and_fails_the_exit_code(self):
        def comment(req):  # the post is recorded before the comment is even tried: a crash here must not allow a second post
            self.assertTrue((self.dir / "linkedin.published.json").exists())
            return urllib.error.HTTPError("u", 403, "Forbidden", Message(), io.BytesIO(b'{"message":"no"}'))
        code = linkedin.approval(SPEC, self.pdf.read_bytes())
        with mock.patch.object(linkedin, "_open", Fake(ME, INIT, UP, AVAIL, POST, comment)), mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(linkedin.main(["publish", str(self.spec), "--publish", "--approve", code]), 1)
        saved = json.loads((self.dir / "linkedin.published.json").read_text())
        self.assertEqual(saved["post"], "urn:li:share:42"); self.assertTrue(saved["comment"].startswith("FAILED"), saved["comment"])
        self.assertIn("HTTP 403", saved["comment"])

    def test_publish_needs_the_approval_code_of_exactly_this_text_comment_and_pdf(self):
        code = linkedin.approval(SPEC, self.pdf.read_bytes())
        for want, change in {"no code": lambda: None,
                             "text changed": lambda: self.spec.write_text(json.dumps(spec(text=SPEC["text"] + " Zmiana."))),
                             "comment changed": lambda: self.spec.write_text(json.dumps(spec(first_comment="Inny link: https://x"))),
                             "title changed": lambda: self.spec.write_text(json.dumps(spec(carousel={**SPEC["carousel"], "title": "Inny tytuł"}))),
                             "PDF changed": lambda: self.pdf.write_bytes(self.pdf.read_bytes() + b" ")}.items():
            with self.subTest(want=want):
                self.fresh(); change(); os.utime(self.spec, (time.time() - 10, time.time() - 10))
                fake = Fake()
                with self.assertRaisesRegex(ValueError, "--approve"): self.run_with(fake, approve=None if want == "no code" else code)
                self.assertEqual(fake.calls, []); self.assertFalse(self.done.exists())

    def test_failures_before_the_post_are_named_and_leave_no_record(self):
        err = urllib.error.HTTPError("u", 422, "Unprocessable", Message(), io.BytesIO(b'{"message":"bad commentary"}'))
        cases = {
            "HTTP 422 .*bad commentary": Fake(ME, INIT, UP, AVAIL, err),  # LinkedIn refused the post itself
            "HTTP 500": Fake(ME, INIT, urllib.error.HTTPError("u", 500, "x", Message(), io.BytesIO(b"{}"))),
            "upload URL outside linkedin.com": Fake(ME, (200, {}, {"value": {"uploadUrl": "https://evil.example/x", "document": "urn:li:document:D1"}})),
            "could not process": Fake(ME, INIT, UP, (200, {}, {"status": "PROCESSING_FAILED"})),
        }
        for want, fake in cases.items():
            with self.subTest(want=want):
                with self.assertRaisesRegex(ValueError, want): self.run_with(fake)
                self.assertFalse((self.dir / "linkedin.published.json").exists())
                self.assertEqual(list(self.seen.glob("*")) if self.seen.exists() else [], [])  # the text is free again
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
            "not a token from linkedin_auth.py": lambda: self.tok.write_text('{"access_token": "T"}'),
            "older than the spec": lambda: os.utime(self.pdf, (time.time() - 100, time.time() - 100)),
            "2 pages": lambda: self.pdf.write_bytes(b"/Type /Page /Type /Page"),
        }.items():
            with self.subTest(want=want):
                self.fresh(); setup()
                fake = Fake()
                with self.assertRaisesRegex(ValueError, want): self.run_with(fake, really=False)
                self.assertEqual(fake.calls, [])


class AuthTest(unittest.TestCase):
    def test_the_token_file_is_owner_only_from_the_start(self):
        import linkedin_auth
        out = Path(tempfile.mkdtemp(prefix="li-auth-")) / "sub" / "token.json"; self.addCleanup(shutil.rmtree, out.parent.parent, True)
        out.parent.mkdir(); out.with_suffix(".part").write_text("old"); os.chmod(out.with_suffix(".part"), 0o644)
        linkedin_auth.save({"access_token": "T", "expires_in": 1}, out)
        self.assertEqual(os.stat(out).st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(out.read_text())["access_token"], "T")


if __name__ == "__main__":
    unittest.main()
