# Changelog

`repositoryVersion` is a documentation-only marker (see `versionFieldNote` in `registry.manifest.json`). Counts below are
the values recomputed from disk when 1.0.0 was finalised; `extraction/verify_all.py` re-checks the manifest and README against disk.

## 1.0.0 - initial design-review build (status: design-review-pending, productionApproved: false)

Contents: 258 tokens (foundation 150, semantic 48, component 42, layout 18; the catalog lists the same 258), 9 primitive,
17 component and 23 section contracts (49 allowlist ids, `allowlistVersion` 1.0.0), 10 templates serving 15 routes 1:1,
20 compatibility-graph rules (17 error, 3 warn), 18 asset roles, a 522-entry citation ledger, a Draft-07 PageSpec schema, an
example PageSpec and a semantic validator.

Verification added in the final build pass
- `extraction/verify_all.py`: 14 checks (json parse, Draft-07 schema + example, schema regeneration drift, allowlist parity in both
  directions, allowlistVersion parity, manifest counts and README counts block recomputed from disk, route-template 1:1 and
  route admission over every route, template/graph/validator parity, citation resolution (line range + quote, CSS quote at
  charRange; a WARN when no source tree is beside the package), asset-role closure with a pinned-value check for the 11
  compliance-critical roles, token reference resolution, no absolute paths, entryPoints/documented-file existence, version note).
- `extraction/prove_drift.py`: injects each drift class into scratch copies and requires `verify_all.py` to fail on it.
- `schema/tests/adversarial_test.py`: controls for every template (auto-iterated) plus 45 rejected mutations, CLI robustness,
  a catalog/policy drift layer and the pinned-asset mutation. PageSpecs have no token-override field, so token misuse is tested
  at the catalog/policy layer only.

Fixes and additions in the final build pass
- New graph rule `CALLOUT_COUNT_PER_ROUTE` (with its implementation and mutations): pins the callout count of the seven routes on
  the shared solution templates, counted from each page's JSX (creator-economy 4, online-gaming 5, dating 3, digital-entertainment 3,
  esim 4, lms 4, merchant-of-record 5). Graph rule ids and validator `RULES` stay in parity.
- Validator: unparseable or missing input prints one `ERROR` line and exits 2 (no traceback); missing required nodes yield one
  aggregated `TEMPLATE_NODE_MATCH` message instead of a per-node cascade; duplicate messages are removed; oneOf schema errors
  report the closest branch's leaf error.
- Schema: local media paths may not contain `..` (schema regenerated with `extraction/build_pagespec_schema.py`).
- `tokens/llm/component-allowlist.json`: removed the stale build-phase wording from `$description` and `versionFieldNote`.
- `verify_all.py` check [g] run over every route found that the optional `bridge.section` node of `solution-impact` is admitted on
  only one of its two routes; that is intentional (instance-level `ROUTE_RESTRICTED_SECTIONS` rejects it on online-gaming), so the
  check only requires optional nodes to be admitted on at least one route of their template.

Evidence and limitations (see README): homepage copy exact from the user's saved page; five inner pages real text from the user's
saved copies; nine pages original AI-written copy; structure/layout/motion measured against live coda.co only for the homepage
(CLONE_SPEC.md), carried over from earlier build-agent reports for the 14 inner pages; copy-provenance citations are `inferred`.
The source has no reduced-motion handling, no dark theme and no shadows. Not for publication without the owner's licence review.
