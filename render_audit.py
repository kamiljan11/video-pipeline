#!/usr/bin/env python3
"""render_audit.py: look at the FINISHED render for what the plan checks cannot see (Skool CCC A1/E3/E4/E17/E25, P1 task 2).

  python3 render_audit.py <plan.json> <film.mp4> [--edl <edl.json>] [--out <report.json>]

Defects (rc 1, each named with its time):
  flash   two picture changes less than FLASH s apart: something shows for a blink (a card, a cut, a b-roll)
  jump    a picture change (ffmpeg scene score > SCENE) further than TOL s from every cut, card and b-roll edge in the EDL
          (a card may take ENTER s to fade in after its start, or out before its end): the render does something the EDL does not say
  repeat  the same word twice in a row in what the film says (a cut that left "agent agent"), REPEAT_OK words aside and not
          across a sentence end ("mamy? Mamy" is a question and its answer)
  short   a card or b-roll in the EDL on screen less than MIN_EVENT s
  face    a card that is not a full screen (gfx_types.is_full / has_pip) hides the face: YuNet (face_track's model) finds
          it FACE_BEFORE s before the card and not in the card's middle (Skool CCC A3, P1 task 5)
The EDL is the plan's "edl_out" unless --edl names the one the film was rendered from. The report goes to --out (default:
next to the film, <film>.audit.json). Heard words come from viewer_pack.film_words (the transcript mapped through the cuts),
not from a new transcription.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path

import gfx_types
from viewer_pack import duration, film_words, stamp

SCENE = 0.25        # ffmpeg scene score (0..1) that counts as a picture change
TOL = 0.15          # s between a change and its EDL mark (a frame or two of encoder and fade slack)
FLASH = 0.5         # s
ENTER = 0.4         # s a card's entrance (fade, slide) may take after its EDL start, and its exit before its end (film 2: 0.25-0.35)
MIN_EVENT = 1.5     # s
REPEAT_OK = {"no", "tak", "nie", "bardzo", "dalej"}  # Polish doubles people say on purpose ("no no", "tak tak")
TIMEOUT = 3600      # s for the scene pass (a 21 min long: ~3 min)
SCALE = 320         # px wide for the scene pass: the score barely changes, the decode is much faster
FACE_BEFORE = 0.3   # s before a card: the face the card must leave visible
FACE_MODEL = Path(__file__).resolve().parent / "models" / "face_detection_yunet_2023mar.onnx"


def marks(edl: dict) -> list[float]:
    """every time the EDL changes the picture: segment joins, card and b-roll in and out, start and end"""
    out, acc = [0.0], 0.0
    for s in edl["segments"]:
        acc += s["out"] - s["in"]
        out.append(acc)
    for o in [*edl.get("overlays", []), *edl.get("broll", [])]:
        out += [o["at"], o["at"] + o["dur"]]
    return sorted(out)


def scene_changes(film: str, threshold: float = SCENE) -> list[float]:
    try:
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostdin", "-i", film, "-an", "-vf",
                            f"scale={SCALE}:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                           capture_output=True, text=True, check=False, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ffmpeg scene pass on {film}: no answer in {TIMEOUT} s") from e
    if r.returncode: raise RuntimeError(f"ffmpeg scene pass on {film}: {r.stderr.strip().splitlines()[-1:]}")
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def norm(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())  # \w keeps Polish letters (ą, ł, ż...)


def audit(changes: list[float], edl: dict, said: list[tuple[float, str]]) -> list[dict]:
    found = []
    m = marks(edl)
    for a, b in pairwise(changes):
        if b - a < FLASH: found.append({"kind": "flash", "t": a, "detail": f"{stamp(a)}-{stamp(b)}: on screen {b - a:.2f} s"})
    shown = [*edl.get("overlays", []), *edl.get("broll", [])]
    for t in changes:
        near = min(m, key=lambda x: abs(x - t))
        fading = any(0 <= t - o["at"] <= ENTER or 0 <= o["at"] + o["dur"] - t <= ENTER for o in shown)
        if abs(near - t) > TOL and not fading: found.append({"kind": "jump", "t": t, "detail": f"{stamp(t)}: picture change, nearest EDL mark {stamp(near)}"})
    for (ta, wa), (tb, wb) in pairwise(said):
        if norm(wa) and norm(wa) == norm(wb) and norm(wa) not in REPEAT_OK and tb - ta < 2.0 and not wa.rstrip().endswith((".", "?", "!")):
            found.append({"kind": "repeat", "t": ta, "detail": f"{stamp(ta)}: {wa!r} {wb!r}"})
    for o in [*edl.get("overlays", []), *edl.get("broll", [])]:
        if o["dur"] < MIN_EVENT:
            found.append({"kind": "short", "t": o["at"], "detail": f"{stamp(o['at'])}: {o.get('id', '?')} on screen {o['dur']:.2f} s, want >= {MIN_EVENT}"})
    return sorted(found, key=lambda f: f["t"])


def face_covered(edl: dict, specs: dict[str, dict], seen: Callable[[float], bool]) -> list[dict]:
    """seen(t) = a face is visible in the finished film at t"""
    out = []
    for o in edl.get("overlays", []):
        sp = specs.get(o.get("id", ""))
        if not sp or gfx_types.is_full(sp) or gfx_types.has_pip(sp): continue  # a full screen covers him on purpose
        mid = o["at"] + o["dur"] / 2
        if seen(max(0.0, o["at"] - FACE_BEFORE)) and not seen(mid):
            out.append({"kind": "face", "t": o["at"], "detail": f"{stamp(o['at'])}: {o['id']} ({sp.get('type')}) hides the face (gone at {stamp(mid)})"})
    return out


def face_seer(film: str) -> Callable[[float], bool]:
    import cv2  # only here: the scene and word checks run without OpenCV
    if not FACE_MODEL.is_file(): raise RuntimeError(f"no face model {FACE_MODEL}")
    cap = cv2.VideoCapture(film)
    w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    size = (640, 360) if w >= h else (360, 640)  # the frame's own shape: a 9:16 short is not squashed to 16:9
    det = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", size, 0.7)

    def seen(t: float) -> bool:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok: return False
        _, faces = det.detect(cv2.resize(fr, size))
        return faces is not None and len(faces) > 0
    return seen


def main(argv: list[str]) -> int:
    opt = {k: argv[argv.index(k) + 1] for k in ("--edl", "--out") if k in argv and argv.index(k) + 1 < len(argv)}
    rest = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--edl", "--out"))]
    if len(rest) != 2: print(__doc__, file=sys.stderr); return 2
    plan_p, film = Path(rest[0]), rest[1]
    try:
        plan = json.loads(plan_p.read_text(encoding="utf-8"))
        edl = json.loads(Path(opt.get("--edl") or plan_p.parent / plan["edl_out"]).read_text(encoding="utf-8"))
        words = json.loads((plan_p.parent / plan["words"]).read_text(encoding="utf-8"))["transcription"]
        total = duration(film)
        found = audit(scene_changes(film), edl, film_words(words, edl["segments"]))
        sp_file = edl.get("gfx_specs") and plan_p.parent / edl["gfx_specs"]
        if sp_file:
            specs = {x["id"]: x for x in json.loads(Path(sp_file).read_text(encoding="utf-8"))}
            found = sorted(found + face_covered(edl, specs, face_seer(film)), key=lambda f: f["t"])
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"FAILED render_audit {film}: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    edl_len = sum(s["out"] - s["in"] for s in edl["segments"]) + edl.get("tail", 0)
    if abs(edl_len - total) > 1.0:
        found.insert(0, {"kind": "edl", "t": 0.0, "detail": f"film {total:.1f} s vs EDL {edl_len:.1f} s: not the EDL this film was rendered from (--edl)"})
    out = Path(opt.get("--out") or Path(film).with_suffix(".audit.json"))
    out.write_text(json.dumps({"film": film, "total": round(total, 2), "defects": found}, ensure_ascii=False, indent=1))
    for f in found: print(f"{f['kind']:7} {f['detail']}")
    counts = {k: sum(f["kind"] == k for f in found) for k in ("edl", "flash", "jump", "repeat", "short", "face")}
    print(("FAILED" if found else "OK") + f" render_audit {Path(film).name}: " + ", ".join(f"{k} {v}" for k, v in counts.items() if v) + f" -> {out}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
