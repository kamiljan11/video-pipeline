"""av_latency: how many milliseconds an ffmpeg audio filter chain delays the sound, measured, so assemble.py can take it back.

Film 2026-11-04 long (Kamil 2026-11-09 "dalej long ma opoznienie i to jeszcze wieksze"): the voice came 40 ms after the
lips. afftdn (noise reduction) delays by 25 ms and every alimiter by its 5 ms look-ahead (latency=1 compensates the
limiter; afftdn has no such option). The chain is the plan's data and changes, so its delay is measured on a test
signal (tone bursts of two pitches, 48 kHz) instead of a table that goes stale.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR = 48000
ENV = 2000  # envelope rate (0.5 ms)
SIGNAL = "aevalsrc='0.3*sin(2*PI*300*t)*lt(mod(t,0.43),0.17)+0.2*sin(2*PI*1100*t)*lt(mod(t,0.31),0.09)':s=48000:d=4"


def _envelope(wav: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True, timeout=120).stdout
    x = np.abs(np.frombuffer(raw, np.int16).astype(np.float32))
    n = len(x) // (SR // ENV)
    return x[:n * (SR // ENV)].reshape(n, -1).mean(axis=1)


def chain_ms(chain: str, max_ms: float = 200.0) -> float:
    """the delay of `chain` (an -af filter chain) in ms, >= 0; raises on an ffmpeg error (the chain would fail the render too)"""
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.wav", Path(d) / "b.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", SIGNAL, "-c:a", "pcm_s16le", str(a)], check=True, timeout=120)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-af", chain, "-ar", str(SR), "-c:a", "pcm_s16le", str(b)],
                       check=True, timeout=120)
        x, y = _envelope(a), _envelope(b)  # x: the test signal, y: the same through the chain
    # all in envelope samples (ENV per second, 0.5 ms): the test signal from 0.5 to 3.3 s, searched up to max_ms later
    start, end, max_lag = int(0.5 * ENV), int(3.3 * ENV), int(max_ms / 1000 * ENV)
    ref = x[start:end]; ref = (ref - ref.mean()) / (ref.std() + 1e-9)
    corr = []
    for lag in range(max_lag + 1):
        seg = y[start + lag:end + lag]; corr.append(float((ref * (seg - seg.mean()) / (seg.std() + 1e-9)).mean()))
    k = int(np.argmax(corr))  # delay in envelope samples
    if k == max_lag:  # the best match at the edge of the search: the real delay is longer, trimming max_ms would be a guess
        raise ValueError(f"av_latency: chain delays the sound by >= {max_ms:.0f} ms (search limit): {chain}")
    return max(0.0, k / ENV * 1000)


_V0: dict[str, float] = {}


def video_start(path: str) -> float:
    """start_time of a file's video stream (2026-11-04: 0.033 s, the sound at 0)"""
    if path not in _V0:
        if not Path(path).exists(): return 0.0  # the caller says what is missing (assemble: cut / preview from rough)
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=start_time",
                            "-of", "csv=p=0", path], capture_output=True, text=True, check=True, timeout=60)
        try: _V0[path] = float(r.stdout.strip() or 0)
        except ValueError:  # "N/A": no start offset written; the seek grid then starts at 0, said
            print(f"av_latency: {path}: video start_time {r.stdout.strip()!r}, taken as 0", file=sys.stderr); _V0[path] = 0.0
    return _V0[path]
