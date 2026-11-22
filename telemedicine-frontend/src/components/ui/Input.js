import React from "react";
import theme from "../../theme/tokens";

/**
 * Input component with consistent styling
 * 
 * @param {Object} props
 * @param {"text"|"email"|"password"|"number"|"tel"|"search"|"url"} props.type
 * @param {string} props.label
 * @param {string} props.error
 * @param {string} props.helperText
 * @param {boolean} props.required
 * @param {boolean} props.disabled
 * @param {boolean} props.fullWidth
 * @param {React.CSSProperties} props.style
 */
const Input = React.forwardRef(({
  type = "text",
  label,
  error,
  helperText,
  required = false,
  disabled = false,
  fullWidth = false,
  style = {},
  id,
  className = "",
  ...rest
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  const containerStyles = {
    display: "flex",
    flexDirection: "column",
    gap: theme.spacing[1],
    width: fullWidth ? "100%" : "auto",
  };

  const labelStyles = {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.medium,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing[1],
  };

  const inputStyles = {
    width: "100%",
    boxSizing: "border-box",
    height: "44px",
    borderRadius: theme.radii.md,
    border: `1px solid ${error ? theme.colors.error : theme.colors.border.medium}`,
    padding: `0 ${theme.spacing[4]}`,
    fontSize: theme.typography.fontSize.base,
    color: theme.colors.text.primary,
    backgroundColor: disabled ? theme.colors.background.secondary : theme.colors.background.primary,
    transition: `border-color ${theme.transitions.fast}, box-shadow ${theme.transitions.fast}`,
    fontFamily: theme.typography.fontFamily.base,
    opacity: disabled ? 0.6 : 1,
    cursor: disabled ? "not-allowed" : "text",
    ...style,
  };

  const errorStyles = {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.error,
    marginTop: theme.spacing[1],
  };

  const helperStyles = {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    marginTop: theme.spacing[1],
  };

  return (
    <div style={containerStyles} className={className}>
      {label && (
        <label htmlFor={inputId} style={labelStyles}>
          {label}
          {required && <span style={{ color: theme.colors.error }}> *</span>}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        type={type}
        disabled={disabled}
        style={inputStyles}
        onFocus={(e) => {
          e.target.style.outline = "none";
          e.target.style.borderColor = theme.colors.border.focus;
          e.target.style.boxShadow = theme.shadows.focus;
        }}
        onBlur={(e) => {
          e.target.style.borderColor = error ? theme.colors.error : theme.colors.border.medium;
          e.target.style.boxShadow = "none";
        }}
        {...rest}
      />
      {error && <span style={errorStyles}>{error}</span>}
      {helperText && !error && <span style={helperStyles}>{helperText}</span>}
    </div>
  );
});

Input.displayName = "Input";

export default Input;
