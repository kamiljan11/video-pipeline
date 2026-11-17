#!/usr/bin/env python3
# stop_render.py — stop this checkout's pipeline processes (run_v4.sh, assemble.py, ffmpeg on its render/) without matching
# itself or another clone's render. Paths are resolved against each process's working directory, symlinks included.
import os
import signal
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent)
SHELLS = {"bash", "sh", "dash"}
SCRIPTS = {"run_v4.sh": SHELLS, "assemble.py": None}  # None = any python interpreter


def _real(cwd: str, arg: str) -> str:
    return os.path.realpath(os.path.join(cwd, arg))


def _is_python(argv0: str) -> bool:
    return os.path.basename(argv0).startswith("python")


def matches(argv: list[str], cwd: str, root: str = ROOT) -> bool:
    """argv/cwd of a process -> True when it is root's run_v4.sh, root's assemble.py, or an ffmpeg on root/render/."""
    if not argv:
        return False
    root = os.path.realpath(root)
    exe = os.path.basename(argv[0])
    if exe == "ffmpeg":
        render = os.path.join(root, "render") + os.sep
        return any(_real(cwd, a).startswith(render) for a in argv[1:] if not a.startswith("-"))
    for name, interpreters in SCRIPTS.items():
        ok_interp = exe in interpreters if interpreters else _is_python(argv[0])
        if ok_interp and any(os.path.basename(a) == name and _real(cwd, a) == os.path.join(root, name) for a in argv[1:]):
            return True
    return False


def main() -> None:
    me = os.getpid(); killed = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) in (me, os.getppid()): continue
        try:
            argv = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="ignore").split("\0")[:-1]
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError: continue  # process gone or not ours
        if matches(argv, cwd):
            try: os.kill(int(pid), signal.SIGTERM); killed.append(" ".join(argv)[:70])
            except OSError: pass  # already exited
    print(len(killed), "stopped"); [print(" ", k) for k in killed]


if __name__ == "__main__":
    main()
