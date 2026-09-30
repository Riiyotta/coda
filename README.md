# Coda clone – information architecture

`ia.json` is the only file to hand-edit. `IA.md` and `matrix.csv` are generated from it and are overwritten on every build.

```bash
node validate.mjs   # hard invariants (route/template totals, referential integrity, categories) + reuse summary
node build.mjs      # regenerates IA.md and matrix.csv
```

## What it covers

15 routes in 10 templates, built from the JSX of the local clone of coda.co. Only these routes exist: the homepage, pricing, six product pages, six industry pages and the merchant-of-record page. Every other coda.co link in the header, footer and body is an intentionally inert `#`, so no template exists for those pages.

Section ids (`hero.main`, `callout.feature`, ...) are the same ids used in `design-repo/`, so the IA, the design contracts and the code share one vocabulary. Each section's `implementedBy` names the file that renders it. Homepage sections are separate components; inner-page sections are markup inline in `src/pages/*Page.jsx`, with their behaviour in `src/lib/`.

## What the data shows

- **Two templates carry 7 of the 15 routes (47%).** The standard industry/use-case template serves 5 routes and the industry-with-impact-figures template 2. The other 8 routes each have their own template: the homepage, pricing and the six product pages.
- **17 sections are shared and 6 are page-local.** The single-use ones are `awards.recognition` and `carousel.press` (homepage), `table.payment-method` (pricing), `tiles.page` and `comparison.integration` (Codapay) and `callout.isolated` (Coda Links). Keep them local until a second page needs them.
- **The page frame is universal.** `shell.navbar`, `hero.main`, `cta.pre-footer` and `shell.footer` are on all 15 routes. Every route carries the full header and footer, so the `chrome` field reads `full` everywhere and does not separate templates.
- **`benefits.stack` and `carousel.cards` are on 14 routes**, everything except pricing. `callout.feature` is on 13, in runs of 2 to 5 per page.

## Reading the generated output

- **Callout run lengths** are not encoded per template. `callout.feature` is listed once at the position of its run. Actual run lengths: 2 (Coda Links), 4 (Codapay, Webstore, Distribution, Consumer Platforms, Giftcloud, creator economy), 5 (online gaming, merchant of record), 3 (dating, digital entertainment) and 4 (eSIM, learning platforms). They are also recorded in the `$comment` of `ia.json`.
- **`benefits.stack` appears twice** on four templates (Codapay, Coda Links and both industry templates), at different positions. `node validate.mjs` counts each occurrence, so its reuse table shows 13 templates for it; `IA.md` and `matrix.csv` correctly show 9.
- **Scope text** only uses route counts. `validate.mjs` reports no mismatches between any scope string and the computed counts.

## Evidence

The structure comes from the JSX as it stands. Copy differs by route: the homepage is exact from a saved page, five inner pages carry real text from saved copies, and nine pages carry original AI-written copy. For the 14 inner pages, the claim that layout matches live within about 1px comes from earlier build reports, not from a recorded measurement file. `design-repo/README.md` has the full evidence and licensing notes; the real partner logos, real-people media and the ABC Monument Grotesk font should not be published without a licence review.
