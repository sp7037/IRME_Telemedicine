import React from "react";
import theme from "../../theme/tokens";

/**
 * Card component for content grouping
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {React.CSSProperties} props.style
 * @param {boolean} props.hoverable - Add hover effect
 * @param {string} props.padding - Padding size: "none" | "sm" | "md" | "lg"
 */
const Card = ({
  children,
  style = {},
  hoverable = false,
  padding = "md",
  className = "",
  onClick,
  ...rest
}) => {
  const paddingValues = {
    none: "0",
    sm: theme.spacing[4],
    md: theme.spacing[6],
    lg: theme.spacing[8],
  };

  const baseStyles = {
    backgroundColor: theme.colors.background.primary,
    borderRadius: theme.radii.lg,
    boxShadow: theme.shadows.md,
    padding: paddingValues[padding],
    transition: `all ${theme.transitions.base}`,
    ...(onClick ? { cursor: "pointer" } : {}),
    ...style,
  };

  const handleMouseEnter = (e) => {
    if (hoverable) {
      e.currentTarget.style.boxShadow = theme.shadows.lg;
      e.currentTarget.style.transform = "translateY(-2px)";
    }
  };

  const handleMouseLeave = (e) => {
    if (hoverable) {
      e.currentTarget.style.boxShadow = theme.shadows.md;
      e.currentTarget.style.transform = "translateY(0)";
    }
  };

  return (
    <div
      style={baseStyles}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      className={className}
      {...rest}
    >
      {children}
    </div>
  );
};

export default Card;
