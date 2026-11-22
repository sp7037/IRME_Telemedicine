import React from "react";

export default function PatientBookingReview({ preview, busy, onConfirm, onCancel, onFunds }) {
  if (!preview) return null;
  return (
    <section aria-label="Review consultation payment" style={{ background: "white", border: "1px solid #bdd5ef", borderRadius: 16, padding: 20, marginBottom: 20 }}>
      <h3>Review consultation payment</h3>
      <p>Base fee: ₹{preview.base_fee} · Platform charge: ₹{preview.platform_fee}</p>
      <p><strong>Total: ₹{preview.total}</strong> · Available balance: ₹{preview.balance}</p>
      {!preview.can_request ? (
        <p role="alert">Low balance. Add ₹{preview.shortfall} before sending this request. No consultation has been booked or charged.</p>
      ) : <p>Confirm to pay ₹{preview.total} from your existing balance and send the consultation request. Doctor acceptance is still required.</p>}
      <p>The price and availability will be checked again when you confirm.</p>
      <button type="button" disabled={busy || !preview.can_request} onClick={onConfirm}>Confirm and request consultation</button>{" "}
      <button type="button" disabled={busy} onClick={onFunds}>Balance / add funds</button>{" "}
      <button type="button" disabled={busy} onClick={onCancel}>Cancel</button>
    </section>
  );
}
