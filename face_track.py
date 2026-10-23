#!/usr/bin/env python3
"""face_track.py edl.json  — per-segment face position + zoom safety (head never leaves the frame).
Samples 3 frames per segment, detects the face (OpenCV YuNet), stores seg["face"]=[cx,cy] (normalised) and
seg["head"]=[x0,y0,x1,y1] (face box grown for hair/chin), then clamps every zoom so the head box fits the crop
with a margin. Writes back into edl.json. Cache: <edl>.faces.json
With plan "steady_x" (16:9) seg["face"][0] is where the crop aims (steady face, see steady_anchors), not the raw detection."""
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

edl_p = sys.argv[1]; E = json.loads(Path(edl_p).read_text())
src = E["sources"]["A"]; vertical = E.get("vertical", False)
cache_p = os.path.join(os.path.dirname(os.path.abspath(edl_p)), "faces_cache.json")
cache = json.loads(Path(cache_p).read_text()) if os.path.exists(cache_p) else {}
det = cv2.FaceDetectorYN.create("/home/kamil-jan/video-pipeline/models/face_detection_yunet_2023mar.onnx", "", (640, 360), 0.7)
cap = cv2.VideoCapture(src); SW = cap.get(cv2.CAP_PROP_FRAME_WIDTH); SH = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
def face_at(t):
    k = f"{t:.2f}"
    if k in cache: return cache[k]
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
    r = None
    if ok:
        sm = cv2.resize(fr, (640, 360)); _, faces = det.detect(sm)
        if faces is not None and len(faces):
            f = max(faces, key=lambda f: f[2] * f[3]); x, y, w, h = f[:4] / [640, 360, 640, 360]
            r = [float(x), float(y), float(w), float(h)]
    cache[k] = r; return r

def track_segment(s, step=0.2):
    """Dense face x-track inside one segment (every `step` s), smoothed into a calm camera path.
    Returns [[t_rel, cx], ...] keyframes every 0.4 s and the widest head span seen (for zoom safety)."""
    d = s["out"] - s["in"]; n = max(2, int(d / step) + 1); xs = []; spans = []
    for k in range(n):
        t = s["in"] + min(d - 0.05, k * step)
        f = face_at(t)
        xs.append(None if not f else f[0] + f[2] / 2)
        if f: spans.append((f[0] - 0.15 * f[3] * SH / SW, f[0] + f[2] + 0.15 * f[3] * SH / SW))
    known = [(i, x) for i, x in enumerate(xs) if x is not None]
    if not known: return None, None
    # fill gaps by nearest known value
    for i in range(n):
        if xs[i] is None: xs[i] = min(known, key=lambda kx: abs(kx[0] - i))[1]
    # dead zone: camera only follows when the face drifts > 2.5% of frame width from where the camera points
    cam = [xs[0]]
    for x in xs[1:]:
        c = cam[-1]
        cam.append(c + (x - c - 0.025) if x - c > 0.025 else c + (x - c + 0.025) if c - x > 0.025 else c)
    # gaussian smoothing (~0.8 s) and speed limit (max 6% of width per second)
    sig = max(1, int(0.4 / step)); ker = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2); ker /= ker.sum()
    sm = np.convolve(np.pad(cam, 3 * sig, mode="edge"), ker, mode="valid")
    for i in range(1, len(sm)):
        lim = 0.06 * step; sm[i] = sm[i - 1] + max(-lim, min(lim, sm[i] - sm[i - 1]))
    keys = [[round(min(d, i * step), 3), round(float(sm[i]), 4)] for i in range(0, n, max(1, int(0.4 / step)))]
    if keys[-1][0] < d - 0.01: keys.append([round(d, 3), round(float(sm[-1]), 4)])
    return keys, (min(a for a, b in spans), max(b for a, b in spans))

M = 0.04  # margin around the head inside the crop (fraction of crop)


def fits(z, fx, fy, TY, head):
    """the head box (x0, y0, x1, y1) stays inside the clamped crop at zoom z, margin M"""
    hx0, hy0, hx1, hy1 = head
    cw = ((SH * 9 / 16) / SW) / z if vertical else 1.0 / z; ch = 1.0 / z
    cx0 = min(max(fx - cw / 2, 0), 1 - cw); cy0 = min(max(fy - ch * (TY if TY is not None else fy), 0), 1 - ch)
    mx, my = M * cw, M * ch
    return hx0 >= cx0 + mx and hx1 <= cx0 + cw - mx and hy0 >= cy0 + my and hy1 <= cy0 + ch - my


def zmax_at(fx, fy, TY, head):
    """largest zoom that keeps the head inside the actual (clamped) crop, same maths as assemble.py"""
    lo, hi = 1.0, 2.0
    if not fits(1.0, fx, fy, TY, head): return 1.0
    for _ in range(20):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if fits(mid, fx, fy, TY, head) else (lo, mid)
    return round(lo, 3)


def seg_faces(s):
    d = s["out"] - s["in"]; ts = [s["in"] + 0.1, s["in"] + d / 2, max(s["in"] + 0.1, s["out"] - 0.1)]
    return [f for f in (face_at(t) for t in ts) if f]


def steady_anchors(window):
    """plan "steady_x" (16:9 only): the median face x of the shots within +-window s of output time, used instead of each
    shot's own detection, so a jump cut no longer slides the picture sideways by detector jitter"""
    xs, mids, acc = [], [], 0.0
    for s in E["segments"]:
        d = s["out"] - s["in"]; fs = seg_faces(s)
        xs.append((min(f[0] for f in fs) + max(f[0] + f[2] for f in fs)) / 2 if fs else None); mids.append(acc + d / 2); acc += d
    return [round(float(np.median(near)), 4) if (near := [x for x, m in zip(xs, mids) if x is not None and abs(m - mi) <= window]) else None
            for mi in mids]


def steady_window(v):
    """plan "steady_x": true = +-45 s, a number = +-that many seconds; anything else is a named error, never a silent default"""
    if isinstance(v, bool): return 45.0
    if isinstance(v, (int, float)) and v > 0: return float(v)
    sys.exit(f"face_track: steady_x must be true or seconds > 0, got {v!r}")


steady = None
if E.get("steady_x") and not vertical:
    steady = steady_anchors(steady_window(E["steady_x"]))
fallback = E.get("face", [0.52, 0.42]); clamped = 0; missing = 0; steadied = 0
for si, s in enumerate(E["segments"]):
    fs = seg_faces(s)
    if not fs:
        missing += 1; s["face"] = fallback; continue
    x0 = min(f[0] for f in fs); y0 = min(f[1] for f in fs); x1 = max(f[0] + f[2] for f in fs); y1 = max(f[1] + f[3] for f in fs)
    h = max(f[3] for f in fs)
    hx0, hy0, hx1, hy1 = x0 - 0.15 * h * SH / SW, y0 - 0.45 * h, x1 + 0.15 * h * SH / SW, y1 + 0.25 * h  # hair above, chin below
    if vertical:
        keys, span = track_segment(s)
        if keys:
            s["track"] = keys
            # horizontal safety now only depends on head width (camera follows the face)
            hw = max(q[2] for q in fs) + 0.3 * h * SH / SW  # one head width (face + ears/hair), not the movement range
            cxm = (x0 + x1) / 2; hx0, hx1 = cxm - hw / 2, cxm + hw / 2
    s["head"] = [round(v, 4) for v in (hx0, hy0, hx1, hy1)]
    s["face"] = [round((x0 + x1) / 2, 4), round((y0 + y1) / 2, 4)]
    fx, fy = s["face"]; TY = E.get("face_target_y", 0.40 if vertical else None)
    head = (hx0, hy0, hx1, hy1)
    z = s["zoom"]
    anchor = steady[si] if steady else None
    if anchor is not None:
        # aim so the (steady) face keeps the screen x it has in the full frame at the shot's opening zoom: every cut is
        # then a punch into the face, never a sideways slide; only when it costs this shot no zoom (head still fits)
        z0 = z if not isinstance(z, dict) else (z["keys"][0][1] if z.get("keys") else z["a"])
        z0 = min(z0, zmax_at(fx, fy, TY, head))  # the zoom the shot really opens with after the head clamp
        aim = round(anchor + (0.5 - anchor) / z0, 4)
        want = z if not isinstance(z, dict) else max([z["a"], z["b"], *(v for _, v in z.get("keys", []))])
        if aim != fx and zmax_at(aim, fy, TY, head) >= min(want, zmax_at(fx, fy, TY, head)) - 1e-3:
            s["face"][0] = fx = aim; steadied += 1
    zmax = zmax_at(fx, fy, TY, head)
    s["zmax"] = zmax
    if isinstance(z, dict) and "beat_fx" in E and (z.get("keys") or z["t1"] - z["t0"] < 1.0) and max([z["b"], *(v for _, v in z.get("keys", []))]) > zmax:
        # editing grammar: a moment's punch must stay visible, so each move keeps its size and slides down under
        # the head limit (that move starts wider) instead of being flattened (also a punch on the shot's first word, t0 = 0); slow drift (whole shot) is clamped as before
        from beatfx import fit_moves
        k = fit_moves(z.get("keys") or [[0.0, z["a"]], [z["t0"], z["a"]], [z["t1"], z["b"]]], zmax)
        if z.get("keys"): z["keys"] = k
        z["a"], z["b"] = k[0][1], max(v for _, v in k)
        clamped += 1
    elif isinstance(z, dict):
        a, b = min(z["a"], zmax), min(z["b"], zmax)
        if (a, b) != (z["a"], z["b"]): clamped += 1
        z["a"], z["b"] = a, b
        if z.get("keys"): z["keys"] = [[t, min(v, zmax)] for t, v in z["keys"]]  # several moves in one shot (plan "beats")
        if abs(a - b) < 0.005 and not (z.get("keys") and len({v for _, v in z["keys"]}) > 1): s["zoom"] = a
    elif z > zmax: s["zoom"] = zmax; clamped += 1
Path(cache_p).write_text(json.dumps(cache))
Path(edl_p).write_text(json.dumps(E, indent=1, ensure_ascii=False))
print(f"faces: {len(E['segments'])} segs, {missing} bez twarzy (fallback), {clamped} zoomów przyciętych do bezpiecznego"
      + (f", {steadied} ujęć z kadrem kroczącym (steady_x)" if steady else ""))
