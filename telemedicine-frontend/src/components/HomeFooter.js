import React from "react";

const HomeFooter = () => {
  return (
    <footer style={styles.footer}>
      <p>&copy; {new Date().getFullYear()} Telemedicine Platform. All rights reserved.</p>
      <p style={styles.links}>
        <a href="/about" style={styles.link}>About Us</a> | 
        <a href="/contact" style={styles.link}>Contact</a> | 
        <a href="/terms" style={styles.link}>Terms & Conditions</a>
      </p>
    </footer>
  );
};

const styles = {
  footer: {
    background: "#007bff",
    color: "white",
    textAlign: "center",
    padding: "15px",
    position: "relative",
    bottom: "0",
    width: "100%",
    marginTop: "40px",
  },
  links: {
    marginTop: "5px",
    fontSize: "14px",
  },
  link: {
    color: "white",
    textDecoration: "none",
    margin: "0 10px",
  },
};

export default HomeFooter;
