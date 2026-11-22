#!/usr/bin/env python3
"""assemble.py edl.json outdir
edl.json: {"sources": {"A": "/path.mp4"}, "segments": [{"src":"A","in":1.2,"out":5.4,"zoom":1.0}],
           "overlays": [{"file":"gfx/x.mov","at":12.3}], "w":2560, "h":1440,
           "face": [0.53, 0.42], "out_name": "final.mp4", "vertical": false}
Stage 1: each segment -> intermediate (accurate cut, zoom/crop, 12ms audio fades)
Stage 2: concat + overlays + audio master + grade -> final."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path

import av_latency  # next to this script: the voice chain's own delay, taken back
import chunks  # next to this script: stage 2 in time windows (memory flat in the number of cards)
import edl_guard  # next to this script: what an EDL may carry into an ffmpeg command line
import gfx_types  # next to this script: where a 9:16 split card puts the face box
import themes  # next to this script (sys.path[0])
import timeline  # next to this script: film length of each piece (seg_exact = whole frames)
import voice_clean  # next to this script: the voice through DeepFilterNet (EDL "voice_clean")

edl = json.loads(Path(sys.argv[1]).read_text()); out = sys.argv[2]
try:
    edl_guard.check(edl)  # before any ffmpeg: plans and EDLs can arrive over Syncthing (no filter text, protocol or option from them)
except edl_guard.EdlError as e:
    sys.exit(f"assemble.py {sys.argv[1]}: {e}")
os.makedirs(out, exist_ok=True)
# --proxy (editing panel preview): same compositing, fast low-quality encodes, output scaled to 640 px on the long side
# --dry (run_v4.sh DRY=1, dry_run.py): the small picture, but the film's own sound (master included) and the recording
# required, so the checks after the render judge what the full render will sound like
DRY = "--dry" in sys.argv[3:]
PROXY = DRY or "--proxy" in sys.argv[3:]
SEG_ENC = ["-preset", "ultrafast", "-crf", "26"] if PROXY else ["-preset", "veryfast", "-crf", "12"]
# EDL "seg_exact" (plan key, via build_edl): frame-exact segments. Without it every segment's picture is rounded to frames
# and starts 1 frame late while its sound is exact; the joins add up and the picture drifts up to ~1 s behind the voice
# (measured on the 2026-10-22 long: 137 sound gaps = 2.3 s in rough.mkv)
EXACT = bool(edl.get("seg_exact"))
OUT_ENC = ["-preset", "ultrafast", "-crf", "30"] if PROXY else ["-preset", "medium", "-crf", "18"]
# every card is its own ffmpeg input (2560x1440 ProRes 4444 with alpha): with the defaults each one keeps a frame per decoder
# thread (one per core) and a deep input queue, which grew past 60 GB on the 21-min long and got the session killed
# (2026-11-04). Two threads and a 4-frame queue: the first 300 s of that long (31 cards) peak 10.2 GB in 2:38, against
# over 30 GB with the defaults (killed) and 10.1 GB in 4:59 with one thread.
CARD_IN = ["-threads", "2", "-thread_queue_size", "4"]
seg_dir = os.path.join(out, "segs"); os.makedirs(seg_dir, exist_ok=True)
W, H = edl.get("w", 2560), edl.get("h", 1440); fx, fy = edl.get("face", [0.5, 0.45])
vertical = edl.get("vertical", False)
TY = edl.get("face_target_y", 0.40 if edl.get("vertical") else None)

SW, SH = edl.get("src_w", 2560), edl.get("src_h", 1440)
E = "\\"
FX0, FY0 = fx, fy
def vf_for(z, face=None, track=None):
    fx, fy = face if face else (FX0, FY0)
    TX = track_expr(track) if (vertical and track) else None
    # static: crop a window centred on the face; dynamic (dict): subpixel animated zoom via perspective
    if not isinstance(z, dict):
        if vertical:
            cw, ch = f"ih*9/16/{z}", f"ih/{z}"
        else:
            cw, ch = f"iw/{z}", f"ih/{z}"
        x = f"max(0{E},min(iw-{cw}{E},iw*({TX if TX else fx})-{cw}/2))"; y = f"max(0{E},min(ih-{ch}{E},ih*{fy}-{ch}*{TY if TY is not None else fy}))"
        return f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos,setsar=1,fps=30"
    a, b, t0, t1 = z["a"], z["b"], z["t0"], max(z["t1"], z["t0"] + 0.05)
    keys = z.get("keys")  # editing grammar: several moves in one shot, [[t, zoom], ...] eased piecewise (build_edl, plan "beats")
    pre = ""
    rfx, rfy = fx, fy
    if vertical:
        rw = int(SH * 9 / 16) // 2 * 2
        rx = int(min(max(fx * SW - rw / 2, 0), SW - rw)) // 2 * 2
        if TX:
            pre = f"crop={rw}:{SH}:max(0{E},min({SW - rw}{E},({TX})*{SW}-{rw / 2})):0,"; rfx = 0.5
        else:
            pre = f"crop={rw}:{SH}:{rx}:0,"; rfx = (fx * SW - rx) / rw
    Z = f"st(0{E},clip((in/30-{t0:.3f})/{t1 - t0:.3f}{E},0{E},1)){E};st(1{E},{a}+({b}-{a})*ld(0)*ld(0)*(3-2*ld(0))){E};"
    if keys:
        Z = f"st(2{E},in/30){E};st(1{E},{keys_expr(keys)}){E};"
    X0 = f"{Z}clip({rfx:.4f}*W-W/ld(1)/2{E},0{E},W-W/ld(1))"
    X1 = f"{X0}+W/ld(1)"
    Y0 = f"{Z}clip({rfy:.4f}*H-H/ld(1)*{TY if TY is not None else rfy:.4f}{E},0{E},H-H/ld(1))"
    Y1 = f"{Y0}+H/ld(1)"
    persp = f"perspective=x0={X0}:y0={Y0}:x1={X1}:y1={Y0}:x2={X0}:y2={Y1}:x3={X1}:y3={Y1}:interpolation=cubic:eval=frame"
    return f"{pre}fps=30,{persp},scale={W}:{H}:flags=lanczos,setsar=1"


def stack_vf(stack):
    """podcast 9:16 "stack" (podcast.py, ADR-0031): person L in the top half, person R in the bottom half, each cut from
    the recording around its own face (EDL "stack_zoom": recording height / panel crop height), eyes a little above the
    panel middle; numbers only reach the filter (edl_guard: stack = two number pairs)"""
    z, ph = float(edl.get("stack_zoom", 1.8)), H // 2
    ch, cw = f"ih/{z:.4f}", f"ih/{z:.4f}*{W}/{ph}"
    parts = [f"[p{i}]crop={cw}:{ch}:max(0{E},min(iw-{cw}{E},iw*{float(px):.4f}-{cw}/2)):max(0{E},min(ih-{ch}{E},ih*{float(py):.4f}-{ch}*0.42)),"
             f"scale={W}:{ph}:flags=lanczos,setsar=1[q{i}]" for i, (px, py) in enumerate(stack)]
    return f"fps=30,split=2[p0][p1];{parts[0]};{parts[1]};[q0][q1]vstack,setsar=1"


def keys_expr(keys):
    """zoom at time ld(2) through keyframes [[t, z], ...]: smoothstep between neighbours, held before/after"""
    e = f"{keys[-1][1]:.4f}"  # numbers only (format spec), never EDL text pasted into the filtergraph
    for (ta, za), (tb, zb) in reversed(list(pairwise(keys))):
        d = max(tb - ta, 0.001)
        e = f"if(lt(ld(2){E},{tb:.3f}){E},(st(0{E},clip((ld(2)-{ta:.3f})/{d:.3f}{E},0{E},1)){E};{za:.4f}+({zb:.4f}-{za:.4f})*ld(0)*ld(0)*(3-2*ld(0))){E},{e})"
    return f"if(lt(ld(2){E},{keys[0][0]:.3f}){E},{keys[0][1]:.4f}{E},{e})"


def track_expr(track, var="t"):
    """piecewise-linear centre x (0..1) as ffmpeg expression; commas escaped for the filtergraph"""
    if not track: return None
    e = f"{track[-1][1]}"
    for (t0, x0), (t1, x1) in reversed(list(pairwise(track))):
        e = f"if(lt({var}{E},{t1}){E},{x0}+({x1}-{x0})*({var}-{t0})/{max(t1 - t0, 0.001)}{E},{e})"
    return f"if(lt({var}{E},{track[0][0]}){E},{track[0][1]}{E},{e})"

def zkey(z):
    if isinstance(z, dict) and z.get("keys"):  # segment cache name must change with every keyframe
        return f"k{__import__('hashlib').md5(str(z['keys']).encode()).hexdigest()[:10]}"
    return z if not isinstance(z, dict) else f"{z['a']}-{z['b']}-{z['t0']:.2f}-{z['t1']:.2f}"

def seek(s) -> tuple[float, str]:
    """(-ss time on the recording's frame grid, cache-name tag): the tag only where the seek moved, so pieces that were
    already on the grid keep their cached names (timeline.snap_in)"""
    t = timeline.snap_in(s["in"], av_latency.video_start(edl["sources"][s["src"]]))
    return t, (f"_g{t:.4f}" if abs(t + 0.0005 - s["in"]) > 0.001 else "")


def cut(i_s):
    i, s = i_s
    ss, gtag = seek(s)
    dst = os.path.join(seg_dir, f"{i:04d}_{s['in']:.3f}_{s['out']:.3f}_{zkey(s.get('zoom',1.0))}_{'-'.join(str(v) for v in s.get('face', []))}{'_tr' + __import__('hashlib').md5(str(s.get('track')).encode()).hexdigest()[:6] if s.get('track') else ''}{gtag}.mkv")
    if s.get("stack"): dst = dst[:-4] + "_st" + __import__('hashlib').md5(str([s["stack"], edl.get("stack_zoom")]).encode()).hexdigest()[:6] + ".mkv"
    if EXACT: dst = dst[:-4] + "_x.mkv"
    # the crop also depends on face_target_y: without it in the name a re-render after a plan change reused segments cut
    # for the old height (2026-10-25 shorts: fixed-zoom shots kept the 0.40 head line). Only when the key is set, so old
    # EDLs keep their segment names (video-pipeline-panel tests/test_pipeline_compat.py)
    if "face_target_y" in edl: dst = dst[:-4] + f"_ty{TY}.mkv"
    if os.path.exists(dst): return dst
    d = s["out"] - s["in"]
    vf, extra = (stack_vf(s["stack"]) if vertical and s.get("stack") else vf_for(s.get("zoom", 1.0), s.get("face"), s.get("track"))), []
    if EXACT:  # n whole frames from 0 and exactly n/30 s of sound, so the concat below has no gaps for the sound to drift by
        n = max(1, round(d * 30)); d = n / 30
        vf, extra = "setpts=PTS-STARTPTS," + vf, ["-frames:v", str(n)]
    f = min(0.012, d / 4)
    af = f"afade=t=in:d={f},afade=t=out:st={d - f:.3f}:d={f},aresample=48000"
    if EXACT: af = f"asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=0:{d:.6f}," + af
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.4f}", "-i", edl["sources"][s["src"]], "-t", f"{d:.3f}",
                    "-vf", vf, *extra, "-af", af, "-c:v", "libx264", *SEG_ENC,
                    "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ac", "1", dst], check=True)
    return dst

with ThreadPoolExecutor(6) as ex:
    files = list(ex.map(cut, enumerate(edl["segments"])))
lst = os.path.join(out, "concat.txt")
# exact piece lengths in the list: .mkv keeps whole ms and the demuxer would add the rounding up piece by piece
Path(lst).write_text(timeline.concat_list([os.path.abspath(p) for p in files], [timeline.piece_len(sg, EXACT) for sg in edl["segments"]]))
rough = os.path.join(out, "rough.mkv")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", rough], check=True)

# 16:9 picture-in-picture (cards in gfx_types.PIP): the face cam window is cut from the recording itself, one square per
# piece around that piece's head (gfx_types.pip_window), not from the zoomed picture. The old crop sat on the film-wide face
# point of the zoomed frame, so a punch-in or a head off the middle went into the window as on the full screen (Kamil
# 2026-11-05). A piece with no window on screen gets a black square of the same length: pip.mkv runs frame for frame with rough.mkv.
# Only with "head_track": true (plan key, build_edl.py copies it): an EDL without it renders as before, the crop of the
# picture at the film face point (video-pipeline-panel tests/test_pipeline_compat.py, panel CLAUDE.md)
HT = edl.get("head_track") is True
pips = [o for o in edl.get("overlays", []) if o.get("pip")]
PIP_INPUTS = 3 if HT else 2  # stage 2 inputs after the cards when the film has a window: mask, frame (+ pip.mkv); b-roll numbers count on it
PS = edl.get("pip_size", 600)
# 9:16 corner circle (layout "corner", build_edl.py): cut from the recording around the head the same way, head and shoulders
# (Kamil 2026-11-05: the old crop of the zoomed vertical picture was "ultra zoomed twarz, nie jest to profesjonalnie")
corners = [o for o in edl.get("overlays", []) if o.get("corner")] if vertical else []
CN = gfx_types.CORNER
HAIR = gfx_types.HEADROOM[edl.get("punch_headroom", "hair")]  # the room face_track.py left above the face box


def seg_len(s):
    return timeline.piece_len(s, EXACT)


starts = [0.0]
for sg in edl["segments"][:-1]: starts.append(starts[-1] + seg_len(sg))


# ffprobe field -> setparams option. setparams sets the frame's tags (libx264 writes them from the frames) and takes
# ffprobe's names as they are; -color_trc/-color_primaries as encoder options were not written at all (ffmpeg 8, review
# 2026-11-10 code-1: and -color_trc rejects ffprobe's "bt470bg")
COLOUR_KEYS = {"color_space": "colorspace", "color_primaries": "color_primaries", "color_transfer": "color_trc",
               "color_range": "range"}


def colour_tags(path: str) -> dict[str, str]:
    """{setparams option: value} of the colour tags the file's video stream names (unknown ones left out)"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=" + ",".join(COLOUR_KEYS), "-of", "json", path], capture_output=True, text=True, check=True)
    st = (json.loads(r.stdout).get("streams") or [{}])[0]
    return {opt: st[k] for k, opt in COLOUR_KEYS.items() if st.get(k) not in (None, "", "unknown")}


def colour_key(path: str) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(colour_tags(path).items()))


def head_track(name, wins, size, fill):
    """<out>/<name>.mkv, frame for frame with rough.mkv: a size x size square cut from the recording around each piece's
    head (gfx_types.pip_window) where a window in `wins` is on screen, black elsewhere. Pieces are cached in <out>/<name>segs/"""
    seg_dir = os.path.join(out, f"{name}segs"); os.makedirs(seg_dir, exist_ok=True)
    gone = sorted(p for p in edl["sources"].values() if not os.path.exists(p))
    if gone and (DRY or not PROXY): sys.exit(f"assemble: {name} is cut from the recording, missing: {', '.join(gone)}")
    if gone:  # a panel preview of a film whose recording went to the cloud: the square from rough.mkv at the film face point
        print(f"assemble: {name} preview from rough.mkv (recording missing: {', '.join(gone)}), framing not checked", file=sys.stderr)

    # every piece carries the recording's colour tags: black pieces had none, cut ones bt470bg, and the tag change in the
    # joined track made ffmpeg 8 rebuild the stage-2 graph mid-window (setpts from 0 again; film 2026-11-04 v5 long lost
    # 20 s at 980 s). The tags name the black pieces, so pieces made without them are not reused. One track = one set: a
    # film from several recordings takes the first one's tags for every piece (setparams relabels, it does not convert).
    tags = colour_tags(next(iter(edl["sources"].values()))) if not gone else colour_tags(rough)
    set_tags = ",setparams=" + ":".join(f"{k}={v}" for k, v in tags.items()) if tags else ""
    tag_name = "-".join(f"{k}={v}" for k, v in tags.items()) or "untagged"

    def cut(i):
        s, t0 = edl["segments"][i], starts[i]; d = seg_len(s)
        n = max(1, round(d * 30)); frames = ["-frames:v", str(n)] if EXACT else ["-t", f"{d:.3f}"]
        if not any(a < t0 + d and b > t0 for a, b in wins):
            dst = os.path.join(seg_dir, f"{i:04d}_{d:.3f}_{size}_black-{tag_name}{'_x' if EXACT else ''}.mkv")
            src = ["-f", "lavfi", "-i", f"color=c=black:s={size}x{size}:r=30"]; vf = "setsar=1"
        elif gone:
            side = int(min(W, H) * 0.8) // 2 * 2  # 9:16 too: the width bounds it
            x = int(min(max(fx * W - side / 2, 0), W - side)); y = int(min(max(fy * H - side * 0.42, 0), H - side))
            stamp = int(os.path.getmtime(rough))  # a new rough.mkv (other zoom or framing at the same t0) is a new piece
            dst = os.path.join(seg_dir, f"{i:04d}_{t0:.3f}_{d:.3f}_rough{stamp}-{x}-{y}-{side}_{size}{'_x' if EXACT else ''}.mkv")
            src = ["-ss", f"{t0:.3f}", "-i", rough]
            vf = ("setpts=PTS-STARTPTS," if EXACT else "") + f"crop={side}:{side}:{x}:{y},scale={size}:{size}:flags=lanczos,setsar=1,fps=30"
        else:
            if s.get("head"): x, y, side = gfx_types.pip_window(s["head"], SW, SH, HAIR, fill)
            else:  # no face found in this piece: the film-wide face point, as before (said, so a wall in the window has a reason)
                print(f"assemble: piece {i} ({s['in']:.1f}-{s['out']:.1f} s) has no head box, {name} on the film face point", file=sys.stderr)
                # the window of the old crop (fill 0.62 of the frame height for a PiP), scaled to this window's fill
                side = int(min(SH, SW, SH * 0.62 / fill * 0.62)) // 2 * 2
                x = int(min(max(fx * SW - side / 2, 0), SW - side)); y = int(min(max(fy * SH - side * 0.42, 0), SH - side))
            ss, gtag = seek(s)
            dst = os.path.join(seg_dir, f"{i:04d}_{s['in']:.3f}_{s['out']:.3f}_{x}-{y}-{side}_{size}{'_x' if EXACT else ''}{gtag}.mkv")
            src = ["-ss", f"{ss:.4f}", "-i", edl["sources"][s["src"]]]
            vf = ("setpts=PTS-STARTPTS," if EXACT else "") + f"crop={side}:{side}:{x}:{y},scale={size}:{size}:flags=lanczos,setsar=1,fps=30"
        if not os.path.exists(dst):
            subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-vf", vf + set_tags, *frames, "-an", "-c:v", "libx264",
                            *SEG_ENC, "-pix_fmt", "yuv420p", dst + ".part.mkv"], check=True)
            os.replace(dst + ".part.mkv", dst)
        return dst

    with ThreadPoolExecutor(6) as ex:
        files = list(ex.map(cut, range(len(edl["segments"]))))
        found = set(ex.map(colour_key, files))
    if len(found) > 1:  # one track, one set of tags (see above): a mix here loses frames in stage 2
        sys.exit(f"assemble: {name} pieces carry different colour tags {sorted(found)} ({seg_dir}; pieces cut before the"
                 " recording's tags changed: delete that folder, the next run cuts them again)")
    lst = os.path.join(out, f"{name}_concat.txt")
    Path(lst).write_text(timeline.concat_list([os.path.abspath(p) for p in files], [seg_len(sg) for sg in edl["segments"]]))
    track = os.path.join(out, f"{name}.mkv")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", track], check=True)
    return track


pip_track = head_track("pip", [(o["at"] + 0.25, o["at"] + o["dur"] - 0.3) for o in pips], PS, 0.62) if pips and HT else None
corner_track = head_track("corner", [(o["at"], o["at"] + o["dur"]) for o in corners], CN["size"], CN["fill"]) if corners and HT else None

# stage 2
inputs = ["-i", rough]; fc = []
# stage 2 in windows (chunks.py): which inputs are cards (swapped for a stand-in off screen) and which run frame for frame
# with rough.mkv (seeked with the window)
card_slots, aligned = [], [0]
grade = edl.get("grade", "eq=contrast=1.04:saturation=1.07:gamma=0.98,unsharp=5:5:0.35")
tail = edl.get("tail", 0)
body = timeline.total(edl["segments"], EXACT)
THEME = edl.get("theme")  # build_edl from work/theme.json (themes.py): accent of the progress bar and the PiP frame
# "progress": "fill" = a bar that fills with the film time. true = the old drawbox bar, kept for old EDLs (video-pipeline-panel tests/test_pipeline_compat.py):
# drawbox evaluates its w once, so that bar stands full width from the first frame
pbar = (f",drawbox=x=0:y=ih-8:w=iw*min(t/{body:.3f}\\,1):h=8:color=0x{themes.bar_hex(THEME)}@0.85:t=fill:enable=lt(t\\,{body:.3f})"
        if edl.get("progress") and edl.get("progress") != "fill" else "")
# the tail: settb first, or tpad steps its clones 33 ms (the 1/1000 time base of rough.mkv) instead of 1/30 s and two of every
# 300 land on the same frame and are dropped (v5 long: "last window has 4089 frames, not 4091"); the windows cut this same text
TAIL_PAD = f",settb=1/{chunks.FPS},tpad=stop_mode=clone:stop_duration={tail}" if tail else ""
fc.append(f"[0:v]{grade}" + TAIL_PAD + pbar + "[v0]")
last = "v0"
if edl.get("progress") == "fill":  # overlay evaluates x on every frame
    fc.append(f"color=c=0x{themes.bar_hex(THEME)}@0.85:s={W}x8:r=30,format=rgba[pbar]")
    fc.append(f"[v0][pbar]overlay=x='-w+w*min(t/{body:.3f},1)':y=H-8:shortest=1:enable='lt(t,{body:.3f})'[vbar]"); last = "vbar"
# stock b-roll (build_edl "broll"): full-frame cutaway under graphics and captions, picture only (the voice goes on);
# its inputs come after the graphics and the pip images, so their input numbers stay as they were
BROLL = edl.get("broll", [])
i_broll = 1 + len(edl.get("overlays", [])) + (PIP_INPUTS if pips else 0)
for k, b in enumerate(BROLL):
    # cut in the filter, not with input -ss/-itsoffset: a seek lets pre-roll frames through (a frozen frame before "at")
    ss = b.get("ss", 0.0)
    fc.append(f"[{i_broll + k}:v]trim=start={ss:.3f}:duration={b['dur']:.3f},setpts=PTS-STARTPTS+{b['at']:.3f}/TB,"
              f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps=30,format=yuv420p[br{k}]")
    fc.append(f"[{last}][br{k}]overlay=eof_action=pass:format=auto[vb{k}]"); last = f"vb{k}"
# 9:16 "web" card with layout "split" (build_edl.py): the face goes in a box under the card, over the card's own background.
# The box is cut from the picture before the cards (the same frame, zooms included). In that picture the face is at its
# recorded height fy in unzoomed shots and at TY in zoomed ones, so the box aims between the two and puts that point at 58 %
# of its height: the box is wide, so it holds less height than the frame, and aiming at TY alone cut the top of the head
# off (2026-10-31 short1 demo: fy 0.42, TY 0.48)
splits = [o for o in edl.get("overlays", []) if o.get("split")] if vertical else []
# a card may set its own box ("face_box" [x, y, w, h], "face_anchor" = where the face point sits in the box height,
# build_edl.py copies them): a short card leaves room, so the box starts right under it and runs off the bottom edge
R = gfx_types.SPLIT["radius"]
sgroups = {}
for o in splits: sgroups.setdefault((tuple(o.get("face_box") or gfx_types.SPLIT["face_box"]), float(o.get("face_anchor", 0.58)), float(o.get("face_zoom", 1.0))), []).append(o)
if splits:
    fc.append(f"[{last}]split={len(sgroups) + 1}[vsb]" + "".join(f"[splitsrc{i}]" for i in range(len(sgroups)))); last = "vsb"
    for i, ((bx, by, bw, bh), anc, fz) in enumerate(sgroups):
        if fz >= 1.0:
            ch = min(round(bh * W / bw / 2) * 2, H)  # source rows that fill the box at its width
            y0 = int(min(max((fy + TY) / 2 * H - ch * anc, 0), H - ch))
            fc.append(f"[splitsrc{i}]crop={W}:{ch}:0:{y0},scale={bw}:{bh}:flags=lanczos,format=yuva444p[sf{i}]")
        else:  # "face_zoom" < 1: the picture smaller in the middle of the box, its blurred copy filling the box (face not too close)
            iw = int(bw * fz) // 2 * 2; ch = min(round(bh * W / iw / 2) * 2, H); ih = round(ch * iw / W / 2) * 2
            y0 = int(min(max((fy + TY) / 2 * H - ch * anc, 0), H - ch))
            fc.append(f"[splitsrc{i}]crop={W}:{ch}:0:{y0},split=2[sa{i}][sb{i}]")
            fc.append(f"[sb{i}]scale={bw}:-2:flags=bicubic,crop={bw}:{bh}:0:(ih-{bh})*{anc},boxblur=30:2,eq=brightness=-0.06[sbg{i}]")
            fc.append(f"[sa{i}]scale={iw}:{ih}:flags=lanczos[sin{i}]")
            fc.append(f"[sbg{i}][sin{i}]overlay={(bw - iw) // 2}:{bh - ih},format=yuva444p[sf{i}]")
# 9:16 "float" with layout "corner" (build_edl.py): the face in a circle in the corner over a full-screen card; the square is
# cut around the face the same way as the split box (between fy and TY), a little wider than the head so the circle holds it whole
HD = int(CN["size"] * CN.get("halo", 0)) // 2 * 2 if corners else 0  # a blurred copy of the circle's picture around it (Kamil 2026-10-31)
# plan "corner_halo": "accent" = the glow in the theme accent instead of the blurred picture (film 2: a red shirt made a red
# smear around the circle; the published shorts have a soft glow, Kamil 2026-11-15 "bycie w kolku bylo duzo lepiej zrobione")
HALO_VF = (f"scale={HD}:{HD}:flags=bicubic,drawbox=x=0:y=0:w=iw:h=ih:color=0x{themes.bar_hex(THEME)}:t=fill" if edl.get("corner_halo") == "accent"
           else f"scale={HD}:{HD}:flags=bicubic,boxblur=34:3")
if corners and not HT:  # an old EDL: the square from the picture before the cards
    fc.append(f"[{last}]split=2[vcb][cornsrc]"); last = "vcb"
    cs = int(W * 0.80) // 2 * 2
    cy0 = int(min(max((fy + TY) / 2 * H - cs * 0.48, 0), H - cs)); cx0 = (W - cs) // 2
    fc.append(f"[cornsrc]crop={cs}:{cs}:{cx0}:{cy0},scale={CN['size']}:{CN['size']}:flags=lanczos,format=yuva444p" + (",split=2[cf][chs]" if HD else "[cf]"))
    if HD: fc.append(f"[chs]{HALO_VF},format=yuva444p[chb]")
# picture-in-picture: face cam in the corner on top of full-screen slides
pip_x, pip_y, pip_en = 0, 0, "0"  # set below when the film has picture-in-picture overlays (pips, PS, pip_track: stage 1)
if pips and not HT:  # an old EDL: the window from the picture before the cards
    fc.append(f"[{last}]split=2[vbase][pipsrc]"); last = "vbase"
    cs = int(SH * 0.62) // 2 * 2
    px0 = int(min(max(fx * SW - cs / 2, 0), SW - cs)); py0 = int(min(max(fy * SH - cs * 0.42, 0), SH - cs))
    fc.append(f"[pipsrc]crop={cs}:{cs}:{px0}:{py0},scale={PS}:{PS}:flags=lanczos,format=yuva444p[pf]")
if pips:
    M = 72
    pip_en = "+".join(f"between(t{E},{o['at'] + 0.25:.3f}{E},{o['at'] + o['dur'] - 0.3:.3f})" for o in pips)
    pip_x, pip_y = W - PS - M, H - PS - M - 20
for k, o in enumerate(edl.get("overlays", [])):
    card_slots.append((len(inputs), o["at"], o.get("dur", float("inf"))))  # no length = on screen in every window
    inputs += [*CARD_IN, "-itsoffset", f"{o['at']:.3f}", "-i", o["file"]]
    sc = f"scale={W}:{H}," if vertical else ""
    fc.append(f"[{k+1}:v]{sc}format=yuva444p10le[g{k}]")
    fc.append(f"[{last}][g{k}]overlay=eof_action=pass:format=auto[v{k+1}]"); last = f"v{k+1}"
if pips:
    frame = themes.pip_frame(THEME)
    inputs += ["-loop", "1", "-i", str(Path(__file__).resolve().parent / "gfx" / "pip_mask.png"), "-loop", "1", "-i", frame]
    i_mask = 1 + len(edl.get("overlays", [])); i_frame = i_mask + 1; i_pip = i_frame + 1
    if HT:
        aligned.append(len(inputs)); inputs += ["-i", pip_track]
        fc.append(f"[{i_pip}:v]{grade},format=yuva444p[pf]")  # the same grade as the full picture
    fc.append(f"[{i_mask}:v]format=gray,scale={PS}:{PS}[pm]")
    fc.append("[pf][pm]alphamerge[pip]")
    fc.append(f"[{last}][{i_frame}:v]overlay={pip_x - 40}:{pip_y - 40}:enable={pip_en}:shortest=1[vpf]")
    fc.append(f"[vpf][pip]overlay={pip_x}:{pip_y}:enable={pip_en}:" + ("eof_action=pass" if HT else "shortest=1") + "[vpp]"); last = "vpp"
for b in BROLL:
    # a downloaded file: only the MP4 demuxer and local reads (an HLS playlist named .mp4 could open other files/URLs)
    inputs += ["-protocol_whitelist", "file", "-f", "mov", "-t", f"{b.get('ss', 0.0) + b['dur']:.3f}", "-i", b["file"]]
# the card fades out over its last 0.35 s (gfx/count_lib.mjs FADE_OUT); the box goes half-way through, when the card is half
# transparent, so neither a bare box on the full-frame face nor a box over a gone card shows for more than ~5 frames
SPLIT_OUT = 0.18
for i, (((bx, by, bw, bh), anc, fz), grp) in enumerate(sgroups.items()):  # after the cards, so the box sits on the card's background
    mask = os.path.join(out, f"split_mask_{bw}x{bh}.png")  # white box, top corners rounded (alpha of the face box)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=white:s={bw}x{bh}", "-frames:v", "1", "-vf",
                    f"format=gray,geq=lum='if(lt(Y,{R})*(lt(X,{R})*gt(hypot({R}-X,{R}-Y),{R})+gt(X,{bw - R})*gt(hypot(X-{bw - R},{R}-Y),{R})),0,255)'",
                    mask], check=True)
    i_smask = sum(1 for a in inputs if a == "-i"); inputs += ["-loop", "1", "-i", mask]
    s_en = "+".join(f"between(t{E},{o['at']:.3f}{E},{o['at'] + o['dur'] - (0 if o.get('no_fade_out') else SPLIT_OUT):.3f})" for o in grp)
    fc.append(f"[{i_smask}:v]format=gray[sm{i}]")
    fc.append(f"[sf{i}][sm{i}]alphamerge[sbox{i}]")
    fc.append(f"[{last}][sbox{i}]overlay={bx}:{by}:enable={s_en}:shortest=1[vsp{i}]"); last = f"vsp{i}"
if corners:  # after the cards: a ring in the theme accent, the face circle on it
    D, RG = CN["size"], CN["ring"]; cmask = os.path.join(out, "corner_mask.png"); cring = os.path.join(out, "corner_ring.png")
    r = D / 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=white:s={D}x{D}", "-frames:v", "1", "-vf",
                    f"format=gray,geq=lum='if(lte(hypot(X-{r - 0.5},Y-{r - 0.5}),{r - 1}),255,0)'", cmask], check=True)
    Dr = D + 2 * RG; rr = Dr / 2; acc = themes.bar_hex(THEME)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x{acc}:s={Dr}x{Dr}", "-frames:v", "1", "-vf",
                    f"format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-{rr - 0.5},Y-{rr - 0.5}),{rr - 1}),255,0)'", cring], check=True)
    i_cm = sum(1 for a in inputs if a == "-i"); inputs += ["-loop", "1", "-i", cmask, "-loop", "1", "-i", cring]
    if HT:
        aligned.append(len(inputs)); inputs += ["-i", corner_track]
        fc.append(f"[{i_cm + 2}:v]{grade},format=yuva444p" + (",split=2[cf][chs]" if HD else "[cf]"))  # the same grade as the full picture
        if HD: fc.append(f"[chs]{HALO_VF},format=yuva444p[chb]")
    c_en = "+".join(f"between(t{E},{o['at']:.3f}{E},{o['at'] + o['dur'] - (0 if o.get('no_fade_out') else SPLIT_OUT):.3f})" for o in corners)
    fc.append(f"[{i_cm}:v]format=gray[cm]")
    fc.append("[cf][cm]alphamerge[cbox]")
    if HD:  # the halo: blurred picture fading out from the circle's edge to nothing at its own edge
        hmask = os.path.join(out, "corner_halo.png"); hr = HD / 2
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=white:s={HD}x{HD}", "-frames:v", "1", "-vf",
                        f"format=gray,geq=lum='clip(255*(1-(hypot(X-{hr},Y-{hr})-{r})/({hr}-{r})),0,255)*0.85'", hmask], check=True)
        i_hm = sum(1 for a in inputs if a == "-i"); inputs += ["-loop", "1", "-i", hmask]
        fc.append(f"[{i_hm}:v]format=gray[hm]"); fc.append("[chb][hm]alphamerge[chalo]")
        hx, hy = int(CN["x"] + r - hr), int(CN["y"] + r - hr)
        fc.append(f"[{last}][chalo]overlay={hx}:{hy}:enable={c_en}:shortest=1[vch]"); last = "vch"
    fc.append(f"[{last}][{i_cm + 1}:v]overlay={CN['x'] - RG}:{CN['y'] - RG}:enable={c_en}:shortest=1[vcr]")
    fc.append(f"[vcr][cbox]overlay={CN['x']}:{CN['y']}:enable={c_en}:shortest=1[vcc]"); last = "vcc"
if edl.get("subs"):
    fc.append(f"[{last}]subtitles='{edl['subs']}':force_style='{edl.get('sub_style','')}'[vs]"); last = "vs"
# with voice_clean "dfn" the default chain has no afftdn and no acompressor: both lowered the measured voice quality (voice_clean.py)
audio = edl.get("audio", voice_clean.CHAIN if edl.get("voice_clean") == "dfn" else
                "highpass=f=70,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2,loudnorm=I=-14:TP=-1.0:LRA=9")
# the voice chain's own delay (afftdn 25 ms, an alimiter without latency=1 5 ms) cut off its start, so the voice stays on
# the lips (film 2026-11-04 long: +40 ms, Kamil 2026-11-09); measured on a test signal, the chain is the plan's data
_lat = av_latency.chain_ms(audio)
# asetpts=N/SR/TB: loudnorm gives its last ~3 s (the look-ahead flush) a time stamp 35 ms late, the AAC encoder fills the jump
# with one long packet and the end of the voice plays 35 ms after the lips (shorts 2026-11-10, av_check "56 ms audio packet");
# time from the sample count is exact, no sample is added or dropped
va = (f"[0:a]{audio},asetpts=N/SR/TB" + (f",atrim=start={_lat / 1000:.4f},asetpts=PTS-STARTPTS" if _lat > 0 else "") + ",aresample=48000"
      + (f",apad=pad_dur={tail}" if tail else ""))
# the sound is mixed in its OWN ffmpeg run, not in the picture graph: in one run with ~100 card inputs ffmpeg 8 dropped
# 0.65 s of the voice where the first card ended (film 2026-11-04 long, 3.09 s: one 0.676 s AAC packet, "Przez" gone,
# and every player that plays samples in a row heard the voice 0.65 s before the lips; Kamil 2026-11-08). The sound
# graph alone has no gap (checked); av_check.py proves it on every film after the mux.
# voice_clean "dfn": the voice of the rough cut through DeepFilterNet first (voice_clean.py), the chain then needs no afftdn
ainputs = ["-i", voice_clean.clean(rough, os.path.join(out, "rough.voice.wav")) if edl.get("voice_clean") == "dfn" else rough]; afc = []
if edl.get("music"):
    mo = ["-ss", f"{edl['music_offset']:.3f}"] if edl.get("music_offset") else []  # preview of a slice: beds start mid-way
    ainputs += [*mo, "-i", edl["music"], *mo, "-i", edl["sfx"]]
    afc.append(va + ",asplit=3[vm][vsc][vss]")
    afc.append(f"[1:a]aresample=48000,volume={edl.get('music_db', -13)}dB[mu]")
    # how far the music dips under the voice (edl_guard checks). mix < 1 = a floor: that share of the ducked music, the rest
    # undipped, so the music stays at one level under loud and quiet words alike (fragment 2026-11-14: threshold 0.04 /
    # ratio 2.5 let it back up to 3 dB under a quiet word at 201 s; 0.004 / 8 / mix 0.8 holds it 12-14 dB under its pause level)
    duck = {"threshold": 0.015, "ratio": 6, "mix": 1, **edl.get("music_duck", {})}
    afc.append(f"[mu][vsc]sidechaincompress=threshold={duck['threshold']:g}:ratio={duck['ratio']:g}:attack=30:release=500:makeup=1:mix={duck['mix']:g}[mud]")
    # the SFX dip under the voice as the music does: a chapter riser landing on a sentence covered "to co się dzieje" by 3 dB
    # (film 2026-11-04 long, 443 s, c4_dowod); in a pause they play at full level (edl_guard checks sfx_duck like music_duck)
    sduck = {"threshold": 0.015, "ratio": 6, "mix": 1, **edl.get("sfx_duck", {})}
    afc.append(f"[2:a]aresample=48000,volume={edl.get('sfx_db', -12)}dB[sxr]")
    afc.append(f"[sxr][vss]sidechaincompress=threshold={sduck['threshold']:g}:ratio={sduck['ratio']:g}:attack=5:release=300:makeup=1:mix={sduck['mix']:g}[sx]")
    afc.append("[vm][mud][sx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89:latency=1[a]")  # latency=1: no 5 ms look-ahead delay
else:
    afc.append(va + "[a]")
if PROXY:
    fc.append(f"[{last}]scale={'360:640' if vertical else '640:360'}:flags=bilinear[vpx]"); last = "vpx"
final = os.path.join(out, edl.get("out_name", "final.mp4"))
vpart, apart = final + ".video.mp4", final + ".audio.m4a"
args = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-an",
        "-c:v", "libx264", *OUT_ENC, "-pix_fmt", "yuv420p", vpart]
aargs = ["ffmpeg", "-v", "error", "-y", *ainputs, "-filter_complex", ";".join(afc), "-map", "[a]",
         "-c:a", "aac", "-b:a", "256k", "-ac", "2", apart]
margs = ["ffmpeg", "-v", "error", "-y", "-i", vpart, "-i", apart, "-map", "0:v", "-map", "1:a", "-c", "copy",
         "-movflags", "+faststart", final]
# the exact stage-2 commands next to the film: a render killed for memory or time can be rerun and measured by hand
Path(out, "assemble.args.json").write_text(json.dumps(args, ensure_ascii=False, indent=0))  # the picture (heavy) run
Path(out, "assemble.audio.args.json").write_text(json.dumps({"audio": aargs, "mux": margs}, ensure_ascii=False, indent=0))


def packets(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", f], capture_output=True, text=True, check=True)
    return int(r.stdout.strip())


def picture_in_windows():
    """The picture run in time windows (chunks.py). A window already made by the same command is kept, so a render
    stopped half-way goes on from there. Every window but the last must hold exactly its frames, or the join would shift
    the picture against the sound."""
    total = round(body * chunks.FPS)
    wins = chunks.windows(total, CHUNK)
    cdir = os.path.join(out, "chunks"); os.makedirs(cdir, exist_ok=True)
    pad = TAIL_PAD
    enc = ["-c:v", "libx264", *OUT_ENC, "-pix_fmt", "yuv420p"]
    parts = []
    for n, w in enumerate(wins):
        a = chunks.window_args(inputs, card_slots, aligned, fc, w, last, pad, enc, "")
        dst = os.path.join(cdir, f"{n:03d}_{chunks.key(a)}.mkv"); a[-1] = dst
        if not os.path.exists(dst):
            print(f"assemble: window {n + 1}/{len(wins)} frames {w[0]}-{w[1] if w[1] is not None else 'end'}", flush=True)
            a[-1] = dst + ".part.mkv"
            subprocess.run(a, check=True)
            os.replace(a[-1], dst)
        got = packets(dst)
        if w[1] is not None and got != w[1] - w[0]:
            sys.exit(f"assemble: window {n + 1} has {got} frames, not {w[1] - w[0]} ({dst})")
        # the last window runs to the end of the graph: the rest of the film plus the tail pad (tpad may round by a frame)
        want = total - w[0] + round(tail * chunks.FPS) if w[1] is None else got
        if abs(got - want) > 1:
            sys.exit(f"assemble: last window has {got} frames, not {want} (film {total} + tail) ({dst})")
        parts.append(dst)
    lst = os.path.join(cdir, "concat.txt")
    lens = [(w[1] - w[0]) / chunks.FPS if w[1] is not None else None for w in wins]  # exact: .mkv rounds to whole ms
    Path(lst).write_text(timeline.concat_list([os.path.abspath(p) for p in parts], lens))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vpart], check=True)
    if (got := packets(vpart)) != (want := sum(packets(p) for p in parts)):
        sys.exit(f"assemble: joined picture has {got} frames, the windows {want}")
    for f in os.listdir(cdir):  # windows of an older command or input (other key) will not be used again
        if f.endswith(".mkv") and os.path.join(cdir, f) not in parts:
            os.remove(os.path.join(cdir, f))


subprocess.run(aargs, check=True)
# <out>/chunks/ keeps the windows of the last run (a rerun with the same inputs reuses them); deleting it is always safe.
# one run when the film fits in one window or for a panel preview; VP_CHUNK_S=0 forces the one run (the old way)
CHUNK = float(os.environ.get("VP_CHUNK_S", chunks.CHUNK_S))  # the same window length for the one-run test and the windows
if PROXY or CHUNK <= 0 or len(chunks.windows(round(body * chunks.FPS), CHUNK)) == 1:
    subprocess.run(args, check=True)
else:
    picture_in_windows()
subprocess.run(margs, check=True)
os.remove(vpart); os.remove(apart)
if "master" in edl and (DRY or not PROXY):  # the whole mix to its loudness and true peak (master_audio.py, plan "master", {} = defaults); previews stay quick
    import master_audio
    rep = master_audio.master_in_place(final, edl["master"])
    print("master", rep["before"], "->", rep["after"])
print("OK", final)
