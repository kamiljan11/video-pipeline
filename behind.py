#!/usr/bin/env python3
"""behind.py gfx_specs.json gfx_dir [--edl edl_x.json] — text BEHIND the speaker (docs/adr/0005-text-behind-speaker.md):
a card whose spec has "behind": {"edl": "edl_x.json"} gets the speaker cut out of its alpha, so the film's own picture of
the speaker stays on top of the card.

The person comes from a matting model (Robust Video Matting, matte/models/rvm_resnet50_fp32.onnx, onnxruntime in
matte/.venv) run on the film's OUTPUT frames under the card: the recording cut and framed exactly like assemble.py does
(its vf_for is lifted out of assemble.py, so the framing has one owner). The card as rendered is kept in <id>.front.mov;
the masked card replaces <id>.mov and carries its key in its metadata (comment=behind:<key>). So a .mov without that mark
is a fresh render (it becomes the new front), the same key = nothing to do, and the only write is one atomic replace.
Everything after (assemble.py, the panel's live player) just overlays the .mov.
Run by gfx/render.mjs after its renders (an EDL that is not built yet = later) and by run_v4.sh before assemble.py with
--edl: only that film's cards, on its final EDL.
"""
import ast
import contextlib
import hashlib
import json
import math
import os
import re
import runpy
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from itertools import pairwise
from pathlib import Path

import numpy as np

from cpu_budget import heavy_threads, low_priority  # next to this script

VP = Path(__file__).resolve().parent
MODEL = VP / "matte" / "models" / "rvm_resnet50_fp32.onnx"
MODEL_SHA = "25db300fcb6ee27f941a1b52c97856e8d1f13c7f35817f81a612f89af0e8a85c"  # GitHub PeterL1n/RobustVideoMatting v1.0.0
FPS = 30
WARM = 1.0  # seconds of film fed to the model before the card: its recurrent state settles on the person first
MAX_DUR = 20.0  # seconds; a card is held one frame at a time, this bounds the run, not the memory
STALE_PART = 2 * 3600  # seconds; a temp file this old is from a killed run (run_v4.sh's timeout is 3600 s)
MARK = "behind:"
VERSION = 2  # in the key: a change of how the cut-out is made redoes every card
SAFE_ID = re.compile(r"[A-Za-z0-9_-]+")  # specs come over Syncthing: a card id / EDL name never leaves gfx_dir / work
SAFE_EDL = re.compile(r"[A-Za-z0-9_-]+\.json")
MAX_PIXELS = 3840 * 2160
Matting = Callable[[float], Callable[[np.ndarray], np.ndarray]]


class BehindError(Exception):
    pass


class BadName(BehindError):
    """a card id / EDL name that is not a plain file name: a fault in the spec, never an EDL not ready yet"""


def framing_src() -> str:
    """assemble.py's vf_for / keys_expr / track_expr as code (part of every card's key: a framing change redoes the cut-outs)"""
    src = (VP / "assemble.py").read_text(encoding="utf-8")
    fns: list[ast.stmt] = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in ("vf_for", "keys_expr", "track_expr")]
    return ast.unparse(ast.Module(body=fns, type_ignores=[]))


def framing(edl: dict):
    """assemble.py's vf_for(zoom, face, track) for this EDL (same globals as assemble.py sets from the EDL)."""
    vertical = edl.get("vertical", False)
    fx, fy = edl.get("face", [0.5, 0.45])
    ns = {"W": edl.get("w", 2560), "H": edl.get("h", 1440), "SW": edl.get("src_w", 2560), "SH": edl.get("src_h", 1440),
          "FX0": fx, "FY0": fy, "vertical": vertical, "TY": edl.get("face_target_y", 0.40 if vertical else None),
          "E": "\\", "pairwise": pairwise}
    with tempfile.TemporaryDirectory() as d:
        mod = Path(d) / "assemble_framing.py"
        mod.write_text(framing_src(), encoding="utf-8")
        return runpy.run_path(str(mod), init_globals=ns)["vf_for"]


def seg_frames(edl: dict) -> list[int]:
    """frames each segment gets in the film: assemble.py's seg_exact cuts exactly round(d*30)"""
    return [max(1, round((s["out"] - s["in"]) * FPS)) for s in edl["segments"]]


def film_frames(edl: dict, first: int, n: int, vf_for, size: tuple[int, int]) -> Iterator[np.ndarray]:
    """RGB uint8 frames first..first+n-1 of the film's picture (before graphics), as assemble.py stage 1 cuts them;
    fewer when the film ends."""
    w, h = size
    start = 0
    for s, k in zip(edl["segments"], seg_frames(edl), strict=True):
        lo, hi = max(first, start), min(first + n, start + k)
        if lo < hi:
            d = k / FPS
            vf = "setpts=PTS-STARTPTS," + vf_for(s.get("zoom", 1.0), s.get("face"), s.get("track"))
            # from the segment start: a dynamic zoom is a function of the frame number in the segment; local files only
            with subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{s['in']:.3f}", "-protocol_whitelist", "file",
                                   "-i", edl["sources"][s["src"]], "-t", f"{d:.3f}", "-vf", vf, "-frames:v", str(hi - start),
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE) as p:
                assert p.stdout is not None
                fr = None
                for i in range(start, hi):  # streamed: a card late in a long segment must not hold the segment in memory
                    b = p.stdout.read(w * h * 3)
                    if len(b) == w * h * 3:
                        fr = np.frombuffer(b, np.uint8).reshape(h, w, 3)
                    if fr is None:
                        raise BehindError(f"ffmpeg gave no frame of {s['src']} at {s['in']:.3f}")
                    if i >= lo:
                        yield fr  # a short decode at the very end repeats its last frame (assemble pads too)
            if p.returncode:
                raise BehindError(f"ffmpeg failed on {s['src']} at {s['in']:.3f} (rc {p.returncode})")
        start += k
        if start >= first + n:
            return


class Matter:
    """Robust Video Matting, frame by frame with its recurrent state: rgb uint8 HxWx3 -> person alpha float HxW (0..1)."""

    def __init__(self, ratio: float):
        if not MODEL.exists():
            raise BehindError(f"no matting model {MODEL} (README: text behind the speaker)")
        if hashlib.sha256(MODEL.read_bytes()).hexdigest() != MODEL_SHA:
            raise BehindError(f"{MODEL} is not the verified RVM v1.0.0 file (sha256 differs)")
        import onnxruntime as ort  # matte/.venv only; the rest of the pipeline does not need it
        so = ort.SessionOptions(); so.intra_op_num_threads = heavy_threads()
        self.s = ort.InferenceSession(str(MODEL), so, providers=["CPUExecutionProvider"])
        self.rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
        self.ratio = np.array([ratio], np.float32)

    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        src = (rgb.astype(np.float32) / 255).transpose(2, 0, 1)[None]
        outs = self.s.run(None, {"src": src, "r1i": self.rec[0], "r2i": self.rec[1], "r3i": self.rec[2],
                                 "r4i": self.rec[3], "downsample_ratio": self.ratio})
        self.rec = [np.asarray(r) for r in outs[2:]]
        return np.asarray(outs[1])[0, 0]


def cut_out(rgba: np.ndarray, person: np.ndarray | None) -> np.ndarray:
    """the card with the person's pixels see-through: alpha * (1 - person); colour untouched; None = no person known"""
    out = rgba.copy()
    if person is not None:
        out[..., 3] = np.round(rgba[..., 3].astype(np.float32) * (1 - np.clip(person, 0, 1))).astype(np.uint8)
    return out


def probe(mov: Path, entry: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry, "-of", "default=nw=1:nk=1",
                           str(mov)], capture_output=True, text=True, check=True, timeout=60).stdout.strip()


def card_frames(mov: Path, size: tuple[int, int]) -> np.ndarray:
    """every frame of a (small) card at once: for tests and checks"""
    w, h = size
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mov), "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                       capture_output=True, check=True, timeout=600)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 4)


def window_key(edl: dict, at: float, n: int) -> list:
    """what the matte depends on in the EDL: the card's place, the segments under it (+ the warm-up) and their files"""
    first = max(0, math.floor((at - WARM) * FPS)); last = math.ceil(at * FPS) + n
    start, under = 0, []
    for s, k in zip(edl["segments"], seg_frames(edl), strict=True):
        if start < last and start + k > first:
            check_segment(s)
            st = Path(edl["sources"][s["src"]]).stat()
            under.append([start, s, st.st_size, st.st_mtime_ns])
        start += k
    return [round(at, 3), n, under, {k: edl.get(k) for k in ("w", "h", "face", "src_w", "src_h", "vertical", "face_target_y")}]


def open_nofollow(p: Path):
    return os.fdopen(os.open(p, os.O_RDONLY | os.O_NOFOLLOW), "rb")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open_nofollow(p) as f:
        while b := f.read(1 << 22):
            h.update(b)
    return h.hexdigest()


def num(v) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def check_edl(edl: dict) -> None:
    """the EDL-wide framing values vf_for pastes into the ffmpeg filter: numbers only, like check_segment"""
    face, ok = edl.get("face"), all(edl.get(k) is None or num(edl[k]) for k in ("w", "h", "src_w", "src_h", "face_target_y"))
    ok = ok and (face is None or (isinstance(face, list) and len(face) == 2 and all(map(num, face))))
    if not (ok and isinstance(edl.get("vertical", False), bool)):
        raise BehindError("EDL: w / h / src_w / src_h / face / face_target_y must be numbers, vertical true or false")


def check_segment(s: dict) -> None:
    """numbers only where vf_for pastes them into the ffmpeg filter (plans come over Syncthing: no filter text from a plan)"""
    z, face, track = s.get("zoom", 1.0), s.get("face"), s.get("track")
    ok = num(z) or (isinstance(z, dict) and all(num(z.get(k)) for k in ("a", "b", "t0", "t1"))
                    and all(isinstance(p, list) and len(p) == 2 and all(map(num, p)) for p in z.get("keys") or []))
    ok = ok and (face is None or (isinstance(face, list) and len(face) == 2 and all(map(num, face))))
    ok = ok and (track is None or (isinstance(track, list) and all(isinstance(p, list) and len(p) == 2 and all(map(num, p)) for p in track)))
    if not ok:
        raise BehindError(f"segment at {s.get('in')}: zoom / face / track must be numbers")


def process(spec: dict, gfx: Path, base: Path, matter_for: Matting | None = None, strict: bool = True) -> str:
    """strict = run_v4.sh's final EDL; not strict (render.mjs, before run_v4.sh rebuilds the EDLs): an EDL that is not ready
    for a cut-out is left for later instead of failing every film's graphics"""
    cid, edl_name = str(spec["id"]), str(spec["behind"]["edl"])
    if not SAFE_ID.fullmatch(cid) or not SAFE_EDL.fullmatch(edl_name):
        raise BadName(f"card id {cid!r} / edl {edl_name!r}: only letters, digits, _ and - (a file in the work folder)")
    edl_p = base / edl_name
    if not edl_p.exists():
        return f"{cid}: {edl_name} not built yet (cut out when it is: run_v4.sh / the panel's next render)"
    edl = json.loads(edl_p.read_text())
    o = next((o for o in edl.get("overlays", []) if o.get("id") == cid), None)
    if o is None:
        return f"{cid}: not in {edl_name} (no cut-out)"
    if not edl.get("seg_exact"):
        if not strict:
            return f"{cid}: {edl_name} has no seg_exact yet (cut out when run_v4.sh rebuilds it)"
        raise BehindError(f"{cid}: {edl_name} has no seg_exact; without it the film's frames drift from the card (plan: \"seg_exact\": true)")
    check_edl(edl)
    mov, front = gfx / f"{cid}.mov", gfx / f"{cid}.front.mov"
    if mov.is_symlink() or front.is_symlink():  # gfx/ can be a synced folder: never write through a link
        raise BehindError(f"{cid}: {mov.name} / {front.name} is a symlink")
    sweep(gfx, cid)
    mark = probe(mov, "format_tags=comment") if mov.exists() else ""
    if mov.exists() and not mark.startswith(MARK):  # a fresh render (render.mjs never writes the mark): the new front
        part = temp_in(gfx, cid)
        try:
            with open_nofollow(mov) as src, part.open("wb") as dst:  # a link swapped in after the check is not read
                shutil.copyfileobj(src, dst, 1 << 22)
            part.replace(front)
        finally:
            part.unlink(missing_ok=True)
    elif not front.exists():
        raise BehindError(f"{cid}: {front.name} is missing; move {mov.name} aside so render.mjs renders the card again")
    w, h = edl.get("w", 2560), edl.get("h", 1440)
    if not (num(w) and num(h) and 0 < w * h <= MAX_PIXELS) or probe(front, "stream=width,height").split() != [str(w), str(h)]:
        raise BehindError(f"{cid}: the card is not {w}x{h} (the film's frame, at most 4K)")
    n = int(probe(front, "stream=nb_frames") or 0)
    if not 0 < n <= MAX_DUR * FPS:
        raise BehindError(f"{cid}: {n} frames; a card behind the speaker is at most {MAX_DUR:.0f} s")
    ratio = spec["behind"].get("ratio", 0.2)
    if not (num(ratio) and 0 < ratio <= 1):
        raise BehindError(f"{cid}: ratio {ratio!r} must be a number in (0, 1]")
    key = hashlib.sha256(json.dumps([VERSION, window_key(edl, o["at"], n), sha(front), ratio, MODEL_SHA,
                                     hashlib.sha256(framing_src().encode()).hexdigest()], sort_keys=True).encode()).hexdigest()
    if mark == MARK + key:
        return f"{cid}: up to date"
    # card frame k is on screen at at + k/30 -> film frame ceil((at + k/30) * 30) (overlay shows the last card frame <= t)
    c0 = math.ceil(o["at"] * FPS - 1e-6); first = max(0, math.floor((o["at"] - WARM) * FPS))
    matter = (matter_for or Matter)(ratio)
    tmp = temp_in(gfx, cid)
    try:
        _encode(cid, front, tmp, key, n, (w, h), film_frames(edl, first, c0 - first + n, framing(edl), (w, h)), first, c0, matter)
        tmp.replace(mov)
    finally:
        tmp.unlink(missing_ok=True)  # a failed run leaves the card as it was (the .mov is only ever replaced whole)
    return f"{cid}: speaker cut out of {n} frames"


def _encode(cid: str, front: Path, tmp: Path, key: str, n: int, size: tuple[int, int], frames: Iterator[np.ndarray],
            first: int, c0: int, matter: Callable[[np.ndarray], np.ndarray]) -> None:
    w, h = size
    with subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(front), "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE) as dec, \
         subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-framerate", str(FPS),
                           "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                           "-metadata", f"comment={MARK}{key}", str(tmp)], stdin=subprocess.PIPE) as enc:
        assert dec.stdout is not None and enc.stdin is not None
        src, sink = dec.stdout, enc.stdin
        fsz = w * h * 4
        done, person = 0, None

        def put(p):
            b = src.read(fsz)
            if len(b) != fsz:
                raise BehindError(f"{cid}: {front.name} has fewer frames than its {n}")
            sink.write(cut_out(np.frombuffer(b, np.uint8).reshape(h, w, 4), p).tobytes())

        for i, rgb in enumerate(frames):
            person = matter(rgb)
            if first + i >= c0:
                put(person); done += 1
        for _ in range(done, n):  # the film ends under the card: its last matte (deterministic, never empty memory)
            put(person)
        sink.close()
        if enc.wait(timeout=600) or dec.wait(timeout=60):
            raise BehindError(f"{cid}: ffmpeg could not write the card (rc {enc.returncode}/{dec.returncode})")


def temp_in(gfx: Path, cid: str) -> Path:
    """a new file with an unguessable name (O_EXCL): nothing planted in a synced gfx/ can redirect the write"""
    fd, name = tempfile.mkstemp(dir=gfx, prefix=f".{cid}.", suffix=".part.mov")
    umask = os.umask(0); os.umask(umask)
    os.fchmod(fd, 0o666 & ~umask)  # the card ends up with the folder's usual mode, not mkstemp's 0600
    os.close(fd)
    return Path(name)


def sweep(gfx: Path, cid: str) -> None:
    """temp files of this card left by a killed run (SIGKILL skips finally); a younger one may be a run still going"""
    now = time.time()
    for p in gfx.glob(f".{cid}.*.part.mov"):
        with contextlib.suppress(FileNotFoundError):  # gone in between: a run finishing at the same time
            if now - p.lstat().st_mtime > STALE_PART:
                p.unlink()


def on_term(*_) -> None:
    """run_v4.sh's timeout sends SIGTERM: say so, and let the finally blocks remove the half-written file"""
    sys.exit("FAILED behind: stopped by SIGTERM (run_v4.sh timeout 3600 s?)")


def main(argv: list[str]) -> int:
    args = argv[1:]
    only = args[args.index("--edl") + 1] if "--edl" in args else None
    specs_p, gfx = Path(args[0]), Path(args[1])
    signal.signal(signal.SIGTERM, on_term)
    low_priority()
    rc = 0
    try:
        specs = json.loads(specs_p.read_text())
    except (OSError, ValueError) as e:
        print(f"FAILED behind: {specs_p}: {e}", file=sys.stderr, flush=True)
        return 1
    for sp in specs:
        if not sp.get("behind"):
            continue
        if only and sp["behind"].get("edl") != only:
            print(f"behind {sp.get('id')}: for {sp['behind'].get('edl')}, not {only}", flush=True)  # a typo shows in render.log
            continue
        try:
            print("behind", process(sp, gfx, specs_p.resolve().parent, strict=only is not None), flush=True)
        except BehindError as e:
            if only is None and not isinstance(e, BadName):  # render.mjs: an EDL run_v4.sh has not rebuilt yet; --edl fails for real
                print(f"behind {sp.get('id')}: left for run_v4.sh: {e}", flush=True)
                continue
            print(f"FAILED behind {sp.get('id')}: {e}", file=sys.stderr, flush=True); rc = 1
        except (subprocess.SubprocessError, OSError, ValueError, KeyError) as e:
            print(f"FAILED behind {sp.get('id')}: {e}", file=sys.stderr, flush=True); rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
