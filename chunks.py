"""Stage 2 of assemble.py in time windows (Kamil 2026-11-08: the long must render to the end).

One ffmpeg run with every card as its own input holds every card's decoder at once: the 95-card long of 2026-11-04
took 55-60 GB of anon memory in 30 s, thrashed under a 60 GB cap and was killed under 32 GB. A window opens only the
cards on screen in it; every other card input becomes a 16x16 transparent frame, so input numbers and the filter
graph stay exactly as assemble.py built them. Each window seeks rough.mkv (and the head tracks cut frame for frame
with it) with -copyts, so every time in the graph (card offsets, enable=between(t,..), the progress bar) stays the
film time. Windows land in <out>/chunks/ named by their command: a render killed half-way starts again where it
stopped. Pure functions here, the run in assemble.py; tests/test_chunks.py."""
import hashlib
import json

FPS = 30
CHUNK_S = 120.0
# a card outside the window: one transparent frame, nothing to decode or hold (alpha 0 = the overlay leaves the picture)
PLACEHOLDER = ["-f", "lavfi", "-i", "color=c=black@0.0:s=16x16:r=30:d=0.034,format=rgba"]


def windows(frames: int, chunk_s: float = CHUNK_S) -> list[tuple[int, int | None]]:
    """[(first frame, end frame or None for the last window)] over `frames` frames; the last window runs to the end
    of the graph (the tail pad). One window when the film is not longer than two chunks' worth."""
    step = max(1, round(chunk_s * FPS))
    if frames <= step:
        return [(0, None)]
    starts = list(range(0, frames, step))
    if frames - starts[-1] < step // 4:  # no stub window of a few seconds at the end
        starts.pop()
    return [(f0, starts[i + 1] if i + 1 < len(starts) else None) for i, f0 in enumerate(starts)]


def on_screen(at: float, dur: float, t0: float, t1: float | None) -> bool:
    """A card [at, at+dur) touches the window [t0, t1) (1 frame of slack on both sides for rounding)."""
    slack = 1 / FPS
    return at < (t1 + slack if t1 is not None else float("inf")) and at + dur > t0 - slack


def window_args(inputs: list[str], cards: list[tuple[int, float, float]], aligned: list[int], fc: list[str],
                win: tuple[int, int | None], last_label: str, tail_pad: str, encode: list[str], dst: str) -> list[str]:
    """The ffmpeg command of one window.
    inputs: assemble.py's input arguments; cards: (index in `inputs` of the card's first argument, at, dur), each card
    taking [*CARD_IN, -itsoffset, at, -i, file] (its slot ends at its first -i and file); aligned: indices in `inputs` of the "-i" of inputs cut
    frame for frame with the film (rough.mkv, head tracks), which get the window's seek; fc: the filter graph parts;
    tail_pad: the tpad text in fc[0] that only the last window keeps; encode: video codec arguments."""
    f0, f1 = win
    t0, t1 = f0 / FPS, (f1 / FPS if f1 is not None else None)
    args = list(inputs)
    seek = ["-ss", f"{t0:.6f}"] + (["-t", f"{t1 - t0 + 1:.6f}"] if t1 is not None else [])
    for i in aligned:
        if args[i] != "-i":
            raise ValueError(f"aligned input {i} is not an -i: {args[i]}")
    # every edit from the highest index down: a stand-in is shorter than a card and a seek adds arguments, and either
    # would move the positions after it
    edits = [(i, "card", at, dur) for i, at, dur in cards] + [(i, "seek", 0.0, 0.0) for i in aligned]
    for i, kind, at, dur in sorted(edits, reverse=True):
        if kind == "seek":
            args[i:i] = seek
        elif not on_screen(at, dur, t0, t1):
            end = args.index("-i", i) + 2  # the card's options, its -i and its file
            args[i:end] = ["-itsoffset", f"{at:.3f}", *PLACEHOLDER]
    graph = list(fc)
    if f1 is not None and tail_pad:
        graph[0] = graph[0].replace(tail_pad, "")
    graph.append(f"[{last_label}]setpts=PTS-STARTPTS[vwin]")
    frames = ["-frames:v", str(f1 - f0)] if f1 is not None else []
    return ["ffmpeg", "-v", "error", "-y", "-copyts", *args, "-filter_complex", ";".join(graph), "-map", "[vwin]", "-an",
            *encode, *frames, dst]


def key(args: list[str]) -> str:
    """Cache name of a window: its whole command (cards, times, graph, codec) minus the output path."""
    return hashlib.sha256(json.dumps(args[:-1]).encode()).hexdigest()[:16]
