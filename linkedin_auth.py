#!/usr/bin/env python3
"""LinkedIn login (OAuth 2.0, 3-legged) -> ~/.config/linkedin/token.json for linkedin.py. Run every ~60 days (no refresh token).

  python3 ~/infisical/infisical_bridge.py run --secrets LINKEDIN_CLIENT_ID,LINKEDIN_CLIENT_SECRET -- python3 linkedin_auth.py

Needs a LinkedIn developer app with "Share on LinkedIn" (w_member_social) and "Sign In with LinkedIn using OpenID Connect"
(openid profile), redirect URL http://127.0.0.1:8789/callback. Opens the consent page; after "Allow" the token is written
with mode 0600 from the first byte. Prints no secret. Same file and format as the toRzeszów copy of this script (one token per profile).
"""
from __future__ import annotations

import http.server
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

REDIRECT = "http://127.0.0.1:8789/callback"
OUT = Path(os.environ.get("VP_LINKEDIN_TOKEN", "~/.config/linkedin/token.json")).expanduser()


def save(tok: dict, out: Path = OUT) -> None:
    """token -> file readable by the owner only (created 0600, never world-readable in between)"""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)  # before the first byte: an older .part with wider rights keeps its mode on O_TRUNC
    with os.fdopen(fd, "w") as f: json.dump(tok, f)
    os.replace(tmp, out)


def main() -> None:
    cid, csec, state, got = os.environ["LINKEDIN_CLIENT_ID"], os.environ["LINKEDIN_CLIENT_SECRET"], secrets.token_urlsafe(16), {}

    class Callback(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                got["code"], msg = q["code"][0], "OK, you can close this tab."
            else:
                msg = "Error: " + str(q.get("error_description", q.get("error", ["?"])))
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
            self.wfile.write(msg.encode())

        def log_message(self, format, *args): pass

    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": REDIRECT, "state": state, "scope": "openid profile w_member_social"})
    print("LinkedIn consent page:", url)
    try:
        srv = http.server.HTTPServer(("127.0.0.1", 8789), Callback)  # bound before the consent page opens
    except OSError as ex:
        raise SystemExit(f"port 8789 is taken ({ex}): close what listens there, then run linkedin_auth.py again") from ex
    webbrowser.open(url)
    deadline = time.time() + 300
    srv.timeout = 5  # handle_request() returns every 5 s, so the 5-minute deadline is really checked
    try:
        while "code" not in got and time.time() < deadline: srv.handle_request()
    finally:
        srv.server_close()
    if "code" not in got: raise SystemExit("no authorization code within 5 min")
    body = urllib.parse.urlencode({"grant_type": "authorization_code", "code": got["code"], "redirect_uri": REDIRECT,
                                   "client_id": cid, "client_secret": csec}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=body,
                                    headers={"Content-Type": "application/x-www-form-urlencoded",
                                             "User-Agent": "video-pipeline linkedin_auth.py"}), timeout=30) as r:
            tok = json.load(r)
    except urllib.error.HTTPError as ex:
        raise SystemExit(f"token exchange: HTTP {ex.code} {ex.read().decode(errors='replace')[:300]}") from ex
    except (urllib.error.URLError, TimeoutError) as ex:  # no answer: the code is single-use, so authorize again
        raise SystemExit(f"token exchange: no answer from LinkedIn ({ex}); run linkedin_auth.py again") from ex
    tok["obtained_at"] = int(time.time())
    save(tok)
    print("token saved to", OUT, "| expires in days:", round(tok.get("expires_in", 0) / 86400, 1))


if __name__ == "__main__":
    main()
