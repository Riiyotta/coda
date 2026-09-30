#!/usr/bin/env python3
"""Regenerates schema/pagespec.schema.json from sections/*.json, templates/templates.json and
assets/asset-roles.json. The shipped schema is static JSON; this script only exists so the schema can be
re-derived (and drift-checked) from the contracts. Usage: python3 extraction/build_pagespec_schema.py [--check]"""
import copy, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PATH = r"^/(?!/)(?!.*\.\.)[A-Za-z0-9._~@%+()/-]+$"
MAX_FALLBACK_WORDS = 40
# callout.feature is polymorphic (body+media vs panels): one fully independent closed schema per branch.
ONEOF_KEEP = {"callout.feature": [["icon", "heading", "body", "extraLines", "link", "media", "mediaSide"],
                                  ["panels", "mediaSide"]]}


def load(*p):
    with open(os.path.join(ROOT, *p)) as f:
        return json.load(f)


def conv(n, routes):
    if isinstance(n, list):
        return [conv(x, routes) for x in n]
    if not isinstance(n, dict):
        return n
    out = {}
    for k, v in n.items():
        if k in ("note", "bodyCopy"):
            continue
        out[k] = conv(v, routes)
    fmt = n.get("format")
    if fmt == "local-asset-path":
        out["pattern"] = LOCAL_PATH
    elif fmt == "route-or-inert-hash":
        out.pop("format", None)
        out["enum"] = ["#"] + routes
    if n.get("type") == "string" and "maxWords" in n and "enum" not in n:
        out["minLength"] = 1
    return out


def content_schema(sid, contract, routes, roles):
    c = conv(contract["content"], routes)
    if "oneOf" in c:
        base = {k: v for k, v in c.items() if k != "oneOf"}
        branches = []
        for keep, ob in zip(ONEOF_KEEP[sid], contract["content"]["oneOf"]):
            b = copy.deepcopy(base)
            b["properties"] = {k: base["properties"][k] for k in keep}
            b["required"] = ob["required"]
            b["additionalProperties"] = False
            branches.append(b)
        return {"oneOf": branches}
    return c


def main():
    tpl = load("templates", "templates.json")["templates"]
    routes = sorted({r for t in tpl for r in t["routes"]})
    ar = load("assets", "asset-roles.json")
    roles = set(ar["assetRoleEnum"])
    secs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "sections", "*.json"))):
        d = json.load(open(f))
        secs[d["id"]] = d
    sids = sorted(secs)
    patterns = sorted({d["motion"]["pattern"] for d in secs.values()})
    branches = []
    for sid in sids:
        d = secs[sid]
        # assetRole enums: keep the contract's own (subset) enum AND require membership in the global closed enum
        cs = content_schema(sid, d, routes, roles)

        def fix(n):
            if isinstance(n, dict):
                for k in list(n):
                    v = n[k]
                    if k.lower().endswith("assetrole") and isinstance(v, dict) and "enum" in v:
                        assert set(v["enum"]) <= roles, (sid, k)
                        n[k] = {"type": "string", "allOf": [{"$ref": "#/definitions/assetRole"}, {"enum": v["enum"]}]}
                    else:
                        fix(v)
            elif isinstance(n, list):
                for x in n:
                    fix(x)
        fix(cs)
        then = {"properties": {"content": cs,
                               "motion": {"properties": {"pattern": {"const": d["motion"]["pattern"]}}}}}
        vkeys = list(d["variants"].keys()) if isinstance(d["variants"], dict) else list(d["variants"])
        if sid.startswith("shell."):
            then["not"] = {"required": ["variant"]}
        elif vkeys:
            then["properties"]["variant"] = {"enum": vkeys}
            if len(vkeys) > 1:
                then["required"] = ["variant"]
        branches.append({"if": {"properties": {"type": {"const": sid}}, "required": ["type"]}, "then": then})
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Coda PageSpec",
        "description": "A generated page: one of the closed templates, its route, and an ordered node list of section instances. There is deliberately NO per-instance token/style override field: styling is owned by section/component contracts. Non-standard keywords maxWords/maxWordsTotal are annotations enforced by schema/semantic_validate.py (word count = len(text.split())). Media use only local paths (no remote URLs) and the closed assetRole enum from assets/asset-roles.json. Generated from the section contracts by extraction/build_pagespec_schema.py.",
        "type": "object",
        "additionalProperties": False,
        "required": ["pageSpecVersion", "template", "route", "nodes"],
        "properties": {
            "$schema": {"type": "string"},
            "pageSpecVersion": {"const": "1.0.0"},
            "template": {"type": "string", "enum": [t["id"] for t in tpl]},
            "route": {"type": "string", "enum": routes},
            "nodes": {"type": "array", "minItems": 3, "items": {"$ref": "#/definitions/node"}},
        },
        "allOf": [{"if": {"properties": {"template": {"const": t["id"]}}, "required": ["template"]},
                   "then": {"properties": {"route": {"enum": t["routes"]}}}} for t in tpl],
        "definitions": {
            "assetRole": {"type": "string", "enum": ar["assetRoleEnum"],
                          "description": "Closed enum from assets/asset-roles.json."},
            "motion": {
                "type": "object", "additionalProperties": False,
                "required": ["pattern", "reducedMotionFallback"],
                "description": "Closed to the fields real section contracts carry per instance: pattern (const-locked per section) and reducedMotionFallback. The contracts' reveals/interaction/marquee/video detail is owned by the section contract, not restated per instance.",
                "properties": {
                    "pattern": {"type": "string", "enum": patterns},
                    "reducedMotionFallback": {
                        "type": "string", "minLength": 1, "maxWords": MAX_FALLBACK_WORDS,
                        "description": "REQUIRED. A design rule: the source site ships no prefers-reduced-motion handling, so this fallback is prescribed by the design-repo, not mirrored from Coda."},
                    "reducedMotionFallbackKind": {"type": "string", "enum": ["design-rule"]},
                },
            },
            "node": {
                "type": "object", "additionalProperties": False,
                "required": ["type", "content", "motion"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
                    "type": {"type": "string", "enum": sids},
                    "variant": {"type": "string"},
                    "content": {"type": "object"},
                    "motion": {"$ref": "#/definitions/motion"},
                },
                "allOf": branches,
            },
        },
    }
    out = json.dumps(schema, indent=1) + "\n"
    path = os.path.join(ROOT, "schema", "pagespec.schema.json")
    if "--check" in sys.argv:
        print("schema up to date" if open(path).read() == out else "SCHEMA DRIFT")
        sys.exit(0 if open(path).read() == out else 1)
    open(path, "w").write(out)
    print("wrote schema/pagespec.schema.json", len(out), "bytes;", len(sids), "sections;", len(tpl), "templates")


if __name__ == "__main__":
    main()
