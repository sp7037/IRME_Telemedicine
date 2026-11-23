import React, { useEffect } from "react";
import { BRAND_NAVY, BRAND_TEAL } from "../../constants/brandTheme";

/**
 * Centered persistent prompt modal for consultation flow actions.
 * Stays until the user chooses an action or dismisses (if onClose provided).
 */
export default function ConsultationPromptModal({
  open,
  title,
  message,
  preview,
  pulse = false,
  actions = [],
  onClose,
  role = "alertdialog",
}) {
  useEffect(() => {
    if (!open || !pulse || typeof document === "undefined") return undefined;
    const el = document.getElementById("consultation-prompt-pulse");
    if (!el) return undefined;
    el.classList.remove("consultation-prompt-pulse-anim");
    // Force reflow so animation restarts
    void el.offsetWidth;
    el.classList.add("consultation-prompt-pulse-anim");
    return undefined;
  }, [open, pulse, title]);

  if (!open) return null;

  return (
    <div style={styles.overlay} role={role} aria-modal="true" aria-labelledby="consultation-prompt-title">
      <div style={styles.modal} id="consultation-prompt-pulse">
        {pulse ? <div style={styles.pulseRing} aria-hidden="true" /> : null}
        <h2 id="consultation-prompt-title" style={styles.title}>
          {title}
        </h2>
        {message ? <p style={styles.message}>{message}</p> : null}
        {preview ? (
          <blockquote style={styles.preview}>
            <div style={styles.previewLabel}>Latest message</div>
            <div style={styles.previewText}>{preview}</div>
          </blockquote>
        ) : null}
        <div style={styles.actions}>
          {actions.map((action) => (
            <button
              key={action.key || action.label}
              type="button"
              disabled={action.disabled || action.busy}
              onClick={action.onClick}
              style={{
                ...styles.btnBase,
                ...(action.variant === "primary"
                  ? styles.primaryBtn
                  : action.variant === "danger"
                    ? styles.dangerBtn
                    : styles.secondaryBtn),
                ...(action.disabled || action.busy ? styles.btnDisabled : {}),
              }}
            >
              {action.busy ? "Working…" : action.label}
            </button>
          ))}
          {onClose ? (
            <button type="button" onClick={onClose} style={{ ...styles.btnBase, ...styles.tertiaryBtn }}>
              Close
            </button>
          ) : null}
        </div>
      </div>
      <style>{`
        @keyframes consultationPromptPulse {
          0% { box-shadow: 0 0 0 0 rgba(19, 168, 158, 0.45); }
          70% { box-shadow: 0 0 0 16px rgba(19, 168, 158, 0); }
          100% { box-shadow: 0 0 0 0 rgba(19, 168, 158, 0); }
        }
        .consultation-prompt-pulse-anim {
          animation: consultationPromptPulse 1.4s ease-out 2;
        }
      `}</style>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(11, 37, 69, 0.45)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1200,
    padding: 16,
  },
  modal: {
    position: "relative",
    width: "100%",
    maxWidth: 440,
    background: "#fff",
    borderRadius: 16,
    padding: "22px 20px 18px",
    boxShadow: "0 20px 40px rgba(11, 37, 69, 0.25)",
    border: "1px solid #d7e5f5",
  },
  pulseRing: {
    position: "absolute",
    top: 12,
    right: 12,
    width: 12,
    height: 12,
    borderRadius: "50%",
    background: BRAND_TEAL,
  },
  title: {
    margin: "0 0 10px",
    color: BRAND_NAVY,
    fontSize: "1.2rem",
    fontWeight: 700,
    lineHeight: 1.3,
  },
  message: {
    margin: "0 0 14px",
    color: "#304860",
    fontSize: "0.98rem",
    lineHeight: 1.45,
  },
  preview: {
    margin: "0 0 16px",
    padding: "12px 14px",
    background: "#f5faf9",
    borderLeft: `3px solid ${BRAND_TEAL}`,
    borderRadius: 8,
  },
  previewLabel: {
    fontSize: 12,
    fontWeight: 700,
    color: "#4c6480",
    marginBottom: 4,
  },
  previewText: {
    color: BRAND_NAVY,
    fontSize: "0.95rem",
    lineHeight: 1.4,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  actions: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  btnBase: {
    borderRadius: 10,
    padding: "12px 16px",
    fontSize: "0.98rem",
    fontWeight: 600,
    cursor: "pointer",
    border: "none",
  },
  primaryBtn: {
    background: `linear-gradient(135deg, ${BRAND_NAVY} 0%, ${BRAND_TEAL} 100%)`,
    color: "#fff",
  },
  secondaryBtn: {
    background: "#fff",
    color: BRAND_NAVY,
    border: `2px solid ${BRAND_NAVY}`,
  },
  dangerBtn: {
    background: "#fff5f5",
    color: "#8a1f1f",
    border: "1px solid #fecaca",
  },
  tertiaryBtn: {
    background: "transparent",
    color: "#4c6480",
    border: "1px solid #d7e5f5",
  },
  btnDisabled: {
    opacity: 0.55,
    cursor: "not-allowed",
  },
};
