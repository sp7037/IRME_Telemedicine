import React from "react";
import { Link } from "react-router-dom";
import { SITE_HEADER_NAVY, SITE_CTA_GREEN } from "../../constants/brandTheme";
import { HOME_TELEMED_COURSE } from "../../constants/homeRoutes";

const FinalCtaSection = () => (
  <section
    className="home-section"
    style={{
      textAlign: "center",
      background: "#ffffff",
      borderRadius: "18px",
      padding: "clamp(28px, 5vw, 48px) 20px",
      border: "1px solid #dbe7f3",
      boxShadow: "0 10px 28px rgba(6,43,79,0.09)",
    }}
    aria-labelledby="final-cta-heading"
  >
    <h2
      id="final-cta-heading"
      style={{
        margin: "0 0 10px",
        fontSize: "clamp(1.35rem, 3.5vw, 1.75rem)",
        fontWeight: 800,
        color: SITE_HEADER_NAVY,
      }}
    >
      Start Your Digital Healthcare Journey with IRME
    </h2>
    <p style={{ margin: "0 auto 22px", maxWidth: "560px", color: "#64748b", lineHeight: 1.65 }}>
      Choose consultation, center ownership, or learning—each path strengthens assisted telemedicine
      for rural India.
    </p>
    <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
      <Link
        to="/register/patient"
        className="site-cta-green"
        style={{
          textDecoration: "none",
          backgroundColor: SITE_CTA_GREEN,
          color: "#052e16",
          fontWeight: 800,
          padding: "14px 22px",
          borderRadius: "12px",
          fontSize: "15px",
        }}
      >
        Start Consultation
      </Link>
      <Link
        to="/register/tmc"
        style={{
          textDecoration: "none",
          border: `2px solid ${SITE_HEADER_NAVY}`,
          color: SITE_HEADER_NAVY,
          fontWeight: 800,
          padding: "12px 20px",
          borderRadius: "12px",
          fontSize: "15px",
        }}
      >
        Register TMC
      </Link>
      <Link
        to={HOME_TELEMED_COURSE}
        style={{
          textDecoration: "none",
          background: "#0f4c81",
          color: "#fff",
          fontWeight: 800,
          padding: "14px 22px",
          borderRadius: "12px",
          fontSize: "15px",
        }}
      >
        Join Course
      </Link>
    </div>
  </section>
);

export default FinalCtaSection;
