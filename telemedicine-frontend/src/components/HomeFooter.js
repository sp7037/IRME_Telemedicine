import React from "react";
import { BRAND_NAVY } from "../constants/brandTheme";

/**
 * Public footer — matches Home.js IRME footer.
 */
const HomeFooter = () => {
  return (
    <footer style={styles.footer}>
      <p style={styles.footerTitle}>IRME INSTITUTE Telemedicine Platform</p>
      <p style={styles.footerText}>
        Direct doctor consultations and center-facilitated care for better
        healthcare access.
      </p>
      <p style={styles.copy}>
        &copy; {new Date().getFullYear()} IRME INSTITUTE. All rights reserved.
      </p>
    </footer>
  );
};

const styles = {
  footer: {
    marginTop: "auto",
    backgroundColor: BRAND_NAVY,
    color: "rgba(255, 255, 255, 0.85)",
    textAlign: "center",
    padding: "32px 20px",
    borderTop: "2px solid rgba(31, 118, 216, 0.5)",
  },
  footerTitle: {
    margin: 0,
    fontWeight: 600,
    fontSize: "16px",
    color: "#ffffff",
    letterSpacing: "0.01em",
  },
  footerText: {
    margin: "12px auto 0",
    fontSize: "15px",
    maxWidth: "560px",
    lineHeight: 1.6,
    opacity: 0.9,
  },
  copy: {
    margin: "16px 0 0",
    fontSize: "14px",
    opacity: 0.75,
  },
};

export default HomeFooter;
