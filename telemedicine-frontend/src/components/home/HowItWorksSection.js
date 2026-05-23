import React from "react";
import { SITE_HEADER_NAVY } from "../../constants/brandTheme";

const StepIcon = ({ children }) => (
  <div className="home-step-icon" aria-hidden="true">
    {children}
  </div>
);

const steps = [
  {
    title: "Patient visits nearby TMC",
    body: "A local Telemedicine Center (TMC) offers a calm, assisted setting for care.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
      </svg>
    ),
  },
  {
    title: "TMC operator enters patient details",
    body: "Basic information is recorded with consent to prepare for consultation.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V8h16v10z" />
      </svg>
    ),
  },
  {
    title: "Doctor consults online",
    body: "A verified clinician connects for an assisted telemedicine session.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
        <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z" />
      </svg>
    ),
  },
  {
    title: "Prescription is prepared",
    body: "If medically appropriate, the clinician’s prescription or advice is documented and explained with TMC support.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.89 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z" />
      </svg>
    ),
  },
  {
    title: "Guidance and follow-up support",
    body: "The TMC can help explain instructions and arrange follow-up where appropriate.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
        <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.6202.02-.91.05 1.16.84 1.91 1.96 1.91 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
      </svg>
    ),
  },
];

const HowItWorksSection = () => (
  <section
    className="home-section"
    style={{
      background: "#fff",
      borderRadius: "18px",
      padding: "clamp(22px, 4vw, 34px)",
      border: "1px solid #e2e8f0",
      boxShadow: "0 8px 24px rgba(6,43,79,0.07)",
    }}
    aria-labelledby="how-heading"
  >
    <h2
      id="how-heading"
      style={{
        margin: "0 0 8px",
        fontSize: "clamp(1.3rem, 3vw, 1.7rem)",
        fontWeight: 800,
        color: SITE_HEADER_NAVY,
      }}
    >
      How assisted telemedicine works
    </h2>
    <p style={{ margin: "0 0 22px", color: "#64748b", maxWidth: "720px", lineHeight: 1.6 }}>
      A simple pathway from village to clinician—with human support at every step.
    </p>
    <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: "14px" }}>
      {steps.map((s, i) => (
        <li
          key={s.title}
          style={{
            display: "flex",
            gap: "16px",
            alignItems: "flex-start",
            padding: "16px 18px",
            borderRadius: "14px",
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
          }}
        >
          <StepIcon>{s.icon}</StepIcon>
          <div>
            <p style={{ margin: 0, fontWeight: 800, color: SITE_HEADER_NAVY }}>
              Step {i + 1}: {s.title}
            </p>
            <p style={{ margin: "6px 0 0", fontSize: "0.95rem", lineHeight: 1.55, color: "#475569" }}>
              {s.body}
            </p>
          </div>
        </li>
      ))}
    </ol>
  </section>
);

export default HowItWorksSection;
