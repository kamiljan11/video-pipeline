#!/usr/bin/env python3
"""Repair camera judder in a recording: frames the camera never sent (ffmpeg repeated the previous one to keep
30 fps CFR) are replaced by an in-between frame from optical flow, so motion is even again.

  .venv/bin/python dejudder.py <in.mp4> <out.mp4> [--scan]

--scan only counts the repeated frames (no output written). Timing, frame count and audio stay identical to the
input, so a transcript of the input (`*.cw.json`) still fits the output. Runs of more than MAX_RUN repeated frames
(the camera stalled) are left as they are: no in-between frame from a picture that long ago would look right.
Why: the Razer Kiyo Pro Ultra delivers 25-30 fps in dim light although 30 is requested (measured 2026-10-22).
"""
from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np

REPEAT_DIFF = 0.06  # mean |Δ| of 320x180 luma; repeated frames measure < 0.03, real ones > 0.1 (2026-10-22 recording)
MAX_RUN = 3
SMALL = (320, 180)
FLOW_W = 640
RENDER_NODE = "/dev/dri/renderD128"  # VAAPI encoder, as in laptop-setup/recorder/recorder.py


def frame_size(w: int, h: int) -> int:
    return w * h * 3 // 2  # yuv420p


def planes(buf: bytes, w: int, h: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = np.frombuffer(buf, np.uint8)
    y = a[: w * h].reshape(h, w)
    u = a[w * h: w * h * 5 // 4].reshape(h // 2, w // 2)
    v = a[w * h * 5 // 4:].reshape(h // 2, w // 2)
    return y, u, v


def small_luma(buf: bytes, w: int, h: int) -> np.ndarray:
    return cv2.resize(planes(buf, w, h)[0], SMALL, interpolation=cv2.INTER_AREA).astype(np.int16)


def is_repeat(prev_small: np.ndarray, small: np.ndarray, threshold: float = REPEAT_DIFF) -> bool:
    return float(np.abs(small - prev_small).mean()) < threshold


def _warp(plane: np.ndarray, flow: np.ndarray, t: float) -> np.ndarray:
    """plane sampled at x - t*flow(x): moves the picture t of the way along the flow."""
    h, w = plane.shape
    f = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR) * (w / flow.shape[1])
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(plane, gx - t * f[..., 0], gy - t * f[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def in_between(a: bytes, b: bytes, w: int, h: int, count: int) -> list[bytes]:
    """`count` evenly spaced frames between real frames a and b (bidirectional flow, blended by distance)."""
    ya, yb = planes(a, w, h)[0], planes(b, w, h)[0]
    fh = round(h * FLOW_W / w)
    sa, sb = cv2.resize(ya, (FLOW_W, fh), interpolation=cv2.INTER_AREA), cv2.resize(yb, (FLOW_W, fh), interpolation=cv2.INTER_AREA)
    dis = cv2.DISOpticalFlow.create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    empty = np.zeros((fh, FLOW_W, 2), np.float32)
    ab, ba = dis.calc(sa, sb, empty.copy()), dis.calc(sb, sa, empty.copy())
    out = []
    for k in range(1, count + 1):
        t = k / (count + 1)
        frame = []
        for pa, pb in zip(planes(a, w, h), planes(b, w, h), strict=True):
            wa, wb = _warp(pa, ab, t), _warp(pb, ba, 1 - t)
            frame.append(cv2.addWeighted(wa, 1 - t, wb, t, 0).tobytes())
        out.append(b"".join(frame))
    return out


def repaired(frames: Iterator[bytes], w: int, h: int, stats: dict[str, int]) -> Iterator[bytes]:
    """Same number of frames out as in; a run of 1..MAX_RUN repeats is replaced by in-between frames."""
    last_real: bytes | None = None
    last_small: np.ndarray | None = None
    held: list[bytes] = []  # at most MAX_RUN frames: a frozen camera must not fill the RAM (5.5 MB per 1440p frame)
    stalled = False
    for buf in frames:
        small = small_luma(buf, w, h)
        if last_small is not None and is_repeat(last_small, small):
            if stalled:
                yield buf
                continue
            held.append(buf)
            if len(held) > MAX_RUN:  # a stall: left as recorded, streamed from here on
                yield from held
                held, stalled = [], True
                stats["stalls"] += 1
            continue
        if held:
            assert last_real is not None
            yield from in_between(last_real, buf, w, h, len(held))
            stats["fixed"] += len(held)
            held = []
        stalled = False
        yield buf
        last_real, last_small = buf, small
    yield from held  # repeats at the very end have no next frame to move towards


def probe(src: str) -> tuple[int, int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", src], capture_output=True, text=True, check=True)
    w, h = (int(x) for x in r.stdout.strip().split(","))
    return w, h


def read_frames(pipe, size: int) -> Iterator[bytes]:
    while True:
        buf = pipe.read(size)
        if len(buf) < size:
            return
        yield buf


def source_fps(src: str) -> str:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", src], capture_output=True, text=True, check=True)
    return r.stdout.strip() or "30"


def av_offset(src: str | Path) -> float:
    """Video start minus audio start (the recorder's video starts ~20 ms after its audio): kept in the output."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,start_time", "-of", "csv=p=0", str(src)],
                       capture_output=True, text=True, check=True)
    starts = dict(line.split(",")[:2] for line in r.stdout.split() if line.count(",") >= 1)
    try:
        return float(starts.get("video", 0)) - float(starts.get("audio", 0))
    except ValueError:  # "N/A" start time: nothing to keep
        return 0.0


def packets(path: Path | str) -> dict[str, int]:
    """Packets per stream type, counted by ffprobe itself (per-packet listing breaks on side data)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries", "stream=codec_type,nb_read_packets",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    out: dict[str, int] = {}
    for line in r.stdout.split():
        kind, n = line.split(",")[:2]
        out[kind] = out.get(kind, 0) + int(n)
    return out


def encode_cmd(src: str, part: Path, w: int, h: int, fps: str, offset: float = 0.0) -> list[str]:
    # an editing source, re-encoded once more by assemble.py: ~2x the recorder's 16M keeps the generation loss low
    return ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{w}x{h}",
            "-framerate", fps, "-itsoffset", f"{offset:.6f}", "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?",
            "-vaapi_device", RENDER_NODE, "-vf", "format=nv12,hwupload",
            "-c:v", "h264_vaapi", "-profile:v", "high", "-b:v", "30M", "-maxrate", "40M", "-bufsize", "60M",
            "-g", "30", "-color_range", "tv", "-colorspace", "bt470bg", "-c:a", "copy", "-movflags", "+faststart", str(part)]


def decoder(src: str) -> subprocess.Popen:
    # passthrough: one raw frame per packet of the recording, so the output can be checked against it 1:1
    return subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-i", src, "-map", "0:v:0", "-fps_mode", "passthrough",
                             "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE)


def scan(src: str, w: int, h: int) -> int:
    dec = decoder(src)
    assert dec.stdout
    frames = repeated = 0
    prev = None
    for buf in read_frames(dec.stdout, frame_size(w, h)):
        small = small_luma(buf, w, h)
        repeated += prev is not None and is_repeat(prev, small)
        frames += 1
        prev = small
    print(f"frames {frames}, repeated {repeated}")
    return dec.wait()


def encode(src: str, part: Path, w: int, h: int, stats: dict[str, int]) -> str:
    """Decode -> repair -> encode into part. Returns '' or what went wrong; both ffmpegs are always reaped."""
    dec = decoder(src)
    enc = subprocess.Popen(encode_cmd(src, part, w, h, source_fps(src), av_offset(src)), stdin=subprocess.PIPE)
    assert dec.stdout and enc.stdin
    t0 = time.time()
    try:
        for buf in repaired(read_frames(dec.stdout, frame_size(w, h)), w, h, stats):
            enc.stdin.write(buf)
            stats["frames"] += 1
            if stats["frames"] % 3000 == 0:
                print(f"{stats['frames']} frames, {stats['frames'] / (time.time() - t0):.0f} fps, fixed {stats['fixed']}",
                      file=sys.stderr, flush=True)
        enc.stdin.close()
    except OSError as e:  # BrokenPipeError = the encoder died (no VAAPI, disk full): its exit code tells why
        for proc in (dec, enc):
            proc.kill()
            proc.wait()
        return f"{type(e).__name__}: encoder {enc.returncode}"
    except BaseException:
        # anything else (cv2, reshape, Ctrl+C): reap both ffmpegs first, or dec.wait() hangs on a full pipe
        for proc in (dec, enc):
            proc.kill()
            proc.wait()
        raise
    if dec.wait() or enc.wait():
        return f"ffmpeg exit: decoder {dec.returncode}, encoder {enc.returncode}"
    return ""


def verify(part: Path, src_packets: dict[str, int]) -> str:
    """The plan and transcript rely on it: every frame and every audio packet of the recording, nothing more."""
    got = packets(part)
    if got.get("video") != src_packets.get("video") or got.get("audio") != src_packets.get("audio"):
        return f"output packets {got} != recording {src_packets}"
    return ""


def main(argv: list[str]) -> int:
    paths = [a for a in argv if a != "--scan"]
    if len(paths) != (1 if "--scan" in argv else 2):
        print(__doc__, file=sys.stderr)
        return 2
    src = paths[0]
    if not Path(src).is_file():
        print(f"FAILED dejudder: no such recording {src}", file=sys.stderr)
        return 1
    try:
        w, h = probe(src)
        src_packets = packets(src)
    except (OSError, subprocess.CalledProcessError, ValueError) as e:
        print(f"FAILED dejudder {src}: not a readable video ({e})", file=sys.stderr)
        return 1
    if "--scan" in argv:
        return scan(src, w, h)
    out = Path(paths[1])
    part = out.with_suffix(".part.mp4")
    if Path(src).resolve() in (out.resolve(), part.resolve()):
        print(f"FAILED dejudder: output {out} would overwrite the recording {src}", file=sys.stderr)
        return 1
    stats = {"frames": 0, "fixed": 0, "stalls": 0}
    t0 = time.time()
    error = "stopped by an exception (traceback below)"
    try:
        error = encode(src, part, w, h, stats) or verify(part, src_packets)
    finally:
        if error:
            print(f"FAILED dejudder {src}: {error}; {stats['frames']} frames written, partial output removed",
                  file=sys.stderr)
            part.unlink(missing_ok=True)
    if error:
        return 1
    part.replace(out)
    print(f"frames {stats['frames']}, repaired {stats['fixed']}, stalls left {stats['stalls']}, "
          f"{time.time() - t0:.0f} s -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
