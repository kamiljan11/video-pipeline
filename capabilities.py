#!/usr/bin/env python3
"""capabilities: every feature the pipeline has, who uses it and which gate checks it, so a film cannot leave one out unseen.

    python3 capabilities.py check                  the map against the code (exit 1: a feature without an entry, owner or check)
    python3 capabilities.py brief <role>           the features a role card owns, for the role's brief
    python3 capabilities.py map <work> <film>...   per film: used / skipped with a reason / not used

Kamil 2026-11-09 "a da sie system enforcowac zeby nie pominal rzeczy": the 2026-11-04 long had no b-roll, no grade and no
sfx_duck, and the visual upgrade plan of 2026-11-05 never reached a film, while every gate was green. Features are found in
the code (card types in gfx/render.mjs, scene pieces, backgrounds and entrances in gfx/scene_lib.mjs, plan keys read by
build_edl.py), so a new feature without an entry in style/capabilities.json fails tests/test_capabilities.py.

Use per form (style/capabilities.json "use"): "required" = the film uses it or skips it in the plan with a reason
(`"skip": {"cap.<id>": "why"}`), film_check long/short.capabilities FAILs otherwise; "report" = listed when unused (WARN);
"infra" = applied by the code to every film, nothing to choose; "never" = not for this form ("why" says why).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAP = ROOT / "style" / "capabilities.json"
FORMS = ("long", "short")
USES = ("required", "report", "infra", "never", "menu")
SPEC_JS = ("gfx/*.mjs",)  # card / scene spec options: `sp.<key>` in the renderers
SPEC_PY = ("*.py", "music/*.py")  # `sp.get("k")`, `sp["k"]` in every stage (round 4 critic: critic.py's "quote" sat outside a fixed list)
SPEC_HAND = {"sfx": "music/make_beds.py", "recap": "film_check.py"}  # read off the spec under another name; the file must still say '"k"'
PIECE_JS = ("gfx/scene_lib.mjs", "gfx/anchor_lib.mjs")  # fields of a scene piece: `e.<key>` (els[])
# fields of objects inside a piece (round 4 critic: a row's mark, a chat line's side, a counter's suffix were invisible):
# (piece field, start marker, end marker, variable) in gfx/scene_lib.mjs; id = pfx.<field>.<key>
NESTED = (("rows", "function row(", "\n}", "o"), ("msgs", "  chat: (e", "\n  }),", "g"), ("count", "  stat: (e", "\n  },", "c"))
# fields of the objects in a scene spec's lists (round 5 critic: a zoom's k / d / on, a camera stop's z / move were invisible):
# (spec option, start marker, end marker, variable) in gfx/scene_lib.mjs; id = opt.<option>.<key>
SPEC_NESTED = (("cam", "    sp.cam.forEach((s, i) => {", "\n    });", "s"), ("cam", "export function camKeyframes(", "\n}\n", "s"),
               ("cam", "export function frameStops(", "\n}\n", "s"), ("cam", "export function soloKeys(", "\n}\n", "s"),
               ("canvas_zoom", "    else sp.canvas_zoom.forEach((z, i) => {", "\n    });", "z"))
THUMBS_SPEC = {"long", "shorts"}  # `spec` also names thumbs.json ({long: [...], shorts: [...]}), outside the map (ADR-0023)
SKIP_MIN = 10  # = film_check.SKIP_MIN: a reason, not "ok" (round 3 critic: a 1-character cap skip passed)


def _between(text: str, start: str, end: str, where: str) -> str:
    i, j = text.find(start), -1
    if i >= 0: j = text.find(end, i)
    if j < 0: raise ValueError(f"{where}: marker {start!r} ... {end!r} not found (capabilities.discover reads features there; update the marker)")
    return text[i:j]


def check_of(c: dict, form: str) -> str:
    """the checklist item (or gate:<file>) that checks a feature in a film of `form`"""
    chk = c.get("check", "")
    return chk.get(form, "") if isinstance(chk, dict) else chk


def discover(root: Path = ROOT) -> dict[str, set[str]]:
    """kind -> names, read from the code itself"""
    render = (root / "gfx" / "render.mjs").read_text()
    scene = (root / "gfx" / "scene_lib.mjs").read_text()
    build = (root / "build_edl.py").read_text()
    body = _between(render, "const html = sp => {", "\n};\n", "gfx/render.mjs")
    # every `sp.type === 'x'` of the dispatcher (also `a || b` and ternaries) and `case 'x':` of a switch (round 5 critic)
    cards = set(re.findall(r"sp\.type === '(\w+)'", body)) | set(re.findall(r"case '(\w+)':", body) if "switch (sp.type)" in body else [])
    pieces = set(re.findall(r"'(\w+)'", _between(scene, "export const KINDS = [", "]", "gfx/scene_lib.mjs")))
    bgs = set(re.findall(r"'(\w+)'", _between(scene, "export const BGS = [", "]", "gfx/scene_lib.mjs")))
    anims = set(re.findall(r"(\w+): 'sc\w+ ", _between(scene, "const ANIMS = {", "};", "gfx/scene_lib.mjs")))
    anims |= set(re.findall(r"(\w+): `sc\w+ ", _between(scene, "tokens: { anims: {", "},", "gfx/scene_lib.mjs")))  # the tokens set
    keys = set(re.findall(r"""P\.get\(["'](\w+)["']""", build)) | set(re.findall(r"""P\[["'](\w+)["']\]""", build))
    keys |= set(re.findall(r'"(\w+)"', _between(build, "**{k: P[k] for k in (", ") if k in P}", "build_edl.py")))
    keys |= set(re.findall(r'"(\w+)"', _between(build, "OPTIONS = {k: P[k] for k in (", ")", "build_edl.py")))
    for py in root.glob("*.py"):  # plan keys other stages read (critic, film_check, edges, shorts...): `plan.get("x")`, `plan["x"]`
        keys |= set(re.findall(r"""\bplan\.get\(["'](\w+)["']""", py.read_text())) | set(re.findall(r"""\bplan\[["'](\w+)["']\]""", py.read_text()))
        keys |= set(re.findall(r"""\bP\.get\(["'](\w+)["']""", py.read_text()))  # critic.py reads the plan as P too
        keys |= set(re.findall(r"""["'](\w+)["'] (?:not )?in P\b""", py.read_text()))  # `if "beats" in P:`
    keys = {k for k in keys if len(k) > 1}  # a docstring example (`plan["x"]`) is no key
    opts = set()
    for f in (f for g in SPEC_JS for f in root.glob(g)):
        t = f.read_text()
        opts |= set(re.findall(r"\bsp\??\.(\w+)", t))  # sp.x, sp?.x
        for names in re.findall(r"(?:const|let) \{([^}]+)\} = sp\b", t): opts |= set(re.findall(r"(\w+)(?=\s*(?:[,=:]|$))", names))
    for f in (f for g in SPEC_PY for f in root.glob(g) if f.name != "capabilities.py"):
        t = f.read_text()
        opts |= set(re.findall(r"""\bsp\.get\(["'](\w+)["']""", t)) | set(re.findall(r"""\bsp\[["'](\w+)["']\]""", t))
        opts |= set(re.findall(r"""["'](\w+)["'] (?:not )?in sp\b""", t))
    for py in (p for p in root.glob("*.py") if p.name != "capabilities.py"):  # a spec read off the table: self.specs.get(id, {}).get("k"); a nested option: spec["behind"].get("k")
        t = py.read_text()
        opts |= set(re.findall(r"""\bspecs?(?:\[(?:[^\[\]]|\[[^\]]*\])+\]|\.get\([^)]*\))\.get\(["'](\w+)["']\)""", t))
        opts |= set(re.findall(r"""\bspec\.get\(["'](\w+)["']""", t)) - THUMBS_SPEC
        opts |= {f"{a}.{b}" for a, b in re.findall(r"""\bspec\[["'](\w+)["']\]\[["'](\w+)["']\]""", t)}
        opts |= {f"{a}.{b}" for a, b in re.findall(r"""\bspec\[["'](\w+)["']\]\.get\(["'](\w+)["']""", t)}
    build_box = re.search(r"BOX_KEYS = \(\((.*)\)\)", build)
    if build_box: opts |= set(re.findall(r'\("(\w+)"', "(" + build_box.group(1)))
    # "_on" / "_from" / "_to" / "_held": written by gfx/anchor_lib.mjs after measuring, never by a role
    pfx = {k for rel in PIECE_JS if (root / rel).exists() for k in re.findall(r"\be\.(\w+)", (root / rel).read_text()) if not k.startswith("_")}
    lib = (root / PIECE_JS[0]).read_text() if (root / PIECE_JS[0]).exists() else ""
    for field, start, end, var in NESTED:
        pfx |= {f"{field}.{k}" for k in re.findall(rf"\b{var}\.(\w+)", _between(lib, start, end, PIECE_JS[0]))}
    pfx |= {f"badge.{k}" for k in re.findall(r"\be\.badge\.(\w+)", lib)}
    for opt, start, end, var in SPEC_NESTED:
        opts |= {f"{opt}.{k}" for k in re.findall(rf"\b{var}\??\.(\w+)", _between(lib, start, end, PIECE_JS[0]))}
    opts |= {k for k, rel in SPEC_HAND.items() if (root / rel).exists() and f'"{k}"' in (root / rel).read_text()}
    return {"card": cards, "piece": pieces, "bg": bgs, "anim": anims, "plan": keys, "opt": opts, "pfx": pfx,
            "menu": {m for m, vals in menus(root).items() if vals}}


def menus(root: Path = ROOT) -> dict[str, list[str]]:
    """the lists a role picks from (shown by `brief`, not counted per film): meme templates, toons, music palettes and moods,
    card sounds, part-card styles, scene motion sets"""
    def keys_of(rel: str, start: str, end: str, rx: str) -> list[str]:
        t = (root / rel).read_text() if (root / rel).exists() else ""
        return sorted(set(re.findall(rx, _between(t, start, end, rel)))) if start in t else []
    memes = root / "style" / "memes.json"
    return {
        "meme": sorted(k for k in json.loads(memes.read_text()) if not k.startswith("_")) if memes.exists() else [],
        "toon": sorted(p.stem for p in (root / "gfx" / "toons").glob("*.svg")),
        "palette": keys_of("music/gen_music.py", "PALETTES = {", "\n}\n", r'(?m)^    "(\w+)": \{'),
        "mood": keys_of("music/make_beds.py", "MOODS = (", ")", r'"(\w+)"'),
        "sfx": sorted(set(keys_of("music/make_beds.py", "BEAT_SFX = {", "}\n", r'"(\w+)": ')) |
                      set(keys_of("music/make_beds.py", "CARD_SFX = {", "}\n", r'"(\w+)": '))),
        "chap_style": keys_of("gfx/cards_lib.mjs", "export const CHAP_STYLES = [", "]", r"'(\w+)'"),
        "motion": keys_of("gfx/scene_lib.mjs", "const MOTION = {", "\n};", r"(?m)^  (\w+): \{ anims"),
        # MEME_BOX "long" = no layout (16:9), not a choice a spec can name (round 4 critic)
        "layout": sorted(set(keys_of("gfx/render.mjs", "const MEME_BOX = {", "};", r"(\w+): \{")) - {"long"} | ({"side"} if "layout === 'side'" in
                         ((root / "gfx" / "scene_lib.mjs").read_text() if (root / "gfx" / "scene_lib.mjs").exists() else "") else set())),
        "theme": sorted(p.stem for p in (root / "style" / "themes").glob("*.json")),
        "beat": sorted(json.loads((root / "style" / "grammar.json").read_text()).get("beats", {})) if (root / "style" / "grammar.json").exists() else [],
        "tone": keys_of("gfx/scene_lib.mjs", "export const TONES = {", "};", r"(\w+): '"),
    }


def default_anims(root: Path = ROOT) -> dict[str, str]:
    """the entrance a scene piece gets without its own "anim" (scene_lib DEF_ANIM, else 'up')"""
    t = (root / "gfx" / "scene_lib.mjs").read_text()
    return dict(re.findall(r"(\w+): '(\w+)'", _between(t, "const DEF_ANIM = {", "};", "gfx/scene_lib.mjs")))


def load(path: Path = MAP) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    caps = data.get("caps") if isinstance(data, dict) else None
    if not isinstance(caps, list) or not all(isinstance(c, dict) and {"id", "use"} <= c.keys() for c in caps):
        raise ValueError(f'{path.name}: {{"caps": [{{"id", "use", ...}}, ...]}} (review 2026-11-09 data-2: a KeyError named no file)')
    return caps


def problems(caps: list[dict], found: dict[str, set[str]], root: Path = ROOT) -> list[str]:
    """what is wrong with the map: a feature of the code without an entry, an entry the code no longer has, an owner that is
    no role card, a check that is no checklist item and no file, a use outside USES, "never" without a why, "required" without
    evidence (its own why, or the why of its checklist item of that form: a long item is no evidence for a short)"""
    roles = {p.stem for p in (root / "team" / "roles").glob("*.md")}
    items = {i["id"]: i for i in json.loads((root / "style" / "checklist.json").read_text())["items"]}
    bad, ids = [], set()
    for c in caps:
        cid = f"{c.get('kind')}.{c.get('name')}"
        if c.get("id") != cid: bad.append(f"{c.get('id')}: id must be kind.name ({cid})")
        if cid in ids: bad.append(f"{cid}: twice in the map")
        ids.add(cid)
        if c.get("owner") not in roles: bad.append(f"{cid}: owner {c.get('owner')!r} is no role card in team/roles/")
        use = c.get("use") or {}
        for f in FORMS:
            chk = check_of(c, f)
            if not (chk in items or (chk.startswith("gate:") and (root / chk[5:]).exists())):
                bad.append(f"{cid}: check {chk!r} ({f}) is no style/checklist.json item and no gate:<file>")
            if use.get(f) not in USES: bad.append(f"{cid}: use.{f} {use.get(f)!r} not one of {', '.join(USES)}")
            it = items.get(chk, {})
            if use.get(f) == "required" and not c.get("why") and not (it.get("why") and it.get("fmt") in (f, "out")):
                bad.append(f"{cid}: required in the {f} without evidence (a why, or a {f} checklist item with a why as its check)")
        if "never" in use.values() and not c.get("why"): bad.append(f"{cid}: 'never' needs a why")
        if "want" in c and not (isinstance(c["want"], list) and c["want"] and all(isinstance(w, str) for w in c["want"]) and c.get("why")):
            bad.append(f"{cid}: \"want\" = a list of the values that count (strings) and a why")
        if "want" in c and c.get("kind") != "plan":  # used() names values of plan keys only: a want elsewhere could never be met
            bad.append(f"{cid}: \"want\" is for kind plan only (critic round 6: an opt/pfx want is never met)")
        if (c.get("kind") == "menu") != all(use.get(f) == "menu" for f in FORMS):
            bad.append(f"{cid}: use 'menu' is for kind menu only, and a menu is 'menu' in every form")
    for kind, names in found.items():
        if not names: bad.append(f"{kind}: 0 found in the code (the scan in capabilities.discover no longer matches it)")
        for n in sorted(names - {c["name"] for c in caps if c.get("kind") == kind}):
            bad.append(f"{kind}.{n}: in the code, not in style/capabilities.json (add it with an owner, a check and a use)")
        for n in sorted({c["name"] for c in caps if c.get("kind") == kind} - names):
            bad.append(f"{kind}.{n}: in style/capabilities.json, no longer in the code (remove it)")
    return bad


def _set(v: object) -> bool:
    return v is not None and v is not False and v not in ("", [], {})  # 0 (0 dB, x = 0) is set


def used(plan: dict, edl: dict, specs: dict, def_anim: dict[str, str] | None = None) -> set[str]:
    """ids of the capabilities a film uses: cards, their options and scene parts on screen (EDL overlays), plan keys set;
    a piece without its own "anim" enters with its default one (def_anim, else 'up')"""
    out = {f"plan.{k}" for k, v in plan.items() if _set(v)}
    out |= {f"plan.{k}={v}" for k, v in plan.items() if isinstance(v, str) and v}  # the value, for a map entry's "want"
    out |= {f"plan.{k}=true" for k, v in plan.items() if v is True}  # a gate that passes on `is True` only (caption_pop)
    for o in edl.get("overlays", []):
        sp = specs.get(o["id"], {})
        out.add(f"card.{sp.get('type')}")
        out |= {f"opt.{k}" for k, v in sp.items() if _set(v)}
        out |= {f"opt.{k}.{x}" for k, v in sp.items() if isinstance(v, dict) for x, y in v.items() if _set(y)}  # behind.clean
        out |= {f"opt.{k}.{x}" for k, v in sp.items() if isinstance(v, list) and k not in ("els", "_held")  # pieces = pfx below
                for d in v if isinstance(d, dict) for x, y in d.items() if _set(y)}  # cam[].z, canvas_zoom[].k
        if sp.get("bg"): out.add(f"bg.{sp['bg']}")
        for e in sp.get("els") or []:
            out.add(f"piece.{e.get('k')}")
            out |= {f"pfx.{k}" for k, v in e.items() if _set(v)}
            for k, v in e.items():  # rows [{t, mark}], msgs [{who, t}], count {pre, suf}, badge {text, tone}
                for d in ([v] if isinstance(v, dict) else [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []):
                    out |= {f"pfx.{k}.{x}" for x, y in d.items() if _set(y)}
            anim = e.get("anim") or (def_anim or {}).get(e.get("k", ""), "up" if def_anim is not None else None)
            if anim: out.add(f"anim.{anim}")
    return out


def coverage(caps: list[dict], form: str, have: set[str], skip: dict) -> tuple[list[str], list[str]]:
    """(required and missing, report and unused) for a film of `form`; a plan skip "cap.<id>" with a reason counts as used.
    One reason per feature: a skip of a checklist item does not waive the features it checks (long.graphics checks kw, maxim,
    gfx and broll; one sentence must not let b-roll go, the 2026-11-04 miss)"""
    def own(c: dict) -> bool:
        want = c.get("want")
        hit = any(f"{c['id']}={w}" in have for w in want) if want else c["id"] in have
        return hit or len(str(skip.get(f"cap.{c['id']}", "")).strip()) >= SKIP_MIN

    def done(c: dict) -> bool:  # a "group" (one of: float/scene/slide/web explain a part) is done by any member of that form
        g = c.get("group")
        return own(c) or bool(g) and any(own(o) for o in caps if o.get("group") == g and o["use"][form] == c["use"][form])
    miss = [c["id"] for c in caps if c["use"][form] == "required" and not done(c)]
    idle = [c["id"] for c in caps if c["use"][form] == "report" and not done(c)]
    return miss, idle


def bad_skips(caps: list[dict], skip: dict) -> list[str]:
    """plan skips of capabilities that are no capability (a typo is silently ignored otherwise) or have no real reason"""
    ids, out = {c["id"] for c in caps}, []
    for k, v in skip.items():
        if not k.startswith("cap."): continue
        if k[4:] not in ids: out.append(f"{k}: no such capability in style/capabilities.json")
        elif len(str(v).strip()) < SKIP_MIN: out.append(f"{k}: the reason must say why (>= {SKIP_MIN} characters), got {v!r}")
    return out


def main(argv: list[str]) -> int:
    if argv[:1] == ["check"]:
        try: bad = problems(load(), discover())
        except (OSError, ValueError) as e: print(f"FAIL {e}"); return 1
        for b in bad: print(f"FAIL {b}")
        print(f"capabilities: {len(load())} in the map, {len(bad)} problems {'OK' if not bad else 'FAIL'}")
        return 1 if bad else 0
    try: all_caps = load()
    except (OSError, ValueError) as e: print(f"FAIL {e}"); return 1
    if argv[:1] == ["brief"] and len(argv) == 2:
        mine, lists = [c for c in all_caps if c["owner"] == argv[1]], menus()
        for c in mine:
            if c["kind"] == "menu": print(f"- {c['id']} (pick from): {', '.join(lists.get(c['name'], []))}"); continue
            print(f"- {c['id']}: long {c['use']['long']}, short {c['use']['short']}; check {check_of(c, 'long')}/{check_of(c, 'short')}" + (f"; {c['why']}" if c.get("why") else ""))
        return 0 if mine else 1
    if argv[:1] == ["map"] and len(argv) >= 3:
        work, caps = Path(argv[1]), all_caps
        for name in argv[2:]:
            try:
                plan = json.loads((work / f"plan_{name}.json").read_text())
                edl = json.loads((work / plan.get("edl_out", f"edl_{name}.json")).read_text())
                specs = {s["id"]: s for s in json.loads((work / plan["gfx_specs"]).read_text())} if plan.get("gfx_specs") else {}
            except (OSError, ValueError, KeyError, TypeError) as e:
                print(f"FAIL capabilities map {name}: {work}/plan_{name}.json, its edl_out or gfx_specs cannot be read ({e})"); return 1
            form = "short" if plan.get("vertical") else "long"
            miss, idle = coverage(caps, form, used(plan, edl, specs, default_anims()), plan.get("skip", {}))
            skips = {k: v for k, v in plan.get("skip", {}).items() if k.startswith("cap.")}
            print(f"{name} ({form}): {len(miss)} required missing, {len(idle)} unused, {len(skips)} skipped with a reason")
            for k, v in skips.items(): print(f"  skip    {k[4:]}: {v}")
            for b in bad_skips(caps, plan.get("skip", {})): print(f"  BAD SKIP {b}")
            for m in miss: print(f"  MISSING {m}")
            for m in idle: print(f"  unused  {m}")
        return 0
    print(__doc__, file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
