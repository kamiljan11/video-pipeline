"""How each graphic type of gfx_specs.json sits on the picture (gfx/render.mjs draws them; one place for the lists).

music/make_beds.py (other folder) and the panel's timeline.sfx_events keep their own copy of CARD_WHOOSH.
"""
SIDE_BOX = ("kw", "count", "list", "slide", "web", "float", "scene", "meme")  # 16:9 graphics over the face side: no punch-in zoom under them
# ("float" = illustration beside the speaker: a punch-in would push the head into it). Not "sticker" or a "side" scene: see beside()
PIP = ("slide", "web", "scene", "meme")  # full-screen cards with the face cam in the corner (assemble.py); a 16:9 meme: render.mjs MEME_BOX "long"
FULL = ("chap", "slide", "web", "meme", "end", "scene") # full-screen cards: head_check.py does not look for the head under them (a 9:16 "web" too: its face sits in a box)
CARD_WHOOSH = ("chap", "slide", "web", "scene") # cards that come in with a whoosh; not "meme": a meme comes in silent, like the references


def beside(spec: dict) -> bool:
    """16:9 card in the free field right of the head (x >= 0.64 W: render.mjs STICKER_BOX, scene_lib SIDE): a "sticker" or a
    scene with layout "side". Not a separate screen, no PiP, and a punch-in may run under it: x1.15 around the face takes
    the head's edge from 0.61 to 0.62 W (film 2), still left of the field"""
    return spec.get("canvas") != "v" and (spec.get("type") == "sticker" or (spec.get("type") == "scene" and spec.get("layout") == "side"))


def is_full(spec: dict) -> bool:
    """a separate screen: a FULL type, except a 16:9 scene with layout "side" (drawn beside the speaker, he stays full frame)"""
    return spec.get("type") in FULL and not beside(spec)


def has_pip(spec: dict) -> bool:
    """a 16:9 card that puts the face cam in the corner (assemble.py): a PIP type, not "pip": false, not beside him (side)"""
    return spec.get("type") in PIP and spec.get("canvas") != "v" and spec.get("pip") is not False and not beside(spec)


# 9:16 "web" or "meme" card, layout "split" (gfx/render.mjs WIN_V draws the card in the top part): the face box under it (assemble.py,
# x, y, w, h and the corner radius in px of 1080x1920) and the middle of the captions in the gap between them (build_edl.py)
SPLIT = {"face_box": (130, 1240, 820, 680), "radius": 40, "caption_y": 1150}
# 9:16 "float" with layout "corner": the face in a circle in the bottom-left corner (left: the right edge holds the app buttons),
# x, y = top-left of the circle, size = its diameter, ring = accent border in px; the captions go above it
CORNER = {"x": 530, "y": 1300, "size": 460, "ring": 10, "caption_y": 1215, "halo": 1.7, "fill": 0.45}  # bottom right (Kamil 2026-10-31), 120 px in from the edge for the app buttons;
# fill: the head takes 45 % of the circle, shoulders in (Kamil 2026-11-05: "oddal mnie… nie ultra zoomed twarz")


# room above the detected face box, in face heights, by plan "punch_headroom": the hair (default) or the brow only (ADR-0012);
# face_track.py grows seg["head"] by it, assemble.py takes it back out for the window
HEADROOM = {"hair": 0.45, "face": 0.12}


def pip_window(head, sw, sh, hair, fill=0.62):
    """16:9 picture-in-picture: the square (x, y, side in source px) cut from the recording around one piece's head.

    head = face_track.py's seg["head"] (normalised x0, y0, x1, y1: the face box, `hair` face heights above it, 0.25 below).
    The whole head, hair included whatever punch_headroom cut the box at, sits in the middle of the window, a little room
    above it and the shoulders below; the window is the frame height at most (Kamil 2026-11-05: "scentruj, a nie
    przeklejaj jak na full screen"). fill = the share of the window height the head takes (the 9:16 corner circle
    takes less, so the shoulders show: CORNER["fill"])."""
    hx0, hy0, hx1, hy1 = head
    fh = (hy1 - hy0) * sh / (1 + hair + 0.25)  # face height back out of the grown box
    top, bottom = hy0 * sh - max(0.45 - hair, 0) * fh, hy1 * sh  # hair line, chin
    side = int(min(sh, sw, (bottom - top) / fill)) // 2 * 2  # the head takes `fill` of the window height
    x = min(max((hx0 + hx1) / 2 * sw - side / 2, 0), sw - side)
    y = min(max(top - 0.12 * side, 0), sh - side)
    return int(x) // 2 * 2, int(y) // 2 * 2, side
