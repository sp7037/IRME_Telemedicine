/**
 * Design tokens for IRME Telemedicine
 * Centralized theme constants: colors, typography, spacing, shadows, borders, radii, breakpoints
 */

// ============================================================================
// COLORS
// ============================================================================

// Brand colors (from existing brandTheme.js)
export const colors = {
  // Primary brand colors
  brand: {
    navy: "#002043",
    navyDeep: "#001018",
    blueMid: "#123a6f",
    blueBright: "#174f8f",
    accent: "#1f76d8",
  },

  // Site/marketing colors
  site: {
    headerNavy: "#062B4F",
    deepBlue: "#0F4C81",
    teal: "#14B8A6",
    ctaGreen: "#22C55E",
    pageBg: "#f0f4f8",
  },

  // Semantic colors
  primary: "#1f76d8",
  secondary: "#174f8f",
  success: "#22C55E",
  warning: "#f59e0b",
  error: "#dc3545",
  info: "#0ea5e9",

  // Neutral palette
  gray: {
    50: "#f9fafb",
    100: "#f3f4f6",
    200: "#e5e7eb",
    300: "#d1d5db",
    400: "#9ca3af",
    500: "#6b7280",
    600: "#4b5563",
    700: "#374151",
    800: "#1f2937",
    900: "#111827",
  },

  // Text colors
  text: {
    primary: "#10243e",
    secondary: "#4b5563",
    tertiary: "#6b7280",
    disabled: "#9ca3af",
    inverse: "#ffffff",
  },

  // Background colors
  background: {
    primary: "#ffffff",
    secondary: "#f9fafb",
    tertiary: "#f3f4f6",
    dark: "#10243e",
    overlay: "rgba(0, 0, 0, 0.5)",
  },

  // Border colors
  border: {
    light: "#e5e7eb",
    medium: "#d1d5db",
    dark: "#9ca3af",
    focus: "#1f76d8",
  },

  // Status colors (consultation states)
  status: {
    pending: { bg: "#fff4cc", fg: "#8a6d00" },
    accepted: { bg: "#e4efff", fg: "#1f4f8f" },
    queued: { bg: "#efe9ff", fg: "#4a2f9b" },
    inProgress: { bg: "#e3f8ea", fg: "#1b6a3a" },
    completed: { bg: "#eceff4", fg: "#3f4b5e" },
    rejected: { bg: "#fde8e8", fg: "#9d1d1d" },
    postponed: { bg: "#ffeedd", fg: "#8a4b10" },
    canceled: { bg: "#fde8e8", fg: "#9d1d1d" },
  },

  // Dashboard colors
  dashboard: {
    pageBg: "linear-gradient(180deg, #eef5fb 0%, #f8fbfe 45%, #eef4f8 100%)",
    sectionBg: "rgba(255, 255, 255, 0.94)",
    border: "#e0ebf6",
  },
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  // Font families
  fontFamily: {
    base: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    mono: "source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace",
  },

  // Font sizes
  fontSize: {
    xs: "0.75rem",    // 12px
    sm: "0.875rem",   // 14px
    base: "1rem",     // 16px
    lg: "1.125rem",   // 18px
    xl: "1.25rem",    // 20px
    "2xl": "1.5rem",  // 24px
    "3xl": "1.875rem", // 30px
    "4xl": "2.25rem",  // 36px
    "5xl": "3rem",     // 48px
  },

  // Font weights
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Line heights
  lineHeight: {
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },

  // Letter spacing
  letterSpacing: {
    tighter: "-0.05em",
    tight: "-0.025em",
    normal: "0",
    wide: "0.025em",
    wider: "0.05em",
  },
};

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  0: "0",
  1: "0.25rem",   // 4px
  2: "0.5rem",    // 8px
  3: "0.75rem",   // 12px
  4: "1rem",      // 16px
  5: "1.25rem",   // 20px
  6: "1.5rem",    // 24px
  8: "2rem",      // 32px
  10: "2.5rem",   // 40px
  12: "3rem",     // 48px
  16: "4rem",     // 64px
  20: "5rem",     // 80px
  24: "6rem",     // 96px
};

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  none: "none",
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  base: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)",
  xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
  "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
  inner: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)",
  dashboard: "0 14px 34px rgba(0, 32, 67, 0.08)",
  focus: "0 0 0 3px rgba(31, 118, 216, 0.22)",
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const radii = {
  none: "0",
  sm: "0.25rem",   // 4px
  base: "0.5rem",  // 8px
  md: "0.625rem",  // 10px
  lg: "0.75rem",   // 12px
  xl: "1rem",      // 16px
  "2xl": "1.5rem", // 24px
  full: "9999px",
};

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const breakpoints = {
  xs: "480px",
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
};

// Media query helpers
export const media = {
  xs: `@media (min-width: ${breakpoints.xs})`,
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
  "2xl": `@media (min-width: ${breakpoints["2xl"]})`,
};

// ============================================================================
// Z-INDEX
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
};

// ============================================================================
// TRANSITIONS
// ============================================================================

export const transitions = {
  fast: "150ms ease",
  base: "200ms ease",
  slow: "300ms ease",
  slowest: "500ms ease",
};

// ============================================================================
// GRADIENTS
// ============================================================================

export const gradients = {
  heroSection: "linear-gradient(140deg, rgba(0, 32, 67, 0.95) 0%, rgba(31, 118, 216, 0.92) 100%)",
  marketingHero: "linear-gradient(135deg, #062B4F 0%, #0F4C81 52%, #0d6e64 100%)",
  dashboardHeader: "linear-gradient(90deg, #002043 0%, #123a6f 55%, #174f8f 100%)",
  dashboardPage: "linear-gradient(180deg, #eef5fb 0%, #f8fbfe 45%, #eef4f8 100%)",
};

// ============================================================================
// EXPORT ALL AS THEME
// ============================================================================

const theme = {
  colors,
  typography,
  spacing,
  shadows,
  radii,
  breakpoints,
  media,
  zIndex,
  transitions,
  gradients,
};

export default theme;
