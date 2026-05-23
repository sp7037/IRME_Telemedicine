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
    color: "#cfe4ff",
    borderTop: "1px solid rgba(158, 201, 255, 0.2)",
  },
  inner: {
    maxWidth: 1200,
    margin: "0 auto",
    padding: "16px 20px",
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    alignItems: "center",
    gap: "12px 24px",
    textAlign: "center",
    fontSize: "clamp(12px, 2vw, 13px)",
  },
  copy: { margin: 0 },
  support: { margin: 0 },
  a: {
    color: "#9ec9ff",
    fontWeight: 600,
  },
};

export default Footer;
