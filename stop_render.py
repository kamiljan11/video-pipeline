#!/usr/bin/env python3
# stop_render.py — stop pipeline processes (run_v4.sh, assemble.py, their ffmpeg on this checkout's render/) without matching itself
import os
import signal
from pathlib import Path

RENDER = str(Path(__file__).resolve().parent / "render") + "/"


def matches(cmd: str, render_dir: str = RENDER) -> bool:
    """A pipeline process: run_v4.sh, assemble.py on an EDL, or an ffmpeg (any path to the binary) on render_dir."""
    if any(k in cmd for k in ("run_v4.sh", "assemble.py edl_")):
        return True
    argv0 = cmd.split(" ", 1)[0]
    return os.path.basename(argv0) == "ffmpeg" and render_dir in cmd


def main() -> None:
    me = os.getpid(); killed = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) in (me, os.getppid()): continue
        try: cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="ignore")
        except OSError: continue  # process gone or not ours
        if matches(cmd):
            try: os.kill(int(pid), signal.SIGTERM); killed.append(cmd[:70])
            except OSError: pass  # already exited
    print(len(killed), "stopped"); [print(" ", k) for k in killed]


if __name__ == "__main__":
    main()
