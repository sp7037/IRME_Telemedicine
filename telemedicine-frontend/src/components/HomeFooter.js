import React from "react";
import { BRAND_NAVY } from "../constants/brandTheme";
import { BRAND_LOGO_HORIZONTAL_WHITE } from "../constants/brandAssets";

/**
 * Public footer — matches Home.js IRME footer.
 */
const HomeFooter = () => {
  return (
    <footer style={styles.footer}>
      <div style={styles.logoContainer}>
        <img 
          src={BRAND_LOGO_HORIZONTAL_WHITE} 
          alt="IRME Telemedicine" 
          style={styles.logo}
          width="200"
          height="50"
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
    marginBottom: "20px",
  },
  logo: {
    height: "50px",
    width: "200px",
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
