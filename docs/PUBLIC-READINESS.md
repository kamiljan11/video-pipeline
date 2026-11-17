# Public readiness: a stranger installs it on their own machine

**Goal (one sentence):** someone who is not the author clones this repo on a fresh Ubuntu 24.04 machine, follows the README,
and gets green tests and a working render without editing code or exposing anything of the author.

Scale: 0 = absent, 5 = works on the author's laptop, 10 = what a well-kept public tool offers (e.g. whisper.cpp, yt-dlp:
clone, documented install, tests pass on a clean box, every download pinned and checked).

| # | Dimension | Weight | Start 2026-11-17 | Target | Now | Biggest gap |
|---|---|---|---|---|---|---|
| 1 | Paths work from any checkout | 3 | 2 | 9 | 2 | `/home/kamil-jan/video-pipeline` in ~25 code sites (Python, shell, `gfx/*.mjs` imports) |
| 2 | Fonts ship with the repo | 2 | 3 | 9 | 3 | cards load Montserrat from the author's `~/.local/share/fonts` |
| 3 | Install proven on a clean machine | 3 | 0 | 8 | 0 | never installed anywhere else (README says so) |
| 4 | No secrets in history | 3 | 8 | 9 | 8 | gitleaks clean with 5 reviewed false positives; label `gitleaks-ignore-reviewed` pending |
| 5 | No private or third-party data | 2 | 7 | 8 | 7 | client theme `style/themes/cetus.json` (owner's call); author photo excluded from the licence |
| 6 | Every download pinned and checked | 2 | 7 | 9 | 7 | whisper model and YuNet without a full sha256 to compare |
| 7 | Docs written for a stranger | 2 | 6 | 8 | 6 | "Quick start" asks to symlink or grep the author's path |
| 8 | Outward actions off by default | 2 | 8 | 8 | 8 | (LinkedIn, blog PR, YouTube: dry run unless `--confirm` / `--publish`) |
| 9 | CI green on the public branch | 3 | 4 | 9 | 4 | PR #11: `secrets` waits for the label, `test` pending |

Chrome at `/usr/bin/google-chrome` stays: it is where Google's `.deb` installs it on every Ubuntu.

## Owner-only (not done by the loop)

- Merge PR #11, then the PR of this branch (`pozwol ALLOW_MERGE`).
- Label `gitleaks-ignore-reviewed` on PR #11.
- Keep or drop the client theme `cetus` before the repo is public.
- Switch the repo to public.

## Log

- 2026-11-17: rubric written; history audit of all refs: 0 recordings, transcripts, plans or env files ever committed, 0 personal data markers.
