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
USES = ("required", "report", "infra", "never")


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start); return text[i:text.index(end, i)]


def discover(root: Path = ROOT) -> dict[str, set[str]]:
    """kind -> names, read from the code itself"""
    render = (root / "gfx" / "render.mjs").read_text()
    scene = (root / "gfx" / "scene_lib.mjs").read_text()
    build = (root / "build_edl.py").read_text()
    cards = set(re.findall(r"if \(sp\.type === '(\w+)'\) (?:return|\{)", _between(render, "const html = sp => {", "\n};\n")))
    pieces = set(re.findall(r"'(\w+)'", _between(scene, "export const KINDS = [", "]")))
    bgs = set(re.findall(r"'(\w+)'", _between(scene, "export const BGS = [", "]")))
    anims = set(re.findall(r"(\w+): 'sc\w+ ", _between(scene, "const ANIMS = {", "};")))
    keys = set(re.findall(r"""P\.get\(["'](\w+)["']""", build)) | set(re.findall(r"""P\[["'](\w+)["']\]""", build))
    keys |= set(re.findall(r'"(\w+)"', _between(build, "**{k: P[k] for k in (", ") if k in P}")))
    keys |= set(re.findall(r'"(\w+)"', _between(build, "OPTIONS = {k: P[k] for k in (", ")")))
    for py in root.glob("*.py"):  # plan keys other stages read (critic, film_check, edges, shorts...): `plan.get("x")`, `plan["x"]`
        keys |= set(re.findall(r"""\bplan\.get\(["'](\w+)["']""", py.read_text())) | set(re.findall(r"""\bplan\[["'](\w+)["']\]""", py.read_text()))
    keys = {k for k in keys if len(k) > 1}  # a docstring example (`plan["x"]`) is no key
    return {"card": cards, "piece": pieces, "bg": bgs, "anim": anims, "plan": keys}


def load(path: Path = MAP) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["caps"]


def problems(caps: list[dict], found: dict[str, set[str]], root: Path = ROOT) -> list[str]:
    """what is wrong with the map: a feature of the code without an entry, an entry the code no longer has, an owner that is
    no role card, a check that is no checklist item and no file, a use outside USES, "never" without a why"""
    roles = {p.stem for p in (root / "team" / "roles").glob("*.md")}
    checks = {i["id"] for i in json.loads((root / "style" / "checklist.json").read_text())["items"]}
    bad, ids = [], set()
    for c in caps:
        cid = f"{c.get('kind')}.{c.get('name')}"
        if c.get("id") != cid: bad.append(f"{c.get('id')}: id must be kind.name ({cid})")
        if cid in ids: bad.append(f"{cid}: twice in the map")
        ids.add(cid)
        if c.get("owner") not in roles: bad.append(f"{cid}: owner {c.get('owner')!r} is no role card in team/roles/")
        chk = c.get("check", "")
        if not (chk in checks or (chk.startswith("gate:") and (root / chk[5:]).exists())):
            bad.append(f"{cid}: check {chk!r} is no style/checklist.json item and no gate:<file>")
        use = c.get("use") or {}
        for f in FORMS:
            if use.get(f) not in USES: bad.append(f"{cid}: use.{f} {use.get(f)!r} not one of {', '.join(USES)}")
        if "never" in use.values() and not c.get("why"): bad.append(f"{cid}: 'never' needs a why")
    for kind, names in found.items():
        for n in sorted(names - {c["name"] for c in caps if c.get("kind") == kind}):
            bad.append(f"{kind}.{n}: in the code, not in style/capabilities.json (add it with an owner, a check and a use)")
        for n in sorted({c["name"] for c in caps if c.get("kind") == kind} - names):
            bad.append(f"{kind}.{n}: in style/capabilities.json, no longer in the code (remove it)")
    return bad


def used(plan: dict, edl: dict, specs: dict) -> set[str]:
    """ids of the capabilities a film uses: cards and scene parts on screen (EDL overlays), plan keys set"""
    out = {f"plan.{k}" for k, v in plan.items() if v not in (None, False, [], {})}
    for o in edl.get("overlays", []):
        sp = specs.get(o["id"], {})
        out.add(f"card.{sp.get('type')}")
        if sp.get("bg"): out.add(f"bg.{sp['bg']}")
        for e in sp.get("els") or []:
            out.add(f"piece.{e.get('k')}")
            if e.get("anim"): out.add(f"anim.{e['anim']}")
    return out


def coverage(caps: list[dict], form: str, have: set[str], skip: dict) -> tuple[list[str], list[str]]:
    """(required and missing, report and unused) for a film of `form`; a plan skip "cap.<id>" with a reason counts as used"""
    def done(c: dict) -> bool:  # used, or skipped with a reason: its own "cap.<id>" or its checklist item (one reason, not two)
        return c["id"] in have or any(str(skip.get(k, "")).strip() for k in (f"cap.{c['id']}", c["check"]))
    miss = [c["id"] for c in caps if c["use"][form] == "required" and not done(c)]
    idle = [c["id"] for c in caps if c["use"][form] == "report" and not done(c)]
    return miss, idle


def main(argv: list[str]) -> int:
    if argv[:1] == ["check"]:
        bad = problems(load(), discover())
        for b in bad: print(f"FAIL {b}")
        print(f"capabilities: {len(load())} in the map, {len(bad)} problems {'OK' if not bad else 'FAIL'}")
        return 1 if bad else 0
    if argv[:1] == ["brief"] and len(argv) == 2:
        mine = [c for c in load() if c["owner"] == argv[1]]
        for c in mine:
            print(f"- {c['id']}: long {c['use']['long']}, short {c['use']['short']}; check {c['check']}" + (f"; {c['why']}" if c.get("why") else ""))
        return 0 if mine else 1
    if argv[:1] == ["map"] and len(argv) >= 3:
        work, caps = Path(argv[1]), load()
        for name in argv[2:]:
            plan = json.loads((work / f"plan_{name}.json").read_text())
            edl = json.loads((work / plan.get("edl_out", f"edl_{name}.json")).read_text())
            specs = {s["id"]: s for s in json.loads((work / plan["gfx_specs"]).read_text())} if plan.get("gfx_specs") else {}
            form = "short" if plan.get("vertical") else "long"
            miss, idle = coverage(caps, form, used(plan, edl, specs), plan.get("skip", {}))
            print(f"{name} ({form}): {len(miss)} required missing, {len(idle)} unused")
            for m in miss: print(f"  MISSING {m}")
            for m in idle: print(f"  unused  {m}")
        return 0
    print(__doc__, file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
