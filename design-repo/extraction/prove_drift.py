#!/usr/bin/env python3
"""prove_drift.py - proves that extraction/verify_all.py actually FAILS on drift (a check that has never been seen to
fail on bad input may not be checking anything). Self-contained: root derived from this file, works with no sibling folders.

    python3 extraction/prove_drift.py        exit 0 only if (1) the baseline scratch copy passes, (2) every injected drift is
                                             caught by the intended check, and (3) the real repo passes verify_all.py

Method: copy the repo to a temp dir, add a tiny synthetic sibling source tree (so citation checks are exercised even when the
real source project is absent), inject ONE drift per scratch copy, run that copy's own verify_all.py and require a FAIL line
from the intended check. When the real source project sits beside this folder, real citations are also corrupted (via
read-only symlinks of the real src/ and public/ into the scratch tree).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_SRC_ROOT = os.path.dirname(ROOT)
ABS_PROBE = "/" + "Users" + "/someone/project/file.txt"  # built by concatenation so this file itself holds no absolute path

PROBE_JSX = "line one\nline two has the quote\nline three\n"
PROBE_CSS = "a{color:red}.probe-quote{margin:0}b{color:blue}\n"
CSS_QUOTE = ".probe-quote{margin:0}"


def jedit(dst, rel, fn):
    p = os.path.join(dst, *rel.split("/"))
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def tedit(dst, rel, fn):
    p = os.path.join(dst, *rel.split("/"))
    with open(p, encoding="utf-8") as f:
        t = f.read()
    with open(p, "w", encoding="utf-8") as f:
        f.write(fn(t))


def add_probe_citations(d):
    d["measuredFrom"].extend([
        {"id": "probe-jsx", "source": "src/probe.jsx:2-3", "quote": "line two has the quote"},
        {"id": "probe-css", "source": "public/styles/probe.css:1-1", "charRange": [PROBE_CSS.index(CSS_QUOTE), PROBE_CSS.index(CSS_QUOTE) + len(CSS_QUOTE)], "quote": CSS_QUOTE}])


_CIT = re.compile(r"^[\w./ -]+\.(?:jsx|js|css|json|md|html|py):\d+(?:-\d+)?$")
SELF_CIT = "design-repo/README.md:1-1"


def neutralize(dst):
    """Synthetic-source mode only: repoint every real source citation at this package's own README so that the ONLY
    source-tree citations left are the probes below (the synthetic tree cannot hold the real project's files)."""
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("source"), str) and _CIT.match(o["source"]) and not o["source"].startswith(("src/probe", "public/styles/probe")):
                o["source"] = SELF_CIT
                o.pop("quote", None)
                o.pop("charRange", None)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str) and _CIT.match(v):
                    o[i] = SELF_CIT
                else:
                    walk(v)
    for d, _, files in os.walk(dst):
        for f in files:
            if f.endswith(".json"):
                p = os.path.join(d, f)
                with open(p, encoding="utf-8") as fh:
                    j = json.load(fh)
                before = json.dumps(j, sort_keys=True)
                walk(j)
                if json.dumps(j, sort_keys=True) != before:  # untouched files (e.g. the generated schema) keep their bytes
                    with open(p, "w", encoding="utf-8") as fh:
                        json.dump(j, fh, indent=2, ensure_ascii=False)


def scratch(real_sibling=False):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "design-repo")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    with open(os.path.join(tmp, "package.json"), "w") as f:
        f.write("{}")
    if real_sibling:
        for name in ("src", "public", "CLONE_SPEC.md", "index.html"):
            os.symlink(os.path.join(REAL_SRC_ROOT, name), os.path.join(tmp, name))
    else:
        os.makedirs(os.path.join(tmp, "src"))
        os.makedirs(os.path.join(tmp, "public", "styles"))
        with open(os.path.join(tmp, "src", "probe.jsx"), "w") as f:
            f.write(PROBE_JSX)
        with open(os.path.join(tmp, "public", "styles", "probe.css"), "w") as f:
            f.write(PROBE_CSS)
        neutralize(dst)
        jedit(dst, "primitives/primitive-button.json", add_probe_citations)
    return tmp, dst


def run_verify(dst):
    r = subprocess.run([sys.executable, os.path.join(dst, "extraction", "verify_all.py")], capture_output=True, text=True)
    return r.returncode, r.stdout


def first_real_citation(dst, ext, want_quote=True):
    """(rel json file, index in measuredFrom) of a real JSX/JS citation carrying a quote."""
    for sub in ("primitives", "components", "sections"):
        for fn in sorted(os.listdir(os.path.join(dst, sub))):
            with open(os.path.join(dst, sub, fn), encoding="utf-8") as f:
                d = json.load(f)
            for i, c in enumerate(d.get("measuredFrom", [])):
                if isinstance(c, dict) and c.get("source", "").split(":")[0].endswith(ext) and c.get("quote"):
                    return "%s/%s" % (sub, fn), i
    raise SystemExit("no real citation found")


def set_measured(idx_fn):
    def apply(d):
        idx_fn(d["measuredFrom"])
    return apply


# each case: (label, expected check tag, needs_real_sibling, injector(dst))
def cases():
    out = []

    def phantom(dst):
        jedit(dst, "tokens/llm/component-allowlist.json", lambda d: d["components"].append("component.ghost-phantom"))
    out.append(("(i) phantom allowlist id", "[d]", False, phantom))

    def orphan(dst):
        shutil.copy(os.path.join(dst, "components", "component-media.json"), os.path.join(dst, "components", "component-orphan-extra.json"))
        jedit(dst, "components/component-orphan-extra.json", lambda d: d.update({"id": "component.orphan-extra"}))
    out.append(("(ii) orphan contract (no allowlist entry)", "[d]", False, orphan))

    def oor(dst):
        jedit(dst, "primitives/primitive-button.json", set_measured(lambda m: m[-2].update({"source": "src/probe.jsx:2-99"})))
    out.append(("(iii) out-of-range citation (synthetic source)", "[i]", False, oor))

    def wrongq(dst):
        jedit(dst, "primitives/primitive-button.json", set_measured(lambda m: m[-2].update({"quote": "text that is not on those lines"})))
    out.append(("(iv) in-range citation, wrong quote (synthetic source)", "[i]", False, wrongq))

    def css_shift(dst):
        jedit(dst, "primitives/primitive-button.json", set_measured(lambda m: m[-1].update({"charRange": [30, 30 + len(CSS_QUOTE) - 4]})))
    out.append(("(iv-css) CSS citation whose charRange no longer holds the quote", "[i]", False, css_shift))

    def real_oor(dst):
        f, i = first_real_citation(dst, ".jsx")
        jedit(dst, f, set_measured(lambda m: m[i].update({"source": m[i]["source"].split(":")[0] + ":99998-99999"})))
    out.append(("(iii-real) out-of-range citation on a REAL source file", "[i]", True, real_oor))

    def real_wrongq(dst):
        f, i = first_real_citation(dst, ".jsx")
        jedit(dst, f, set_measured(lambda m: m[i].update({"quote": "this exact text is not in that file"})))
    out.append(("(iv-real) in-range but wrong quote on a REAL source file", "[i]", True, real_wrongq))

    def count(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["counts"].update({"sections": d["counts"]["sections"] + 1}))
    out.append(("(v) wrong manifest count (sections +1)", "[f]", False, count))

    def tokcount(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["counts"]["tokens"].update({"semantic": 1}))
    out.append(("(v-b) wrong manifest token-tier count", "[f]", False, tokcount))

    def ver(dst):
        jedit(dst, "registry.manifest.json", lambda d: d.update({"allowlistVersion": "9.9.9"}))
    out.append(("(vi) wrong allowlistVersion in manifest", "[e]", False, ver))

    def abspath(dst):
        tedit(dst, "README.md", lambda t: t + "\nSee " + ABS_PROBE + "\n")
    out.append(("(vii) absolute path string in README", "[l]", False, abspath))

    def unpin(dst):
        def f(d):
            r = next(x for x in d["roles"] if x["complianceCritical"])
            r["generationPolicy"] = "may-generate-new"  # valid enum member, wrong for a pinned role
        jedit(dst, "assets/asset-roles.json", f)
    out.append(("(viii) compliance-critical role set to a different-but-valid policy", "[j]", False, unpin))

    def entry(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["entryPoints"]["docs"].append("../CLONE_SPEC.md"))
    out.append(("(ix) entryPoints entry with ../", "[m]", False, entry))

    def routemap(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["routeTemplateMap"].update({"/pricing/": "home"}))
    out.append(("(x) route mapped to the wrong template in manifest", "[g]", False, routemap))

    def route_dup(dst):
        def f(d):
            t = {x["id"]: x for x in d["templates"]}
            t["home"]["routes"].append("/pricing/")
        jedit(dst, "templates/templates.json", f)
    out.append(("(xi) route served by two templates (not 1:1)", "[g]", False, route_dup))

    def graph_ghost(dst):
        jedit(dst, "compatibility/graph.json", lambda d: d["rules"].append({"id": "GHOST_RULE", "severity": "error", "description": "x", "exceptions": []}))
    out.append(("(xii) graph rule id with no validator implementation", "[h]", False, graph_ghost))

    def docs(dst):
        tedit(dst, "README.md", lambda t: t + "\nRun `extraction/not_built_script.py` to regenerate things.\n")
    out.append(("(xiii) README documents a script that does not exist", "[m]", False, docs))

    def note(dst):
        jedit(dst, "registry.manifest.json", lambda d: d.pop("versionFieldNote"))
    out.append(("(xiv) versionFieldNote removed", "[n]", False, note))

    def badrole(dst):
        jedit(dst, "sections/callout-feature.json", lambda d: d.__setitem__("probeRole", {"assetRole": "stock-photo"}))
    out.append(("(xv) unlisted assetRole used in a contract", "[j]", False, badrole))

    def readme_count(dst):
        tedit(dst, "README.md", lambda t: t.replace("Primitives 9", "Primitives 8", 1))
    out.append(("(xvi) README counts block edited by hand", "[f]", False, readme_count))
    def colour(dst):
        jedit(dst, "tokens/00-foundation/color.json", lambda d: d["tokens"]["color.charcoal"].update({"rgb": [33, 32, 32]}))
    out.append(("(xvii-real) foundation colour value not declared in the real stylesheet", "[k]", True, colour))
    return out


def main():
    results, bad = [], 0
    tmp, dst = scratch()
    try:
        rc, out = run_verify(dst)
        ok = rc == 0 and "PASS [i]" in out
        print("%-7s baseline scratch copy (synthetic source tree) passes verify_all: %s" % ("OK" if ok else "BROKEN", out.strip().splitlines()[-1]))
        bad += not ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    real_present = os.path.isdir(os.path.join(REAL_SRC_ROOT, "src")) and os.path.isfile(os.path.join(REAL_SRC_ROOT, "package.json"))
    for label, tag, needs_real, inject in cases():
        if needs_real and not real_present:
            print("SKIPPED %s (real source project not beside this folder)" % label)
            continue
        tmp, dst = scratch(real_sibling=needs_real)
        try:
            if needs_real:
                shutil.copy(os.path.join(REAL_SRC_ROOT, "package.json"), os.path.join(tmp, "package.json"))
                # real citations resolve against the real tree through symlinks; unmodified scratch must pass first
                rc0, out0 = run_verify(dst)
                if rc0 != 0:
                    print("BROKEN  %s: unmodified real-sibling scratch does not pass:\n%s" % (label, out0))
                    bad += 1
                    continue
            inject(dst)
            rc, out = run_verify(dst)
            lines = [l for l in out.splitlines() if l.startswith("FAIL") and tag in l]
            caught = rc != 0 and bool(lines)
            bad += not caught
            print("%-7s %s\n          -> %s" % ("CAUGHT" if caught else "MISSED", label, lines[0][:175] if lines else "verify_all exit %d, no FAIL line for %s" % (rc, tag)))
            results.append((label, caught))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    rc, out = run_verify(ROOT)
    print("%-7s the REAL repo still passes verify_all: %s" % ("OK" if rc == 0 else "FAILED", out.strip().splitlines()[-1]))
    bad += rc != 0
    print("SUMMARY: %d/%d injected drifts caught; baseline + real repo %s" % (sum(c for _, c in results), len(results), "pass" if not bad else "-- PROBLEMS, see above"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
