import React from "react";
import { Link } from "react-router-dom";
import { SITE_HEADER_NAVY, SITE_CTA_GREEN } from "../../constants/brandTheme";
import {
  HOME_JOIN_DOCTOR,
  HOME_TMC_JOIN,
  HOME_TELEMED_COURSE,
} from "../../constants/homeRoutes";

const cards = [
  {
    title: "Join as Consultant Doctor",
    desc: "Offer professional online consultations within your scope of practice and platform verification.",
    benefits: [
      "Expanded reach for rural healthcare access",
      "Digital profile and consultation workflow",
      "Assisted telemedicine through TMC network",
    ],
    cta: "View doctor pathway",
    to: HOME_JOIN_DOCTOR,
  },
  {
    title: "Join as Telemedicine Center",
    desc: "Operate a local assisted telemedicine point for patients who need hands-on support with digital care.",
    benefits: [
      "Serve your community with dignity",
      "Platform training and onboarding guidance",
      "Possible consultation-linked income—subject to plan and verification",
    ],
    cta: "Explore TMC onboarding",
    to: HOME_TMC_JOIN,
  },
  {
    title: "Join Telemedicine Support Course",
    desc: "Build practical skills for assisted telemedicine operations and digital health support roles.",
    benefits: [
      "Baseline skills for TMC assistance",
      "Ethics, privacy, and patient communication",
      "Pathway clarity before formal admission",
    ],
    cta: "View course details",
    to: HOME_TELEMED_COURSE,
  },
];

const JoinIrmeSection = () => (
  <section className="home-section" aria-labelledby="join-irme-home-heading">
    <h2
      id="join-irme-home-heading"
      style={{
        margin: "0 0 8px",
        fontSize: "clamp(1.3rem, 3vw, 1.7rem)",
        fontWeight: 800,
        color: SITE_HEADER_NAVY,
      }}
    >
      Join the IRME rural digital health movement
    </h2>
    <p style={{ margin: "0 0 22px", color: "#64748b", maxWidth: "720px", lineHeight: 1.65 }}>
      Choose the role that matches you. All paths are subject to verification and platform policy.
    </p>
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "18px",
      }}
    >
      {cards.map((c) => (
        <article
          key={c.title}
          className="home-card-lift"
          style={{
            background: "#fff",
            borderRadius: "16px",
            padding: "22px 20px",
            border: "1px solid #dbe7f3",
            boxShadow: "0 8px 22px rgba(6,43,79,0.08)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <h3 style={{ margin: "0 0 10px", fontSize: "1.12rem", color: SITE_HEADER_NAVY }}>
            {c.title}
          </h3>
          <p style={{ margin: "0 0 12px", fontSize: "0.95rem", lineHeight: 1.55, color: "#475569" }}>
            {c.desc}
          </p>
          <p style={{ margin: "0 0 6px", fontSize: "12px", fontWeight: 800, color: SITE_HEADER_NAVY }}>
            Benefits
          </p>
          <ul style={{ margin: "0 0 18px", paddingLeft: "1.1rem", color: "#64748b", fontSize: "0.9rem" }}>
            {c.benefits.map((b) => (
              <li key={b} style={{ marginBottom: "6px" }}>
                {b}
              </li>
            ))}
          </ul>
          <Link
            to={c.to}
            className="site-cta-green"
            style={{
              marginTop: "auto",
              textAlign: "center",
              textDecoration: "none",
              backgroundColor: SITE_CTA_GREEN,
              color: "#052e16",
              fontWeight: 800,
              padding: "12px 16px",
              borderRadius: "10px",
              fontSize: "14px",
            }}
          >
            {c.cta}
          </Link>
        </article>
      ))}
    </div>
  </section>
);

export default JoinIrmeSection;
