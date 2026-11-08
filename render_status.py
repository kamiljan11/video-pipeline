#!/usr/bin/env python3
"""How far a render unit is and how long until the whole film set is done (Kamil 2026-11-08: "widget zebym wiedzial
ile zrenderowalo i ile trzeba czekac do konca na calosc contentow").

  python3 render_status.py [UNIT] [--json]      default unit vp-render-v4

Read-only: the unit's processes (cgroup), the stage-2 ffmpeg's read position in rough.mkv (/proc/<pid>/fdinfo: how far
into the film it has encoded) and the finished files in the out dirs. The pure functions take plain data so they test
without a running render (tests/test_render_status.py)."""
import itertools
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CG = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service")
# measured: 18 shorts in 44 min on 2026-11-07 (render-v4.service), the stamp + out_gate tail a few minutes
SHORT_S = 150.0
TAIL_S = 180.0
STAGES = (("assemble.py", "assemble"), ("render.mjs", "gfx"), ("behind.py", "behind"), ("critic.py", "critic"),
          ("build_edl.py", "edl"), ("film_check.py", "checks"), ("research_gate.py", "checks"), ("face_track.py", "edl"),
          ("av_check.py", "checks"), ("sync_check.py", "checks"), ("words_check.py", "checks"), ("manifest.py", "finish"),
          ("out_gate.py", "finish"))


def stage_of(cmdlines: list[list[str]]) -> tuple[str, str | None]:
    """(stage, film) from the unit's command lines: the first known script wins in STAGES order; the film is the
    edl_<name>.json / plan_<name>.json argument when there is one."""
    for script, stage in STAGES:
        for args in cmdlines:
            if any(a.endswith(script) for a in args):
                film = next((m.group(1) for a in args if (m := re.search(r"(?:edl|plan)_([\w]+)\.json$", a))), None)
                return stage, film
    return "start", None


def stage2_pid(procs: dict[int, list[str]]) -> int | None:
    """The assemble stage-2 ffmpeg: the one with a filter graph reading rough.mkv (stage 1 cuts pieces, no graph)."""
    for pid, args in procs.items():
        if args and args[0].endswith("ffmpeg") and "-filter_complex" in args and any(a.endswith("rough.mkv") for a in args):
            return pid
    return None


def eta(films: list[str], done: list[str], current: str | None, frac: float | None, stage2_s: float | None,
        short_times: list[float]) -> dict:
    """Seconds left for the whole set. The current film: from its encode rate once stage 2 has moved (frac > 2 %),
    otherwise unknown (None). The films after it: the mean of the shorts finished this run, else SHORT_S."""
    per_short = sum(short_times) / len(short_times) if short_times else SHORT_S
    left_cur = None
    if frac is not None and stage2_s is not None and frac > 0.02:
        left_cur = stage2_s / frac * (1 - frac)
    rest = [f for f in films if f not in done and f != current]
    total = None if (current and left_cur is None) else (left_cur or 0) + per_short * len(rest) + TAIL_S
    return {"current_left_s": left_cur, "rest_films": len(rest), "per_short_s": per_short, "total_left_s": total}


def queue(films: list[str], done: list[str], current: str | None, finishing: bool) -> list[dict]:
    """One row per format for the window: long 0/1, shorts 3/18, the materials step (stamp + out_gate after the films;
    posts, blog, IG and thumbnails are built before the render, render_v4.sh only stamps and gates them)."""
    shorts = [f for f in films if f != "long"]
    rows = [{"name": "Long", "done": int("long" in done), "total": 1, "now": current == "long"},
            {"name": "Shorty", "done": sum(f in done for f in shorts), "total": len(shorts),
             "now": current is not None and current != "long"}]
    rows.append({"name": "Materiały (pieczątki + out_gate)", "done": 0, "total": 1, "now": finishing})
    return rows


def shell_var(text: str, name: str) -> str:
    """NAME=value from a shell script, quotes dropped and $VAR / ${VAR} from earlier lines of the script expanded."""
    env: dict[str, str] = {}
    for m in re.finditer(r'^([A-Za-z_]\w*)=("([^"]*)"|(\S*))', text, re.MULTILINE):
        env[m.group(1)] = re.sub(r"\$\{?(\w+)\}?", lambda v: env.get(v.group(1), ""), m.group(3) if m.group(3) is not None else m.group(4))
    return env.get(name, "")


def fmt(s: float | None) -> str:
    if s is None:
        return "?"
    m = int(s // 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


# ---- live data (thin shell around the pure functions above) ----
def _procs(unit: str) -> dict[int, list[str]]:
    out = {}
    for f in CG.glob(f"**/{unit}.service/cgroup.procs"):
        for pid in f.read_text().split():
            try:
                out[int(pid)] = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")[:-1]
            except OSError:
                continue
    return out


def _read_frac(pid: int) -> float | None:
    """How far ffmpeg has read rough.mkv: fd position / file size."""
    try:
        for fd in os.listdir(f"/proc/{pid}/fd"):
            target = os.readlink(f"/proc/{pid}/fd/{fd}")
            if target.endswith("rough.mkv"):
                m = re.search(r"pos:\s*(\d+)", Path(f"/proc/{pid}/fdinfo/{fd}").read_text())
                return min(int(m.group(1)) / os.path.getsize(target), 1.0) if m else None
    except OSError:
        return None
    return None


def _age(pid: int) -> float | None:
    try:
        return float(subprocess.run(["ps", "-o", "etimes=", "-p", str(pid)], capture_output=True, text=True, check=False).stdout)
    except ValueError:
        return None


def _unit_start(unit: str) -> float | None:
    r = subprocess.run(["systemctl", "--user", "show", unit, "-p", "ActiveEnterTimestampMonotonic", "-p", "ActiveState"],
                       capture_output=True, text=True, check=False).stdout
    kv = dict(line.split("=", 1) for line in r.splitlines() if "=" in line)
    mono = int(kv.get("ActiveEnterTimestampMonotonic", "0") or 0)
    if not mono:
        return None
    return time.time() - (time.monotonic() - mono / 1e6)


def collect(unit: str = "vp-render-v4", script: str | None = None) -> dict:
    """The status of `unit`: film list and out dirs come from its render_v4.sh (W, O, S variables)."""
    procs = _procs(unit)
    active = bool(procs)
    src = script or next((a for args in procs.values() for a in args if a.endswith("render_v4.sh")), None)
    if src and not os.path.isabs(src):
        src = os.path.join("/home/kamil-jan/Dane/video-pipeline", src)
    text = Path(src).read_text() if src and os.path.exists(src) else ""
    out = shell_var(text, "O")
    shorts = shell_var(text, "S").split()
    films = ["long", *shorts]
    start = _unit_start(unit) if active else None
    done, short_times = [], []
    if out and start:
        mp4s = sorted((p.stat().st_mtime, p) for p in Path(out).glob("*/*.mp4") if p.stat().st_mtime > start)
        for t, p in mp4s:
            name = "long" if p.parent.name == "long" else next((s for s in shorts if p.stem.startswith(s)), p.stem)
            done.append(name)
        st = [t for t, p in mp4s if p.parent.name == "shorts"]
        short_times = [b - a for a, b in itertools.pairwise(st)]
    stage, film = stage_of(list(procs.values()))
    pid = stage2_pid(procs)
    frac = _read_frac(pid) if pid else None
    # the rate from assemble.py's age: in windows a new ffmpeg starts every 2 min, so its own age says nothing
    apid = next((p for p, args in procs.items() if any(a.endswith("assemble.py") for a in args)), None)
    e = eta(films, done, film, frac, _age(apid) if (pid and apid) else None, short_times)
    return {"unit": unit, "active": active, "stage": stage, "film": film, "frac": frac, "films": films, "done": done,
            "queue": queue(films, done, film, stage == "finish"),
            "elapsed_s": time.time() - start if start else None, **e}


def main(argv: list[str]) -> int:
    unit = next((a for a in argv if not a.startswith("-")), "vp-render-v4")
    s = collect(unit)
    if "--json" in argv:
        print(json.dumps(s))
    else:
        pct = f"{s['frac'] * 100:.0f} %" if s["frac"] is not None else "-"
        print(f"{unit}: {'running' if s['active'] else 'stopped'} | {s['film'] or '-'} {s['stage']} {pct} | "
              f"done {len(s['done'])}/{len(s['films'])} | left {fmt(s['total_left_s'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
