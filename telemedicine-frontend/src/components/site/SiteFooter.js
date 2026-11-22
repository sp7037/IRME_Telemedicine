import React from "react";
import { Link } from "react-router-dom";
import { BRAND_LOGO_HORIZONTAL_WHITE } from "../../constants/brandAssets";
import { SITE_HEADER_NAVY, SITE_TEAL, BRAND_ACCENT } from "../../constants/brandTheme";

const footerColTitle = {
  margin: "0 0 12px",
  fontSize: "13px",
  fontWeight: 800,
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  color: "#99f6e4",
};

const linkStyle = {
  color: "#e0f2fe",
  textDecoration: "none",
  fontSize: "14px",
  display: "block",
  padding: "4px 0",
};

const SiteFooter = () => {
  return (
    <footer
      style={{
        backgroundColor: SITE_HEADER_NAVY,
        color: "#cfeffc",
        borderTop: `3px solid ${BRAND_ACCENT}`,
        marginTop: "auto",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "36px 20px 24px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "28px",
        }}
      >
        <div>
          <img
            src={BRAND_LOGO_HORIZONTAL_WHITE}
            alt="IRME Telemedicine"
            width="200"
            height="50"
            style={{
              height: "50px",
              width: "200px",
              objectFit: "contain",
              marginBottom: "12px",
            }}
          />
          <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.55, opacity: 0.92 }}>
            <strong style={{ color: "#fff" }}>IRME Telemedicine</strong> supports online
            consultation and assisted healthcare access across rural and urban communities.
          </p>
        </div>

        <div>
          <p style={footerColTitle}>Quick links</p>
          <Link to="/" className="site-footer-link" style={linkStyle}>
            Home
          </Link>
          <Link to="/tmc" className="site-footer-link" style={linkStyle}>
            Open Telemedicine Center
          </Link>
          <Link to="/telemedicine-course" className="site-footer-link" style={linkStyle}>
            Telemedicine Course
          </Link>
          <Link to="/join-irme" className="site-footer-link" style={linkStyle}>
            Join IRME
          </Link>
        </div>

        <div>
          <p style={footerColTitle}>Login</p>
          <Link to="/login" className="site-footer-link" style={linkStyle}>
            Patient Login
          </Link>
          <Link to="/login" className="site-footer-link" style={linkStyle}>
            Doctor Login
          </Link>
          <Link to="/login" className="site-footer-link" style={linkStyle}>
            TMC Login
          </Link>
        </div>

        <div>
          <p style={footerColTitle}>Join</p>
          <Link to="/join/doctor" className="site-footer-link" style={linkStyle}>
            Join as Doctor
          </Link>
          <Link to="/tmc" className="site-footer-link" style={linkStyle}>
            Join as Telemedicine Center
          </Link>
          <Link to="/telemedicine-assistant-course/uttar-pradesh/muzaffarnagar" className="site-footer-link" style={linkStyle}>
            Course in Muzaffarnagar
          </Link>
          <Link to="/register/patient" className="site-footer-link" style={linkStyle}>
            Start consultation
          </Link>
        </div>
      </div>

      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "0 20px 28px",
        }}
      >
        <p
          style={{
            margin: 0,
            padding: "14px 16px",
            backgroundColor: "rgba(20, 184, 166, 0.12)",
            border: `1px solid rgba(20, 184, 166, 0.35)`,
            borderRadius: "12px",
            fontSize: "13px",
            lineHeight: 1.55,
            color: "#ecfeff",
          }}
        >
          <strong style={{ color: SITE_TEAL }}>Important:</strong> IRME Telemedicine supports
          online consultation and assisted healthcare access.{" "}
          <strong>Emergency medical cases</strong> should be referred to nearby hospitals or
          emergency services without delay.
        </p>
        <p
          style={{
            textAlign: "center",
            margin: "18px 0 0",
            fontSize: "13px",
            opacity: 0.8,
          }}
        >
          &copy; {new Date().getFullYear()} IRME Institute. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export default SiteFooter;
