import React from "react";

export function postponementOutcome(consultation, role = "patient") {
  if (consultation?.status !== "REJECTED_BY_PATIENT") return null;
  const result = consultation.wallet_return || {};
  const body = role === "doctor"
    ? "The patient declined your proposed time. This consultation request is closed."
    : "You rejected the doctor's proposed time. You can search for another doctor or send a new request to this doctor when available.";
  const payment = result.status === "RETURNED"
    ? `Rs ${result.amount} returned to the ${result.destination}. Reference: ${result.reference}.`
    : result.status === "NO_CHARGE" ? "No consultation amount was charged."
      : "The payment/quota outcome requires administrator review; a refund has not been confirmed.";
  return { title: role === "doctor" ? "Patient declined the proposed time" : "Proposed time rejected", body: `${body} ${payment}` };
}

export default function PostponementOutcome({ consultation, role }) {
  const outcome = postponementOutcome(consultation, role);
  if (!outcome) return null;
  return <section role="status" aria-live="polite" style={{ padding: 16, margin: "16px 0", border: "1px solid #bad3f0", borderRadius: 12, background: "#eef6ff" }}>
    <strong>{outcome.title} · Consultation #{consultation.id}</strong>
    <p>{outcome.body}</p>
    <p>This record remains in consultation history.</p>
  </section>;
}
