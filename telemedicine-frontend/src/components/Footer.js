import React from "react";
import { BRAND_NAVY, BRAND_NAVY_DEEP } from "../constants/brandTheme";

const Footer = () => {
  return (
    <footer style={styles.footer}>
      <div style={styles.inner}>
        <p style={styles.copy}>&copy; {new Date().getFullYear()} IRME Telemedicine. All rights reserved.</p>
        <p style={styles.support}>
          Support:{" "}
          <a href="mailto:support@irme.in" style={styles.a}>
            support@irme.in
          </a>
        </p>
      </div>
    </footer>
  );
};

const styles = {
  footer: {
    marginTop: "auto",
    background: `linear-gradient(180deg, ${BRAND_NAVY} 0%, ${BRAND_NAVY_DEEP} 100%)`,
    color: "rgba(255, 255, 255, 0.85)",
    borderTop: "2px solid rgba(31, 118, 216, 0.3)",
  },
  inner: {
    maxWidth: 1200,
    margin: "0 auto",
    padding: "20px 24px",
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    alignItems: "center",
    gap: "14px 28px",
    textAlign: "center",
    fontSize: "14px",
  },
  copy: { margin: 0, opacity: 0.9 },
  support: { margin: 0, opacity: 0.9 },
  a: {
    color: "#9ec9ff",
    fontWeight: 600,
    textDecoration: "none",
    transition: "color 150ms ease",
  },
};

export default Footer;
