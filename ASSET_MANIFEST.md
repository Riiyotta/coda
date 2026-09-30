Source: https://www.coda.co/

# Asset manifest: coda.co homepage

Method: I recorded every image, font and media response on live at 1440x900, 1280x900 and 390x844. The runs included nav dropdown hovers on all 4 categories, the mobile menu and submenu, product-card hovers and card-carousel navigation. I then compared each file to `public/` by original filename (with WordPress `-WxH` size suffixes stripped). I also cross-checked every `/wp-content/uploads/` URL referenced anywhere in the live HTML, including srcsets and page JSON.

## Result

- Every asset the homepage actually loads is available locally as its original file.
- Live serves WP srcset size variants (`-300xNNN`, `-768xNNN`, `-1536xNNN`); the clone uses the originals. Rendered boxes are identical.
- Nav dropdowns load **no images**. Menu icons and the featured cards' icons are inline SVG, and the featured cards have no background image.
- Hover-state and mobile images were already present: `asset_hover*.avif`, `webstore-asset-hover-mobile.avif`, `codalinks-grow-with-coda-asset-image-mobile.webp`.

## Downloaded in this pass

| File | Path | Format | Size | Used for |
|---|---|---|---|---|
| Coda-cropped-MasterIcon-1-150x150.webp | public/images/ | WebP 150x150 | 2214 B | `<link rel="icon" sizes="32x32">` |
| Coda-cropped-MasterIcon-1-300x300.webp | public/images/ | WebP 300x300 | 4546 B | `<link rel="icon" sizes="192x192">`, `apple-touch-icon`, `msapplication-TileImage` |

Both come from `https://www.coda.co/wp-content/uploads/2026/07/`. Live `<head>` also sets `<meta name="theme-color" content="#26393A">`. Local index.html currently points to `/favicon.svg`.

## Referenced but intentionally not downloaded

- `Coda-White-Paper-–-Beyond-The-App-Store-Banner-1355x2048px.webp` (+ size variants). It appears only in the page's embedded post JSON; the homepage never requests it at any of the three widths.
- Third-party tracking pixels (LinkedIn, etc.) and the usercentrics CMP.

## Loaded assets → local file map

### Fonts
All from `/_build/assets/`, all present in `public/fonts`:
- ABCMonumentGrotesk-Regular-CCsuHl-t.woff2
- ABCMonumentGrotesk-Medium-B5Yc04pP.woff2
- ABCMonumentGrotesk-Heavy-Ba5k0oMp.woff2
- JetBrainsMono-Regular-BQaDgvhP.woff2

### Video
- `2026/08/Coda-Website-Hero-Video-260826.mp4` → public/video/

### Images
All in `public/images/`.

| Live URL (uploads/…) | Widths loaded | Local original |
|---|---|---|
| 2026/05/logo-slot1…6(-300x80).avif | all | logo-slot1…6.avif |
| 2026/05/1…4(-300x94).avif (awards) | all | 1.avif … 4.avif |
| 2026/05/press-logos1…4-300x97.avif, press-logos5-300x105.avif | all | press-logos1…5.avif |
| 2026/05/tinder-reverse.avif | all | tinder-reverse.avif |
| 2026/06/1_1-scale-recharge-1…3(-239x300).avif | all | 1_1-scale-recharge-1…3.avif |
| 2026/06/asset_base(-300x232, -768x593).avif | all | asset_base.avif |
| 2026/06/asset_hover(-300x232, -768x593).avif | all | asset_hover.avif |
| 2026/06/asset_base-1(-300x114, -1536x584).avif | ≥800 | asset_base-1.avif |
| 2026/06/asset_hover-1(-300x114, -768x292, -1536x584).avif | all | asset_hover-1.avif |
| 2026/06/webstore-asset-hover-mobile(-300x244).avif | <800 | webstore-asset-hover-mobile.avif |
| 2026/06/codalinks-grow-with-coda-asset-image-mobile(-300x232, -768x593).webp | all | codalinks-grow-with-coda-asset-image-mobile.webp |
| 2026/06/homepage-codapay-2560x1802-1(-300x211, -768x541).webp | all | homepage-codapay-2560x1802-1.webp |
| 2026/06/homepage-coda-webstore-2560x1802-1(-300x211, -768x541, -1536x1081).webp | all | homepage-coda-webstore-2560x1802-1.webp |
| 2026/06/homepage-coda-distribution-2560x1802-1(…).webp | all | homepage-coda-distribution-2560x1802-1.webp |
| 2026/06/homepage-coda-consumer-platforms-2560x1802-1(…).webp | all | homepage-coda-consumer-platforms-2560x1802-1.webp |
| 2026/07/distribution-header-image-image-asset-1(-300x135, -768x346, -1536x691).webp | all | distribution-header-image-image-asset-1-scaled.webp (WP "-scaled" original) |
| 2026/07/B2B-Blog-–-Case-Study-–-Tinder-–-1920x1080-1(-768x432, -1536x864).webp | all | same name .webp |
| 2026/07/Coda-x-Unity-Partnership-Coda-Press-Page(-768x432, -1536x864).webp | all | Coda-x-Unity-Partnership-Coda-Press-Page.webp |
| 2026/07/coda-white-paper-banner-featured-post(-768x255).webp | all | coda-white-paper-banner-featured-post.webp |
| 2026/09/{DealStreetAsia,Gamesbeat,IGN,Tech-in-Asia}-logo-494x160-1-300x97.webp | all | *-logo-494x160-1.webp |

Inline SVG (no network): the Coda logo, nav icons, ArrowButton, the play/pause icons, social icons and the language flags. The flags are data-URI SVGs in the bundle, used only in the language dropdown.
