#!/usr/bin/env python3
"""Adversarial tests for the PageSpec schema + semantic validator + drift checks.

Runs from the design-repo alone (root derived from this file's location; no sibling folders needed):
    python3 schema/tests/adversarial_test.py          exit 0 = every control passed and every mutation was rejected

Layers
  1. CONTROLS - the shipped example and synthesize_control(t) for EVERY template in templates.json (auto-iterated, so a
     future template is covered with no new code) must produce 0 errors. A validator that rejects everything is broken too.
  2. MUTATIONS - each mutated PageSpec must be REJECTED, and rejected by the rule the mutation targets (printed).
  3. CLI - unparseable input gives one clean error line and exit code 2, never a traceback.
  4. CATALOG / POLICY DRIFT INJECTION - PageSpecs have NO per-instance token or style override field (the schema
     rejects a `tokens` field, mutation 'per-instance tokens field'); styling is owned entirely by the section/component
     contracts (token-policy.json `overrides`, MASTER-GUIDE 3.21). So there is nothing at the PageSpec layer to mutate
     for token misuse; token safety is tested one layer down, by injecting drift into a scratch copy of the repo and
     asserting extraction/verify_all.py fails.
  5. PINNED ASSET POLICY - a complianceCritical asset role is changed to a DIFFERENT-BUT-VALID generationPolicy in a
     scratch copy; verify_all.py must fail (membership in the 4-value enum alone would not catch it).
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "schema"))
import semantic_validate as sv  # noqa: E402

FAILED = []


def load_example():
    with open(os.path.join(ROOT, "schema", "example.pagespec.json"), encoding="utf-8") as f:
        return json.load(f)


EX = load_example()
REPO = sv.load_repo(ROOT)
TEMPLATES = sorted(REPO["templates"])


def first(spec, t, n=0):
    return [i for i, x in enumerate(spec["nodes"]) if x["type"] == t][n]


def node_of(control_template, section):
    spec = sv.synthesize_control(control_template, ROOT)
    return copy.deepcopy(spec["nodes"][first(spec, section)])


def words(n):
    return " ".join("word%d" % i for i in range(n))


# ------------------------------------------------------------------------------------------- mutations
MUTS = []


def mut(name, expect):
    def deco(fn):
        MUTS.append((name, expect, fn))
        return fn
    return deco


@mut("wrong template enum", ["SCHEMA"])
def _(s):
    s["template"] = "solution-bogus"


@mut("route not served by template", ["TEMPLATE_SERVES_ROUTE"])
def _(s):
    s["route"] = "/pricing/"


@mut("invented node type (hero.banner)", ["SCHEMA"])
def _(s):
    s["nodes"][1]["type"] = "hero.banner"


@mut("invented section alias (callout-feature)", ["SCHEMA"])
def _(s):
    s["nodes"][7]["type"] = "callout-feature"


@mut("missing reducedMotionFallback", ["SCHEMA", "SEM-MOTION"])
def _(s):
    del s["nodes"][3]["motion"]["reducedMotionFallback"]


@mut("empty reducedMotionFallback", ["SCHEMA", "SEM-MOTION"])
def _(s):
    s["nodes"][3]["motion"]["reducedMotionFallback"] = "  "


@mut("missing motion", ["SCHEMA", "SEM-MOTION"])
def _(s):
    del s["nodes"][5]["motion"]


@mut("invented motion field (duration)", ["SCHEMA"])
def _(s):
    s["nodes"][5]["motion"]["duration"] = 900


@mut("wrong motion pattern for the section", ["SCHEMA", "SEM-MOTION"])
def _(s):
    s["nodes"][5]["motion"]["pattern"] = "marquee-scroll" if s["nodes"][5]["motion"]["pattern"] != "marquee-scroll" else "reveal-fade"


@mut("extra content field", ["SCHEMA"])
def _(s):
    s["nodes"][1]["content"]["subtitle"] = "not in the contract"


@mut("per-instance `tokens` field on a node", ["SCHEMA"])
def _(s):
    s["nodes"][1]["tokens"] = {"color.charcoal": "#ff0000"}


@mut("per-instance `tokens` field at page level", ["SCHEMA"])
def _(s):
    s["tokens"] = {"text.primary": "color.black"}


@mut("duplicate one-per-page section (hero)", ["ONE_HERO_PER_PAGE", "SECTION_CONTRACT_CONSTRAINTS"])
def _(s):
    s["nodes"].insert(2, copy.deepcopy(s["nodes"][1]))


@mut("adjacent benefits stacks", ["NO_ADJACENT_SAME_SECTION", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][3] = copy.deepcopy(s["nodes"][2])


@mut("third benefits stack (maxPerPage 2)", ["SECTION_CONTRACT_CONSTRAINTS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].insert(6, copy.deepcopy(s["nodes"][2]))


for _sec in ("faq.accordion", "spacer.footer-gap", "cta.pre-footer", "shell.footer", "shell.navbar"):
    def _mk(sec):
        @mut("removed mandatory section %s" % sec, ["TEMPLATE_NODE_MATCH"])
        def _(s):
            del s["nodes"][first(s, sec)]
    _mk(_sec)


@mut("reordered fixed node: navbar/hero swapped", ["NAVBAR_FIRST_FOOTER_LAST", "HERO_FOLLOWS_NAVBAR", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][0], s["nodes"][1] = s["nodes"][1], s["nodes"][0]


@mut("reordered fixed node: pre-footer moved before spacer", ["PRE_FOOTER_LAST_BEFORE_FOOTER", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][12], s["nodes"][13] = s["nodes"][13], s["nodes"][12]


@mut("reordered fixed node: pre-footer moved to the top of the body", ["PRE_FOOTER_LAST_BEFORE_FOOTER", "TEMPLATE_NODE_MATCH"])
def _(s):
    n = s["nodes"].pop(13)
    s["nodes"].insert(2, n)


@mut("template/node mismatch: home nodes under solution-standard", ["TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"] = sv.synthesize_control("home", ROOT)["nodes"]


@mut("template/node mismatch: solution-standard nodes under product-codapay", ["TEMPLATE_NODE_MATCH"])
def _(s):
    s["template"], s["route"] = "product-codapay", "/product/codapay/"


@mut("maxWords overflow on hero heading", ["SEM-WORDS"])
def _(s):
    s["nodes"][1]["content"]["heading"] = words(30)


@mut("maxWords overflow on a card body", ["SEM-WORDS"])
def _(s):
    s["nodes"][7]["content"]["body"] = words(120)


@mut("maxWords overflow on reducedMotionFallback", ["SEM-WORDS"])
def _(s):
    s["nodes"][5]["motion"]["reducedMotionFallback"] = words(60)


@mut("invented assetRole", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][7]["content"]["media"]["assetRole"] = "stock-photo"


@mut("assetRole valid globally but not allowed for this slot", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][7]["content"]["media"]["assetRole"] = "partner-logo"


@mut("remote URL in a media path", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][7]["content"]["media"]["assetRef"] = "https://cdn.example.com/x.webp"


@mut("protocol-relative // URL in a media path", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][7]["content"]["media"]["assetRef"] = "//cdn.example.com/x.webp"


@mut("path traversal in a media path", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][7]["content"]["media"]["assetRef"] = "/images/../../etc/passwd"


@mut("remote URL in a link href", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][7]["content"]["link"]["href"] = "https://coda.co/blog/"


@mut("route-restricted section: awards.recognition off the homepage", ["ROUTE_RESTRICTED_SECTIONS"])
def _(s):
    s["nodes"].insert(6, node_of("home", "awards.recognition"))


@mut("route-restricted section: tiles.page off /product/codapay/", ["ROUTE_RESTRICTED_SECTIONS"])
def _(s):
    s["nodes"].insert(6, node_of("product-codapay", "tiles.page"))


@mut("route-restricted section: table.payment-method off /pricing/", ["ROUTE_RESTRICTED_SECTIONS"])
def _(s):
    s["nodes"].insert(6, node_of("pricing", "table.payment-method"))


@mut("callout run too long (6 callouts)", ["CALLOUT_COUNT_PER_ROUTE", "TEMPLATE_NODE_MATCH", "SECTION_CONTRACT_CONSTRAINTS"])
def _(s):
    for _ in range(3):
        s["nodes"].insert(7, copy.deepcopy(s["nodes"][7]))


@mut("callout run too short (2 callouts)", ["CALLOUT_COUNT_PER_ROUTE", "TEMPLATE_NODE_MATCH"])
def _(s):
    del s["nodes"][7]


@mut("callout run mixes variants", ["CALLOUT_RUN_SINGLE_VARIANT", "TEMPLATE_NODE_MATCH", "VARIANT"])
def _(s):
    s["nodes"][8]["variant"] = "titled"


@mut("callouts not contiguous", ["CALLOUTS_CONTIGUOUS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].insert(8, node_of("solution-standard", "metrics.band"))


@mut("bridge moved away from the callout run", ["BRIDGE_BEFORE_CALLOUT_RUN", "TEMPLATE_NODE_MATCH"])
def _(s):
    b = s["nodes"].pop(6)
    s["nodes"].insert(4, b)


def _gaming_control():
    """A VALID online-gaming PageSpec: solution-impact, 5 callouts, no bridge (the real page)."""
    s = sv.synthesize_control("solution-impact", ROOT)
    s["route"] = "/industries/online-gaming-payments/"
    i = first(s, "callout.feature")
    s["nodes"].insert(i, copy.deepcopy(s["nodes"][i]))
    s["nodes"] = [n for n in s["nodes"] if n["type"] != "bridge.section"]
    return s


def _creator_control():
    s = sv.synthesize_control("solution-impact", ROOT)
    s["nodes"].insert(first(s, "callout.feature"), node_of("solution-standard", "bridge.section"))
    return s


CTRL_EXTRA = [("online-gaming solution-impact (5 callouts, no bridge)", _gaming_control),
              ("creator-economy solution-impact (4 callouts + bridge)", _creator_control)]
MUT_EXTRA = []


def extra(name, expect, base, fn):
    MUT_EXTRA.append((name, expect, base, fn))


def _bridge_on_gaming(s):
    s["nodes"].insert(first(s, "callout.feature"), node_of("solution-standard", "bridge.section"))


extra("solution-impact bridge.section on online-gaming", ["ROUTE_RESTRICTED_SECTIONS"], _gaming_control, _bridge_on_gaming)


def _gaming_four(s):
    del s["nodes"][first(s, "callout.feature")]


extra("online-gaming with 4 callouts (real page has 5)", ["CALLOUT_COUNT_PER_ROUTE"], _gaming_control, _gaming_four)


def _creator_five(s):
    i = first(s, "callout.feature")
    s["nodes"].insert(i, copy.deepcopy(s["nodes"][i]))


extra("creator-economy with 5 callouts (real page has 4)", ["CALLOUT_COUNT_PER_ROUTE"], _creator_control, _creator_five)


# ------------------------------------------------------------------------------------------- runner
def rejected_by(spec):
    errors, _ = sv.validate(spec, ROOT)
    return errors


def report(ok, tag, name, detail=""):
    print("%-8s %s%s" % (tag, name, (" <- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def run_controls():
    print("== controls (must produce 0 errors) ==")
    errs = rejected_by(copy.deepcopy(EX))
    report(not errs, "PASS" if not errs else "FAIL", "shipped example", "; ".join(errs[:2]))
    for t in TEMPLATES:
        errs = rejected_by(sv.synthesize_control(t, ROOT))
        report(not errs, "PASS" if not errs else "FAIL", "synthesize_control(%s)" % t, "; ".join(errs[:2]))
    for name, fn in CTRL_EXTRA:
        errs = rejected_by(fn())
        report(not errs, "PASS" if not errs else "FAIL", "control " + name, "; ".join(errs[:2]))


def run_mutations():
    print("== mutations (each must be REJECTED by the targeted rule) ==")
    cases = [(n, e, copy.deepcopy(EX), fn) for n, e, fn in MUTS] + [(n, e, b(), fn) for n, e, b, fn in MUT_EXTRA]
    for name, expect, base, fn in cases:
        fn(base)
        errs = rejected_by(base)
        hit = [e for e in errs if any(x in e for x in expect)]
        if not errs:
            report(False, "ACCEPTED", name, "the validator accepted a mutated PageSpec")
        elif not hit:
            report(False, "WRONGRULE", name, "rejected, but not by %s: %s" % (expect, errs[0][:140]))
        else:
            report(True, "REJECTED", name, hit[0][:150])


def run_cli():
    print("== validator CLI robustness ==")
    tmp = tempfile.mkdtemp()
    try:
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w") as f:
            f.write("{ not json")
        for label, path in (("unparseable JSON", bad), ("missing file", os.path.join(tmp, "nope.json"))):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "schema", "semantic_validate.py"), path], capture_output=True, text=True)
            clean = r.returncode == 2 and "Traceback" not in r.stderr + r.stdout and r.stdout.startswith("ERROR")
            report(clean, "PASS" if clean else "FAIL", "CLI " + label, "exit %d, %s" % (r.returncode, (r.stdout.strip() or r.stderr.strip())[:90]))
        spec = copy.deepcopy(EX)
        del spec["nodes"][first(spec, "faq.accordion")]
        errs = rejected_by(spec)
        readable = 1 <= len(errs) <= 3 and len(errs) == len(set(errs))
        report(readable, "PASS" if readable else "FAIL", "missing node gives a short de-duplicated message set", "%d message(s): %s" % (len(errs), errs[0][:90]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def scratch_copy():
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "design-repo")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    return tmp, dst


def verify_fails(dst, expect_check):
    r = subprocess.run([sys.executable, os.path.join(dst, "extraction", "verify_all.py")], capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith("FAIL") and expect_check in l]
    return r.returncode != 0 and bool(lines), (lines[0][:170] if lines else "verify_all did not fail on %s (exit %d)" % (expect_check, r.returncode))


def edit_json(path, fn):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def run_drift_layer():
    print("== catalog / policy drift injection + pinned asset policy (scratch copies; PageSpecs have no token field) ==")

    def policy_category(d):
        d["rawValueRestrictions"]["shadow"] = d["rawValueRestrictions"].pop("elevation")

    def dangling_ref(d):
        first_key = next(iter(d["tokens"]))
        d["tokens"][first_key] = {"$ref": "color.does-not-exist"}

    def drop_catalog_entry(d):
        d["categories"]["color"]["tokens"].pop()

    def unpin_role(d):
        # a DIFFERENT-BUT-VALID policy value on a complianceCritical role (may-generate-new is in the closed enum)
        r = next(x for x in d["roles"] if x["complianceCritical"])
        assert r["generationPolicy"] != "may-generate-new"
        r["generationPolicy"] = "may-generate-new"

    def unpin_font(d):
        r = next(x for x in d["roles"] if x["id"] == "brand-typeface-file")
        r["generationPolicy"] = "must-reuse-exact"

    cases = [
        ("policy category renamed to a label that is not a catalog key (elevation->shadow)", "tokens/llm/token-policy.json", policy_category, "[k]"),
        ("dangling $ref in a semantic token", "tokens/10-semantic/color.json", dangling_ref, "[k]"),
        ("catalog entry removed (count/ids drift)", "tokens/llm/token-catalog.json", drop_catalog_entry, "[f]"),
        ("PINNED complianceCritical role switched to may-generate-new (valid enum value)", "assets/asset-roles.json", unpin_role, "[j]"),
        ("PINNED role brand-typeface-file switched to must-reuse-exact (valid enum value)", "assets/asset-roles.json", unpin_font, "[j]"),
    ]
    for name, rel, fn, check in cases:
        tmp, dst = scratch_copy()
        try:
            edit_json(os.path.join(dst, *rel.split("/")), fn)
            ok, line = verify_fails(dst, check)
            report(ok, "CAUGHT" if ok else "MISSED", name, line)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    tmp, dst = scratch_copy()  # sanity: an unmodified scratch copy passes, so the failures above are due to the injections
    try:
        r = subprocess.run([sys.executable, os.path.join(dst, "extraction", "verify_all.py")], capture_output=True, text=True)
        report(r.returncode == 0, "PASS" if r.returncode == 0 else "FAIL", "unmodified scratch copy passes verify_all", r.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    run_controls()
    run_mutations()
    run_cli()
    run_drift_layer()
    print("== summary ==")
    n_mut = len(MUTS) + len(MUT_EXTRA)
    print("controls: %d templates + example + %d extra; mutations: %d; failures: %d" % (len(TEMPLATES), len(CTRL_EXTRA), n_mut, len(FAILED)))
    for f in FAILED:
        print("  FAILED:", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
