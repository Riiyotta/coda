# Coda clone – information architecture

Source: Local clone of coda.co (Vite + React) covering 15 of the site's routes
Status: **measured-from-source** · production approved: **false**
15 routes · 10 templates · 23 unique sections

> Generated from `ia.json` by `build.mjs`. Edit the JSON, not this file.

## Shape of the site

The largest 3 templates (Industry / use-case (standard), Industry (with impact figures), Homepage) account for 8 of 15 routes (53%). The remaining 7 routes span 7 templates.

| template | routes | share |
|---|---:|---:|
| Industry / use-case (standard) | 5 | 33% |
| Industry (with impact figures) | 2 | 13% |
| Homepage | 1 | 7% |
| Pricing | 1 | 7% |
| Product – Codapay | 1 | 7% |
| Product – Coda Links | 1 | 7% |
| Product – Coda Webstore | 1 | 7% |
| Product – Distribution | 1 | 7% |
| Product – Consumer Platforms | 1 | 7% |
| Product – Giftcloud | 1 | 7% |

## Page chrome

**15 routes carry chrome = `full`** — Homepage, Pricing, Product – Codapay, Product – Coda Links, Product – Coda Webstore, Product – Distribution, Product – Consumer Platforms, Product – Giftcloud, Industry / use-case (standard), Industry (with impact figures).

## Sections by reuse

How widely a section is shared determines whether it belongs in a shared
component library or stays local to its page.

| section | category | templates | routes | implementation | scope |
|---|---|---:|---:|---|---|
| `shell.navbar` | SHELL | 10 | 15 | `src/components/Header.jsx + src/lib/header/navController.js` | Present on all 15 routes. |
| `shell.footer` | SHELL | 10 | 15 | `src/components/Footer.jsx` | Present on all 15 routes. |
| `hero.main` | HERO | 10 | 15 | `src/components/Hero.jsx (home); markup inline in src/pages/*Page.jsx` | Opens every route. |
| `cta.pre-footer` | COMMERCE | 10 | 15 | `src/components/PreFooter.jsx (home); markup inline in src/pages/*Page.jsx` | Closes every route. |
| `benefits.stack` | PRODUCT | 9 | 14 | `src/components/BenefitsStack.jsx (home); markup inline in src/pages/*Page.jsx` | Every route except the pricing page (14 routes); some routes carry it twice. |
| `carousel.cards` | CONTENT | 9 | 14 | `src/components/CardCarousel.jsx + src/lib/carousel/useCarousel.js (home); src/lib/enhance/carousel.js (inner pages)` | Every route except the pricing page (14 routes). |
| `spacer.footer-gap` | SHELL | 8 | 13 | `markup inline in src/pages/*Page.jsx` | Sits before the closing band on the routes that end with an FAQ; 13 routes. |
| `callout.feature` | PRODUCT | 8 | 13 | `markup inline in src/pages/*Page.jsx` | One run per route on every route that has feature callouts (13 routes); run length varies by template. |
| `faq.accordion` | CONTENT | 8 | 13 | `src/lib/enhance/faq.js (behaviour) on markup inline in src/pages/*Page.jsx` | Routes that end with an FAQ (13 routes). |
| `highlight.mega` | PRODUCT | 4 | 9 | `markup inline in src/pages/*Page.jsx` | Webstore and distribution product pages and all industry and use-case pages (9 routes). |
| `bridge.section` | PRODUCT | 4 | 9 | `markup inline in src/pages/*Page.jsx` | Routes that open a callout run with its own heading (9 routes). |
| `impact.figures` | PROOF | 7 | 8 | `markup inline in src/pages/*Page.jsx` | Six product pages and two industry pages (8 routes). |
| `metrics.band` | PROOF | 3 | 8 | `src/components/Metrics.jsx (home); markup inline in src/pages/*Page.jsx` | Homepage and the use-case and industry pages that carry it (8 routes). |
| `products.highlight` | COMMERCE | 5 | 5 | `src/components/ProductsHighlight.jsx (home); markup inline in src/pages/*Page.jsx` | The homepage plus the four product pages that cross-sell. |
| `pricing.price-stack` | COMMERCE | 5 | 5 | `markup inline in src/pages/*Page.jsx` | The pricing page and the four product pages that end with pricing. |
| `features.stack` | PRODUCT | 3 | 3 | `markup inline in src/pages/*Page.jsx` | Three of the product pages. |
| `features.grid` | PRODUCT | 2 | 2 | `markup inline in src/pages/*Page.jsx` | Two of the product pages. |
| `callout.isolated` | PRODUCT | 1 | 1 | `markup inline in src/pages/*Page.jsx` | The payment-links product page only. |
| `tiles.page` | PRODUCT | 1 | 1 | `markup inline in src/pages/*Page.jsx` | The Codapay product page only. |
| `comparison.integration` | PRODUCT | 1 | 1 | `markup inline in src/pages/*Page.jsx` | The Codapay product page only. |
| `awards.recognition` | PROOF | 1 | 1 | `src/components/Awards.jsx` | Homepage only. |
| `carousel.press` | PROOF | 1 | 1 | `src/components/PressCarousel.jsx + src/lib/marquee/Marquee.jsx` | Homepage only. |
| `table.payment-method` | CONTENT | 1 | 1 | `src/lib/pricing/PaymentMethodTable.jsx` | The pricing page only. |

**17 shared sections** appear in more than one template and belong in a component library.

**6 single-use sections** appear in exactly one template. Building these
as "reusable" components up front would be speculative — keep them page-local
until a second caller actually appears.

## Templates

### Homepage — `template.home`

1 route · `/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | COMMERCE | `products.highlight` | shared ×5 |
| 4 | PRODUCT | `benefits.stack` | shared ×9 |
| 5 | PROOF | `metrics.band` | shared ×3 |
| 6 | PROOF | `awards.recognition` | page-local |
| 7 | CONTENT | `carousel.cards` | shared ×9 |
| 8 | PROOF | `carousel.press` | page-local |
| 9 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 10 | SHELL | `shell.footer` | shared ×10 |

### Pricing — `template.pricing`

1 route · `/pricing/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | COMMERCE | `pricing.price-stack` | shared ×5 |
| 4 | CONTENT | `table.payment-method` | page-local |
| 5 | CONTENT | `faq.accordion` | shared ×8 |
| 6 | SHELL | `spacer.footer-gap` | shared ×8 |
| 7 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 8 | SHELL | `shell.footer` | shared ×10 |

### Product – Codapay — `template.product-codapay`

1 route · `/product/codapay/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PRODUCT | `features.stack` | shared ×3 |
| 5 | PROOF | `impact.figures` | shared ×7 |
| 6 | PRODUCT | `benefits.stack` | shared ×9 |
| 7 | PRODUCT | `callout.feature` | shared ×8 |
| 8 | PRODUCT | `tiles.page` | page-local |
| 9 | PRODUCT | `comparison.integration` | page-local |
| 10 | CONTENT | `carousel.cards` | shared ×9 |
| 11 | COMMERCE | `pricing.price-stack` | shared ×5 |
| 12 | COMMERCE | `products.highlight` | shared ×5 |
| 13 | CONTENT | `faq.accordion` | shared ×8 |
| 14 | SHELL | `spacer.footer-gap` | shared ×8 |
| 15 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 16 | SHELL | `shell.footer` | shared ×10 |

### Product – Coda Links — `template.product-links`

1 route · `/product/coda-links/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PROOF | `impact.figures` | shared ×7 |
| 5 | PRODUCT | `benefits.stack` | shared ×9 |
| 6 | PRODUCT | `bridge.section` | shared ×4 |
| 7 | PRODUCT | `callout.feature` | shared ×8 |
| 8 | PRODUCT | `callout.isolated` | page-local |
| 9 | CONTENT | `carousel.cards` | shared ×9 |
| 10 | COMMERCE | `pricing.price-stack` | shared ×5 |
| 11 | COMMERCE | `products.highlight` | shared ×5 |
| 12 | CONTENT | `faq.accordion` | shared ×8 |
| 13 | SHELL | `spacer.footer-gap` | shared ×8 |
| 14 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 15 | SHELL | `shell.footer` | shared ×10 |

### Product – Coda Webstore — `template.product-webstore`

1 route · `/product/coda-webstore/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PROOF | `impact.figures` | shared ×7 |
| 5 | PRODUCT | `features.grid` | shared ×2 |
| 6 | PRODUCT | `callout.feature` | shared ×8 |
| 7 | PRODUCT | `highlight.mega` | shared ×4 |
| 8 | CONTENT | `carousel.cards` | shared ×9 |
| 9 | COMMERCE | `pricing.price-stack` | shared ×5 |
| 10 | COMMERCE | `products.highlight` | shared ×5 |
| 11 | CONTENT | `faq.accordion` | shared ×8 |
| 12 | SHELL | `spacer.footer-gap` | shared ×8 |
| 13 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 14 | SHELL | `shell.footer` | shared ×10 |

### Product – Distribution — `template.product-distribution`

1 route · `/product/distribution/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PROOF | `impact.figures` | shared ×7 |
| 5 | PRODUCT | `features.stack` | shared ×3 |
| 6 | PRODUCT | `bridge.section` | shared ×4 |
| 7 | PRODUCT | `callout.feature` | shared ×8 |
| 8 | PRODUCT | `highlight.mega` | shared ×4 |
| 9 | CONTENT | `carousel.cards` | shared ×9 |
| 10 | COMMERCE | `pricing.price-stack` | shared ×5 |
| 11 | COMMERCE | `products.highlight` | shared ×5 |
| 12 | CONTENT | `faq.accordion` | shared ×8 |
| 13 | SHELL | `spacer.footer-gap` | shared ×8 |
| 14 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 15 | SHELL | `shell.footer` | shared ×10 |

### Product – Consumer Platforms — `template.product-consumer-platforms`

1 route · `/product/coda-consumer-platforms/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PROOF | `impact.figures` | shared ×7 |
| 5 | PRODUCT | `features.grid` | shared ×2 |
| 6 | PRODUCT | `callout.feature` | shared ×8 |
| 7 | CONTENT | `carousel.cards` | shared ×9 |
| 8 | CONTENT | `faq.accordion` | shared ×8 |
| 9 | SHELL | `spacer.footer-gap` | shared ×8 |
| 10 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 11 | SHELL | `shell.footer` | shared ×10 |

### Product – Giftcloud — `template.product-giftcloud`

1 route · `/product/coda-giftcloud/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PROOF | `impact.figures` | shared ×7 |
| 5 | PRODUCT | `features.stack` | shared ×3 |
| 6 | PRODUCT | `callout.feature` | shared ×8 |
| 7 | CONTENT | `carousel.cards` | shared ×9 |
| 8 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 9 | SHELL | `shell.footer` | shared ×10 |

### Industry / use-case (standard) — `template.solution-standard`

5 routes · `/industries/dating-app-payments/`, `/industries/digital-entertainment/`, `/industries/esim-digital-utility-payments/`, `/industries/learning-management-system-payments/`, `/use-case/merchant-of-record/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PRODUCT | `highlight.mega` | shared ×4 |
| 5 | PRODUCT | `benefits.stack` | shared ×9 |
| 6 | PROOF | `metrics.band` | shared ×3 |
| 7 | PRODUCT | `bridge.section` | shared ×4 |
| 8 | PRODUCT | `callout.feature` | shared ×8 |
| 9 | CONTENT | `carousel.cards` | shared ×9 |
| 10 | CONTENT | `faq.accordion` | shared ×8 |
| 11 | SHELL | `spacer.footer-gap` | shared ×8 |
| 12 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 13 | SHELL | `shell.footer` | shared ×10 |

### Industry (with impact figures) — `template.solution-impact`

2 routes · `/industries/creator-economy-payments/`, `/industries/online-gaming-payments/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.navbar` | shared ×10 |
| 2 | HERO | `hero.main` | shared ×10 |
| 3 | PRODUCT | `benefits.stack` | shared ×9 |
| 4 | PRODUCT | `highlight.mega` | shared ×4 |
| 5 | PRODUCT | `benefits.stack` | shared ×9 |
| 6 | PROOF | `impact.figures` | shared ×7 |
| 7 | PRODUCT | `bridge.section` | shared ×4 |
| 8 | PRODUCT | `callout.feature` | shared ×8 |
| 9 | PROOF | `metrics.band` | shared ×3 |
| 10 | CONTENT | `carousel.cards` | shared ×9 |
| 11 | CONTENT | `faq.accordion` | shared ×8 |
| 12 | SHELL | `spacer.footer-gap` | shared ×8 |
| 13 | COMMERCE | `cta.pre-footer` | shared ×10 |
| 14 | SHELL | `shell.footer` | shared ×10 |

## Section reference

### SHELL

_Site-wide chrome: fixed header with its dropdown menus, the footer, and the layout spacer that seats the closing band._

**`shell.navbar`** — Fixed header: wordmark, four hover-dropdown categories (Products, Solutions, Resources, Company), a Pricing link, language, login and get-started buttons; a full-screen menu below the mobile breakpoint. Hides while scrolling down.

· Present on all 15 routes. · appears on 15 routes · implemented by `src/components/Header.jsx + src/lib/header/navController.js`

**`shell.footer`** — Site footer: wordmark and social row, four link columns, legal links and copyright.

· Present on all 15 routes. · appears on 15 routes · implemented by `src/components/Footer.jsx`

**`spacer.footer-gap`** — Zero-height layout spacer that sits between the last content section and the closing band so they overlap correctly.

· Sits before the closing band on the routes that end with an FAQ; 13 routes. · appears on 13 routes · implemented by `markup inline in src/pages/*Page.jsx`

### HERO

_The opening block of a route: headline, one supporting line, calls to action._

**`hero.main`** — Opening block: optional product icon row, h1, one supporting paragraph, up to two buttons, and on some routes a publisher-logo marquee or a hero video/image.

· Opens every route. · appears on 15 routes · implemented by `src/components/Hero.jsx (home); markup inline in src/pages/*Page.jsx`

### PRODUCT

_Product and capability explanation: cards, callouts, toolkit grids, integration options._

**`benefits.stack`** — Grey-card benefits grid: a section heading over a row of icon cards.

· Every route except the pricing page (14 routes); some routes carry it twice. · appears on 14 routes · implemented by `src/components/BenefitsStack.jsx (home); markup inline in src/pages/*Page.jsx`

**`features.stack`** — Feature cells separated by hairlines, optionally with a heading, a wide media band and a closing button.

· Three of the product pages. · appears on 3 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`features.grid`** — Toolkit grid of feature cards under a heading, wrapped in a full-width rounded panel.

· Two of the product pages. · appears on 2 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`callout.feature`** — Two-column callout: text block (icon, heading, paragraph, optional link) beside one product mockup; the media side alternates down a run of callouts. A dual-panel variant is used on the consumer-platforms page.

· One run per route on every route that has feature callouts (13 routes); run length varies by template. · appears on 13 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`callout.isolated`** — Single dark rounded panel with a heading, one-line body, docs button and a wide screenshot.

· The payment-links product page only. · appears on 1 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`highlight.mega`** — Large dark rounded panel: heading, a wide media band, then a set of feature cards or a table.

· Webstore and distribution product pages and all industry and use-case pages (9 routes). · appears on 9 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`bridge.section`** — Standalone heading with optional short description that introduces a run of callouts.

· Routes that open a callout run with its own heading (9 routes). · appears on 9 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`tiles.page`** — Two illustrated navigation tiles under a heading; their destinations lie outside the cloned routes, so they are inert links.

· The Codapay product page only. · appears on 1 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`comparison.integration`** — Three integration options as image cards with a closing docs button.

· The Codapay product page only. · appears on 1 routes · implemented by `markup inline in src/pages/*Page.jsx`

### PROOF

_Evidence and credibility: headline figures, big-number cards, awards, press logos._

**`impact.figures`** — Big-number proof block: coloured rounded panel with a heading and a few figure cards.

· Six product pages and two industry pages (8 routes). · appears on 8 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`metrics.band`** — Charcoal band of four headline company figures with a heading.

· Homepage and the use-case and industry pages that carry it (8 routes). · appears on 8 routes · implemented by `src/components/Metrics.jsx (home); markup inline in src/pages/*Page.jsx`

**`awards.recognition`** — Row of award badges with title, source and a learn-more link.

· Homepage only. · appears on 1 routes · implemented by `src/components/Awards.jsx`

**`carousel.press`** — Auto-scrolling strip of press-outlet logos under a heading.

· Homepage only. · appears on 1 routes · implemented by `src/components/PressCarousel.jsx + src/lib/marquee/Marquee.jsx`

### CONTENT

_Interactive or list-style content the visitor works with: FAQ, tables, cross-links, article carousels._

**`carousel.cards`** — Draggable 'Explore more' carousel of three cards on a grey rounded panel, with previous/next arrows.

· Every route except the pricing page (14 routes). · appears on 14 routes · implemented by `src/components/CardCarousel.jsx + src/lib/carousel/useCarousel.js (home); src/lib/enhance/carousel.js (inner pages)`

**`faq.accordion`** — Frequently-asked-questions accordion on a soft grey rounded panel; every item starts collapsed.

· Routes that end with an FAQ (13 routes). · appears on 13 routes · implemented by `src/lib/enhance/faq.js (behaviour) on markup inline in src/pages/*Page.jsx`

**`table.payment-method`** — Interactive payment-method table with a Type tab (rows of logos) and a Country tab (searchable list of countries).

· The pricing page only. · appears on 1 routes · implemented by `src/lib/pricing/PaymentMethodTable.jsx`

### COMMERCE

_Pricing and conversion: price cards, product cross-sell, and the closing call-to-action._

**`products.highlight`** — Product cards on a dark tile grid. The homepage shows the full product set with hover image swaps; inner product pages show a single cross-sell card.

· The homepage plus the four product pages that cross-sell. · appears on 5 routes · implemented by `src/components/ProductsHighlight.jsx (home); markup inline in src/pages/*Page.jsx`

**`pricing.price-stack`** — Two pricing cards: standard (rate columns) and custom (contact sales).

· The pricing page and the four product pages that end with pricing. · appears on 5 routes · implemented by `markup inline in src/pages/*Page.jsx`

**`cta.pre-footer`** — Closing dark call-to-action band directly above the footer.

· Closes every route. · appears on 15 routes · implemented by `src/components/PreFooter.jsx (home); markup inline in src/pages/*Page.jsx`
