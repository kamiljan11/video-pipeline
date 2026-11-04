"""How each graphic type of gfx_specs.json sits on the picture (gfx/render.mjs draws them; one place for the lists).

music/make_beds.py (other folder) and the panel's timeline.sfx_events keep their own copy of CARD_WHOOSH.
"""
SIDE_BOX = ("kw", "count", "list", "slide", "web", "float")  # 16:9 graphics over the face side: no punch-in zoom under them
# ("float" = illustration beside the speaker: a punch-in would push the head into it)
PIP = ("slide", "web")                     # full-screen cards with the face cam in the corner (assemble.py)
FULL = ("chap", "slide", "web", "end")     # full-screen cards: head_check.py does not look for the head under them (a 9:16 "web" too: its face sits in a box)
CARD_WHOOSH = ("chap", "slide", "web")     # cards that come in with a whoosh
# 9:16 "web" card, layout "split" (gfx/render.mjs WIN_V draws the card in the top part): the face box under it (assemble.py,
# x, y, w, h and the corner radius in px of 1080x1920) and the middle of the captions in the gap between them (build_edl.py)
SPLIT = {"face_box": (130, 1240, 820, 680), "radius": 40, "caption_y": 1150}
# 9:16 "float" with layout "corner": the face in a circle in the bottom-left corner (left: the right edge holds the app buttons),
# x, y = top-left of the circle, size = its diameter, ring = accent border in px; the captions go above it
CORNER = {"x": 530, "y": 1300, "size": 460, "ring": 10, "caption_y": 1215, "halo": 1.7}  # bottom right (Kamil 2026-10-31), 120 px in from the edge for the app buttons
