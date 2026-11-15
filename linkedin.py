#!/usr/bin/env python3
"""LinkedIn post for a video (ADR-0009, ADR-0010): text + media + first comment, from <dir>/linkedin.json.

The media decides the kind of post:
  document  "carousel" in the spec        -> <dir>/linkedin.pdf (render) through the Documents API
  video     "video": "<path>.mp4"          -> that MP4 (relative to <dir>) through the Videos API (a short)
  image     neither                        -> <dir>/grafika.png through the Images API (alt text: "alt_text" or grafika.txt)

  python3 linkedin.py check   <dir>/linkedin.json            rules of style/linkedin.json, every problem named
  python3 linkedin.py render  <dir>/linkedin.json            -> <dir>/linkedin.pdf (document posts; gfx/carousel.mjs, Chrome)
  python3 linkedin.py publish <dir>/linkedin.json [--publish --approve <code>]
  python3 linkedin.py comment <dir>/linkedin.json [--checked]  the first comment again, when it failed after the post
  python3 linkedin.py queue add <dir>/linkedin.json --at "2026-11-16 17:00" --approve <code>   (Europe/Warsaw time)
  python3 linkedin.py queue list | queue remove <dir>/linkedin.json
  python3 linkedin.py run-due [--publish]                    publish what is due (the systemd timer in deploy/)

The dry run prints an approval code (a hash of the post text, the media title or alt text, the first comment and the media
bytes). --publish needs that code: what Kamil approved is exactly what goes out; any change after the dry run changes the
code and stops the publish. A queued item carries its code; run-due publishes it only while the code still matches.

publish without --publish is a dry run: it checks the token and the author and sends nothing. With --publish it uploads
the media, posts on Kamil Jan's profile (Posts API), then the first comment, and writes <dir>/linkedin.published.json.
That record is taken before the first write to LinkedIn and kept when the post's outcome is unknown (timeout, no id),
so a rerun can never post twice; it is removed only when nothing was posted.
Token: ~/.config/linkedin/token.json from linkedin_auth.py (toRzeszów scripts, ADR-0009), scope w_member_social.
"""
from __future__ import annotations

import datetime
import fcntl
import hashlib
import http.client
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
RULES = ROOT / "style" / "linkedin.json"
TOKEN = Path(os.environ.get("VP_LINKEDIN_TOKEN", "~/.config/linkedin/token.json")).expanduser()
# one file per post text on this laptop: the same text from another folder (copy, new draft, fresh clone) is a duplicate too
SEEN = Path(os.environ.get("VP_LINKEDIN_SEEN", "~/.local/state/vp-linkedin/seen")).expanduser()
# what run-due publishes and when: one JSON object per line {"when", "spec", "approve", "added"}
QUEUE = Path(os.environ.get("VP_LINKEDIN_QUEUE", "~/.local/state/vp-linkedin/queue.jsonl")).expanduser()
WARSAW = ZoneInfo("Europe/Warsaw")  # queue times are Kamil's wall clock, like the YouTube schedule
MAX_LATE_H = 3.0  # an item more than this late (laptop off or asleep) is not published: a stale burst is worse than a miss
MAX_ATTEMPTS = 3  # publish attempts per queued item; a refusal that keeps coming must not re-upload a video every 15 min
IMAGE, ALT = "grafika.png", "grafika.txt"
AUTH = f"python3 ~/infisical/infisical_bridge.py run --secrets LINKEDIN_CLIENT_ID,LINKEDIN_CLIENT_SECRET -- python3 {ROOT}/linkedin_auth.py"
API = "https://api.linkedin.com"
PROFILE = "your LinkedIn profile (Activity > Posts)"
VERSION = "202609"  # LinkedIn-Version (YYYYMM); a version is sunset about a year after release
RESERVED = re.compile(r"([|{}@\[\]()<>#\\*_~])")  # little text format: these must be escaped to stay plain text
TAG = re.compile(r"[^\W_]+")  # a hashtag is one word: letters and digits (Polish letters too)
LINK = re.compile(r"https?://|www\.", re.IGNORECASE)
DASH = re.compile("[–—]")
FAILURES = (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, http.client.HTTPException)


def escape(text: str) -> str:
    """plain text -> little text: a reserved character becomes literal instead of markup (or a rejected post)"""
    return RESERVED.sub(r"\\\1", text)


def commentary(spec: dict) -> str:
    """the post text as the Posts API wants it: escaped text, then the hashtags as real hashtags"""
    tags = " ".join(f"#{t}" for t in spec.get("hashtags", []))
    return escape(spec["text"].strip()) + (f"\n\n{tags}" if tags else "")


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.strip().split("\n") if ln.strip()]


CTA_VARIANTS = ("question", "ps")
SPEC_KEYS = {"text", "hashtags", "first_comment", "carousel", "cta_variant", "video", "video_title", "alt_text"}
SLIDE_KEYS = {"type", "title", "sub", "body", "photo"}


def kind(spec: dict) -> str:
    """document (carousel PDF), video (an MP4, e.g. a short) or image (grafika.png next to the spec)"""
    return "document" if "carousel" in spec else "video" if "video" in spec else "image"


def _rules_for(spec: dict, rules: dict) -> tuple[dict, set[str]]:
    """the text limits for this kind of post and the rules that only warn for it"""
    extra = rules.get(kind(spec), {})
    return {**rules["text"], **extra.get("text", {})}, set(extra.get("soft", []))


def check(spec: dict, rules: dict) -> list[str]:
    """every rule the spec breaks, named; [] = fine (warnings() lists the heuristics that only warn for this kind)"""
    out = [f'unknown key "{k}" (a typo? known: {", ".join(sorted(SPEC_KEYS))})' for k in sorted(set(spec) - SPEC_KEYS)]
    if "cta_variant" in spec and spec["cta_variant"] not in CTA_VARIANTS:  # round 2 LI4: the A/B label of the closing call, never posted
        out.append(f'"cta_variant": {spec["cta_variant"]!r}, want one of {", ".join(CTA_VARIANTS)}')
    lim, soft = _rules_for(spec, rules)
    out += [msg for rule, msg in _check_text(spec, lim) if rule not in soft]
    k = kind(spec)
    if k == "document": out += _check_carousel(spec.get("carousel"), rules["carousel"])
    return out + _check_media_keys(spec, k, rules)


def warnings(spec: dict, rules: dict) -> list[str]:
    """the heuristic rules this spec breaks that do not stop this kind of post: shown in the dry run, Kamil decides"""
    lim, soft = _rules_for(spec, rules)
    return [msg for rule, msg in _check_text(spec, lim) if rule in soft]


def _check_media_keys(spec: dict, k: str, rules: dict) -> list[str]:
    out = []
    if k == "document" and "video" in spec: out.append('"carousel" and "video" together: one post has one media')
    if k != "video" and "video_title" in spec: out.append('"video_title" only goes with "video"')
    if k != "image" and "alt_text" in spec: out.append('"alt_text" only goes with an image post (no "carousel", no "video")')
    if k == "video":
        v, t = spec["video"], spec.get("video_title", "")
        if not isinstance(v, str) or not v.lower().endswith(".mp4"): out.append('"video": the path of an .mp4 file (relative to the spec folder)')
        if not isinstance(t, str) or len(t) > rules["video"]["title_max"]: out.append(f'"video_title": a text of at most {rules["video"]["title_max"]} characters')
    if k == "image" and "alt_text" in spec:
        a = spec["alt_text"]
        if not isinstance(a, str) or not 0 < len(a) <= rules["image"]["alt_max"]: out.append(f'"alt_text": a text of 1-{rules["image"]["alt_max"]} characters')
    return out


def _check_text(spec: dict, lim: dict) -> list[tuple[str, str]]:
    """(rule, message) per broken rule; the rule name lets a kind of post turn a heuristic into a warning"""
    text, out = spec.get("text"), []
    if not isinstance(text, str) or not text.strip(): return [("text", '"text" must be a non-empty text')]
    lines = _lines(text)
    if len(text.strip()) < lim["min_chars"]: out.append(("min_chars", f'"text": {len(text.strip())} characters, at least {lim["min_chars"]}'))
    tags = spec.get("hashtags", [])
    if not isinstance(tags, list) or not all(isinstance(x, str) and TAG.fullmatch(x) for x in tags):
        out.append(("hashtags", '"hashtags": a list of single words without "#" (letters and digits)'))
    elif not lim["hashtags"][0] <= len(tags) <= lim["hashtags"][1]:
        out.append(("hashtags", f'"hashtags": {len(tags)}, want {lim["hashtags"][0]}-{lim["hashtags"][1]}'))
    elif (n := len(commentary(spec))) > lim["max_chars"]:
        out.append(("max_chars", f"post: {n} characters with escapes and hashtags, at most {lim['max_chars']}"))
    if len(lines[0]) > lim["hook_max"]: out.append(("hook", f"first line (hook): {len(lines[0])} characters, at most {lim['hook_max']}"))
    if len(fold := " ".join(lines[:2])) > lim["fold_max"]:
        out.append(("fold", f"first two lines: {len(fold)} characters, at most {lim['fold_max']} (they must show before '...więcej')"))
    if LINK.search(text): out.append(("link", '"text" has a link: links go in "first_comment" (a link in the post cuts its reach)'))
    first = spec.get("first_comment")
    if not isinstance(first, str) or not first.strip() or len(first) > lim["comment_max"]:
        out.append(("first_comment", f'"first_comment": required, 1-{lim["comment_max"]} characters (the post points readers to it)'))
    for name, value in (("text", text), ("first_comment", first if isinstance(first, str) else "")):
        if DASH.search(value): out.append(("dash", f'"{name}" has an en/em dash: use a comma, a colon or a full stop'))
    return out


def _check_carousel(car: object, lim: dict) -> list[str]:
    if not isinstance(car, dict): return ['"carousel" must be an object with "title" and "slides"']
    out = []
    if not isinstance(car.get("title"), str) or not 0 < len(car["title"]) <= lim["doc_title_max"]:
        out.append(f'carousel.title: a text of 1-{lim["doc_title_max"]} characters (the document name LinkedIn shows)')
    slides = car.get("slides")
    if not isinstance(slides, list) or not lim["slides"][0] <= len(slides) <= lim["slides"][1]:
        return [*out, f'carousel.slides: {lim["slides"][0]}-{lim["slides"][1]} slides']
    for i, slide in enumerate(slides):
        at, want = f"slide {i + 1}", "cover" if i == 0 else "end" if i == len(slides) - 1 else "point"
        if not isinstance(slide, dict) or slide.get("type") != want: out.append(f'{at}: "type" must be "{want}"'); continue
        out += [f'{at}: unknown key "{k}"' for k in sorted(set(slide) - SLIDE_KEYS)]
        if not isinstance(slide.get("title"), str) or not 0 < len(slide["title"]) <= lim["title_max"]:
            out.append(f'{at}: "title" of 1-{lim["title_max"]} characters')
        for k in ("sub", "body"):
            if k in slide and (not isinstance(slide[k], str) or len(slide[k]) > lim["body_max"]):
                out.append(f'{at}: "{k}" a text of at most {lim["body_max"]} characters')
        out += [f'{at}: "{k}" has an en/em dash' for k in ("title", "sub", "body") if isinstance(slide.get(k), str) and DASH.search(slide[k])]
    return out


def load(spec_path: Path) -> tuple[dict, dict]:
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    try: spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex: raise ValueError(f"{spec_path}: not valid JSON ({ex})") from ex
    if not isinstance(spec, dict): raise TypeError(f"{spec_path}: expected a JSON object")
    return spec, rules


def render(spec_path: Path) -> Path:
    if kind(load(spec_path)[0]) != "document": raise ValueError(f"{spec_path}: render is for document posts (a \"carousel\"); image and video posts upload their file as it is")
    pdf = spec_path.parent / "linkedin.pdf"
    r = subprocess.run(["node", str(ROOT / "gfx" / "carousel.mjs"), str(spec_path), str(pdf)], capture_output=True, text=True, timeout=180, check=False)
    if r.returncode: raise ValueError((r.stderr or r.stdout).strip() or f"carousel.mjs exit {r.returncode}")
    return pdf


def _open(req: urllib.request.Request, timeout: int):
    return urllib.request.urlopen(req, timeout=timeout)


class ApiError(ValueError):
    """LinkedIn answered with an HTTP error; .code tells a rejection (4xx: nothing was created) from a server fault"""
    def __init__(self, msg: str, code: int):
        super().__init__(msg); self.code = code


def api(access: str, method: str, url: str, body: dict | None = None, raw: bytes | None = None) -> tuple[int, dict, dict]:
    """one LinkedIn call -> (status, headers, json); an HTTP error is a named ValueError with LinkedIn's own message"""
    headers = {"Authorization": f"Bearer {access}", "X-Restli-Protocol-Version": "2.0.0", "LinkedIn-Version": VERSION,
               "User-Agent": "video-pipeline linkedin.py"}
    data = raw
    if body is not None: headers["Content-Type"], data = "application/json", json.dumps(body).encode()
    if raw is not None: headers["Content-Type"] = "application/octet-stream"
    try:
        with _open(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=60) as r:
            txt = r.read().decode() or "{}"
            return r.status, {k.lower(): v for k, v in r.headers.items()}, json.loads(txt) if txt.lstrip().startswith("{") else {}
    except urllib.error.HTTPError as ex:
        ids = " ".join(f"{k}={v}" for k, v in (ex.headers or {}).items() if k.lower().startswith("x-li-"))  # for LinkedIn support
        raise ApiError(f"{method} {url.split('?')[0]}: HTTP {ex.code} {ex.read().decode(errors='replace')[:300]}"
                       + (f" [{ids}]" if ids else ""), ex.code) from ex


def token() -> str:
    """the access token, or a named stop with the renewal command when it is gone, unreadable or about to expire"""
    if not TOKEN.is_file(): raise ValueError(f"no LinkedIn token ({TOKEN}); get one: {AUTH}")
    try:
        tok = json.loads(TOKEN.read_text())
        left, access, scope = (tok["obtained_at"] + tok["expires_in"] - time.time()) / 86400, tok["access_token"], str(tok.get("scope", ""))
    except (ValueError, KeyError, TypeError) as ex:  # the file is written by linkedin_auth.py
        raise ValueError(f"{TOKEN}: not a token from linkedin_auth.py ({type(ex).__name__}: {ex}); renew: {AUTH}") from ex
    if left < 3: raise ValueError(f"LinkedIn token expires in {left:.1f} days; renew: {AUTH}  (Kamil clicks Allow)")
    if "w_member_social" not in scope: raise ValueError(f"token scope {scope!r} has no w_member_social; renew: {AUTH}")
    print(f"token: ~{left:.0f} days left")
    return access


def _pdf_pages(blob: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", blob))


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _save(done: Path, rec: dict) -> None:
    """whole file or the old one: a crash mid-write must not lose the post id"""
    tmp = done.with_suffix(".part")
    tmp.write_text(json.dumps(rec, indent=1))
    os.replace(tmp, done)


def _seen_key(text: str) -> Path:
    return SEEN / hashlib.sha256(text.encode()).hexdigest()[:16]


def _seen_by(text: str) -> str | None:
    """the record of an earlier publish of this exact text, from any folder"""
    try: return json.loads(_seen_key(text).read_text()).get("record", "?")
    except FileNotFoundError: return None
    except (OSError, ValueError): return "unreadable"


def _claim(done: Path, text: str) -> dict:
    """the record and the text are taken (O_EXCL) before the first call that writes to LinkedIn: two runs, or the same
    text from two folders, cannot both post"""
    try:
        with open(done, "x") as f: f.write(json.dumps({"state": "pending", "at": _now()}))
    except FileExistsError:
        raise ValueError(_taken(done)) from None
    SEEN.mkdir(parents=True, exist_ok=True)
    try:
        with open(_seen_key(text), "x") as f: f.write(json.dumps({"record": str(done), "at": _now()}))
    except FileExistsError:
        done.unlink()
        raise ValueError(f"this post text was already published or is being published from {_seen_by(text)}; "
                         f"check {PROFILE}") from None
    return {"state": "pending", "seen": str(_seen_key(text))}


def _release(done: Path, rec: dict) -> None:
    """nothing was posted: both claims go, a rerun is safe"""
    done.unlink(missing_ok=True)
    Path(rec["seen"]).unlink(missing_ok=True)


def _taken(done: Path) -> str:
    """why a second publish is refused, and the one safe next step for that state"""
    try: state = json.loads(done.read_text() or "{}").get("state", "?")
    except (OSError, ValueError): state = "unreadable"
    if state == "published":
        return f"{done} exists (state published): already published; a missing first comment: linkedin.py comment <spec>"
    return (f"{done} exists (state {state}): a publish is running or stopped mid-way, the post may be live; "
            f"check {PROFILE} and delete that file only if the post is not there")


def _sent(st: object) -> bool:
    return isinstance(st, int) and 200 <= st < 300


def _comment(access: str, person: str, done: Path, rec: dict) -> dict:
    """the approved first comment (from the record) under the recorded post; its result goes into the record either way"""
    rec["comment"] = "UNKNOWN sending (the run stopped while the comment was on its way)"
    _save(done, rec)  # a kill or Ctrl-C mid-call leaves UNKNOWN, never a state that looks safe to resend
    text = rec["first_comment"]
    try:
        st, _, _ = api(access, "POST", f"{API}/v2/socialActions/{urllib.parse.quote(rec['post'], safe='')}/comments",
                       {"actor": person, "message": {"text": text}})
        rec["comment"] = st
    except ApiError as ex:  # 4xx: refused, nothing under the post; 5xx: it may be there
        rec["comment"] = f"{'FAILED' if 400 <= ex.code < 500 else 'UNKNOWN'} {ex}"
    except FAILURES as ex:  # a timeout may come after LinkedIn added the comment
        rec["comment"] = f"UNKNOWN {type(ex).__name__}: {ex}"
    _save(done, rec)
    print(f"first comment: {rec['comment']}")
    return rec


def _linkedin_url(url: str) -> str:
    """an upload URL from LinkedIn must stay on linkedin.com: the media and the token go there"""
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or not (u.hostname or "").endswith(".linkedin.com"): raise ValueError(f"upload URL outside linkedin.com: {url[:80]}")
    return url


def _wait_ready(access: str, coll: str, urn: str, wait_s: float, step_s: float, blind_s: float | None = None) -> None:
    """poll /rest/<coll>/<urn> until AVAILABLE; blind_s: a 403 on the read (a w_member_social token may not read the
    asset) waits that long instead and lets the post call find out"""
    deadline, status = time.monotonic() + wait_s, ""
    while status != "AVAILABLE":
        try:
            _, _, d = api(access, "GET", f"{API}/rest/{coll}/{urllib.parse.quote(urn, safe='')}")
        except ApiError as ex:
            if blind_s is None or ex.code != 403: raise
            print(f"{urn}: status not readable with this token (HTTP 403), waiting {blind_s:.0f} s before the post")
            time.sleep(blind_s); return
        status = d.get("status", "")
        if status == "PROCESSING_FAILED":
            why = d.get("processingFailureReason")
            raise ValueError(f"LinkedIn could not process the {coll[:-1]} ({urn})" + (f": {why}" if why else ""))
        if status != "AVAILABLE":
            if time.monotonic() > deadline: raise ValueError(f"{urn} still {status or 'unknown'} after {wait_s:.0f} s; nothing was posted, run publish again")
            time.sleep(step_s)


def _upload_document(access: str, person: str, blob: bytes, wait_s: float, step_s: float) -> str:
    """PDF -> document URN once LinkedIn has processed it; nothing is posted here"""
    _, _, init = api(access, "POST", f"{API}/rest/documents?action=initializeUpload", {"initializeUploadRequest": {"owner": person}})
    up, doc = _linkedin_url(init["value"]["uploadUrl"]), init["value"]["document"]
    st, _, _ = api(access, "PUT", up, raw=blob)
    print(f"upload PDF: {st} {doc}")
    _wait_ready(access, "documents", doc, wait_s, step_s)
    return doc


def _upload_image(access: str, person: str, blob: bytes, wait_s: float, step_s: float) -> str:
    """PNG/JPEG/GIF -> image URN. No status poll: a w_member_social token cannot GET /rest/images (Images API docs,
    2026-11); an image is ready after the PUT, and a post that comes too early is refused (4xx: claim released, rerun)"""
    _, _, init = api(access, "POST", f"{API}/rest/images?action=initializeUpload", {"initializeUploadRequest": {"owner": person}})
    up, img = _linkedin_url(init["value"]["uploadUrl"]), init["value"]["image"]
    st, _, _ = api(access, "PUT", up, raw=blob)
    print(f"upload image: {st} {img}")
    return img


def _upload_video(access: str, person: str, blob: bytes, wait_s: float, step_s: float) -> str:
    """MP4 -> video URN: initializeUpload, one PUT per part (byte ranges from LinkedIn), finalizeUpload with the parts'
    ETags in order, then wait until AVAILABLE; nothing is posted here"""
    _, _, init = api(access, "POST", f"{API}/rest/videos?action=initializeUpload", {"initializeUploadRequest": {
        "owner": person, "fileSizeBytes": len(blob), "uploadCaptions": False, "uploadThumbnail": False}})
    v = init["value"]
    video, parts = v["video"], sorted(v["uploadInstructions"], key=lambda p: p["firstByte"])
    offset = 0
    for p in parts:  # the ranges must cover the file exactly once, or the finalized video is not the approved bytes
        if p["firstByte"] != offset or p["lastByte"] < p["firstByte"]: raise ValueError(f"{video}: upload parts do not cover the file (gap or overlap at byte {offset})")
        offset = p["lastByte"] + 1
    if offset != len(blob): raise ValueError(f"{video}: upload parts cover {offset} bytes, the file has {len(blob)}")
    etags = []
    for i, p in enumerate(parts):
        st, hd, _ = api(access, "PUT", _linkedin_url(p["uploadUrl"]), raw=blob[p["firstByte"]:p["lastByte"] + 1])
        if not hd.get("etag"): raise ValueError(f"{video}: part {i + 1}/{len(parts)} uploaded (HTTP {st}) without an ETag")
        etags.append(hd["etag"].strip('"'))
    print(f"upload video: {len(parts)} part(s) {video}")
    api(access, "POST", f"{API}/rest/videos?action=finalizeUpload", {"finalizeUploadRequest": {
        "video": video, "uploadToken": v.get("uploadToken", ""), "uploadedPartIds": etags}})
    # a token that cannot read the status waits BLIND_S: a post on a video still processing is refused (4xx: claim released,
    # the next run-due tick retries); one that LinkedIn later fails to process stays a broken post (ADR-0010 › Ryzyka)
    _wait_ready(access, "videos", video, wait_s, step_s, blind_s=min(wait_s, BLIND_S))
    return video


UPLOAD = {"document": _upload_document, "image": _upload_image, "video": _upload_video}
WAIT_S = {"document": 120, "image": 0, "video": 900}  # how long LinkedIn may take to process the upload
BLIND_S = 180  # video status not readable with this token: wait this long before the post (a 30-90 s short transcodes in about a minute)


class Media(NamedTuple):
    kind: str
    path: Path
    blob: bytes  # read once: the approved bytes are the uploaded bytes
    title: str  # document title, image alt text or video title: public, so it is in the approval code
    about: str  # one line for the dry run


def _image_size(blob: bytes) -> tuple[int, int] | None:
    if blob[:8] == b"\x89PNG\r\n\x1a\n" and len(blob) >= 24: return int.from_bytes(blob[16:20], "big"), int.from_bytes(blob[20:24], "big")
    if blob[:4] == b"GIF8" and len(blob) >= 10: return int.from_bytes(blob[6:8], "little"), int.from_bytes(blob[8:10], "little")
    return None


def media(spec_path: Path, spec: dict, rules: dict) -> Media:
    """the file this post uploads, checked before any call: missing, stale, wrong format or out of LinkedIn's limits = named stop"""
    k, folder = kind(spec), spec_path.parent
    if k == "document":
        pdf = folder / "linkedin.pdf"
        if not pdf.is_file() or pdf.stat().st_mtime < spec_path.stat().st_mtime: raise ValueError(f"{pdf} missing or older than the spec: run linkedin.py render first")
        blob = pdf.read_bytes()
        if (n := _pdf_pages(blob)) != len(spec["carousel"]["slides"]): raise ValueError(f"{pdf}: {n} pages, the spec has {len(spec['carousel']['slides'])} slides")
        return Media(k, pdf, blob, spec["carousel"]["title"], f"PDF {pdf.name} {n} pages")
    if k == "image":
        img = folder / IMAGE
        if not img.is_file(): raise ValueError(f"{img} missing: an image post needs {IMAGE} next to the spec")
        blob = img.read_bytes()
        if not (blob[:8] == b"\x89PNG\r\n\x1a\n" or blob[:3] == b"\xff\xd8\xff" or blob[:4] == b"GIF8"): raise ValueError(f"{img}: not a PNG, JPEG or GIF")
        size = _image_size(blob)
        if size and size[0] * size[1] >= rules["image"]["max_pixels"]: raise ValueError(f"{img}: {size[0]}x{size[1]} pixels, LinkedIn takes fewer than {rules['image']['max_pixels']}")
        alt = spec.get("alt_text") or ((folder / ALT).read_text(encoding="utf-8").strip() if (folder / ALT).is_file() else "")
        if len(alt) > rules["image"]["alt_max"]: raise ValueError(f"{folder / ALT}: alt text {len(alt)} characters, at most {rules['image']['alt_max']}")
        return Media(k, img, blob, alt, f"image {img.name}" + (f" {size[0]}x{size[1]}" if size else "") + f", {len(blob) // 1024} KB")
    vid = (folder / spec["video"]).resolve()
    if not vid.is_relative_to(folder.resolve().parent):  # the spec folder or a sibling (../s01.mp4), never any MP4 on the laptop
        raise ValueError(f"{vid}: outside {folder.resolve().parent}; put the video next to the spec folder")
    if not vid.is_file(): raise ValueError(f"{vid} missing (\"video\" in {spec_path})")
    lim, n = rules["video"], vid.stat().st_size
    if not lim["min_bytes"] <= n <= lim["max_bytes"]: raise ValueError(f"{vid}: {n} bytes, LinkedIn takes {lim['min_bytes']}-{lim['max_bytes']}")
    blob = vid.read_bytes()
    if not lim["min_bytes"] <= len(blob) <= lim["max_bytes"]: raise ValueError(f"{vid}: changed while read ({len(blob)} bytes); run again")
    if blob[4:8] != b"ftyp": raise ValueError(f"{vid}: not an MP4 (no ftyp box)")
    return Media(k, vid, blob, spec.get("video_title", ""), f"video {vid}, {n / 1e6:.1f} MB")  # the full path: Kamil sees which file


def _content(m: Media, urn: str) -> dict:
    if m.kind == "image": return {"media": {"id": urn, **({"altText": m.title} if m.title else {})}}
    return {"media": {"id": urn, **({"title": m.title} if m.title else {})}}


def approval(spec: dict, blob: bytes, title: str | None = None) -> str:
    """short code over everything the post makes public: text, media title (document title, alt text, video title), first
    comment, media bytes; title None = the document title (document posts, the codes printed before ADR-0010 stay valid)"""
    parts = (commentary(spec), spec["carousel"]["title"] if title is None else title, spec["first_comment"])
    return hashlib.sha256(b"\0".join(x.encode() for x in parts) + b"\0" + blob).hexdigest()[:12]


def _author(access: str) -> str:
    _, _, me = api(access, "GET", f"{API}/v2/userinfo")
    print(f"author: {me.get('name')} urn:li:person:{me['sub']}")
    return f"urn:li:person:{me['sub']}"


def _post(access: str, done: Path, rec: dict, body: dict) -> str:
    """POST /rest/posts -> post URN; refused (4xx) removes the claim, any unclear outcome leaves state unknown"""
    def unknown(why: str) -> ValueError:
        _save(done, {**rec, "state": "unknown", "error": why})
        return ValueError(f"post: {why}; it may be live: check {PROFILE}, then delete {done} only if it is not there")
    try:
        st, hd, _ = api(access, "POST", f"{API}/rest/posts", body)
    except ApiError as ex:
        if 400 <= ex.code < 500:  # LinkedIn refused the post: nothing is live, a rerun is safe
            _release(done, rec); raise
        raise unknown(str(ex)) from ex
    except BaseException as ex:  # a timeout may come after LinkedIn created the post: keep the record
        raise unknown(f"{type(ex).__name__}: {ex}") from ex
    if not hd.get("x-restli-id"): raise unknown(f"HTTP {st}, no post id")  # errors (4xx/5xx) raised in api() already
    return hd["x-restli-id"]


def prepare(spec_path: Path) -> tuple[dict, Media, str]:
    """everything checked without the network: spec rules, record, duplicate text, media file; -> spec, media, approval code"""
    spec, rules = load(spec_path)
    if problems := check(spec, rules): raise ValueError("; ".join(problems))
    done = spec_path.parent / "linkedin.published.json"
    if done.exists(): raise ValueError(_taken(done))
    if (prev := _seen_by(commentary(spec))): raise ValueError(f"this post text was already published from {prev}; check {PROFILE}")
    m = media(spec_path, spec, rules)
    return spec, m, approval(spec, m.blob, m.title)


def publish(spec_path: Path, really: bool, approve: str | None = None, wait_s: float | None = None, step_s: float = 3,
            on_upload=None) -> dict:
    """on_upload: called once just before the first upload call (run-due counts an attempt there, not on a missing network)"""
    spec, m, code = prepare(spec_path)
    done = spec_path.parent / "linkedin.published.json"
    if really and approve != code:  # checked before any call: no approval, no traffic
        raise ValueError("--publish needs --approve <code> from the dry run Kamil approved; the text, title, comment or media "
                         "changed since then, or no code was given")
    access = token()
    person, text = _author(access), commentary(spec)
    print(f"post ({m.kind}): {len(text)} characters, {m.about}")
    if not really:
        warn = warnings(spec, load(spec_path)[1])  # heuristics that do not stop this kind of post
        label = {"document": "document title", "image": "image alt text", "video": "video title"}[m.kind]
        print(f"DRY RUN, nothing sent.\n---\n{text}\n--- {label} ---\n{m.title}\n"
              f"--- first comment ---\n{spec['first_comment']}\n---\n"
              + "".join(f"WARNING (heuristic, Kamil decides): {w}\n" for w in warn)
              + f"approval code: {code}  (after Kamil's OK: linkedin.py publish {spec_path} --publish --approve {code})")
        return {"dry_run": True, "approve": code}
    rec = {**_claim(done, text), "approve": code, "kind": m.kind, "media_file": str(m.path), "first_comment": spec["first_comment"]}
    try:
        if on_upload: on_upload()
        media_urn = UPLOAD[m.kind](access, person, m.blob, WAIT_S[m.kind] if wait_s is None else wait_s, step_s)
        # from here to the saved record a stop (SIGTERM) waits: a kill between the post and its record would lose the post id
        _HOLD["on"] = True
    except BaseException:
        _release(done, rec)
        raise
    try:
        rec.update(media=media_urn, at=_now())
        if m.kind == "document": rec["document"] = media_urn  # the field name records written before ADR-0010 use
        _post_and_record(access, done, rec, m, person, text, media_urn)
    finally:
        _HOLD["on"] = False
        if _HOLD.pop("pending", None): raise SystemExit(128 + signal.SIGTERM)  # the stop that waited, now that the record is saved
    return _comment(access, person, done, rec)


def _post_and_record(access: str, done: Path, rec: dict, m: Media, person: str, text: str, media_urn: str) -> None:
    post_urn = _post(access, done, rec, {
        "author": person, "commentary": text, "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": _content(m, media_urn), "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False})
    rec.update(state="published", post=post_urn, url=f"https://www.linkedin.com/feed/update/{post_urn}/", comment=None)
    print(f"post: 201 {rec['url']}")  # before the save: if the disk write fails, the post id is still on screen
    try:
        _save(done, rec)  # before the comment: a failed comment must not lead to a second post
    except OSError as ex:  # the claim (state pending) stays on disk, so a rerun is still refused
        raise ValueError(f"the post is LIVE at {rec['url']} but {done} could not be written ({ex}); "
                         f"before anything else write this into it by hand: {json.dumps(rec, ensure_ascii=False)}") from ex


def comment(spec_path: Path, checked: bool = False) -> dict:
    """the first comment again, for a post whose comment failed (the post itself is never repeated)"""
    spec, _ = load(spec_path)
    done = spec_path.parent / "linkedin.published.json"
    with open(spec_path.parent / "linkedin.comment.lock", "w") as lock:  # two retries at once would both pass the checks below
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError(f"another linkedin.py comment is running for {spec_path}") from None
        rec = json.loads(done.read_text()) if done.is_file() else {}
        if rec.get("state") != "published": raise ValueError(f"{done}: no published post here (state {rec.get('state')!r})")
        if _sent(rec.get("comment")): raise ValueError(f"{rec['url']} already has its first comment")
        if str(rec.get("comment")).startswith("UNKNOWN") and not checked:
            raise ValueError(f"the last comment attempt may have gone through: look under {rec['url']}, then rerun with --checked if it is not there")
        if spec.get("first_comment") != rec.get("first_comment"):  # only the approved text goes out, never an edit made later
            raise ValueError(f'"first_comment" in {spec_path} differs from the one approved at publish; the approved one is in {done}')
        access = token()
        return _comment(access, _author(access), done, rec)


def parse_when(text: str) -> datetime.datetime:
    """'2026-11-16 17:00' (Europe/Warsaw wall clock) or an ISO time with an offset -> aware datetime"""
    try: at = datetime.datetime.fromisoformat(text.strip().replace(" ", "T", 1))
    except ValueError as ex: raise ValueError(f"time {text!r}: want YYYY-MM-DD HH:MM (Europe/Warsaw)") from ex
    if at.tzinfo: return at
    at = at.replace(tzinfo=WARSAW)
    if at.astimezone(datetime.UTC).astimezone(WARSAW).replace(tzinfo=None) != at.replace(tzinfo=None):
        raise ValueError(f"time {text!r} does not exist in Europe/Warsaw (the clock jumps forward that night): pick another")
    return at


class _Locked:
    """flock on a file next to the queue; blocking=False: None when someone else holds it"""
    def __init__(self, name: str, blocking: bool = True):
        self.path, self.blocking, self.f = QUEUE.with_name(name), blocking, None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.path, "w")
        try: fcntl.flock(self.f, fcntl.LOCK_EX | (0 if self.blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            self.f.close(); return None
        return self.f

    def __exit__(self, *exc):
        if self.f and not self.f.closed: self.f.close()
        return False


def read_queue() -> list[dict]:
    """the queue in time order; a broken line is a named stop, not a silently skipped post"""
    if not QUEUE.is_file(): return []
    items = []
    for n, line in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip(): continue
        try:
            it = json.loads(line); parse_when(it["when"]); str(it["spec"]); str(it["approve"])
        except (ValueError, KeyError, TypeError) as ex:
            raise ValueError(f"{QUEUE}:{n}: not a queue item ({type(ex).__name__}: {ex})") from ex
        items.append(it)
    return sorted(items, key=lambda it: parse_when(it["when"]))


def queue_add(spec_path: Path, when: str, approve: str | None, now: datetime.datetime | None = None) -> dict:
    """one post at one time, with the code of the dry run Kamil approved; checked offline (no token, no call)"""
    spec_path = spec_path.resolve()
    at, now = parse_when(when), now or datetime.datetime.now(WARSAW)
    if at <= now: raise ValueError(f"{at.isoformat(timespec='minutes')} is not in the future: publish it now with linkedin.py publish")
    _, _, code = prepare(spec_path)
    if approve != code:
        raise ValueError("queue add needs --approve <code> from the dry run Kamil approved; the text, title, comment or media "
                         "changed since then, or no code was given")
    item = {"when": at.isoformat(timespec="minutes"), "spec": str(spec_path), "approve": code, "added": _now()}
    with _Locked("queue.lock"):
        if any(it["spec"] == str(spec_path) for it in read_queue()):
            raise ValueError(f"{spec_path} is already queued (linkedin.py queue list; queue remove to change its time)")
        _write_queue([*read_queue(), item])
    print(f"queued {spec_path} at {at.astimezone(WARSAW):%Y-%m-%d %H:%M} Europe/Warsaw (approval {code})")
    return item


def _write_queue(items: list[dict]) -> None:
    """whole file or the old one (tmp + rename): a crash mid-write must not leave a line that stops every command"""
    tmp = QUEUE.with_suffix(".part")
    tmp.write_text("".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items), encoding="utf-8")
    os.replace(tmp, QUEUE)


def queue_remove(spec_path: Path) -> int:
    """only between runs: a remove while run-due publishes could not stop an upload already on its way, so it is refused"""
    spec_path = spec_path.resolve()
    with _Locked("run.lock", blocking=False) as idle:
        if idle is None: raise ValueError("a linkedin.py run-due is publishing right now; wait a minute, then queue list and remove again")
        with _Locked("queue.lock"):
            items = read_queue()
            keep = [it for it in items if it["spec"] != str(spec_path)]
            if len(keep) == len(items): raise ValueError(f"{spec_path} is not in {QUEUE}")
            _set_attempts(str(spec_path), None)  # a new queue add starts with fresh attempts
            _write_queue(keep)
    print(f"removed {spec_path} from the queue")
    return len(items) - len(keep)


def _attempts() -> dict:
    """{spec: publish attempts} next to the queue; unreadable = a named stop (it guards against re-upload loops)"""
    f = QUEUE.with_name("attempts.json")
    try: return json.loads(f.read_text())
    except FileNotFoundError: return {}
    except ValueError as ex: raise ValueError(f"{f}: not JSON ({ex}); fix or delete it") from ex


def _set_attempts(spec: str, n: int | None) -> None:
    att = _attempts()
    if n is None: att.pop(spec, None)
    else: att[spec] = n
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    _save(QUEUE.with_name("attempts.json"), att)


def item_state(it: dict, now: datetime.datetime, max_late_h: float = MAX_LATE_H) -> str:
    """done | stuck <state> | waiting | late | due"""
    done = Path(it["spec"]).parent / "linkedin.published.json"
    if done.exists():
        try: st = json.loads(done.read_text() or "{}").get("state", "?")
        except (OSError, ValueError): st = "unreadable"
        return "done" if st == "published" else f"stuck {st}"
    at = parse_when(it["when"])
    if at > now: return "waiting"
    return "late" if (now - at).total_seconds() > max_late_h * 3600 else "due"


def queue_list(now: datetime.datetime | None = None) -> list[tuple[dict, str]]:
    now = now or datetime.datetime.now(WARSAW)
    rows = [(it, item_state(it, now)) for it in read_queue()]
    for it, st in rows: print(f"{parse_when(it['when']).astimezone(WARSAW):%Y-%m-%d %H:%M}  {st:<14} {it['approve']}  {it['spec']}")
    if not rows: print(f"queue empty ({QUEUE})")
    return rows


def _skip_reason(it: dict, st: str, max_late_h: float) -> str | None:
    """why a queued item is not published in this run (None = it may go); every reason fails the run (exit 1)"""
    if st.startswith("stuck"): return f"{st}: a publish stopped mid-way, the post may be live; check {PROFILE}"
    if st == "late": return f"late by more than {max_late_h:g} h (the laptop was off?): not published; queue remove, then queue add with a new time"
    if (n := _attempts().get(it["spec"], 0)) >= MAX_ATTEMPTS:
        return f"{n} failed publish attempts, not retried; see the journal, fix, then queue remove + queue add"
    return None


def _count_attempt(spec: str) -> None:
    with _Locked("queue.lock"):  # the same lock as queue remove, which clears the count
        _set_attempts(spec, _attempts().get(spec, 0) + 1)


def _publish_item(it: dict, really: bool) -> int:
    """one due item: code still matches, still queued, then publish -> exit code"""
    spec_path = Path(it["spec"])
    code = prepare(spec_path)[2]
    if code != it["approve"]:
        raise ValueError(f"approval code is {code} now, {it['approve']} when queued: the text, title, comment or media "
                         "changed after Kamil's OK; not published (new dry run, new OK, queue remove + queue add)")
    if not really:
        print(f"DUE {spec_path} (approval {code} matches): run-due --publish would publish it now"); return 0
    with _Locked("queue.lock"):  # a queue remove since this run read the queue wins
        if not any(q["spec"] == it["spec"] and q["approve"] == it["approve"] for q in read_queue()):
            print(f"{spec_path} left the queue during this run: not published"); return 0
    print(f"publishing {spec_path} (queued for {it['when']})")
    rec = publish(spec_path, True, it["approve"], on_upload=lambda: _count_attempt(it["spec"]))
    return 1 if isinstance(rec.get("comment"), str) else 0  # the post is up, the comment is not: linkedin.py comment <spec>


def run_due(really: bool, now: datetime.datetime | None = None, max_late_h: float = MAX_LATE_H, limit: int = 1) -> int:
    """publish the due items, at most `limit` per run (one post per timer tick, never a burst), each only while its stored
    approval code still matches the files; a late item (laptop was off) is reported, never published. -> exit code"""
    now, rc, sent = now or datetime.datetime.now(WARSAW), 0, 0
    with _Locked("run.lock", blocking=False) as held:
        if held is None:
            print("another linkedin.py run-due is running; this tick does nothing"); return 0
        with _Locked("queue.lock"): items = read_queue()
        for it in items:
            st = item_state(it, now, max_late_h)
            if st in ("done", "waiting"): continue
            if (why := _skip_reason(it, st, max_late_h)):
                print(f"SKIPPED {it['spec']}: {why}", file=sys.stderr); rc = 1; continue
            if sent >= limit:
                print(f"next tick: {it['spec']} (one post per run)"); continue
            sent += 1  # counted before the call: a publish that fails after the post may be live still uses this run's one post
            try: rc = max(rc, _publish_item(it, really))
            except FAILURES as ex:
                print(f"FAILED {it['spec']}: {type(ex).__name__}: {ex}", file=sys.stderr); rc = 1
    return rc


def _opt(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv[:-1] else None


_HOLD: dict = {"on": False}  # set between the end of an upload and the saved post record


def _terminate(signum, frame):
    """SIGTERM (systemd stop or TimeoutStartSec) -> SystemExit, so the claim of an upload that never reached the post is
    released; during _HOLD the stop waits until the post record is on disk (a flag, not a signal mask: Python runs handlers
    in the main thread whatever thread the signal hit)"""
    if _HOLD["on"]:
        _HOLD["pending"] = True; return
    raise SystemExit(128 + signum)


def main(argv: list[str]) -> int:
    signal.signal(signal.SIGTERM, _terminate)
    if not argv or argv[0] not in ("check", "render", "publish", "comment", "queue", "run-due") \
            or (argv[0] not in ("run-due", "queue") and len(argv) < 2) \
            or (argv[0] == "queue" and (len(argv) < 2 or argv[1] not in ("add", "list", "remove") or (argv[1] != "list" and len(argv) < 3))):
        print(__doc__, file=sys.stderr); return 2
    cmd = argv[0]
    try:
        if cmd == "run-due": return run_due("--publish" in argv)
        if cmd == "queue":
            if argv[1] == "list": queue_list()
            elif argv[1] == "remove": queue_remove(Path(argv[2]))
            else:
                if not (at := _opt(argv, "--at")): raise ValueError('queue add needs --at "YYYY-MM-DD HH:MM" (Europe/Warsaw)')
                queue_add(Path(argv[2]), at, _opt(argv, "--approve"))
            return 0
        spec_path = Path(argv[1])
        if cmd == "comment":
            return 0 if _sent(comment(spec_path, "--checked" in argv)["comment"]) else 1
        spec, rules = load(spec_path)
        if problems := check(spec, rules):
            print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
            raise ValueError(f"{len(problems)} problem(s) in {spec_path}")
        if cmd == "check":
            what = f"{len(spec['carousel']['slides'])} slides" if kind(spec) == "document" else f"{kind(spec)} post"
            print(f"OK {spec_path}: {len(commentary(spec))} characters, {what}")
            for w in warnings(spec, rules): print(f"WARNING (heuristic, Kamil decides): {w}")
        elif cmd == "render": print(render(spec_path))
        else:
            rec = publish(spec_path, "--publish" in argv, _opt(argv, "--approve"))
            if isinstance(rec.get("comment"), str): return 1  # the post is up, the comment is not (or unknown): linkedin.py comment <spec>
    except FAILURES as ex:
        print(f"FAILED linkedin {' '.join(argv[:2])}: {type(ex).__name__}: {ex}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
