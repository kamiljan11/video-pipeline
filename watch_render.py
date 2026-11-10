#!/usr/bin/env python3
"""watch_render: waits for a run_v4.sh run and says one line when it ends, fails or stops moving. Costs no tokens while waiting.

    python3 watch_render.py <render.log> [--stall 900] [--poll 20] <path> [<path> ...]

Ends with one line: DONE (exit 0), FAILED <what> (exit 1), STALL <seconds> (exit 3). The paths (the work folder's
timeline.log and gfx.log, the film's folder in render/) are what must keep changing: the newest change among them and
render.log older than --stall seconds = STALL. Only lines written after the start count (an old ALL_DONE in the log is not
this run's). Kamil 2026-11-10: "dlaczego nic? skoro kazałem ci działać do końca?" — a render crawled 6 h unseen
(NOTES_LOG row 33); the watcher then only reacted to DONE/FAILED and matched itself with pgrep -f.
"""
import os
import sys
import time


def newest(paths: list[str]) -> float:
    """latest change among the paths; a folder counts with what is directly in it and one level below"""
    t = 0.0
    for p in paths:
        try:
            t = max(t, os.path.getmtime(p))
            if os.path.isdir(p):
                for e in os.scandir(p):
                    t = max(t, e.stat().st_mtime)
                    if e.is_dir(): t = max([t, *(x.stat().st_mtime for x in os.scandir(e.path))])
        except OSError:
            continue  # a path not there yet (the film's folder before assemble) or gone mid-scan: nothing newer from it
    return t


def verdict(new_lines: list[str]) -> tuple[int, str] | None:
    """the run's end read from render.log lines written since the start; None = still running"""
    if not any(ln.strip() == "ALL_DONE" for ln in new_lines): return None
    failed = [ln.strip() for ln in new_lines if ln.startswith("FAILED")]
    return (1, "; ".join(failed[:6])) if failed else (0, "DONE " + " ".join(ln.split(" ", 1)[1].strip() for ln in new_lines if ln.startswith(("DONE ", "DRY_OK "))))


def main(argv: list[str]) -> int:
    opts = {"--stall": 900.0, "--poll": 20.0}
    args = []
    it = iter(argv)
    for a in it:
        if a in opts: opts[a] = float(next(it))
        else: args.append(a)
    if not args: print(__doc__); return 2
    log, paths = args[0], args
    start = os.path.getsize(log) if os.path.exists(log) else 0
    t0 = time.time()
    while True:
        if os.path.exists(log):
            with open(log, encoding="utf-8", errors="replace") as f:
                f.seek(start)
                v = verdict(f.read().splitlines())
            if v: print(v[1]); return v[0]
        idle = time.time() - max(newest(paths), t0)
        if idle > opts["--stall"]:
            print(f"STALL {idle:.0f} s without a change in {', '.join(paths)}"); return 3
        time.sleep(opts["--poll"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
