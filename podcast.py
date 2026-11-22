#!/usr/bin/env python3
"""podcast.py edl.json: the framing pass for a two-person podcast (plan "podcast", ADR-0030), run by face_track.py in its place.

face_track.py frames one speaker. Here the EDL's pieces are cut again where the shot changes (podcast_shots.py), and every
piece gets the fields assemble.py already reads, so the render needs no second code path for a single shot:
- 16:9 "L" / "R": "face" = that person's face, a static "zoom" (single_zoom): a punch-in from the wide shot (virtual multicam)
- 16:9 "wide": "face" = between the two faces, "zoom" = wide_zoom (the two-shot)
- 9:16 "L" / "R": "face" = that person's face, zoom 1 (the full-height 9:16 window holds one face)
- 9:16 "stack": "stack" = [[fx, fy] of L, [fx, fy] of R]: assemble.py puts L in the top half and R in the bottom half
plus "shot", "spk" (who has the floor) and "head" (the box head_check.py looks for). A 16:9 side card (gfx_types.SIDE_BOX)
over a wide shot would cover one person: the shot under it becomes the speaker's single shot (face centred by the crop,
critic C2 knows it, ADR-0030).
The shot rules run on FILM time (only the kept words, joined as the film plays), so the opening wide, the hold and the
cutaways count what the viewer sees; a shot change is moved to the nearest pause between words (each piece fades its
sound in and out over 12 ms in assemble.py: never inside a word).
Speakers come from podcast_faces.py (mouth motion), cached in podcast_spk.json next to the EDL; podcast_fix.json there
overrides stretches by hand ([[t0, t1, "L"|"R"], ...], recording seconds).
"""
import hashlib
import json
import os
import sys
from itertools import pairwise
from pathlib import Path

import edl_guard
import podcast_faces
import podcast_shots
import timeline
from gfx_types import SIDE_BOX

FPS = 30
SNAP_S = 1.0  # a shot change moves at most this far to reach a pause between words
ALGO = 2  # bump when podcast_faces' speaker or box logic changes: the cache is then measured again


def ranges_of(segments):
    """the recording stretches the film uses, merged where they touch"""
    out = []
    for s in sorted(segments, key=lambda s: s["in"]):
        if out and s["in"] <= out[-1][1] + 0.05: out[-1][1] = max(out[-1][1], s["out"])
        else: out.append([s["in"], s["out"]])
    return out


def film_starts(segments, exact):
    """film second where each piece starts (timeline.piece_len: whole frames with seg_exact)"""
    acc, out = 0.0, []
    for s in segments:
        out.append(acc); acc += timeline.piece_len(s, exact)
    return out, acc


def film_words(words, spk, segments, starts):
    """the kept words on film time: (from, to, text) and their speakers, in film order"""
    fw, fs = [], []
    for s, f0 in zip(segments, starts, strict=True):
        for (a, b, t), k in zip(words, spk, strict=True):
            if s["in"] <= (a + b) / 2 < s["out"]:
                fw.append((f0 + max(a, s["in"]) - s["in"], f0 + min(b, s["out"]) - s["in"], t)); fs.append(k)
    return fw, fs


def snap(shots, fw, cuts):
    """move every shot change to the nearest pause between words (or piece join) within SNAP_S"""
    gaps = [(x[1] + y[0]) / 2 for x, y in pairwise(fw) if y[0] >= x[1]] + list(cuts)
    if not gaps or len(shots) < 2: return shots
    out = [list(x) for x in shots]
    for i in range(1, len(out)):
        x = out[i][0]; g = min(gaps, key=lambda g: abs(g - x))
        if abs(g - x) <= SNAP_S and out[i - 1][0] < g < out[i][1]: out[i - 1][1] = out[i][0] = round(g, 3)
    return podcast_shots.merge(out)


def split_points(seg, f0, shots):
    """film-time shot changes inside a piece -> recording seconds, on whole frames from the piece start; the last piece
    keeps the frame count of the piece it came from (timeline.piece_frames rounds each piece: a .5 tie is avoided)"""
    a, b = seg["in"], seg["out"]; total = timeline.piece_frames(seg)
    ns = []
    for x0, _, _ in shots[1:]:
        n = round((x0 - f0) * FPS)
        if 0 < n < total and (not ns or n > ns[-1]): ns.append(n)
    if ns and ns[-1] + timeline.piece_frames({"in": a + ns[-1] / FPS, "out": b}) != total:
        ns[-1] += 1 if ns[-1] + 1 < total else -1
        if len(ns) > 1 and ns[-1] <= ns[-2]: ns.pop()
    return [round(a + n / FPS, 6) for n in ns]


def centre(box):
    x, y, w, h = box
    return [round(x + w / 2, 4), round(y + h / 2, 4)]


def head(box):
    """face box grown for hair and chin (like face_track.py), as x0, y0, x1, y1"""
    x, y, w, h = box
    return [round(v, 4) for v in (x - 0.15 * w, y - 0.6 * h, x + w * 1.15, y + h * 1.25)]


def frame_piece(p, shot, spk, faces, cfg, vertical):
    """the assemble.py fields of one piece; faces {"L": box, "R": box}. One face only: its single shot (a stack would show
    the same person twice). No face: the piece stays as build_edl made it and the report counts it."""
    for k in ("track", "stack", "shot", "spk"): p.pop(k, None)  # a re-run on the same EDL must not keep an old stack
    if not faces: return p
    if len(faces) == 1 and shot in ("stack", "wide", "L", "R"):
        shot = next(iter(faces))
    p["shot"], p["spk"] = shot, spk
    if shot == "stack":
        p["stack"] = [centre(faces["L"]), centre(faces["R"])]; p["zoom"] = 1.0
        p["face"], p["head"] = centre(faces[spk]), head(faces[spk]); return p
    if shot == "wide":
        (lx, ly), (rx, ry) = centre(faces["L"]), centre(faces["R"])
        p["face"] = [round((lx + rx) / 2, 4), round((ly + ry) / 2, 4)]
        hl, hr = head(faces["L"]), head(faces["R"]); p["head"] = [min(hl[0], hr[0]), min(hl[1], hr[1]), max(hl[2], hr[2]), max(hl[3], hr[3])]
        p["zoom"] = 1.0 if vertical else cfg["wide_zoom"]; return p
    p["face"], p["head"] = centre(faces[shot]), head(faces[shot])
    p["zoom"] = 1.0 if vertical else cfg["single_zoom"]
    return p


def specs_of(E):
    f = E.get("gfx_specs")
    specs = json.loads(Path(f).read_text()) if f and os.path.isfile(f) else {}
    return {s.get("id"): s for s in specs} if isinstance(specs, list) else specs


def card_spans(E, specs):
    """film-time spans of 16:9 cards over the side of the picture (they would cover one of the two people)"""
    return [(o["at"], o["at"] + o["dur"]) for o in E.get("overlays", [])
            if (specs.get(o.get("id")) or {}).get("type") in SIDE_BOX and (specs.get(o.get("id")) or {}).get("canvas") != "v"]


def faces_lookup(faces_by_window):
    """{"t0-t1": {"L": box, "R": box}} (recording seconds) -> faces_at(t): the window holding t, else the nearest one"""
    wins = sorted((tuple(map(float, k.split("-"))), v) for k, v in faces_by_window.items())
    def faces_at(t):
        hit = [v for (a, b), v in wins if a - 0.05 <= t <= b + 0.05]
        if hit: return hit[0]
        return min(wins, key=lambda w: min(abs(t - w[0][0]), abs(t - w[0][1])))[1] if wins else {}
    return faces_at


def reframe(E, spk_words, words, faces_by_window, cfg):
    """the EDL with its pieces cut at shot changes and framed; pure (tests call it without video) -> (EDL, shots, report)"""
    vertical, exact = bool(E.get("vertical")), bool(E.get("seg_exact"))
    segs = E["segments"]; starts, _ = film_starts(segs, exact)
    fw, fs = film_words(words, spk_words, segs, starts)
    tn = podcast_shots.turns(fw, fs, cfg)
    if not tn: sys.exit("podcast: no speaker found for any kept word (no faces?): fix with podcast_fix.json")
    shots = podcast_shots.short_shots(tn, cfg) if vertical else podcast_shots.long_shots(tn, cfg)
    shots = snap(shots, fw, starts[1:])
    faces_at = faces_lookup(faces_by_window)
    specs = specs_of(E)
    sides = [] if vertical else card_spans(E, specs)
    behind = [(o["at"], o["at"] + o["dur"]) for o in E.get("overlays", []) if (specs.get(o.get("id")) or {}).get("behind")]
    out, report = [], {"no_face": 0, "behind_on_stack": 0}
    for s, f0 in zip(segs, starts, strict=True):
        pts = split_points(s, f0, shots)
        for a, b in zip([s["in"], *pts], [*pts, s["out"]], strict=True):
            p = dict(s); p["in"], p["out"] = a, b
            fa = f0 + (a - s["in"]); fb = fa + timeline.piece_len(p, exact); mid = (fa + fb) / 2
            shot, who = podcast_shots.shot_at(shots, mid), podcast_shots.shot_at(tn, mid)
            if shot == "wide" and any(c0 < fb and fa < c1 for c0, c1 in sides): shot = who
            faces = faces_at((a + b) / 2)
            if not faces: report["no_face"] += 1
            p = frame_piece(p, shot, who, faces, cfg, vertical)
            if p.get("stack") and any(c0 < fb and fa < c1 for c0, c1 in behind): report["behind_on_stack"] += 1
            out.append(p)
    E = dict(E); E["segments"] = out
    return E, shots, report


def words_of(E):
    f = E.get("words")
    if not f or not os.path.isfile(f): sys.exit(f"podcast: the EDL needs \"words\" (the plan's .cw.json), got {f!r}")
    return [(x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000, x["text"]) for x in json.loads(Path(f).read_text())["transcription"]]


def probe(src):
    import cv2
    cap = cv2.VideoCapture(src); w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT); cap.release()
    if not w or not h: sys.exit(f"podcast: cannot read the size of {src}")
    return int(w), int(h)


def cache_key(src, ranges, words, cfg):
    """the speaker cache is valid for this recording, these stretches, these words (times and text) and this algorithm"""
    return hashlib.md5(json.dumps([ALGO, src, os.path.getsize(src), os.path.getmtime(src), ranges, words, cfg["detect_fps"],
                                   cfg["face_every_s"], cfg["mouth_ratio"]]).encode()).hexdigest()


def write_atomic(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp"); tmp.write_text(text); os.replace(tmp, path)


def main(edl_p):
    E = json.loads(Path(edl_p).read_text())
    try:
        edl_guard.check(E)  # before ffmpeg and OpenCV open the source: the same rules as assemble.py (ADR-0006)
    except edl_guard.EdlError as e:
        sys.exit(f"podcast.py {edl_p}: {e}")
    work = os.path.dirname(os.path.abspath(edl_p))
    over = E["podcast"] if isinstance(E.get("podcast"), dict) else {}
    cfg = podcast_shots.load_cfg(over)
    src = E["sources"]["A"]; words = words_of(E)
    E["src_w"], E["src_h"] = probe(src)  # assemble.py crops in recording pixels (default 2560x1440 is wrong for 4K)
    ranges = ranges_of(E["segments"])
    key = cache_key(src, ranges, words, cfg)
    cache_p = Path(work) / "podcast_spk.json"
    cache = json.loads(cache_p.read_text()) if cache_p.is_file() else {}
    if cache.get("key") != key:
        print(f"podcast: measuring faces and mouths in {len(ranges)} stretches, {sum(b - a for a, b in ranges):.0f} s of recording", flush=True)
        samples, boxes = podcast_faces.analyse(src, ranges, cfg)
        cache = {"key": key, "spk": podcast_faces.word_speakers(words, samples, cfg["mouth_ratio"]), "faces": boxes}
        write_atomic(cache_p, json.dumps(cache))
    spk = podcast_faces.apply_fix(words, cache["spk"], podcast_faces.load_fix(work))
    E["stack_zoom"] = E.get("stack_zoom", cfg["stack_zoom"])
    E, shots, rep = reframe(E, spk, words, cache["faces"], cfg)
    write_atomic(Path(edl_p), json.dumps(E, ensure_ascii=False, indent=1))
    used = [i for i, (a, b, _) in enumerate(words) if any(r0 <= (a + b) / 2 < r1 for r0, r1 in ranges)]
    unsure = sum(1 for i in used if spk[i] == "?")
    count = {k: sum(1 for x in shots if x[2] == k) for k in ("wide", "L", "R", "stack")}
    print(f"podcast: {len(E['segments'])} pieces, shots {count}, words without a clear speaker {unsure}/{len(used)}"
          + (" (check podcast_fix.json)" if used and unsure / len(used) > 0.2 else "")
          + (f", {rep['no_face']} pieces without a face (left as built)" if rep["no_face"] else "")
          + (f", {rep['behind_on_stack']} stack pieces under a 'behind' card (the matte follows the full picture, check them)"
             if rep["behind_on_stack"] else ""))


if __name__ == "__main__":
    main(sys.argv[1])
