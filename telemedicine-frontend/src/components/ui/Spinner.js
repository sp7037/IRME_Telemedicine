import React from "react";
import theme from "../../theme/tokens";

/**
 * Loading spinner component
 * 
 * @param {Object} props
 * @param {"sm"|"md"|"lg"} props.size
 * @param {string} props.color
 */
const Spinner = ({ size = "md", color, style = {}, className = "" }) => {
  const sizeValues = {
    sm: "20px",
    md: "40px",
    lg: "60px",
  };

  const spinnerColor = color || theme.colors.primary;

  const spinnerStyles = {
    width: sizeValues[size],
    height: sizeValues[size],
    border: `3px solid ${theme.colors.gray[200]}`,
    borderTopColor: spinnerColor,
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    ...style,
  };

  return (
    <>
      <style>
        {`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}
      </style>
      <div style={spinnerStyles} className={className} role="status" aria-label="Loading" />
    </>
  );
};

export default Spinner;
