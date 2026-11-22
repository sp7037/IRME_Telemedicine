import React from "react";
import theme from "../../theme/tokens";

/**
 * Alert component for messages and notifications
 * 
 * @param {Object} props
 * @param {"info"|"success"|"warning"|"error"} props.variant
 * @param {React.ReactNode} props.children
 * @param {boolean} props.dismissible
 * @param {Function} props.onDismiss
 */
const Alert = ({
  variant = "info",
  children,
  dismissible = false,
  onDismiss,
  style = {},
  className = "",
  ...rest
}) => {
  const variantStyles = {
    info: {
      backgroundColor: "#e0f2fe",
      color: "#0369a1",
      borderColor: "#7dd3fc",
    },
    success: {
      backgroundColor: "#dcfce7",
      color: "#15803d",
      borderColor: "#86efac",
    },
    warning: {
      backgroundColor: "#fef3c7",
      color: "#b45309",
      borderColor: "#fde047",
    },
    error: {
      backgroundColor: "#fee2e2",
      color: "#b91c1c",
      borderColor: "#fca5a5",
    },
  };

  const baseStyles = {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: theme.spacing[3],
    padding: theme.spacing[4],
    borderRadius: theme.radii.md,
    border: `1px solid ${variantStyles[variant].borderColor}`,
    backgroundColor: variantStyles[variant].backgroundColor,
    color: variantStyles[variant].color,
    fontSize: theme.typography.fontSize.sm,
    lineHeight: theme.typography.lineHeight.relaxed,
    ...style,
  };

  const dismissButtonStyles = {
    background: "none",
    border: "none",
    color: "inherit",
    cursor: "pointer",
    fontSize: theme.typography.fontSize.lg,
    padding: "0",
    marginLeft: theme.spacing[2],
    opacity: 0.7,
    transition: `opacity ${theme.transitions.fast}`,
  };

  return (
    <div style={baseStyles} role="alert" className={className} {...rest}>
      <div style={{ flex: 1 }}>{children}</div>
      {dismissible && (
        <button
          type="button"
          style={dismissButtonStyles}
          onClick={onDismiss}
          onMouseEnter={(e) => (e.target.style.opacity = 1)}
          onMouseLeave={(e) => (e.target.style.opacity = 0.7)}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
};

export default Alert;
