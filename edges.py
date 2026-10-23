"""Cut edges: where a kept range may start/end so a cut never opens on dead air or chops a sound in half.

One place for the edge rules of plan key "edge_fix" (build_edl.py) and the critic checks C12/C13 (critic.py).
  "edge_fix": true                       -> a computed edge inside a silence > 0.4 s moves to that silence's boundary,
                                            explicit plan t0/t1 are final (never re-snapped)
  "edge_fix": {"dips": true, ...}        -> also: a computed edge in loud speech moves to the nearest energy dip
     keys: wav (16-bit PCM of the recording; default: the words file with .cw.json -> .wav), loud_db (-32),
           dip_db (-35), win (0.25 s)
Energy = 10 ms RMS frames in dBFS; the level "at" a time is the loudest of the 3 frames around it (as heard at a cut).
"""
import array
import math
import sys
import wave
from pathlib import Path

LONG_SIL = 0.4        # silences shorter than this are breaths between words, not dead air
IN_PAD, OUT_PAD = 0.08, 0.12  # same margins as build_edl's own snap rules: just before the sound, just after it
DEAD_AIR = 0.6        # C12: more than this of silence right at a cut edge is heard as a gap
LOUD_DB, DIP_DB, WIN = -32.0, -35.0, 0.25
FRAME = 0.01


BAD_WAV = (ValueError, wave.Error, EOFError, OSError)  # what Energy() raises for a file it cannot use


def options(plan):
    """plan["edge_fix"] -> dict of settings, or None when the key is off (absent, null, false). Bad values stop with a named error."""
    v = plan.get("edge_fix")
    if v is None or v is False: return None
    if v is True: v = {}
    if not isinstance(v, dict): sys.exit(f"edge_fix: expected true or an object, got {v!r}")
    if not isinstance(v.get("dips", False), bool): sys.exit(f"edge_fix.dips: expected true or false, got {v['dips']!r}")
    o = {"dips": v.get("dips", False), "wav": v.get("wav"), "loud_db": v.get("loud_db", LOUD_DB),
         "dip_db": v.get("dip_db", DIP_DB), "win": v.get("win", WIN)}
    for k in ("loud_db", "dip_db", "win"):
        if isinstance(o[k], bool) or not isinstance(o[k], (int, float)) or not math.isfinite(o[k]):
            sys.exit(f"edge_fix.{k}: expected a number, got {o[k]!r}")
    if not 0 < o["win"] <= 1: sys.exit(f"edge_fix.win: expected 0 < win <= 1 s, got {o['win']!r}")
    return o


def wav_path(plan, opts=None):
    """The recording's audio: edge_fix.wav, else <words stem>.wav next to the words file; None when missing."""
    p = (opts or {}).get("wav") or str(plan.get("words", "")).replace(".cw.json", ".wav")
    return p if p.endswith(".wav") and Path(p).is_file() else None


class Energy:
    """10 ms RMS frames of a 16-bit PCM wav, read lazily around the times asked for (never the whole file)."""

    def __init__(self, path):
        """ValueError / wave.Error / EOFError when the file is not a readable 16-bit PCM wav."""
        self.path = path
        with wave.open(path) as w:
            if w.getsampwidth() != 2: raise ValueError(f"{path} must be 16-bit PCM")
            self.sr, self.ch, self.n = w.getframerate(), w.getnchannels(), w.getnframes()
        if Path(path).stat().st_size < 44 + self.n * self.ch * 2:  # cut short (interrupted conversion): the missing end is no silence
            raise ValueError(f"{path} is shorter than its header says")
        self.hop = max(1, round(self.sr * FRAME)); self.cache = {}

    def frame_db(self, i):
        """dBFS of 10 ms frame i (frame i covers i*10 ms .. (i+1)*10 ms); outside the file = silence."""
        if i in self.cache: return self.cache[i]
        if i < 0 or i * self.hop >= self.n: return -120.0
        with wave.open(self.path) as w:  # a few hundred frames per film, each read once (cache)
            w.setpos(i * self.hop)
            a = array.array("h", w.readframes(self.hop))
        if sys.byteorder == "big": a.byteswap()
        db = 20 * math.log10(math.sqrt(sum(x * x for x in a) / max(1, len(a))) / 32768 + 1e-9)
        self.cache[i] = db
        return db

    def at(self, t):
        """Level heard at a cut at time t: the loudest of the frames just before, at and just after it."""
        i = int(t / FRAME)
        return max(self.frame_db(j) for j in (i - 1, i, i + 1))

    def dip(self, t, lo, hi, dip_db):
        """Nearest time in [lo, hi] to t whose level is <= dip_db (frame centre), or None."""
        best = None
        for j in range(int(lo / FRAME), int(hi / FRAME) + 1):
            c = (j + 0.5) * FRAME
            if lo <= c <= hi and self.at(c) <= dip_db and (best is None or abs(c - t) < abs(best - t)): best = c
        return best


def inside(t, sil):
    """The silence (ss, se) longer than LONG_SIL that strictly contains t, or None."""
    for ss, se in sil:
        if se - ss > LONG_SIL and ss < t < se: return ss, se
    return None


def trim_dead_air(t0, t1, sil, fix0=True, fix1=True):
    """A start inside a long silence moves to just before the sound after it; an end, to just after the sound before it.
    Only when at least 0.3 s of the range is left; fix0/fix1 False = that edge is the editor's own value, left alone."""
    s = inside(t0, sil) if fix0 else None
    if s and s[1] - IN_PAD < t1 - 0.3: t0 = max(t0, s[1] - IN_PAD)
    s = inside(t1, sil) if fix1 else None
    if s and s[0] + OUT_PAD > t0 + 0.3: t1 = min(t1, s[0] + OUT_PAD)
    return t0, t1


def snap_loud(t, lo, hi, energy, opts):
    """t in loud sound (> loud_db) -> nearest dip (<= dip_db) within +-win, never outside [lo, hi]; else t unchanged."""
    if energy.at(t) <= opts["loud_db"]: return t
    d = energy.dip(t, max(lo, t - opts["win"]), min(hi, t + opts["win"]), opts["dip_db"])
    return t if d is None else d


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def findings(segments, sil, energy=None, loud_db=LOUD_DB):
    """Cut edges of an EDL that sound wrong, as (code, msg, output time): C12 dead air > DEAD_AIR at an edge, C13 a cut in loud sound.
    An edge where the next segment continues the same source (gap < 20 ms) is no cut and is not checked."""
    out = []; acc = 0.0
    for k, s in enumerate(segments):
        d = s["out"] - s["in"]
        cut_in = k == 0 or abs(s["in"] - segments[k - 1]["out"]) > 0.02
        cut_out = k + 1 == len(segments) or abs(segments[k + 1]["in"] - s["out"]) > 0.02
        for is_in, cut, t, at in ((True, cut_in, s["in"], acc), (False, cut_out, s["out"], acc + d)):
            if not cut: continue
            for ss, se in sil:
                dead = (se - t) if is_in else (t - ss)
                if ss <= t <= se and dead > DEAD_AIR:
                    out.append(("C12", f"{mmss(at)} {'początek' if is_in else 'koniec'} ujęcia: {dead:.1f} s ciszy przy cięciu (źródło {t:.2f}s)", at))
                    break
            if energy is not None and (db := energy.at(t)) > loud_db:
                out.append(("C13", f"{mmss(at)} cięcie w głośnej mowie ({db:.0f} dB, {'początek' if is_in else 'koniec'} ujęcia, źródło {t:.2f}s)", at))
        acc += d
    return out
