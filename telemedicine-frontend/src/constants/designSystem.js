/**
 * IRME Telemedicine Design System
 * 
 * Centralized design tokens for a modern, clean, trustworthy healthcare UI.
 * Based on the existing brand navy (#002043) with improved accessibility,
 * consistency, and modern healthcare aesthetics.
 */

// ============================================================================
// COLORS
// ============================================================================

export const colors = {
  // Brand colors (from existing logo)
  brand: {
    navy: "#002043",
    navyDeep: "#001018",
    blue: "#1f76d8",
    blueMid: "#123a6f",
    blueBright: "#174f8f",
  },

  // Primary palette
  primary: {
    50: "#e8f2ff",
    100: "#c8dff8",
    200: "#9ec9ff",
    300: "#74b3ff",
    400: "#4a9dff",
    500: "#1f76d8", // Main primary
    600: "#1762bf",
    700: "#0f4c81",
    800: "#0a3760",
    900: "#062B4F",
  },

  // Success (medical green)
  success: {
    50: "#eef8f2",
    100: "#d4ede1",
    200: "#acdec6",
    300: "#7fc9a3",
    400: "#52b77f",
    500: "#22C55E", // Main success
    600: "#17a34a",
    700: "#137a39",
    800: "#0d5e2b",
    900: "#084b21",
  },

  // Warning
  warning: {
    50: "#fffbf0",
    100: "#fff4d6",
    200: "#ffe8ad",
    300: "#ffd97e",
    400: "#ffc34f",
    500: "#f59e0b",
    600: "#d97706",
    700: "#b45309",
    800: "#92400e",
    900: "#78350f",
  },

  // Error/Danger
  error: {
    50: "#fef2f2",
    100: "#fee2e2",
    200: "#fecaca",
    300: "#fca5a5",
    400: "#f87171",
    500: "#ef4444",
    600: "#dc2626",
    700: "#b91c1c",
    800: "#991b1b",
    900: "#7f1d1d",
  },

  // Neutrals
  neutral: {
    0: "#ffffff",
    50: "#f8fafb",
    100: "#f0f4f8",
    150: "#e7ecf1",
    200: "#dfe6ed",
    300: "#cbd5e0",
    400: "#a0aec0",
    500: "#718096",
    600: "#4a5568",
    700: "#2d3748",
    800: "#1a202c",
    900: "#171923",
    950: "#0a0e14",
  },

  // Semantic colors
  text: {
    primary: "#10243e",
    secondary: "#4c6480",
    tertiary: "#718096",
    inverse: "#ffffff",
    link: "#1762bf",
    linkHover: "#0f4c81",
  },

  bg: {
    primary: "#ffffff",
    secondary: "#f8fafb",
    tertiary: "#f0f4f8",
    muted: "#fbfdff",
    hover: "#f0f7ff",
    active: "#e8f2ff",
  },

  border: {
    light: "#e7ecf1",
    default: "#d7e5f5",
    medium: "#c6d7eb",
    strong: "#a0aec0",
  },
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  fontFamily: {
    base: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    mono: "source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace",
  },

  fontSize: {
    xs: "0.75rem",    // 12px
    sm: "0.875rem",   // 14px
    base: "1rem",     // 16px
    lg: "1.125rem",   // 18px
    xl: "1.25rem",    // 20px
    "2xl": "1.5rem",  // 24px
    "3xl": "1.875rem",// 30px
    "4xl": "2.25rem", // 36px
    "5xl": "3rem",    // 48px
  },

  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },

  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },

  letterSpacing: {
    tighter: "-0.05em",
    tight: "-0.025em",
    normal: "0",
    wide: "0.025em",
    wider: "0.05em",
    widest: "0.1em",
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
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  none: "0",
  sm: "0.375rem",   // 6px
  base: "0.5rem",   // 8px
  md: "0.625rem",   // 10px
  lg: "0.75rem",    // 12px
  xl: "1rem",       // 16px
  "2xl": "1.25rem", // 20px
  full: "9999px",
};

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  none: "none",
  xs: "0 1px 2px 0 rgba(0, 32, 67, 0.05)",
  sm: "0 1px 3px 0 rgba(0, 32, 67, 0.1), 0 1px 2px 0 rgba(0, 32, 67, 0.06)",
  base: "0 4px 6px -1px rgba(0, 32, 67, 0.1), 0 2px 4px -1px rgba(0, 32, 67, 0.06)",
  md: "0 10px 15px -3px rgba(0, 32, 67, 0.1), 0 4px 6px -2px rgba(0, 32, 67, 0.05)",
  lg: "0 14px 24px -4px rgba(0, 32, 67, 0.1), 0 8px 10px -4px rgba(0, 32, 67, 0.04)",
  xl: "0 20px 25px -5px rgba(0, 32, 67, 0.1), 0 10px 10px -5px rgba(0, 32, 67, 0.04)",
  "2xl": "0 25px 50px -12px rgba(0, 32, 67, 0.25)",
  inner: "inset 0 2px 4px 0 rgba(0, 32, 67, 0.06)",
  focus: "0 0 0 3px rgba(31, 118, 216, 0.22)",
};

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const breakpoints = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
};

// ============================================================================
// TRANSITION
// ============================================================================

export const transition = {
  fast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  base: "200ms cubic-bezier(0.4, 0, 0.2, 1)",
  slow: "300ms cubic-bezier(0.4, 0, 0.2, 1)",
  slower: "500ms cubic-bezier(0.4, 0, 0.2, 1)",
};

// ============================================================================
// COMPONENT-SPECIFIC STYLES
// ============================================================================

export const components = {
  button: {
    primary: {
      base: {
        background: colors.primary[600],
        color: colors.neutral[0],
        border: "none",
        borderRadius: borderRadius.md,
        padding: `${spacing[2]} ${spacing[4]}`,
        fontWeight: typography.fontWeight.semibold,
        fontSize: typography.fontSize.sm,
        cursor: "pointer",
        transition: transition.base,
        boxShadow: shadows.sm,
      },
      hover: {
        background: colors.primary[700],
        boxShadow: shadows.md,
      },
      active: {
        background: colors.primary[800],
      },
      disabled: {
        opacity: 0.6,
        cursor: "not-allowed",
      },
    },
    secondary: {
      base: {
        background: colors.bg.active,
        color: colors.primary[700],
        border: `1px solid ${colors.border.medium}`,
        borderRadius: borderRadius.md,
        padding: `${spacing[2]} ${spacing[4]}`,
        fontWeight: typography.fontWeight.semibold,
        fontSize: typography.fontSize.sm,
        cursor: "pointer",
        transition: transition.base,
      },
      hover: {
        background: colors.bg.hover,
        borderColor: colors.primary[400],
      },
    },
    success: {
      base: {
        background: colors.success[600],
        color: colors.neutral[0],
        border: "none",
        borderRadius: borderRadius.md,
        padding: `${spacing[2]} ${spacing[4]}`,
        fontWeight: typography.fontWeight.bold,
        fontSize: typography.fontSize.sm,
        cursor: "pointer",
        transition: transition.base,
        boxShadow: shadows.sm,
      },
      hover: {
        background: colors.success[700],
        boxShadow: shadows.md,
      },
    },
    warning: {
      base: {
        background: colors.warning[50],
        color: colors.warning[800],
        border: `1px solid ${colors.warning[300]}`,
        borderRadius: borderRadius.md,
        padding: `${spacing[2]} ${spacing[4]}`,
        fontWeight: typography.fontWeight.semibold,
        fontSize: typography.fontSize.sm,
        cursor: "pointer",
        transition: transition.base,
      },
      hover: {
        background: colors.warning[100],
        borderColor: colors.warning[400],
      },
    },
  },

  input: {
    base: {
      width: "100%",
      height: "44px",
      borderRadius: borderRadius.md,
      border: `1px solid ${colors.border.medium}`,
      padding: `0 ${spacing[3]}`,
      fontSize: typography.fontSize.base,
      color: colors.text.primary,
      background: colors.bg.muted,
      transition: `border-color ${transition.fast}, box-shadow ${transition.fast}`,
      fontFamily: typography.fontFamily.base,
    },
    focus: {
      outline: "none",
      borderColor: colors.primary[500],
      boxShadow: shadows.focus,
      background: colors.neutral[0],
    },
    hover: {
      borderColor: colors.border.strong,
    },
    error: {
      borderColor: colors.error[500],
    },
  },

  card: {
    base: {
      background: colors.neutral[0],
      border: `1px solid ${colors.border.default}`,
      borderRadius: borderRadius.xl,
      padding: spacing[4],
      boxShadow: shadows.sm,
      transition: `box-shadow ${transition.base}, transform ${transition.base}`,
    },
    hover: {
      boxShadow: shadows.md,
      transform: "translateY(-1px)",
    },
    elevated: {
      boxShadow: shadows.lg,
    },
  },

  badge: {
    success: {
      background: colors.success[100],
      color: colors.success[800],
      border: `1px solid ${colors.success[300]}`,
      borderRadius: borderRadius.full,
      padding: `${spacing[1]} ${spacing[2]}`,
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.bold,
    },
    warning: {
      background: colors.warning[100],
      color: colors.warning[800],
      border: `1px solid ${colors.warning[300]}`,
      borderRadius: borderRadius.full,
      padding: `${spacing[1]} ${spacing[2]}`,
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.bold,
    },
    error: {
      background: colors.error[100],
      color: colors.error[800],
      border: `1px solid ${colors.error[300]}`,
      borderRadius: borderRadius.full,
      padding: `${spacing[1]} ${spacing[2]}`,
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.bold,
    },
    info: {
      background: colors.primary[100],
      color: colors.primary[800],
      border: `1px solid ${colors.primary[300]}`,
      borderRadius: borderRadius.full,
      padding: `${spacing[1]} ${spacing[2]}`,
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.bold,
    },
  },
};

// ============================================================================
// GRADIENTS
// ============================================================================

export const gradients = {
  primary: `linear-gradient(135deg, ${colors.primary[900]} 0%, ${colors.primary[700]} 52%, ${colors.primary[600]} 100%)`,
  dashboard: `linear-gradient(180deg, ${colors.neutral[100]} 0%, ${colors.neutral[50]} 45%, ${colors.neutral[100]} 100%)`,
  hero: `linear-gradient(140deg, ${colors.brand.navy} 0%, ${colors.primary[600]} 100%)`,
  subtle: `linear-gradient(to bottom, ${colors.bg.secondary}, ${colors.bg.tertiary})`,
};

// ============================================================================
// ACCESSIBILITY
// ============================================================================

export const a11y = {
  // Focus visible styles for keyboard navigation
  focusRing: {
    outline: "none",
    boxShadow: shadows.focus,
    borderColor: colors.primary[500],
  },

  // Skip to main content link
  skipLink: {
    position: "absolute",
    left: "-9999px",
    zIndex: 999,
    padding: spacing[2],
    background: colors.brand.navy,
    color: colors.neutral[0],
    textDecoration: "none",
    borderRadius: borderRadius.base,
  },

  // High contrast mode support
  highContrast: {
    border: "1px solid currentColor",
  },
};
