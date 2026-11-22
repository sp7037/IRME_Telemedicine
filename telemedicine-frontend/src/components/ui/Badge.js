import React from "react";
import theme from "../../theme/tokens";

/**
 * Badge component for status indicators and labels
 * 
 * @param {Object} props
 * @param {"default"|"primary"|"success"|"warning"|"error"|"info"} props.variant
 * @param {"sm"|"md"|"lg"} props.size
 * @param {React.ReactNode} props.children
 */
const Badge = ({
  variant = "default",
  size = "md",
  children,
  style = {},
  className = "",
  ...rest
}) => {
  const variantStyles = {
    default: {
      backgroundColor: theme.colors.gray[200],
      color: theme.colors.gray[700],
    },
    primary: {
      backgroundColor: theme.colors.primary,
      color: theme.colors.text.inverse,
    },
    success: {
      backgroundColor: theme.colors.success,
      color: theme.colors.text.inverse,
    },
    warning: {
      backgroundColor: theme.colors.warning,
      color: "#ffffff",
    },
    error: {
      backgroundColor: theme.colors.error,
      color: theme.colors.text.inverse,
    },
    info: {
      backgroundColor: theme.colors.info,
      color: theme.colors.text.inverse,
    },
  };

  const sizeStyles = {
    sm: {
      padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
      fontSize: theme.typography.fontSize.xs,
    },
    md: {
      padding: `${theme.spacing[1]} ${theme.spacing[3]}`,
      fontSize: theme.typography.fontSize.sm,
    },
    lg: {
      padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
      fontSize: theme.typography.fontSize.base,
    },
  };

  const baseStyles = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: theme.typography.fontWeight.semibold,
    borderRadius: theme.radii.full,
    whiteSpace: "nowrap",
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  };

  return (
    <span style={baseStyles} className={className} {...rest}>
      {children}
    </span>
  );
};

export default Badge;
