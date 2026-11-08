#!/usr/bin/env python3
"""utm.py: the one place that tags a KamilJan.com link with where the click came from (round 2 X1).

utm_source = the platform (youtube, linkedin, instagram), utm_medium = the form (long, short, post, ig), utm_campaign = the
film (its folder date or slug). Only links to SITE get tags: other sites keep their links as written.
  python3 utm.py <url> <source> <medium> <campaign>
"""
from __future__ import annotations

import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SITE = "kamiljan.com"
URL = re.compile(r"https?://[^\s)>\]\"']+[^\s)>\]\"'.,;:!?]")  # a dot or comma ending the sentence is not the link


def ours(url: str) -> bool:
    host = urlsplit(url).netloc.lower()
    return host == SITE or host.endswith("." + SITE)


def tag(url: str, source: str, medium: str, campaign: str) -> str:
    """url with utm_source/medium/campaign set (existing utm_ values replaced, other query kept); not ours = unchanged"""
    if not ours(url): return url
    p = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.startswith("utm_")]
    q += [("utm_source", source), ("utm_medium", medium), ("utm_campaign", campaign)]
    return urlunsplit((p.scheme, p.netloc, p.path or "/", urlencode(q), p.fragment))


def untagged(text: str) -> list[str]:
    """links to SITE in text without utm_source and utm_campaign"""
    return [u for u in URL.findall(text) if ours(u) and not {"utm_source", "utm_campaign"} <= {k for k, _ in parse_qsl(urlsplit(u).query)}]


if __name__ == "__main__":
    if len(sys.argv) != 5: print(__doc__, file=sys.stderr); sys.exit(2)
    print(tag(*sys.argv[1:]))
