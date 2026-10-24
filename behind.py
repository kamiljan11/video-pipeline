#!/usr/bin/env python3
"""behind.py gfx_specs.json gfx_dir — text BEHIND the speaker: a card whose spec has "behind": {"edl": "edl_x.json"} gets
the speaker cut out of its alpha, so the film's own picture of the speaker stays on top of the card.

The person comes from a matting model (Robust Video Matting, matte/models/rvm_resnet50_fp32.onnx, onnxruntime in
matte/.venv) run on the film's OUTPUT frames under the card: the recording cut and framed exactly like assemble.py does
(its vf_for is lifted out of assemble.py, so the framing has one owner). The masked card replaces <id>.mov; the card as
rendered stays in <id>.front.mov. Everything after (assemble.py, the panel's live player) just overlays the .mov.
Run by gfx/render.mjs after its renders; a card whose front, EDL window and spec did not change is skipped (<id>.mov.behind).
"""
import ast
import hashlib
import json
import math
import runpy
import subprocess
import sys
import tempfile
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path

import numpy as np

VP = Path(__file__).resolve().parent
MODEL = VP / "matte" / "models" / "rvm_resnet50_fp32.onnx"
MODEL_SHA = "25db300fcb6ee27f941a1b52c97856e8d1f13c7f35817f81a612f89af0e8a85c"  # GitHub PeterL1n/RobustVideoMatting v1.0.0
FPS = 30
WARM = 1.0  # seconds of film fed to the model before the card: its recurrent state settles on the person first


def framing(edl: dict):
    """assemble.py's vf_for(zoom, face, track) for this EDL (same globals as assemble.py sets from the EDL)."""
    src = (VP / "assemble.py").read_text(encoding="utf-8")
    fns: list[ast.stmt] = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in ("vf_for", "keys_expr", "track_expr")]
    vertical = edl.get("vertical", False)
    fx, fy = edl.get("face", [0.5, 0.45])
    ns = {"W": edl.get("w", 2560), "H": edl.get("h", 1440), "SW": edl.get("src_w", 2560), "SH": edl.get("src_h", 1440),
          "FX0": fx, "FY0": fy, "vertical": vertical, "TY": edl.get("face_target_y", 0.40 if vertical else None),
          "E": "\\", "pairwise": pairwise}
    with tempfile.TemporaryDirectory() as d:
        mod = Path(d) / "assemble_framing.py"
        mod.write_text(ast.unparse(ast.Module(body=fns, type_ignores=[])), encoding="utf-8")
        return runpy.run_path(str(mod), init_globals=ns)["vf_for"]


def seg_frames(edl: dict) -> list[int]:
    """frames each segment gets in the film: assemble.py's seg_exact cuts round(d*30); without it ~ the same."""
    return [max(1, round((s["out"] - s["in"]) * FPS)) for s in edl["segments"]]


def film_frames(edl: dict, first: int, n: int, vf_for, size: tuple[int, int]):
    """RGB uint8 frames first..first+n-1 of the film's picture (before graphics), as assemble.py stage 1 cuts them."""
    w, h = size
    start = 0
    for s, k in zip(edl["segments"], seg_frames(edl), strict=True):
        lo, hi = max(first, start), min(first + n, start + k)
        if lo < hi:
            d = k / FPS
            vf = "setpts=PTS-STARTPTS," + vf_for(s.get("zoom", 1.0), s.get("face"), s.get("track"))
            # from the segment start: a dynamic zoom is a function of the frame number in the segment
            with subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{s['in']:.3f}", "-i", edl["sources"][s["src"]], "-t", f"{d:.3f}",
                                   "-vf", vf, "-frames:v", str(hi - start), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE) as p:
                assert p.stdout is not None
                fr = None
                for i in range(start, hi):  # streamed: a card late in a long segment must not hold the whole segment in memory
                    b = p.stdout.read(w * h * 3)
                    if len(b) == w * h * 3:
                        fr = np.frombuffer(b, np.uint8).reshape(h, w, 3)
                    if fr is None:
                        raise RuntimeError(f"behind: ffmpeg gave no frame of {s['src']} at {s['in']:.3f}")
                    if i >= lo:
                        yield fr  # a short decode at the very end repeats its last frame (assemble pads too)
            if p.returncode:
                raise RuntimeError(f"behind: ffmpeg failed on {s['src']} at {s['in']:.3f} (rc {p.returncode})")
        start += k
        if start >= first + n:
            return


class Matter:
    """Robust Video Matting, frame by frame with its recurrent state: rgb uint8 HxWx3 -> person alpha float HxW (0..1)."""

    def __init__(self, ratio: float):
        if not MODEL.exists():
            sys.exit(f"behind: no matting model {MODEL} (see README: text behind the speaker)")
        if hashlib.sha256(MODEL.read_bytes()).hexdigest() != MODEL_SHA:
            sys.exit(f"behind: {MODEL} is not the verified RVM v1.0.0 file (sha256 differs)")
        import onnxruntime as ort  # matte/.venv only; the rest of the pipeline does not need it
        so = ort.SessionOptions(); so.intra_op_num_threads = 16  # of 32: the desktop stays responsive
        self.s = ort.InferenceSession(str(MODEL), so, providers=["CPUExecutionProvider"])
        self.rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
        self.ratio = np.array([ratio], np.float32)

    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        src = (rgb.astype(np.float32) / 255).transpose(2, 0, 1)[None]
        outs = self.s.run(None, {"src": src, "r1i": self.rec[0], "r2i": self.rec[1], "r3i": self.rec[2],
                                 "r4i": self.rec[3], "downsample_ratio": self.ratio})
        self.rec = [np.asarray(r) for r in outs[2:]]
        return np.asarray(outs[1])[0, 0]


def cut_out(rgba: np.ndarray, person: np.ndarray) -> np.ndarray:
    """the card with the person's pixels see-through: alpha * (1 - person); colour untouched."""
    out = rgba.copy()
    out[..., 3] = np.round(rgba[..., 3].astype(np.float32) * (1 - np.clip(person, 0, 1))).astype(np.uint8)
    return out


def card_frames(mov: Path, size: tuple[int, int]) -> np.ndarray:
    w, h = size
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mov), "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                       capture_output=True, check=True, timeout=600)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 4)


def window_key(edl: dict, at: float, n: int) -> list:
    """what the matte depends on: the card's place and the segments under it (+ the warm-up)"""
    first = max(0, math.floor((at - WARM) * FPS)); last = math.ceil(at * FPS) + n
    start, under = 0, []
    for s, k in zip(edl["segments"], seg_frames(edl), strict=True):
        if start < last and start + k > first:
            under.append([start, s])
        start += k
    return [round(at, 3), n, under, {k: edl.get(k) for k in ("w", "h", "face", "src_w", "src_h", "vertical", "face_target_y")}]


def process(spec: dict, gfx: Path, base: Path, matter_for: Callable[[float], Callable[[np.ndarray], np.ndarray]] = Matter) -> str:
    cid = spec["id"]
    mov, front, stamp = gfx / f"{cid}.mov", gfx / f"{cid}.front.mov", gfx / f"{cid}.mov.behind"
    edl = json.loads((base / spec["behind"]["edl"]).read_text())
    o = next((o for o in edl.get("overlays", []) if o.get("id") == cid), None)
    if o is None:
        return f"{cid}: not in {spec['behind']['edl']} (no cut-out)"
    old = json.loads(stamp.read_text()) if stamp.exists() else {}
    sha = hashlib.sha256(mov.read_bytes()).hexdigest()
    if old and sha != old.get("out") and front.exists():
        front.unlink()  # render.mjs made a new card: it is the new front
    if not front.exists():
        mov.rename(front); old = {}
    w, h = edl.get("w", 2560), edl.get("h", 1440)
    rgba = card_frames(front, (w, h))
    key = hashlib.sha256(json.dumps([window_key(edl, o["at"], len(rgba)), hashlib.sha256(front.read_bytes()).hexdigest()],
                                    sort_keys=True).encode()).hexdigest()
    if old.get("key") == key and mov.exists():
        return f"{cid}: up to date"
    # card frame k is on screen at at + k/30 -> film frame ceil((at + k/30) * 30) (overlay shows the last card frame <= t)
    c0 = math.ceil(o["at"] * FPS - 1e-6); first = max(0, math.floor((o["at"] - WARM) * FPS))
    matter = matter_for(spec["behind"].get("ratio", 0.2))
    out = np.empty_like(rgba)
    for i, rgb in enumerate(film_frames(edl, first, c0 - first + len(rgba), framing(edl), (w, h))):
        person = matter(rgb)
        k = first + i - c0
        if k >= 0:
            out[k] = cut_out(rgba[k], person)
    tmp = gfx / f"{cid}.behind.part.mov"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-framerate", str(FPS),
                    "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(tmp)],
                   input=out.tobytes(), check=True, timeout=600)
    tmp.replace(mov)
    stamp.write_text(json.dumps({"key": key, "out": hashlib.sha256(mov.read_bytes()).hexdigest()}))
    return f"{cid}: speaker cut out of {len(rgba)} frames"


def main(argv: list[str]) -> None:
    specs_p, gfx = Path(argv[1]), Path(argv[2])
    for sp in json.loads(specs_p.read_text()):
        if sp.get("behind"):
            print("behind", process(sp, gfx, specs_p.resolve().parent), flush=True)


if __name__ == "__main__":
    main(sys.argv)
