#!/usr/bin/env python3
"""manifest: every film and material in the out folder says which pipeline commit made it; old code = not done.

    python3 manifest.py stamp <folder> <part> [<part> ...]   after a step writes <folder>/<part> (run_v4: <out>/long or
                                                             <out>/shorts + the film's file; materials: <out> + "thumbnails",
                                                             "youtube", "posts", "instagram", "blog")
    python3 manifest.py check <out>                          exit 1: a part without a stamp, or made by code changed since

Kamil 2026-11-08: "inne materialy tez nowe logiki robiles czy wszystko po starych poszlo??" (out_v3: the long was rendered
with the new code, most materials were not re-made). <out>/manifest.json = {part: {commit, dirty, at}}. A part is current
when its commit has no code change against HEAD (docs/, tests/ and *.md do not count) and the tree was clean at the stamp.
Films: <out>/long/manifest.json and <out>/shorts/manifest.json, one entry per .mp4 (run_v4 moves them there).
film_check --out runs check as the item out.manifest.
"""
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOT_CODE = (":(exclude)docs", ":(exclude)tests", ":(exclude)*.md")
FILM_DIRS = ("long", "shorts")
# code that never touches a film or its checks (the materials' tools, this stamp): a change here does not make long/ or
# shorts/ stale (2026-11-10: an ig_carousel path fix would have re-rendered the 18 min long). Anything not listed counts.
NOT_FILM = ("manifest.py", "watch_render.py", "ig_carousel.py", "ig_check.py", "post_check.py", "article_check.py", "desc_check.py", "publish_post.py",
                 "utm.py", "thumb_check.py", "gfx/carousel_gfx.mjs", "gfx/post_gfx.mjs", "gfx/thumbs.mjs")
SKIP = {"manifest.json", "RAPORT.md"}  # top-level entries of out that are not made by a pipeline step


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=False, timeout=60)


def head() -> str:
    return git("rev-parse", "HEAD").stdout.strip()


def dirty() -> bool:
    """uncommitted code: a stamp from it cannot be traced back to a commit"""
    return bool(git("status", "--porcelain", "--", ".", *NOT_CODE).stdout.strip())


def code_changed(commit: str, film: bool = False) -> str | None:
    """None when the code at `commit` equals HEAD's (for a film: leaving out NOT_FILM); else a short reason"""
    if git("cat-file", "-e", f"{commit}^{{commit}}").returncode: return f"unknown commit {commit[:12]}"
    skip = [f":(exclude){f}" for f in NOT_FILM] if film else []
    r = git("diff", "--name-only", commit, "HEAD", "--", ".", *NOT_CODE, *skip)
    files = r.stdout.split()
    return f"code changed since {commit[:7]}: {', '.join(files[:4])}{' ...' if len(files) > 4 else ''}" if files else None


def load(out: Path) -> dict:
    p = out / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def stamp(out: Path, parts: list[str]) -> dict:
    m = load(out)
    at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    entry = {"commit": head(), "dirty": dirty(), "at": at}
    for p in parts: m[p.strip("/")] = entry
    (out / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return entry


def parts_in(out: Path) -> list[tuple[Path, str]]:
    """(folder whose manifest.json holds the stamp, part): each film in long/ and shorts/, every other top-level folder"""
    need = []
    for d in sorted(x for x in out.iterdir() if x.name not in SKIP and not x.name.startswith(".")):
        if d.is_dir() and d.name in FILM_DIRS: need += [(d, f.name) for f in sorted(d.glob("*.mp4"))]
        else: need.append((out, d.name))
    return need


def check(out: Path) -> list[str]:
    bad, cache, ms = [], {}, {}
    for folder, p in parts_in(out):
        if folder not in ms: ms[folder] = load(folder)
        e, name = ms[folder].get(p), p if folder == out else f"{folder.name}/{p}"
        if not e: bad.append(f"{name}: no stamp (made outside the pipeline, or before manifest.py)"); continue
        if e.get("dirty"): bad.append(f"{name}: made with uncommitted code ({e.get('commit', '')[:7]})"); continue
        c = e.get("commit", "")
        film = folder != out and folder.name in FILM_DIRS
        if (c, film) not in cache: cache[c, film] = code_changed(c, film)
        if cache[c, film]: bad.append(f"{name}: {cache[c, film]}")
    return bad


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "stamp":
        e = stamp(Path(argv[1]), argv[2:])
        print(f"manifest: {', '.join(argv[2:])} <- {e['commit'][:7]}{' (DIRTY tree)' if e['dirty'] else ''}")
        return 0
    if len(argv) == 2 and argv[0] == "check":
        bad = check(Path(argv[1]))
        for b in bad: print(b)
        print(f"manifest: {len(bad)} part(s) not made by the current code" if bad else "manifest: every part made by the current code")
        return 1 if bad else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
