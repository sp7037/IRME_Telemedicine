import React from "react";
import { BRAND_NAVY, BRAND_TEAL } from "../../constants/brandTheme";

/**
 * Payment review card shown after "Review fee & consult".
 * Money values and API callbacks come from `preview`; doctor display comes from the
 * doctor card the patient already selected (not from the preview endpoint).
 */
export default function PatientBookingReview({ preview, doctor, busy, onConfirm, onCancel, onFunds }) {
  if (!preview) return null;

  const firstName = doctor?.first_name || "";
  const lastName = doctor?.last_name || "";
  const doctorName = doctor
    ? `Dr. ${firstName} ${lastName}`.trim()
    : preview.doctor_name || "Doctor";
  const doctorSpecialty = doctor?.specialty || doctor?.specialization || "";
  const doctorPhoto = doctor?.photo || null;
  const initial = (firstName || lastName || doctorName.replace(/^Dr\.\s*/i, "") || "D").charAt(0).toUpperCase();

  const baseFee = Number(preview.base_fee) || 0;
  const platformCharge = Number(preview.platform_fee) || 0;
  const total = Number(preview.total) || 0;
  const balance = Number(preview.balance) || 0;
  const balanceAfter = balance - total;
  const canRequest = preview.can_request === true;

  return (
    <section aria-label="Review consultation payment" style={styles.container}>
      <h3 style={styles.heading}>Review consultation payment</h3>

      <div style={styles.doctorSection}>
        {doctorPhoto ? (
          <img src={doctorPhoto} alt="" style={styles.doctorPhoto} />
        ) : (
          <div style={styles.doctorPhotoPlaceholder} aria-hidden="true">
            {initial}
          </div>
        )}
        <div style={styles.doctorInfo}>
          <div style={styles.doctorName}>{doctorName}</div>
          {doctorSpecialty ? <div style={styles.doctorSpecialty}>{doctorSpecialty}</div> : null}
        </div>
      </div>

      <div style={styles.feeBreakdown}>
        <div style={styles.feeRow}>
          <span>Base fee</span>
          <span style={styles.feeValue}>₹{preview.base_fee}</span>
        </div>
        <div style={styles.feeRow}>
          <span>Platform charge</span>
          <span style={styles.feeValue}>₹{preview.platform_fee}</span>
        </div>
        <div style={styles.feeDivider} />
        <div style={styles.feeRow}>
          <span style={styles.totalLabel}>Total</span>
          <span style={styles.totalValue}>₹{preview.total}</span>
        </div>
      </div>

      <div style={styles.balanceSection}>
        <div style={styles.balanceRow}>
          <span style={styles.balanceLabel}>Current balance</span>
          <span style={styles.balanceValue}>₹{preview.balance}</span>
        </div>
        <div style={styles.balanceRow}>
          <span style={styles.balanceLabel}>Balance after payment</span>
          <span style={{ ...styles.balanceValue, color: balanceAfter >= 0 ? "#17623c" : "#8a1f1f" }}>
            ₹{balanceAfter.toFixed(2)}
          </span>
        </div>
      </div>

      {!canRequest ? (
        <div style={styles.warningBox} role="alert">
          <strong>Low balance</strong>
          <p style={styles.warningText}>
            Add ₹{preview.shortfall} before sending this request. No consultation has been booked or charged.
          </p>
        </div>
      ) : (
        <div style={styles.infoBox}>
          <p style={styles.infoText}>
            Confirm to pay <strong>₹{preview.total}</strong> from your existing balance and send the consultation
            request.
          </p>
          <p style={styles.noteText}>
            <strong>Note:</strong> Doctor acceptance is still required. The price and availability will be checked
            again when you confirm.
          </p>
        </div>
      )}

      <div style={styles.buttonGroup}>
        <button
          type="button"
          disabled={busy || !canRequest}
          onClick={onConfirm}
          style={{
            ...styles.primaryBtn,
            ...(busy || !canRequest ? styles.btnDisabled : {}),
          }}
        >
          {busy ? "Processing…" : "Confirm and request consultation"}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onFunds}
          style={{ ...styles.secondaryBtn, ...(busy ? styles.btnDisabled : {}) }}
        >
          Add funds
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onCancel}
          style={{ ...styles.tertiaryBtn, ...(busy ? styles.btnDisabled : {}) }}
        >
          Cancel
        </button>
      </div>
    </section>
  );
}

const styles = {
  container: {
    background: "white",
    border: "1px solid #d7e5f5",
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    boxShadow: "0 4px 6px -1px rgba(0, 32, 67, 0.08), 0 2px 4px -1px rgba(0, 32, 67, 0.04)",
    maxWidth: "100%",
  },
  heading: {
    margin: "0 0 16px",
    color: BRAND_NAVY,
    fontSize: "1.25rem",
    fontWeight: 600,
  },
  doctorSection: {
    display: "flex",
    gap: 12,
    alignItems: "center",
    marginBottom: 16,
    padding: 14,
    background: "#f8fafb",
    borderRadius: 12,
  },
  doctorPhoto: {
    width: 56,
    height: 56,
    borderRadius: "50%",
    objectFit: "cover",
    border: `2px solid ${BRAND_TEAL}`,
    flexShrink: 0,
  },
  doctorPhotoPlaceholder: {
    width: 56,
    height: 56,
    borderRadius: "50%",
    background: `linear-gradient(135deg, ${BRAND_NAVY} 0%, ${BRAND_TEAL} 100%)`,
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "1.4rem",
    fontWeight: 600,
    flexShrink: 0,
  },
  doctorInfo: { flex: 1, minWidth: 0 },
  doctorName: {
    fontSize: "1.05rem",
    fontWeight: 600,
    color: BRAND_NAVY,
    marginBottom: 4,
  },
  doctorSpecialty: {
    fontSize: "0.9rem",
    color: "#4c6480",
  },
  feeBreakdown: {
    marginBottom: 14,
    padding: 14,
    background: "#fbfdff",
    borderRadius: 12,
    border: "1px solid #e7ecf1",
  },
  feeRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    padding: "8px 0",
    fontSize: "0.95rem",
    color: "#10243e",
  },
  feeValue: { fontWeight: 600, color: BRAND_NAVY },
  feeDivider: {
    height: 1,
    background: "#d7e5f5",
    margin: "4px 0",
  },
  totalLabel: {
    fontSize: "1.05rem",
    fontWeight: 700,
    color: BRAND_NAVY,
  },
  totalValue: {
    fontSize: "1.15rem",
    fontWeight: 700,
    color: BRAND_TEAL,
  },
  balanceSection: {
    marginBottom: 14,
    padding: 14,
    background: "#f0f8ff",
    borderRadius: 12,
    border: "1px solid #bdd5ef",
  },
  balanceRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    padding: "6px 0",
  },
  balanceLabel: { fontSize: "0.95rem", color: "#123a6f" },
  balanceValue: { fontSize: "1rem", fontWeight: 600, color: BRAND_NAVY },
  warningBox: {
    background: "#fff5f5",
    border: "1px solid #fecaca",
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  warningText: {
    color: "#8a1f1f",
    margin: "8px 0 0",
    fontSize: "0.95rem",
  },
  infoBox: {
    background: "#f0f8ff",
    border: "1px solid #bdd5ef",
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  infoText: {
    color: "#123a6f",
    margin: "0 0 8px",
    fontSize: "0.95rem",
  },
  noteText: {
    color: "#4c6480",
    margin: 0,
    fontSize: "0.85rem",
    lineHeight: 1.5,
  },
  buttonGroup: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  primaryBtn: {
    background: `linear-gradient(135deg, ${BRAND_NAVY} 0%, ${BRAND_TEAL} 100%)`,
    color: "white",
    border: "none",
    borderRadius: 10,
    padding: "14px 20px",
    fontSize: "1rem",
    fontWeight: 600,
    cursor: "pointer",
    boxShadow: "0 2px 4px rgba(11, 37, 69, 0.2)",
  },
  secondaryBtn: {
    background: "white",
    color: BRAND_NAVY,
    border: `2px solid ${BRAND_NAVY}`,
    borderRadius: 10,
    padding: "12px 20px",
    fontSize: "0.95rem",
    fontWeight: 600,
    cursor: "pointer",
  },
  tertiaryBtn: {
    background: "transparent",
    color: "#4c6480",
    border: "1px solid #d7e5f5",
    borderRadius: 10,
    padding: "12px 20px",
    fontSize: "0.95rem",
    fontWeight: 500,
    cursor: "pointer",
  },
  btnDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
};
