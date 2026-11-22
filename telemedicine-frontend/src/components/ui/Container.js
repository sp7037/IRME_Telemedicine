import React from "react";
import theme from "../../theme/tokens";

/**
 * Responsive container component with consistent max-width and padding
 * 
 * @param {Object} props
 * @param {"fluid"|"sm"|"md"|"lg"|"xl"} props.maxWidth
 * @param {boolean} props.centerContent
 * @param {React.ReactNode} props.children
 */
const Container = ({
  maxWidth = "lg",
  centerContent = false,
  children,
  style = {},
  className = "",
  ...rest
}) => {
  const maxWidthValues = {
    fluid: "100%",
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
  };

  const containerStyles = {
    width: "100%",
    maxWidth: maxWidthValues[maxWidth],
    marginLeft: "auto",
    marginRight: "auto",
    paddingLeft: theme.spacing[4],
    paddingRight: theme.spacing[4],
    boxSizing: "border-box",
    ...(centerContent
      ? {
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }
      : {}),
    ...style,
  };

  return (
    <div style={containerStyles} className={className} {...rest}>
      {children}
    </div>
  );
};

export default Container;
