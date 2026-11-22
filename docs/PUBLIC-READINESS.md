# Public readiness: a stranger installs it on their own machine

**Goal (one sentence):** someone who is not the author clones this repo on a fresh Ubuntu 24.04 machine, follows the README,
and gets green tests and a working render without editing code or exposing anything of the author.

Scale: 0 = absent, 5 = works on the author's laptop, 10 = what a well-kept public tool offers (e.g. whisper.cpp, yt-dlp:
clone, documented install, tests pass on a clean box, every download pinned and checked).

| # | Dimension | Weight | Start 2026-11-17 | Target | Now | Biggest gap |
|---|---|---|---|---|---|---|
| 1 | Paths work from any checkout | 3 | 2 | 9 | 9 | none in code (clean-box grep); `research_gate` default ledger stays the author's, absent = 0 items |
| 2 | Fonts ship with the repo | 2 | 3 | 9 | 9 | Montserrat VF vendored (OFL); DejaVu from apt |
| 3 | Install proven on a clean machine | 3 | 0 | 8 | 8 | clean Ubuntu 24.04 run green; no full film rendered there |
| 4 | No secrets in history | 3 | 8 | 9 | 8 | gitleaks clean with 5 reviewed false positives; label `gitleaks-ignore-reviewed` pending |
| 5 | No private or third-party data | 2 | 7 | 8 | 8 | theme `cetus` = colours only, kept (owner 2026-11-22); no logo file in the tree or history; author photo excluded from the licence |
| 6 | Every download pinned and checked | 2 | 7 | 9 | 9 | whisper.cpp source pinned by commit, not hash-checked |
| 7 | Docs written for a stranger | 2 | 6 | 8 | 8 | no docs/ARCHITECTURE.md (ADRs cover decisions) |
| 8 | Outward actions off by default | 2 | 8 | 8 | 8 | (LinkedIn, blog PR, YouTube: dry run unless `--confirm` / `--publish`) |
| 9 | CI green on the public branch | 3 | 4 | 9 | 7 | runs installers + URL check; PR #11 waits for the owner's label and merge |

Chrome at `/usr/bin/google-chrome` stays: it is where Google's `.deb` installs it on every Ubuntu.

## Owner-only (not done by the loop)

- Merge PR #11, then the PR of this branch (`pozwol ALLOW_MERGE`).
- Label `gitleaks-ignore-reviewed` on PR #11.
- Switch the repo to public.

## Log

- 2026-11-17: rubric written; history audit of all refs: 0 recordings, transcripts, plans or env files ever committed, 0 personal data markers.
- 2026-11-17: feat/portable-install: no author paths, vendored font, `install/` (ffmpeg, models, check), clean ubuntu:24.04
  run (user `tester`): check.sh "ready", npm 181/181, python 886 OK. The runs found and fixed: ffmpeg.sh never skipping a
  reinstall, Chrome's sandbox and `/dev/shm` in Docker (now told by check.sh), DejaVu fonts missing on a server image, a test
  that needed the optional matte/.venv. pg-review T2 (code, ops, product): APPROVE.
