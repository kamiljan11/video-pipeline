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
    length), between pieces it sticks to the start of the piece that comes next IN THE SOURCE, after all of them to the
    film end. Pieces may be out of source order (the 2026-11-04 v5 long plays the promise at 109 s before the problem at
    38 s): the first version returned at the first piece starting after t, so every source time before that piece got
    its film start and 38 s of the problem part sat on one instant (found by film_check long.retakes, 2026-11-09)"""
    acc, nxt = 0.0, None
    for s in segments:
        L = piece_len(s, exact)
        if s["in"] <= t <= s["out"]: return acc + min(t - s["in"], L)
        if s["in"] > t and (nxt is None or s["in"] < nxt[0]): nxt = (s["in"], acc)
        acc += L
    return nxt[1] if nxt else acc


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



def snap_in(t: float, v0: float) -> float:
    """the seek time for a piece starting at source time t: just before the source video frame nearest to t.

    A recording's frames sit at v0 + k / FPS (film 2026-11-04: video start_time 0.033 s, sound at 0). A piece cut at
    `-ss t` got its first frame up to one frame after t, and setpts/asetpts=PTS-STARTPTS put picture and sound both at 0:
    the picture ran up to 33 ms ahead of the voice, piece by piece (Kamil 2026-11-09 "dalej long ma opoznienie"). Seeking
    to a frame's own time (0.5 ms before it) makes the first frame and the first sound sample the same instant."""
    k = max(round((t - v0) * FPS), 0)  # before the first frame: the first frame
    return max(v0 + k / FPS - 0.0005, 0.0)
