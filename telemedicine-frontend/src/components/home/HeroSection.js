import React from "react";
import { Link } from "react-router-dom";
import { SITE_CTA_GREEN } from "../../constants/brandTheme";
import {
  HOME_JOIN_DOCTOR,
  HOME_TMC_JOIN,
  HOME_JOIN_HUB,
} from "../../constants/homeRoutes";

const publicBase = process.env.PUBLIC_URL || "";
const HERO_IMAGE_SRC = `${publicBase}/Hero_Image_TMC.png`;

const floatCards = [
  { title: "Verified Doctors", subtitle: "Clinical care through digital channels" },
  { title: "Assisted TMC Visit", subtitle: "Local support for teleconsultation" },
  { title: "Rural Healthcare Support", subtitle: "Dignity, guidance, and access" },
  { title: "Digital Consultation", subtitle: "Video, records, and follow-up" },
];

const btnPrimary = {
  textDecoration: "none",
  backgroundColor: SITE_CTA_GREEN,
  color: "#ffffff",
  fontWeight: 600,
  padding: "14px 24px",
  borderRadius: "10px",
  fontSize: "16px",
  display: "inline-block",
  border: "none",
  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.15)",
  transition: "background 150ms ease, box-shadow 150ms ease",
};

const btnGhost = {
  textDecoration: "none",
  border: "2px solid rgba(255,255,255,0.8)",
  color: "#ffffff",
  fontWeight: 600,
  padding: "12px 22px",
  borderRadius: "10px",
  fontSize: "16px",
  display: "inline-block",
  background: "rgba(255,255,255,0.1)",
  transition: "background 150ms ease, border-color 150ms ease",
};

const HeroSection = () => (
  <section className="home-hero-shell" aria-labelledby="home-hero-heading">
    <div className="home-hero-split">
      <div className="home-hero-split__content home-hero-split__content--gradient">
        <div className="home-hero-split__inner">
          <h1
            id="home-hero-heading"
            style={{
              margin: 0,
              fontSize: "clamp(1.75rem, 5vw, 2.5rem)",
              lineHeight: 1.2,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              textShadow: "0 1px 2px rgba(0,0,0,0.1)",
            }}
          >
            Strengthening Rural Healthcare Through Telemedicine Centers
          </h1>
          <p
            style={{
              marginTop: "20px",
              fontSize: "clamp(16px, 2.5vw, 18px)",
              lineHeight: 1.65,
              maxWidth: "36rem",
              opacity: 0.95,
              textShadow: "0 1px 2px rgba(0,0,0,0.08)",
              fontWeight: 400,
            }}
          >
            IRME Telemedicine connects patients with verified doctors through assisted{" "}
            <strong>Telemedicine Centers (TMCs)</strong>, helping rural and semi-urban communities
            access healthcare with dignity, guidance, and digital support.
          </p>
          <div
            style={{
              marginTop: "28px",
              display: "flex",
              flexWrap: "wrap",
              gap: "14px",
              alignItems: "center",
            }}
          >
            <Link
              to="/register/patient"
              className="site-cta-green home-hero-pulse"
              style={btnPrimary}
            >
              Start Consultation
            </Link>
            <Link to={HOME_TMC_JOIN} className="site-cta-ghost" style={btnGhost}>
              Become a Telemedicine Center
            </Link>
            <Link to={HOME_JOIN_DOCTOR} className="site-cta-ghost" style={btnGhost}>
              Join as Doctor
            </Link>
          </div>
          <p style={{ marginTop: "14px", fontSize: "13px", opacity: 0.9 }}>
            Already registered?{" "}
            <Link to="/login" style={{ color: "#a7f3d0", fontWeight: 700 }}>
              Sign in
            </Link>
            {" · "}
            <Link to={HOME_JOIN_HUB} style={{ color: "#bae6fd", fontWeight: 600 }}>
              Ways to join IRME
            </Link>
          </p>

          <div className="home-hero-mini-grid" aria-label="Key features">
            {floatCards.map((c) => (
              <div
                key={c.title}
                className="home-float-card home-card-lift"
                style={{
                  background: "rgba(255,255,255,0.12)",
                  border: "1px solid rgba(255,255,255,0.28)",
                  borderRadius: "14px",
                  padding: "12px 12px",
                  backdropFilter: "blur(6px)",
                }}
              >
                <p style={{ margin: 0, fontWeight: 800, fontSize: "14px" }}>{c.title}</p>
                <p
                  style={{
                    margin: "6px 0 0",
                    fontSize: "11px",
                    lineHeight: 1.45,
                    opacity: 0.9,
                  }}
                >
                  {c.subtitle}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="home-hero-split__media">
        <img
          className="home-hero-split__img"
          src={HERO_IMAGE_SRC}
          width={800}
          height={600}
          alt="Telemedicine center: staff assisting a patient with an online doctor consultation at IRME"
          loading="eager"
          decoding="async"
        />
        <div className="home-hero-split__scrim" aria-hidden="true" />
      </div>
    </div>
  </section>
);

export default HeroSection;
