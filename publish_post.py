"""publish_post.py: an article from out/blog/<slug>/ (article_check.py) -> a pull request on the kamiljan.com repo.

The site (kamiljan11/comfy-container, Lovable + Vercel) keeps blog posts as data in src/data/posts.ts; a post needs its
entry there (the film embedded as a `youtube` block after the first paragraph), its pictures in public/blog/<slug>/, a line in public/sitemap.xml and its page in e2e/og-meta.spec.ts. This
script writes all four on a new branch in a separate worktree (the main checkout is someone else's work in progress),
commits, pushes and opens the PR. Merging it is Kamil's click (nothing goes live from here); Vercel deploys after the merge.

It refuses an article that fails article_check, or that has no YouTube URL yet (the post links the film, so the film has
to be up first). Without --confirm it only prints what it would write.

  python3 publish_post.py out/blog/<slug> [--repo ~/src/comfy-container] [--words <film words json>] [--remote <push url>] [--confirm]
  push and PR go through the secrets bridge: python3 ~/infisical/infisical_bridge.py run --secrets GITHUB_Token -- ...
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from article_check import problems

REPO = Path.home() / "src" / "comfy-container"
GH_REPO = "kamiljan11/comfy-container"
BASE = "main"
PUSH_HOOKS = ("pre-push", "reference-transaction")  # hooks git runs locally during a push
PG_HOOKS = Path.home() / ".claude" / "git-hooks"  # our quality hooks (core.hooksPath of our repos): the only trusted pre-push
POSTS = "src/data/posts.ts"
ANCHOR = "export const POSTS: Post[] = ["
SITEMAP = "public/sitemap.xml"
OG_SPEC = "e2e/og-meta.spec.ts"
WEBP_Q = 82
TIMEOUT = int(os.environ.get("PUBLISH_TIMEOUT", "300"))  # seconds per git/ffmpeg/gh call: a hung network or a credential prompt ends with a message, not a hang


YT_ID = re.compile(r"^https://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})(?:[&?#].*)?$")


def youtube_id(url: str) -> str:
    """the 11-character video id from a youtube.com/watch?v= or youtu.be URL (the site validates the same rule)"""
    m = YT_ID.match(url or "")
    if not m: sys.exit(f"youtube {url!r}: not a youtube.com/watch?v= or youtu.be link")
    return m.group(1)


def with_video(blocks: list[dict], video: dict) -> list[dict]:
    """the film's player right after the first paragraph (the lead is a separate field above the blocks), so a reader
    can watch it before the first section; with no paragraph it opens the body"""
    i = next((k + 1 for k, x in enumerate(blocks) if x.get("t") == "p"), 0)
    return blocks[:i] + [video] + blocks[i:]


def ts_post(a: dict, slug: str) -> str:
    """the posts.ts entry: the article's JSON with picture paths moved to /blog/<slug>/ (JSON is a valid TS literal) and
    the film embedded as a `youtube` block (site ADR 0009: our cover as the poster, YouTube loads only after a click)"""
    web = lambda f: f"/blog/{slug}/{Path(f).with_suffix('.webp').name}"
    cover = web(a["cover"]["src"])
    vid = youtube_id(a["youtube"])
    body = {lang: {**b, "blocks": with_video([{**x, "src": web(x["src"])} if x.get("t") == "img" else x for x in b["blocks"]],
                                             {"t": "youtube", "id": vid, "title": b["title"], "poster": cover})}
            for lang, b in a["body"].items()}
    post = {"slug": slug, "date": a["date"], "cover": {**a["cover"], "src": cover}, "body": body}
    return "  " + json.dumps(post, ensure_ascii=False, indent=2).replace("\n", "\n  ") + ","


def add_post(src: str, entry: str, slug: str) -> str:
    if f'"slug": "{slug}"' in src or f'slug: "{slug}"' in src: sys.exit(f"{POSTS}: a post with slug {slug!r} is already there")
    if ANCHOR not in src: sys.exit(f"{POSTS}: {ANCHOR!r} not found; the site changed, update publish_post.py")
    return src.replace(ANCHOR, f"{ANCHOR}\n{entry}", 1)  # newest first, as the list on /blog


def add_sitemap(src: str, slug: str, date: str) -> str:
    loc = f"https://kamiljan.com/blog/{slug}"
    if loc in src: return src
    url = f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{date}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"
    if "</urlset>" not in src: sys.exit(f"{SITEMAP}: no </urlset>")
    return src.replace("</urlset>", url + "</urlset>", 1)


def add_og_page(src: str, slug: str) -> str:
    page = f'  "/blog/{slug}",'
    if page in src: return src
    last = [m for m in re.finditer(r'^  "/blog/[^"]+",$', src, re.MULTILINE)]
    if not last: sys.exit(f"{OG_SPEC}: no /blog/ page list found")
    i = last[-1].end()
    return src[:i] + "\n" + page + src[i:]


def redact(text: str, token: str | None) -> str:
    return text.replace(token, "***") if token else text


def run(*cmd: str, cwd: Path | None = None, env: dict | None = None, token: str | None = None) -> str:
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.exit(f"{' '.join(cmd[:3])}...: no answer in {TIMEOUT} s")
    if r.returncode: sys.exit(f"{' '.join(cmd[:3])}...: rc {r.returncode}\n{redact(r.stderr[-1500:], token)}")
    return r.stdout


def auth_env(token: str) -> dict:
    """the token as a git config header for the push alone (owner-only /proc/<pid>/environ), never in argv or a remote URL;
    os.environ no longer holds GITHUB_Token (main pops it), so git add/commit and the site's pre-commit hook never see it"""
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader", "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}"}


def opt(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv else None


def write_post(a: dict, folder: Path, wt: Path, pics: list[str], entry: str) -> None:
    slug = a["slug"]
    out = wt / "public" / "blog" / slug
    out.mkdir(parents=True, exist_ok=True)
    for p in pics:
        run("ffmpeg", "-v", "error", "-y", "-i", str(folder / p), "-c:v", "libwebp", "-quality", str(WEBP_Q), str(out / Path(p).with_suffix(".webp").name))
    for rel, fn in ((POSTS, lambda s: add_post(s, entry, slug)), (SITEMAP, lambda s: add_sitemap(s, slug, a["date"])), (OG_SPEC, lambda s: add_og_page(s, slug))):
        f = wt / rel
        f.write_text(fn(f.read_text(encoding="utf-8")), encoding="utf-8")


def main(argv: list[str]) -> int:
    args = [x for i, x in enumerate(argv) if not x.startswith("--") and (i == 0 or argv[i - 1] not in ("--repo", "--words", "--remote"))]
    if len(args) != 1: print(__doc__); return 2
    folder = Path(args[0])
    repo = Path(opt(argv, "--repo") or REPO)
    words = opt(argv, "--words")
    remote = opt(argv, "--remote") or f"https://github.com/{GH_REPO}.git"
    bad = problems(folder, Path(words) if words else None)
    if bad: print("\n".join(bad)); sys.exit("article_check failed: fix the article first")
    a = json.loads((folder / "article.json").read_text(encoding="utf-8"))
    slug = a["slug"]
    if not a.get("youtube"): sys.exit('"youtube" is null: the post links the film, so publish the film first and put its URL in article.json')
    pics = sorted({a["cover"]["src"], *(x["src"] for b in a["body"].values() for x in b["blocks"] if x.get("t") == "img")})
    entry = ts_post(a, slug)
    if "--confirm" not in argv:
        print(f"dry run: branch blog/{slug} on {GH_REPO}, {len(pics)} pictures -> public/blog/{slug}/*.webp, "
              f"{POSTS} +{entry.count(chr(10)) + 1} lines, {SITEMAP} +1 url, {OG_SPEC} +1 page. Add --confirm to open the PR.")
        return 0
    token = os.environ.pop("GITHUB_Token", None)  # out of the environment every child inherits (ffmpeg, git commit + the site's hooks)
    if not token: sys.exit("GITHUB_Token not set: run through python3 ~/infisical/infisical_bridge.py run --secrets GITHUB_Token -- ...")
    wt, branch = repo.parent / f"comfy-blog-{slug}", f"blog/{slug}"
    if wt.exists(): sys.exit(f"{wt} exists: a previous run left it (git -C {repo} worktree remove {wt})")
    run("git", "-C", str(repo), "fetch", "-q", "origin", BASE)
    run("git", "-C", str(repo), "worktree", "add", "-q", "-b", branch, str(wt), f"origin/{BASE}")
    pushing = False
    try:  # until the push nothing left the laptop: a failure removes the worktree and the branch, the next run starts clean
        write_post(a, folder, wt, pics, entry)
        run("git", "add", "-A", cwd=wt)
        run("git", "commit", "-q", "-m", f"feat(blog): {slug}\n\nArticle made from the film {a['youtube']} by video-pipeline (article_check passed).", cwd=wt)
        hooks = Path(run("git", "rev-parse", "--path-format=absolute", "--git-path", "hooks", cwd=wt).strip())
        # only our own quality hooks are trusted (the git-hooks folder of PG), nothing else under it: a temp dir there passed
        # as trusted (test failed when TMPDIR sat in that folder)
        # the hooks git runs on our side of a push, not only pre-push (security review 2026-11-07: reference-transaction);
        # the site's pre-commit ran before the token entered any environment, so it may stay
        live = [h for h in PUSH_HOOKS if (hooks / h).is_file() and os.access(hooks / h, os.X_OK)]
        if live and hooks.resolve() != PG_HOOKS.resolve():
            sys.exit(f"{hooks}: the site's own {', '.join(live)} (a push hook would run with the token in its environment); read it, then push by hand")
        pushing = True
        run("git", "push", "-q", remote, f"{branch}:{branch}", cwd=wt, env=auth_env(token), token=token)
    except BaseException:
        if pushing:  # a push that timed out or failed may still have landed: keep the branch, say how to check
            print(f"push of {branch} failed or hung: check {GH_REPO} for the branch; worktree {wt} kept", file=sys.stderr)
            raise
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt)], capture_output=True, check=False, timeout=TIMEOUT)
        subprocess.run(["git", "-C", str(repo), "branch", "-D", branch], capture_output=True, check=False, timeout=TIMEOUT)
        raise
    title = a["body"]["pl"]["title"]
    pr = ["gh", "pr", "create", "--repo", GH_REPO, "--base", BASE, "--head", branch, "--title", f"feat(blog): {title}"[:120],
          "--body", f"Article made from the film {a['youtube']} (video-pipeline, article_check passed).\n\nMerge = publish (Vercel deploys main)."]
    try:
        r = subprocess.run(pr, cwd=wt, env={**os.environ, "GH_TOKEN": token}, capture_output=True, text=True, check=False, timeout=TIMEOUT)
        failed = f"rc {r.returncode}\n{redact(r.stderr[-800:], token)}" if r.returncode else ""
    except subprocess.TimeoutExpired:
        r, failed = None, f"no answer in {TIMEOUT} s"
    if failed or r is None:
        sys.exit(f"gh pr create: {failed}\nbranch {branch} is pushed; open the PR by hand from {wt}, then: git -C {repo} worktree remove {wt} && git -C {repo} branch -D {branch}")
    print(f"PR: {r.stdout.strip()}  (worktree {wt}; remove it after the merge)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
