#!/usr/bin/env python3
"""How far a render unit is and how long until the whole film set is done (Kamil 2026-11-08: "widget zebym wiedzial
ile zrenderowalo i ile trzeba czekac do konca na calosc contentow").

  python3 render_status.py [UNIT] [--json]      default unit vp-render-v4

Read-only: the unit's processes (cgroup), the stage-2 ffmpeg's read position in rough.mkv (/proc/<pid>/fdinfo: how far
into the film it has encoded) and the finished files in the out dirs. The pure functions take plain data so they test
without a running render (tests/test_render_status.py)."""
import glob
import itertools
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import progress

CG = Path(f"/sys/fs/cgroup/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service")
# defaults until this run measures its own: 18 shorts in 44 min on 2026-11-07 (render-v4.service), the stamp + out_gate
# tail a few minutes. Once two shorts are done their mean replaces SHORT_S (eta short_times)
SHORT_S = 150.0
TAIL_S = 180.0
STAGES = (("assemble.py", "assemble"), ("render.mjs", "gfx"), ("behind.py", "behind"), ("critic.py", "critic"),
          ("build_edl.py", "edl"), ("film_check.py", "checks"), ("research_gate.py", "checks"), ("face_track.py", "edl"),
          ("av_check.py", "checks"), ("sync_check.py", "checks"), ("words_check.py", "checks"), ("manifest.py", "finish"),
          ("out_gate.py", "finish"))


def film_of(args: list[str], films: tuple[str, ...] | list[str] = ()) -> str | None:
    """the film a command works on: an edl_<name>.json / plan_<name>.json argument, a render/<name>/ path
    (words_check, av_check) or a bare film name (film_check . <name>)"""
    for a in args:
        if m := re.search(r"(?:edl|plan)_(\w+)\.(?:json|txt)$", a):
            return m.group(1)
    for a in args:
        if (m := re.search(r"/render/(\w+)/[^/]+$", a)) and (not films or m.group(1) in films):
            return m.group(1)
    return next((a for a in args[2:] if a in films), None)


def stage_of(cmdlines: list[list[str]], films: tuple[str, ...] | list[str] = ()) -> tuple[str, str | None]:
    """(stage, film) from the unit's command lines: the first known script wins in STAGES order (film_of)"""
    for script, stage in STAGES:
        for args in cmdlines:
            if any(a.endswith(script) for a in args):
                return stage, film_of(args, films)
    return "start", None


STEP_PL = {"assemble.py": "składanie filmu", "render.mjs": "grafiki", "behind.py": "tekst za mówcą", "critic.py": "krytyk",
           "build_edl.py": "montaż (EDL)", "film_check.py": "lista kontrolna", "research_gate.py": "bramka researchu",
           "face_track.py": "kadrowanie twarzy", "av_check.py": "kontrola dźwięku", "sync_check.py": "kontrola synchronizacji",
           "words_check.py": "kontrola słów", "manifest.py": "pieczątka", "out_gate.py": "out_gate"}


def proc_rows(procs: dict[int, list[str]], unit_pids: set[int], films: list[str]) -> list[dict]:
    """one row per pipeline step running anywhere (the render unit or by hand beside it, Kamil 2026-11-08 "na tym
    widgecie to powinny wszystkie procesy leciec"): script, Polish step name (+ words_check mode), film, by_hand"""
    rows = []
    for pid, args in sorted(procs.items()):
        script = next((sc for sc, _ in STAGES if any(a.endswith("/" + sc) or a == sc for a in args)), None)
        if script is None:
            continue
        i = next(k for k, a in enumerate(args) if a.endswith(script))
        run_by = os.path.basename(args[i - 1]) if i else ""  # python3 / node right before the script (a shell -c line is not a step)
        if i and "python" not in run_by and run_by != "node":
            continue
        mode = args[i + 1] if script == "words_check.py" and i + 1 < len(args) else None
        step = STEP_PL[script] + (f" ({'cięcie' if mode == 'cut' else 'dźwięk'})" if mode in ("cut", "sound") else "")
        rows.append({"pid": pid, "script": script, "step": step, "film": film_of(args, films), "by_hand": pid not in unit_pids})
    return rows


def whisper_pct(text: str) -> float | None:
    """the last "progress = NN%" of whisper-cli --print-progress"""
    hits = re.findall(r"progress\s*=\s*(\d+)%", text)
    return int(hits[-1]) / 100 if hits else None


def stage2_pid(procs: dict[int, list[str]]) -> int | None:
    """The assemble stage-2 ffmpeg: the one with a filter graph reading rough.mkv (stage 1 cuts pieces, no graph)."""
    for pid, args in procs.items():
        if args and args[0].endswith("ffmpeg") and "-filter_complex" in args and any(a.endswith("rough.mkv") for a in args):
            return pid
    return None


def eta(films: list[str], done: list[str], current: str | None, frac: float | None, stage2_s: float | None,
        short_times: list[float], rate: float | None = None, film_age_s: float | None = None) -> dict:
    """Seconds left for the whole set. The current film: from `rate` (fraction of the film per second, measured by a
    caller that samples frac over time, the widget) when given, else from stage2_s (assemble.py's age: includes stage
    1, so it overstates) once stage 2 has moved (frac > 2 %); otherwise unknown (None). The films after it: the mean of
    the shorts finished this run, else SHORT_S."""
    per_short = sum(short_times) / len(short_times) if short_times else SHORT_S
    left_cur = None
    if frac is not None and rate:
        left_cur = (1 - frac) / rate
    elif frac is not None and stage2_s is not None and frac > 0.02:
        left_cur = stage2_s / frac * (1 - frac)
    elif current and current != "long" and film_age_s is not None:  # checks, gfx, edl: no counter, a short takes per_short
        left_cur = max(per_short - film_age_s, 0.1 * per_short)
    rest = [f for f in films if f not in done and f != current]
    total = None if (current and left_cur is None) else (left_cur or 0) + per_short * len(rest) + TAIL_S
    return {"current_left_s": left_cur, "rest_films": len(rest), "per_short_s": per_short, "total_left_s": total}


def total_pct(elapsed_s: float | None, left_s: float | None) -> float | None:
    """share of the whole set done by time: elapsed / (elapsed + left)"""
    if not elapsed_s or left_s is None:
        return None
    return elapsed_s / (elapsed_s + left_s)


def failed_films(films: list[str], done: list[str], current: str | None, finishing: bool,
                 busy: tuple[str, ...] | set[str] = ()) -> list[str]:
    """films the run has gone past without a finished file (Kamil 2026-11-08 "nie pokazuje ze renderuje sie long": the
    long had failed a gate and stood as 0/1 like one still waiting): every film before the current one in render order
    (all of them once the run is in the finish step) that is not done"""
    upto = len(films) if finishing else (films.index(current) if current in films else 0)
    return [f for f in films[:upto] if f not in done and f not in busy]  # busy: still worked on by hand


def queue(films: list[str], done: list[str], current: str | None, finishing: bool,
          busy: tuple[str, ...] | set[str] = ()) -> list[dict]:
    """One row per format for the window: long 0/1, shorts 3/18 (+ how many failed), the materials step (stamp + out_gate
    after the films; posts, blog, IG and thumbnails are built before the render, render_v4.sh only stamps and gates them)."""
    shorts = [f for f in films if f != "long"]
    bad = failed_films(films, done, current, finishing, busy)
    rows = [{"name": "Long", "done": int("long" in done), "total": 1, "now": current == "long" or "long" in busy,
             "failed": int("long" in bad)},
            {"name": "Shorty", "done": sum(f in done for f in shorts), "total": len(shorts),
             "now": (current is not None and current != "long") or any(f in busy for f in shorts),
             "failed": sum(f in bad for f in shorts)}]
    rows.append({"name": "Materiały (pieczątki + out_gate)", "done": 0, "total": 1, "now": finishing})
    return rows


def materials(out: str | Path, shorts: list[str]) -> list[dict]:
    """Rows for the materials built before the render (Kamil 2026-11-08: "czemu tu nie ma artykulow postow"): what is
    already in the out dir per format. done = files found, total = what the film set needs (a cover and an IG reel text
    per short, a YouTube text for the long and each short) or, for posts / carousels / articles, the folders made."""
    o = Path(out)
    ok = lambda pattern: len(list(o.glob(pattern)))
    dirs = lambda pattern: len([d for d in o.glob(pattern) if d.is_dir()])
    rows = [("Miniatury longa (A/B…)", ok("thumbnails/long_?.jpg"), max(2, ok("thumbnails/long_?.jpg"))),
            ("Okładki shortów", sum((o / "thumbnails" / f"{s}_cover.jpg").exists() for s in shorts), len(shorts)),
            ("Posty LinkedIn", ok("posts/*/post.md"), dirs("posts/*")),
            ("Karuzele Instagram", sum(any(d.glob("*.png")) or any(d.glob("*.jpg")) for d in o.glob("instagram/p*") if d.is_dir()),
             dirs("instagram/p*")),
            ("Opisy reels Instagram", sum((o / "instagram/reels" / f"{s}.json").exists() for s in shorts), len(shorts)),
            ("Artykuł na bloga", ok("blog/*/article.json"), max(1, dirs("blog/*"))),
            ("Opisy YouTube", int((o / "youtube/long.md").exists()) + sum((o / "youtube/shorts" / f"{s}.md").exists() for s in shorts),
             1 + len(shorts))]
    return [{"name": n, "done": d, "total": t, "now": False} for n, d, t in rows]


def fail_reasons(log_text: str, names: list[str]) -> dict[str, str]:
    """the last FAILED line of render.log naming each film (run_v4.sh: "FAILED <step> <film> ..."), "FAILED assemble <film>"
    skipped when a more specific line came before it"""
    out: dict[str, str] = {}
    for line in log_text.splitlines():
        m = re.match(r"FAILED (.+?) (\S+)(?: \(.*\))?$", line)
        if m and m.group(2) in names and not (m.group(1) == "assemble" and m.group(2) in out):
            out[m.group(2)] = m.group(1)
    return out


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


VP = str(Path(__file__).resolve().parent) + "/"  # the pipeline repo, wherever it lives (planned rename: content-pipeline)


def _all_pipeline_procs() -> dict[int, list[str]]:
    """every process on the machine running a pipeline script from VP (the unit and anything beside it)"""
    out = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            args = Path(f"/proc/{d}/cmdline").read_bytes().decode(errors="replace").split("\0")[:-1]
        except OSError:
            continue
        if any(a.startswith(VP) and any(a.endswith(sc) for sc, _ in STAGES) for a in args):
            out[int(d)] = args
    return out


def _whisper_progress(args: list[str]) -> float | None:
    """words_check writes whisper's --print-progress to ~/.cache/vp-progress (progress.progress_file)"""
    for a in args:
        for f in progress.PROGRESS_DIR.glob(glob.escape(progress.progress_key(a)) + ".*.progress") if a.startswith("/") else ():
            try:
                if time.time() - f.stat().st_mtime < 600:
                    return whisper_pct(f.read_text(errors="replace")[-2000:])
            except OSError:
                continue
    return None


def _new_mp4s(out: str, start: float) -> list[tuple[float, Path]]:
    """(mtime, path) of the films in the out dirs written after start, oldest first; a file moved away meanwhile is skipped"""
    found = []
    for p in Path(out).glob("*/*.mp4"):
        try:
            t = p.stat().st_mtime
        except OSError:
            continue
        if t > start:
            found.append((t, p))
    return sorted(found)


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


def collect(unit: str = "vp-render-v4", script: str | None = None, rate: float | None = None) -> dict:
    """The status of `unit`: film list and out dirs come from its render_v4.sh (W, O, S variables). rate: see eta.
    Fields (the desktop widget reads them): unit, active, stage, film, frac, films, done, queue, elapsed_s,
    current_left_s, rest_films, per_short_s, total_left_s."""
    procs = _procs(unit)
    active = bool(procs)
    shell = next(((p, a) for p, args in procs.items() for a in args if a.endswith("render_v4.sh")), (None, None))
    src = script or shell[1]
    if src and not os.path.isabs(src) and shell[0]:  # a relative path is relative to the unit's working directory
        try:
            src = os.path.join(os.readlink(f"/proc/{shell[0]}/cwd"), src)
        except OSError:
            src = None
    text = Path(src).read_text() if src and os.path.exists(src) else ""
    out = shell_var(text, "O")
    shorts = shell_var(text, "S").split()
    films = ["long", *shorts]
    start = _unit_start(unit) if active else None
    done, short_times = [], []
    if out and start:
        mp4s = _new_mp4s(out, start)
        for t, p in mp4s:
            name = "long" if p.parent.name == "long" else next((s for s in shorts if p.stem.startswith(s)), p.stem)
            done.append(name)
        st = [t for t, p in mp4s if p.parent.name == "shorts"]
        short_times = [b - a for a, b in itertools.pairwise(st)]
    stage, film = stage_of(list(procs.values()), films)
    every = {**_all_pipeline_procs(), **procs}
    rows = proc_rows(every, set(procs), films)
    for r in rows:
        r["age_s"] = _age(r["pid"])
        r["pct"] = _whisper_progress(every[r["pid"]]) if r["script"] == "words_check.py" else None
    busy = {r["film"] for r in rows if r["by_hand"] and r["film"]}
    bad = failed_films(films, done, film, stage == "finish", busy)
    log = Path(src).resolve().parents[3] / "render.log" if src else None  # <VP>/render/montaz/<date>/work/render_v4.sh
    try:
        why = fail_reasons(log.read_text(errors="replace")[-400_000:], bad) if log and bad else {}
    except OSError:
        why = {}
    fails = [{"film": f, "why": why.get(f, "?")} for f in bad]
    pid = stage2_pid(procs)
    frac = _read_frac(pid) if pid else None
    # the rate from assemble.py's age: in windows a new ffmpeg starts every 2 min, so its own age says nothing
    apid = next((p for p, args in procs.items() if any(a.endswith("assemble.py") for a in args)), None)
    new = _new_mp4s(out, start) if out and start else []
    last = new[-1][0] if new else (start or 0.0)  # when the current film began: the last finished one, else the run start
    e = eta(films, done, film, frac, _age(apid) if (pid and apid) else None, short_times, rate,
            time.time() - last if last else None)
    elapsed = time.time() - start if start else None
    return {"unit": unit, "active": active, "stage": stage, "film": film, "frac": frac, "films": films, "done": done,
            "queue": queue(films, done, film, stage == "finish", busy) + (materials(out, shorts) if out else []),
            "failed": fails, "procs": rows, "elapsed_s": elapsed, **e, "total_pct": total_pct(elapsed, e["total_left_s"])}


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
