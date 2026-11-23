import React from "react";

/**
 * Inline notification component to replace blocking browser alerts
 * Provides consistent, accessible, non-blocking feedback
 */
const InlineNotification = ({ type = "info", title, message, onDismiss, persistent = false, role = "status" }) => {
  const styles = getStyles(type);

  return (
    <div style={styles.container} role={role} aria-live={type === "error" ? "assertive" : "polite"}>
      <div style={styles.content}>
        {title && <div style={styles.title}>{title}</div>}
        {message && <div style={styles.message}>{message}</div>}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          style={styles.dismissBtn}
          aria-label="Dismiss notification"
        >
          ×
        </button>
      )}
    </div>
  );
};

const getStyles = (type) => {
  const baseStyles = {
    container: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start",
      gap: 12,
      padding: "12px 14px",
      borderRadius: 10,
      marginBottom: 14,
      border: "1px solid",
      fontFamily: "Segoe UI, system-ui, sans-serif",
    },
    content: {
      flex: 1,
      minWidth: 0,
    },
    title: {
      fontWeight: 800,
      marginBottom: 3,
      fontSize: 14,
    },
    message: {
      fontSize: 14,
      lineHeight: 1.4,
    },
    dismissBtn: {
      border: "1px solid rgba(18, 58, 111, 0.2)",
      background: "rgba(255,255,255,0.75)",
      borderRadius: 8,
      width: 28,
      height: 28,
      fontWeight: 800,
      cursor: "pointer",
      lineHeight: "24px",
      fontSize: 18,
      flexShrink: 0,
    },
  };

  const variants = {
    success: {
      container: {
        ...baseStyles.container,
        background: "#eef8f2",
        borderColor: "#acd9bf",
        color: "#123a2a",
      },
      dismissBtn: {
        ...baseStyles.dismissBtn,
        color: "#123a2a",
      },
    },
    error: {
      container: {
        ...baseStyles.container,
        background: "#fdeeee",
        borderColor: "#efb4b4",
        color: "#711f1f",
      },
      dismissBtn: {
        ...baseStyles.dismissBtn,
        color: "#711f1f",
      },
    },
    warning: {
      container: {
        ...baseStyles.container,
        background: "#fff8e8",
        borderColor: "#efcf88",
        color: "#624000",
      },
      dismissBtn: {
        ...baseStyles.dismissBtn,
        color: "#624000",
      },
    },
    urgent: {
      container: {
        ...baseStyles.container,
        background: "#fff1e8",
        borderColor: "#f0b27a",
        color: "#643000",
      },
      dismissBtn: {
        ...baseStyles.dismissBtn,
        color: "#643000",
      },
    },
    info: {
      container: {
        ...baseStyles.container,
        background: "#edf4fd",
        borderColor: "#c8ddf4",
        color: "#174577",
      },
      dismissBtn: {
        ...baseStyles.dismissBtn,
        color: "#174577",
      },
    },
  };

  const variant = variants[type] || variants.info;

  return {
    container: variant.container,
    content: baseStyles.content,
    title: baseStyles.title,
    message: baseStyles.message,
    dismissBtn: variant.dismissBtn,
  };
};

/**
 * Persistent action notification that stays visible on consultation card
 */
export const ActionNotification = ({ type = "info", title, message, action, onActionClick }) => {
  const styles = getStyles(type);

  return (
    <div style={{ ...styles.container, marginTop: 10 }} role="status" aria-live="polite">
      <div style={styles.content}>
        {title && <div style={styles.title}>{title}</div>}
        {message && <div style={styles.message}>{message}</div>}
      </div>
      {action && onActionClick && (
        <button
          type="button"
          onClick={onActionClick}
          style={{
            background: type === "error" ? "#b42318" : "#1762bf",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "6px 12px",
            fontWeight: 700,
            cursor: "pointer",
            flexShrink: 0,
            fontSize: 13,
          }}
        >
          {action}
        </button>
      )}
    </div>
  );
};

/**
 * Loading state indicator
 */
export const LoadingNotification = ({ message = "Loading..." }) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "12px 14px",
        borderRadius: 10,
        marginBottom: 14,
        background: "#f4f8fe",
        border: "1px solid #d7e5f5",
        color: "#4c6480",
        fontSize: 14,
      }}
      role="status"
      aria-live="polite"
    >
      <div
        style={{
          width: 16,
          height: 16,
          border: "2px solid #d7e5f5",
          borderTopColor: "#1762bf",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <div>{message}</div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

/**
 * Stale/offline indicator
 */
export const StaleNotification = ({ onRetry }) => {
  return (
    <InlineNotification
      type="warning"
      title="Updates paused"
      message="Background refresh failed. Data may be outdated."
      onDismiss={onRetry}
      persistent
    />
  );
};

export default InlineNotification;
