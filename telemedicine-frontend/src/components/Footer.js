import React from "react";

const Footer = () => {
  return (
    <footer style={styles.footer}>
      <div style={styles.footerContent}>
        <p style={styles.copyright}>&copy; 2025 Telemedicine Platform. All rights reserved.</p>
        <p style={styles.support}>
          Support: <a 
            href="mailto:support@irme.in" 
            style={styles.emailLink}
            onMouseEnter={(e) => e.target.style.color = "#f0f0f0"}
            onMouseLeave={(e) => e.target.style.color = "white"}
          >support@irme.in</a>
        </p>
      </div>
    </footer>
  );
};

const styles = {
  footer: {
    background: "#007bff",
    color: "white",
    textAlign: "center",
    padding: "5px 10px",
    position: "fixed",
    bottom: 0,
    width: "100%",
    zIndex: 1000,
    boxShadow: "0 -2px 5px rgba(0,0,0,0.1)",
  },
  footerContent: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: "20px",
    flexWrap: "wrap",
    fontSize: "12px",
  },
  copyright: {
    margin: 0,
    padding: 0,
  },
  support: {
    margin: 0,
    padding: 0,
  },
  emailLink: {
    color: "white",
    textDecoration: "underline",
    fontWeight: "500",
    transition: "color 0.2s",
  },
};

export default Footer;
