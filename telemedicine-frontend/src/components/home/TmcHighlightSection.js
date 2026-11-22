import React from "react";
import { Link } from "react-router-dom";
import { SITE_HEADER_NAVY, SITE_CTA_GREEN } from "../../constants/brandTheme";
import { HOME_TMC_JOIN } from "../../constants/homeRoutes";

const cards = [
  {
    title: "Assist Patients",
    text: "Help patients who may struggle with mobile apps, online forms, video visits, or digital prescriptions—right at the TMC.",
  },
  {
    title: "Connect with Doctors",
    text: "Bridge patients to verified doctors for assisted teleconsultation and clearer medical guidance.",
  },
  {
    title: "Generate Prescriptions",
    text: "When the consulting clinician issues a prescription or care plan, the TMC helps the patient receive and understand it appropriately.",
  },
  {
    title: "Support Rural Families",
    text: "Offer a trusted local point for families who face distance, connectivity, or literacy barriers.",
  },
  {
    title: "Earn Through Consultations",
    text: "Where the platform model allows, TMCs may earn through consultation-related services—subject to verification and plan terms.",
  },
];

const TmcHighlightSection = () => (
  <section className="home-section" aria-labelledby="tmc-heading">
    <h2
      id="tmc-heading"
      style={{
        margin: "0 0 10px",
        fontSize: "clamp(1.35rem, 3.5vw, 1.85rem)",
        fontWeight: 800,
        color: SITE_HEADER_NAVY,
        lineHeight: 1.2,
      }}
    >
      Telemedicine Centers: The Backbone of Rural Digital Healthcare
    </h2>
    <p
      style={{
        margin: "0 0 22px",
        maxWidth: "820px",
        fontSize: "1.05rem",
        lineHeight: 1.65,
        color: "#475569",
      }}
    >
      Many rural patients are not comfortable using smartphones for healthcare alone. A{" "}
      <strong>Telemedicine Center (TMC)</strong> provides assisted telemedicine—helping with
      registration, consultation setup, understanding next steps, and digital health literacy—in a
      way that respects privacy and dignity.
    </p>
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        gap: "14px",
      }}
    >
      {cards.map((c) => (
        <article
          key={c.title}
          className="home-card-lift"
          style={{
            background: "#fff",
            borderRadius: "14px",
            padding: "18px 16px",
            border: "1px solid #dbe7f3",
            boxShadow: "0 6px 18px rgba(6,43,79,0.07)",
          }}
        >
          <h3 style={{ margin: "0 0 8px", fontSize: "1.05rem", color: SITE_HEADER_NAVY }}>
            {c.title}
          </h3>
          <p style={{ margin: 0, fontSize: "0.92rem", lineHeight: 1.55, color: "#64748b" }}>
            {c.text}
          </p>
        </article>
      ))}
    </div>
    <div style={{ marginTop: "22px", textAlign: "center" }}>
      <Link
        to={HOME_TMC_JOIN}
        className="site-cta-green"
        style={{
          display: "inline-block",
          textDecoration: "none",
          backgroundColor: SITE_CTA_GREEN,
          color: "#052e16",
          fontWeight: 800,
          padding: "14px 28px",
          borderRadius: "12px",
          fontSize: "15px",
        }}
      >
        Open Your TMC
      </Link>
    </div>
  </section>
);

export default TmcHighlightSection;
