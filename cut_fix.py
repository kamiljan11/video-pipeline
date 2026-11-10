"""cut_fix: cut edges moved by hand on the Kdenlive timeline, kept in the plan and applied by build_edl.py.

Plan key "cut_fix": [[old, new], ...] — seconds in the recording. `old` is a cut edge (start or end of a piece) as
build_edl.py computes it without this key; `new` is where Kamil dragged it. Written by kden_import.py from a saved Kdenlive
project (kden_export.py makes that project from the EDL); may be typed by hand too.

Kamil 2026-11-10: "ucinasz za duzo momentami ... musze miec mozliwosc przesuwana klipow zeby np odzyskac jakas czesc".
An edge that no longer exists (the keeps changed since the export) stops the build, named: a moved cut is never dropped unseen.
"""
TOL = 0.02       # s: `old` comes from an EDL rounded to 1 ms and a 30 fps timeline; closer than one frame = the same edge
MIN_PIECE = 0.2  # s: a piece dragged shorter than this is a mistake on the timeline, not a cut


class CutFixError(ValueError):
    pass


def check(fixes) -> None:
    if not isinstance(fixes, list) or any(not isinstance(f, list) or len(f) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 for v in f) for f in fixes):
        raise CutFixError(f"cut_fix: a list of [old, new] seconds in the recording, got {fixes!r}")


def apply(segs: list[list], fixes: list[list[float]]) -> int:
    """moves the edges of `segs` ([start, end, kind], recording seconds, film order) in place; returns how many moved"""
    check(fixes)
    before = [(s[0], s[1]) for s in segs]
    for old, new in fixes:
        hits = [(i, e) for i, s in enumerate(before) for e in (0, 1) if abs(s[e] - old) <= TOL]
        if len(hits) != 1:
            raise CutFixError(f"cut_fix: {'no' if not hits else len(hits)} cut edge{'s' if hits else ''} at {old:.3f} s "
                              "(the cut changed since the Kdenlive project was made: export it again and move the edge there)")
        i, e = hits[0]
        segs[i][e] = new
    for i, s in enumerate(segs):
        if s[1] - s[0] < MIN_PIECE: raise CutFixError(f"cut_fix: the piece at {before[i][0]:.3f} s would last {s[1] - s[0]:.2f} s (under {MIN_PIECE} s)")
        # two pieces that followed each other in the recording must not overlap after the move: the same words twice
        if i and before[i][0] >= before[i - 1][1] and s[0] < segs[i - 1][1] - 1e-6:
            raise CutFixError(f"cut_fix: the pieces at {before[i - 1][0]:.3f} s and {before[i][0]:.3f} s overlap after the move "
                              f"({segs[i - 1][1]:.3f} > {s[0]:.3f}): the same words would play twice")
    return len(fixes)
