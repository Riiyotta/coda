#!/usr/bin/env python3
"""Semantic validator for Coda PageSpecs (everything JSON Schema cannot express).

Usage:  python3 schema/semantic_validate.py <pagespec.json>      (exit 1 when there are errors)
        python3 schema/semantic_validate.py --parity              (graph rule id <-> implementation parity)
        exit codes: 0 valid, 1 validation errors, 2 unreadable/unparseable input or bad usage
Import: from semantic_validate import validate, synthesize_control, graph_parity
        errors, warnings = validate(pagespec_dict, repo_root=None)

What it checks (schema errors and semantic errors are both reported by validate()):
  SCHEMA  jsonschema Draft7Validator against schema/pagespec.schema.json
  (a)(b)  TEMPLATE_NODE_MATCH: nodes vs the declared template's node list (order, required, repeatable+count,
          (section, variant) keyed contiguity, template-fixed variants)
  (c)     TEMPLATE_SERVES_ROUTE, ROUTE_RESTRICTED_SECTIONS
  (d)     every rule in compatibility/graph.json, with its severity and named exceptions (RULES dict below)
  (e)     SEM-MOTION: node.motion.reducedMotionFallback present, non-empty
  (f)     SEM-WORDS: per-instance maxWords / maxWordsTotal (word count is ALWAYS len(text.split()))
  (g)     SEM-ASSET: assetRole in the closed global enum and in the slot's allowed roles; local paths only
  (h)     SECTION_CONTRACT_CONSTRAINTS: onePerPage/maxPerPage/mustBeFirst/mustBeLast/noConsecutive/
          mustFollowNav/mustPrecedeFooter read from sections/*.json
Chrome-aware position semantics: mustBeFirst / mustBeLast on a shell.* section are absolute (first / last node);
on any other section they are relative to the page body (the nodes between shell.navbar and shell.footer).
mustFollowNav means index 1, mustPrecedeFooter means the node right before shell.footer.
"""
import json
import os
import re
import sys

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(SCHEMA_DIR)
LOCAL_PATH_RE = re.compile(r"^/(?!/)(?!.*\.\.)[A-Za-z0-9._~@%+()/-]+$")
MAX_FALLBACK_WORDS = 40


def wc(text):
    """The one word-count function used everywhere."""
    return len(text.split())


# --------------------------------------------------------------------------------------- repo loading
_CACHE = {}


def load_repo(repo_root=None):
    root = os.path.abspath(repo_root or DEFAULT_REPO)
    if root in _CACHE:
        return _CACHE[root]

    def j(*p):
        with open(os.path.join(root, *p)) as f:
            return json.load(f)
    import glob
    contracts = {}
    for f in sorted(glob.glob(os.path.join(root, "sections", "*.json"))):
        with open(f) as fh:
            d = json.load(fh)
        contracts[d["id"]] = d
    tpls = {t["id"]: t for t in j("templates", "templates.json")["templates"]}
    repo = {"root": root, "contracts": contracts, "templates": tpls,
            "graph": j("compatibility", "graph.json"), "roles": j("assets", "asset-roles.json"),
            "schema": j("schema", "pagespec.schema.json")}
    repo["role_set"] = set(repo["roles"]["assetRoleEnum"])
    repo["routes"] = sorted({r for t in tpls.values() for r in t["routes"]})
    _CACHE[root] = repo
    return repo


def variant_keys(contract):
    v = contract.get("variants")
    return list(v.keys()) if isinstance(v, dict) else list(v or [])


# --------------------------------------------------------------------------------------- graph rules
class Ctx:
    def __init__(self, spec, repo):
        self.spec, self.repo = spec, repo
        self.nodes = [n for n in spec.get("nodes", []) if isinstance(n, dict)]
        self.types = [n.get("type") for n in self.nodes]
        self.template_id = spec.get("template")
        self.tpl = repo["templates"].get(self.template_id)
        self.route = spec.get("route")

    def idx(self, t):
        return [i for i, x in enumerate(self.types) if x == t]


RULES = {}


def rule(fn):
    RULES[fn.__name__] = fn
    return fn


@rule
def TEMPLATE_SERVES_ROUTE(c, r):
    if c.tpl and c.route not in c.tpl["routes"]:
        return [f"route {c.route!r} is not served by template {c.template_id!r} (serves {c.tpl['routes']})"]
    return []


@rule
def TEMPLATE_NODE_MATCH(c, r):
    if not c.tpl:
        return [f"unknown template {c.template_id!r}"]
    msgs, pos, missing = [], 0, []
    for tn in c.tpl["nodes"]:
        sec = tn["section"]
        start = pos
        while pos < len(c.nodes) and c.types[pos] == sec and (tn["repeatable"] or pos == start):
            pos += 1
        cnt = pos - start
        if cnt == 0:
            if tn["required"]:
                if not missing:
                    missing.append((pos, c.types[pos] if pos < len(c.types) else "end of nodes"))
                missing.append(sec)
            continue
        if tn["repeatable"]:
            lo, hi = (tn.get("count") or {}).get("min", 1), (tn.get("count") or {}).get("max", 10 ** 6)
            if cnt < lo or cnt > hi:
                msgs.append(f"node {sec!r} repeated {cnt}x, template {c.template_id!r} allows {lo}-{hi}")
        if tn.get("variant"):
            for n in c.nodes[start:pos]:
                if n.get("variant") != tn["variant"]:
                    msgs.append(f"node {sec!r} variant {n.get('variant')!r} must be {tn['variant']!r} in template {c.template_id!r}")
    if missing:  # ONE message for all missing required nodes (no per-node cascade)
        (mp, mf), names = missing[0], missing[1:]
        msgs.insert(0, f"required template node(s) missing or out of order: {', '.join(map(repr, names))} "
                       f"(first mismatch at position {mp}, found {mf!r}; template {c.template_id!r})")
    if pos < len(c.nodes):  # one readable message instead of one per leftover node
        rest = [f"{c.types[i]!r}@{i}" for i in range(pos, len(c.nodes))]
        msgs.append(f"{len(rest)} extra or out-of-order node(s) not allowed by template {c.template_id!r}, starting at index {pos}: "
                    + ", ".join(rest[:6]) + (" ..." if len(rest) > 6 else ""))
    return msgs


@rule
def ONE_HERO_PER_PAGE(c, r):
    n = c.types.count("hero.main")
    return [] if n == 1 else [f"expected exactly one hero.main, found {n}"]


@rule
def NAVBAR_FIRST_FOOTER_LAST(c, r):
    m = []
    for s, where, want in (("shell.navbar", "first", 0), ("shell.footer", "last", len(c.types) - 1)):
        n = c.types.count(s)
        if n != 1:
            m.append(f"{s} must appear exactly once (found {n})")
        elif c.types.index(s) != want:
            m.append(f"{s} must be the {where} node (found at index {c.types.index(s)})")
    return m


@rule
def HERO_FOLLOWS_NAVBAR(c, r):
    h, n = c.idx("hero.main"), c.idx("shell.navbar")
    if h and n and h[0] != n[0] + 1:
        return [f"hero.main (index {h[0]}) must immediately follow shell.navbar (index {n[0]})"]
    return []


@rule
def PRE_FOOTER_LAST_BEFORE_FOOTER(c, r):
    if c.types.count("cta.pre-footer") != 1:
        return [f"cta.pre-footer must appear exactly once (found {c.types.count('cta.pre-footer')})"]
    if len(c.types) < 2 or c.types[-2] != "cta.pre-footer":
        return ["cta.pre-footer must be the node immediately before shell.footer"]
    return []


@rule
def NO_ADJACENT_SAME_SECTION(c, r):
    ok = {e["section"] for e in r.get("exceptions", []) if "section" in e}
    return [f"{c.types[i]!r} appears twice in a row at index {i - 1},{i}" for i in range(1, len(c.types))
            if c.types[i] == c.types[i - 1] and c.types[i] not in ok]


@rule
def FAQ_FOLLOWED_BY_SPACER(c, r):
    return [f"faq.accordion at index {i} must be followed by spacer.footer-gap" for i in c.idx("faq.accordion")
            if c.types[i + 1:i + 2] != ["spacer.footer-gap"]]


@rule
def SPACER_BEFORE_PRE_FOOTER(c, r):
    m = []
    for i in c.idx("spacer.footer-gap"):
        if c.types[i + 1:i + 2] != ["cta.pre-footer"]:
            m.append(f"spacer.footer-gap at index {i} must be immediately before cta.pre-footer")
        if c.types[i - 1:i] != ["faq.accordion"]:
            m.append(f"spacer.footer-gap at index {i} must immediately follow faq.accordion")
    return m


@rule
def FAQ_PRESENT_ON_CONTENT_PAGES(c, r):
    return [] if ("faq.accordion" in c.types and "spacer.footer-gap" in c.types) else \
        ["page has no faq.accordion + spacer.footer-gap"]


@rule
def PRICE_STACK_BEFORE_PRODUCTS_HIGHLIGHT(c, r):
    return [f"products.highlight at index {i} must immediately follow pricing.price-stack"
            for i in c.idx("products.highlight") if c.types[i - 1:i] != ["pricing.price-stack"]]


@rule
def PRICE_STACK_AFTER_CAROUSEL(c, r):
    return [f"pricing.price-stack at index {i} should immediately follow carousel.cards"
            for i in c.idx("pricing.price-stack") if c.types[i - 1:i] != ["carousel.cards"]]


@rule
def BRIDGE_BEFORE_CALLOUT_RUN(c, r):
    return [f"bridge.section at index {i} must be immediately before the callout.feature run"
            for i in c.idx("bridge.section") if c.types[i + 1:i + 2] != ["callout.feature"]]


@rule
def CALLOUTS_CONTIGUOUS(c, r):
    ix = c.idx("callout.feature")
    return [] if not ix or ix == list(range(ix[0], ix[-1] + 1)) else \
        [f"callout.feature nodes must be one contiguous run (indices {ix})"]


@rule
def CALLOUT_COUNT_PER_ROUTE(c, r):
    want = r.get("perRoute", {}).get(c.route)
    n = c.types.count("callout.feature")
    if want is not None and n != want:
        return [f"route {c.route!r} has {n} callout.feature nodes; the real page has exactly {want}"]
    return []


@rule
def CALLOUT_RUN_SINGLE_VARIANT(c, r):
    vs = {n.get("variant") for n in c.nodes if n.get("type") == "callout.feature"}
    return [] if len(vs) <= 1 else [f"callout.feature nodes mix variants {sorted(map(str, vs))}"]


@rule
def ISOLATED_CALLOUT_AFTER_CALLOUT_RUN(c, r):
    return [f"callout.isolated at index {i} must immediately follow a callout.feature"
            for i in c.idx("callout.isolated") if c.types[i - 1:i] != ["callout.feature"]]


@rule
def ROUTE_RESTRICTED_SECTIONS(c, r):
    m = []
    for t in sorted(set(x for x in c.types if x)):
        allowed = r.get("restrictions", {}).get(t)
        if allowed is None and t in c.repo["contracts"]:
            allowed = c.repo["contracts"][t].get("usedOn")
        if allowed is not None and c.route not in allowed:
            m.append(f"section {t!r} is not allowed on route {c.route!r} (allowed: {allowed})")
    return m


@rule
def SECTION_CONTRACT_CONSTRAINTS(c, r):
    m = []
    last = len(c.types) - 1
    body = [i for i, t in enumerate(c.types) if not str(t).startswith("shell.")]
    for t in sorted(set(x for x in c.types if x in c.repo["contracts"])):
        k = c.repo["contracts"][t].get("constraints", {})
        ix, shell = c.idx(t), str(t).startswith("shell.")
        if k.get("onePerPage") and len(ix) > 1:
            m.append(f"{t}: onePerPage violated ({len(ix)} instances)")
        if k.get("maxPerPage") is not None and len(ix) > k["maxPerPage"]:
            m.append(f"{t}: maxPerPage {k['maxPerPage']} exceeded ({len(ix)} instances)")
        if k.get("mustBeFirst"):
            want = 0 if shell else (body[0] if body else 0)
            if ix and ix[0] != want:
                m.append(f"{t}: mustBeFirst violated (index {ix[0]}, expected {want})")
        if k.get("mustBeLast"):
            want = last if shell else (body[-1] if body else last)
            if ix and ix[-1] != want:
                m.append(f"{t}: mustBeLast violated (index {ix[-1]}, expected {want})")
        if k.get("mustFollowNav") and ix and "shell.navbar" in c.types and (c.types[:1] != ["shell.navbar"] or ix[0] != 1):
            m.append(f"{t}: mustFollowNav violated (index {ix[0]})")
        if k.get("mustPrecedeFooter") and ix and ix[-1] != last - 1:
            m.append(f"{t}: mustPrecedeFooter violated (index {ix[-1]}, footer at {last})")
        if k.get("noConsecutive") and any(b - a == 1 for a, b in zip(ix, ix[1:])):
            m.append(f"{t}: noConsecutive violated")
    return m


@rule
def VARIANT_MATCHES_ROUTE(c, r):
    m = []
    for i, n in enumerate(c.nodes):
        v, ct = n.get("variant"), c.repo["contracts"].get(n.get("type"))
        if v is None or not ct:
            continue
        if v not in variant_keys(ct):
            m.append(f"node {i} {n.get('type')!r}: variant {v!r} is not one of {variant_keys(ct)}")
            continue
        entry = ct["variants"][v] if isinstance(ct["variants"], dict) else None
        if isinstance(entry, dict) and entry.get("routes") and c.route not in entry["routes"]:
            m.append(f"node {i} {n.get('type')!r}: variant {v!r} is evidenced only on {entry['routes']}, not {c.route!r}")
    return m


def graph_parity(repo_root=None):
    """(graph ids without implementation, implemented ids missing from graph)."""
    ids = [x["id"] for x in load_repo(repo_root)["graph"]["rules"]]
    return sorted(set(ids) - set(RULES)), sorted(set(RULES) - set(ids))


# --------------------------------------------------------------------------------------- content checks
def _walk(inst, sch, path, repo, out, tot):
    """Walk an instance next to its section-contract content schema: word budgets, roles, paths."""
    if not isinstance(sch, dict):
        return
    if isinstance(inst, str):
        if "maxWords" in sch:
            n = wc(inst)
            tot[0] += n
            if n > sch["maxWords"]:
                out.append(f"SEM-WORDS {path}: {n} words exceeds maxWords {sch['maxWords']}")
        if sch.get("format") == "local-asset-path" and not LOCAL_PATH_RE.match(inst):
            out.append(f"SEM-ASSET {path}: {inst!r} is not a local asset path (remote URLs/schemes are forbidden)")
        if sch.get("format") == "route-or-inert-hash" and inst != "#" and inst not in repo["routes"]:
            out.append(f"SEM-ASSET {path}: {inst!r} must be '#' or one of the 15 routes")
        en = sch.get("enum")
        if en and set(en) <= repo["role_set"]:
            if inst not in repo["role_set"]:
                out.append(f"SEM-ASSET {path}: assetRole {inst!r} is not in the closed assetRole enum")
            elif inst not in en:
                out.append(f"SEM-ASSET {path}: assetRole {inst!r} not allowed in this slot (allowed: {en})")
    elif isinstance(inst, dict) and "properties" in sch:
        for k, v in inst.items():
            if k in sch["properties"]:
                _walk(v, sch["properties"][k], f"{path}.{k}", repo, out, tot)
        # role/path coupling: video roles live under /video/, everything else does not
        role = inst.get("assetRole")
        for ref in ("assetRef", "mobileAssetRef"):
            p = inst.get(ref)
            if isinstance(role, str) and isinstance(p, str) and p.startswith("/"):
                isvid = role in ("hero-video", "promo-video")
                if isvid != p.startswith("/video/"):
                    out.append(f"SEM-ASSET {path}.{ref}: role {role!r} does not match path {p!r}")
    elif isinstance(inst, list) and "items" in sch:
        for i, x in enumerate(inst):
            _walk(x, sch["items"], f"{path}[{i}]", repo, out, tot)


def content_checks(spec, repo):
    errs = []
    for i, n in enumerate(spec.get("nodes", [])):
        if not isinstance(n, dict):
            continue
        t = n.get("type")
        ct = repo["contracts"].get(t)
        m = n.get("motion")
        if not (isinstance(m, dict) and isinstance(m.get("reducedMotionFallback"), str) and m["reducedMotionFallback"].strip()):
            errs.append(f"SEM-MOTION nodes[{i}] {t}: reducedMotionFallback is required (a design rule: the source site has no reduced-motion handling)")
        elif wc(m["reducedMotionFallback"]) > MAX_FALLBACK_WORDS:
            errs.append(f"SEM-WORDS nodes[{i}].motion.reducedMotionFallback: {wc(m['reducedMotionFallback'])} words exceeds {MAX_FALLBACK_WORDS}")
        if ct and isinstance(m, dict) and m.get("pattern") not in (None, ct["motion"]["pattern"]):
            errs.append(f"SEM-MOTION nodes[{i}] {t}: motion.pattern {m.get('pattern')!r} must be {ct['motion']['pattern']!r}")
        if ct and isinstance(n.get("content"), dict):
            out, tot = [], [0]
            _walk(n["content"], ct["content"], f"nodes[{i}].content", repo, out, tot)
            cap = ct["content"].get("maxWordsTotal")
            if cap is not None and tot[0] > cap:
                out.append(f"SEM-WORDS nodes[{i}].content: {tot[0]} total words exceeds maxWordsTotal {cap}")
            errs.extend(f"{e} [{t}]" for e in out)
    return errs


# --------------------------------------------------------------------------------------- public API
def validate(pagespec, repo_root=None):
    """Return (errors, warnings). Schema errors and semantic errors are both included in `errors`."""
    from jsonschema import Draft7Validator
    repo = load_repo(repo_root)
    errors, warnings = [], []
    if not isinstance(pagespec, dict):
        return ["SCHEMA: PageSpec must be a JSON object"], []
    from jsonschema.exceptions import best_match
    for e in sorted(Draft7Validator(repo["schema"]).iter_errors(pagespec), key=lambda e: list(map(str, e.path))):
        while e.context:  # oneOf/anyOf: report a leaf error from the branch that is closest to matching
            groups = {}
            for sub in e.context:
                groups.setdefault(sub.relative_schema_path[0], []).append(sub)
            e = best_match(min(groups.values(), key=len)) or e.context[0]
        loc = "/".join(map(str, e.absolute_path)) or "<root>"
        errors.append(f"SCHEMA {loc}: {e.message[:240]}")
    if not isinstance(pagespec.get("nodes"), list):
        return errors, warnings
    c = Ctx(pagespec, repo)
    for r in repo["graph"]["rules"]:
        fn = RULES.get(r["id"])
        if fn is None:
            errors.append(f"GRAPH rule {r['id']} has no implementation")
            continue
        if any(e.get("template") == c.template_id for e in r.get("exceptions", [])):
            continue
        for msg in fn(c, r):
            (errors if r["severity"] == "error" else warnings).append(f"[{r['id']}] {msg}")
    errors.extend(content_checks(pagespec, repo))
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


# --------------------------------------------------------------------------------------- control synthesizer
def _sample(sch, key=""):
    if "enum" in sch:
        return sch["enum"][0]
    t = sch.get("type")
    if t == "string":
        if sch.get("format") == "local-asset-path":
            return "/images/control-asset.webp"
        if sch.get("format") == "route-or-inert-hash":
            return "#"
        return " ".join(["Sample", "text"][:max(1, min(2, sch.get("maxWords", 2)))])
    if t == "array":
        return [_sample(sch["items"]) for _ in range(sch.get("minItems", 0))]
    if t == "object":
        return _sample_obj(sch)
    if t in ("integer", "number"):
        return 0
    if t == "boolean":
        return False
    raise ValueError(f"cannot synthesize {sch}")


def _sample_obj(sch):
    req = list(sch.get("required", []))
    if "oneOf" in sch and not req:
        pass
    if "oneOf" in sch:
        req = list(dict.fromkeys(req + sch["oneOf"][0]["required"]))
    o = {k: _sample(sch["properties"][k], k) for k in req}
    # coherent role/path pairs: a video role needs a /video/ path
    role = o.get("assetRole")
    for ref in ("assetRef", "mobileAssetRef"):
        if role in ("hero-video", "promo-video") and ref in o:
            o[ref] = "/video/control-asset.mp4"
    return o


def synthesize_control(template_id, repo_root=None):
    """Minimal valid PageSpec for a template, generated from its node list + each section contract's
    required fields (required nodes only, repeatable nodes at their minimum count)."""
    repo = load_repo(repo_root)
    tpl = repo["templates"][template_id]
    route = tpl["routes"][0]
    nodes = []
    for tn in tpl["nodes"]:
        if not tn["required"]:
            continue
        ct = repo["contracts"][tn["section"]]
        reps = (tn.get("count") or {}).get("min", 1) if tn["repeatable"] else 1
        if tn["repeatable"]:  # a per-route callout count pinned by the graph wins over the template's range
            pinned = next((x.get("perRoute", {}).get(route) for x in repo["graph"]["rules"] if x["id"] == "CALLOUT_COUNT_PER_ROUTE"), None)
            if pinned is not None and tn["section"] == "callout.feature":
                reps = pinned
        vk = variant_keys(ct)
        variant = tn.get("variant")
        if variant is None and len(vk) > 1 and not tn["section"].startswith("shell."):
            v = ct["variants"]
            variant = next((k for k in vk if isinstance(v, dict) and isinstance(v[k], dict) and route in v[k].get("routes", [])), vk[0])
        for _ in range(reps):
            n = {"type": tn["section"]}
            if variant:
                n["variant"] = variant
            n["content"] = _sample_obj(ct["content"])
            n["motion"] = {"pattern": ct["motion"]["pattern"],
                           "reducedMotionFallback": "Render the final state with no animation."}
            nodes.append(n)
    return {"pageSpecVersion": "1.0.0", "template": template_id, "route": route, "nodes": nodes}


def main(argv):
    if "--parity" in argv:
        a, b = graph_parity()
        print("graph ids without implementation:", a)
        print("implemented ids missing from graph:", b)
        return 1 if (a or b) else 0
    paths = [a for a in argv if not a.startswith("--")]
    if len(paths) != 1:
        print(__doc__)
        return 2
    try:
        with open(paths[0], encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:  # unreadable or unparseable input: one clean line, no traceback
        print(f"ERROR cannot read PageSpec {paths[0]!r}: {type(e).__name__}: {e}")
        return 2
    errors, warnings = validate(spec)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
