#!/usr/bin/env python3
"""master_audio.py: loudness and true peak on the FINISHED mix (Skool CCC G1/A11, P1 task 7).

assemble.py normalises the voice alone, then adds music and SFX and a sample-peak limiter: film 2's long came out at
-14.6 LUFS with a true peak of +1.9 dBFS (clips after AAC). This runs ffmpeg loudnorm twice on the whole mix (measure,
then apply with the measured values), limits the peaks at 4x oversampling, copies the video untouched, measures the
result again and writes a report.

  python3 master_audio.py <film.mp4> <out.mp4> [--lufs -14] [--tp -1.5] [--report <json>]
assemble.py runs it when the EDL has "master": {"lufs": -14, "tp": -1.5} (plan key "master"; without it nothing changes).
rc 1 when the result is off target by more than LU_TOL or its true peak is above the ceiling.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

LUFS, TP, LRA = -14.0, -1.5, 11.0
LU_TOL = 0.5
TP_MARGIN = 0.5    # dB under the ceiling for the limiter: AAC still adds a little
LOWPASS = 16000    # Hz
TIMEOUT = 3600     # s per ffmpeg pass: a 21 min long takes ~1 min, a hang ends with a message


def _ff(args: list[str]) -> str:
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", *args], capture_output=True, text=True, check=False, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ffmpeg {' '.join(args[:4])}...: no answer in {TIMEOUT} s") from e
    if r.returncode: raise RuntimeError(f"ffmpeg {' '.join(args[:4])}...: {r.stderr.strip().splitlines()[-1:]}")
    return r.stderr


def measure_loudnorm(film: str, lufs: float, tp: float) -> dict:
    out = _ff(["-i", film, "-vn", "-af", f"loudnorm=I={lufs}:TP={tp}:LRA={LRA}:print_format=json", "-f", "null", "-"])
    return json.loads(out[out.rindex("{"):out.rindex("}") + 1])


def measure(film: str) -> dict:
    """integrated loudness and true peak as EBU R128 reads them (the same ebur128 critic.py C7 uses)"""
    out = _ff(["-i", film, "-vn", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"])
    i, p = re.findall(r"I:\s+(-?[\d.]+) LUFS", out), re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    if not i or not p: raise RuntimeError(f"ebur128 gave no summary for {film}")
    return {"lufs": float(i[-1]), "tp": float(p[-1])}


def master(film: str, out: str, lufs: float = LUFS, tp: float = TP) -> dict:
    """loudnorm sets the gain (linear, measured first); a look-ahead limiter at 4x oversampling (192 kHz) holds the peaks
    TP_MARGIN under the ceiling; a LOWPASS before AAC: the encoder put ~4 dB of overs on film 2's top end (TP -1.7 in PCM,
    +2.3 after AAC; with the low-pass -2.0). YouTube's own encode cuts about there anyway."""
    before, m = measure(film), measure_loudnorm(film, lufs, tp)
    ln = (f"loudnorm=I={lufs}:TP={tp}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    lim = 10 ** ((tp - TP_MARGIN) / 20)
    chain = f"{ln},lowpass=f={LOWPASS},aresample=192000,alimiter=limit={lim:.4f}:attack=5:release=50:level=disabled,aresample=48000"
    _ff(["-y", "-i", film, "-map", "0:v?", "-map", "0:a", "-c:v", "copy", "-af", chain,
         "-c:a", "aac", "-b:a", "256k", "-ac", "2", "-movflags", "+faststart", out])
    after = measure(out)
    ok = abs(after["lufs"] - lufs) <= LU_TOL and after["tp"] <= tp
    return {"film": film, "out": out, "target": {"lufs": lufs, "tp": tp, "lu_tol": LU_TOL}, "before": before, "after": after, "ok": ok}


def master_in_place(final: str, cfg: dict) -> dict:
    """assemble.py's step (EDL "master", {} = the defaults): the mastered mix replaces final; off target or an ffmpeg
    error = SystemExit naming it, the unmastered file stays and no half-made .master.mp4 is left behind"""
    tmp = final + ".master.mp4"
    try:
        rep = master(final, tmp, cfg.get("lufs", LUFS), cfg.get("tp", TP))
    except (RuntimeError, ValueError, KeyError) as e:  # ValueError/KeyError: loudnorm printed no or a broken JSON block
        Path(tmp).unlink(missing_ok=True)
        raise SystemExit(f"FAILED master {final}: {e} (unmastered file kept)") from e
    Path(final).with_suffix(".master.json").write_text(json.dumps(rep, indent=1))
    if not rep["ok"]:
        Path(tmp).unlink(missing_ok=True)
        raise SystemExit(f"FAILED master {final}: {rep['after']} vs target {rep['target']} (unmastered file kept)")
    Path(tmp).replace(final)
    return rep


def main(argv: list[str]) -> int:
    opt = {k: argv[argv.index(k) + 1] for k in ("--lufs", "--tp", "--report") if k in argv and argv.index(k) + 1 < len(argv)}
    rest = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--lufs", "--tp", "--report"))]
    if len(rest) != 2: print(__doc__, file=sys.stderr); return 2
    try:
        r = master(rest[0], rest[1], float(opt.get("--lufs", LUFS)), float(opt.get("--tp", TP)))
    except (RuntimeError, ValueError, KeyError, OSError) as e:
        print(f"FAILED master_audio {rest[0]}: {e}", file=sys.stderr)
        return 1
    Path(opt.get("--report") or Path(rest[1]).with_suffix(".master.json")).write_text(json.dumps(r, indent=1))
    b, a = r["before"], r["after"]
    print(f"{'OK' if r['ok'] else 'FAILED'} master_audio {Path(rest[0]).name}: {b['lufs']} LUFS / TP {b['tp']} -> {a['lufs']} LUFS / TP {a['tp']}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
