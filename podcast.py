#!/usr/bin/env python3
"""podcast.py edl.json: the framing pass for a two-person podcast (plan "podcast", ADR-0030), run by face_track.py in its place.

face_track.py frames one speaker. Here the EDL's pieces are cut again where the shot changes (podcast_shots.py), and every
piece gets the fields assemble.py already reads, so the render needs no second code path for a single shot:
- 16:9 "L" / "R": "face" = that person's face, a static "zoom" (single_zoom): a punch-in from the wide shot (virtual multicam)
- 16:9 "wide": "face" = between the two faces, "zoom" = wide_zoom (the two-shot)
- 9:16 "L" / "R": "face" = that person's face, zoom 1 (the full-height 9:16 window holds one face)
- 9:16 "stack": "stack" = [[fx, fy] of L, [fx, fy] of R]: assemble.py puts L in the top half and R in the bottom half
plus "shot", "spk" (who has the floor) and "head" (the box head_check.py looks for). A 16:9 side card (gfx_types.SIDE_BOX)
over a wide shot would cover one person: the shot under it becomes the speaker's single shot.
Speakers come from podcast_faces.py (mouth motion), cached in podcast_spk.json next to the EDL; podcast_fix.json there
overrides stretches by hand ([[t0, t1, "L"|"R"], ...], recording seconds).
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import podcast_faces
import podcast_shots
from gfx_types import SIDE_BOX

FPS = 30


def ranges_of(segments):
    """the recording stretches the film uses, merged where they touch"""
    out = []
    for s in sorted(segments, key=lambda s: s["in"]):
        if out and s["in"] <= out[-1][1] + 0.05: out[-1][1] = max(out[-1][1], s["out"])
        else: out.append([s["in"], s["out"]])
    return out


def split_points(seg, shots):
    """shot changes inside a piece, snapped to whole frames from the piece start (the pieces then add up to the same
    frame count as the one they replace: timeline.piece_len rounds each piece)"""
    a, b = seg["in"], seg["out"]
    pts = []
    for x0, _, _ in shots[1:]:
        if a < x0 < b:
            n = round((x0 - a) * FPS)
            if 0 < n < round((b - a) * FPS): pts.append(round(a + n / FPS, 6))
    return sorted(set(pts))


def centre(box):
    x, y, w, h = box
    return [round(x + w / 2, 4), round(y + h / 2, 4)]


def head(box):
    """face box grown for hair and chin (like face_track.py), as x0, y0, x1, y1"""
    x, y, w, h = box
    return [round(v, 4) for v in (x - 0.15 * w, y - 0.6 * h, x + w * 1.15, y + h * 1.25)]


def frame_piece(p, shot, spk, faces, cfg, vertical):
    """the assemble.py fields of one piece; faces {"L": box, "R": box} (a missing side falls back to the other)"""
    fl, fr = faces.get("L") or faces.get("R"), faces.get("R") or faces.get("L")
    if not fl or not fr: return p  # no face found in this stretch: leave the piece as build_edl made it
    for k in ("track",): p.pop(k, None)
    p["shot"], p["spk"] = shot, spk
    if shot == "stack":
        p["stack"] = [centre(fl), centre(fr)]; p["zoom"] = 1.0
        p["face"] = centre(faces.get(spk) or fl); p["head"] = head(faces.get(spk) or fl); return p
    if shot == "wide":
        (lx, ly), (rx, ry) = centre(fl), centre(fr)
        p["face"] = [round((lx + rx) / 2, 4), round((ly + ry) / 2, 4)]
        hl, hr = head(fl), head(fr); p["head"] = [min(hl[0], hr[0]), min(hl[1], hr[1]), max(hl[2], hr[2]), max(hl[3], hr[3])]
        p["zoom"] = 1.0 if vertical else cfg["wide_zoom"]; return p
    box = faces.get(shot) or fl
    p["face"], p["head"] = centre(box), head(box)
    p["zoom"] = 1.0 if vertical else cfg["single_zoom"]
    return p


def card_spans(E):
    """output-time spans of 16:9 cards over the side of the picture (they would cover one of the two people)"""
    f = E.get("gfx_specs")
    specs = json.loads(Path(f).read_text()) if f and os.path.isfile(f) else {}
    if isinstance(specs, list): specs = {s.get("id"): s for s in specs}
    return [(o["at"], o["at"] + o["dur"]) for o in E.get("overlays", [])
            if (specs.get(o.get("id")) or {}).get("type") in SIDE_BOX and (specs.get(o.get("id")) or {}).get("canvas") != "v"]


def reframe(E, spk_words, words, faces_by_range, cfg):
    """the EDL with its pieces cut at shot changes and framed; pure (tests call it without video)"""
    vertical = bool(E.get("vertical"))
    tn = podcast_shots.turns(words, spk_words, cfg)
    if not tn: sys.exit("podcast: no speaker found for any word (no faces?): fix with podcast_fix.json")
    shots = podcast_shots.short_shots(tn, cfg) if vertical else podcast_shots.long_shots(tn, cfg)
    ranges = sorted((tuple(map(float, k.split("-"))), v) for k, v in faces_by_range.items())
    def faces_at(t):
        return next((v for (a, b), v in ranges if a - 0.05 <= t <= b + 0.05), {})
    out, t_out = [], 0.0
    sides = [] if vertical else card_spans(E)
    for s in E["segments"]:
        pts = split_points(s, shots)
        for a, b in zip([s["in"], *pts], [*pts, s["out"]], strict=True):
            p = dict(s); p["in"], p["out"] = a, b
            mid = (a + b) / 2
            shot, who = podcast_shots.shot_at(shots, mid), podcast_shots.shot_at(tn, mid)
            if shot == "wide" and any(c0 < t_out + (b - a) and t_out < c1 for c0, c1 in sides): shot = who
            out.append(frame_piece(p, shot, who, faces_at(mid), cfg, vertical)); t_out += b - a
    E = dict(E); E["segments"] = out
    return E, shots


def words_of(E):
    f = E.get("words")
    if not f or not os.path.isfile(f): sys.exit(f"podcast: the EDL needs \"words\" (the plan's .cw.json), got {f!r}")
    return [(x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000, x["text"]) for x in json.loads(Path(f).read_text())["transcription"]]


def probe(src):
    import cv2
    cap = cv2.VideoCapture(src); w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT); cap.release()
    if not w or not h: sys.exit(f"podcast: cannot read the size of {src}")
    return int(w), int(h)


def main(edl_p):
    E = json.loads(Path(edl_p).read_text())
    work = os.path.dirname(os.path.abspath(edl_p))
    over = E["podcast"] if isinstance(E.get("podcast"), dict) else {}
    cfg = podcast_shots.load_cfg(over)
    src = E["sources"]["A"]; words = words_of(E)
    E["src_w"], E["src_h"] = probe(src)  # assemble.py crops in recording pixels (default 2560x1440 is wrong for 4K)
    ranges = ranges_of(E["segments"])
    key = hashlib.md5(json.dumps([src, os.path.getsize(src), ranges, len(words), cfg["detect_fps"], cfg["face_every_s"],
                                  cfg["mouth_ratio"]]).encode()).hexdigest()
    cache_p = Path(work) / "podcast_spk.json"
    cache = json.loads(cache_p.read_text()) if cache_p.is_file() else {}
    if cache.get("key") != key:
        samples, boxes = podcast_faces.analyse(src, ranges, cfg)
        cache = {"key": key, "spk": podcast_faces.word_speakers(words, samples, cfg["mouth_ratio"]), "faces": boxes}
        cache_p.write_text(json.dumps(cache))
    spk = podcast_faces.apply_fix(words, cache["spk"], podcast_faces.load_fix(work))
    E["stack_zoom"] = E.get("stack_zoom", cfg["stack_zoom"])
    E, shots = reframe(E, spk, words, cache["faces"], cfg)
    Path(edl_p).write_text(json.dumps(E, ensure_ascii=False, indent=1))
    used = [i for i, (a, b, _) in enumerate(words) if any(r0 <= a < r1 for r0, r1 in ranges)]
    unsure = sum(1 for i in used if cache["spk"][i] == "?")
    count = {k: sum(1 for x in shots if x[2] == k) for k in ("wide", "L", "R", "stack")}
    print(f"podcast: {len(E['segments'])} pieces, shots {count}, words without a clear speaker {unsure}/{len(used)}"
          + (" (check podcast_fix.json)" if used and unsure / len(used) > 0.2 else ""))


if __name__ == "__main__":
    main(sys.argv[1])
