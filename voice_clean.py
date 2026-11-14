"""voice_clean: the voice of the rough cut through DeepFilterNet before the voice chain (plan/EDL "voice_clean": "dfn").

Kamil 2026-11-14 after the fragment test: "audio mikrofon ... zeby byl dzwiek jak studyjny" -> "wybierz se najlepszy".
Measured on two 30 s pieces of the 2026-11-04 recording (TorchAudio-SQUIM, no reference; raw microphone PESQ 3.80 / 3.74):
the old chain (afftdn + acompressor + loudnorm) 3.02 / 3.02, DeepFilterNet + highpass + loudnorm 3.77 / 3.72, the same with
acompressor ratio 3: 3.52 / 3.37; Resemble Enhance 2.43 and ~28 min per 4 min of film on this CPU. afftdn and the
compressor both lowered the score, the loudness range stayed the same without them (2.4 / 3.5 LU against 2.2 / 3.4).
So a film with voice_clean "dfn" sets "audio" to a chain without afftdn and acompressor (plan data, edl_guard checks it).

The binary is the author's static release build (github.com/Rikorose/DeepFilterNet v0.5.6, MIT / Apache-2.0), not in the
repo: VP_DEEP_FILTER or ~/.local/share/vp-voice/dfn/deep-filter. A missing binary stops the render with its path named;
there is no silent fall back to the uncleaned voice. -D takes the model's own delay back, sync_check measures the result.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

DEFAULT_BIN = Path.home() / ".local/share/vp-voice/dfn/deep-filter"
CHAIN = "highpass=f=70,loudnorm=I=-14:TP=-1.0:LRA=9"  # assemble.py's default voice chain behind DeepFilterNet


def binary() -> Path:
    return Path(os.environ.get("VP_DEEP_FILTER") or DEFAULT_BIN)


def clean(media: str, dst: str) -> str:
    """dst = the sound of `media` (48 kHz wav) through deep-filter; returns dst. Raises SystemExit with the reason."""
    exe = binary()
    if not (exe.is_file() and os.access(exe, os.X_OK)):
        raise SystemExit(f"voice_clean: no DeepFilterNet binary at {exe} (set VP_DEEP_FILTER, or drop \"voice_clean\" from the plan)")
    with tempfile.TemporaryDirectory(prefix="voice-clean-") as tmp:
        raw, outdir = os.path.join(tmp, "voice.wav"), os.path.join(tmp, "out")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", media, "-vn", "-ar", "48000", "-c:a", "pcm_s16le", raw], check=True, timeout=3600)
            subprocess.run([str(exe), "-D", "-o", outdir, raw], check=True, capture_output=True, timeout=7200)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            err = getattr(e, "stderr", b"") or b""
            raise SystemExit(f"voice_clean: FAILED on {media}: {e} {err[-400:].decode('utf-8', 'replace')}") from e
        made = Path(outdir, "voice.wav")
        if not made.is_file() or made.stat().st_size < 1000:
            raise SystemExit(f"voice_clean: {exe} wrote no sound for {media}")
        shutil.move(str(made), dst)
    return dst
