"""What an EDL may carry into an ffmpeg command line. assemble.py pastes EDL values into -vf / -filter_complex text and
passes its file names to -i; plans and EDLs can arrive over Syncthing, so a value there must never become a filter, an
option or a protocol. check(edl) refuses anything else with the field it found (ADR-0006; behind.py uses the same rules).

Numbers: finite, |v| < 1e9. Filter chains ("audio", "grade"): only the filters in AUDIO / VIDEO, options k=v with a plain
value (no file, no quoting). File names: local paths (no "proto:" prefix). The subtitles file and its style are pasted
inside quotes, so their text has no quote, backslash or filtergraph separator."""
import re

AUDIO = frozenset({"highpass", "lowpass", "bandpass", "equalizer", "afftdn", "anlmdn", "acompressor", "agate", "alimiter",
                   "loudnorm", "dynaudnorm", "volume", "deesser", "anull"})
VIDEO = frozenset({"eq", "unsharp", "hue", "colorbalance", "vibrance", "colortemperature", "null"})
VALUE = r"[A-Za-z0-9.+-]+"  # a number, dB, a word: never a path (no /), a quote or a nested filter
FILTER = re.compile(rf"([a-z][a-z0-9_]*)(?:=(\w+={VALUE}(?::\w+={VALUE})*|{VALUE}(?::{VALUE})*))?", re.ASCII)
PROTOCOL = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")  # http:, concat:, subfile:, data: ... (a path from the plan is a file)
QUOTED_TEXT = re.compile(r"[^'\\:,;\[\]=\n\r]*")  # pasted between '...' in the filtergraph (subtitles file name)
STYLE = re.compile(r"[A-Za-z0-9 =,.&#-]*")  # ASS force_style: Fontname=..,Fontsize=..,PrimaryColour=&H..
HEX = re.compile(r"#[0-9A-Fa-f]{6}")
NAME = re.compile(r"[A-Za-z0-9_-]+")


class EdlError(ValueError):
    pass


def num(v) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool) and -1e9 < v < 1e9  # NaN, inf and 10**400 fail too


def pair(p) -> bool:
    return isinstance(p, list) and len(p) == 2 and all(map(num, p))


def shape_ok(edl) -> bool:
    """what every step indexes: segments with numeric in/out and a known source, overlays with a numeric at"""
    if not isinstance(edl, dict):
        return False
    segs, ovs, srcs = edl.get("segments"), edl.get("overlays", []), edl.get("sources")  # no overlays = no card in it
    if not (isinstance(segs, list) and isinstance(ovs, list) and isinstance(srcs, dict)):
        return False
    return (all(isinstance(v, str) for v in srcs.values()) and all(isinstance(o, dict) and num(o.get("at")) for o in ovs)
            and all(isinstance(g, dict) and num(g.get("in")) and num(g.get("out")) and g.get("src") in srcs for g in segs))


def framing_ok(edl: dict) -> bool:
    """the EDL-wide values vf_for pastes into the filter (a key present means set: null is refused, not defaulted)"""
    ok = all(num(edl[k]) for k in ("w", "h", "src_w", "src_h") if k in edl)
    ok = ok and (edl.get("face_target_y") is None or num(edl["face_target_y"]))  # null = vf_for's own default
    return ok and pair(edl.get("face", [0.5, 0.45])) and isinstance(edl.get("vertical", False), bool)


def segment_ok(s: dict) -> bool:
    """a segment's zoom (number or {a, b, t0, t1, keys}), face and track: numbers only"""
    z, face, track = s.get("zoom", 1.0), s.get("face"), s.get("track")
    ok = num(z) or (isinstance(z, dict) and all(num(z.get(k)) for k in ("a", "b", "t0", "t1"))
                    and isinstance(z.get("keys") or [], list) and all(map(pair, z.get("keys") or [])))
    return ok and (face is None or pair(face)) and (track is None or (isinstance(track, list) and all(map(pair, track))))


def chain_ok(text, allowed: frozenset) -> bool:
    if not isinstance(text, str) or not text:
        return False
    for part in text.split(","):
        m = FILTER.fullmatch(part)
        if not (m and m.group(1) in allowed):
            return False
    return True


def local_file(v) -> bool:
    return isinstance(v, str) and bool(v) and not PROTOCOL.match(v) and "\n" not in v


def problems(edl) -> list[str]:
    """every field of the EDL that assemble.py would carry into ffmpeg and that breaks the rules above"""
    if not shape_ok(edl):
        return ["segments (in/out numbers, src in sources), overlays (at number), sources (file names)"]
    out = []
    if not framing_ok(edl):
        out.append("w / h / src_w / src_h / face / face_target_y must be numbers, vertical true or false")
    out += [f"segment at {s['in']}: zoom / face / track must be numbers" for s in edl["segments"] if not segment_ok(s)]
    out += [f"{k} must be a number" for k in ("tail", "music_db", "sfx_db", "pip_size", "music_offset")
            if edl.get(k) is not None and not num(edl[k])]
    out += [f"{k}: only the filters {sorted(allowed)}, options with plain values" for k, allowed in (("audio", AUDIO), ("grade", VIDEO))
            if k in edl and not chain_ok(edl[k], allowed)]
    for o in edl.get("overlays", []):
        if not (local_file(o.get("file", "")) and num(o.get("dur", 0))):
            out.append(f"overlay at {o['at']}: file must be a local path, dur a number")
    for b in edl.get("broll", []) if isinstance(edl.get("broll", []), list) else [None]:
        if not (isinstance(b, dict) and local_file(b.get("file")) and all(num(b.get(k, 0)) for k in ("at", "dur", "ss"))):
            out.append("broll: each clip needs a local file and numeric at / dur / ss")
    out += [f"sources {k}: a local path" for k, v in edl["sources"].items() if not local_file(v)]
    out += [f"{k}: a local path" for k in ("music", "sfx") if edl.get(k) and not local_file(edl[k])]
    if edl.get("subs") and not (local_file(edl["subs"]) and QUOTED_TEXT.fullmatch(edl["subs"])):
        out.append("subs: a local path without quotes, backslashes or : , ; [ ] =")
    if not (isinstance(edl.get("sub_style", ""), str) and STYLE.fullmatch(edl.get("sub_style", ""))):
        out.append("sub_style: ASS style text (letters, digits, space = , . & # -)")
    th = edl.get("theme")
    if th is not None and not (isinstance(th, dict) and isinstance(th.get("acc"), str) and HEX.fullmatch(th["acc"])
                               and isinstance(th.get("name"), str) and NAME.fullmatch(th["name"])):
        out.append("theme: name [A-Za-z0-9_-], acc #RRGGBB")
    return out


def check(edl) -> None:
    if bad := problems(edl):
        raise EdlError("EDL refused (" + "; ".join(bad) + ")")
