import React from "react";
import { Link } from "react-router-dom";
import { BRAND_HORIZONTAL_LOGO_PNG } from "../constants/brandAssets";
import { BRAND_NAVY } from "../constants/brandTheme";

/**
 * Public marketing header — matches Home.js IRME topbar for consistent branding.
 */
const HomeHeader = () => {
  return (
    <header style={styles.topbar}>
      <Link to="/" style={styles.brandLink}>
        <div style={styles.brandBlock}>
          <img
            src={BRAND_HORIZONTAL_LOGO_PNG}
            alt="IRME Institute — Telemedicine"
            style={styles.brandLogo}
          />
          <p style={styles.tagline}>
            Rural India Deserves Best Medical Health Services
          </p>
        </div>
      </Link>
      <div style={styles.topActions}>
        <Link to="/login" style={styles.ghostButton}>
          Patient Login
        </Link>
        <Link to="/login" style={styles.ghostButton}>
          Doctor Login
        </Link>
        <Link to="/login" style={styles.ghostButton}>
          TMC Login
        </Link>
      </div>
    </header>
  );
};

const styles = {
  topbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "20px",
    padding: "24px 32px",
    backgroundColor: BRAND_NAVY,
    color: "#ffffff",
    borderBottom: "3px solid #1f76d8",
    boxShadow: "0 2px 8px rgba(0, 32, 67, 0.15)",
  },
  brandLink: {
    textDecoration: "none",
    color: "inherit",
    transition: "opacity 150ms ease",
  },
  brandBlock: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    alignItems: "flex-start",
  },
  brandLogo: {
    display: "block",
    height: "52px",
    width: "auto",
    maxWidth: "min(400px, 85vw)",
    objectFit: "contain",
  },
  tagline: {
    margin: 0,
    fontSize: "14px",
    opacity: 0.92,
    letterSpacing: "0.01em",
    fontWeight: 500,
  },
  topActions: {
    display: "flex",
    flexWrap: "wrap",
    gap: "12px",
    alignItems: "center",
  },
  ghostButton: {
    color: "#ffffff",
    textDecoration: "none",
    border: "1px solid rgba(255, 255, 255, 0.4)",
    borderRadius: "10px",
    padding: "10px 16px",
    fontSize: "14px",
    fontWeight: 600,
    transition: "background 150ms ease, border-color 150ms ease",
    backgroundColor: "rgba(255, 255, 255, 0.05)",
  },
};

export default HomeHeader;
