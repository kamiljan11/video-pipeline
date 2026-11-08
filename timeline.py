"""timeline: how long each EDL piece lasts in the finished film, and where it starts. The ONE place for that decision.

With seg_exact (assemble.py stage 1) every piece is cut to whole frames at FPS, so a piece lasts round(d * FPS) / FPS,
not its EDL length d. build_edl.py used the EDL lengths for every card, scene beat, subtitle and punch-in while
assemble.py cut whole frames: on film 2026-11-04 the pictures ran up to 287 ms off the words by the end of the long
(sync_check.py measured +74 ms median, +253 ms max on rough.mkv). Everything that turns a source time into a film time
goes through here: build_edl.src2out, assemble.seg_len, behind.seg_frames, sync_check.planned_starts.
"""
FPS = 30


def piece_len(seg: dict, exact: bool) -> float:
    """seconds the piece lasts in the film"""
    d = seg["out"] - seg["in"]
    return max(1, round(d * FPS)) / FPS if exact else d


def piece_frames(seg: dict) -> int:
    """whole frames of a seg_exact piece"""
    return max(1, round((seg["out"] - seg["in"]) * FPS))


def starts(segments: list[dict], exact: bool) -> list[float]:
    """film time where each piece starts"""
    acc, out = 0.0, []
    for s in segments:
        out.append(acc)
        acc += piece_len(s, exact)
    return out


def total(segments: list[dict], exact: bool) -> float:
    return sum(piece_len(s, exact) for s in segments)


def src2out(t: float, segments: list[dict], exact: bool) -> float:
    """film time of source time t: inside a piece the time runs 1:1 from the piece start (clamped to the piece's film
    length), between pieces it sticks to the next piece start"""
    acc = 0.0
    for s in segments:
        if t < s["in"]: return acc
        L = piece_len(s, exact)
        if t <= s["out"]: return acc + min(t - s["in"], L)
        acc += L
    return acc


def concat_list(files: list[str], seconds: list[float | None]) -> str:
    """ffmpeg concat demuxer list with each file's exact length (`duration`). Without it the demuxer places the next file
    at the end of the previous one as its container says, and .mkv says whole milliseconds: a 44-frame piece (1.466667 s)
    reads 1.466 s. Over 275 pieces of the 2026-11-04 long the head track (picture only) ran 3+ frames ahead of rough.mkv
    (picture + sound, rounded the other way) and the corner head moved its lips before the voice. None = no duration
    (the last file, whose length nothing after it depends on)."""
    if len(files) != len(seconds):
        raise ValueError(f"concat_list: {len(files)} files, {len(seconds)} lengths")
    out = []
    for f, d in zip(files, seconds, strict=True):
        if "'" in f or "\n" in f:
            raise ValueError(f"concat_list: a quote or newline in {f!r}")
        out.append(f"file '{f}'\n" + (f"duration {d:.6f}\n" if d is not None else ""))
    return "".join(out)

