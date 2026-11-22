import React, { useEffect } from "react";
import theme from "../../theme/tokens";

/**
 * Modal dialog component
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Function} props.onClose
 * @param {string} props.title
 * @param {React.ReactNode} props.children
 * @param {React.ReactNode} props.footer
 * @param {"sm"|"md"|"lg"|"xl"} props.size
 */
const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
  style = {},
  className = "",
  ...rest
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeStyles = {
    sm: { maxWidth: "400px" },
    md: { maxWidth: "600px" },
    lg: { maxWidth: "800px" },
    xl: { maxWidth: "1200px" },
  };

  const backdropStyles = {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: theme.colors.background.overlay,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: theme.zIndex.modal,
    padding: theme.spacing[4],
    overflowY: "auto",
  };

  const modalStyles = {
    backgroundColor: theme.colors.background.primary,
    borderRadius: theme.radii.lg,
    boxShadow: theme.shadows["2xl"],
    width: "100%",
    ...sizeStyles[size],
    maxHeight: "90vh",
    display: "flex",
    flexDirection: "column",
    ...style,
  };

  const headerStyles = {
    padding: theme.spacing[6],
    borderBottom: `1px solid ${theme.colors.border.light}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  };

  const titleStyles = {
    fontSize: theme.typography.fontSize["2xl"],
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    margin: 0,
  };

  const closeButtonStyles = {
    background: "none",
    border: "none",
    fontSize: theme.typography.fontSize["2xl"],
    cursor: "pointer",
    color: theme.colors.text.secondary,
    padding: theme.spacing[2],
    lineHeight: 1,
    transition: `color ${theme.transitions.fast}`,
  };

  const bodyStyles = {
    padding: theme.spacing[6],
    overflowY: "auto",
    flex: 1,
  };

  const footerStyles = {
    padding: theme.spacing[6],
    borderTop: `1px solid ${theme.colors.border.light}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: theme.spacing[3],
  };

  return (
    <div
      style={backdropStyles}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div style={modalStyles} className={className} role="dialog" aria-modal="true" {...rest}>
        <div style={headerStyles}>
          {title && <h2 style={titleStyles}>{title}</h2>}
          <button
            type="button"
            style={closeButtonStyles}
            onClick={onClose}
            onMouseEnter={(e) => (e.target.style.color = theme.colors.text.primary)}
            onMouseLeave={(e) => (e.target.style.color = theme.colors.text.secondary)}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div style={bodyStyles}>{children}</div>
        {footer && <div style={footerStyles}>{footer}</div>}
      </div>
    </div>
  );
};

export default Modal;
