import React from "react";
import theme from "../../theme/tokens";

/**
 * Button component with variants, sizes, and states
 * 
 * @param {Object} props
 * @param {"primary"|"secondary"|"success"|"danger"|"outline"|"ghost"} props.variant
 * @param {"sm"|"md"|"lg"} props.size
 * @param {boolean} props.fullWidth
 * @param {boolean} props.disabled
 * @param {boolean} props.loading
 * @param {React.ReactNode} props.children
 * @param {React.CSSProperties} props.style
 */
const Button = ({
  variant = "primary",
  size = "md",
  fullWidth = false,
  disabled = false,
  loading = false,
  children,
  onClick,
  type = "button",
  style = {},
  className = "",
  ...rest
}) => {
  const baseStyles = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing[2],
    fontFamily: theme.typography.fontFamily.base,
    fontWeight: theme.typography.fontWeight.semibold,
    borderRadius: theme.radii.md,
    border: "none",
    cursor: disabled || loading ? "not-allowed" : "pointer",
    transition: `all ${theme.transitions.fast}`,
    textDecoration: "none",
    whiteSpace: "nowrap",
    opacity: disabled || loading ? 0.6 : 1,
    width: fullWidth ? "100%" : "auto",
    ...(disabled || loading ? { pointerEvents: "none" } : {}),
  };

  const variantStyles = {
    primary: {
      backgroundColor: theme.colors.primary,
      color: theme.colors.text.inverse,
      ":hover": {
        backgroundColor: "#1565c0",
      },
    },
    secondary: {
      backgroundColor: theme.colors.secondary,
      color: theme.colors.text.inverse,
      ":hover": {
        backgroundColor: "#0d3a6f",
      },
    },
    success: {
      backgroundColor: theme.colors.success,
      color: theme.colors.text.inverse,
      ":hover": {
        backgroundColor: "#16a34a",
      },
    },
    danger: {
      backgroundColor: theme.colors.error,
      color: theme.colors.text.inverse,
      ":hover": {
        backgroundColor: "#b91c1c",
      },
    },
    outline: {
      backgroundColor: "transparent",
      color: theme.colors.primary,
      border: `1px solid ${theme.colors.primary}`,
      ":hover": {
        backgroundColor: theme.colors.primary,
        color: theme.colors.text.inverse,
      },
    },
    ghost: {
      backgroundColor: "transparent",
      color: theme.colors.primary,
      ":hover": {
        backgroundColor: theme.colors.background.secondary,
      },
    },
  };

  const sizeStyles = {
    sm: {
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      fontSize: theme.typography.fontSize.sm,
      minHeight: "32px",
    },
    md: {
      padding: `${theme.spacing[3]} ${theme.spacing[5]}`,
      fontSize: theme.typography.fontSize.base,
      minHeight: "40px",
    },
    lg: {
      padding: `${theme.spacing[4]} ${theme.spacing[6]}`,
      fontSize: theme.typography.fontSize.lg,
      minHeight: "48px",
    },
  };

  const handleMouseEnter = (e) => {
    if (disabled || loading) return;
    const hoverStyle = variantStyles[variant][":hover"];
    if (hoverStyle) {
      Object.assign(e.target.style, hoverStyle);
    }
  };

  const handleMouseLeave = (e) => {
    if (disabled || loading) return;
    Object.assign(e.target.style, variantStyles[variant]);
  };

  const combinedStyles = {
    ...baseStyles,
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  };

  delete combinedStyles[":hover"];

  return (
    <button
      type={type}
      style={combinedStyles}
      onClick={onClick}
      disabled={disabled || loading}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={className}
      {...rest}
    >
      {loading && <span style={{ animation: "spin 1s linear infinite" }}>⏳</span>}
      {children}
    </button>
  );
};

export default Button;
