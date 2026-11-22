import React from "react";
import { SITE_HEADER_NAVY, SITE_TEAL } from "../../constants/brandTheme";

const stats = [
  {
    title: "Rural Focus",
    text: "Designed around villages, small towns, and families who need care closer to home.",
  },
  {
    title: "Assisted Consultation",
    text: "Human support at the TMC so digital health does not leave anyone behind.",
  },
  {
    title: "Doctor Network",
    text: "Connecting communities with verified clinicians for teleconsultation where available.",
  },
];

const ImpactSection = () => (
  <section
    className="home-section"
    style={{
      background: `linear-gradient(135deg, ${SITE_HEADER_NAVY} 0%, #0c4a6e 55%, #0f766e 100%)`,
      color: "#fff",
      borderRadius: "18px",
      padding: "clamp(26px, 5vw, 42px)",
      boxShadow: "0 14px 36px rgba(6,43,79,0.25)",
    }}
    aria-labelledby="impact-heading"
  >
    <h2
      id="impact-heading"
      style={{
        margin: "0 0 12px",
        fontSize: "clamp(1.35rem, 3.5vw, 1.9rem)",
        fontWeight: 800,
        lineHeight: 1.2,
      }}
    >
      Bridging the Healthcare Gap Between Villages and Doctors
    </h2>
    <p
      style={{
        margin: "0 0 28px",
        fontSize: "1.05rem",
        lineHeight: 1.7,
        maxWidth: "820px",
        opacity: 0.94,
      }}
    >
      Many rural patients delay treatment because specialists, transport, and digital tools are not
      easily available. IRME Telemedicine aims to make consultation more reachable through trained
      local <strong>Telemedicine Centers (TMCs)</strong> that champion{" "}
      <strong>rural healthcare access</strong> and <strong>digital health equity</strong>—without replacing
      emergency or hospital care when it is needed.
    </p>
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "14px",
      }}
    >
      {stats.map((s) => (
        <div
          key={s.title}
          style={{
            background: "rgba(255,255,255,0.1)",
            border: "1px solid rgba(255,255,255,0.22)",
            borderRadius: "14px",
            padding: "20px 16px",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: "12px",
              fontWeight: 800,
              letterSpacing: "0.06em",
              color: SITE_TEAL,
            }}
          >
            {s.title}
          </p>
          <p style={{ margin: "10px 0 0", fontSize: "0.95rem", lineHeight: 1.55, opacity: 0.94 }}>
            {s.text}
          </p>
        </div>
      ))}
    </div>
  </section>
);

export default ImpactSection;
