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
    color: "#cfe4ff",
    textAlign: "center",
    padding: "20px 16px",
  },
  footerTitle: {
    margin: 0,
    fontWeight: 700,
    fontSize: "15px",
  },
  footerText: {
    margin: "8px auto 0",
    fontSize: "14px",
    maxWidth: "520px",
    lineHeight: 1.55,
  },
  copy: {
    margin: "14px 0 0",
    fontSize: "13px",
    opacity: 0.85,
  },
};

export default HomeFooter;
