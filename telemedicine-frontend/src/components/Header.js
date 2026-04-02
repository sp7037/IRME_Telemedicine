import React from "react";
import { Link } from "react-router-dom";

const Header = () => {
  return (
    <header style={styles.header}>
      <div style={styles.logo}>🩺 Telemedicine Platform</div>
      <nav style={styles.nav}>
        <Link to="/dashboard/patient" style={styles.navLink}>Dashboard</Link>
        <Link to="/patient/profile" style={styles.navLink}>Profile</Link>
        <Link to="/logout" style={styles.navButton}>🚪 Logout</Link>
      </nav>
    </header>
  );
};

const styles = {
  header: {
    background: "#007bff",
    color: "white",
    padding: "15px 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    zIndex: 1000,
  },
  logo: {
    fontSize: "20px",
    fontWeight: "bold",
  },
  nav: {
    display: "flex",
    gap: "15px",
  },
  navLink: {
    color: "white",
    textDecoration: "none",
    padding: "8px 15px",
    borderRadius: "5px",
  },
  navButton: {
    background: "red",
    color: "white",
    padding: "8px 15px",
    borderRadius: "5px",
    textDecoration: "none",
  },
};

export default Header;
