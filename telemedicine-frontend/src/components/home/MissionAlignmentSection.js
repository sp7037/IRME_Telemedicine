import React from "react";
import { SITE_HEADER_NAVY, SITE_DEEP_BLUE, SITE_TEAL } from "../../constants/brandTheme";

const base = process.env.PUBLIC_URL || "";

const MissionAlignmentSection = () => (
  <section
    className="home-section"
    style={{
      background: "linear-gradient(180deg, #ffffff 0%, #f0f9ff 100%)",
      borderRadius: "18px",
      padding: "clamp(22px, 4vw, 36px)",
      border: "1px solid #dbeafe",
      boxShadow: "0 8px 28px rgba(6, 43, 79, 0.08)",
    }}
    aria-labelledby="mission-heading"
  >
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "28px",
        alignItems: "center",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <img
          src={`${base}/eSanjeevaniLogo.svg`}
          alt="eSanjeevani National Telemedicine Service logo"
          style={{
            maxWidth: "min(280px, 85%)",
            height: "auto",
            margin: "0 auto",
            display: "block",
          }}
        />
      </div>
      <div>
        <h2
          id="mission-heading"
          style={{
            margin: "0 0 12px",
            fontSize: "clamp(1.25rem, 3vw, 1.6rem)",
            fontWeight: 800,
            color: SITE_HEADER_NAVY,
            lineHeight: 1.25,
          }}
        >
          Aligned with India&apos;s Digital Health Vision
        </h2>
        <p
          style={{
            margin: 0,
            fontSize: "1rem",
            lineHeight: 1.7,
            color: "#334155",
          }}
        >
          <strong>eSanjeevani – National Telemedicine Service of India</strong> is a step towards{" "}
          <strong>digital health equity</strong> and Universal Health Coverage (UHC). IRME
          Telemedicine <strong>supports</strong> this broader direction and is <strong>inspired by</strong>{" "}
          the mission of expanding telemedicine access. We promote <strong>assisted telemedicine</strong>{" "}
          through local <strong>Telemedicine Centers (TMCs)</strong>, especially for rural and semi-urban
          communities that benefit from guided digital consultations.
        </p>
        <p
          style={{
            margin: "16px 0 0",
            fontSize: "12px",
            lineHeight: 1.55,
            color: "#64748b",
            borderLeft: `3px solid ${SITE_TEAL}`,
            paddingLeft: "12px",
          }}
        >
          <strong>Disclaimer:</strong> IRME Telemedicine is an independent initiative and does{" "}
          <strong>not</strong> claim official affiliation with eSanjeevani or any government
          department unless specifically approved in writing.
        </p>
      </div>
    </div>
    <div
      style={{
        marginTop: "20px",
        height: "3px",
        borderRadius: "3px",
        background: `linear-gradient(90deg, ${SITE_HEADER_NAVY} 0%, ${SITE_DEEP_BLUE} 40%, #ea580c 85%, ${SITE_TEAL} 100%)`,
        opacity: 0.55,
      }}
      aria-hidden="true"
    />
  </section>
);

export default MissionAlignmentSection;
