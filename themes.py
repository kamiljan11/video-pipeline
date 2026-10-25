"""Project theme for the Python side (build_edl.py captions, assemble.py progress bar and PiP frame).

work/theme.json {"theme": "<name>"} picks style/themes/<name>.json (same file and rules as gfx/theme_lib.mjs, which colors
the cards). No theme.json in the work dir = nothing changes.
"""
import json
import re
import sys
from pathlib import Path

THEMES = Path(__file__).resolve().parent / "style" / "themes"
GFX = Path(__file__).resolve().parent / "gfx"
NAME = re.compile(r"[a-z0-9-]{1,40}")
HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def load(work: "str | Path" = ".", themes: Path = THEMES):
    """-> None without <work>/theme.json, else {"name", "acc" (#RRGGBB), "ink" (#RRGGBB)}; a bad file stops with a named error."""
    f = Path(work) / "theme.json"
    if not f.is_file(): return None
    name = _object(f).get("theme")
    if not isinstance(name, str) or not NAME.fullmatch(name): sys.exit(f"{f}: \"theme\" must be a name like \"cetus\", got {name!r}")
    src = themes / f"{name}.json"
    if not src.is_file(): sys.exit(f"{f}: no theme {name!r} ({src})")
    css = _object(src).get("css") or {}
    out = {"name": name}
    for key, tok in (("acc", "--acc"), ("ink", "--ink")):
        v = css.get(tok)
        if not isinstance(v, str) or not HEX.fullmatch(v): sys.exit(f"{src}: {tok} must be #RRGGBB, got {v!r}")
        out[key] = v.upper()
    return out


def _object(f):
    try:
        v = json.loads(f.read_text())
    except ValueError as e:
        sys.exit(f"{f}: not valid JSON ({e})")
    if not isinstance(v, dict): sys.exit(f"{f}: expected a JSON object, got {type(v).__name__}")
    return v


def bar_hex(theme):
    """Progress bar colour for the ffmpeg color source (0x...): the theme accent, else the template's own accent."""
    return theme["acc"][1:] if theme else "2de2c4"


def pip_frame(theme, gfx=GFX):
    """PiP frame PNG. A theme's frame carries its accent in the name (gfx/pip_frame_<name>_<RRGGBB>.png), so after an
    edit of --acc the old frame is not used by mistake: a missing frame stops with the command that makes it."""
    if theme is None: return str(Path(gfx) / "pip_frame.png")
    f = Path(gfx) / f"pip_frame_{theme['name']}_{theme['acc'][1:]}.png"
    if not f.is_file(): sys.exit(f"no PiP frame {f}: node gfx/pip_assets.mjs 600 {theme['acc']} {theme['name']}")
    return str(f)


def ass_color(hex_rgb, alpha=None):
    """#RRGGBB -> ASS &HBBGGRR (inline {\\c...&} tag), with alpha -> &HAABBGGRR (style field; 0 = opaque)."""
    r, g, b = hex_rgb[1:3].upper(), hex_rgb[3:5].upper(), hex_rgb[5:7].upper()
    return f"&H{'' if alpha is None else f'{alpha:02X}'}{b}{g}{r}"
