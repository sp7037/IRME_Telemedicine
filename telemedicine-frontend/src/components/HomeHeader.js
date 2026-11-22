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
    gap: "16px",
    padding: "20px 28px",
    backgroundColor: BRAND_NAVY,
    color: "#ffffff",
    borderBottom: "3px solid #1f76d8",
  },
  brandLink: {
    textDecoration: "none",
    color: "inherit",
  },
  brandBlock: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    alignItems: "flex-start",
  },
  brandLogo: {
    display: "block",
    height: "48px",
    width: "auto",
    maxWidth: "min(380px, 85vw)",
    objectFit: "contain",
  },
  tagline: {
    margin: 0,
    fontSize: "13px",
    opacity: 0.95,
  },
  topActions: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
  },
  ghostButton: {
    color: "#ffffff",
    textDecoration: "none",
    border: "1px solid rgba(255, 255, 255, 0.5)",
    borderRadius: "8px",
    padding: "8px 12px",
    fontSize: "13px",
    fontWeight: 600,
  },
};

export default HomeHeader;
