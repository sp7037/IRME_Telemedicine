import React from "react";
import { BRAND_NAVY } from "../constants/brandTheme";
import { BRAND_HORIZONTAL_LOGO_PNG } from "../constants/brandAssets";

/**
 * Public footer — matches Home.js IRME footer.
 */
const HomeFooter = () => {
  return (
    <footer style={styles.footer}>
      <div style={styles.logoContainer}>
        <img 
          src={BRAND_HORIZONTAL_LOGO_PNG} 
          alt="IRME Institute Telemedicine" 
          style={styles.logo}
        />
      </div>
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
    padding: "40px 20px 32px",
    borderTop: "2px solid rgba(31, 118, 216, 0.5)",
  },
  logoContainer: {
    display: "inline-flex",
    backgroundColor: "#ffffff",
    borderRadius: "24px",
    padding: "12px 20px",
    marginBottom: "20px",
  },
  logo: {
    height: "36px",
    width: "auto",
    maxWidth: "280px",
    objectFit: "contain",
    display: "block",
  },
  footerText: {
    margin: "0 auto",
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
