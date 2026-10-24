"""How each graphic type of gfx_specs.json sits on the picture (gfx/render.mjs draws them; one place for the lists).

music/make_beds.py (other folder) and the panel's timeline.sfx_events keep their own copy of CARD_WHOOSH.
"""
SIDE_BOX = ("kw", "count", "list", "slide", "web", "float")  # 16:9 graphics over the face side: no punch-in zoom under them
# ("float" = illustration beside the speaker: a punch-in would push the head into it)
PIP = ("slide", "web")                     # full-screen cards with the face cam in the corner (assemble.py)
FULL = ("chap", "slide", "web", "end")     # full-screen cards: head_check.py does not look for the head under them
CARD_WHOOSH = ("chap", "slide", "web")     # cards that come in with a whoosh
