/**
 * Brand Assets - New IRME Logo (i + heartbeat mark)
 * Navy #0B2545 | Teal #13A89E
 * 
 * Paths to files in `public/` (CRA: use with %PUBLIC_URL% / process.env.PUBLIC_URL).
 */
const base = process.env.PUBLIC_URL || "";

// Horizontal Logos (primary)
export const BRAND_LOGO_HORIZONTAL_DARK = `${base}/images/brand/logo-horizontal-dark.svg`; // Navy text, light backgrounds
export const BRAND_LOGO_HORIZONTAL_DARK_PNG = `${base}/images/brand/logo-horizontal-dark.png`;
export const BRAND_LOGO_HORIZONTAL_WHITE = `${base}/images/brand/logo-horizontal-white.svg`; // White text, dark/navy backgrounds
export const BRAND_LOGO_HORIZONTAL_WHITE_PNG = `${base}/images/brand/logo-horizontal-white.png`;

// Stacked Logo (vertical, for centered layouts)
export const BRAND_LOGO_STACKED = `${base}/images/brand/logo-stacked.svg`; // Navy, light backgrounds
export const BRAND_LOGO_STACKED_PNG = `${base}/images/brand/logo-stacked.png`;

// Mark/Symbol Only
export const BRAND_MARK = `${base}/images/brand/mark.svg`; // i + heartbeat symbol
export const BRAND_MARK_PNG = `${base}/images/brand/mark-navy-1024.png`;

// Icons (for favicons, app icons)
export const BRAND_ICON_NAVY_ROUNDED = `${base}/images/brand/icon-navy-rounded.svg`;
export const BRAND_ICON_NAVY_SQUARE = `${base}/images/brand/icon-navy-square.svg`;
export const BRAND_ICON_TEAL_ROUNDED = `${base}/images/brand/icon-teal-rounded.svg`;

// Favicons
export const BRAND_FAVICON_SVG = `${base}/images/brand/favicon.svg`;
export const BRAND_FAVICON_32 = `${base}/images/brand/favicon-32.png`;
export const BRAND_FAVICON_ICO = `${base}/favicon.ico`;
export const BRAND_APPLE_TOUCH_ICON = `${base}/images/apple-touch-icon.png`;

// App Icons (PWA manifest)
export const BRAND_ICON_192 = `${base}/images/brand/icon-192.png`;
export const BRAND_ICON_512 = `${base}/images/brand/icon-navy-square-512.png`;

// @deprecated Old logo paths - will be removed
export const BRAND_FAVICON_PNG = `${base}/irme_telemedicine_fevicon.png`;
export const BRAND_HORIZONTAL_LOGO_PNG = `${base}/images/irme-horizontal-logo.png`;
export const BRAND_SQUARE_LOGO_PNG = `${base}/images/irme-logo-square.png`;
export const BRAND_HORIZONTAL_LOGO_PNG_LEGACY = `${base}/irme_hostizontal_topmenu_logo.png`;
