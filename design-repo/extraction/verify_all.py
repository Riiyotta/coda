#!/usr/bin/env python3
"""verify_all.py - one-shot integrity check for this design-repo. Exit code 0 only if every check passes.

Usage:  python3 extraction/verify_all.py            run all checks, print PASS/FAIL/WARN lines and a summary
        python3 extraction/verify_all.py --emit-counts   print the recomputed counts (JSON + the README block)

The repo root is derived from this file's location (no absolute paths). Checks:
  [a] json-parse            every *.json parses
  [b] schema-example        pagespec.schema.json is valid Draft-07; the example has 0 schema errors and passes semantic_validate
  [c] schema-uptodate       extraction/build_pagespec_schema.py --check
  [d] allowlist-parity      component-allowlist.json <-> primitive/component/section contract ids, both directions
  [e] allowlist-version     allowlistVersion in the allowlist == registry.manifest.json
  [f] manifest-counts       manifest `counts` recomputed from disk (+ README counts block, + catalog parity)
  [g] route-template        15 routes <-> templates 1:1, manifest routeTemplateMap, route admission over every route
  [h] template-graph        template node sections exist, schema section enum, graph rule ids <-> validator RULES
  [i] citations             every `path:line[-line]` citation resolves against the real source file + quote (WARN when no sibling source tree)
  [j] asset-roles           closed 18-role enum, closed policy set, PINNED value for every complianceCritical role
  [k] token-refs            token references resolve; catalog/policy category names match; theme completeness; colour provenance in the stylesheet (WARN without source tree)
  [l] no-absolute-paths     no machine-local absolute paths in any shipped file
  [m] entrypoints-docs      entryPoints exist inside the repo (no `..`), cover every file; every documented file exists
  [n] version-note          versionFieldNote present and honest about machine-checked vs documentation-only fields
Drift proof for these checks: python3 extraction/prove_drift.py
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.dirname(ROOT)  # sibling project tree, only present while the repo sits next to its source project

_ABS_PATTERNS = [re.compile(p) for p in (
    "/" + "Users" + "/", "/" + "home" + "/[A-Za-z0-9_.-]+/", "(?<![A-Za-z0-9])[A-Za-z]:" + "\\\\" + "[A-Za-z]", "/private" + "/(?:var|tmp)/")]

RESULTS = []  # (status, name, message)


def rel(p):
    return os.path.relpath(p, ROOT)


def jload(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


def all_files():
    out = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git")]
        for f in files:
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            out.append(os.path.join(d, f))
    return sorted(out)


def json_files():
    return [p for p in all_files() if p.endswith(".json")]


def contract_files():
    return {k: sorted(glob.glob(os.path.join(ROOT, k, "*.json"))) for k in ("primitives", "components", "sections")}


def contract_ids():
    ids = {}
    for kind, files in contract_files().items():
        for f in files:
            with open(f, encoding="utf-8") as fh:
                ids[json.load(fh)["id"]] = (kind, f)
    return ids


def token_tiers():
    """{tier: {token id: token}} from disk. Foundation includes the font entries."""
    tiers = {"foundation": {}, "semantic": {}, "component": {}, "layout": {}}
    for tier, d in (("foundation", "00-foundation"), ("semantic", "10-semantic"), ("component", "20-component"), ("layout", "30-layout")):
        for f in sorted(glob.glob(os.path.join(ROOT, "tokens", d, "*.json"))):
            with open(f, encoding="utf-8") as fh:
                j = json.load(fh)
            tiers[tier].update(j.get("tokens", {}))
            tiers[tier].update(j.get("fonts", {}))
    return tiers


def compute_counts():
    tiers = token_tiers()
    tpl = jload("templates", "templates.json")["templates"]
    cf = contract_files()
    t = {k: len(v) for k, v in tiers.items()}
    t["total"] = sum(t.values())
    cat = jload("tokens", "llm", "token-catalog.json")["categories"]
    return {
        "tokens": t,
        "catalogEntries": sum(len(v["tokens"]) for v in cat.values()),
        "primitives": len(cf["primitives"]),
        "components": len(cf["components"]),
        "sections": len(cf["sections"]),
        "templates": len(tpl),
        "routes": len({r for x in tpl for r in x["routes"]}),
        "graphRules": len(jload("compatibility", "graph.json")["rules"]),
        "assetRoles": len(jload("assets", "asset-roles.json")["roles"]),
        "citations": len(jload("extraction", "measured-values.json")["citations"]),
    }


def counts_block(c):
    t = c["tokens"]
    return ("- Tokens: %d total (foundation %d, semantic %d, component %d, layout %d); catalog entries: %d\n"
            "- Primitives %d, components %d, sections %d\n"
            "- Templates %d, routes %d (1:1), graph rules %d, asset roles %d, ledger citations %d" % (
                t["total"], t["foundation"], t["semantic"], t["component"], t["layout"], c["catalogEntries"],
                c["primitives"], c["components"], c["sections"], c["templates"], c["routes"], c["graphRules"],
                c["assetRoles"], c["citations"]))


# ------------------------------------------------------------------------------------------------ framework
def check(name):
    def deco(fn):
        def run():
            try:
                fails, warns, info = fn()
            except Exception as e:  # a crashing check is a failing check
                fails, warns, info = ["check crashed: %s: %s" % (type(e).__name__, e)], [], ""
            for w in warns:
                RESULTS.append(("WARN", name, w))
            if fails:
                for m in fails[:12]:
                    RESULTS.append(("FAIL", name, m))
                if len(fails) > 12:
                    RESULTS.append(("FAIL", name, "... and %d more" % (len(fails) - 12)))
            else:
                RESULTS.append(("PASS", name, info))
        run.__name__ = fn.__name__
        CHECKS.append(run)
        return fn
    return deco


CHECKS = []


def walk_strings(o, fn, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            walk_strings(v, fn, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_strings(v, fn, path + "[%d]" % i)
    elif isinstance(o, str):
        fn(path, o)


# ------------------------------------------------------------------------------------------------ [a]
@check("[a] json-parse")
def c_a():
    fails, n = [], 0
    for p in json_files():
        n += 1
        try:
            with open(p, encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            fails.append("%s: %s" % (rel(p), e))
    return fails, [], "%d json files parse" % n


# ------------------------------------------------------------------------------------------------ [b]
@check("[b] schema-example")
def c_b():
    from jsonschema import Draft7Validator
    fails = []
    schema = jload("schema", "pagespec.schema.json")
    try:
        Draft7Validator.check_schema(schema)
    except Exception as e:
        return ["pagespec.schema.json is not a valid Draft-07 schema: %s" % str(e)[:200]], [], ""
    if schema.get("$schema", "").rstrip("#") != "http://json-schema.org/draft-07/schema":
        fails.append("schema $schema is not draft-07: %r" % schema.get("$schema"))
    ex = jload("schema", "example.pagespec.json")
    errs = list(Draft7Validator(schema).iter_errors(ex))
    for e in errs[:5]:
        fails.append("example schema error at %s: %s" % ("/".join(map(str, e.absolute_path)), e.message[:160]))
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    errors, warnings = sv.validate(ex, ROOT)
    fails.extend("example semantic error: %s" % e for e in errors[:8])
    return fails, [], "Draft-07 schema valid; example has 0 schema errors and 0 semantic errors (%d warnings)" % len(warnings)


# ------------------------------------------------------------------------------------------------ [c]
@check("[c] schema-uptodate")
def c_c():
    script = os.path.join(ROOT, "extraction", "build_pagespec_schema.py")
    if not os.path.isfile(script):
        return ["extraction/build_pagespec_schema.py is missing"], [], ""
    r = subprocess.run([sys.executable, script, "--check"], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return ["build_pagespec_schema.py --check exit %d: %s" % (r.returncode, out[:200])], [], ""
    return [], [], out


# ------------------------------------------------------------------------------------------------ [d]
@check("[d] allowlist-parity")
def c_d():
    fails = []
    al = jload("tokens", "llm", "component-allowlist.json")["components"]
    ids = contract_ids()
    if len(al) != len(set(al)):
        fails.append("allowlist has duplicate entries")
    for a in sorted(set(al) - set(ids)):
        fails.append("phantom allowlist id (no contract): %s" % a)
    for i in sorted(set(ids) - set(al)):
        fails.append("orphan contract (not in allowlist): %s (%s)" % (i, rel(ids[i][1])))
    for i, (kind, f) in ids.items():  # contract folder / file name coherence
        if os.path.basename(f) != i.replace(".", "-") + ".json":
            fails.append("file name %s does not match id %s" % (rel(f), i))
        prefix = i.split(".")[0]
        want = {"primitive": "primitives", "component": "components"}.get(prefix, "sections")
        if kind != want:
            fails.append("%s lives in the wrong folder %s (expected %s)" % (i, kind, want))
    return fails, [], "%d allowlist ids == %d contract ids (no phantom, no orphan)" % (len(set(al)), len(ids))


# ------------------------------------------------------------------------------------------------ [e]
@check("[e] allowlist-version")
def c_e():
    a = jload("tokens", "llm", "component-allowlist.json").get("allowlistVersion")
    m = jload("registry.manifest.json").get("allowlistVersion")
    if not a or a != m:
        return ["allowlistVersion mismatch: allowlist=%r manifest=%r" % (a, m)], [], ""
    return [], [], "allowlistVersion %s in allowlist and manifest" % a


# ------------------------------------------------------------------------------------------------ [f]
@check("[f] manifest-counts")
def c_f():
    fails = []
    got = compute_counts()
    claim = jload("registry.manifest.json").get("counts")
    if not isinstance(claim, dict):
        return ["manifest has no counts block"], [], ""

    def cmp(path, a, b):
        if isinstance(a, dict) or isinstance(b, dict):
            if not (isinstance(a, dict) and isinstance(b, dict)):
                fails.append("counts.%s: shape differs (disk %r vs manifest %r)" % (path, a, b))
                return
            for k in sorted(set(a) | set(b)):
                cmp(path + "." + k if path else k, a.get(k, "<absent>"), b.get(k, "<absent>"))
        elif a != b:
            fails.append("counts.%s: disk=%s manifest=%s" % (path, a, b))
    cmp("", got, claim)
    # catalog parity: every catalog id exists on disk per tier, and the catalog's own counts are honest
    cat = jload("tokens", "llm", "token-catalog.json")
    tiers = token_tiers()
    by_tier = {}
    for name, v in cat["categories"].items():
        if v["count"] != len(v["tokens"]):
            fails.append("catalog %s count %d != %d entries" % (name, v["count"], len(v["tokens"])))
        by_tier.setdefault(v["tier"], set()).update(t["id"] for t in v["tokens"])
    for tier, ids in tiers.items():
        if by_tier.get(tier, set()) != set(ids):
            fails.append("catalog tier %s ids differ from disk (only-catalog %s, only-disk %s)" % (
                tier, sorted(by_tier.get(tier, set()) - set(ids))[:4], sorted(set(ids) - by_tier.get(tier, set()))[:4]))
    if cat.get("counts") and {k: v["count"] for k, v in cat["categories"].items()} != cat["counts"]:
        fails.append("catalog `counts` block differs from its categories")
    # README counts block must equal the recomputed block (hand-written counts are a drift source)
    rp = os.path.join(ROOT, "README.md")
    if os.path.isfile(rp):
        with open(rp, encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r"<!-- counts:begin -->\n(.*?)\n<!-- counts:end -->", txt, re.S)
        if not m:
            fails.append("README.md has no <!-- counts:begin/end --> block")
        elif m.group(1).strip() != counts_block(got).strip():
            fails.append("README.md counts block differs from the recomputed counts")
    else:
        fails.append("README.md missing")
    return fails, [], "manifest counts == disk (%d tokens, %d sections, %d templates, %d routes, %d citations); catalog + README block agree" % (
        got["tokens"]["total"], got["sections"], got["templates"], got["routes"], got["citations"])


# ------------------------------------------------------------------------------------------------ [g]
@check("[g] route-template")
def c_g():
    fails = []
    man = jload("registry.manifest.json")
    tpls = jload("templates", "templates.json")["templates"]
    schema = jload("schema", "pagespec.schema.json")
    served = {}
    for t in tpls:
        for r in t["routes"]:
            served.setdefault(r, []).append(t["id"])
    for r, ts in sorted(served.items()):
        if len(ts) != 1:
            fails.append("route %s is served by %d templates %s (must be exactly 1)" % (r, len(ts), ts))
    mp = man.get("routeTemplateMap")
    if not isinstance(mp, dict):
        fails.append("manifest has no routeTemplateMap")
        mp = {}
    if set(mp) != set(served):
        fails.append("manifest routeTemplateMap routes differ from templates (only-manifest %s, only-templates %s)" % (
            sorted(set(mp) - set(served)), sorted(set(served) - set(mp))))
    for r, ts in served.items():
        if mp.get(r) != ts[0]:
            fails.append("route %s: manifest says template %r, templates.json says %r" % (r, mp.get(r), ts[0]))
    if len(served) != man.get("counts", {}).get("routes") or len(served) != 15:
        fails.append("expected exactly 15 routes, found %d (manifest claims %s)" % (len(served), man.get("counts", {}).get("routes")))
    props = schema["properties"]
    if set(props["route"]["enum"]) != set(served):
        fails.append("schema route enum differs from template routes")
    if set(props["template"]["enum"]) != {t["id"] for t in tpls}:
        fails.append("schema template enum differs from template ids")
    # route admission, unscoped over EVERY route: each node's section must admit the route (usedOn, restrictions)
    contracts = {i: json.load(open(f, encoding="utf-8")) for i, (k, f) in contract_ids().items() if k == "sections"}
    graph = jload("compatibility", "graph.json")
    restr = next((r.get("restrictions", {}) for r in graph["rules"] if r["id"] == "ROUTE_RESTRICTED_SECTIONS"), {})
    checked = 0
    for t in tpls:
        for r in t["routes"]:
            for n in t["nodes"]:
                s = n["section"]
                if s not in contracts:
                    continue
                allowed = restr.get(s, contracts[s].get("usedOn"))
                checked += 1
                if allowed is not None and r not in allowed:
                    if n["required"]:
                        fails.append("route %s: template %s REQUIRES section %s which is not admitted on that route (usedOn %s)" % (r, t["id"], s, allowed))
                    else:
                        # an optional node may be admitted on only some of the template's routes; the instance-level rule
                        # ROUTE_RESTRICTED_SECTIONS rejects it elsewhere. It must be admitted on at least one route, though.
                        if not any(allowed is None or rr in allowed for rr in t["routes"]):
                            fails.append("template %s optional section %s is admitted on none of its routes" % (t["id"], s))
                v = n.get("variant")
                ct = contracts[s]
                if v and isinstance(ct.get("variants"), dict):
                    vr = ct["variants"].get(v, {}).get("routes") if isinstance(ct["variants"].get(v), dict) else None
                    if vr and r not in vr:
                        fails.append("route %s: %s variant %r is only evidenced on %s" % (r, s, v, vr))
    return fails, [], "%d routes <-> %d templates 1:1; manifest map agrees; %d route/section admissions consistent" % (len(served), len(tpls), checked)


# ------------------------------------------------------------------------------------------------ [h]
@check("[h] template-graph")
def c_h():
    fails = []
    tpls = jload("templates", "templates.json")["templates"]
    sec_ids = {i for i, (k, f) in contract_ids().items() if k == "sections"}
    used = set()
    for t in tpls:
        for n in t["nodes"]:
            used.add(n["section"])
            if n["section"] not in sec_ids:
                fails.append("template %s node %r has no section contract" % (t["id"], n["section"]))
        if t.get("nodeCount") not in (None, len(t["nodes"])):
            fails.append("template %s nodeCount %s != %d nodes" % (t["id"], t.get("nodeCount"), len(t["nodes"])))
        if t["nodes"][0]["section"] != "shell.navbar" or t["nodes"][-1]["section"] != "shell.footer":
            fails.append("template %s does not start with shell.navbar / end with shell.footer" % t["id"])
    schema = jload("schema", "pagespec.schema.json")
    enum = set(schema["definitions"]["node"]["properties"]["type"]["enum"])
    if enum != sec_ids:
        fails.append("schema section enum != section contracts (only-schema %s, only-contracts %s)" % (sorted(enum - sec_ids), sorted(sec_ids - enum)))
    for s in sorted(sec_ids - used):
        fails.append("section %s is not used by any template" % s)
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    un, miss = sv.graph_parity(ROOT)
    if un:
        fails.append("graph rule ids with no validator implementation: %s" % un)
    if miss:
        fails.append("validator RULES missing from graph.json: %s" % miss)
    graph = jload("compatibility", "graph.json")
    for r in graph["rules"]:
        if r.get("severity") not in ("error", "warn"):
            fails.append("graph rule %s has severity %r" % (r["id"], r.get("severity")))
    return fails, [], "%d template node sections all have contracts; schema enum == %d sections; %d graph rules <-> validator RULES" % (
        len(used), len(sec_ids), len(graph["rules"]))


# ------------------------------------------------------------------------------------------------ [i]
_CIT = re.compile(r"^([\w./ -]+\.(?:jsx|js|css|json|md|html|py)):(\d+)(?:-(\d+))?$")
_TEXT_CACHE = {}


def _read(path):
    if path not in _TEXT_CACHE:
        with open(path, encoding="utf-8") as f:
            _TEXT_CACHE[path] = f.read()
    return _TEXT_CACHE[path]


def collect_citations():
    """[(file, source string, dict-or-None)] for every path:line[-line] source in every json file."""
    out = []

    def walk(o, f):
        if isinstance(o, dict):
            s = o.get("source")
            if isinstance(s, str) and _CIT.match(s):
                out.append((f, s, o))
            for k, v in o.items():
                if not (k == "source" and isinstance(v, str)):
                    walk(v, f)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, str) and _CIT.match(v):
                    out.append((f, v, None))
                else:
                    walk(v, f)
    for p in json_files():
        with open(p, encoding="utf-8") as fh:
            walk(json.load(fh), rel(p))
    return out


def source_tree_present():
    return os.path.isdir(os.path.join(SRC_ROOT, "src")) and os.path.isfile(os.path.join(SRC_ROOT, "package.json"))


@check("[i] citations")
def c_i():
    allc = collect_citations()
    if not allc:
        return ["no citations found at all (ledger empty?)"], [], ""
    # citations into this package itself ("design-repo/...") always resolve against ROOT; the rest need the source tree
    selfc = [c for c in allc if c[1].startswith("design-repo/")]
    cits = [c for c in allc if not c[1].startswith("design-repo/")]
    have_src = source_tree_present()
    warns = []
    if not have_src:
        warns.append("source tree not present beside the package: %d citations NOT resolved (self-contained mode, not a "
                     "failure). Re-run next to the source project to verify them." % len(cits))
        cits = []
    fails, ok = [], 0
    for f, s, d in cits + selfc:
        m = _CIT.match(s)
        path, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        fp = os.path.join(ROOT, path[len("design-repo/"):]) if path.startswith("design-repo/") else os.path.join(SRC_ROOT, path)
        if not os.path.isfile(fp):
            fails.append("%s: %s -> file does not exist" % (f, s))
            continue
        txt = _read(fp)
        lines = txt.split("\n")  # NOT splitlines(): JSX contains U+2028/form-feed chars that are not line breaks for editors
        if lines and lines[-1] == "":
            lines.pop()
        if a < 1 or a > b or b > len(lines):
            fails.append("%s: %s out of range (file has %d lines)" % (f, s, len(lines)))
            continue
        if d is not None and isinstance(d.get("quote"), str):
            q = d["quote"]
            if "charRange" in d:
                lo, hi = d["charRange"]
                if not (0 <= lo < hi <= len(txt)):
                    fails.append("%s: %s charRange %s outside file (%d chars)" % (f, s, d["charRange"], len(txt)))
                    continue
                if q not in txt[lo:hi]:
                    fails.append("%s: %s quote %r not found at charRange %s" % (f, s, q[:50], d["charRange"]))
                    continue
            elif q not in "\n".join(lines[a - 1:b]):
                fails.append("%s: %s quote %r not found at those lines" % (f, s, q[:50]))
                continue
        ok += 1
    info = "%d/%d citations resolve (line range + quote; CSS quote at charRange) against the real files" % (ok, len(cits) + len(selfc))
    if not have_src:
        info = "%d/%d resolved (%d in-package); %d source-tree citations skipped" % (ok, len(allc), len(selfc), len(allc) - len(selfc))
    return fails, warns, info


# ------------------------------------------------------------------------------------------------ [j]
def _role_strings(o, key_hit=False, acc=None, path=""):
    """Strings living under an assetRole/assetRoles key (any depth), skipping schema keywords."""
    acc = [] if acc is None else acc
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("$ref", "type", "description", "note", "format", "pattern"):
                continue
            _role_strings(v, key_hit or k in ("assetRole", "assetRoles"), acc, path + "/" + k)
    elif isinstance(o, list):
        for v in o:
            _role_strings(v, key_hit, acc, path)
    elif isinstance(o, str) and key_hit:
        acc.append((path, o))
    return acc


@check("[j] asset-roles")
def c_j():
    fails = []
    ar = jload("assets", "asset-roles.json")
    enum, pol = ar["assetRoleEnum"], ar["generationPolicyEnum"]
    if len(enum) != 18 or len(set(enum)) != 18:
        fails.append("assetRoleEnum must be the closed 18-role set (found %d)" % len(enum))
    if ar.get("closed") is not True:
        fails.append("asset-roles.json is not marked closed")
    if len(pol) != 4 or len(set(pol)) != 4:
        fails.append("generationPolicyEnum must be the closed 4-value set (found %r)" % pol)
    roles = {r["id"]: r for r in ar["roles"]}
    if set(roles) != set(enum) or len(ar["roles"]) != len(enum):
        fails.append("roles[] ids differ from assetRoleEnum")
    pinned_declared = set(ar.get("pinnedRoles", []))
    critical = {i for i, r in roles.items() if r.get("complianceCritical")}
    if pinned_declared != critical:
        fails.append("pinnedRoles %s != complianceCritical roles %s" % (sorted(pinned_declared ^ critical), sorted(critical)))
    for i, r in roles.items():
        if r["generationPolicy"] not in pol:
            fails.append("role %s generationPolicy %r is not in the closed policy set" % (i, r["generationPolicy"]))
        if r.get("complianceCritical"):
            # PINNED VALUE (not just enum membership): generationPolicy must equal the value this file pins
            if r.get("pinnedPolicy") not in pol:
                fails.append("role %s pinnedPolicy %r invalid" % (i, r.get("pinnedPolicy")))
            if r["generationPolicy"] != r.get("pinnedPolicy"):
                fails.append("PINNED role %s: generationPolicy %r != pinnedPolicy %r" % (i, r["generationPolicy"], r.get("pinnedPolicy")))
            if r.get("realCompanyAssets") and r.get("pinnedPolicy") == "may-generate-new":
                fails.append("PINNED role %s covers real-company assets but is pinned to may-generate-new" % i)
        elif "pinnedPolicy" in r and r["pinnedPolicy"] != r["generationPolicy"]:
            fails.append("role %s carries a pinnedPolicy that differs from its generationPolicy" % i)
    # closure: every role named anywhere (contracts, schema, allowlist-adjacent files) is in the enum
    used = set()
    for p in json_files():
        if rel(p) == os.path.join("assets", "asset-roles.json"):
            continue
        with open(p, encoding="utf-8") as fh:
            j = json.load(fh)
        for path, s in _role_strings(j):
            used.add(s)
            if s not in enum:
                fails.append("%s%s: assetRole %r is not in the closed enum" % (rel(p), path, s))

        def enums(o, pth=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "enum" and isinstance(v, list) and any(x in enum for x in v if isinstance(x, str)):
                        for x in v:
                            if x not in enum:
                                fails.append("%s%s: enum mixes asset roles with non-role %r" % (rel(p), pth, x))
                    enums(v, pth + "/" + str(k))
            elif isinstance(o, list):
                for v in o:
                    enums(v, pth)
        enums(j)
    sch = jload("schema", "pagespec.schema.json")
    if set(sch["definitions"]["assetRole"]["enum"]) != set(enum):
        fails.append("schema definitions.assetRole enum != assetRoleEnum")
    return fails, [], "18-role enum closed, 4-policy set closed, %d compliance-critical roles pinned (generationPolicy == pinnedPolicy); %d roles referenced in contracts/schema all in enum" % (len(critical), len(used))


# ------------------------------------------------------------------------------------------------ [k]
@check("[k] token-refs")
def c_k():
    fails = []
    tiers = token_tiers()
    allids = {i for t in tiers.values() for i in t}
    cat = jload("tokens", "llm", "token-catalog.json")
    pol = jload("tokens", "llm", "token-policy.json")
    if set(pol["rawValueRestrictions"]) != set(cat["categories"]):
        fails.append("token-policy category names differ from catalog keys (only-policy %s, only-catalog %s)" % (
            sorted(set(pol["rawValueRestrictions"]) - set(cat["categories"])), sorted(set(cat["categories"]) - set(pol["rawValueRestrictions"]))))
    n = 0
    # $ref inside token files
    for tier, toks in tiers.items():
        for i, t in toks.items():
            if isinstance(t, dict) and isinstance(t.get("$ref"), str):
                n += 1
                if t["$ref"] not in allids:
                    fails.append("token %s $ref -> unknown token %r" % (i, t["$ref"]))
    # catalog resolvesTo
    for cname, c in cat["categories"].items():
        for t in c["tokens"]:
            if "resolvesTo" in t:
                n += 1
                if t["resolvesTo"] not in allids:
                    fails.append("catalog %s resolvesTo unknown %r" % (t["id"], t["resolvesTo"]))
    # themes
    sem = set(tiers["semantic"])
    schema_themes = jload("registry.manifest.json").get("schemaValidatedThemes", [])
    for th in schema_themes:
        tp = os.path.join(ROOT, "tokens", "themes", th + ".json")
        if not os.path.isfile(tp):
            fails.append("schemaValidatedThemes lists %r but tokens/themes/%s.json is missing" % (th, th))
            continue
        res = jload("tokens", "themes", th + ".json")["resolutions"]
        for i, r in res.items():
            n += 1
            if r.get("resolvesTo") not in allids:
                fails.append("theme %s: %s resolvesTo unknown %r" % (th, i, r.get("resolvesTo")))
        for i in sorted(sem - set(res)):
            fails.append("theme %s does not resolve semantic token %s" % (th, i))
        for i in sorted(set(res) - sem):
            fails.append("theme %s resolves unknown semantic token %s" % (th, i))
    # contracts
    for i, (kind, f) in contract_ids().items():
        with open(f, encoding="utf-8") as fh:
            tk = json.load(fh).get("tokens")
        vals = tk if isinstance(tk, list) else (list(tk) if isinstance(tk, dict) else [])
        for v in vals:
            n += 1
            if not isinstance(v, str) or v not in allids:
                fails.append("%s: token reference %r does not exist" % (rel(f), v))
    # evidence ids (cit-*) referenced anywhere resolve in the ledger
    led = {c["id"] for c in jload("extraction", "measured-values.json")["citations"]}
    for p in json_files():
        if rel(p).startswith("extraction"):
            continue
        with open(p, encoding="utf-8") as fh:
            j = json.load(fh)

        def chk(path, s, p=p):
            for m in re.findall(r"\bcit-[A-Za-z0-9-]*[A-Za-z0-9](?![-*A-Za-z0-9])", s):
                if m not in led:
                    fails.append("%s%s: evidence id %s not in the citation ledger" % (rel(p), path, m))
        walk_strings(j, chk)
    # colour provenance: every foundation colour must exist in the compiled stylesheet (needs the source tree)
    warns = []
    css = os.path.join(SRC_ROOT, "public", "styles", "coda-main.css")
    if source_tree_present() and os.path.isfile(css):
        ctxt = open(css, encoding="utf-8").read().lower()
        nc = 0
        for i, t in tiers["foundation"].items():
            if i.startswith("color.") and isinstance(t, dict) and t.get("rgb"):
                nc += 1
                r, g, b = t["rgb"]
                if t.get("cssVar"):
                    ok = re.search(re.escape(t["cssVar"].lower()) + r"\s*:\s*%d %d %d\b" % (r, g, b), ctxt)
                else:
                    ok = ("#%02x%02x%02x" % (r, g, b)) in ctxt
                if not ok:
                    fails.append("colour provenance: %s %s is not declared in public/styles/coda-main.css" % (i, t["rgb"]))
        n += nc
    else:
        warns.append("colour provenance NOT checked: stylesheet not present beside the package (self-contained mode)")
    return fails, warns, "%d token/theme/catalog/contract/colour-provenance references resolve; policy categories == %d catalog keys; theme(s) %s complete; evidence ids resolve" % (
        n, len(cat["categories"]), ",".join(schema_themes))


# ------------------------------------------------------------------------------------------------ [l]
@check("[l] no-absolute-paths")
def c_l():
    fails, n = [], 0
    for p in all_files():
        n += 1
        try:
            txt = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        for pat in _ABS_PATTERNS:
            for m in pat.finditer(txt):
                line = txt.count("\n", 0, m.start()) + 1
                fails.append("%s:%d contains an absolute local path (%s)" % (rel(p), line, txt[m.start():m.start() + 24].replace("\n", " ")))
                break
    return fails, [], "no absolute local paths in %d shipped files" % n


# ------------------------------------------------------------------------------------------------ [m]
_DOC_PATH = re.compile(r"(?<![\w/.-])((?:[A-Za-z0-9_-]+/)+[A-Za-z0-9_.-]+\.(?:py|json|md|sh))\b")
_DOC_BARE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_-]+\.(?:py|sh))\b")
_EXTERNAL = ("src/", "public/", "tools/", "crawl/", "dist/", "node_modules/")


def python_doc_text(src):
    import ast
    import io
    import tokenize
    parts = []
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d:
                parts.append(d)
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            parts.append(tok.string)
    return "\n".join(parts)


@check("[m] entrypoints-docs")
def c_m():
    fails = []
    man = jload("registry.manifest.json")
    eps = man.get("entryPoints")
    if not eps:
        return ["manifest has no entryPoints"], [], ""
    flat = []

    def collect(o):
        if isinstance(o, str):
            flat.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(eps)
    files = [rel(p) for p in all_files()]
    for e in flat:
        if os.path.isabs(e) or ".." in e.replace("\\", "/").split("/") or e.startswith(("~", "./..")):
            fails.append("entryPoint %r is absolute or contains `..`" % e)
            continue
        target = os.path.normpath(os.path.join(ROOT, e))
        if not (target == ROOT or target.startswith(ROOT + os.sep)):
            fails.append("entryPoint %r resolves outside the package" % e)
        elif not os.path.exists(target):
            fails.append("entryPoint %r does not exist inside the package" % e)
    norm = [os.path.normpath(e) for e in flat]
    for f in files:
        if not any(f == e or f.startswith(e.rstrip("/") + os.sep) for e in norm):
            fails.append("shipped file %s is not covered by any entryPoint" % f)
    # every documented file must exist (docs, manifest, scripts' docstrings/comments)
    basenames = {os.path.basename(f) for f in files}
    docs = [p for p in all_files() if p.endswith((".md", ".py", ".json"))]
    for p in docs:
        txt = open(p, encoding="utf-8").read()
        if p.endswith(".py"):  # a script "documents" files in its docstrings and comments, not in string literals it manipulates
            txt = python_doc_text(txt)
        for m in _DOC_PATH.finditer(txt):
            d = m.group(1)
            if d.startswith("design-repo/"):
                d = d[len("design-repo/"):]
            if d.startswith(_EXTERNAL) or "*" in d or "<" in d:
                continue
            if not os.path.exists(os.path.join(ROOT, d)):
                fails.append("%s documents %s but it does not exist" % (rel(p), d))
        for m in _DOC_BARE.finditer(txt):
            if m.group(1) not in basenames and not re.search(r"(?:\w+/)" + re.escape(m.group(1)), txt):
                fails.append("%s mentions script %s but no such file is shipped" % (rel(p), m.group(1)))
    return fails, [], "%d entryPoints exist inside the package with no `..`, cover all %d files; documented files all exist" % (len(flat), len(files))


# ------------------------------------------------------------------------------------------------ [n]
@check("[n] version-note")
def c_n():
    fails = []
    man = jload("registry.manifest.json")
    note = man.get("versionFieldNote")
    if not isinstance(note, str) or len(note) < 60:
        return ["manifest.versionFieldNote missing or too short"], [], ""
    low = note.lower()
    for f in ("allowlistVersion", "repositoryVersion", "pageSpecVersion"):
        if f not in note:
            fails.append("versionFieldNote does not mention %s" % f)
        if f not in man:
            fails.append("manifest has no %s field" % f)
    if "machine" not in low or "documentation" not in low:
        fails.append("versionFieldNote must say which fields are machine-checked and which are documentation-only")
    if not re.search(r"allowlistVersion[^.;]*machine", note, re.I):
        fails.append("versionFieldNote must state allowlistVersion is machine-checked")
    if not re.search(r"(repositoryVersion|pageSpecVersion)[^.;]*documentation", note, re.I):
        fails.append("versionFieldNote must state repositoryVersion/pageSpecVersion are documentation-only")
    for f in ("allowlistVersion", "repositoryVersion", "pageSpecVersion"):
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(man.get(f, ""))):
            fails.append("%s is not semver: %r" % (f, man.get(f)))
    al = jload("tokens", "llm", "component-allowlist.json")
    if "phase" in (al.get("$description", "") + al.get("versionFieldNote", "")).lower():
        fails.append("component-allowlist.json still carries stale build-phase wording")
    if man.get("status") != "design-review-pending" or man.get("productionApproved") is not False:
        fails.append("manifest status must be design-review-pending with productionApproved false")
    return fails, [], "versionFieldNote separates machine-checked (allowlistVersion) from documentation-only (repositoryVersion, pageSpecVersion)"


# ------------------------------------------------------------------------------------------------ main
def main(argv):
    if "--emit-counts" in argv:
        c = compute_counts()
        print(json.dumps(c, indent=2))
        print(counts_block(c))
        return 0
    for run in CHECKS:
        run()
    npass = nfail = nwarn = 0
    for status, name, msg in RESULTS:
        print("%-4s %s%s" % (status, name, (" - " + msg) if msg else ""))
        npass += status == "PASS"
        nfail += status == "FAIL"
        nwarn += status == "WARN"
    checks_failed = len({n for s, n, m in RESULTS if s == "FAIL"})
    print("SUMMARY: %d/%d checks passed, %d failed, %d warning(s)" % (len(CHECKS) - checks_failed, len(CHECKS), checks_failed, nwarn))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
