Source: https://www.coda.co/

# Coda homepage: motion and interaction spec

Scope: homepage `/` only. Static layout already matches live: every section bounding box is identical at 1440x900, 1280x900 and 390x844, and doc heights match (7363 / 6801 / 7523 px). This spec covers **motion + interaction** (what the static copy lacks) and the few static mismatches found.

Provenance tags:
- **[bundle X]**: read from Coda's production JS, `https://www.coda.co/_build/assets/X`. The main bundle is `client-CrH_2JZ5.js`.
- **[measured]**: measured with Playwright (Chromium, DPR 1) on live, using getComputedStyle / getBoundingClientRect / getAnimations sampled over time. The usercentrics banner was removed first.

Library facts **[bundle client-CrH_2JZ5.js]**:
- The live site uses **GSAP 3.15.0**, but only for the nav dropdown tweens. ScrollTrigger is used only for `ScrollTrigger.refresh()` when body height changes.
- **react-fast-marquee** is inlined as `index-C-Tc9-Q2.js`.
- motion/framer-motion is used for one thing only: the featured-card description height in the nav.
- There is **no smooth-scroll library** (no Lenis/ScrollSmoother). Native scrolling.
- There is **no scroll-progress bar**. The fixed 1px bar at the top is a *route-change loading bar* (see Header). It never animates on a single-page homepage load or scroll.

Breakpoints (coda-main.css): `sm 600`, `md 800`, `lg 1200`, `xl 1600`, `2xl 2000` (all min-width). JS also branches on `window.innerWidth < 800` (useWindowSize) for the marquees.

Responsive spacing tokens (motion distances depend on them) **[measured, computed]**:

| token | 390 | 1280 | 1440 | formula (>=1200) |
|---|---|---|---|---|
| spacing-3 | 8 | 12.47 | 13.44 | 12px + (100vw-1200px)*.006 |
| spacing-5 | 16 | 24.95 | 26.88 | 24px + (100vw-1200px)*.012 |
| spacing-6 | 20 | 33.27 | 35.83 | 32px + (100vw-1200px)*.016 |
| spacing-7 | 24 | 41.59 | 44.80 | 40px + (100vw-1200px)/50 |
| spacing-navBarHeightBase | 52 | 66.55 | 71.67 | |
| spacing-navBarInnerTopBase | 108 | 87.36 | 94.08 | |
| spacing-navToggleAnimate | 5 | 5.19 | 5.59 | |

`translate-y-7` therefore equals 44.8px at 1440, 41.6px at 1280 and 24px at 390.

---

## 0. Shared: scroll-reveal (`src/lib/reveal.js`)

### Live component `M3` (exported as `A`) **[bundle client-CrH_2JZ5.js]**

```js
const M3 = ({delay, slide=false, zoom=false, once=true, active=true, duration=500, ...}) => {
  const {isIntersecting, ref} = useIntersectionObserver({root:null, rootMargin:"0px", threshold:.1, freezeOnceVisible: once});
  className = cn("transition-all opacity-0", slide && "translate-y-7", zoom && "scale-110",
                 isIntersecting && active && "opacity-100 translate-y-0 scale-100", n);
  style = {transitionDelay: delay ? `${delay}ms` : undefined, transitionDuration: `${duration}ms`}
}
```

Behaviour:
- **Trigger:** one IntersectionObserver per element. `threshold: 0.1`, `rootMargin: "0px"`, `root: null`.
- **Once:** `freezeOnceVisible: true`, so there is no un-reveal on scroll back.
  - Measured on live: every element flipped once at visible fraction 0.10 to 0.14 (sampled every 20px of scroll) and never reverted.
- **Transition:** `transition-property: all`, `duration 500ms`, `timing cubic-bezier(0.4, 0, 0.2, 1)` (Tailwind default easing) **[measured]**.
- **Initial state:** `opacity: 0`, plus `translateY(var(--spacing-7))` for `slide` elements (44.8px at 1440). The `zoom` variant (`scale(1.1)`) is not used on the homepage.
- **Final state:** `opacity: 1`, `translateY(0)`, `scale(1)`.
- **Important for the clone:** live React *replaces* the class list, so `translate-y-7` is removed on reveal. In coda-main.css `.translate-y-7` (offset 63427) comes **after** `.translate-y-0` (offset 62949). Adding `translate-y-0` while leaving `translate-y-7` in place therefore does nothing. The reveal must **remove** `opacity-0`, `translate-y-7` and `scale-110`, then add `opacity-100 translate-y-0 scale-100`.
- **Nesting:** reveal wrappers nest (section, then card, then paragraph/icon). Each has its own observer, so opacities multiply while both are animating. This is intended.
- **Load timeline:** SSR ships all hero wrappers at `opacity-0`. Measured on live, the hero reveal starts about **1035ms after navigation start** (after hydration) and completes 500ms later. In the clone it can start on mount.
  - Observed curve for `.inline-media` translateY: 44.8, 44.69 (+33ms), 42.56 (+84ms), 38.8 (+116ms), 24.3 (+183ms), 12.1 (+250ms), 5.56 (+317ms), 0.46 (+455ms), 0 (+516ms).

### Which elements reveal, with delay and slide values

Delays are **[bundle]** and were confirmed by computed `transition-delay` **[measured]**.

| Element | slide | delay |
|---|---|---|
| `.hero` wrapper, `.hero-title`, hero `.block-p`, `.inline-buttons`, `.publisher-logos` | no | 0 |
| hero `.inline-media` | **yes** | 0 |
| `.products-hightlight`, `.section-bridge`, `.block-p`, `.block-heading` | no | 0 |
| product card inner wrapper (`div.w-full.h-full.relative.overflow-hidden` inside each `a.products-highlight-inner-card`) | **yes** | `(index+1)*50`, i.e. 50/100/150/200/250ms |
| `.inline-icon` (within `.inline-icons`) | no | `index*50`, i.e. 0/50ms |
| `.marquee`, `.media-hover-up`, `.media-hover-replace` wrappers | no | 0 |
| `.benefits-stack`, `.benefits-stack-inner-card` | no | 50/100/150/200/250/300ms (cards 1 to 6) |
| `.metrics`, `.metrics-item` | no | 50/100/150/200ms |
| `.awards`, `.awards-item` | no | 50/100/150/200ms |
| `.card-carousel`, `.press-carousel`, `.pre-footer` | no | 0 |

### Local bugs to fix in `reveal.js` / markup [measured on localhost:5210]

1. **Wrongly marked `<line>` elements.** `tools/html2jsx.py mark_reveal()` also tagged the ArrowButton hover `<line>` (`class="transition-all opacity-0 duration-300 md:group-hover:opacity-100"`) with `data-reveal`. That is 4 in CardCarousel.jsx and 5 in ProductsHighlight.jsx.
   - The placeholder reveal then forces them to `opacity-100`, so the arrow line is visible at rest.
   - Measured locally: `line` opacity is 1 before hover; on live it is 0.
   - These are **not** reveal elements and must be excluded (e.g. skip SVG elements or any `duration-300` element).
2. **Stuck slide.** Product cards 4 (Webstore) and 5 (Distribution) keep `translate-y-7` after reveal. Locally they stay shifted **+44.8px at 1440**: local wrapper top is 45px below the card link, versus 0 on live.
   - Cause: the cascade issue described above. This is the "Webstore card looks taller/lower" symptom. The bounding box height is identical (576.77px); the card is displaced by 44.8px.
3. **Lost slide.** The saved HTML captured product cards 1, 2 and 3 and hero `.inline-media` *already revealed*. mark_reveal reset them to `opacity-0` but did not restore `translate-y-7`, so locally they fade without sliding. Add `translate-y-7` back to:
   - the 5 product-card inner wrappers;
   - hero `.inline-media`.

---

## 1. Header (`Header.jsx`)

### 1a. Hide/show on scroll [bundle `pb()` in client-CrH_2JZ5.js; measured]

Wrapper: `div.fixed.top-0.left-0.w-full.z-[55].pointer-events-none.transition-transform.duration-300`. The computed transition is `transform 0.3s cubic-bezier(0.4,0,0.2,1)`.

The logic runs on a requestAnimationFrame loop, throttled to one decision per 50ms:

```
y = scrollY; threshold = innerHeight * 0.2
if |y - lastY| < 5 → ignore
hidden = (y > threshold && y > lastY)   // scrolling down past 20% vh
lastY = y
```

- Apply the class `-translate-y-full` when `hidden && !isMenuOpen && activeDropdown === ""`. Otherwise apply `transform-none`.
- Measured hidden offset: **-107.48px @1440** (wrapper height 107.5), **-99.80px @1280**, **-860px @390**. At 390 the wrapper contains the full-height (100dvh) mobile nav.
- Measured show curve after a 150px scroll up, top in px sampled every ~50ms: -107.5, -107.5, -98.4, -58.3, -17.5, -5.6, -0.76, 0. This is about 300ms.
- **Local:** the header never hides (top stays 0 at scrollY 1000). Needs implementing.

### 1b. Backdrop blur layer [bundle; measured]

First child of the wrapper: `absolute left-0 top-0 w-[100vw] h-[100vh] bg-charcoal bg-opacity-10 backdrop-blur-[20px] opacity-0 transition-opacity duration-700 pointer-events-none`.

- It gets `opacity-100` when a dropdown is active or the mobile menu is open.
- Measured: `backdrop-filter: blur(20px)`. Background computes to `rgba(0,0,0,0)` because `bg-opacity-10` does not apply in this CSS build, so it is a blur only.
- Opacity transitions over **700ms** with cubic-bezier(.4,0,.2,1). Measured open: 0.21 @175ms, 0.52 @260ms, 0.87 @430ms, 1 @720ms.

### 1c. Route loading bar (the "1px bar") [bundle `kb()`]

`fixed top-0 left-0 h-[1px] z-[1000] w-0 invert bg-[#000000]`. It is driven only by router events:
- start: `w-[70%]`, `transition: width 2s ease-out`;
- data-ready: `w-[80%]`;
- finished: `w-full -translate-y-full`, `transition: width .3s ease-out, transform .8s .8s`;
- reset after 1000ms.

On a static single-page clone it stays at `w-0` (invisible). **No scroll-progress behaviour exists.** Optional to implement.

### 1d. Desktop nav dropdowns (Products / Solutions / Resources / Company) [bundle `ob()`, `aS()`, `oS()`; measured]

**Structure.** Already present in Header.jsx:
- `.nav-header-category-{Label}` contains a `button.nav-header-item` and a `div.primary-category`.
- `div.primary-category` is `absolute left-0 top-0 w-full pt-navBarInnerTopBase opacity-0` (md: no transform). It contains:
  - `.primary-category-bg > .primary-category-bg-inner` (white, rounded-lg, starts at `translateY(-100%)`);
  - `.primary-inner` (the columns);
  - an optional `a.primary-category-featured`.
- Pricing is a plain link. It has no dropdown; hover bg is `rgb(237,238,225)`.

**Shared state:** `{active:"", lastActive:"", hoverTimer, isMenuOpen}`.

**Triggers:**
- `mouseover` on the button or the panel clears hoverTimer and sets `active = label`.
- `mouseout` on the button or the panel sets `hoverTimer = setTimeout(() => active = "", 300)`.
- Clicking the button on desktop does nothing: it calls preventDefault and only acts on mobile.
- The Pricing link's mouseover sets `active = ""` immediately.

**GSAP tweens** (selectors are scoped to the category element via `useGSAP({scope})`):

- **Open from closed** (`active === label && lastActive === ""`):
  - `.primary-category, .primary-inner`: opacity 0→1, 0.5s, `power2.out`.
  - `.primary-category-bg-inner`: y "-100%"→0, 0.5s, `power2.inOut`.
  - `.primary-category .nav-header-item`: opacity 0→1, y "-35%"→0, 0.35s, `power2.out`, **stagger 0.03s**, **delay 0.2s**.
  - `.primary-category-featured`: opacity 0→1, y "-10%"→0, 0.35s, `power2.out`, delay 0.4s.
- **Switch to this category from another** (`lastActive !== ""`):
  - set `.primary-category` opacity 1;
  - tween `.primary-inner, .nav-header-item, .primary-category-featured` to opacity 1, 0.5s, power2.out;
  - set bg-inner y to 0.
- **Switched away** (another category became active): tween everything to opacity 0 and items/featured to y 0, 0.5s power2.out; set bg-inner y "-100%".
- **Close** (`active` becomes ""): after an additional `setTimeout(300)`, run:
  - `.primary-category`: opacity→0, 0.35s power2.out, **delay 0.35s**;
  - `.primary-inner`: opacity→0, 0.5s power2.out;
  - `.primary-category-bg-inner`: y→"-100%", 0.5s `power2.inOut`;
  - `.primary-category-featured`: opacity→0, 0.35s.
- Every tween first calls `killTweensOf` on the same selectors.
- CSS equivalents if not using GSAP: `power2.out` = easeOutCubic `cubic-bezier(0.33,1,0.68,1)`; `power2.inOut` = easeInOutCubic `cubic-bezier(0.65,0,0.35,1)`. Recommended: add `gsap` and port the tweens verbatim.

**Measured open timeline** (Products, 1440; bg-inner translateY / item0 opacity / item3 opacity):

| t | bg-inner y | item0 op | item3 op |
|---|---|---|---|
| 0ms | -333.65 | 0 | 0 |
| 89ms | -315.5 | 0 | 0 |
| 175ms | -237.8 | 0.07 | 0 |
| 260ms | -93.4 | 0.61 | 0.03 |
| 345ms | -25.1 | 0.86 | 0.53 |
| 470ms | 0 | 1 | 0.93 |
| 638ms | 0 | 1 | 1 |

The trigger button background animates to `rgb(237,238,225)` (grey-0) via transition-colors 150ms.

**Measured close:** starts **~300ms** after mouse leaves (backdrop starts fading). `.primary-inner` starts fading at **~600ms**. bg-inner reaches -331px at ~1050ms, and `.primary-category` opacity reaches 0 at ~1100ms.

**Panel geometry @1440** [measured]:
- `.primary-category` rect is x 26.9, y 17.9, w 1386.25 (the nav bar width). Heights: Products 334.2, Solutions 517.2, Resources 365.7, Company 430.0.
- Padding is `94.08px 17.92px 13.44px` (pt = navBarInnerTopBase).
- bg-inner radius is 22.4px.
- Columns are a CSS grid `grid-cols-[repeat(var(--cols),minmax(0,1fr))]` with md:gap-8.

**Nav item** (`oS`):
- `.nav-item`: padding 13.44px, radius 13.44px.
- Hover bg is `rgb(237,238,225)`, transition-colors 150ms.
- Title is `type-ui-nav-l`: 17.92px / 26.88px.
- Description is `type-ui-nav-s` in text-grey-2.
- Icon tile `.w-navIcon` is 31.36px square, radius 8.96px.

**Content** [measured live DOM; items with icon tiles in Products]:
- **Products** (3 columns):
  - Codapay, "Unlock global payment coverage", /product/codapay/
  - Coda Links, "Link out-of-app seamlessly", /product/coda-links/
  - Coda Webstore, "Build your webstore instantly", /product/coda-webstore/
  - Coda Distribution, "Scale globally with full control", /product/distribution/
  - Coda Consumer Platforms, "Instant global distribution", /product/coda-consumer-platforms/
  - Giftcloud, "B2B digital rewards platform", /product/coda-giftcloud/
  - Items are 408x82 @1440.
- **Solutions** (2 columns, no icons, items 644x54):
  - Mobile & Online Gaming; Creator Economy; Digital Entertainment; EdTech & Online Learning; eSIM & Digital Utilities; Dating
  - Merchant of Record (MoR); Unity
- **Resources** (2 columns plus featured card):
  - Tech Docs (docs.coda.co); Reports & White Papers; Case Studies; Blogs
  - Payment Guides; Market Guides
- **Company** (1 column plus featured card):
  - About Coda; Events; Press; Careers; Job Openings (jobs.lever.co/Coda, target _blank, external icon)

**Featured card** (Resources: "CASE STUDIES / Read case studies / How we're helping publishers achieve measurable results." → /case-studies/; Company: "CONTACT US / How can we help? / Get in touch with our sales and support teams…" → /contact/):
- No background image (bg grey-0 `rgb(237,238,225)`, text charcoal).
- Rect @1440: 442.66 x 258.2 (Resources) or 322.45 (Company); radius 17.92px.
- Hover:
  - radius → **26.88px** (`md:hover:rounded-xlu`, transition-all 150ms);
  - title arrow `<line>` scaleX 0→1 / opacity 0→1, 200ms, origin-right;
  - the hidden description `p` animates `{opacity: 0→1, height: 0→auto}` with motion's default spring/tween. Measured final: height 62.7px (Resources) / 89.6px (Company), opacity 1.

### 1e. Right-side buttons @1440 [measured]

All three are 43px tall with radius 13.44px and transition-colors 150ms.

| Button | position/size | style |
|---|---|---|
| Language "EN" | x 1095.6, w 77.6 | padding 0 14.34 0 8.96; bg transparent; hover `bg-charcoal/10` |
| Login | x 1182.2, w 80 | padding 8.96 17.92; hover grey-0 |
| Get started | x 1271.2, w 124.1 | bg `rgb(32,32,32)`, text `rgb(248,249,235)`; hover grey-0 / black text |

Font is 17.92px. Language dropdown: only if more than one language (live has en/zh/ja/ko). It opens on click (no animation) as an `absolute top-[calc(100%+8px)] rounded-md bg-offWhite shadow-sm` list, with a fixed inset-0 click-catcher.

### 1f. Mobile menu (<800px) [bundle `vg()`, `db()`, `ob()`; measured @390]

**Nav shell:**
- `relative flex-col rounded-mdu min-h-navBarHeightBase h-[100dvh] overflow-clip`: 374x844 at x 8, y 8.
- White bar: `h-navBarHeightBase` = 52px.
- Logo: `w-headerLogo`, absolute left-5, 88x52.

**Right cluster** (absolute right-0, h 52):
- "EN" 55.6x33.6, radius 10px.
- "Get started" 92.9x33.6, bg `rgb(32,32,32)`, radius 8px, 14px font.
- Hamburger (`db`):
  - wrapper 44x36 with padding `p-4 pr-5`;
  - lines box 16x12 with gap 3px, lines 16x2 `bg-current`, `transition-all` 150ms;
  - open state (`.open` on wrapper): line1 `rotate-45 translate-y-navToggleAnimate(5px)`, line2 `opacity-0`, line3 `-rotate-45 -translate-y-navToggleAnimate`.

**Toggle:** `isMenuOpen = !isMenuOpen`. When closing, `active` is reset to "" after 300ms.

**Menu panel** (sections list): `opacity-0 -translate-y-6 transition-all duration-300 bg-white pt-navBarHeightBase`. When open: `translate-y-0 opacity-100 pointer-events-auto`.
- Measured open (opacity / translateY): 0.08 / -18.3 @43ms, 0.69 / -6.1 @130ms, 0.95 / -1.0 @213ms, 1 / 0 @300ms.
- Close mirrors this: 0.83 / -3.5 @85ms, 0.22 / -15.5 @170ms, 0 / -20 @340ms.
- Backdrop (1b) fades over 700ms.

**Mobile buttons row** (`md:hidden …`): same opacity/translate transition, 374x46 at y 243. Contains Login (59x32) and Get started (93x32, bg charcoal); font 14px, padding 8px 12px.

**Category rows:** Products/Solutions/Resources/Company/Pricing are 374x41 each, padding 12px 16px, 14px font, with a chevron-right icon (1.2em).

**Tapping a category** sets `active = label`, which does two things:
- The menu panel and buttons row get `-translate-x-full` (transition-all 300ms). Measured x: -12.3 @42ms, -220.9 @125ms, -344 @210ms, -374 @336ms.
- The category's `.primary-category` is positioned `absolute left-0 translate-x-full` inside the panel, so it slides in with it. Its opacity is GSAP-tweened as in 1d: 0.25 @42ms, 0.59 @125ms, 0.93 @294ms, 1 @508ms.

**Submenu panel:**
- 374 x 520.8, white, `rounded-mdu`, padding `52px 16px 8px`.
- `max-h-[calc(95dvh - notification)] overflow-auto`.
- "Back" row: chevron-left, 342x33 at y 60. Clicking it sets `active = ""`.
- Items are 342x56 each.

---

## 2. Hero (`Hero.jsx`)

- **Reveal:** see section 0. `.inline-media` must have `slide`.
- **Publisher logos marquee** (react-fast-marquee) [bundle publisher-logos-Bi5xzS59.js, index-C-Tc9-Q2.js; measured]:
  - Props: `autoFill = play = (innerWidth < 800 || logoCount > 4)`. Live has 6 logos, so both are always true. `gradient = !(innerWidth < 800) && s`, `gradientColor "#fcfcfc"`, `gradientWidth 200` (default).
  - Defaults: `speed 50` (px/s), `direction "left"`, `delay 0`, `pauseOnHover false`, `loop 0` (infinite).
  - Keyframes `scroll`: `translateX(0%)` → `translateX(-100%)`, `linear infinite`. Two `.rfm-marquee` copies side by side.
  - **Duration = (contentWidth × copies) / 50 s.** Copies = `ceil(containerW / contentW)` when autoFill and content < container, else 1. Recomputed with a ResizeObserver on container and content.
  - Measured:

    | width | container | content | copies | duration | gradient overlay |
    |---|---|---|---|---|---|
    | 1440 | 797.4 | 806.25 | 1 | **16.125s** | 200px, #fcfcfc |
    | 1280 | 740.5 | 748.6 | 1 | **14.97s** | 200px |
    | 390 | 390 | 616.97 | 1 | **12.34s** | **none** |

  - Logo box: `w-[8.57em] aspect-[120/32]`.
  - **Local mismatch:** duration is baked at `17.276s` at every width. The overlay is also baked in, so a 200px gradient shows at 390 where live has none. Compute at runtime.
- **Hero video** [bundle InlineVideo-CpOHSTVY.js; measured]:
  - `<video autoPlay loop muted playsInline class="w-full h-full object-contain">` in `div.w-full.aspect-video.relative.rounded-md.overflow-hidden`.
  - State `playing = true`. A `useEffect` calls `video.play()` or `video.pause()` whenever it changes.
  - Button: `absolute right-4 bottom-4 p-3 rounded-md bg-charcoal/20 text-offWhite`.
    - Measured bg `rgba(32,32,32,0.2)`, color `rgb(248,249,235)`, radius 13.44px, padding 13.44px.
    - Size 53.8 @1440, 49.9 @1280, 32 @390 (at x 1368.3 / y 1363.2 page-absolute @1440).
    - Icon `div.w-5.h-5`: **pause icon while playing**, play icon while paused. There is no transition.
  - Pause SVG (viewBox 0 0 20 20): two rects, `M5.75 3C5.33579 3 5 3.33579 5 3.75V16.25C5 16.6642 5.33579 17 5.75 17H7.25C7.66421 17 8 16.6642 8 16.25V3.75C8 3.33579 7.66421 3 7.25 3H5.75Z` and `M12.75 3C12.3358 3 12 3.33579 12 3.75V16.25C12 16.6642 12.3358 17 12.75 17H14.25C14.6642 17 15 16.6642 15 16.25V3.75C15 3.33579 14.6642 3 14.25 3H12.75Z`, fill currentColor.
  - Play SVG (viewBox 0 0 24 24): `M6 7.40825C6 6.33866 7.14675 5.66062 8.08395 6.17607L16.7394 10.9366C17.7108 11.4708 17.7108 12.8667 16.7394 13.4009L8.08395 18.1614C7.14675 18.6769 6 17.9988 6 16.9292V7.40825Z`, fill currentColor, evenodd.
  - Measured: live `paused=false` on load; click → paused; click → playing.
  - **Local mismatch:** the video is `paused=true` after load, so autoplay is blocked, and the button is inert. React's `muted` prop does not set the attribute before autoplay evaluation. Fix: mirror live and call `ref.current.muted = true; ref.current.play()` in an effect. Wire the button toggle and icon swap too.

---

## 3. ProductsHighlight (`ProductsHighlight.jsx`)

**Card** (`a.products-highlight-inner-card.group`) [bundle products-highlight-inner-card-D5uHEDGv.js; measured]:
- Reveal wrapper has `slide`, delay `(i+1)*50`.
- Inner box: `rounded-md bg-charcoal pt-5 transition-all md:group-hover:rounded-xlu`. Radius **13.44px → 26.88px** on hover, transition-all 150ms cubic-bezier(.4,0,.2,1). Measured: 19.59 @50ms, 25.8 @100ms, 26.88 @150ms.

**ArrowButton** (`absolute right-5 top-5`, `fill="white"`, `[&_rect]:stroke-transparent`) [bundle ArrowButton-BzPXnroR.js]:
- svg 40x40 viewBox, rendered at `w-7` = 44.8px @1440 (32px <800). Offset 26.88px from the top and right @1440. Transition-colors 300ms.
- `path` (chevron): `-translate-x-[0.15em]` (-2.4px) at rest → `translate-x-0` on `md:group-hover`, transition-transform 300ms.
- `line` (shaft): opacity 0 → 1 on `md:group-hover`, transition-all 300ms.
  - Measured line opacity: 0.085 @50ms, 0.457 @100ms, 0.776 @150ms, 0.99 @250ms.
  - **Local: shows at rest** (see section 0, bug 1).

**media-hover-replace** (cards 3, 4, 5) [bundle media-hover-replace-6gv7pbaK.js; measured]:
- The base layer div has `group-hover:md:opacity-0`, and the absolute bottom layer `group-hover:md:opacity-100`.
- Both use `transition-opacity duration-200` (0.2s cubic-bezier(.4,0,.2,1)). Measured base opacity: 0.76 @50ms, 0.22 @100ms, 0 @200ms.
- Pure CSS; works locally already.
- Mobile uses `imageMobile` (`md:hidden`): e.g. `webstore-asset-hover-mobile.avif` for Webstore. There is no hover swap on mobile.

**media-hover-up** (card 2, Coda Links) [bundle media-hover-up-DXlksD4N.js]:
- The absolute layer at `top-2` gets `group-hover:-translate-y-2`: measured **-8.96px @1440**, transition-transform 150ms. Works locally.

**Card 1 marquee** (`content/marquee`, images 1_1-scale-recharge-1/2/3 + tinder-reverse) [bundle marquee-aVY9p8pW.js]:
- Two instances: desktop `hidden md:block` and mobile `md:hidden`.
- Both use `autoFill = !(innerWidth < 800)`, speed 50, no gradient.
- Items: `flex gap-4 pr-4`, height `h-productCardMarqueeH`.
- Measured:

  | width | content | copies | duration |
  |---|---|---|---|
  | 1440 | 1034.81 | 2 | **41.39s** |
  | 1280 | 960.89 | 2 | **38.44s** |
  | 390 (mobile instance, autoFill off) | 912 | 1 | **18.24s** |

- **Local mismatch:** desktop is baked at 44.35s. The mobile instance is baked at **0s, so it does not animate on mobile**.

Delay stagger inside a card: `.inline-icon` 0/50ms. Other children are revealed individually with no delay.

---

## 4. BenefitsStack (`BenefitsStack.jsx`)

- Reveal only. Cards have delay 50 to 300ms (cards 1 to 6), no slide.
- No hover states [bundle benefits-stack-inner-card-FZ1fJfvU.js].
- Card: `rounded-md bg-grey-0 p-5`.

## 5. Metrics (`Metrics.jsx`)

- Reveal only: `.metrics` then `.metrics-item` with delay (i+1)*50 = 50/100/150/200ms.
- **No count-up.** The bundle (metrics-item-C4srIFH-.js) renders static `core/heading` h3 text; confirmed static on live.

## 6. Awards (`Awards.jsx`)

- Reveal: items delay 50/100/150/200ms.
- Hover [bundle awards-item-DHJgsyBn.js; measured]: `[&:hover_.wp-block-image]:-translate-y-1`, i.e. the logo moves **-4.48px** @1440 with transition-transform 300ms cubic-bezier(.4,0,.2,1).
- "Learn more" link (`md:arrow-button` utility): the computed style of the `<a>` does not change on hover (pill, radius 9999px, padding 12.46 22.9, 15.68px/500).
- Pure CSS; identical locally.

## 7. CardCarousel (`CardCarousel.jsx`)

Source: [bundle card-carousel-pYWQhttU.js, useCarousel-DE99UO_7.js, card-carousel-item-Bp52Ae0-.js; measured].

**Container:**
- `.card-carousel md:px-6`, then a `bg-grey-0 rounded-md py-6 overflow-hidden` box. Measured @1440: x 35.83, w 1368.3, h 591.3, padding 35.84px 0, radius 13.44px.
- Title row: h2 `type-header-l` plus desktop buttons `hidden md:flex gap-2` (two ArrowButtons 44.8px at x 1185.9 and 1239.7).
- Mobile buttons: `md:hidden flex justify-end gap-2` below the track, 32px each (x 302 and 338 @390).
- Track: `.carousel w-[85%] md:w-full relative aspect-[328/362] md:aspect-[1008/400] flex`, starting with `.carousel-spacer w-3` (spacing-3).

**useCarousel** (`snapElement ".carousel-snap"`, `spacerElement ".carousel-spacer"`, `startEnabled true`, `slide true`, `setOuterHeight false`):
- Each `.card-carousel-item` gets inline `position:absolute; left:0; top:0; transition:none; user-select:none`, and its `<img>` gets `transition:none`.
- **Layout:** `x_i = i * (itemWidth + spacerWidth)`. The target offset is `x_current`. Measured step: **1142px @1440** (1128.95 + 13.44), **1060px @1280** (1048.3 + 12.47), **306px @390** (297.5 + 8).
- **Per rAF** (skipped if less than 1000/60 ms since last):
  - `xLerp += (x_i - x_current + dragLerp - xLerp) * 0.125`, rounded to 0.001;
  - `style.transform = translateX(${xLerp}px)`;
  - `dragLerp += (dragDelta - dragLerp) * 0.2`.
- Measured slide 0→1 @1440, card 2 x from 1142: 874 @33ms, 512 @104ms, 300 @174ms, 154 @245ms, 53 @409ms, 14 @574ms, 3.7 @737ms, 0.84 @919ms, 0.11 @1167ms. About 1.2s exponential settle.
- **Buttons:**
  - prev: `setCurrent(current-1)` with `reverse` (rotate-180), `disabled` when current === 0;
  - next: disabled when current === count-1.
  - Disabled style: `text-grey-2/50` → `rgba(90,90,79,0.5)`, no `group` class so no hover arrow, no onClick. Enabled: `text-charcoal` `rgb(32,32,32)`. Color transition 300ms.
  - Carousel ArrowButtons use `fill="transparent"` with the rect stroke = currentColor.
- **Drag/swipe:** window pointer listeners.
  - pointerdown inside the track records the start.
  - pointermove sets delta; |dx| > 10 marks it as dragged. When |dx| > **15% of item width**, it goes next (dx<0) or prev and ends the drag.
  - **Drag wraps around** (last→0, 0→last); buttons do not.
  - Clicks on links are suppressed after a drag, and mousedown/mousemove on `<a>` are preventDefault'ed.
  - Measured on live: dragging left from index 1 went to index 2.
- **Peek (static mismatch):**
  - Live second card left edge is at x 1297.5 @1440, so the next card peeks **106.7px** inside the grey box (right edge 1404.2).
  - Locally the baked `translateX(1224px)` puts it at 1379.5, a **24.7px** peek (**-82px** delta). At 1280 local shows no peek (live shows 70.9px). At 390 live peeks 64px; local card 2 is at x 1244 (no peek).
  - Cause: translateX values were baked from the saved snapshot. Replace them with runtime useCarousel.

**Item hover** (md only) [bundle; measured]:
- Title `p.type-header-s`: `md:text-grey-2` `rgb(90,90,79)` → `md:group-hover:text-charcoal` `rgb(32,32,32)`, 300ms.
- Small arrow svg: `md:opacity-0 md:translate-x-1/2` (+8.95px) → opacity 1 / translate 0, transition-all 300ms.
- Image wrapper: `md:group-hover:scale-[1.05] transition-transform duration-500 ease-in-out`.
- Pure CSS; identical locally.

## 8. PressCarousel (`PressCarousel.jsx`)

- react-fast-marquee `autoFill`, speed 50, no gradient, direction left [bundle press-carousel-m1jH77zE.js].
- Items: `w-pressLogoW`, gap-2.
- Measured content width and duration:

  | width | content | duration |
  |---|---|---|
  | 1440 | 2561.25 | **51.225s** |
  | 1280 | 2378.38 | **47.57s** |
  | 390 | 2255 | **45.1s** |

- Local is baked at 54.89s. Compute at runtime.

## 9. PreFooter (`PreFooter.jsx`)

- Reveal only.
- Buttons (CSS, identical locally) [measured]:
  - `is-style-glass-white`: bg `rgba(248,249,235,0.2)`, `backdrop-filter: blur(4px)`.
  - `is-style-grey`: bg `rgb(237,238,225)`.
  - Both: radius 13.44 → **22.4px** on hover, and the `::before` "→" width 0 → 16.8px / opacity 0 → 1. Transition 0.3s cubic-bezier(.4,0,.2,1).
  - The hero buttons (`is-style-grey`, `is-style-black` `rgb(0,0,0)`) behave identically.

## 10. Footer (`Footer.jsx`)

[bundle `wg()`; measured; all pure CSS, verified identical locally]
- Social icons: `text-grey-1 md:hover:text-grey-0 transition-colors duration-300`.
- Link lists (`group/fitem`): an arrow slot `w-0 → md:group-hover/fitem:w-[1.2em]` (0 → 21.5px @1440), transition-all 200ms.
- Credits popover (`group/credits`):
  - `opacity-0 translate-y-4` → `opacity-100 translate-y-0`, 300ms.
  - Panel `p-6 rounded-lg bg-grey-mid/85 backdrop-blur-[32px]`: measured bg `rgba(124,125,118,0.85)`, blur 32px, 300x115.6 @1440.
  - Inner links' external icon: `md:group-hover/creditsitem:-translate-y-1`, 200ms.
- Cookie link (`#cookies`) calls `window.__ucCmp.showSecondLayer()`. Not applicable locally.

---

## Static mismatches summary (live vs localhost:5210)

| # | What | Delta | Cause |
|---|---|---|---|
| 1 | Webstore and Distribution product cards | shifted **+44.8px** down @1440 (+41.6 @1280, +24 @390) after reveal | `translate-y-7` not removed; it beats `translate-y-0` in the cascade |
| 2 | ArrowButton `<line>` in product cards and carousel | visible at rest (opacity 1 vs 0) | mark_reveal tagged it `data-reveal` |
| 3 | Card carousel peek | 24.7px vs 106.7px @1440; none vs 70.9 @1280; none vs 64 @390 | baked `translateX(1224px/2448px)` |
| 4 | Marquee durations | publisher 17.28s vs 16.13 / 14.97 / 12.34; product 44.35 vs 41.39 / 38.44; press 54.89 vs 51.23 / 47.57 / 45.1 | baked `--duration` |
| 5 | Mobile product-card marquee | static (0s) vs 18.24s | baked at desktop width where it was hidden |
| 6 | Publisher-logos gradient @390 | 200px #fcfcfc fade present vs none | baked overlay; live drops it below 800px |
| 7 | Hero video | paused on load vs playing | autoplay blocked; no play() effect |
| 8 | Header hide, nav dropdowns, mobile menu, carousel buttons/drag | inert | no JS |
| 9 | Favicon | `/favicon.svg` placeholder vs Coda MasterIcon | downloaded, see ASSET_MANIFEST.md |
| 10 | Image sources | local uses originals (e.g. 2560x1802 webp) where live uses srcset sizes (1536w/768w/300w) | cosmetic/perf only; rendered boxes identical |
