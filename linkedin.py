#!/usr/bin/env python3
"""LinkedIn document post for a video (ADR-0009): text + PDF carousel + first comment, from <dir>/linkedin.json.

  python3 linkedin.py check   <dir>/linkedin.json            rules of style/linkedin.json, every problem named
  python3 linkedin.py render  <dir>/linkedin.json            -> <dir>/linkedin.pdf (gfx/carousel.mjs, Chrome)
  python3 linkedin.py publish <dir>/linkedin.json [--publish]

publish without --publish is a dry run: it checks the token and the author and sends nothing. With --publish it uploads
the PDF (Documents API), posts on Kamil Jan's profile (Posts API), then the first comment, and writes
<dir>/linkedin.published.json; a second publish of the same spec is refused (no duplicate posts).
Token: ~/.config/linkedin/token.json from linkedin_auth.py (toRzeszów scripts, ADR-0009), scope w_member_social.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RULES = ROOT / "style" / "linkedin.json"
TOKEN = Path(os.environ.get("VP_LINKEDIN_TOKEN", "~/.config/linkedin/token.json")).expanduser()
AUTH = "python3 ~/infisical/infisical_bridge.py run --secrets LINKEDIN_CLIENT_ID,LINKEDIN_CLIENT_SECRET -- python3 ~/Documents/toRzeszow/skrypty/linkedin_auth.py"
API = "https://api.linkedin.com"
VERSION = "202609"  # LinkedIn-Version (YYYYMM); a version is sunset about a year after release
RESERVED = re.compile(r"([|{}@\[\]()<>#\\*_~])")  # little text format: these must be escaped to stay plain text
TAG = re.compile(r"[^\W_]+")  # a hashtag is one word: letters and digits (Polish letters too)
LINK = re.compile(r"https?://|www\.", re.IGNORECASE)
DASH = re.compile("[–—]")
FAILURES = (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError)


def escape(text: str) -> str:
    """plain text -> little text: a reserved character becomes literal instead of markup (or a rejected post)"""
    return RESERVED.sub(r"\\\1", text)


def commentary(spec: dict) -> str:
    """the post text as the Posts API wants it: escaped text, then the hashtags as real hashtags"""
    tags = " ".join(f"#{t}" for t in spec.get("hashtags", []))
    return escape(spec["text"].strip()) + (f"\n\n{tags}" if tags else "")


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.strip().split("\n") if ln.strip()]


def check(spec: dict, rules: dict) -> list[str]:
    """every rule the spec breaks, named; [] = fine"""
    t, c, out = rules["text"], rules["carousel"], []
    text = spec.get("text")
    if not isinstance(text, str) or not text.strip(): return ['"text" must be a non-empty text']
    lines = _lines(text)
    if len(text.strip()) < t["min_chars"]: out.append(f'"text": {len(text.strip())} characters, at least {t["min_chars"]}')
    tags = spec.get("hashtags", [])
    if not isinstance(tags, list) or not all(isinstance(x, str) and TAG.fullmatch(x) for x in tags):
        out.append('"hashtags": a list of single words without "#" (letters and digits)')
    elif not t["hashtags"][0] <= len(tags) <= t["hashtags"][1]:
        out.append(f'"hashtags": {len(tags)}, want {t["hashtags"][0]}-{t["hashtags"][1]}')
    else:
        n = len(commentary(spec))
        if n > t["max_chars"]: out.append(f"post: {n} characters with escapes and hashtags, at most {t['max_chars']}")
    if len(lines[0]) > t["hook_max"]: out.append(f"first line (hook): {len(lines[0])} characters, at most {t['hook_max']}")
    if len(" ".join(lines[:2])) > t["fold_max"]: out.append(f"first two lines: {len(' '.join(lines[:2]))} characters, at most {t['fold_max']} (they must show before '...więcej')")
    if LINK.search(text): out.append('"text" has a link: links go in "first_comment" (a link in the post cuts its reach)')
    fc = spec.get("first_comment", "")
    if not isinstance(fc, str) or len(fc) > t["comment_max"]: out.append(f'"first_comment": a text of at most {t["comment_max"]} characters')
    for name, s in (("text", text), ("first_comment", fc if isinstance(fc, str) else "")):
        if DASH.search(s): out.append(f'"{name}" has an en/em dash: use a comma, a colon or a full stop')
    car = spec.get("carousel")
    if not isinstance(car, dict): return [*out, '"carousel" must be an object with "title" and "slides"']
    if not isinstance(car.get("title"), str) or not 0 < len(car["title"]) <= c["doc_title_max"]:
        out.append(f'carousel.title: a text of 1-{c["doc_title_max"]} characters (the document name LinkedIn shows)')
    slides = car.get("slides")
    if not isinstance(slides, list) or not c["slides"][0] <= len(slides) <= c["slides"][1]:
        return [*out, f'carousel.slides: {c["slides"][0]}-{c["slides"][1]} slides']
    for i, sp in enumerate(slides):
        at, want = f"slide {i + 1}", "cover" if i == 0 else "end" if i == len(slides) - 1 else "point"
        if not isinstance(sp, dict) or sp.get("type") != want: out.append(f'{at}: "type" must be "{want}"'); continue
        if not isinstance(sp.get("title"), str) or not 0 < len(sp["title"]) <= c["title_max"]: out.append(f'{at}: "title" of 1-{c["title_max"]} characters')
        for k in ("sub", "body"):
            if k in sp and (not isinstance(sp[k], str) or len(sp[k]) > c["body_max"]): out.append(f'{at}: "{k}" a text of at most {c["body_max"]} characters')
        for k in ("title", "sub", "body"):
            if isinstance(sp.get(k), str) and DASH.search(sp[k]): out.append(f'{at}: "{k}" has an en/em dash')
    return out


def load(spec_path: Path) -> tuple[dict, dict]:
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    try: spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex: raise ValueError(f"{spec_path}: not valid JSON ({ex})") from ex
    if not isinstance(spec, dict): raise TypeError(f"{spec_path}: expected a JSON object")
    return spec, rules


def render(spec_path: Path) -> Path:
    pdf = spec_path.parent / "linkedin.pdf"
    r = subprocess.run(["node", str(ROOT / "gfx" / "carousel.mjs"), str(spec_path), str(pdf)], capture_output=True, text=True, timeout=180, check=False)
    if r.returncode: raise ValueError((r.stderr or r.stdout).strip() or f"carousel.mjs exit {r.returncode}")
    return pdf


def _open(req: urllib.request.Request, timeout: int):
    return urllib.request.urlopen(req, timeout=timeout)


def api(token: str, method: str, url: str, body: dict | None = None, raw: bytes | None = None) -> tuple[int, dict, dict]:
    """one LinkedIn call -> (status, headers, json); an HTTP error is a named ValueError with LinkedIn's own message"""
    h = {"Authorization": f"Bearer {token}", "X-Restli-Protocol-Version": "2.0.0", "LinkedIn-Version": VERSION}
    data = raw
    if body is not None: h["Content-Type"], data = "application/json", json.dumps(body).encode()
    if raw is not None: h["Content-Type"] = "application/octet-stream"
    try:
        with _open(urllib.request.Request(url, data=data, headers=h, method=method), timeout=60) as r:
            txt = r.read().decode() or "{}"
            return r.status, {k.lower(): v for k, v in r.headers.items()}, json.loads(txt) if txt.lstrip().startswith("{") else {}
    except urllib.error.HTTPError as ex:
        raise ValueError(f"{method} {url.split('?')[0]}: HTTP {ex.code} {ex.read().decode(errors='replace')[:300]}") from ex


def token() -> str:
    """the access token, or a named stop with the renewal command when it is gone or about to expire"""
    if not TOKEN.is_file(): raise ValueError(f"no LinkedIn token ({TOKEN}); get one: {AUTH}")
    tok = json.loads(TOKEN.read_text())
    left = (tok["obtained_at"] + tok["expires_in"] - time.time()) / 86400
    if left < 3: raise ValueError(f"LinkedIn token expires in {left:.1f} days; renew: {AUTH}  (Kamil clicks Allow)")
    if "w_member_social" not in str(tok.get("scope", "")): raise ValueError(f"token scope {tok.get('scope')!r} has no w_member_social; renew: {AUTH}")
    print(f"token: ~{left:.0f} days left")
    return tok["access_token"]


def _pdf_pages(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", pdf.read_bytes()))


def publish(spec_path: Path, really: bool, wait_s: float = 120, step_s: float = 3) -> dict:
    spec, rules = load(spec_path)
    if problems := check(spec, rules): raise ValueError("; ".join(problems))
    done, pdf = spec_path.parent / "linkedin.published.json", spec_path.parent / "linkedin.pdf"
    if done.exists(): raise ValueError(f"already published ({done}): a second post would be a duplicate; delete that file only on purpose")
    if not pdf.is_file() or pdf.stat().st_mtime < spec_path.stat().st_mtime: raise ValueError(f"{pdf} missing or older than the spec: run linkedin.py render first")
    if (n := _pdf_pages(pdf)) != len(spec["carousel"]["slides"]): raise ValueError(f"{pdf}: {n} pages, the spec has {len(spec['carousel']['slides'])} slides")
    tk = token()
    _, _, me = api(tk, "GET", f"{API}/v2/userinfo")
    person = f"urn:li:person:{me['sub']}"
    text = commentary(spec)
    print(f"author: {me.get('name')} {person}\npost: {len(text)} characters, PDF {pdf.name} {n} pages")
    if not really:
        print(f"DRY RUN, nothing sent.\n---\n{text}\n--- first comment ---\n{spec.get('first_comment', '')}")
        return {"dry_run": True}
    _, _, init = api(tk, "POST", f"{API}/rest/documents?action=initializeUpload", {"initializeUploadRequest": {"owner": person}})
    up, doc = init["value"]["uploadUrl"], init["value"]["document"]
    u = urllib.parse.urlsplit(up)
    if u.scheme != "https" or not (u.hostname or "").endswith(".linkedin.com"): raise ValueError(f"upload URL outside linkedin.com: {up[:80]}")
    st, _, _ = api(tk, "PUT", up, raw=pdf.read_bytes())
    print(f"upload PDF: {st} {doc}")
    deadline, status = time.monotonic() + wait_s, ""
    while status != "AVAILABLE":
        _, _, d = api(tk, "GET", f"{API}/rest/documents/{urllib.parse.quote(doc, safe='')}")
        status = d.get("status", "")
        if status == "PROCESSING_FAILED": raise ValueError(f"LinkedIn could not process {pdf.name} ({doc})")
        if status != "AVAILABLE":
            if time.monotonic() > deadline: raise ValueError(f"{doc} still {status or 'unknown'} after {wait_s:.0f} s; nothing was posted, run publish again")
            time.sleep(step_s)
    st, hd, _ = api(tk, "POST", f"{API}/rest/posts", {
        "author": person, "commentary": text, "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"media": {"title": spec["carousel"]["title"], "id": doc}},
        "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False})
    urn = hd.get("x-restli-id")
    if st != 201 or not urn: raise ValueError(f"post: HTTP {st}, no post id")
    rec = {"post": urn, "url": f"https://www.linkedin.com/feed/update/{urn}/", "document": doc,
           "at": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"), "comment": None}
    done.write_text(json.dumps(rec, indent=1))  # before the comment: a failed comment must not lead to a second post
    print(f"post: {st} {rec['url']}")
    if spec.get("first_comment"):
        try:
            st, _, _ = api(tk, "POST", f"{API}/v2/socialActions/{urllib.parse.quote(urn, safe='')}/comments",
                           {"actor": person, "message": {"text": spec["first_comment"]}})
            rec["comment"] = st
        except FAILURES as ex:
            rec["comment"] = f"FAILED {ex}"
        done.write_text(json.dumps(rec, indent=1))
        print(f"first comment: {rec['comment']}")
    return rec


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("check", "render", "publish"):
        print(__doc__, file=sys.stderr); return 2
    cmd, spec_path = argv[0], Path(argv[1])
    try:
        spec, rules = load(spec_path)
        if problems := check(spec, rules):
            print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
            raise ValueError(f"{len(problems)} problem(s) in {spec_path}")
        if cmd == "check": print(f"OK {spec_path}: {len(commentary(spec))} characters, {len(spec['carousel']['slides'])} slides")
        elif cmd == "render": print(render(spec_path))
        else:
            rec = publish(spec_path, "--publish" in argv)
            if isinstance(rec.get("comment"), str): return 1  # the post is up, the comment is not: say so by exit code
    except FAILURES as ex:
        print(f"FAILED linkedin {cmd} {spec_path}: {type(ex).__name__}: {ex}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
