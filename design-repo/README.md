# Coda clone design repository

An AI-ready design repository extracted from a Vite + React clone of coda.co (15 routes): design tokens, primitive /
component / section contracts, page templates, a compatibility graph, a PageSpec JSON Schema with a semantic validator,
and the scripts that keep all of it honest. Status: **design-review-pending** (`productionApproved: false`). It is a
specification for generating pages in this site's style, not a component library.

## Counts (recomputed from disk by `extraction/verify_all.py`; that script fails if this block or the manifest drifts)

<!-- counts:begin -->
- Tokens: 258 total (foundation 150, semantic 48, component 42, layout 18); catalog entries: 258
- Primitives 9, components 17, sections 23
- Templates 10, routes 15 (1:1), graph rules 20, asset roles 18, ledger citations 522
<!-- counts:end -->

Routes to templates (each route is served by exactly one template): `/` -> home; `/pricing/` -> pricing;
`/product/codapay/` -> product-codapay; `/product/coda-links/` -> product-links; `/product/coda-webstore/` -> product-webstore;
`/product/distribution/` -> product-distribution; `/product/coda-consumer-platforms/` -> product-consumer-platforms;
`/product/coda-giftcloud/` -> product-giftcloud; creator-economy and online-gaming -> solution-impact; dating-app,
digital-entertainment, esim-digital-utility, learning-management-system and `/use-case/merchant-of-record/` -> solution-standard.
The machine-readable map is `routeTemplateMap` in `registry.manifest.json`.

## Folder map

| Path | What it holds |
| --- | --- |
| `registry.manifest.json` | status, versions (+ which are machine-checked), counts, route map, scope/constraints, entry points |
| `tokens/00-foundation/`, `10-semantic/`, `20-component/`, `30-layout/`, `themes/` | token tiers; ids are dotted (`color.charcoal`, `text.primary`, `component.themed-block.dark`); one theme, `light` |
| `tokens/llm/` | `token-catalog.json`, `token-policy.json` (category names = catalog keys), `component-allowlist.json` (versioned, closed id list) |
| `assets/asset-roles.json` | closed 18-role `assetRole` enum, 4-value `generationPolicy` enum, pinned policies for compliance-critical roles |
| `primitives/`, `components/`, `sections/` | one contract per id (`hero.main` -> `sections/hero-main.json`) |
| `templates/templates.json` | 10 page templates (node sequences, required/repeatable, per-route evidence) |
| `compatibility/graph.json` | rhythm/position rules, each with severity and exceptions; every id is implemented in the validator |
| `schema/` | `pagespec.schema.json` (Draft-07), `example.pagespec.json`, `semantic_validate.py`, `schema/tests/adversarial_test.py` |
| `extraction/` | `measured-values.json` (citation ledger), `verify_all.py`, `prove_drift.py`, `build_pagespec_schema.py` |

## How to run (Python 3 with the `jsonschema` package; run from the repository root)

```
python3 extraction/verify_all.py            # 14 checks, PASS/FAIL/WARN per check, non-zero exit on any failure
python3 schema/tests/adversarial_test.py    # controls + mutations + CLI + catalog/policy + pinned-asset drift layer
python3 extraction/prove_drift.py           # injects drift into scratch copies; verify_all.py must fail on each
python3 schema/semantic_validate.py schema/example.pagespec.json   # validate one PageSpec (exit 0 valid, 1 errors, 2 unreadable)
python3 extraction/build_pagespec_schema.py [--check]              # regenerate / drift-check the static schema
```

All scripts derive their root from their own location, so they also run on a copy of this folder with no sibling
directories. Source citations (`path:line-line` plus a stored `quote`) are resolved against the source project only when it
sits beside this folder; otherwise `verify_all.py` prints a WARN line and skips them (a warning, not a failure). Citations
that point into this package itself are always checked.

## Licensing and generation guidance (read before generating anything)

- The source is a real, live, commercial company. Real third-party logos (publisher marquee, press, award images), about 79
  payment-method logos and 49 country flags, real product UI mockups, a hero video of real people and real partner names
  appear on the pages. **A generator must never reproduce, redraw, approximate or fabricate them**; `assets/asset-roles.json`
  gives every asset role a `generationPolicy` and pins it for the 11 compliance-critical roles (checked by `verify_all.py`
  check [j], which compares the value, not just enum membership).
- ABC Monument Grotesk is a commercially licensed typeface, not redistributable (`must-not-redistribute`). Do not copy, convert
  or re-host it.
- Nothing here grants rights to Coda's copy, marks or assets. **Do not publish or make this repository public without the
  owner's licence review.**
- No external requests: all media paths in a PageSpec are local paths (`/images/...`, `/video/...`); remote and `//` URLs
  are rejected. Links may only be `#` (inert) or one of the 15 routes.
- Packaging: the project is not a git repository. If it is ever put under git, `design-repo.zip` must be gitignored and never
  committed next to the live folder (it goes stale the moment the folder changes). Regenerate the zip last, with the CLI
  `zip` tool, after `verify_all.py` passes.

## Evidence and limitations

Three copy evidence levels exist and are recorded per route (`extraction/measured-values.json` `perRouteCopyEvidence`, and
per template in `templates/templates.json`); they are never flattened.

- **Homepage copy is exact**, taken from the user's own saved page (level a-exact).
- **Five inner pages** (coda-links, coda-giftcloud, distribution, consumer-platforms, pricing) carry real text from the user's
  own saved copies (level b-real-saved-copy).
- **Nine pages** (codapay, coda-webstore, six industry pages, merchant-of-record) carry **original AI-written copy, not Coda's
  wording**, sized to the original slot lengths (level c-original-slot-sized). Their word budgets derive from slot lengths, not
  from measured real copy. Contracts and the example use only short headings/labels within `maxWords`.
- **Structure, layout and motion**: for the homepage they were measured against live coda.co (about 1px) and are documented in the
  source project's `CLONE_SPEC.md`. For the **14 inner pages** the same claim is carried over from earlier build-agent reports;
  it is **not independently recorded in any project file**, so it is not claimed as independently verified.
- **Copy-provenance citations are `inferred`** (`cit-p3-copy-levels`): no source file records which page has which copy level.
- Token values come only from the compiled stylesheet `public/styles/coda-main.css` (minified on one line, so its citations are
  `path:1-1` with a `charRange` and `quote`). Motion values come from the ported implementations and `CLONE_SPEC.md`.
- Word count everywhere is `len(text.split())`. Longer body-copy budgets are rounded upper bounds; budgets are measured only
  where the source text is 1-30 words.

## Known limitations

- **The source has no `prefers-reduced-motion` handling, no dark theme and no box-shadows.** `reducedMotionFallback` (required on
  every node) is a design-repo rule, not mirrored behaviour; there is one theme (`light`) and no elevation shadows. There is no
  page-canvas colour token and no focus/keyboard states in the CSS, so none are specified.
- PageSpecs have **no per-instance token or style override field** (a `tokens` field is rejected). Token safety is checked at the
  catalog/policy layer (parity, `$ref` resolution, theme completeness), not per PageSpec.
- Callout runs are pinned per route by `CALLOUT_COUNT_PER_ROUTE` (creator-economy 4, online-gaming 5, dating 3, digital-
  entertainment 3, esim 4, lms 4, merchant-of-record 5, counted from each page's JSX). Still loose: the creator-economy bridge
  section is optional in `solution-impact`, so a creator PageSpec that omits its bridge is accepted; the contract vocabulary has
  no `minPerPage`.
- `benefits.stack` variants are left off the shared-template nodes: pages with two benefit stacks are ambiguous, so the variant
  per position is not enforced by the template (variant names are still checked against the contract).
- No motion-budget or scroll-stage rule exists (no evidence for one in the source; see `notEvidenced` in `compatibility/graph.json`).
- JS-driven behaviour that is not visible in the JSX (FAQ accordion, card carousel, marquees, inline video, header dropdowns and
  mobile menu, pricing type/country table, image `sizes`) is described in the contracts from the ported implementations.
  Not cloned and not specified: the EN language dropdown behaviour and the route-loading-bar animation.
- Scope was deliberately reduced to 15 routes. Every link to any other coda.co page is an inert `href="#"`; no templates exist for
  those pages and none should be added without new evidence.
- `repositoryVersion` and `pageSpecVersion` are documentation-only; only `allowlistVersion` is machine-checked (see
  `versionFieldNote` in the manifest).

## Snapshot warning

This repository is a snapshot of the source project (React ^18.3.1, Vite ^5.4.8, GSAP ^3.15.0 per its package.json when this
was finalised). If the project changes (a dependency bump, a new route, a copy or layout edit), re-diff the counts, framework
versions, citations and per-route section sequences before trusting this repository; `verify_all.py` re-checks citations only while
the source tree sits beside this folder.
