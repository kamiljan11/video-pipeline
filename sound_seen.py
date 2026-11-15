#!/usr/bin/env python3
"""sound_seen: the sound checks of a film are not run again on the same sound and the same cut.

    python3 sound_seen.py key <work> <film> <rough.mkv> <film file> <assemble.audio.args.json> <commit>   prints the key
    python3 sound_seen.py same <work> <film> <key>    exit 0: these checks passed on this key (prints when)
    python3 sound_seen.py pass <work> <film> <key>    after sync_check, words_check, retake_check and music_check passed

Measured on the 2026-11-15 long (timeline.log): dry run 23 min of render + 53 min of checks, full render 18 + 25 min, so 78
of 123 min went to checks, and the full render heard again the sound the dry run had just passed. A card moved after that
asks for both runs once more with the sound untouched.

The key is what those checks read: the decoded sound of rough.mkv and of the film (md5 of the samples, so a file made again
is the same sound or it is not), the cut and the sound settings of the EDL (everything but its cards and the keys make_beds
writes), the plan's words (edl_<film>.txt), the retakes named on purpose, assemble's audio command and the commit. Any of
them different = another key = every check runs. The picture is not in the key: av_check and lip_check always run.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

NOT_SOUND = ("overlays", "music", "sfx")  # the cards, and the paths make_beds.py writes back (dry_run.DERIVED)


def samples_md5(path: Path) -> str:
    """md5 of the decoded sound (16-bit, as stored): the same for a file muxed again, other for any other sound"""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-f", "md5", "-"], capture_output=True, text=True, check=True, timeout=1800)
    return r.stdout.strip().removeprefix("MD5=")


def key(work: Path, film: str, rough: Path, out: Path, audio_args: Path, commit: str, md5=samples_md5) -> str:
    edl = json.loads((work / f"edl_{film}.json").read_text(encoding="utf-8"))
    plan = json.loads((work / f"plan_{film}.json").read_text(encoding="utf-8"))
    parts = {
        "commit": commit, "rough": md5(rough), "film": md5(out),
        "cut": {k: v for k, v in edl.items() if k not in NOT_SOUND},
        "words": hashlib.sha256((work / f"edl_{film}.txt").read_bytes()).hexdigest(),
        "retakes_ok": plan.get("retakes_ok"),
        "audio_args": hashlib.sha256(audio_args.read_bytes()).hexdigest() if audio_args.is_file() else None,
    }
    if not commit: raise ValueError("no commit: the checks of unknown code are not carried over")
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def record(work: Path, film: str) -> Path:
    return work / f"sound_seen_{film}.json"


def same(work: Path, film: str, k: str) -> str:
    """when the checks passed on this key, "" when they did not"""
    try: rec = json.loads(record(work, film).read_text(encoding="utf-8"))
    except (OSError, ValueError): return ""
    return str(rec.get("at", "")) if isinstance(rec, dict) and k and rec.get("key") == k else ""


def main(argv: list[str]) -> int:
    if len(argv) == 7 and argv[0] == "key":
        try: print(key(Path(argv[1]), argv[2], Path(argv[3]), Path(argv[4]), Path(argv[5]), argv[6]))
        except (OSError, ValueError, subprocess.SubprocessError) as e: print(f"sound_seen: no key ({e})", file=sys.stderr); return 1
        return 0
    if len(argv) == 4 and argv[0] == "same":
        at = same(Path(argv[1]), argv[2], argv[3])
        if at: print(f"sound_seen: {argv[2]}: the same sound and cut passed sync, words, retake and music checks at {at}; not run again")
        return 0 if at else 1
    if len(argv) == 4 and argv[0] == "pass":
        if not argv[3]: print("sound_seen: no key, nothing recorded"); return 1
        record(Path(argv[1]), argv[2]).write_text(json.dumps({"key": argv[3], "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}))
        return 0
    print(__doc__, file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
